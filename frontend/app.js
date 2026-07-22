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

  let currentFile = null;
  let parsedProducts = [];

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
      showAlert(`Relatório '${data.filename}' analisado com sucesso! 72 itens importados.`, "success");

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
    const term = e.target.value.toLowerCase().strip ? e.target.value.toLowerCase().strip() : e.target.value.toLowerCase();
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
});
