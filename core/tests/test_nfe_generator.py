import xml.etree.ElementTree as ET

from core.domain.product import Product
from core.domain.report import TransferReport
from core.services.nfe_generator import NFeGenerator

def test_generate_nfe_xml_structure():
    p1 = Product(code="BUD-17-1-1", description="FRONHA BUDDEMEYER", quantity=10, unit_price=25.0, total_price=250.0)
    p2 = Product(code="PM068", description="ALIMENTADOR INTERNO", quantity=5, unit_price=30.0, total_price=150.0)
    report = TransferReport(filename="test.xls", products=[p1, p2])

    xml_str = NFeGenerator.generate_xml(report, n_nf=50624)
    
    assert "<nfeProc" in xml_str
    assert "ARBORETHO IMPORTS LTDA" in xml_str
    assert "40484774000150" in xml_str
    assert "BUD-17-1-1" in xml_str
    assert "PM068" in xml_str
    assert "50624" in xml_str

    root = ET.fromstring(xml_str)
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
    
    dets = root.findall(".//nfe:det", ns)
    assert len(dets) == 2
    
    v_prod = root.find(".//nfe:ICMSTot/nfe:vProd", ns)
    assert v_prod is not None and v_prod.text == "400.00"
