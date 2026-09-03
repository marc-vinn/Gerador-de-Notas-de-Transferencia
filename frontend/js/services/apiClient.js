/**
 * API Client Service
 * Encapsulates HTTP communication with Backend and External APIs (BrasilAPI / ViaCEP).
 */
import { CONFIG } from "../config.js";
import { sanitizeDigits } from "../utils/sanitizer.js";

export const ApiClient = {
  async uploadReport(file) {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(CONFIG.ENDPOINTS.UPLOAD, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Erro ao processar o relatório.");
    }
    return data;
  },

  async analyzeMultiReports(files) {
    const formData = new FormData();
    formData.append("branch_sales", files.branchSales);
    formData.append("branch_stock", files.branchStock);
    formData.append("matrix_sales", files.matrixSales);
    formData.append("matrix_stock", files.matrixStock);

    const res = await fetch(CONFIG.ENDPOINTS.ANALYZE_MULTI, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Erro ao processar os 4 relatórios de transferência.");
    }
    return data;
  },

  async generateXml(payload) {
    const formData = new FormData();
    if (payload.file) {
      formData.append("file", payload.file);
    }
    formData.append("filename", payload.filename || "relatorio.xls");
    formData.append("products", JSON.stringify(payload.products));
    formData.append("direction", payload.direction || "matrix_to_branch");

    if (payload.recipient) {
      const r = payload.recipient;
      if (r.cnpj) formData.append("recipient_cnpj", r.cnpj);
      if (r.name) formData.append("recipient_name", r.name);
      if (r.ie) formData.append("recipient_ie", r.ie);
      if (r.phone) formData.append("recipient_phone", r.phone);
      if (r.street) formData.append("recipient_street", r.street);
      if (r.number) formData.append("recipient_number", r.number);
      if (r.complement) formData.append("recipient_complement", r.complement);
      if (r.bairro) formData.append("recipient_bairro", r.bairro);
      if (r.cityName) formData.append("recipient_city_name", r.cityName);
      if (r.uf) formData.append("recipient_uf", r.uf);
      if (r.cep) formData.append("recipient_cep", r.cep);
      if (r.cityCode) formData.append("recipient_city_code", r.cityCode);
    }

    const res = await fetch(CONFIG.ENDPOINTS.GENERATE_XML, {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.error || "Erro ao gerar XML da DANFE.");
    }

    return await res.blob();
  },

  async lookupCnpj(cnpjRaw) {
    const clean = sanitizeDigits(cnpjRaw);
    if (clean.length !== 14) {
      throw new Error("Digite um CNPJ válido com 14 dígitos.");
    }

    let data = null;
    try {
      const res = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${clean}`);
      if (res.ok) {
        data = await res.json();
      }
    } catch (e) {
      console.warn("BrasilAPI fallback triggered:", e);
    }

    if (!data) {
      const res2 = await fetch(`https://minhareceita.org/${clean}`);
      if (res2.ok) {
        data = await res2.json();
      }
    }

    if (!data) {
      throw new Error("Não foi possível localizar dados do CNPJ informado.");
    }

    return data;
  },

  async lookupCep(cepRaw) {
    const clean = sanitizeDigits(cepRaw);
    if (clean.length !== 8) {
      throw new Error("Digite um CEP válido com 8 dígitos.");
    }

    const res = await fetch(`https://viacep.com.br/ws/${clean}/json/`);
    const data = await res.json();

    if (data.erro) {
      throw new Error("CEP não encontrado.");
    }

    return data;
  }
};
