"""
Domain entity representing the Transfer Report parsed from the branch sales report.
"""
from dataclasses import dataclass, field
from typing import List
from .product import Product

@dataclass
class TransferReport:
    filename: str
    products: List[Product] = field(default_factory=list)

    @property
    def total_quantity(self) -> float:
        return sum(p.quantity for p in self.products)

    @property
    def total_value(self) -> float:
        return sum(p.total_price for p in self.products)

    @property
    def total_freight(self) -> float:
        return sum(p.freight_price for p in self.products)

    @property
    def item_count(self) -> int:
        return len(self.products)
