import io
import openpyxl
from core.services.spreadsheet_parser import SpreadsheetParser
from core.tests.test_parser import FIXTURE_FILE_PATH

def test_spreadsheet_parser_xls_fixture():
    with open(FIXTURE_FILE_PATH, "rb") as f:
        file_bytes = f.read()

    report = SpreadsheetParser.parse(file_bytes, "relatorio.xls")
    assert report.filename == "relatorio.xls"
    assert report.item_count == 72
    assert report.total_quantity > 0
    assert report.total_value > 0

def test_spreadsheet_parser_xlsx_dynamic():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Código", "Descrição do Produto", "Quantidade", "Valor Unitário", "Total Líquido", "Frete"])
    ws.append(["SKU-100", "Camiseta Básica Algodão", 10, 25.0, 250.0, 0.0])
    ws.append(["SKU-200", "=cmd|'calc'!A0", 5, 50.0, 250.0, 10.0])  # Formula injection payload

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    xlsx_bytes = stream.getvalue()

    report = SpreadsheetParser.parse(xlsx_bytes, "planilha_teste.xlsx")
    assert report.item_count == 2
    assert report.products[0].code == "SKU-100"
    assert report.products[0].description == "Camiseta Básica Algodão"
    assert report.products[0].quantity == 10.0
    assert report.products[0].total_price == 250.0

    # Test formula neutralization on second product
    assert not report.products[1].description.startswith("=")
    assert "cmd|'calc'!A0" in report.products[1].description


def test_spreadsheet_parser_stock_report():
    """
    Validates stock report schema:
    Col A: SKU
    Col B: Descrição
    Col C: Estoque Atual
    Col D: Unidades Reservadas (subtracted to get available quantity)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["SKU", "Descrição do Produto", "Estoque Atual", "Unidades Reservadas"])
    ws.append(["SKU-A1", "Item A - Com Reserva Parcial", 100, 30])    # 100 - 30 = 70 available
    ws.append(["SKU-B2", "Item B - Sem Reserva", 50, 0])              # 50 - 0 = 50 available
    ws.append(["SKU-C3", "Item C - Reserva Excede Estoque", 10, 25])  # max(0, 10 - 25) = 0 available
    ws.append(["SKU-D4", "Item D - Coluna Reserva Vazia", 40, None])  # 40 available

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    xlsx_bytes = stream.getvalue()

    stock_report = SpreadsheetParser.parse_stock_report(xlsx_bytes, "estoque_filial.xlsx")
    assert stock_report.item_count == 4
    
    prod_map = {p.code: p for p in stock_report.products}
    assert prod_map["SKU-A1"].quantity == 70.0
    assert prod_map["SKU-B2"].quantity == 50.0
    assert prod_map["SKU-C3"].quantity == 0.0
    assert prod_map["SKU-D4"].quantity == 40.0
