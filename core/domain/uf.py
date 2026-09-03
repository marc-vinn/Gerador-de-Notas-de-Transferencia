"""
Domain Value Object and official IBGE codes for Brazilian Federative Units (UF).
Enforces Domain-Driven Design (DDD) invariants and Fail-Fast validation.
"""
from enum import Enum
from typing import Dict, List, Optional

class InvalidUFError(ValueError):
    """Domain exception raised when an invalid UF abbreviation or code is supplied."""
    pass

UF_IBGE_CODES: Dict[str, str] = {
    "RO": "11",
    "AC": "12",
    "AM": "13",
    "RR": "14",
    "PA": "15",
    "AP": "16",
    "TO": "17",
    "MA": "21",
    "PI": "22",
    "CE": "23",
    "RN": "24",
    "PB": "25",
    "PE": "26",
    "AL": "27",
    "SE": "28",
    "BA": "29",
    "MG": "31",
    "ES": "32",
    "RJ": "33",
    "SP": "35",
    "PR": "41",
    "SC": "42",
    "RS": "43",
    "MS": "50",
    "MT": "51",
    "GO": "52",
    "DF": "53"
}

class UF(str, Enum):
    """
    Value Object Enum representing the 27 official Brazilian Federative Units.
    Guarantees domain consistency and prevents silent corruption or invalid state defaults.
    """
    RO = "RO"
    AC = "AC"
    AM = "AM"
    RR = "RR"
    PA = "PA"
    AP = "AP"
    TO = "TO"
    MA = "MA"
    PI = "PI"
    CE = "CE"
    RN = "RN"
    PB = "PB"
    PE = "PE"
    AL = "AL"
    SE = "SE"
    BA = "BA"
    MG = "MG"
    ES = "ES"
    RJ = "RJ"
    SP = "SP"
    PR = "PR"
    SC = "SC"
    RS = "RS"
    MS = "MS"
    MT = "MT"
    GO = "GO"
    DF = "DF"

    @property
    def ibge_code(self) -> str:
        """Returns the official 2-digit IBGE code for this Federative Unit."""
        return UF_IBGE_CODES[self.value]

    @classmethod
    def valid_ufs(cls) -> List[str]:
        """Returns a sorted list of all valid 2-letter UF codes."""
        return sorted([u.value for u in cls])

    @classmethod
    def from_str(cls, value: Optional[str]) -> "UF":
        """
        Parses and validates a UF string strictly following Fail-Fast principle.
        Raises InvalidUFError if the string is empty, not a string, or not a valid UF.
        """
        if not value or not isinstance(value, str):
            raise InvalidUFError("Sigla de UF não pode ser vazia ou nula.")
        
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid_list = ", ".join(cls.valid_ufs())
            raise InvalidUFError(
                f"Sigla de UF inválida: '{value}'. Deve ser uma das 27 UFs válidas brasileiras: {valid_list}"
            )

def get_ibge_uf_code(uf: str) -> str:
    """
    Returns the 2-digit IBGE code for a given Brazilian UF abbreviation (e.g. 'SP' -> '35').
    Enforces Fail-Fast: raises InvalidUFError immediately if input is invalid or unrecognized.
    """
    uf_obj = UF.from_str(uf)
    return uf_obj.ibge_code
