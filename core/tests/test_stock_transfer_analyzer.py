import pytest
from core.domain.product import Product
from core.domain.report import TransferReport
from core.domain.transfer_decision import TransferState
from core.services.stock_transfer_analyzer import StockTransferAnalyzer

def create_report(filename: str, products_data: list) -> TransferReport:
    products = [
        Product(
            code=p["code"],
            description=p["desc"],
            quantity=p["qty"],
            unit_price=p.get("price", 10.0),
            total_price=p.get("total", p["qty"] * p.get("price", 10.0))
        )
        for p in products_data
    ]
    return TransferReport(filename=filename, products=products)


def test_state_1_normal_transfer_approved():
    """Branch needs 30 un (4*10 - 10), Matrix has 60 - 20 = 40 balance >= 30 -> Approved."""
    rep_b_sales = create_report("b_sales.xls", [{"code": "SKU-1", "desc": "Item 1", "qty": 10.0, "price": 50.0}])
    rep_b_stock = create_report("b_stock.xls", [{"code": "SKU-1", "desc": "Item 1", "qty": 10.0}])
    rep_m_sales = create_report("m_sales.xls", [{"code": "SKU-1", "desc": "Item 1", "qty": 20.0}])
    rep_m_stock = create_report("m_stock.xls", [{"code": "SKU-1", "desc": "Item 1", "qty": 60.0}])

    res = StockTransferAnalyzer.analyze(rep_b_sales, rep_b_stock, rep_m_sales, rep_m_stock)

    assert len(res.approved_normal) == 1
    assert res.approved_normal[0].state == TransferState.TRANSFERENCIA_NORMAL_APROVADA
    assert res.approved_normal[0].quantity == 30.0
    assert res.approved_normal[0].total_price == 1500.0
    assert len(res.purchase_alerts) == 0


def test_state_2_matrix_insufficient_balance():
    """Branch needs 30 un, Matrix balance is 60 - 50 = 10 < 30 -> Removed with Purchase Alert."""
    rep_b_sales = create_report("b_sales.xls", [{"code": "SKU-2", "desc": "Item 2", "qty": 10.0, "price": 20.0}])
    rep_b_stock = create_report("b_stock.xls", [{"code": "SKU-2", "desc": "Item 2", "qty": 10.0}])
    rep_m_sales = create_report("m_sales.xls", [{"code": "SKU-2", "desc": "Item 2", "qty": 50.0}])
    rep_m_stock = create_report("m_stock.xls", [{"code": "SKU-2", "desc": "Item 2", "qty": 60.0}])

    res = StockTransferAnalyzer.analyze(rep_b_sales, rep_b_stock, rep_m_sales, rep_m_stock)

    assert len(res.approved_normal) == 0
    assert len(res.removed_items) == 1
    assert res.removed_items[0].state == TransferState.REMOVIDO_MATRIZ_SEM_SALDO
    assert res.removed_items[0].need_purchase is True
    assert len(res.purchase_alerts) == 1
    assert res.purchase_alerts[0].sku == "SKU-2"


def test_state_3_both_units_stable():
    """Branch has 25 >= 4*5 = 20, Matrix balance is 40 - 30 = +10 >= 0 -> Both stable."""
    rep_b_sales = create_report("b_sales.xls", [{"code": "SKU-3", "desc": "Item 3", "qty": 5.0, "price": 15.0}])
    rep_b_stock = create_report("b_stock.xls", [{"code": "SKU-3", "desc": "Item 3", "qty": 25.0}])
    rep_m_sales = create_report("m_sales.xls", [{"code": "SKU-3", "desc": "Item 3", "qty": 30.0}])
    rep_m_stock = create_report("m_stock.xls", [{"code": "SKU-3", "desc": "Item 3", "qty": 40.0}])

    res = StockTransferAnalyzer.analyze(rep_b_sales, rep_b_stock, rep_m_sales, rep_m_stock)

    assert len(res.approved_normal) == 0
    assert len(res.approved_reverse) == 0
    assert len(res.removed_items) == 1
    assert res.removed_items[0].state == TransferState.FILIAL_E_MATRIZ_ESTAVEIS
    assert res.removed_items[0].need_purchase is False
    assert len(res.purchase_alerts) == 0


def test_state_4_safe_reverse_transfer_preserves_branch():
    """
    Branch sells 5/week (Month demand = 20), has 50 stock -> Excedente = 30.
    Matrix sells 40/month, has 25 stock -> Déficit = 15.
    Reverse transfer = min(30, 15) = 15 un.
    Validates Branch post-transfer stock is 50 - 15 = 35 >= 20 (Preserves 100% of branch demand).
    """
    rep_b_sales = create_report("b_sales.xls", [{"code": "SKU-4", "desc": "Item 4", "qty": 5.0, "price": 30.0}])
    rep_b_stock = create_report("b_stock.xls", [{"code": "SKU-4", "desc": "Item 4", "qty": 50.0}])
    rep_m_sales = create_report("m_sales.xls", [{"code": "SKU-4", "desc": "Item 4", "qty": 40.0}])
    rep_m_stock = create_report("m_stock.xls", [{"code": "SKU-4", "desc": "Item 4", "qty": 25.0}])

    res = StockTransferAnalyzer.analyze(rep_b_sales, rep_b_stock, rep_m_sales, rep_m_stock)

    assert len(res.approved_normal) == 0
    assert len(res.approved_reverse) == 1
    rev_item = res.approved_reverse[0]
    assert rev_item.state == TransferState.TRANSFERENCIA_INVERSA_APROVADA
    assert rev_item.quantity == 15.0
    assert rev_item.total_price == 450.0

    # Invariant verification: Branch stock - Transfer >= 4 * Branch week sales
    branch_remaining = rev_item.branch_stock - rev_item.quantity
    assert branch_remaining == 35.0
    assert branch_remaining >= rev_item.branch_demand_month


def test_state_5_critical_rupture_both_units():
    """Branch needs 40 un, Matrix has 10 - 30 = -20 deficit -> Ruptura Crítica + Purchase Alert."""
    rep_b_sales = create_report("b_sales.xls", [{"code": "SKU-5", "desc": "Item 5", "qty": 10.0, "price": 10.0}])
    rep_b_stock = create_report("b_stock.xls", [{"code": "SKU-5", "desc": "Item 5", "qty": 0.0}])
    rep_m_sales = create_report("m_sales.xls", [{"code": "SKU-5", "desc": "Item 5", "qty": 30.0}])
    rep_m_stock = create_report("m_stock.xls", [{"code": "SKU-5", "desc": "Item 5", "qty": 10.0}])

    res = StockTransferAnalyzer.analyze(rep_b_sales, rep_b_stock, rep_m_sales, rep_m_stock)

    assert len(res.approved_normal) == 0
    assert len(res.removed_items) == 1
    assert res.removed_items[0].state == TransferState.RUPTURA_CRITICA_AMBAS
    assert res.removed_items[0].need_purchase is True
    assert len(res.purchase_alerts) == 1
