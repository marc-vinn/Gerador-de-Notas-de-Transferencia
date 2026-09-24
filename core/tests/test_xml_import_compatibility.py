import xml.etree.ElementTree as ET
from dataclasses import replace
from core.tests.test_nfe_generator import TEST_COMPANY
from core.domain.product import Product
from core.domain.report import TransferReport
from core.services.nfe_generator import NFeGenerator
from core.services.nfe_builder.chave_acesso import ChaveAcessoGenerator

NS = {'n': 'http://www.portalfiscal.inf.br/nfe'}

def test_empty_fields_use_legacy_import_values():
    product = Product('SKU', 'Produto', 2, 5, 10, ean='', ncm='', cfop='', unit='')
    company = replace(TEST_COMPANY, crt='')
    root = ET.fromstring(NFeGenerator.generate_xml(TransferReport('test.xls', [product]), company, company))
    for tag, expected in {'nNF':'50624', 'CRT':'1', 'NCM':'63023100', 'CFOP':'5152',
                          'cEAN':'SEM GTIN', 'cEANTrib':'SEM GTIN', 'uCom':'PC', 'uTrib':'PC'}.items():
        assert root.find(f'.//n:{tag}', NS).text == expected
    key = root.find('.//n:infNFe', NS).get('Id')[3:]
    assert len(key) == 44
    assert key[-1] == ChaveAcessoGenerator.calculate_mod11(key[:-1])
    assert root.find('.//n:protNFe', NS) is None

def test_explicit_product_fields_and_number_are_preserved():
    product = Product('SKU', 'Produto', 2, 5, 10, ean='7909301781805', ncm='63026000', cfop='6152', unit='JG')
    company = replace(TEST_COMPANY, crt='3')
    root = ET.fromstring(NFeGenerator.generate_xml(TransferReport('test.xls', [product]), company, company, n_nf=123))
    for tag, expected in {'nNF':'123', 'CRT':'3', 'NCM':'63026000', 'CFOP':'6152',
                          'cEAN':'7909301781805', 'uCom':'JG', 'uTrib':'JG'}.items():
        assert root.find(f'.//n:{tag}', NS).text == expected

def test_api_export_handles_empty_metadata_in_both_directions():
    from api.index import app
    data = {'products': [{'sku': 'SKU', 'description': 'Produto', 'quantity': 2,
                         'unit_price': 5, 'ean': '', 'ncm': '', 'cfop': '', 'unit': ''}]}
    for prefix, cnpj in [('emitter', '40484774000150'), ('recipient', '40484774000230')]:
        data.update({f'{prefix}_cnpj': cnpj, f'{prefix}_name': 'Empresa', f'{prefix}_uf': 'GO',
                     f'{prefix}_city_code': '5208707'})
    with app.test_client() as client:
        for direction, cnpj in [('matrix_to_branch', '40484774000150'), ('branch_to_matrix', '40484774000230')]:
            response = client.post('/api/generate-xml', json={**data, 'direction': direction})
            assert response.status_code == 200
            root = ET.fromstring(response.data)
            assert root.find('.//n:emit/n:CNPJ', NS).text == cnpj
            assert root.find('.//n:NCM', NS).text == '63023100'
            assert root.find('.//n:uCom', NS).text == 'PC'
            assert root.find('.//n:nNF', NS).text == '50624'
            key = root.find('.//n:infNFe', NS).get('Id')[3:]
            assert key[6:20] == cnpj
            assert key[-1] == ChaveAcessoGenerator.calculate_mod11(key[:-1])
