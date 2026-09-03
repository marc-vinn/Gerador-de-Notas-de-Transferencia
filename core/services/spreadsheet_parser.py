"""
Spreadsheet parser service supporting both .xls (xlrd) and .xlsx (openpyxl) formats.
Supports dynamic Sales Reports and specialized Stock Reports (Col A: SKU, Col B: Desc, Col C: Estoque, Col D: Reservado).
Applies schema validation, string sanitization, and formula injection prevention.
"""
import io
import xlrd
import openpyxl
from typing import List, Tuple, Any
from ..domain.product import Product
from ..domain.report import TransferReport
from .document_validator import DocumentValidator, ValidationError

class SpreadsheetParser:
    @staticmethod
    def _format_code(val: Any) -> str:
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val).strip()

    @staticmethod
    def _sanitize_cell_value(val: Any) -> str:
        """
        Sanitizes cell string value against control characters and formula injection prefixes.
        """
        text = str(val).strip() if val is not None else ""
        text = DocumentValidator.sanitize_text(text)
        # Neutralize Excel/CSV formula injection prefixes if present at start of text
        if text.startswith(("=", "+", "-", "@", "\t", "\r")):
            text = text.lstrip("=+-@\t\r ").strip()
        return text

    @classmethod
    def _map_columns(cls, header_row: List[str]) -> Tuple[int, int, int, int, int, int]:
        desc_idx = -1
        code_idx = -1
        qty_idx = -1
        liq_idx = -1
        freight_idx = -1
        total_idx = -1

        for i, col_name in enumerate(header_row):
            norm = DocumentValidator.normalize_str(col_name)
            if "produto" in norm or "descri" in norm:
                desc_idx = i
            elif "codigo" in norm or "sku" in norm or "cod" in norm:
                code_idx = i
            elif any(k in norm for k in ["quant", "qtd", "venda", "estoque", "fisico", "saldo"]):
                qty_idx = i
            elif "liquido" in norm or norm == "valor":
                liq_idx = i
            elif "frete" in norm:
                freight_idx = i
            elif "total" in norm and total_idx == -1:
                total_idx = i

        # Fallback to positional columns if header labels are atypical
        if code_idx == -1 and len(header_row) > 0:
            code_idx = 0
        if desc_idx == -1 and len(header_row) > 1:
            desc_idx = 1
        if qty_idx == -1 and len(header_row) > 2:
            qty_idx = 2

        return desc_idx, code_idx, qty_idx, liq_idx, freight_idx, total_idx

    @classmethod
    def _parse_xls(cls, file_bytes: bytes) -> List[List[Any]]:
        workbook = xlrd.open_workbook(file_contents=file_bytes, ignore_workbook_corruption=True)
        sheet = workbook.sheet_by_index(0)
        return [sheet.row_values(r) for r in range(sheet.nrows)]

    @classmethod
    def _parse_xlsx(cls, file_bytes: bytes) -> List[List[Any]]:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=False)
        sheet = wb.active
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(list(row))
        wb.close()
        return rows

    @classmethod
    def parse(cls, file_bytes: bytes, filename: str) -> TransferReport:
        """
        Parses Sales Transfer Report mapping columns dynamically.
        """
        DocumentValidator.validate_file(file_bytes, filename, report_type="sales")

        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext == "xlsx":
            rows = cls._parse_xlsx(file_bytes)
        else:
            rows = cls._parse_xls(file_bytes)

        if not rows or len(rows) < 2:
            raise ValidationError("A planilha não contém linhas de dados suficientes para processamento.")

        header_row = [str(c or "") for c in rows[0]]
        desc_idx, code_idx, qty_idx, liq_idx, freight_idx, total_idx = cls._map_columns(header_row)

        products: List[Product] = []

        for row_vals in rows[1:]:
            raw_desc = row_vals[desc_idx] if desc_idx < len(row_vals) else ""
            raw_code = row_vals[code_idx] if code_idx < len(row_vals) else ""
            raw_qty = row_vals[qty_idx] if qty_idx < len(row_vals) else 0

            if not raw_desc or not str(raw_desc).strip():
                continue
            if not raw_code or not str(raw_code).strip():
                continue

            desc = cls._sanitize_cell_value(raw_desc)
            code = cls._sanitize_cell_value(cls._format_code(raw_code))

            if not desc or not code:
                continue

            try:
                qty = float(raw_qty)
            except (ValueError, TypeError):
                continue

            if qty <= 0:
                continue

            liq_val = 0.0
            if liq_idx != -1 and liq_idx < len(row_vals):
                try:
                    liq_val = float(row_vals[liq_idx] or 0)
                except (ValueError, TypeError):
                    liq_val = 0.0

            freight_val = 0.0
            if freight_idx != -1 and freight_idx < len(row_vals):
                try:
                    freight_val = float(row_vals[freight_idx] or 0)
                except (ValueError, TypeError):
                    freight_val = 0.0

            total_val = liq_val
            if total_val == 0.0 and total_idx != -1 and total_idx < len(row_vals):
                try:
                    total_val = float(row_vals[total_idx] or 0)
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

    @classmethod
    def parse_stock_report(cls, file_bytes: bytes, filename: str) -> TransferReport:
        """
        Parses stock report with specific schema:
        - Col A (0): SKU (Unique identifier for cross-referencing)
        - Col B (1): Descrição do Produto
        - Col C (2): Estoque Atual / Físico (Quantidade bruta)
        - Col D (3): Estoque Reservado (Vendas pendentes -> Subtraídas do estoque disponível)
        
        Available stock = max(0.0, Estoque Físico - Estoque Reservado)
        """
        DocumentValidator.validate_file(file_bytes, filename, report_type="stock")

        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext == "xlsx":
            rows = cls._parse_xlsx(file_bytes)
        else:
            rows = cls._parse_xls(file_bytes)

        if not rows or len(rows) < 1:
            raise ValidationError("A planilha de estoque não contém linhas de dados suficientes.")

        # Default positional column indices (Col A: 0, Col B: 1, Col C: 2, Col D: 3)
        sku_idx = 0
        desc_idx = 1
        stock_idx = 2
        reserved_idx = 3

        # Determine header row if present and map columns dynamically
        start_row = 0
        first_row_txt = " ".join(str(c or "").lower() for c in rows[0])
        if any(keyword in first_row_txt for keyword in ["sku", "codigo", "código", "descri", "estoque", "reserva", "produto"]):
            start_row = 1
            header_row = [DocumentValidator.normalize_str(str(c or "")) for c in rows[0]]
            for i, h in enumerate(header_row):
                if "reserv" in h:
                    reserved_idx = i
                elif "estoque" in h or "fisico" in h or "saldo" in h:
                    stock_idx = i
                elif "produto" in h or "descri" in h:
                    desc_idx = i
                elif "sku" in h or "codigo" in h:
                    sku_idx = i
        elif len(rows) > 1:
            try:
                float(rows[0][2])
            except (ValueError, TypeError, IndexError):
                start_row = 1

        products: List[Product] = []

        for row_vals in rows[start_row:]:
            if not row_vals or len(row_vals) < 2:
                continue

            raw_code = row_vals[sku_idx] if sku_idx < len(row_vals) else ""
            raw_desc = row_vals[desc_idx] if desc_idx < len(row_vals) else ""
            raw_stock = row_vals[stock_idx] if stock_idx < len(row_vals) else 0.0
            raw_reserved = row_vals[reserved_idx] if reserved_idx < len(row_vals) else 0.0

            if not raw_code or not str(raw_code).strip():
                continue

            code = cls._sanitize_cell_value(cls._format_code(raw_code))
            desc = cls._sanitize_cell_value(raw_desc) or f"Produto {code}"

            if not code:
                continue

            try:
                stock_qty = float(raw_stock or 0.0)
            except (ValueError, TypeError):
                stock_qty = 0.0

            try:
                reserved_qty = float(raw_reserved or 0.0)
            except (ValueError, TypeError):
                reserved_qty = 0.0

            # Deduct reserved units: Available stock cannot be negative
            available_qty = max(0.0, stock_qty - reserved_qty)

            products.append(Product(
                code=code,
                description=desc,
                quantity=available_qty,
                unit_price=0.0,
                total_price=0.0,
                freight_price=0.0
            ))

        if not products:
            raise ValidationError("Nenhum produto válido foi encontrado na planilha de estoque.")

        return TransferReport(filename=filename, products=products)
