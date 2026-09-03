"""
Domain exports and compatibility layer for NFe XML generation.
All company defaults are loaded dynamically from environment variables.
"""
from .company import AddressInfo, CompanyInfo
from .uf import UF_IBGE_CODES, get_ibge_uf_code

DEFAULT_EMITTER = CompanyInfo()
DEFAULT_RECIPIENT = CompanyInfo()

__all__ = [
    "AddressInfo",
    "CompanyInfo",
    "DEFAULT_EMITTER",
    "DEFAULT_RECIPIENT",
    "UF_IBGE_CODES",
    "get_ibge_uf_code"
]
