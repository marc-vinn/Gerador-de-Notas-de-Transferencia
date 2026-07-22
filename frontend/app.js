document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const alertBox = document.getElementById("alertBox");
  const metricsGrid = document.getElementById("metricsGrid");
  const dataSection = document.getElementById("dataSection");

  const metricFilename = document.getElementById("metricFilename");
  const metricItemCount = document.getElementById("metricItemCount");
  const metricTotalQty = document.getElementById("metricTotalQty");
  const metricTotalValue = document.getElementById("metricTotalValue");

  const searchInput = document.getElementById("searchInput");
  const productsTableBody = document.getElementById("productsTableBody");
  const btnDownloadXml = document.getElementById("btnDownloadXml");

  // Recipient Modal Elements
  const btnOpenModal = document.getElementById("btnOpenModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnCancelModal = document.getElementById("btnCancelModal");
  const btnResetDefault = document.getElementById("btnResetDefault");
  const recipientModal = document.getElementById("recipientModal");
  const recipientForm = document.getElementById("recipientForm");
  const destBadgeName = document.getElementById("destBadgeName");

  const btnSearchCnpj = document.getElementById("btnSearchCnpj");
  const btnSearchCep = document.getElementById("btnSearchCep");
  const modalApiStatus = document.getElementById("modalApiStatus");

  const fields = {
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

  let currentFile = null;
  let parsedProducts = [];

  const STORAGE_KEY = "arboretho_transfer_recipient";

  function getStoredRecipient() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  function saveStoredRecipient(recipient) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(recipient));
    } catch (e) {
      console.warn("Storage error:", e);
    }
  }

  function clearStoredRecipient() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn("Storage error:", e);
    }
  }

  function updateBadgeUI() {
    const recipient = getStoredRecipient();
    if (recipient && recipient.name) {
      destBadgeName.textContent = recipient.name;
    } else {
      destBadgeName.textContent = "Não configurada (Clique para cadastrar)";
    }
  }

  function fillFormWithStored() {
    const recipient = getStoredRecipient() || {};
    fields.cnpj.value = recipient.cnpj || "";
    fields.name.value = recipient.name || "";
    fields.ie.value = recipient.ie || "";
    fields.phone.value = recipient.phone || "";
    fields.street.value = recipient.street || "";
    fields.number.value = recipient.number || "";
    fields.complement.value = recipient.complement || "";
    fields.bairro.value = recipient.bairro || "";
    fields.cityName.value = recipient.cityName || "";
    fields.uf.value = recipient.uf || "";
    fields.cep.value = recipient.cep || "";
    fields.cityCode.value = recipient.cityCode || "";
  }

  function setModalStatus(message, type = "info") {
    if (!message) {
      modalApiStatus.classList.add("hidden");
      return;
    }
    modalApiStatus.textContent = message;
    modalApiStatus.className = `modal-status ${type}`;
    modalApiStatus.classList.remove("hidden");
  }

  // --- API CNPJ Lookup ---
  async function fetchCnpj(cnpjRaw) {
    const cleanCnpj = cnpjRaw.replace(/\D/g, "");
    if (cleanCnpj.length !== 14) {
      setModalStatus("Digite um CNPJ válido com 14 dígitos.", "error");
      return;
    }

    setModalStatus("🔍 Consultando dados da empresa na Receita Federal...", "info");
    btnSearchCnpj.disabled = true;

    try {
      let data = null;

      // Primary API: BrasilAPI
      try {
        const res = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cleanCnpj}`);
        if (res.ok) {
          data = await res.json();
        }
      } catch (e) {
        console.warn("BrasilAPI failed, trying fallback...", e);
      }

      // Fallback API: MinhaReceita
      if (!data) {
        const res2 = await fetch(`https://minhareceita.org/${cleanCnpj}`);
        if (res2.ok) {
          data = await res2.json();
        }
      }

      if (!data) {
        throw new Error("Não foi possível localizar o CNPJ informado.");
      }

      // Populate form fields
      fields.name.value = data.razao_social || data.nome_fantasia || "";
      fields.street.value = data.logradouro || "";
      fields.number.value = data.numero || "";
      fields.complement.value = data.complemento || "";
      fields.bairro.value = data.bairro || "";
      fields.cityName.value = data.municipio || "";
      fields.uf.value = data.uf || "";

      if (data.ddd_telefone_1) {
        fields.phone.value = data.ddd_telefone_1;
      } else if (data.telefone) {
        fields.phone.value = data.telefone;
      }

      if (data.cep) {
        const cleanCep = String(data.cep).replace(/\D/g, "");
        fields.cep.value = cleanCep;
        // Trigger ViaCEP for IBGE code
        await fetchCep(cleanCep, false);
      }

      setModalStatus(`✅ Empresa '${fields.name.value}' localizada com sucesso!`, "info");

    } catch (err) {
      setModalStatus(`Erro ao buscar CNPJ: ${err.message}`, "error");
    } finally {
      btnSearchCnpj.disabled = false;
    }
  }

  // --- API CEP Lookup (ViaCEP) ---
  async function fetchCep(cepRaw, showStatus = true) {
    const cleanCep = cepRaw.replace(/\D/g, "");
    if (cleanCep.length !== 8) {
      if (showStatus) setModalStatus("Digite um CEP válido com 8 dígitos.", "error");
      return;
    }

    if (showStatus) setModalStatus("🔍 Consultando endereço no ViaCEP...", "info");
    btnSearchCep.disabled = true;

    try {
      const res = await fetch(`https://viacep.com.br/ws/${cleanCep}/json/`);
      const data = await res.json();

      if (data.erro) {
        throw new Error("CEP não encontrado.");
      }

      if (data.logradouro) fields.street.value = data.logradouro;
      if (data.bairro) fields.bairro.value = data.bairro;
      if (data.localidade) fields.cityName.value = data.localidade;
      if (data.uf) fields.uf.value = data.uf;
      if (data.ibge) fields.cityCode.value = data.ibge;

      if (showStatus) setModalStatus(`✅ Endereço '${data.logradouro || data.localidade}' carregado pelo CEP!`, "info");

    } catch (err) {
      if (showStatus) setModalStatus(`Erro ao buscar CEP: ${err.message}`, "error");
    } finally {
      btnSearchCep.disabled = false;
    }
  }

  // Auto-search on CNPJ & CEP button clicks
  btnSearchCnpj.addEventListener("click", () => fetchCnpj(fields.cnpj.value));
  btnSearchCep.addEventListener("click", () => fetchCep(fields.cep.value));

  // Auto-search on 14 digits typed in CNPJ or 8 digits in CEP
  fields.cnpj.addEventListener("blur", () => {
    const clean = fields.cnpj.value.replace(/\D/g, "");
    if (clean.length === 14 && !fields.name.value) {
      fetchCnpj(clean);
    }
  });

  fields.cep.addEventListener("blur", () => {
    const clean = fields.cep.value.replace(/\D/g, "");
    if (clean.length === 8) {
      fetchCep(clean, false);
    }
  });

  // Modal Open/Close Handlers
  btnOpenModal.addEventListener("click", () => {
    setModalStatus("");
    fillFormWithStored();
    recipientModal.classList.remove("hidden");
  });

  function closeModal() {
    recipientModal.classList.add("hidden");
  }

  btnCloseModal.addEventListener("click", closeModal);
  btnCancelModal.addEventListener("click", closeModal);

  recipientModal.addEventListener("click", (e) => {
    if (e.target === recipientModal) closeModal();
  });

  btnResetDefault.addEventListener("click", () => {
    clearStoredRecipient();
    updateBadgeUI();
    fillFormWithStored();
    setModalStatus("");
    showAlert("Cadastro da destinatária limpo.", "success");
    closeModal();
  });

  recipientForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const recipientData = {
      cnpj: fields.cnpj.value.trim(),
      name: fields.name.value.trim(),
      ie: fields.ie.value.trim(),
      phone: fields.phone.value.trim(),
      street: fields.street.value.trim(),
      number: fields.number.value.trim(),
      complement: fields.complement.value.trim(),
      bairro: fields.bairro.value.trim(),
      cityName: fields.cityName.value.trim(),
      uf: fields.uf.value.trim(),
      cep: fields.cep.value.trim(),
      cityCode: fields.cityCode.value.trim()
    };

    if (!recipientData.cnpj || !recipientData.name) {
      alert("Por favor, preencha o CNPJ e a Razão Social da empresa destinatária.");
      return;
    }

    saveStoredRecipient(recipientData);
    updateBadgeUI();
    showAlert(`Empresa destinatária '${recipientData.name}' cadastrada com sucesso!`, "success");
    closeModal();
  });

  // Drag and Drop listeners
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });

  function showAlert(message, type = "danger") {
    alertBox.textContent = message;
    alertBox.className = `alert alert-${type}`;
    alertBox.classList.remove("hidden");
  }

  function hideAlert() {
    alertBox.classList.add("hidden");
  }

  async function handleFile(file) {
    hideAlert();
    currentFile = file;

    const formData = new FormData();
    formData.append("file", file);

    try {
      btnDownloadXml.disabled = true;
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.error || "Erro ao processar o relatório.");
      }

      parsedProducts = data.products;

      // Update Dashboard Metrics
      metricFilename.textContent = data.filename;
      metricItemCount.textContent = data.summary.item_count;
      metricTotalQty.textContent = data.summary.total_quantity.toLocaleString("pt-BR");
      metricTotalValue.textContent = data.summary.total_value.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
      });

      metricsGrid.classList.remove("hidden");
      dataSection.classList.remove("hidden");
      btnDownloadXml.disabled = false;

      renderTable(parsedProducts);
      showAlert(`Relatório '${data.filename}' analisado com sucesso! ${data.summary.item_count} itens importados.`, "success");

    } catch (err) {
      showAlert(`Erro: ${err.message}`, "danger");
      metricsGrid.classList.add("hidden");
      dataSection.classList.add("hidden");
    }
  }

  function renderTable(products) {
    productsTableBody.innerHTML = "";

    products.forEach((p, idx) => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td style="color: var(--text-muted); font-size: 0.8rem;">${idx + 1}</td>
        <td><span class="badge-sku">${p.code}</span></td>
        <td style="font-weight: 500;">${p.description}</td>
        <td style="font-weight: 600; color: #a5b4fc;">${p.quantity}</td>
        <td>${p.unit_price.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</td>
        <td style="font-weight: 600; color: #38bdf8;">${p.total_price.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</td>
      `;

      productsTableBody.appendChild(tr);
    });
  }

  // Filter Table Products
  searchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase().trim();
    const filtered = parsedProducts.filter(p => 
      p.code.toLowerCase().includes(term) || p.description.toLowerCase().includes(term)
    );
    renderTable(filtered);
  });

  // Download XML Trigger
  btnDownloadXml.addEventListener("click", async () => {
    if (!currentFile) return;

    try {
      btnDownloadXml.disabled = true;
      btnDownloadXml.textContent = "Gerando XML...";

      const formData = new FormData();
      formData.append("file", currentFile);

      // Append custom recipient if configured
      const recipient = getStoredRecipient();
      if (recipient && recipient.cnpj && recipient.name) {
        formData.append("recipient_cnpj", recipient.cnpj);
        formData.append("recipient_name", recipient.name);
        if (recipient.ie) formData.append("recipient_ie", recipient.ie);
        if (recipient.phone) formData.append("recipient_phone", recipient.phone);
        if (recipient.street) formData.append("recipient_street", recipient.street);
        if (recipient.number) formData.append("recipient_number", recipient.number);
        if (recipient.complement) formData.append("recipient_complement", recipient.complement);
        if (recipient.bairro) formData.append("recipient_bairro", recipient.bairro);
        if (recipient.cityName) formData.append("recipient_city_name", recipient.cityName);
        if (recipient.uf) formData.append("recipient_uf", recipient.uf);
        if (recipient.cep) formData.append("recipient_cep", recipient.cep);
        if (recipient.cityCode) formData.append("recipient_city_code", recipient.cityCode);
      }

      const res = await fetch("/api/generate-xml", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Erro ao gerar XML da DANFE.");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `danfe_transferencia_${currentFile.name.replace(/\.[^/.]+$/, "")}.xml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

      showAlert("XML da DANFE gerado e baixado com sucesso!", "success");
    } catch (err) {
      showAlert(`Erro ao gerar XML: ${err.message}`, "danger");
    } finally {
      btnDownloadXml.disabled = false;
      btnDownloadXml.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        Baixar XML da DANFE
      `;
    }
  });

  // Initialize Badge State
  updateBadgeUI();
});
