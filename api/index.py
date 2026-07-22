"""
Flask application API for Vercel Serverless Functions and local dev server.
Enforces security limits, CORS/security headers, and clean error handling.
"""
import os
from flask import Flask, request, jsonify, Response, send_from_directory
from core.services.xls_parser import XLSParser
from core.services.nfe_generator import NFeGenerator
from core.services.document_validator import ValidationError

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
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "Nome de arquivo inválido."}), 400

    try:
        file_bytes = file.read()
        report = XLSParser.parse(file_bytes, file.filename or "relatorio.xls")
        xml_content = NFeGenerator.generate_xml(report)

        return Response(
            xml_content,
            mimetype="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=nfe_transferencia_{report.filename}.xml"
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
