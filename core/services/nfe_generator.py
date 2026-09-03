"""
High-level service for generating standard NFe 4.00 XML from TransferReport entities.
Adheres to Clean Architecture and delegates construction to NFeXmlBuilder.
"""
from typing import Optional
from ..domain.report import TransferReport
from ..domain.company import CompanyInfo
from ..domain.nfe import DEFAULT_EMITTER, DEFAULT_RECIPIENT
from .nfe_builder.nfe_xml_builder import NFeXmlBuilder

class NFeGenerator:
    @classmethod
    def generate_xml(
        cls,
        report: TransferReport,
        emitter: CompanyInfo = DEFAULT_EMITTER,
        recipient: CompanyInfo = DEFAULT_RECIPIENT,
        n_nf: Optional[int] = None,
        serie: int = 1
    ) -> str:
        """
        Generates standard formatted NFe 4.00 XML string.
        When n_nf is None, number and access key fields remain empty for ERP automatic assignment.
        """
        builder = NFeXmlBuilder(
            report=report,
            emitter=emitter,
            recipient=recipient,
            n_nf=n_nf,
            serie=serie
        )
        return builder.build_xml_string()
