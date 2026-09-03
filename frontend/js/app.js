/**
 * Main Application Bootstrapper
 * Coordinates Multi-Report Wizard, 3-Tab Table Dashboard, and Recipient Modal.
 */
import { StorageManager } from "./services/storageManager.js";
import { ModalController } from "./components/modalController.js";
import { TableController } from "./components/tableController.js";
import { WizardController } from "./components/wizardController.js";

document.addEventListener("DOMContentLoaded", () => {
  const alertBox = document.getElementById("alertBox");
  const btnPurgeSession = document.getElementById("btnPurgeSession");

  function showAlert(message, type = "danger") {
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.className = `alert alert-${type}`;
    alertBox.classList.remove("hidden");
  }

  function hideAlert() {
    if (!alertBox) return;
    alertBox.classList.add("hidden");
  }

  // Initialize Controllers
  const modalController = new ModalController({
    onAlert: showAlert
  });

  const tableController = new TableController({
    onAlert: showAlert
  });

  const wizardController = new WizardController({
    onAlert: showAlert,
    onAnalysisComplete: (result, files) => {
      const filename = files.branchSales?.name || "relatorio_transferencia.xls";
      tableController.setAnalysisResult(result, filename);
      wizardController.collapse();
    }
  });

  // Global Event Listener to open company modal on specific tab
  window.addEventListener("open-company-modal", (e) => {
    modalController.open(e.detail?.tab || "emitter");
  });

  // Purge Session Action
  btnPurgeSession?.addEventListener("click", () => {
    if (confirm("Deseja realmente limpar os relatórios e a sessão atual? (O cadastro da Matriz será preservado)")) {
      StorageManager.purgeAllSessionData(false);
      modalController.updateBadgeUI();
      modalController.fillForm();
      wizardController.reset();

      const dataSection = document.getElementById("dataSection");
      const metricsGrid = document.getElementById("metricsGrid");
      if (dataSection) dataSection.classList.add("hidden");
      if (metricsGrid) metricsGrid.classList.add("hidden");

      showAlert("Sessão limpa e assistente de importação reiniciado.", "info");
    }
  });
});
