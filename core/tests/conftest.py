"""
Pytest configuration and test environment setup.
Defines required environment variables for fiscal and emitter tests.
"""
import os
import pytest

# Configure mock environment for testing emitter domain loading
os.environ.setdefault("COMPANY_CNPJ", "40484774000150")
os.environ.setdefault("COMPANY_NAME", "ARBORETHO IMPORTS LTDA")
os.environ.setdefault("COMPANY_TRADE_NAME", "ARBORETHO")
os.environ.setdefault("COMPANY_IE", "108282910")
os.environ.setdefault("COMPANY_CRT", "1")
os.environ.setdefault("COMPANY_STREET", "RUA 19")
os.environ.setdefault("COMPANY_NUMBER", "230")
os.environ.setdefault("COMPANY_NEIGHBORHOOD", "SETOR SANTO ANTONIO")
os.environ.setdefault("COMPANY_CITY_CODE", "5208707")
os.environ.setdefault("COMPANY_CITY_NAME", "GOIANIA")
os.environ.setdefault("COMPANY_UF", "GO")
os.environ.setdefault("COMPANY_CEP", "74853320")
os.environ.setdefault("COMPANY_PHONE", "6230000000")
