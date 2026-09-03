"""
Access Key (Chave de Acesso) generator and Modulo 11 check-digit calculation for NFe 4.00.
"""
from typing import Tuple

class ChaveAcessoGenerator:
    @staticmethod
    def calculate_mod11(base_key: str) -> str:
        """
        Calculates Modulo 11 check digit (cDV) for SEFAZ 44-digit NFe access key.
        Weights cycle through 2, 3, 4, 5, 6, 7, 8, 9 from right to left.
        """
        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        total = 0
        for i, char in enumerate(reversed(base_key)):
            weight = weights[i % len(weights)]
            total += int(char) * weight

        remainder = total % 11
        cdv = 0 if remainder in [0, 1] else 11 - remainder
        return str(cdv)

    @classmethod
    def generate(
        cls,
        uf_ibge_code: str,
        date_aamm: str,
        cnpj: str,
        mod: str = "55",
        serie: str = "1",
        number: str = "1",
        tp_emis: str = "1",
        cnf: str = "00000000"
    ) -> Tuple[str, str]:
        """
        Generates 44-digit NFe Chave de Acesso and Modulo 11 check digit (cDV).
        Structure: cUF(2) + AAMM(4) + CNPJ(14) + mod(2) + serie(3) + nNF(9) + tpEmis(1) + cNF(8) + cDV(1)
        """
        uf_fmt = str(uf_ibge_code).zfill(2)
        aamm_fmt = str(date_aamm).zfill(4)
        cnpj_fmt = str(cnpj).zfill(14)
        mod_fmt = str(mod).zfill(2)
        serie_fmt = str(serie).zfill(3)
        nnf_fmt = str(number).zfill(9)
        tp_emis_fmt = str(tp_emis)
        cnf_fmt = str(cnf).zfill(8)

        base_key = f"{uf_fmt}{aamm_fmt}{cnpj_fmt}{mod_fmt}{serie_fmt}{nnf_fmt}{tp_emis_fmt}{cnf_fmt}"
        cdv = cls.calculate_mod11(base_key)
        full_key = f"{base_key}{cdv}"

        return full_key, cdv
