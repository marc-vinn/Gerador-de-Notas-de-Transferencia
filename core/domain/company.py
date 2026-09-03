"""
Domain entities representing Company and Address information for NFe processing.
Enforces Domain-Driven Design (DDD) invariants and Fail-Fast validation.
"""
import os
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .uf import UF, InvalidUFError, get_ibge_uf_code

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

    def __post_init__(self):
        self.street = str(self.street).strip()
        self.number = str(self.number).strip()
        self.complement = str(self.complement).strip()
        self.neighborhood = str(self.neighborhood).strip()
        self.city_code = re.sub(r"\D", "", str(self.city_code))
        self.city_name = str(self.city_name).strip()
        
        # Strict Fail-Fast validation on UF if provided
        raw_uf = str(self.uf).strip()
        if raw_uf:
            self.uf = UF.from_str(raw_uf).value
        else:
            self.uf = ""

        self.cep = re.sub(r"\D", "", str(self.cep))
        self.country_code = str(self.country_code).strip() or "1058"
        self.country_name = str(self.country_name).strip() or "Brasil"
        self.phone = re.sub(r"\D", "", str(self.phone))

    @property
    def ibge_uf_code(self) -> str:
        """
        Returns the 2-digit IBGE code for the address UF.
        Raises InvalidUFError if UF is not defined (Fail-Fast).
        """
        if not self.uf:
            raise InvalidUFError("Endereço sem UF definida. A UF é obrigatória para operações fiscais da NFe.")
        return get_ibge_uf_code(self.uf)


@dataclass
class CompanyInfo:
    cnpj: str = field(default_factory=lambda: os.getenv("COMPANY_CNPJ", ""))
    name: str = field(default_factory=lambda: os.getenv("COMPANY_NAME", ""))
    trade_name: str = field(default_factory=lambda: os.getenv("COMPANY_TRADE_NAME", ""))
    ie: str = field(default_factory=lambda: os.getenv("COMPANY_IE", ""))
    crt: str = field(default_factory=lambda: os.getenv("COMPANY_CRT", ""))
    address: AddressInfo = field(default_factory=AddressInfo)

    def __post_init__(self):
        self.cnpj = re.sub(r"\D", "", str(self.cnpj))
        self.name = str(self.name).strip()
        self.trade_name = str(self.trade_name).strip() or self.name
        self.ie = re.sub(r"\D", "", str(self.ie))
        self.crt = str(self.crt).strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any], fallback: Optional["CompanyInfo"] = None) -> "CompanyInfo":
        """
        Creates a CompanyInfo instance from a dictionary (e.g. request parameters).
        Uses fallback if fields are omitted.
        """
        fb_addr = fallback.address if fallback else AddressInfo()
        fb_company = fallback if fallback else CompanyInfo()

        addr = AddressInfo(
            street=data.get("street") or data.get("recipient_street") or fb_addr.street,
            number=data.get("number") or data.get("recipient_number") or fb_addr.number,
            complement=data.get("complement") or data.get("recipient_complement") or fb_addr.complement,
            neighborhood=data.get("neighborhood") or data.get("bairro") or data.get("recipient_bairro") or fb_addr.neighborhood,
            city_code=data.get("city_code") or data.get("recipient_city_code") or fb_addr.city_code,
            city_name=data.get("city_name") or data.get("cityName") or data.get("recipient_city_name") or fb_addr.city_name,
            uf=data.get("uf") or data.get("recipient_uf") or fb_addr.uf,
            cep=data.get("cep") or data.get("recipient_cep") or fb_addr.cep,
            phone=data.get("phone") or data.get("recipient_phone") or fb_addr.phone,
        )

        return cls(
            cnpj=data.get("cnpj") or data.get("recipient_cnpj") or fb_company.cnpj,
            name=data.get("name") or data.get("recipient_name") or fb_company.name,
            trade_name=data.get("trade_name") or data.get("recipient_trade_name") or fb_company.trade_name,
            ie=data.get("ie") or data.get("recipient_ie") or fb_company.ie,
            crt=data.get("crt") or fb_company.crt,
            address=addr
        )
