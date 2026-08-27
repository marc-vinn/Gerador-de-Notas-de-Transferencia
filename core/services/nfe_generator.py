"""
Service for generating valid NFe XML (version 4.00) from TransferReport entities.
"""
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Optional
from xml.dom import minidom

from ..domain.report import TransferReport
from ..domain.nfe import CompanyInfo, DEFAULT_EMITTER, DEFAULT_RECIPIENT

class NFeGenerator:
    @staticmethod
    def _generate_access_key(uf: str, date_str: str, cnpj: str, mod: str, serie: str, number: str, tp_emis: str, cnf: str) -> tuple[str, str]:
        """
        Generates 44-digit NFe Chave de Acesso and Modulo 11 check digit (cDV).
        """
        # Format: cUF(2) + AAMM(4) + CNPJ(14) + mod(2) + serie(3) + nNF(9) + tpEmis(1) + cNF(8)
        uf_code = "52"
        aamm = date_str  # YYMM format
        cnpj_clean = cnpj.zfill(14)
        mod_fmt = mod.zfill(2)
        serie_fmt = serie.zfill(3)
        nnf_fmt = number.zfill(9)
        tp_emis_fmt = tp_emis
        cnf_fmt = cnf.zfill(8)

        base_key = f"{uf_code}{aamm}{cnpj_clean}{mod_fmt}{serie_fmt}{nnf_fmt}{tp_emis_fmt}{cnf_fmt}"
        
        # Calculate Modulo 11 for cDV
        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        total = 0
        for i, char in enumerate(reversed(base_key)):
            weight = weights[i % len(weights)]
            total += int(char) * weight
        
        remainder = total % 11
        cdv = 0 if remainder in [0, 1] else 11 - remainder

        full_key = f"{base_key}{cdv}"
        return full_key, str(cdv)

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
        When n_nf is None (default), the number and access key fields are left
        empty so the ERP can assign its own number and recalculate the key.
        """
        now = datetime.now(timezone(timedelta(hours=-3)))
        dh_emi = now.strftime("%Y-%m-%dT%H:%M:%S-03:00")
        dh_sai = (now + timedelta(seconds=21)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
        date_aamm = now.strftime("%y%m")

        cnf = str(random.randint(10000000, 99999999))

        # Only compute access key when a real NFe number is provided
        if n_nf is not None:
            ch_nfe, cdv = cls._generate_access_key(
                uf="52",
                date_str=date_aamm,
                cnpj=emitter.cnpj,
                mod="55",
                serie=str(serie),
                number=str(n_nf),
                tp_emis="1",
                cnf=cnf
            )
        else:
            ch_nfe = ""
            cdv = ""

        nfe_proc = ET.Element("nfeProc", {
            "xmlns": "http://www.portalfiscal.inf.br/nfe",
            "versao": "4.00"
        })

        nfe = ET.SubElement(nfe_proc, "NFe", {"xmlns": "http://www.portalfiscal.inf.br/nfe"})
        inf_nfe_attrs = {"versao": "4.00"}
        if ch_nfe:
            inf_nfe_attrs["Id"] = f"NFe{ch_nfe}"
        inf_nfe = ET.SubElement(nfe, "infNFe", inf_nfe_attrs)

        # <ide>
        ide = ET.SubElement(inf_nfe, "ide")
        ET.SubElement(ide, "cUF").text = "52"
        ET.SubElement(ide, "cNF").text = cnf
        ET.SubElement(ide, "natOp").text = "Transferencia de mercadoria SAIDA"
        ET.SubElement(ide, "mod").text = "55"
        ET.SubElement(ide, "serie").text = str(serie)
        ET.SubElement(ide, "nNF").text = str(n_nf) if n_nf is not None else ""
        ET.SubElement(ide, "dhEmi").text = dh_emi
        ET.SubElement(ide, "dhSaiEnt").text = dh_sai
        ET.SubElement(ide, "tpNF").text = "1"
        ET.SubElement(ide, "idDest").text = "1"
        ET.SubElement(ide, "cMunFG").text = emitter.address.city_code
        ET.SubElement(ide, "tpImp").text = "1"
        ET.SubElement(ide, "tpEmis").text = "1"
        ET.SubElement(ide, "cDV").text = cdv
        ET.SubElement(ide, "tpAmb").text = "1"
        ET.SubElement(ide, "finNFe").text = "1"
        ET.SubElement(ide, "indFinal").text = "1"
        ET.SubElement(ide, "indPres").text = "2"
        ET.SubElement(ide, "indIntermed").text = "0"
        ET.SubElement(ide, "procEmi").text = "0"
        ET.SubElement(ide, "verProc").text = "Sistema Transferencia Filiais 1.0"

        # <emit>
        emit = ET.SubElement(inf_nfe, "emit")
        ET.SubElement(emit, "CNPJ").text = emitter.cnpj
        ET.SubElement(emit, "xNome").text = emitter.name
        ET.SubElement(emit, "xFant").text = emitter.trade_name
        ender_emit = ET.SubElement(emit, "enderEmit")
        ET.SubElement(ender_emit, "xLgr").text = emitter.address.street
        ET.SubElement(ender_emit, "nro").text = emitter.address.number
        ET.SubElement(ender_emit, "xCpl").text = emitter.address.complement
        ET.SubElement(ender_emit, "xBairro").text = emitter.address.neighborhood
        ET.SubElement(ender_emit, "cMun").text = emitter.address.city_code
        ET.SubElement(ender_emit, "xMun").text = emitter.address.city_name
        ET.SubElement(ender_emit, "UF").text = emitter.address.uf
        ET.SubElement(ender_emit, "CEP").text = emitter.address.cep
        ET.SubElement(ender_emit, "cPais").text = emitter.address.country_code
        ET.SubElement(ender_emit, "xPais").text = emitter.address.country_name
        ET.SubElement(emit, "IE").text = emitter.ie
        ET.SubElement(emit, "CRT").text = emitter.crt

        # <dest> (Requerido: emitente e destinatário iguais)
        dest = ET.SubElement(inf_nfe, "dest")
        ET.SubElement(dest, "CNPJ").text = recipient.cnpj
        ET.SubElement(dest, "xNome").text = recipient.name
        ender_dest = ET.SubElement(dest, "enderDest")
        ET.SubElement(ender_dest, "xLgr").text = recipient.address.street
        ET.SubElement(ender_dest, "nro").text = recipient.address.number
        ET.SubElement(ender_dest, "xCpl").text = recipient.address.complement
        ET.SubElement(ender_dest, "xBairro").text = recipient.address.neighborhood
        ET.SubElement(ender_dest, "cMun").text = recipient.address.city_code
        ET.SubElement(ender_dest, "xMun").text = recipient.address.city_name
        ET.SubElement(ender_dest, "UF").text = recipient.address.uf
        ET.SubElement(ender_dest, "CEP").text = recipient.address.cep
        ET.SubElement(ender_dest, "cPais").text = recipient.address.country_code
        ET.SubElement(ender_dest, "xPais").text = recipient.address.country_name
        ET.SubElement(ender_dest, "fone").text = recipient.address.phone
        ET.SubElement(dest, "indIEDest").text = "1"
        ET.SubElement(dest, "IE").text = recipient.ie

        # Products items <det>
        tot_vprod = 0.0
        tot_vtrib = 0.0

        for idx, prod in enumerate(report.products, start=1):
            det = ET.SubElement(inf_nfe, "det", {"nItem": str(idx)})
            
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

            v_trib = round(prod.total_price * 0.3863, 2)  # IBPT tax estimate (~38.63%)
            tot_vprod += prod.total_price
            tot_vtrib += v_trib

            # Taxes <imposto>
            imp = ET.SubElement(det, "imposto")
            ET.SubElement(imp, "vTotTrib").text = f"{v_trib:.2f}"
            
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

        # <total>
        total = ET.SubElement(inf_nfe, "total")
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
        ET.SubElement(icms_tot, "vProd").text = f"{tot_vprod:.2f}"
        ET.SubElement(icms_tot, "vFrete").text = "0.00"
        ET.SubElement(icms_tot, "vSeg").text = "0.00"
        ET.SubElement(icms_tot, "vDesc").text = "0.00"
        ET.SubElement(icms_tot, "vII").text = "0.00"
        ET.SubElement(icms_tot, "vIPI").text = "0.00"
        ET.SubElement(icms_tot, "vIPIDevol").text = "0.00"
        ET.SubElement(icms_tot, "vPIS").text = "0.00"
        ET.SubElement(icms_tot, "vCOFINS").text = "0.00"
        ET.SubElement(icms_tot, "vOutro").text = "0.00"
        ET.SubElement(icms_tot, "vNF").text = f"{tot_vprod:.2f}"
        ET.SubElement(icms_tot, "vTotTrib").text = f"{tot_vtrib:.2f}"

        # <transp>
        transp = ET.SubElement(inf_nfe, "transp")
        ET.SubElement(transp, "modFrete").text = "9"
        vol = ET.SubElement(transp, "vol")
        ET.SubElement(vol, "pesoL").text = "0.000"
        ET.SubElement(vol, "pesoB").text = "0.000"

        # <pag>
        pag = ET.SubElement(inf_nfe, "pag")
        det_pag = ET.SubElement(pag, "detPag")
        ET.SubElement(det_pag, "tPag").text = "90"
        ET.SubElement(det_pag, "vPag").text = "0"

        # <infAdic>
        inf_adic = ET.SubElement(inf_nfe, "infAdic")
        fed_tax = tot_vtrib * 0.51
        est_tax = tot_vtrib * 0.49
        ET.SubElement(inf_adic, "infCpl").text = (
            f"Tributos aproximados: R$ {fed_tax:,.2f} (Federal) e R$ {est_tax:,.2f} (Estadual). Fonte: IBPT"
        )

        # Render pretty XML
        raw_xml = ET.tostring(nfe_proc, encoding="utf-8")
        parsed_dom = minidom.parseString(raw_xml)
        pretty_xml = parsed_dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        
        # Strip header line if minidom adds xml declaration at start so top tag is nfeProc
        xml_lines = pretty_xml.splitlines()
        if xml_lines and xml_lines[0].startswith("<?xml"):
            xml_lines = xml_lines[1:]
        
        return "\n".join(xml_lines)
