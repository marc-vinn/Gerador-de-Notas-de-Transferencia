"""
Domain entities and defaults for NFe XML generation.
Supports dynamic configuration via environment variables.
"""
import os
from dataclasses import dataclass, field

@dataclass
class AddressInfo:
    street: str = field(default_factory=lambda: os.getenv("COMPANY_STREET", "RUA 19"))
    number: str = field(default_factory=lambda: os.getenv("COMPANY_NUMBER", "230"))
    complement: str = field(default_factory=lambda: os.getenv("COMPANY_COMPLEMENT", "QUADRA 46, LOTE 08 E"))
    neighborhood: str = field(default_factory=lambda: os.getenv("COMPANY_NEIGHBORHOOD", "JD SANTO ANTONIO"))
    city_code: str = field(default_factory=lambda: os.getenv("COMPANY_CITY_CODE", "5208707"))
    city_name: str = field(default_factory=lambda: os.getenv("COMPANY_CITY_NAME", "Goiania"))
    uf: str = field(default_factory=lambda: os.getenv("COMPANY_UF", "GO"))
    cep: str = field(default_factory=lambda: os.getenv("COMPANY_CEP", "74853320"))
    country_code: str = field(default_factory=lambda: os.getenv("COMPANY_COUNTRY_CODE", "1058"))
    country_name: str = field(default_factory=lambda: os.getenv("COMPANY_COUNTRY_NAME", "Brasil"))
    phone: str = field(default_factory=lambda: os.getenv("COMPANY_PHONE", "62992544599"))

@dataclass
class CompanyInfo:
    cnpj: str = field(default_factory=lambda: os.getenv("COMPANY_CNPJ", "40484774000150"))
    name: str = field(default_factory=lambda: os.getenv("COMPANY_NAME", "ARBORETHO IMPORTS LTDA"))
    trade_name: str = field(default_factory=lambda: os.getenv("COMPANY_TRADE_NAME", "ARBORETHO"))
    ie: str = field(default_factory=lambda: os.getenv("COMPANY_IE", "108282910"))
    crt: str = field(default_factory=lambda: os.getenv("COMPANY_CRT", "1"))  # 1 = Simples Nacional
    address: AddressInfo = field(default_factory=AddressInfo)

# Default Issuer and Recipient details (as specified: emitente e destinatário são iguais)
DEFAULT_EMITTER = CompanyInfo()
DEFAULT_RECIPIENT = CompanyInfo()
