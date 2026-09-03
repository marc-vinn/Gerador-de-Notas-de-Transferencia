from core.domain.product import Product
from core.services.tax_calculator import TaxCalculator

def test_tax_calculator_item():
    product = Product(code="101", description="Produto Teste", quantity=2, unit_price=100.0, total_price=200.0)
    summary = TaxCalculator.calculate_item_tax(product)

    assert summary.total_price == 200.0
    # 200 * 0.3863 = 77.26
    assert summary.ibpt_estimated_tax == 77.26
    # Federal: 77.26 * 0.51 = 39.40
    assert summary.federal_tax == 39.40
    # State: 77.26 * 0.49 = 37.86
    assert summary.state_tax == 37.86

def test_tax_calculator_invoice_summary():
    p1 = Product(code="1", description="P1", quantity=1, unit_price=100.0, total_price=100.0)
    p2 = Product(code="2", description="P2", quantity=1, unit_price=50.0, total_price=50.0)

    summary = TaxCalculator.calculate_invoice_summary([p1, p2])
    assert summary.total_products == 150.0
    assert summary.total_invoice == 150.0
    # Total trib: (100*0.3863 = 38.63) + (50*0.3863 = 19.31) = 57.94
    assert summary.total_trib == 57.94
    assert summary.total_federal_tax == round(57.94 * 0.51, 2)
    assert summary.total_state_tax == round(57.94 * 0.49, 2)
