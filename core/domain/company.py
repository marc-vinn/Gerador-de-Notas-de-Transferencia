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

    def is_valid_for_nfe(self, role_label: str = "Empresa") -> tuple[bool, str]:
        """Validates that mandatory fiscal fields are present for NF-e generation."""
        if not self.cnpj or len(self.cnpj) != 14:
            return False, f"{role_label} com CNPJ inválido ou não informado (necessário 14 dígitos)."
        if not self.name:
            return False, f"{role_label} sem Razão Social / Nome informado."
        if not self.address or not self.address.uf:
            return False, f"{role_label} sem UF definida. A UF é obrigatória para operações fiscais da NFe."
        return True, ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any], prefix: str = "", fallback: Optional["CompanyInfo"] = None) -> "CompanyInfo":
        """
        Creates a CompanyInfo instance from a dictionary (e.g. request parameters).
        Supports optional prefix (e.g. 'emitter' or 'recipient').
        Uses fallback if fields are omitted.
        """
        fb_addr = fallback.address if fallback else AddressInfo()
        fb_company = fallback if fallback else CompanyInfo()

        p = f"{prefix}_" if prefix else ""

        street = data.get(f"{p}street") or (data.get("street") if not prefix else None) or (data.get("recipient_street") if not prefix else None) or fb_addr.street
        number = data.get(f"{p}number") or (data.get("number") if not prefix else None) or (data.get("recipient_number") if not prefix else None) or fb_addr.number
        complement = data.get(f"{p}complement") or (data.get("complement") if not prefix else None) or (data.get("recipient_complement") if not prefix else None) or fb_addr.complement
        bairro = data.get(f"{p}bairro") or data.get(f"{p}neighborhood") or (data.get("bairro") if not prefix else None) or (data.get("neighborhood") if not prefix else None) or (data.get("recipient_bairro") if not prefix else None) or fb_addr.neighborhood
        city_code = data.get(f"{p}city_code") or data.get(f"{p}cityCode") or (data.get("city_code") if not prefix else None) or (data.get("cityCode") if not prefix else None) or (data.get("recipient_city_code") if not prefix else None) or fb_addr.city_code
        city_name = data.get(f"{p}city_name") or data.get(f"{p}cityName") or (data.get("city_name") if not prefix else None) or (data.get("cityName") if not prefix else None) or (data.get("recipient_city_name") if not prefix else None) or fb_addr.city_name
        uf = data.get(f"{p}uf") or (data.get("uf") if not prefix else None) or (data.get("recipient_uf") if not prefix else None) or fb_addr.uf
        cep = data.get(f"{p}cep") or (data.get("cep") if not prefix else None) or (data.get("recipient_cep") if not prefix else None) or fb_addr.cep
        phone = data.get(f"{p}phone") or (data.get("phone") if not prefix else None) or (data.get("recipient_phone") if not prefix else None) or fb_addr.phone

        addr = AddressInfo(
            street=street,
            number=number,
            complement=complement,
            neighborhood=bairro,
            city_code=city_code,
            city_name=city_name,
            uf=uf,
            cep=cep,
            phone=phone,
        )

        cnpj = data.get(f"{p}cnpj") or (data.get("cnpj") if not prefix else None) or (data.get("recipient_cnpj") if not prefix else None) or fb_company.cnpj
        name = data.get(f"{p}name") or (data.get("name") if not prefix else None) or (data.get("recipient_name") if not prefix else None) or fb_company.name
        trade_name = data.get(f"{p}trade_name") or data.get(f"{p}tradeName") or (data.get("trade_name") if not prefix else None) or (data.get("recipient_trade_name") if not prefix else None) or fb_company.trade_name
        ie = data.get(f"{p}ie") or (data.get("ie") if not prefix else None) or (data.get("recipient_ie") if not prefix else None) or fb_company.ie
        crt = data.get(f"{p}crt") or (data.get("crt") if not prefix else None) or fb_company.crt

        return cls(
            cnpj=cnpj,
            name=name,
            trade_name=trade_name,
            ie=ie,
            crt=crt,
            address=addr
        )

