"""
Security and integrity validator for incoming sales report files.
"""
import io
import re
import unicodedata
import xlrd

class ValidationError(Exception):
    """Custom exception raised when document validation fails."""
    pass

class DocumentValidator:
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
    OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    ZIP_MAGIC = b"PK\x03\x04"

    REQUIRED_COLUMN_GROUPS = [
        ["produto", "descri"],
        ["codigo", "sku"],
        ["quant"]
    ]

    @classmethod
    def normalize_str(cls, text: str) -> str:
        if not text:
            return ""
        nfkd_form = unicodedata.normalize('NFKD', str(text))
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

    @classmethod
    def validate_file(cls, file_bytes: bytes, filename: str) -> bool:
        """
        Validates file size, file extension, magic bytes, and XLS column schema.
        Raises ValidationError if any security or format rule is violated.
        """
        if not file_bytes:
            raise ValidationError("O arquivo enviado está vazio.")

        if len(file_bytes) > cls.MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"Tamanho do arquivo excede o limite máximo de {cls.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
            )

        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext not in ["xls", "xlsx"]:
            raise ValidationError("Formato de arquivo não suportado. Envie um arquivo .xls ou .xlsx.")

        # Check binary signature / magic bytes
        if not (file_bytes.startswith(cls.OLE_MAGIC) or file_bytes.startswith(cls.ZIP_MAGIC)):
            raise ValidationError("Assinatura binária do arquivo inválida. O arquivo não é uma planilha Excel legítima.")

        # Inspect XLS header columns
        try:
            workbook = xlrd.open_workbook(
                file_contents=file_bytes,
                ignore_workbook_corruption=True
            )
            sheet = workbook.sheet_by_index(0)

            if sheet.nrows < 1:
                raise ValidationError("A planilha está vazia.")

            # Extract header values normalized
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

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitizes text fields to prevent injection or malicious control characters.
        """
        if not text:
            return ""
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(text))
        return sanitized.strip()
