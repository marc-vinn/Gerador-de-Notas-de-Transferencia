"""
Modular Builder for NFe 4.00 XML generation adhering to SOLID Single Responsibility Principle.
"""
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from xml.dom import minidom

from ...domain.company import CompanyInfo
from ...domain.product import Product
from ...domain.report import TransferReport
from ..tax_calculator import TaxCalculator
from .chave_acesso import ChaveAcessoGenerator

class NFeXmlBuilder:
    def __init__(
        self,
        report: TransferReport,
        emitter: CompanyInfo,
        recipient: CompanyInfo,
        n_nf: Optional[int] = None,
        serie: int = 1
    ):
        self.report = report
        self.emitter = emitter
        self.recipient = recipient
        self.n_nf = n_nf
        self.serie = serie

        # Timezone BRT (-03:00)
        self.now = datetime.now(timezone(timedelta(hours=-3)))
        self.dh_emi = self.now.strftime("%Y-%m-%dT%H:%M:%S-03:00")
        self.dh_sai = (self.now + timedelta(seconds=21)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
        self.date_aamm = self.now.strftime("%y%m")
        self.cnf = str(random.randint(10000000, 99999999))
        self.uf_code = self.emitter.address.ibge_uf_code

        # Chave de Acesso
        if self.n_nf is not None:
            self.ch_nfe, self.cdv = ChaveAcessoGenerator.generate(
                uf_ibge_code=self.uf_code,
                date_aamm=self.date_aamm,
                cnpj=self.emitter.cnpj,
                mod="55",
                serie=str(self.serie),
                number=str(self.n_nf),
                tp_emis="1",
                cnf=self.cnf
            )
        else:
            self.ch_nfe = ""
            self.cdv = ""

        # Precalculate taxes
        self.tax_summary = TaxCalculator.calculate_invoice_summary(self.report.products)

    def _build_ide(self, parent: ET.Element) -> ET.Element:
        ide = ET.SubElement(parent, "ide")
        ET.SubElement(ide, "cUF").text = self.uf_code
        ET.SubElement(ide, "cNF").text = self.cnf
        ET.SubElement(ide, "natOp").text = "Transferencia de mercadoria SAIDA"
        ET.SubElement(ide, "mod").text = "55"
        ET.SubElement(ide, "serie").text = str(self.serie)
        ET.SubElement(ide, "nNF").text = str(self.n_nf) if self.n_nf is not None else ""
        ET.SubElement(ide, "dhEmi").text = self.dh_emi
        ET.SubElement(ide, "dhSaiEnt").text = self.dh_sai
        ET.SubElement(ide, "tpNF").text = "1"
        ET.SubElement(ide, "idDest").text = "1"
        ET.SubElement(ide, "cMunFG").text = self.emitter.address.city_code
        ET.SubElement(ide, "tpImp").text = "1"
        ET.SubElement(ide, "tpEmis").text = "1"
        ET.SubElement(ide, "cDV").text = self.cdv
        ET.SubElement(ide, "tpAmb").text = "1"
        ET.SubElement(ide, "finNFe").text = "1"
        ET.SubElement(ide, "indFinal").text = "1"
        ET.SubElement(ide, "indPres").text = "2"
        ET.SubElement(ide, "indIntermed").text = "0"
        ET.SubElement(ide, "procEmi").text = "0"
        ET.SubElement(ide, "verProc").text = "Sistema Transferencia Filiais 1.0"
        return ide

    def _build_emit(self, parent: ET.Element) -> ET.Element:
        emit = ET.SubElement(parent, "emit")
        ET.SubElement(emit, "CNPJ").text = self.emitter.cnpj
        ET.SubElement(emit, "xNome").text = self.emitter.name
        ET.SubElement(emit, "xFant").text = self.emitter.trade_name
        ender = ET.SubElement(emit, "enderEmit")
        ET.SubElement(ender, "xLgr").text = self.emitter.address.street
        ET.SubElement(ender, "nro").text = self.emitter.address.number
        ET.SubElement(ender, "xCpl").text = self.emitter.address.complement
        ET.SubElement(ender, "xBairro").text = self.emitter.address.neighborhood
        ET.SubElement(ender, "cMun").text = self.emitter.address.city_code
        ET.SubElement(ender, "xMun").text = self.emitter.address.city_name
        ET.SubElement(ender, "UF").text = self.emitter.address.uf
        ET.SubElement(ender, "CEP").text = self.emitter.address.cep
        ET.SubElement(ender, "cPais").text = self.emitter.address.country_code
        ET.SubElement(ender, "xPais").text = self.emitter.address.country_name
        ET.SubElement(emit, "IE").text = self.emitter.ie
        ET.SubElement(emit, "CRT").text = self.emitter.crt
        return emit

    def _build_dest(self, parent: ET.Element) -> ET.Element:
        dest = ET.SubElement(parent, "dest")
        ET.SubElement(dest, "CNPJ").text = self.recipient.cnpj
        ET.SubElement(dest, "xNome").text = self.recipient.name
        ender = ET.SubElement(dest, "enderDest")
        ET.SubElement(ender, "xLgr").text = self.recipient.address.street
        ET.SubElement(ender, "nro").text = self.recipient.address.number
        ET.SubElement(ender, "xCpl").text = self.recipient.address.complement
        ET.SubElement(ender, "xBairro").text = self.recipient.address.neighborhood
        ET.SubElement(ender, "cMun").text = self.recipient.address.city_code
        ET.SubElement(ender, "xMun").text = self.recipient.address.city_name
        ET.SubElement(ender, "UF").text = self.recipient.address.uf
        ET.SubElement(ender, "CEP").text = self.recipient.address.cep
        ET.SubElement(ender, "cPais").text = self.recipient.address.country_code
        ET.SubElement(ender, "xPais").text = self.recipient.address.country_name
        ET.SubElement(ender, "fone").text = self.recipient.address.phone
        ET.SubElement(dest, "indIEDest").text = "1"
        ET.SubElement(dest, "IE").text = self.recipient.ie
        return dest

    def _build_det_list(self, parent: ET.Element) -> None:
        for idx, prod in enumerate(self.report.products, start=1):
            item_tax = TaxCalculator.calculate_item_tax(prod)
            det = ET.SubElement(parent, "det", {"nItem": str(idx)})

            # <prod>
            p_elem = ET.SubElement(det, "prod")
            ET.SubElement(p_elem, "cProd").text = prod.code
            ET.SubElement(p_elem, "cEAN").text = prod.ean
            ET.SubElement(p_elem, "xProd").text = prod.description
            ET.SubElement(p_elem, "NCM").text = prod.ncm
            ET.SubElement(p_elem, "CFOP").text = prod.cfop
            ET.SubElement(p_elem, "uCom").text = prod.unit
            ET.SubElement(p_elem, "qCom").text = f"{prod.quantity:.4f}"
            ET.SubElement(p_elem, "vUnCom").text = f"{prod.unit_price:.2f}"
            ET.SubElement(p_elem, "vProd").text = f"{prod.total_price:.2f}"
            ET.SubElement(p_elem, "cEANTrib").text = prod.ean
            ET.SubElement(p_elem, "uTrib").text = prod.unit
            ET.SubElement(p_elem, "qTrib").text = f"{prod.quantity:.4f}"
            ET.SubElement(p_elem, "vUnTrib").text = f"{prod.unit_price:.2f}"
            ET.SubElement(p_elem, "indTot").text = "1"

            # <imposto>
            imp = ET.SubElement(det, "imposto")
            ET.SubElement(imp, "vTotTrib").text = f"{item_tax.ibpt_estimated_tax:.2f}"

            icms = ET.SubElement(imp, "ICMS")
            icms_sn = ET.SubElement(icms, "ICMSSN102")
            ET.SubElement(icms_sn, "orig").text = "1"
            ET.SubElement(icms_sn, "CSOSN").text = "400"

            ipi = ET.SubElement(imp, "IPI")
            ET.SubElement(ipi, "cEnq").text = "999"
            ipi_trib = ET.SubElement(ipi, "IPITrib")
            ET.SubElement(ipi_trib, "CST").text = "50"
            ET.SubElement(ipi_trib, "vBC").text = f"{prod.total_price:.2f}"
            ET.SubElement(ipi_trib, "pIPI").text = "0.0000"
            ET.SubElement(ipi_trib, "vIPI").text = "0.00"

            pis = ET.SubElement(imp, "PIS")
            pis_aliq = ET.SubElement(pis, "PISAliq")
            ET.SubElement(pis_aliq, "CST").text = "01"
            ET.SubElement(pis_aliq, "vBC").text = f"{prod.total_price:.2f}"
            ET.SubElement(pis_aliq, "pPIS").text = "0.0000"
            ET.SubElement(pis_aliq, "vPIS").text = "0.00"

            cofins = ET.SubElement(imp, "COFINS")
            cofins_aliq = ET.SubElement(cofins, "COFINSAliq")
            ET.SubElement(cofins_aliq, "CST").text = "01"
            ET.SubElement(cofins_aliq, "vBC").text = f"{prod.total_price:.2f}"
            ET.SubElement(cofins_aliq, "pCOFINS").text = "0.0000"
            ET.SubElement(cofins_aliq, "vCOFINS").text = "0.00"

    def _build_total(self, parent: ET.Element) -> ET.Element:
        total = ET.SubElement(parent, "total")
        icms_tot = ET.SubElement(total, "ICMSTot")
        ET.SubElement(icms_tot, "vBC").text = "0.00"
        ET.SubElement(icms_tot, "vICMS").text = "0.00"
        ET.SubElement(icms_tot, "vICMSDeson").text = "0.00"
        ET.SubElement(icms_tot, "vFCPUFDest").text = "0.00"
        ET.SubElement(icms_tot, "vICMSUFDest").text = "0.00"
        ET.SubElement(icms_tot, "vICMSUFRemet").text = "0.00"
        ET.SubElement(icms_tot, "vFCP").text = "0.00"
        ET.SubElement(icms_tot, "vBCST").text = "0.00"
        ET.SubElement(icms_tot, "vST").text = "0.00"
        ET.SubElement(icms_tot, "vFCPST").text = "0.00"
        ET.SubElement(icms_tot, "vFCPSTRet").text = "0.00"
        ET.SubElement(icms_tot, "vProd").text = f"{self.tax_summary.total_products:.2f}"
        ET.SubElement(icms_tot, "vFrete").text = "0.00"
        ET.SubElement(icms_tot, "vSeg").text = "0.00"
        ET.SubElement(icms_tot, "vDesc").text = "0.00"
        ET.SubElement(icms_tot, "vII").text = "0.00"
        ET.SubElement(icms_tot, "vIPI").text = "0.00"
        ET.SubElement(icms_tot, "vIPIDevol").text = "0.00"
        ET.SubElement(icms_tot, "vPIS").text = "0.00"
        ET.SubElement(icms_tot, "vCOFINS").text = "0.00"
        ET.SubElement(icms_tot, "vOutro").text = "0.00"
        ET.SubElement(icms_tot, "vNF").text = f"{self.tax_summary.total_invoice:.2f}"
        ET.SubElement(icms_tot, "vTotTrib").text = f"{self.tax_summary.total_trib:.2f}"
        return total

    def _build_transp(self, parent: ET.Element) -> ET.Element:
        transp = ET.SubElement(parent, "transp")
        ET.SubElement(transp, "modFrete").text = "9"
        vol = ET.SubElement(transp, "vol")
        ET.SubElement(vol, "pesoL").text = "0.000"
        ET.SubElement(vol, "pesoB").text = "0.000"
        return transp

    def _build_pag(self, parent: ET.Element) -> ET.Element:
        pag = ET.SubElement(parent, "pag")
        det_pag = ET.SubElement(pag, "detPag")
        ET.SubElement(det_pag, "tPag").text = "90"
        ET.SubElement(det_pag, "vPag").text = "0"
        return pag

    def _build_inf_adic(self, parent: ET.Element) -> ET.Element:
        inf_adic = ET.SubElement(parent, "infAdic")
        ET.SubElement(inf_adic, "infCpl").text = (
            f"Tributos aproximados: R$ {self.tax_summary.total_federal_tax:,.2f} (Federal) e "
            f"R$ {self.tax_summary.total_state_tax:,.2f} (Estadual). Fonte: IBPT"
        )
        return inf_adic

    def build_xml_string(self) -> str:
        nfe_proc = ET.Element("nfeProc", {
            "xmlns": "http://www.portalfiscal.inf.br/nfe",
            "versao": "4.00"
        })

        nfe = ET.SubElement(nfe_proc, "NFe", {"xmlns": "http://www.portalfiscal.inf.br/nfe"})
        inf_nfe_attrs = {"versao": "4.00"}
        if self.ch_nfe:
            inf_nfe_attrs["Id"] = f"NFe{self.ch_nfe}"
        inf_nfe = ET.SubElement(nfe, "infNFe", inf_nfe_attrs)

        self._build_ide(inf_nfe)
        self._build_emit(inf_nfe)
        self._build_dest(inf_nfe)
        self._build_det_list(inf_nfe)
        self._build_total(inf_nfe)
        self._build_transp(inf_nfe)
        self._build_pag(inf_nfe)
        self._build_inf_adic(inf_nfe)

        raw_xml = ET.tostring(nfe_proc, encoding="utf-8")
        parsed_dom = minidom.parseString(raw_xml)
        pretty_xml = parsed_dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

        xml_lines = pretty_xml.splitlines()
        if xml_lines and xml_lines[0].startswith("<?xml"):
            xml_lines = xml_lines[1:]

        return "\n".join(xml_lines)
