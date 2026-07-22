"""
Domain entity representing a Product item in the transfer system.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    code: str
    description: str
    quantity: float
    unit_price: float
    total_price: float
    freight_price: float = 0.0
    ean: str = "SEM GTIN"
    ncm: str = "63023100"
    cfop: str = "5152"
    unit: str = "PC"

    def __post_init__(self):
        self.code = str(self.code).strip()
        self.description = str(self.description).strip()
        self.quantity = float(self.quantity)
        self.unit_price = float(self.unit_price)
        self.total_price = float(self.total_price)
        self.freight_price = float(self.freight_price)

        if not self.code:
            raise ValueError("Product code cannot be empty")
        if not self.description:
            raise ValueError("Product description cannot be empty")
        if self.quantity < 0:
            raise ValueError("Product quantity cannot be negative")
