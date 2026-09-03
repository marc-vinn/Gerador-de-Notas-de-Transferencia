"""
Domain Entities and State Enums for Stock Transfer Decision Engine (Option C).
Adheres strictly to Domain-Driven Design (DDD) invariants and Fail-Fast principles.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any

class TransferState(str, Enum):
    """
    Mutually exclusive Domain States for stock evaluation across Branch and Matrix units.
    """
    TRANSFERENCIA_NORMAL_APROVADA = "TRANSFERENCIA_NORMAL_APROVADA"
    REMOVIDO_MATRIZ_SEM_SALDO = "REMOVIDO_MATRIZ_SEM_SALDO"
    FILIAL_E_MATRIZ_ESTAVEIS = "FILIAL_E_MATRIZ_ESTAVEIS"
    TRANSFERENCIA_INVERSA_APROVADA = "TRANSFERENCIA_INVERSA_APROVADA"
    RUPTURA_CRITICA_AMBAS = "RUPTURA_CRITICA_AMBAS"

    @property
    def label(self) -> str:
        labels = {
            self.TRANSFERENCIA_NORMAL_APROVADA: "Transferência Normal Aprovada (Matriz → Filial)",
            self.REMOVIDO_MATRIZ_SEM_SALDO: "Removido da Transferência (Matriz sem Saldo Seguro)",
            self.FILIAL_E_MATRIZ_ESTAVEIS: "Ambas as Unidades Estáveis (Estoque Suficiente)",
            self.TRANSFERENCIA_INVERSA_APROVADA: "Transferência Inversa Aprovada (Filial → Matriz)",
            self.RUPTURA_CRITICA_AMBAS: "Ruptura Crítica (Déficit em Ambas as Unidades)"
        }
        return labels.get(self, self.value)


@dataclass
class TransferDecisionItem:
    sku: str
    description: str
    state: TransferState
    quantity: float
    unit_price: float
    total_price: float
    reason: str
    need_purchase: bool = False
    
    # Detailed branch metrics
    branch_sales_week: float = 0.0
    branch_stock: float = 0.0
    branch_demand_month: float = 0.0
    branch_balance: float = 0.0
    
    # Detailed matrix metrics
    matrix_sales_month: float = 0.0
    matrix_stock: float = 0.0
    matrix_balance: float = 0.0

    # Fiscal metadata
    ean: str = ""
    ncm: str = ""
    cfop: str = ""
    unit: str = ""

    def __post_init__(self):
        self.sku = str(self.sku).strip()
        self.description = str(self.description).strip()
        self.quantity = max(0.0, float(self.quantity))
        self.unit_price = max(0.0, float(self.unit_price))
        self.total_price = round(self.quantity * self.unit_price, 2) if self.total_price == 0.0 else round(float(self.total_price), 2)
        
        if not self.sku:
            raise ValueError("SKU do produto não pode ser vazio.")
        if not self.description:
            raise ValueError("Descrição do produto não pode ser vazia.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sku": self.sku,
            "code": self.sku,
            "description": self.description,
            "state": self.state.value,
            "state_label": self.state.label,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "reason": self.reason,
            "need_purchase": self.need_purchase,
            "branch_sales_week": self.branch_sales_week,
            "branch_stock": self.branch_stock,
            "branch_demand_month": self.branch_demand_month,
            "branch_balance": self.branch_balance,
            "matrix_sales_month": self.matrix_sales_month,
            "matrix_stock": self.matrix_stock,
            "matrix_balance": self.matrix_balance,
            "ean": self.ean,
            "ncm": self.ncm,
            "cfop": self.cfop,
            "unit": self.unit
        }


@dataclass
class StockAnalysisResult:
    approved_normal: List[TransferDecisionItem] = field(default_factory=list)
    removed_items: List[TransferDecisionItem] = field(default_factory=list)
    purchase_alerts: List[TransferDecisionItem] = field(default_factory=list)
    approved_reverse: List[TransferDecisionItem] = field(default_factory=list)

    @property
    def summary(self) -> Dict[str, Any]:
        total_normal_qty = sum(item.quantity for item in self.approved_normal)
        total_normal_value = round(sum(item.total_price for item in self.approved_normal), 2)
        
        total_reverse_qty = sum(item.quantity for item in self.approved_reverse)
        total_reverse_value = round(sum(item.total_price for item in self.approved_reverse), 2)

        return {
            "normal_items_count": len(self.approved_normal),
            "normal_total_quantity": total_normal_qty,
            "normal_total_value": total_normal_value,
            "removed_items_count": len(self.removed_items),
            "purchase_alerts_count": len(self.purchase_alerts),
            "reverse_items_count": len(self.approved_reverse),
            "reverse_total_quantity": total_reverse_qty,
            "reverse_total_value": total_reverse_value
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": True,
            "summary": self.summary,
            "approved_normal": [item.to_dict() for item in self.approved_normal],
            "removed_items": [item.to_dict() for item in self.removed_items],
            "purchase_alerts": [item.to_dict() for item in self.purchase_alerts],
            "approved_reverse": [item.to_dict() for item in self.approved_reverse]
        }
