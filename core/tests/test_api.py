import io
import os
import pytest
from api.index import app
from core.tests.test_parser import FIXTURE_FILE_PATH

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_api_index_route(client):
    rv = client.get("/")
    assert rv.status_code in [200, 404]

def test_api_upload_endpoint(client):
    with open(FIXTURE_FILE_PATH, "rb") as f:
        file_bytes = f.read()

    data = {
        "file": (io.BytesIO(file_bytes), "relatorio.xls")
    }
    rv = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    res_json = rv.get_json()
    assert res_json["success"] is True
    assert res_json["summary"]["item_count"] == 72
    assert len(res_json["products"]) == 72

def test_api_generate_xml_default_recipient(client):
    with open(FIXTURE_FILE_PATH, "rb") as f:
        file_bytes = f.read()

    data = {
        "file": (io.BytesIO(file_bytes), "relatorio.xls")
    }
    rv = client.post("/api/generate-xml", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert rv.mimetype == "application/xml"
    xml_data = rv.data.decode("utf-8")
    assert "<nfeProc" in xml_data
    assert "ARBORETHO IMPORTS LTDA" in xml_data

def test_api_generate_xml_custom_recipient(client):
    with open(FIXTURE_FILE_PATH, "rb") as f:
        file_bytes = f.read()

    data = {
        "file": (io.BytesIO(file_bytes), "relatorio.xls"),
        "recipient_cnpj": "12.345.678/0001-99",
        "recipient_name": "FILIAL SÃO PAULO LTDA",
        "recipient_ie": "999888777",
        "recipient_street": "AV PAULISTA",
        "recipient_number": "1000",
        "recipient_bairro": "BELA VISTA",
        "recipient_city_name": "SAO PAULO",
        "recipient_uf": "SP"
    }
    rv = client.post("/api/generate-xml", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert rv.mimetype == "application/xml"
    xml_data = rv.data.decode("utf-8")
    assert "FILIAL SÃO PAULO LTDA" in xml_data
    assert "12345678000199" in xml_data
    assert "AV PAULISTA" in xml_data
    assert "<UF>SP</UF>" in xml_data

def test_api_generate_xml_with_edited_products(client):
    import json
    edited_products = [
        {
            "code": "EDITED-001",
            "description": "PRODUTO EDITADO TESTE",
            "quantity": 25.0,
            "unit_price": 49.90,
            "total_price": 1247.50
        }
    ]
    data = {
        "products": json.dumps(edited_products),
        "filename": "relatorio_teste.xls"
    }
    rv = client.post("/api/generate-xml", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    assert rv.mimetype == "application/xml"
    xml_data = rv.data.decode("utf-8")
    assert "EDITED-001" in xml_data
    assert "PRODUTO EDITADO TESTE" in xml_data
    assert "<qCom>25.0000</qCom>" in xml_data
    assert "<vUnCom>49.90</vUnCom>" in xml_data
    assert "<vProd>1247.50</vProd>" in xml_data

