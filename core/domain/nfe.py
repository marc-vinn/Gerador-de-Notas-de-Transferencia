"""
Domain entities and defaults for NFe XML generation.
All company fields are loaded exclusively from environment variables.
No hardcoded example data — fields default to empty strings when
the corresponding env var is not set.
"""
import os
from dataclasses import dataclass, field

@dataclass
class AddressInfo:
    street: str = field(default_factory=lambda: os.getenv("COMPANY_STREET", ""))
    number: str = field(default_factory=lambda: os.getenv("COMPANY_NUMBER", ""))
    complement: str = field(default_factory=lambda: os.getenv("COMPANY_COMPLEMENT", ""))
    neighborhood: str = field(default_factory=lambda: os.getenv("COMPANY_NEIGHBORHOOD", ""))
    city_code: str = field(default_factory=lambda: os.getenv("COMPANY_CITY_CODE", ""))
    city_name: str = field(default_factory=lambda: os.getenv("COMPANY_CITY_NAME", ""))
    uf: str = field(default_factory=lambda: os.getenv("COMPANY_UF", ""))
    cep: str = field(default_factory=lambda: os.getenv("COMPANY_CEP", ""))
    country_code: str = field(default_factory=lambda: os.getenv("COMPANY_COUNTRY_CODE", "1058"))
    country_name: str = field(default_factory=lambda: os.getenv("COMPANY_COUNTRY_NAME", "Brasil"))
    phone: str = field(default_factory=lambda: os.getenv("COMPANY_PHONE", ""))

@dataclass
class CompanyInfo:
    cnpj: str = field(default_factory=lambda: os.getenv("COMPANY_CNPJ", ""))
    name: str = field(default_factory=lambda: os.getenv("COMPANY_NAME", ""))
    trade_name: str = field(default_factory=lambda: os.getenv("COMPANY_TRADE_NAME", ""))
    ie: str = field(default_factory=lambda: os.getenv("COMPANY_IE", ""))
    crt: str = field(default_factory=lambda: os.getenv("COMPANY_CRT", ""))
    address: AddressInfo = field(default_factory=AddressInfo)

# Default Issuer and Recipient details — populated from environment variables only
DEFAULT_EMITTER = CompanyInfo()
DEFAULT_RECIPIENT = CompanyInfo()
