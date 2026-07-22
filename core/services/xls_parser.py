"""
Parser service for extracting sales report items from XLS spreadsheets.
"""
import xlrd
from typing import List
from ..domain.product import Product
from ..domain.report import TransferReport
from .document_validator import DocumentValidator, ValidationError

class XLSParser:
    @staticmethod
    def _format_code(val) -> str:
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val).strip()

    @classmethod
    def parse(cls, file_bytes: bytes, filename: str) -> TransferReport:
        """
        Validates and parses file bytes into a TransferReport containing Product entities.
        """
        # Validate security and schema first
        DocumentValidator.validate_file(file_bytes, filename)

        workbook = xlrd.open_workbook(
            file_contents=file_bytes,
            ignore_workbook_corruption=True
        )
        sheet = workbook.sheet_by_index(0)

        header_row = [DocumentValidator.normalize_str(cell) for cell in sheet.row_values(0)]

        # Map column indices
        desc_idx = -1
        code_idx = -1
        qty_idx = -1
        liq_idx = -1
        freight_idx = -1
        total_idx = -1

        for i, col_name in enumerate(header_row):
            if "produto" in col_name or "descri" in col_name:
                desc_idx = i
            elif "codigo" in col_name or "sku" in col_name:
                code_idx = i
            elif "quant" in col_name:
                qty_idx = i
            elif "liquido" in col_name or col_name == "valor":
                liq_idx = i
            elif "frete" in col_name:
                freight_idx = i
            elif "total" in col_name and total_idx == -1:
                total_idx = i

        if desc_idx == -1 or code_idx == -1 or qty_idx == -1:
            raise ValidationError("Não foi possível mapear as colunas obrigatórias do relatório.")

        products: List[Product] = []

        for r in range(1, sheet.nrows):
            row_vals = sheet.row_values(r)
            
            raw_desc = row_vals[desc_idx] if desc_idx < len(row_vals) else ""
            raw_code = row_vals[code_idx] if code_idx < len(row_vals) else ""
            raw_qty = row_vals[qty_idx] if qty_idx < len(row_vals) else 0

            # Skip header total summary rows or empty rows
            if not raw_desc or not str(raw_desc).strip():
                continue
            if not raw_code or not str(raw_code).strip():
                continue

            desc = DocumentValidator.sanitize_text(str(raw_desc))
            code = DocumentValidator.sanitize_text(cls._format_code(raw_code))

            try:
                qty = float(raw_qty)
            except (ValueError, TypeError):
                continue

            if qty <= 0:
                continue

            liq_val = 0.0
            if liq_idx != -1 and liq_idx < len(row_vals):
                try:
                    liq_val = float(row_vals[liq_idx])
                except (ValueError, TypeError):
                    liq_val = 0.0

            freight_val = 0.0
            if freight_idx != -1 and freight_idx < len(row_vals):
                try:
                    freight_val = float(row_vals[freight_idx])
                except (ValueError, TypeError):
                    freight_val = 0.0

            total_val = liq_val
            if total_val == 0.0 and total_idx != -1 and total_idx < len(row_vals):
                try:
                    total_val = float(row_vals[total_idx])
                except (ValueError, TypeError):
                    total_val = 0.0

            unit_price = round(total_val / qty, 4) if qty > 0 else 0.0

            product = Product(
                code=code,
                description=desc,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_val,
                freight_price=freight_val
            )
            products.append(product)

        if not products:
            raise ValidationError("Nenhum produto válido foi encontrado no relatório enviado.")

        return TransferReport(filename=filename, products=products)
