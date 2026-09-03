/**
 * Modal Controller Component
 * Manages Dual Company configuration (Emitter/Matrix and Recipient/Branch),
 * automatic CEP/CNPJ searches, and storage synchronization.
 */
import { ApiClient } from "../services/apiClient.js";
import { StorageManager } from "../services/storageManager.js";
import { sanitizeDigits } from "../utils/sanitizer.js";

export class ModalController {
  constructor({ onSave, onReset, onAlert }) {
    this.onSave = onSave;
    this.onReset = onReset;
    this.onAlert = onAlert;
    this.activeTab = "emitter"; // 'emitter' or 'recipient'

    this.modal = document.getElementById("recipientModal");
    this.form = document.getElementById("recipientForm");
    this.apiStatus = document.getElementById("modalApiStatus");
    this.modalTitle = document.getElementById("modalTitle");

    this.emitterBadgeName = document.getElementById("emitterBadgeName");
    this.destBadgeName = document.getElementById("destBadgeName");
    this.emitterBadge = document.getElementById("emitterBadge");
    this.destBadge = document.getElementById("destBadge");

    this.btnOpenEmitter = document.getElementById("btnOpenEmitterModal");
    this.btnOpenRecipient = document.getElementById("btnOpenRecipientModal");
    this.btnLegacyOpen = document.getElementById("btnOpenModal"); // backwards compatibility

    this.btnClose = document.getElementById("btnCloseModal");
    this.btnCancel = document.getElementById("btnCancelModal");
    this.btnReset = document.getElementById("btnResetDefault");
    this.btnSubmit = document.getElementById("btnSubmitCompany");
    this.btnSearchCnpj = document.getElementById("btnSearchCnpj");
    this.btnSearchCep = document.getElementById("btnSearchCep");

    this.tabEmitter = document.getElementById("tabCompanyEmitter");
    this.tabRecipient = document.getElementById("tabCompanyRecipient");
    this.lblCnpj = document.getElementById("lblCnpj");
    this.lblName = document.getElementById("lblName");

    this.fields = {
      cnpj: document.getElementById("recipientCnpj"),
      name: document.getElementById("recipientName"),
      ie: document.getElementById("recipientIe"),
      phone: document.getElementById("recipientPhone"),
      street: document.getElementById("recipientStreet"),
      number: document.getElementById("recipientNumber"),
      complement: document.getElementById("recipientComplement"),
      bairro: document.getElementById("recipientBairro"),
      cityName: document.getElementById("recipientCityName"),
      uf: document.getElementById("recipientUf"),
      cep: document.getElementById("recipientCep"),
      cityCode: document.getElementById("recipientCityCode")
    };

    this.initEvents();
    this.updateBadgeUI();
  }

  initEvents() {
    this.btnOpenEmitter?.addEventListener("click", () => this.open("emitter"));
    this.btnOpenRecipient?.addEventListener("click", () => this.open("recipient"));
    this.btnLegacyOpen?.addEventListener("click", () => this.open("recipient"));

    this.emitterBadge?.addEventListener("click", () => this.open("emitter"));
    this.destBadge?.addEventListener("click", () => this.open("recipient"));

    this.tabEmitter?.addEventListener("click", () => this.switchTab("emitter"));
    this.tabRecipient?.addEventListener("click", () => this.switchTab("recipient"));

    this.btnClose?.addEventListener("click", () => this.close());
    this.btnCancel?.addEventListener("click", () => this.close());

    this.modal?.addEventListener("click", (e) => {
      if (e.target === this.modal) this.close();
    });

    this.btnReset?.addEventListener("click", () => this.handleReset());
    this.form?.addEventListener("submit", (e) => this.handleSubmit(e));

    this.btnSearchCnpj?.addEventListener("click", () => this.handleCnpjLookup());
    this.btnSearchCep?.addEventListener("click", () => this.handleCepLookup());

    this.fields.cnpj?.addEventListener("blur", () => {
      const clean = sanitizeDigits(this.fields.cnpj.value);
      if (clean.length === 14 && !this.fields.name.value) {
        this.handleCnpjLookup();
      }
    });

    this.fields.cep?.addEventListener("blur", () => {
      const clean = sanitizeDigits(this.fields.cep.value);
      if (clean.length === 8) {
        this.handleCepLookup(false);
      }
    });
  }

  switchTab(targetTab) {
    this.activeTab = targetTab;
    this.setStatus("");

    if (targetTab === "emitter") {
      this.tabEmitter?.classList.add("active");
      this.tabRecipient?.classList.remove("active");
      if (this.modalTitle) this.modalTitle.textContent = "Cadastro da Empresa Emitente (Matriz)";
      if (this.lblCnpj) this.lblCnpj.textContent = "CNPJ Matriz (Emitente) *";
      if (this.lblName) this.lblName.textContent = "Razão Social / Nome da Matriz *";
      if (this.btnSubmit) this.btnSubmit.textContent = "Salvar Empresa Emitente (Matriz)";
      if (this.btnReset) this.btnReset.textContent = "Limpar Matriz";
    } else {
      this.tabRecipient?.classList.add("active");
      this.tabEmitter?.classList.remove("active");
      if (this.modalTitle) this.modalTitle.textContent = "Cadastro da Empresa Destinatária (Filial)";
      if (this.lblCnpj) this.lblCnpj.textContent = "CNPJ Filial (Destinatária) *";
      if (this.lblName) this.lblName.textContent = "Razão Social / Nome da Filial *";
      if (this.btnSubmit) this.btnSubmit.textContent = "Salvar Empresa Destinatária (Filial)";
      if (this.btnReset) this.btnReset.textContent = "Limpar Filial";
    }

    this.fillForm();
  }

  setStatus(message, type = "info") {
    if (!this.apiStatus) return;
    if (!message) {
      this.apiStatus.classList.add("hidden");
      return;
    }
    this.apiStatus.textContent = message;
    this.apiStatus.className = `modal-status ${type}`;
    this.apiStatus.classList.remove("hidden");
  }

  open(tab = null) {
    if (tab) {
      this.switchTab(tab);
    } else {
      this.switchTab(this.activeTab);
    }
    this.modal?.classList.remove("hidden");
    this.fields.cnpj?.focus();
  }

  close() {
    this.modal?.classList.add("hidden");
  }

  fillForm() {
    const data = this.activeTab === "emitter" 
      ? (StorageManager.getEmitter() || {}) 
      : (StorageManager.getRecipient() || {});

    this.fields.cnpj.value = data.cnpj || "";
    this.fields.name.value = data.name || "";
    this.fields.ie.value = data.ie || "";
    this.fields.phone.value = data.phone || "";
    this.fields.street.value = data.street || "";
    this.fields.number.value = data.number || "";
    this.fields.complement.value = data.complement || "";
    this.fields.bairro.value = data.bairro || "";
    this.fields.cityName.value = data.cityName || "";
    this.fields.uf.value = data.uf || "";
    this.fields.cep.value = data.cep || "";
    this.fields.cityCode.value = data.cityCode || "";
  }

  updateBadgeUI() {
    const emitter = StorageManager.getEmitter();
    const recipient = StorageManager.getRecipient();

    // Emitter (Matriz) badge
    if (this.emitterBadgeName) {
      if (emitter && emitter.name && emitter.uf) {
        this.emitterBadgeName.textContent = `${emitter.name} (${emitter.uf})`;
        this.emitterBadge?.classList.add("company-badge-success");
        this.emitterBadge?.classList.remove("company-badge-warning");
      } else {
        this.emitterBadgeName.textContent = "Não configurada (Clique para cadastrar)";
        this.emitterBadge?.classList.add("company-badge-warning");
        this.emitterBadge?.classList.remove("company-badge-success");
      }
    }

    // Recipient (Filial) badge
    if (this.destBadgeName) {
      if (recipient && recipient.name && recipient.uf) {
        this.destBadgeName.textContent = `${recipient.name} (${recipient.uf})`;
        this.destBadge?.classList.add("company-badge-success");
        this.destBadge?.classList.remove("company-badge-warning");
      } else {
        this.destBadgeName.textContent = "Não configurada (Clique para cadastrar)";
        this.destBadge?.classList.add("company-badge-warning");
        this.destBadge?.classList.remove("company-badge-success");
      }
    }
  }

  async handleCnpjLookup() {
    const raw = this.fields.cnpj.value;
    try {
      this.setStatus("🔍 Consultando dados da empresa na Receita Federal...", "info");
      this.btnSearchCnpj.disabled = true;

      const data = await ApiClient.lookupCnpj(raw);
      this.fields.name.value = data.razao_social || data.nome_fantasia || "";
      this.fields.street.value = data.logradouro || "";
      this.fields.number.value = data.numero || "";
      this.fields.complement.value = data.complemento || "";
      this.fields.bairro.value = data.bairro || "";
      this.fields.cityName.value = data.municipio || "";
      this.fields.uf.value = data.uf || "";

      if (data.ddd_telefone_1) {
        this.fields.phone.value = data.ddd_telefone_1;
      } else if (data.telefone) {
        this.fields.phone.value = data.telefone;
      }

      if (data.cep) {
        const cleanCep = sanitizeDigits(data.cep);
        this.fields.cep.value = cleanCep;
        await this.handleCepLookup(false);
      }

      this.setStatus(`✅ Empresa '${this.fields.name.value}' localizada com sucesso!`, "info");
    } catch (err) {
      this.setStatus(`Erro ao buscar CNPJ: ${err.message}`, "error");
    } finally {
      this.btnSearchCnpj.disabled = false;
    }
  }

  async handleCepLookup(showStatus = true) {
    const raw = this.fields.cep.value;
    try {
      if (showStatus) this.setStatus("🔍 Consultando endereço no ViaCEP...", "info");
      this.btnSearchCep.disabled = true;

      const data = await ApiClient.lookupCep(raw);
      if (data.logradouro) this.fields.street.value = data.logradouro;
      if (data.bairro) this.fields.bairro.value = data.bairro;
      if (data.localidade) this.fields.cityName.value = data.localidade;
      if (data.uf) this.fields.uf.value = data.uf;
      if (data.ibge) this.fields.cityCode.value = data.ibge;

      if (showStatus) this.setStatus(`✅ Endereço '${data.logradouro || data.localidade}' carregado pelo CEP!`, "info");
    } catch (err) {
      if (showStatus) this.setStatus(`Erro ao buscar CEP: ${err.message}`, "error");
    } finally {
      this.btnSearchCep.disabled = false;
    }
  }

  handleSubmit(e) {
    e.preventDefault();
    const data = {
      cnpj: this.fields.cnpj.value.trim(),
      name: this.fields.name.value.trim(),
      ie: this.fields.ie.value.trim(),
      phone: this.fields.phone.value.trim(),
      street: this.fields.street.value.trim(),
      number: this.fields.number.value.trim(),
      complement: this.fields.complement.value.trim(),
      bairro: this.fields.bairro.value.trim(),
      cityName: this.fields.cityName.value.trim(),
      uf: this.fields.uf.value.trim().toUpperCase(),
      cep: this.fields.cep.value.trim(),
      cityCode: this.fields.cityCode.value.trim()
    };

    if (!data.cnpj || !data.name) {
      alert("Por favor, preencha o CNPJ e a Razão Social da empresa.");
      return;
    }

    if (!data.uf || data.uf.length !== 2) {
      alert("A UF (Estado) é obrigatória para operações fiscais da NF-e (2 letras).");
      this.fields.uf.focus();
      return;
    }

    if (this.activeTab === "emitter") {
      StorageManager.saveEmitter(data);
      this.onAlert?.(`Empresa Emitente (Matriz) '${data.name}' salva com sucesso!`, "success");
    } else {
      StorageManager.saveRecipient(data);
      this.onAlert?.(`Empresa Destinatária (Filial) '${data.name}' salva com sucesso!`, "success");
    }

    this.updateBadgeUI();
    this.close();
    this.onSave?.(data, this.activeTab);
  }

  handleReset() {
    if (this.activeTab === "emitter") {
      StorageManager.clearEmitter();
      this.onAlert?.("Cadastro da Matriz limpo.", "success");
    } else {
      StorageManager.clearRecipient();
      this.onAlert?.("Cadastro da Filial limpo.", "success");
    }
    this.updateBadgeUI();
    this.fillForm();
    this.setStatus("");
    this.close();
    this.onReset?.(this.activeTab);
  }
}
