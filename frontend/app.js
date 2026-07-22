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
    cep: document.getElementById("recipientCep")
  };

  let currentFile = null;
  let parsedProducts = [];

  // Load custom recipient configuration from localStorage
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
      destBadgeName.textContent = "ARBORETHO IMPORTS LTDA (Padrão)";
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
  }

  // Modal Handlers
  btnOpenModal.addEventListener("click", () => {
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
    showAlert("Configuração da destinatária restaurada para o padrão (Mesma Empresa).", "success");
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
      cep: fields.cep.value.trim()
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
