import pytest
from core.domain.product import Product
from core.domain.report import TransferReport
from core.domain.company import CompanyInfo, AddressInfo
from core.domain.uf import UF, InvalidUFError, get_ibge_uf_code, UF_IBGE_CODES

def test_product_creation_valid():
    p = Product(code="SKU-001", description="Test Product", quantity=10, unit_price=5.0, total_price=50.0)
    assert p.code == "SKU-001"
    assert p.quantity == 10.0
    assert p.total_price == 50.0

def test_product_validation_empty_code():
    with pytest.raises(ValueError, match="Product code cannot be empty"):
        Product(code="", description="Valid", quantity=1, unit_price=1, total_price=1)

def test_product_validation_empty_description():
    with pytest.raises(ValueError, match="Product description cannot be empty"):
        Product(code="123", description="  ", quantity=1, unit_price=1, total_price=1)

def test_product_validation_negative_quantity():
    with pytest.raises(ValueError, match="Product quantity cannot be negative"):
        Product(code="123", description="Valid", quantity=-5, unit_price=1, total_price=1)

def test_transfer_report_metrics():
    p1 = Product(code="1", description="Item 1", quantity=2, unit_price=10.0, total_price=20.0, freight_price=2.0)
    p2 = Product(code="2", description="Item 2", quantity=3, unit_price=20.0, total_price=60.0, freight_price=3.0)
    report = TransferReport(filename="test.xls", products=[p1, p2])

    assert report.item_count == 2
    assert report.total_quantity == 5.0
    assert report.total_value == 80.0
    assert report.total_freight == 5.0

def test_uf_value_object_valid_and_ibge():
    assert UF.from_str("GO") == UF.GO
    assert UF.from_str("sp") == UF.SP
    assert UF.from_str(" RJ ").ibge_code == "33"
    assert get_ibge_uf_code("MG") == "31"
    assert get_ibge_uf_code("DF") == "53"
    assert len(UF_IBGE_CODES) == 27
    assert len(UF.valid_ufs()) == 27

def test_uf_value_object_fail_fast_invalid():
    # Typos, full state names or nonexistent abbreviations must raise InvalidUFError (Fail-Fast)
    with pytest.raises(InvalidUFError, match="Sigla de UF inválida: 'XX'"):
        UF.from_str("XX")

    with pytest.raises(InvalidUFError, match="Sigla de UF inválida: 'Goiás'"):
        UF.from_str("Goiás")

    with pytest.raises(InvalidUFError, match="Sigla de UF inválida: '123'"):
        UF.from_str("123")

    with pytest.raises(InvalidUFError, match="não pode ser vazia ou nula"):
        UF.from_str("")

    with pytest.raises(InvalidUFError, match="não pode ser vazia ou nula"):
        UF.from_str(None)

def test_address_info_uf_fail_fast():
    # Instantiating address with invalid UF raises InvalidUFError
    with pytest.raises(InvalidUFError, match="Sigla de UF inválida"):
        AddressInfo(uf="INVALID")

    # Empty UF raises InvalidUFError when attempting to get IBGE code
    addr_empty = AddressInfo(uf="")
    with pytest.raises(InvalidUFError, match="Endereço sem UF definida"):
        _ = addr_empty.ibge_uf_code

def test_company_and_address_from_dict():
    data = {
        "recipient_cnpj": "12.345.678/0001-90",
        "recipient_name": "Empresa Teste S/A",
        "recipient_uf": "SP",
        "recipient_cep": "01001-000",
        "recipient_city_code": "3550308",
        "recipient_city_name": "São Paulo"
    }
    company = CompanyInfo.from_dict(data)
    assert company.cnpj == "12345678000190"
    assert company.name == "Empresa Teste S/A"
    assert company.address.uf == "SP"
    assert company.address.ibge_uf_code == "35"
    assert company.address.cep == "01001000"
