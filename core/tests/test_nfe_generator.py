import xml.etree.ElementTree as ET

from core.domain.product import Product
from core.domain.report import TransferReport
from core.domain.nfe import CompanyInfo, AddressInfo
from core.services.nfe_generator import NFeGenerator

# Explicit test emitter/recipient — no reliance on env vars or hardcoded defaults
TEST_ADDRESS = AddressInfo(
    street="RUA TESTE",
    number="100",
    complement="SALA 1",
    neighborhood="CENTRO",
    city_code="5200000",
    city_name="Goiania",
    uf="GO",
    cep="74000000",
    country_code="1058",
    country_name="Brasil",
    phone="6200000000"
)

TEST_COMPANY = CompanyInfo(
    cnpj="00000000000191",
    name="EMPRESA TESTE LTDA",
    trade_name="EMPRESA TESTE",
    ie="000000000",
    crt="1",
    address=TEST_ADDRESS
)


def test_generate_nfe_xml_structure():
    """Default export: nNF must be empty and infNFe must NOT have an Id (access key)."""
    p1 = Product(code="BUD-17-1-1", description="FRONHA BUDDEMEYER", quantity=10, unit_price=25.0, total_price=250.0)
    p2 = Product(code="PM068", description="ALIMENTADOR INTERNO", quantity=5, unit_price=30.0, total_price=150.0)
    report = TransferReport(filename="test.xls", products=[p1, p2])

    xml_str = NFeGenerator.generate_xml(report, emitter=TEST_COMPANY, recipient=TEST_COMPANY)
    
    assert "<nfeProc" in xml_str
    assert "EMPRESA TESTE LTDA" in xml_str
    assert "00000000000191" in xml_str
    assert "BUD-17-1-1" in xml_str
    assert "PM068" in xml_str

    # nNF must be empty so the ERP assigns a new number
    assert "<nNF/>" in xml_str or "<nNF></nNF>" in xml_str

    root = ET.fromstring(xml_str)
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
    
    # infNFe must NOT contain an Id attribute (no access key without a number)
    inf_nfe = root.find(".//nfe:infNFe", ns)
    assert inf_nfe is not None
    assert "Id" not in inf_nfe.attrib

    # cDV must be empty
    cdv_elem = root.find(".//nfe:cDV", ns)
    assert cdv_elem is not None
    assert not cdv_elem.text  # empty or None

    dets = root.findall(".//nfe:det", ns)
    assert len(dets) == 2
    
    v_prod = root.find(".//nfe:ICMSTot/nfe:vProd", ns)
    assert v_prod is not None and v_prod.text == "400.00"


def test_generate_nfe_xml_with_explicit_number():
    """When n_nf is provided, nNF and the access key must be populated."""
    p1 = Product(code="BUD-17-1-1", description="FRONHA BUDDEMEYER", quantity=10, unit_price=25.0, total_price=250.0)
    report = TransferReport(filename="test.xls", products=[p1])

    xml_str = NFeGenerator.generate_xml(report, emitter=TEST_COMPANY, recipient=TEST_COMPANY, n_nf=12345)
    
    root = ET.fromstring(xml_str)
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    # nNF must contain the provided number
    nnf_elem = root.find(".//nfe:nNF", ns)
    assert nnf_elem is not None and nnf_elem.text == "12345"

    # infNFe must have an Id attribute with a 44-digit access key
    inf_nfe = root.find(".//nfe:infNFe", ns)
    assert inf_nfe is not None
    nfe_id = inf_nfe.attrib.get("Id", "")
    assert nfe_id.startswith("NFe")
    assert len(nfe_id) == 47  # "NFe" + 44 digits

    # cDV must be populated
    cdv_elem = root.find(".//nfe:cDV", ns)
    assert cdv_elem is not None and cdv_elem.text
