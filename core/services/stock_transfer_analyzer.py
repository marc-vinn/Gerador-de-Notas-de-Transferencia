"""
Core Service: Stock Transfer Decision Engine (Option C).
Evaluates 4 spreadsheets simultaneously and classifies every product into 1 of 5 explicit Domain States.
"""
from typing import Dict, List, Optional
from ..domain.report import TransferReport
from ..domain.product import Product
from ..domain.transfer_decision import (
    TransferState,
    TransferDecisionItem,
    StockAnalysisResult
)

class StockTransferAnalyzer:
    @staticmethod
    def _build_quantity_map(report: TransferReport) -> Dict[str, float]:
        """Indexes product quantities by sanitized SKU code."""
        qty_map: Dict[str, float] = {}
        for p in report.products:
            sku = str(p.code).strip()
            qty_map[sku] = qty_map.get(sku, 0.0) + float(p.quantity)
        return qty_map

    @classmethod
    def analyze(
        cls,
        branch_sales_report: TransferReport,
        branch_stock_report: TransferReport,
        matrix_sales_report: TransferReport,
        matrix_stock_report: TransferReport
    ) -> StockAnalysisResult:
        """
        Executes the Option C Stock Decision Matrix for all items in the branch sales report.
        """
        branch_stock_map = cls._build_quantity_map(branch_stock_report)
        matrix_sales_map = cls._build_quantity_map(matrix_sales_report)
        matrix_stock_map = cls._build_quantity_map(matrix_stock_report)

        result = StockAnalysisResult()

        for prod in branch_sales_report.products:
            sku = prod.code
            desc = prod.description
            u_price = prod.unit_price

            q_venda_filial_semana = float(prod.quantity)
            e_filial = branch_stock_map.get(sku, 0.0)
            v_matriz_30d = matrix_sales_map.get(sku, 0.0)
            e_matriz = matrix_stock_map.get(sku, 0.0)

            d_filial_mes = 4.0 * q_venda_filial_semana
            b_filial = e_filial - d_filial_mes
            b_matriz = e_matriz - v_matriz_30d

            # Common base metrics for decision items
            metrics = {
                "sku": sku,
                "description": desc,
                "unit_price": u_price,
                "branch_sales_week": q_venda_filial_semana,
                "branch_stock": e_filial,
                "branch_demand_month": d_filial_mes,
                "branch_balance": b_filial,
                "matrix_sales_month": v_matriz_30d,
                "matrix_stock": e_matriz,
                "matrix_balance": b_matriz,
                "ean": prod.ean,
                "ncm": prod.ncm,
                "cfop": prod.cfop,
                "unit": prod.unit
            }

            # =========================================================================
            # Caso 1: Filial em Déficit (b_filial < 0 -> Necessita Reposição)
            # =========================================================================
            if b_filial < 0:
                necessidade_filial = abs(b_filial)

                # Subcaso 1.1: Matriz possui saldo seguro (E_matriz - necessidade >= V_matriz)
                if b_matriz >= necessidade_filial:
                    item = TransferDecisionItem(
                        state=TransferState.TRANSFERENCIA_NORMAL_APROVADA,
                        quantity=necessidade_filial,
                        total_price=round(necessidade_filial * u_price, 2),
                        reason="Transferência aprovada para cobrir demanda de 4 semanas da filial mantendo cobertura de 30 dias da matriz.",
                        need_purchase=False,
                        **metrics
                    )
                    result.approved_normal.append(item)

                # Subcaso 1.2: Matriz está positiva para si mas não suporta ceder a necessidade total
                elif b_matriz >= 0 and b_matriz < necessidade_filial:
                    item = TransferDecisionItem(
                        state=TransferState.REMOVIDO_MATRIZ_SEM_SALDO,
                        quantity=necessidade_filial,
                        total_price=round(necessidade_filial * u_price, 2),
                        reason="Matriz não possui saldo seguro de estoque para transferir sem comprometer sua própria cobertura de 30 dias.",
                        need_purchase=True,
                        **metrics
                    )
                    result.removed_items.append(item)
                    result.purchase_alerts.append(item)

                # Subcaso 1.3: Matriz também está em déficit próprio (b_matriz < 0)
                else:
                    item = TransferDecisionItem(
                        state=TransferState.RUPTURA_CRITICA_AMBAS,
                        quantity=necessidade_filial,
                        total_price=round(necessidade_filial * u_price, 2),
                        reason="Ruptura crítica: Filial e Matriz operando abaixo da demanda mensal. Compra de reposição imediata necessária.",
                        need_purchase=True,
                        **metrics
                    )
                    result.removed_items.append(item)
                    result.purchase_alerts.append(item)

            # =========================================================================
            # Caso 2: Filial Abastecida (b_filial >= 0 -> Sem Transferência Normal)
            # =========================================================================
            else:
                # Subcaso 2.1: Filial com excedente real (b_filial > 0) e Matriz em déficit (b_matriz < 0)
                if b_filial > 0 and b_matriz < 0:
                    excedente_filial = b_filial
                    deficit_matriz = abs(b_matriz)
                    qtd_reversa = min(excedente_filial, deficit_matriz)

                    reverse_item = TransferDecisionItem(
                        state=TransferState.TRANSFERENCIA_INVERSA_APROVADA,
                        quantity=qtd_reversa,
                        total_price=round(qtd_reversa * u_price, 2),
                        reason=f"Excedente de estoque na filial ({excedente_filial:.1f} un) transferível para suprir déficit da matriz ({deficit_matriz:.1f} un), preservando 100% da cobertura da filial.",
                        need_purchase=False,
                        **metrics
                    )
                    result.approved_reverse.append(reverse_item)

                    removed_info = TransferDecisionItem(
                        state=TransferState.TRANSFERENCIA_INVERSA_APROVADA,
                        quantity=0.0,
                        total_price=0.0,
                        reason="Filial com estoque suficiente para o mês; excedente identificado para transferência inversa opcional à matriz.",
                        need_purchase=False,
                        **metrics
                    )
                    result.removed_items.append(removed_info)

                # Subcaso 2.2: Ambas as unidades com estoque suficiente (b_filial >= 0 e b_matriz >= 0)
                else:
                    item = TransferDecisionItem(
                        state=TransferState.FILIAL_E_MATRIZ_ESTAVEIS,
                        quantity=0.0,
                        total_price=0.0,
                        reason="Filial e Matriz possuem estoque suficiente para cobrir suas demandas mensais. Nenhuma transferência necessária.",
                        need_purchase=False,
                        **metrics
                    )
                    result.removed_items.append(item)

        return result
