"""
Flask application API for Vercel Serverless Functions and local dev server.
Enforces security limits, CORS/security headers, custom recipient info, and clean error handling.
"""
import os
import re
import json
from flask import Flask, request, jsonify, Response, send_from_directory
from core.services.xls_parser import XLSParser
from core.services.nfe_generator import NFeGenerator
from core.services.document_validator import ValidationError
from core.domain.nfe import CompanyInfo, AddressInfo, DEFAULT_RECIPIENT, DEFAULT_EMITTER
from core.domain.product import Product
from core.domain.report import TransferReport

app = Flask(__name__, static_folder="../frontend", static_url_path="")

# Security: Limit maximum payload size to 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

@app.after_request
def add_security_headers(response):
    """Applies standard HTTP security headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

def extract_recipient_from_request(form_data) -> CompanyInfo:
    """Extracts custom recipient company details from form parameters if provided."""
    cnpj_raw = form_data.get("recipient_cnpj", "").strip()
    name_raw = form_data.get("recipient_name", "").strip()

    if not cnpj_raw or not name_raw:
        return DEFAULT_RECIPIENT

    cnpj_clean = re.sub(r"\D", "", cnpj_raw)
    ie_clean = re.sub(r"\D", "", form_data.get("recipient_ie", "")) or DEFAULT_RECIPIENT.ie
    cep_clean = re.sub(r"\D", "", form_data.get("recipient_cep", "")) or DEFAULT_RECIPIENT.address.cep
    phone_clean = re.sub(r"\D", "", form_data.get("recipient_phone", "")) or DEFAULT_RECIPIENT.address.phone

    address = AddressInfo(
        street=form_data.get("recipient_street", "").strip().upper() or DEFAULT_RECIPIENT.address.street,
        number=form_data.get("recipient_number", "").strip() or DEFAULT_RECIPIENT.address.number,
        complement=form_data.get("recipient_complement", "").strip().upper() or DEFAULT_RECIPIENT.address.complement,
        neighborhood=form_data.get("recipient_bairro", "").strip().upper() or DEFAULT_RECIPIENT.address.neighborhood,
        city_code=form_data.get("recipient_city_code", "").strip() or DEFAULT_RECIPIENT.address.city_code,
        city_name=form_data.get("recipient_city_name", "").strip() or DEFAULT_RECIPIENT.address.city_name,
        uf=form_data.get("recipient_uf", "").strip().upper() or DEFAULT_RECIPIENT.address.uf,
        cep=cep_clean,
        phone=phone_clean
    )

    return CompanyInfo(
        cnpj=cnpj_clean,
        name=name_raw.upper(),
        trade_name=form_data.get("recipient_trade_name", name_raw).strip().upper(),
        ie=ie_clean,
        address=address
    )

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
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Nome de arquivo inválido."}), 400

    try:
        file_bytes = file.read()
        report = XLSParser.parse(file_bytes, file.filename)

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

    except ValidationError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro no processamento do arquivo: {str(e)}"}), 500

@app.route("/api/generate-xml", methods=["POST"])
def generate_xml_endpoint():
    try:
        form_data = request.form if request.form else {}
        json_data = request.get_json(silent=True) or {}
        merged_params = {**form_data, **json_data}

        products_json = form_data.get("products") or json_data.get("products")
        filename = form_data.get("filename") or json_data.get("filename")
        
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
                
                products.append(Product(
                    code=str(p_dict.get("code", "")).strip(),
                    description=str(p_dict.get("description", "")).strip(),
                    quantity=qty,
                    unit_price=u_price,
                    total_price=tot_price,
                    freight_price=float(p_dict.get("freight_price", 0.0)),
                    ean=str(p_dict.get("ean", "SEM GTIN")),
                    ncm=str(p_dict.get("ncm", "63023100")),
                    cfop=str(p_dict.get("cfop", "5152")),
                    unit=str(p_dict.get("unit", "PC"))
                ))
            
            if not filename:
                filename = "relatorio_editado.xls"
            report = TransferReport(filename=filename, products=products)

        elif "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            file_bytes = file.read()
            report = XLSParser.parse(file_bytes, file.filename or "relatorio.xls")
        else:
            return jsonify({"success": False, "error": "Nenhum arquivo ou lista de produtos enviada."}), 400

        if not report.products:
            return jsonify({"success": False, "error": "Nenhum produto disponível para exportação na DANFE."}), 400

        # Extract optional custom recipient from request form or json
        recipient = extract_recipient_from_request(merged_params)

        # Extract optional n_nf (defaults to 0 for auto-fill in ERP)
        n_nf = 0
        if "n_nf" in merged_params and str(merged_params["n_nf"]).isdigit():
            n_nf = int(merged_params["n_nf"])

        xml_content = NFeGenerator.generate_xml(report, recipient=recipient, n_nf=n_nf)

        clean_filename = re.sub(r"[^\w\.-]", "_", report.filename)
        return Response(
            xml_content,
            mimetype="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=nfe_transferencia_{clean_filename}.xml"
            }
        )

    except ValidationError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro na geração do XML: {str(e)}"}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"success": False, "error": "O arquivo enviado excede o limite máximo permitido de 10MB."}), 413

if __name__ == "__main__":
    is_debug = os.getenv("FLASK_DEBUG", "False").lower() in ["true", "1"]
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=is_debug)

