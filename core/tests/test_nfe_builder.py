from core.domain.product import Product
from core.domain.report import TransferReport
from core.domain.company import CompanyInfo, AddressInfo
from core.services.nfe_builder.chave_acesso import ChaveAcessoGenerator
from core.services.nfe_builder.nfe_xml_builder import NFeXmlBuilder

def test_chave_acesso_modulo_11():
    # Base key length 43 chars
    base_key = "5226094048477400015055001000000001112345678"
    cdv = ChaveAcessoGenerator.calculate_mod11(base_key)
    assert len(cdv) == 1
    assert cdv.isdigit()

    full_key, returned_cdv = ChaveAcessoGenerator.generate(
        uf_ibge_code="52",
        date_aamm="2609",
        cnpj="40484774000150",
        mod="55",
        serie="1",
        number="1",
        tp_emis="1",
        cnf="12345678"
    )
    assert len(full_key) == 44
    assert full_key.startswith("5226094048477400015055001000000001112345678")
    assert full_key.endswith(returned_cdv)

def test_chave_acesso_different_states():
    # Test SP (35)
    key_sp, cdv_sp = ChaveAcessoGenerator.generate(
        uf_ibge_code="35",
        date_aamm="2609",
        cnpj="12345678000190",
        mod="55",
        serie="1",
        number="100",
        tp_emis="1",
        cnf="87654321"
    )
    assert len(key_sp) == 44
    assert key_sp.startswith("35260912345678000190")

def test_nfe_xml_builder_structure():
    addr = AddressInfo(street="RUA 1", number="10", neighborhood="BAIRRO", city_code="3550308", city_name="SAO PAULO", uf="SP", cep="01001000")
    emitter = CompanyInfo(cnpj="11111111000111", name="EMPRESA EMISSORA LTDA", address=addr)
    recipient = CompanyInfo(cnpj="22222222000122", name="EMPRESA DESTINATARIA LTDA", address=addr)
    prod = Product(code="P01", description="PRODUTO TESTE", quantity=5.0, unit_price=20.0, total_price=100.0)
    report = TransferReport(filename="rel.xls", products=[prod])

    builder = NFeXmlBuilder(report=report, emitter=emitter, recipient=recipient, n_nf=123)
    xml_str = builder.build_xml_string()

    assert "<nfeProc" in xml_str
    assert "<cUF>35</cUF>" in xml_str  # Derived from SP emitter
    assert "<nNF>123</nNF>" in xml_str
    assert "EMPRESA EMISSORA LTDA" in xml_str
    assert "EMPRESA DESTINATARIA LTDA" in xml_str
    assert "<cProd>P01</cProd>" in xml_str
    assert "<vProd>100.00</vProd>" in xml_str
