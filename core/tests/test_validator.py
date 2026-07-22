import pytest
from core.services.document_validator import DocumentValidator, ValidationError

def test_validate_empty_file():
    with pytest.raises(ValidationError, match="vazio"):
        DocumentValidator.validate_file(b"", "report.xls")

def test_validate_invalid_extension():
    with pytest.raises(ValidationError, match="Formato"):
        DocumentValidator.validate_file(b"content", "report.pdf")

def test_validate_invalid_magic_bytes():
    with pytest.raises(ValidationError, match="Assinatura binária"):
        DocumentValidator.validate_file(b"NOT_OLE_OR_ZIP", "report.xls")

def test_sanitize_text():
    raw = "<script>alert('xss')</script>\x00Text"
    sanitized = DocumentValidator.sanitize_text(raw)
    assert "\x00" not in sanitized
    assert "Text" in sanitized
