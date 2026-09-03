"""
Tax calculation service for estimating IBPT, ICMS, IPI, PIS, and COFINS in NFe generation.
"""
from dataclasses import dataclass
from typing import List
from ..domain.product import Product

@dataclass
class ItemTaxSummary:
    product_code: str
    total_price: float
    ibpt_estimated_tax: float
    federal_tax: float
    state_tax: float
    icms_base: float
    icms_value: float
    ipi_base: float
    ipi_value: float
    pis_base: float
    pis_value: float
    cofins_base: float
    cofins_value: float

@dataclass
class InvoiceTaxSummary:
    total_products: float
    total_trib: float
    total_federal_tax: float
    total_state_tax: float
    total_invoice: float

class TaxCalculator:
    IBPT_TAX_RATE = 0.3863       # ~38.63% average IBPT estimate
    FEDERAL_TAX_SPLIT = 0.51     # 51% Federal proportion
    STATE_TAX_SPLIT = 0.49       # 49% State proportion

    @classmethod
    def calculate_item_tax(cls, product: Product) -> ItemTaxSummary:
        total_p = round(product.total_price, 2)
        v_trib = round(total_p * cls.IBPT_TAX_RATE, 2)
        fed_tax = round(v_trib * cls.FEDERAL_TAX_SPLIT, 2)
        est_tax = round(v_trib * cls.STATE_TAX_SPLIT, 2)

        return ItemTaxSummary(
            product_code=product.code,
            total_price=total_p,
            ibpt_estimated_tax=v_trib,
            federal_tax=fed_tax,
            state_tax=est_tax,
            icms_base=0.0,
            icms_value=0.0,
            ipi_base=total_p,
            ipi_value=0.0,
            pis_base=total_p,
            pis_value=0.0,
            cofins_base=total_p,
            cofins_value=0.0
        )

    @classmethod
    def calculate_invoice_summary(cls, products: List[Product]) -> InvoiceTaxSummary:
        tot_prod = sum(round(p.total_price, 2) for p in products)
        tot_trib = sum(cls.calculate_item_tax(p).ibpt_estimated_tax for p in products)
        tot_fed = round(tot_trib * cls.FEDERAL_TAX_SPLIT, 2)
        tot_est = round(tot_trib * cls.STATE_TAX_SPLIT, 2)

        return InvoiceTaxSummary(
            total_products=round(tot_prod, 2),
            total_trib=round(tot_trib, 2),
            total_federal_tax=tot_fed,
            total_state_tax=tot_est,
            total_invoice=round(tot_prod, 2)
        )
