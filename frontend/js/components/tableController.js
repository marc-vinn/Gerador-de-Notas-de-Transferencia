/**
 * Table Controller Component
 * Manages 3-Tab Results Dashboard:
 * 1. Normal Transfer (Matrix -> Branch)
 * 2. Removed Items & Purchase Alerts
 * 3. Safe Reverse Transfer (Branch -> Matrix)
 */
import { escapeHtml } from "../utils/sanitizer.js";
import { StorageManager } from "../services/storageManager.js";
import { ApiClient } from "../services/apiClient.js";

export class TableController {
  constructor({ onAlert }) {
    this.onAlert = onAlert;

    // Current active tab ('normal', 'removed', 'reverse')
    this.activeTab = "normal";

    // Dataset collections from Option C Analysis
    this.data = {
      approvedNormal: [],
      removedItems: [],
      purchaseAlerts: [],
      approvedReverse: [],
      summary: {},
      filename: "relatorio.xls"
    };

    // DOM Elements
    this.dataSection = document.getElementById("dataSection");
    this.metricsGrid = document.getElementById("metricsGrid");

    this.tabBtnNormal = document.getElementById("tabBtnNormal");
    this.tabBtnRemoved = document.getElementById("tabBtnRemoved");
    this.tabBtnReverse = document.getElementById("tabBtnReverse");

    this.badgeNormalCount = document.getElementById("badgeNormalCount");
    this.badgeRemovedCount = document.getElementById("badgeRemovedCount");
    this.badgeReverseCount = document.getElementById("badgeReverseCount");

    this.tabContentNormal = document.getElementById("tabContentNormal");
    this.tabContentRemoved = document.getElementById("tabContentRemoved");
    this.tabContentReverse = document.getElementById("tabContentReverse");

    this.tbodyNormal = document.getElementById("tbodyNormal");
    this.tbodyRemoved = document.getElementById("tbodyRemoved");
    this.tbodyReverse = document.getElementById("tbodyReverse");

    this.searchInput = document.getElementById("searchInput");
    this.btnDownloadXmlNormal = document.getElementById("btnDownloadXmlNormal");
    this.btnDownloadXmlReverse = document.getElementById("btnDownloadXmlReverse");

    this.metricFilename = document.getElementById("metricFilename");
    this.metricItemCount = document.getElementById("metricItemCount");
    this.metricTotalQty = document.getElementById("metricTotalQty");
    this.metricTotalValue = document.getElementById("metricTotalValue");
    this.metricPurchaseAlerts = document.getElementById("metricPurchaseAlerts");

    this.initEvents();
  }

  initEvents() {
    this.tabBtnNormal?.addEventListener("click", () => this.switchTab("normal"));
    this.tabBtnRemoved?.addEventListener("click", () => this.switchTab("removed"));
    this.tabBtnReverse?.addEventListener("click", () => this.switchTab("reverse"));

    this.searchInput?.addEventListener("input", (e) => this.handleSearch(e.target.value));

    // Inline edit and actions delegation on normal and reverse tables
    this.tbodyNormal?.addEventListener("input", (e) => this.handleNormalInlineEdit(e));
    this.tbodyNormal?.addEventListener("click", (e) => this.handleNormalTableClicks(e));
    this.tbodyReverse?.addEventListener("input", (e) => this.handleReverseInlineEdit(e));
    this.tbodyReverse?.addEventListener("click", (e) => this.handleReverseTableClicks(e));

    // Download XML buttons
    this.btnDownloadXmlNormal?.addEventListener("click", () => this.downloadXml("matrix_to_branch"));
    this.btnDownloadXmlReverse?.addEventListener("click", () => this.downloadXml("branch_to_matrix"));
  }

  setAnalysisResult(result, filename = "relatorio.xls") {
    this.data.approvedNormal = result.approved_normal || [];
    this.data.removedItems = result.removed_items || [];
    this.data.purchaseAlerts = result.purchase_alerts || [];
    this.data.approvedReverse = result.approved_reverse || [];
    this.data.summary = result.summary || {};
    this.data.filename = filename || "relatorio.xls";

    if (this.dataSection) this.dataSection.classList.remove("hidden");
    if (this.metricsGrid) this.metricsGrid.classList.remove("hidden");

    this.updateBadges();
    this.updateMetrics();
    this.switchTab("normal");
    this.renderAll();
  }

  updateBadges() {
    if (this.badgeNormalCount) this.badgeNormalCount.textContent = this.data.approvedNormal.length;
    if (this.badgeRemovedCount) this.badgeRemovedCount.textContent = this.data.removedItems.length;
    if (this.badgeReverseCount) this.badgeReverseCount.textContent = this.data.approvedReverse.length;

    // Show reverse tab container only if there are reverse items or keep subtle
    if (this.tabBtnReverse) {
      if (this.data.approvedReverse.length > 0) {
        this.tabBtnReverse.classList.remove("hidden");
      } else {
        this.tabBtnReverse.classList.add("hidden");
      }
    }
  }

  updateMetrics() {
    const totalQty = this.data.approvedNormal.reduce((sum, p) => sum + (parseFloat(p.quantity) || 0), 0);
    const totalVal = this.data.approvedNormal.reduce((sum, p) => sum + (parseFloat(p.total_price) || 0), 0);

    if (this.metricFilename) this.metricFilename.textContent = this.data.filename || "-";
    if (this.metricItemCount) this.metricItemCount.textContent = this.data.approvedNormal.length;
    if (this.metricTotalQty) this.metricTotalQty.textContent = totalQty.toLocaleString("pt-BR", { maximumFractionDigits: 4 });
    if (this.metricTotalValue) {
      this.metricTotalValue.textContent = totalVal.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
      });
    }
    if (this.metricPurchaseAlerts) {
      this.metricPurchaseAlerts.textContent = this.data.purchaseAlerts.length;
    }

    if (this.btnDownloadXmlNormal) {
      this.btnDownloadXmlNormal.disabled = this.data.approvedNormal.length === 0;
    }
    if (this.btnDownloadXmlReverse) {
      this.btnDownloadXmlReverse.disabled = this.data.approvedReverse.length === 0;
    }
  }

  switchTab(tab) {
    this.activeTab = tab;

    this.tabBtnNormal?.classList.toggle("active", tab === "normal");
    this.tabBtnRemoved?.classList.toggle("active", tab === "removed");
    this.tabBtnReverse?.classList.toggle("active", tab === "reverse");

    this.tabContentNormal?.classList.toggle("hidden", tab !== "normal");
    this.tabContentRemoved?.classList.toggle("hidden", tab !== "removed");
    this.tabContentReverse?.classList.toggle("hidden", tab !== "reverse");

    this.handleSearch(this.searchInput?.value || "");
  }

  renderAll() {
    this.renderNormalTable();
    this.renderRemovedTable();
    this.renderReverseTable();
  }

  renderNormalTable(filteredList = null) {
    if (!this.tbodyNormal) return;
    this.tbodyNormal.innerHTML = "";

    const list = filteredList !== null ? filteredList : this.data.approvedNormal;
    const checkedCodes = StorageManager.getBookmarks();

    if (list.length === 0) {
      this.tbodyNormal.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            Nenhum produto aprovado para transferência Matriz → Filial.
          </td>
        </tr>
      `;
      return;
    }

    list.forEach((p, idx) => {
      const originalIdx = this.data.approvedNormal.indexOf(p);
      const isChecked = checkedCodes.includes(p.sku);
      const tr = document.createElement("tr");
      if (isChecked) tr.classList.add("row-bookmarked");

      const safeSku = escapeHtml(p.sku);
      const safeDesc = escapeHtml(p.description);
      const safeQty = parseFloat(p.quantity) || 0;
      const safeUnitPrice = (parseFloat(p.unit_price) || 0).toFixed(2);
      const safeTotal = (parseFloat(p.total_price) || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

      tr.innerHTML = `
        <td style="text-align: center;">
          <input type="checkbox" class="btn-bookmark-row" data-code="${safeSku}" title="Conferido" ${isChecked ? "checked" : ""}>
        </td>
        <td style="color: var(--text-muted); font-size: 0.8rem;">${idx + 1}</td>
        <td>
          <div class="sku-container">
            <span class="badge-sku">${safeSku}</span>
            <button type="button" class="btn-copy-sku" title="Copiar SKU" data-sku="${safeSku}">📋</button>
          </div>
        </td>
        <td style="font-weight: 500;">${safeDesc}</td>
        <td>
          <input type="number" class="input-table-edit qty-input" step="any" min="0" value="${safeQty}" data-idx="${originalIdx}">
        </td>
        <td>
          <input type="number" class="input-table-edit price-input" step="0.01" min="0" value="${safeUnitPrice}" data-idx="${originalIdx}">
        </td>
        <td class="row-total" style="font-weight: 600; color: #60a5fa;">
          ${safeTotal}
        </td>
        <td style="text-align: center;">
          <button type="button" class="btn-delete-row" title="Excluir produto" data-idx="${originalIdx}">🗑️</button>
        </td>
      `;

      this.tbodyNormal.appendChild(tr);
    });
  }

  renderRemovedTable(filteredList = null) {
    if (!this.tbodyRemoved) return;
    this.tbodyRemoved.innerHTML = "";

    const list = filteredList !== null ? filteredList : this.data.removedItems;

    if (list.length === 0) {
      this.tbodyRemoved.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            Nenhum item removido da transferência.
          </td>
        </tr>
      `;
      return;
    }

    list.forEach((p, idx) => {
      const tr = document.createElement("tr");

      const safeSku = escapeHtml(p.sku);
      const safeDesc = escapeHtml(p.description);
      const safeReason = escapeHtml(p.reason);

      let badgeHtml = "";
      if (p.need_purchase) {
        badgeHtml = `<span class="badge-status badge-purchase">⚠️ Necessidade de Compra</span>`;
      } else if (p.state === "FILIAL_E_MATRIZ_ESTAVEIS") {
        badgeHtml = `<span class="badge-status badge-stable">✅ Cobertura Suprida</span>`;
      } else {
        badgeHtml = `<span class="badge-status badge-info">🔄 Reversa Elegível</span>`;
      }

      const branchStockVal = parseFloat(p.branch_stock) || 0;
      const branchSalesWeek = parseFloat(p.branch_sales_week) || 0;
      const branchDemandMonth = parseFloat(p.branch_demand_month) || 0;

      const matrixStockVal = parseFloat(p.matrix_stock) || 0;
      const matrixSalesMonth = parseFloat(p.matrix_sales_month) || 0;

      tr.innerHTML = `
        <td style="color: var(--text-muted); font-size: 0.8rem;">${idx + 1}</td>
        <td>
          <span class="badge-sku">${safeSku}</span>
        </td>
        <td style="font-weight: 500;">${safeDesc}</td>
        <td style="font-size: 0.85rem; color: #cbd5e1;">${safeReason}</td>
        <td>
          <div class="stock-sales-group">
            <div class="metric-pill stock-pill" title="Saldo físico em estoque na filial">
              <span class="pill-label">📦 Estoque:</span>
              <strong class="pill-value">${branchStockVal} un</strong>
            </div>
            <div class="metric-pill sales-pill" title="Vendas da semana e projeção mensal de 4 semanas">
              <span class="pill-label">🛒 Vendas:</span>
              <span class="pill-value">${branchSalesWeek} un/sem <span class="pill-sub">(Mês: ${branchDemandMonth})</span></span>
            </div>
          </div>
        </td>
        <td>
          <div class="stock-sales-group">
            <div class="metric-pill stock-pill" title="Saldo físico em estoque na matriz">
              <span class="pill-label">📦 Estoque:</span>
              <strong class="pill-value">${matrixStockVal} un</strong>
            </div>
            <div class="metric-pill sales-pill" title="Volume vendido nos últimos 30 dias na matriz">
              <span class="pill-label">🛒 Vendas (30d):</span>
              <span class="pill-value">${matrixSalesMonth} un</span>
            </div>
          </div>
        </td>
        <td style="text-align: center;">${badgeHtml}</td>
      `;

      this.tbodyRemoved.appendChild(tr);
    });
  }

  renderReverseTable(filteredList = null) {
    if (!this.tbodyReverse) return;
    this.tbodyReverse.innerHTML = "";

    const list = filteredList !== null ? filteredList : this.data.approvedReverse;
    const checkedCodes = StorageManager.getBookmarks();

    if (list.length === 0) {
      this.tbodyReverse.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            Nenhum produto elegível para transferência reversa Filial → Matriz.
          </td>
        </tr>
      `;
      return;
    }

    list.forEach((p, idx) => {
      const originalIdx = this.data.approvedReverse.indexOf(p);
      const isChecked = checkedCodes.includes(p.sku);
      const tr = document.createElement("tr");
      if (isChecked) tr.classList.add("row-bookmarked");

      const safeSku = escapeHtml(p.sku);
      const safeDesc = escapeHtml(p.description);
      const safeQty = parseFloat(p.quantity) || 0;
      const safeUnitPrice = (parseFloat(p.unit_price) || 0).toFixed(2);
      const safeTotal = (parseFloat(p.total_price) || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

      tr.innerHTML = `
        <td style="text-align: center;">
          <input type="checkbox" class="btn-bookmark-row" data-code="${safeSku}" title="Conferido" ${isChecked ? "checked" : ""}>
        </td>
        <td style="color: var(--text-muted); font-size: 0.8rem;">${idx + 1}</td>
        <td>
          <div class="sku-container">
            <span class="badge-sku">${safeSku}</span>
            <button type="button" class="btn-copy-sku" title="Copiar SKU" data-sku="${safeSku}">📋</button>
          </div>
        </td>
        <td style="font-weight: 500;">${safeDesc}</td>
        <td>
          <input type="number" class="input-table-edit qty-input" step="any" min="0" value="${safeQty}" data-idx="${originalIdx}">
        </td>
        <td>
          <input type="number" class="input-table-edit price-input" step="0.01" min="0" value="${safeUnitPrice}" data-idx="${originalIdx}">
        </td>
        <td class="row-total" style="font-weight: 600; color: #34d399;">
          ${safeTotal}
        </td>
        <td style="text-align: center;">
          <button type="button" class="btn-delete-row" title="Excluir produto" data-idx="${originalIdx}">🗑️</button>
        </td>
      `;

      this.tbodyReverse.appendChild(tr);
    });
  }

  handleSearch(term) {
    const cleanTerm = (term || "").toLowerCase().trim();

    if (this.activeTab === "normal") {
      const filtered = this.data.approvedNormal.filter(p =>
        (p.sku || "").toLowerCase().includes(cleanTerm) ||
        (p.description || "").toLowerCase().includes(cleanTerm)
      );
      this.renderNormalTable(filtered);
    } else if (this.activeTab === "removed") {
      const filtered = this.data.removedItems.filter(p =>
        (p.sku || "").toLowerCase().includes(cleanTerm) ||
        (p.description || "").toLowerCase().includes(cleanTerm) ||
        (p.reason || "").toLowerCase().includes(cleanTerm)
      );
      this.renderRemovedTable(filtered);
    } else if (this.activeTab === "reverse") {
      const filtered = this.data.approvedReverse.filter(p =>
        (p.sku || "").toLowerCase().includes(cleanTerm) ||
        (p.description || "").toLowerCase().includes(cleanTerm)
      );
      this.renderReverseTable(filtered);
    }
  }

  handleNormalInlineEdit(e) {
    const target = e.target;
    if (!target.dataset.idx) return;

    const idx = parseInt(target.dataset.idx, 10);
    if (isNaN(idx) || idx < 0 || idx >= this.data.approvedNormal.length) return;

    if (target.classList.contains("qty-input")) {
      let val = parseFloat(target.value);
      if (isNaN(val) || val < 0) val = 0;
      this.data.approvedNormal[idx].quantity = val;
      this.data.approvedNormal[idx].total_price = Math.round(val * this.data.approvedNormal[idx].unit_price * 100) / 100;
    } else if (target.classList.contains("price-input")) {
      let val = parseFloat(target.value);
      if (isNaN(val) || val < 0) val = 0;
      this.data.approvedNormal[idx].unit_price = val;
      this.data.approvedNormal[idx].total_price = Math.round(this.data.approvedNormal[idx].quantity * val * 100) / 100;
    }

    const row = target.closest("tr");
    if (row) {
      const totalCell = row.querySelector(".row-total");
      if (totalCell) {
        totalCell.textContent = this.data.approvedNormal[idx].total_price.toLocaleString("pt-BR", {
          style: "currency",
          currency: "BRL"
        });
      }
    }

    this.updateMetrics();
  }

  handleNormalTableClicks(e) {
    const checkbox = e.target.closest(".btn-bookmark-row");
    if (checkbox) {
      const code = checkbox.dataset.code;
      const codes = StorageManager.getBookmarks();
      const idx = codes.indexOf(code);
      if (idx === -1) codes.push(code);
      else codes.splice(idx, 1);
      StorageManager.saveBookmarks(codes);
      checkbox.closest("tr")?.classList.toggle("row-bookmarked", idx === -1);
      return;
    }

    const copyBtn = e.target.closest(".btn-copy-sku");
    if (copyBtn) {
      const sku = copyBtn.dataset.sku;
      if (sku) {
        navigator.clipboard.writeText(sku).then(() => {
          const original = copyBtn.innerHTML;
          copyBtn.innerHTML = "✓";
          copyBtn.classList.add("copied");
          setTimeout(() => {
            copyBtn.innerHTML = original;
            copyBtn.classList.remove("copied");
          }, 1500);
        });
      }
      return;
    }

    const deleteBtn = e.target.closest(".btn-delete-row");
    if (deleteBtn) {
      const idx = parseInt(deleteBtn.dataset.idx, 10);
      if (isNaN(idx) || idx < 0 || idx >= this.data.approvedNormal.length) return;
      this.data.approvedNormal.splice(idx, 1);
      this.updateBadges();
      this.updateMetrics();
      this.handleSearch(this.searchInput?.value);
    }
  }

  handleReverseInlineEdit(e) {
    const target = e.target;
    if (!target.dataset.idx) return;

    const idx = parseInt(target.dataset.idx, 10);
    if (isNaN(idx) || idx < 0 || idx >= this.data.approvedReverse.length) return;

    if (target.classList.contains("qty-input")) {
      let val = parseFloat(target.value);
      if (isNaN(val) || val < 0) val = 0;
      this.data.approvedReverse[idx].quantity = val;
      this.data.approvedReverse[idx].total_price = Math.round(val * this.data.approvedReverse[idx].unit_price * 100) / 100;
    } else if (target.classList.contains("price-input")) {
      let val = parseFloat(target.value);
      if (isNaN(val) || val < 0) val = 0;
      this.data.approvedReverse[idx].unit_price = val;
      this.data.approvedReverse[idx].total_price = Math.round(this.data.approvedReverse[idx].quantity * val * 100) / 100;
    }

    const row = target.closest("tr");
    if (row) {
      const totalCell = row.querySelector(".row-total");
      if (totalCell) {
        totalCell.textContent = this.data.approvedReverse[idx].total_price.toLocaleString("pt-BR", {
          style: "currency",
          currency: "BRL"
        });
      }
    }

    this.updateBadges();
    this.updateMetrics();
  }

  handleReverseTableClicks(e) {
    const checkbox = e.target.closest(".btn-bookmark-row");
    if (checkbox) {
      const code = checkbox.dataset.code;
      const codes = StorageManager.getBookmarks();
      const idx = codes.indexOf(code);
      if (idx === -1) codes.push(code);
      else codes.splice(idx, 1);
      StorageManager.saveBookmarks(codes);
      checkbox.closest("tr")?.classList.toggle("row-bookmarked", idx === -1);
      return;
    }

    const copyBtn = e.target.closest(".btn-copy-sku");
    if (copyBtn) {
      const sku = copyBtn.dataset.sku;
      if (sku) {
        navigator.clipboard.writeText(sku).then(() => {
          const original = copyBtn.innerHTML;
          copyBtn.innerHTML = "✓";
          copyBtn.classList.add("copied");
          setTimeout(() => {
            copyBtn.innerHTML = original;
            copyBtn.classList.remove("copied");
          }, 1500);
        });
      }
      return;
    }

    const deleteBtn = e.target.closest(".btn-delete-row");
    if (deleteBtn) {
      const idx = parseInt(deleteBtn.dataset.idx, 10);
      if (isNaN(idx) || idx < 0 || idx >= this.data.approvedReverse.length) return;
      this.data.approvedReverse.splice(idx, 1);
      this.updateBadges();
      this.updateMetrics();
      this.handleSearch(this.searchInput?.value);
    }
  }

  async downloadXml(direction = "matrix_to_branch") {
    const isReverse = direction === "branch_to_matrix";
    const products = isReverse ? this.data.approvedReverse : this.data.approvedNormal;
    const btn = isReverse ? this.btnDownloadXmlReverse : this.btnDownloadXmlNormal;

    if (!products || products.length === 0) {
      this.onAlert?.("Nenhum produto disponível para exportar na DANFE XML.", "danger");
      return;
    }

    const emitter = StorageManager.getEmitter();
    if (!emitter || !emitter.cnpj || !emitter.name || !emitter.uf) {
      this.onAlert?.("⚠️ Operação bloqueada: A Empresa Emitente (Matriz) deve estar cadastrada com CNPJ, Razão Social e UF antes de gerar a DANFE XML.", "warning");
      window.dispatchEvent(new CustomEvent("open-company-modal", { detail: { tab: "emitter" } }));
      return;
    }

    const recipient = StorageManager.getRecipient();
    if (!recipient || !recipient.cnpj || !recipient.name || !recipient.uf) {
      this.onAlert?.("⚠️ Operação bloqueada: A Empresa Destinatária (Filial) deve estar cadastrada com CNPJ, Razão Social e UF antes de gerar a DANFE XML.", "warning");
      window.dispatchEvent(new CustomEvent("open-company-modal", { detail: { tab: "recipient" } }));
      return;
    }

    try {
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Gerando XML...";
      }

      const baseFilename = this.data.filename || "transferencia.xls";

      const blob = await ApiClient.generateXml({
        filename: baseFilename,
        products: products,
        emitter: emitter,
        recipient: recipient,
        direction: direction
      });

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const cleanBase = baseFilename.replace(/\.[^/.]+$/, "");
      const prefix = isReverse ? "nfe_transferencia_reversa" : "nfe_transferencia";
      a.download = `${prefix}_${cleanBase}.xml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

      this.onAlert?.(`XML da DANFE (${isReverse ? 'Filial → Matriz' : 'Matriz → Filial'}) baixado com sucesso!`, "success");
    } catch (err) {
      this.onAlert?.(`Erro ao gerar XML: ${err.message}`, "danger");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = isReverse ? "Baixar XML DANFE Inversa (Filial → Matriz)" : "Baixar XML da DANFE";
      }
    }
  }
}
