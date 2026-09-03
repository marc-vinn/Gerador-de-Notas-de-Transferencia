/**
 * Modal Controller Component
 * Manages Recipient configuration modal, CEP/CNPJ searches, and storage synchronization.
 */
import { ApiClient } from "../services/apiClient.js";
import { StorageManager } from "../services/storageManager.js";
import { sanitizeDigits } from "../utils/sanitizer.js";

export class ModalController {
  constructor({ onSave, onReset, onAlert }) {
    this.onSave = onSave;
    this.onReset = onReset;
    this.onAlert = onAlert;

    this.modal = document.getElementById("recipientModal");
    this.form = document.getElementById("recipientForm");
    this.destBadgeName = document.getElementById("destBadgeName");
    this.apiStatus = document.getElementById("modalApiStatus");

    this.btnOpen = document.getElementById("btnOpenModal");
    this.btnClose = document.getElementById("btnCloseModal");
    this.btnCancel = document.getElementById("btnCancelModal");
    this.btnReset = document.getElementById("btnResetDefault");
    this.btnSearchCnpj = document.getElementById("btnSearchCnpj");
    this.btnSearchCep = document.getElementById("btnSearchCep");

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
    this.btnOpen?.addEventListener("click", () => this.open());
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

  open() {
    this.setStatus("");
    this.fillForm();
    this.modal?.classList.remove("hidden");
  }

  close() {
    this.modal?.classList.add("hidden");
  }

  fillForm() {
    const recipient = StorageManager.getRecipient() || {};
    this.fields.cnpj.value = recipient.cnpj || "";
    this.fields.name.value = recipient.name || "";
    this.fields.ie.value = recipient.ie || "";
    this.fields.phone.value = recipient.phone || "";
    this.fields.street.value = recipient.street || "";
    this.fields.number.value = recipient.number || "";
    this.fields.complement.value = recipient.complement || "";
    this.fields.bairro.value = recipient.bairro || "";
    this.fields.cityName.value = recipient.cityName || "";
    this.fields.uf.value = recipient.uf || "";
    this.fields.cep.value = recipient.cep || "";
    this.fields.cityCode.value = recipient.cityCode || "";
  }

  updateBadgeUI() {
    const recipient = StorageManager.getRecipient();
    if (this.destBadgeName) {
      if (recipient && recipient.name) {
        this.destBadgeName.textContent = recipient.name;
      } else {
        this.destBadgeName.textContent = "Não configurada (Clique para cadastrar)";
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
      uf: this.fields.uf.value.trim(),
      cep: this.fields.cep.value.trim(),
      cityCode: this.fields.cityCode.value.trim()
    };

    if (!data.cnpj || !data.name) {
      alert("Por favor, preencha o CNPJ e a Razão Social da empresa destinatária.");
      return;
    }

    StorageManager.saveRecipient(data);
    this.updateBadgeUI();
    this.close();
    this.onAlert?.(`Empresa destinatária '${data.name}' cadastrada com sucesso!`, "success");
    this.onSave?.(data);
  }

  handleReset() {
    StorageManager.clearRecipient();
    this.updateBadgeUI();
    this.fillForm();
    this.setStatus("");
    this.close();
    this.onAlert?.("Cadastro da destinatária limpo.", "success");
    this.onReset?.();
  }
}
