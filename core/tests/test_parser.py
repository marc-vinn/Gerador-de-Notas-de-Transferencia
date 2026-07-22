import os
import pytest
from core.services.xls_parser import XLSParser

SAMPLE_FILE_PATH = r"c:\Users\marco\Sistema de transferencia\relatorio-de-vendas_22-07-2026-15-05-58.xls"

def test_parse_sample_xls_file():
    assert os.path.exists(SAMPLE_FILE_PATH), "Sample XLS file missing"
    
    with open(SAMPLE_FILE_PATH, "rb") as f:
        content = f.read()

    report = XLSParser.parse(content, "relatorio-de-vendas.xls")
    
    assert report.filename == "relatorio-de-vendas.xls"
    assert len(report.products) == 72
    assert report.total_quantity > 0
    assert report.total_value > 0

    # Test specific product from sample
    prod_fronha = next((p for p in report.products if p.code == "BUD-17-1-1"), None)
    assert prod_fronha is not None
    assert prod_fronha.quantity == 42.0
    assert "FRONHA BUDDEMEYER" in prod_fronha.description
