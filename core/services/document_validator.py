"""
Security and integrity validator for incoming sales and stock report files.
Protects against oversized uploads, malicious extensions, invalid magic bytes, and XXE.
Flexible schema validation accepting both Sales and Stock spreadsheets.
"""
import io
import re
import unicodedata
import xlrd
import openpyxl

class ValidationError(Exception):
    """Custom exception raised when document validation fails."""
    pass

class DocumentValidator:
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
    OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    ZIP_MAGIC = b"PK\x03\x04"

    REQUIRED_COLUMN_GROUPS = [
        ["produto", "descri", "item", "nome", "sku", "codigo", "código"],
        ["quant", "qtd", "venda", "estoque", "saldo", "fisico", "físico", "unid", "total", "valor"]
    ]

    @classmethod
    def normalize_str(cls, text: str) -> str:
        if not text:
            return ""
        nfkd_form = unicodedata.normalize('NFKD', str(text))
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitizes text fields to prevent injection or malicious control characters.
        """
        if not text:
            return ""
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(text))
        return sanitized.strip()

    @classmethod
    def validate_file(cls, file_bytes: bytes, filename: str, report_type: str = "any") -> bool:
        """
        Validates file size, file extension, magic bytes, and spreadsheet column schema.
        Raises ValidationError if any security or format rule is violated.
        """
        if not file_bytes:
            raise ValidationError("O arquivo enviado está vazio.")

        if len(file_bytes) > cls.MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"Tamanho do arquivo excede o limite máximo de {cls.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
            )

        clean_filename = cls.sanitize_text(filename)
        ext = clean_filename.lower().split(".")[-1] if "." in clean_filename else ""
        if ext not in ["xls", "xlsx"]:
            raise ValidationError("Formato de arquivo não suportado. Envie um arquivo .xls ou .xlsx.")

        # Check binary signature / magic bytes
        if ext == "xls" and not file_bytes.startswith(cls.OLE_MAGIC):
            raise ValidationError("Assinatura binária do arquivo .xls inválida. O arquivo não é uma planilha Excel legítima.")
        elif ext == "xlsx" and not file_bytes.startswith(cls.ZIP_MAGIC):
            raise ValidationError("Assinatura binária do arquivo .xlsx inválida. O arquivo não é um documento OpenXML legítimo.")
        elif not (file_bytes.startswith(cls.OLE_MAGIC) or file_bytes.startswith(cls.ZIP_MAGIC)):
            raise ValidationError("Assinatura binária do arquivo inválida.")

        # Inspect headers
        try:
            if ext == "xlsx":
                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
                sheet = wb.active
                first_row = next(sheet.iter_rows(values_only=True), None)
                wb.close()
                if not first_row:
                    raise ValidationError("A planilha está vazia.")
                header_row = [cls.normalize_str(str(cell or "")) for cell in first_row]
            else:
                workbook = xlrd.open_workbook(file_contents=file_bytes, ignore_workbook_corruption=True)
                sheet = workbook.sheet_by_index(0)
                if sheet.nrows < 1:
                    raise ValidationError("A planilha está vazia.")
                header_row = [cls.normalize_str(cell) for cell in sheet.row_values(0)]

            for kw_group in cls.REQUIRED_COLUMN_GROUPS:
                col_found = any(any(kw in h for kw in kw_group) for h in header_row if h)
                if not col_found:
                    raise ValidationError(
                        f"Estrutura do relatório inválida. Coluna obrigatória ({'/'.join(kw_group)}) não foi encontrada."
                    )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Erro ao processar estrutura da planilha Excel: {str(e)}")

        return True
