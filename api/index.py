import os
import sys
import re
import json
import traceback

# Ensure project root is on sys.path for direct script execution and Vercel
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify, Response, send_from_directory
from werkzeug.exceptions import HTTPException
from core.services.spreadsheet_parser import SpreadsheetParser
from core.services.nfe_generator import NFeGenerator
from core.services.stock_transfer_analyzer import StockTransferAnalyzer
from core.services.document_validator import ValidationError
from core.domain.company import CompanyInfo
from core.domain.uf import InvalidUFError
from core.domain.nfe import DEFAULT_EMITTER, DEFAULT_RECIPIENT
from core.domain.product import Product
from core.domain.report import TransferReport

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__, static_folder="../frontend", static_url_path="")

# Security: Limit maximum payload size to 50MB (supporting 4 simultaneous spreadsheet uploads)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

@app.after_request
def add_security_headers(response):
    """Applies standard HTTP and CSP security headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://brasilapi.com.br https://minhareceita.org https://viacep.com.br; "
        "img-src 'self' data:; "
        "script-src 'self' 'unsafe-inline'"
    )
    return response

def extract_company_from_request(form_data: dict, prefix: str = "recipient") -> Optional[CompanyInfo]:
    """Extracts company details from request parameters for a given prefix ('emitter' or 'recipient')."""
    p = f"{prefix}_"
    cnpj_raw = form_data.get(f"{p}cnpj") or (form_data.get("cnpj", "") if prefix == "recipient" else "")
    name_raw = form_data.get(f"{p}name") or (form_data.get("name", "") if prefix == "recipient" else "")

    if not str(cnpj_raw or "").strip() or not str(name_raw or "").strip():
        return None

    return CompanyInfo.from_dict(form_data, prefix=prefix)


def extract_recipient_from_request(form_data: dict) -> CompanyInfo:
    """Extracts custom recipient company details from request parameters (backward compatibility)."""
    comp = extract_company_from_request(form_data, prefix="recipient")
    return comp if comp else DEFAULT_RECIPIENT


@app.route("/")
def index():
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    return send_from_directory(frontend_dir, "index.html")

@app.route("/<path:path>")
def static_files(path):
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    return send_from_directory(frontend_dir, path)

@app.route("/api/upload", methods=["POST"])
def upload_report():
    """Single file upload endpoint (backwards compatible)."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Nome de arquivo inválido."}), 400

    try:
        file_bytes = file.read()
        report = SpreadsheetParser.parse(file_bytes, file.filename)

        products_json = [
            {
                "code": p.code,
                "description": p.description,
                "quantity": p.quantity,
                "unit_price": p.unit_price,
                "total_price": p.total_price,
                "freight_price": p.freight_price,
                "ean": p.ean,
                "ncm": p.ncm,
                "cfop": p.cfop,
                "unit": p.unit
            }
            for p in report.products
        ]

        return jsonify({
            "success": True,
            "filename": report.filename,
            "summary": {
                "item_count": report.item_count,
                "total_quantity": report.total_quantity,
                "total_value": report.total_value,
                "total_freight": report.total_freight
            },
            "products": products_json
        })

    except (ValidationError, InvalidUFError) as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro no processamento do arquivo: {str(e)}"}), 500

@app.route("/api/analyze-multi", methods=["POST"])
def analyze_multi_reports():
    """
    Processes 4 spreadsheets simultaneously (Branch Sales, Branch Stock, Matrix Sales, Matrix Stock)
    and executes Option C Stock Decision Matrix.
    """
    required_keys = ["branch_sales", "branch_stock", "matrix_sales", "matrix_stock"]
    for key in required_keys:
        if key not in request.files or not request.files[key].filename:
            return jsonify({
                "success": False,
                "error": f"Arquivo obrigatório ausente: {key}. Por favor envie os 4 relatórios no wizard."
            }), 400

    try:
        b_sales_file = request.files["branch_sales"]
        b_stock_file = request.files["branch_stock"]
        m_sales_file = request.files["matrix_sales"]
        m_stock_file = request.files["matrix_stock"]

        rep_b_sales = SpreadsheetParser.parse(b_sales_file.read(), b_sales_file.filename)
        rep_b_stock = SpreadsheetParser.parse_stock_report(b_stock_file.read(), b_stock_file.filename)
        rep_m_sales = SpreadsheetParser.parse(m_sales_file.read(), m_sales_file.filename)
        rep_m_stock = SpreadsheetParser.parse_stock_report(m_stock_file.read(), m_stock_file.filename)

        analysis_result = StockTransferAnalyzer.analyze(
            branch_sales_report=rep_b_sales,
            branch_stock_report=rep_b_stock,
            matrix_sales_report=rep_m_sales,
            matrix_stock_report=rep_m_stock
        )

        response_payload = analysis_result.to_dict()
        response_payload["filename"] = b_sales_file.filename
        return jsonify(response_payload)

    except (ValidationError, InvalidUFError) as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro na análise multi-relatórios: {str(e)}"}), 500

@app.route("/api/generate-xml", methods=["POST"])
def generate_xml_endpoint():
    try:
        form_data = request.form if request.form else {}
        json_data = request.get_json(silent=True) or {}
        merged_params = {**form_data, **json_data}

        products_json = form_data.get("products") or json_data.get("products")
        filename = form_data.get("filename") or json_data.get("filename")
        direction = form_data.get("direction") or json_data.get("direction") or "matrix_to_branch"

        products = []

        if products_json:
            if isinstance(products_json, str):
                products_list = json.loads(products_json)
            else:
                products_list = products_json

            if not isinstance(products_list, list):
                return jsonify({"success": False, "error": "Formato de produtos inválido."}), 400

            for p_dict in products_list:
                qty = float(p_dict.get("quantity", 0))
                u_price = float(p_dict.get("unit_price", 0))
                tot_price = round(qty * u_price, 2)

                sku = str(p_dict.get("sku") or p_dict.get("code") or "").strip()
                desc = str(p_dict.get("description") or "").strip()

                if not sku or not desc or qty <= 0:
                    continue

                products.append(Product(
                    code=sku,
                    description=desc,
                    quantity=qty,
                    unit_price=u_price,
                    total_price=tot_price,
                    freight_price=float(p_dict.get("freight_price", 0.0)),
                    ean=str(p_dict.get("ean", "")),
                    ncm=str(p_dict.get("ncm", "")),
                    cfop=str(p_dict.get("cfop", "")),
                    unit=str(p_dict.get("unit", ""))
                ))

            if not filename:
                filename = "relatorio_transferencia.xls"
            report = TransferReport(filename=filename, products=products)

        elif "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            file_bytes = file.read()
            report = SpreadsheetParser.parse(file_bytes, file.filename or "relatorio.xls")
        else:
            return jsonify({"success": False, "error": "Nenhum arquivo ou lista de produtos enviada."}), 400

        if not report.products:
            return jsonify({"success": False, "error": "Nenhum produto válido disponível para exportação na DANFE."}), 400

        # Extract both companies dynamically
        configured_emitter = extract_company_from_request(merged_params, prefix="emitter")
        configured_recipient = extract_company_from_request(merged_params, prefix="recipient")

        # Strict Security Gate: Both companies MUST be registered and complete
        if not configured_emitter:
            return jsonify({
                "success": False,
                "error": "Empresa Emitente (Matriz) não configurada. Por favor, cadastre a Matriz antes de gerar a DANFE XML."
            }), 400

        is_emit_valid, emit_err = configured_emitter.is_valid_for_nfe(role_label="Empresa Emitente (Matriz)")
        if not is_emit_valid:
            return jsonify({"success": False, "error": emit_err}), 400

        if not configured_recipient:
            return jsonify({
                "success": False,
                "error": "Empresa Destinatária (Filial) não configurada. Por favor, cadastre a Filial antes de gerar a DANFE XML."
            }), 400

        is_dest_valid, dest_err = configured_recipient.is_valid_for_nfe(role_label="Empresa Destinatária (Filial)")
        if not is_dest_valid:
            return jsonify({"success": False, "error": dest_err}), 400

        n_nf = None
        if "n_nf" in merged_params and str(merged_params["n_nf"]).strip().isdigit():
            n_nf = int(merged_params["n_nf"])

        # Determine emitter and recipient based on transfer direction (Symmetric Swap)
        if direction == "branch_to_matrix":
            # Reverse transfer: Branch -> Matrix
            emitter = configured_recipient
            recipient = configured_emitter
            prefix = "nfe_transferencia_reversa"
        else:
            # Normal transfer: Matrix -> Branch
            emitter = configured_emitter
            recipient = configured_recipient
            prefix = "nfe_transferencia"

        xml_content = NFeGenerator.generate_xml(report, emitter=emitter, recipient=recipient, n_nf=n_nf)

        base_name = os.path.basename(report.filename)
        clean_base = os.path.splitext(base_name)[0]
        clean_filename = re.sub(r"[^\w\-]", "_", clean_base).strip("_") or "relatorio"
        return Response(
            xml_content,
            mimetype="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename={prefix}_{clean_filename}.xml"
            }
        )

    except (ValidationError, InvalidUFError) as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro na geração do XML: {str(e)}"}), 500

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Ensure all HTTP errors (400, 404, 413, 500, etc.) always return JSON instead of HTML."""
    msg = e.description or str(e)
    if e.code == 413:
        msg = "O tamanho combinado dos arquivos enviados excede o limite máximo permitido de 50MB."
    return jsonify({
        "success": False,
        "error": msg
    }), e.code

@app.errorhandler(Exception)
def handle_generic_exception(e):
    """Catch-all for unhandled exceptions to return JSON instead of HTML."""
    traceback.print_exc()
    return jsonify({
        "success": False,
        "error": f"Erro interno no servidor: {str(e)}"
    }), 500

if __name__ == "__main__":
    is_debug = os.getenv("FLASK_DEBUG", "False").lower() in ["true", "1"]
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=is_debug)
