import pytest
from core.domain.product import Product
from core.domain.report import TransferReport
from core.domain.nfe import CompanyInfo, DEFAULT_EMITTER

def test_product_initialization_and_validation():
    p = Product(code="PROD1", description="Produto Teste", quantity=10, unit_price=25.5, total_price=255.0)
    assert p.code == "PROD1"
    assert p.description == "Produto Teste"
    assert p.quantity == 10.0
    assert p.unit_price == 25.5
    assert p.total_price == 255.0

def test_invalid_product_raises_error():
    with pytest.raises(ValueError):
        Product(code="", description="Sem codigo", quantity=1, unit_price=10, total_price=10)
    with pytest.raises(ValueError):
        Product(code="P1", description="", quantity=1, unit_price=10, total_price=10)
    with pytest.raises(ValueError):
        Product(code="P1", description="Valid", quantity=-5, unit_price=10, total_price=10)

def test_transfer_report_totals():
    p1 = Product(code="P1", description="Item 1", quantity=5, unit_price=10.0, total_price=50.0, freight_price=5.0)
    p2 = Product(code="P2", description="Item 2", quantity=2, unit_price=20.0, total_price=40.0, freight_price=2.0)
    report = TransferReport(filename="test.xls", products=[p1, p2])

    assert report.item_count == 2
    assert report.total_quantity == 7.0
    assert report.total_value == 90.0
    assert report.total_freight == 7.0

def test_default_company_info():
    company = DEFAULT_EMITTER
    assert company.cnpj == "40484774000150"
    assert company.name == "ARBORETHO IMPORTS LTDA"
    assert company.ie == "108282910"
