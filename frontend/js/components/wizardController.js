/**
 * Wizard Controller Component
 * Manages 4-step progressive spreadsheet upload, stepper dots, validation, and analysis trigger.
 */
import { CONFIG } from "../config.js";
import { ApiClient } from "../services/apiClient.js";
import { escapeHtml } from "../utils/sanitizer.js";

export class WizardController {
  constructor({ onAnalysisComplete, onAlert }) {
    this.onAnalysisComplete = onAnalysisComplete;
    this.onAlert = onAlert;

    this.currentStep = 1;
    this.totalSteps = 4;

    this.stepsMeta = [
      {
        id: 1,
        title: "1. Vendas da Semana (Filial)",
        subtitle: "Selecione a planilha com o histórico de vendas semanais da filial",
        key: "branchSales",
        label: "Relatório de Vendas Filial (.xls / .xlsx)"
      },
      {
        id: 2,
        title: "2. Estoque Atual (Filial)",
        subtitle: "Selecione a planilha com as posições de estoque da filial",
        key: "branchStock",
        label: "Relatório de Estoque Filial (.xls / .xlsx)"
      },
      {
        id: 3,
        title: "3. Vendas dos Últimos 30 Dias (Matriz)",
        subtitle: "Selecione a planilha com as vendas dos últimos 30 dias na matriz",
        key: "matrixSales",
        label: "Relatório de Vendas Matriz (.xls / .xlsx)"
      },
      {
        id: 4,
        title: "4. Estoque Atual (Matriz)",
        subtitle: "Selecione a planilha com as posições de estoque da matriz",
        key: "matrixStock",
        label: "Relatório de Estoque Matriz (.xls / .xlsx)"
      }
    ];

    this.files = {
      branchSales: null,
      branchStock: null,
      matrixSales: null,
      matrixStock: null
    };

    // DOM Elements
    this.wizardContainer = document.getElementById("uploadWizard");
    this.summaryBar = document.getElementById("wizardSummaryBar");
    this.summaryDetails = document.getElementById("wizardSummaryDetails");
    this.btnToggleWizard = document.getElementById("btnToggleWizard");
    this.btnMinimizeWizard = document.getElementById("btnMinimizeWizard");

    this.stepTitle = document.getElementById("wizardStepTitle");
    this.stepSubtitle = document.getElementById("wizardStepSubtitle");
    this.dropZone = document.getElementById("dropZone");
    this.fileInput = document.getElementById("wizardFileInput");
    this.fileInfoCard = document.getElementById("wizardFileInfo");
    this.fileNameDisplay = document.getElementById("wizardFileName");
    this.fileSizeDisplay = document.getElementById("wizardFileSize");
    this.btnRemoveFile = document.getElementById("btnRemoveWizardFile");

    this.btnPrev = document.getElementById("btnWizardPrev");
    this.btnNext = document.getElementById("btnWizardNext");
    this.stepperDots = document.querySelectorAll(".stepper-dot");

    this.initEvents();
    this.renderStep();
  }

  initEvents() {
    this.btnToggleWizard?.addEventListener("click", () => this.toggle());
    this.btnMinimizeWizard?.addEventListener("click", () => this.collapse());

    this.dropZone?.addEventListener("click", () => this.fileInput?.click());

    this.dropZone?.addEventListener("dragover", (e) => {
      e.preventDefault();
      this.dropZone.classList.add("drag-over");
    });

    this.dropZone?.addEventListener("dragleave", () => {
      this.dropZone.classList.remove("drag-over");
    });

    this.dropZone?.addEventListener("drop", (e) => {
      e.preventDefault();
      this.dropZone.classList.remove("drag-over");
      if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
        this.handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    this.fileInput?.addEventListener("change", (e) => {
      if (e.target?.files && e.target.files.length > 0) {
        this.handleFileSelected(e.target.files[0]);
      }
    });

    this.btnRemoveFile?.addEventListener("click", (e) => {
      e.stopPropagation();
      this.removeCurrentFile();
    });

    this.btnPrev?.addEventListener("click", () => this.prevStep());
    this.btnNext?.addEventListener("click", () => this.nextStep());
  }

  getCurrentMeta() {
    return this.stepsMeta[this.currentStep - 1];
  }

  handleFileSelected(file) {
    const ext = (file.name.split(".").pop() || "").toLowerCase();
    if (!CONFIG.SUPPORTED_EXTENSIONS.includes(ext)) {
      this.onAlert?.("Formato não suportado. Envie um arquivo .xls ou .xlsx.", "danger");
      return;
    }

    if (file.size > CONFIG.MAX_FILE_SIZE_BYTES) {
      this.onAlert?.("O arquivo excede o limite máximo permitido de 10MB.", "danger");
      return;
    }

    const currentMeta = this.getCurrentMeta();
    this.files[currentMeta.key] = file;
    this.renderStep();
    this.onAlert?.(`Arquivo '${file.name}' selecionado para a ${currentMeta.title}.`, "success");
  }

  removeCurrentFile() {
    const currentMeta = this.getCurrentMeta();
    this.files[currentMeta.key] = null;
    if (this.fileInput) this.fileInput.value = "";
    this.renderStep();
  }

  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.renderStep();
    }
  }

  async nextStep() {
    const currentMeta = this.getCurrentMeta();
    const currentFile = this.files[currentMeta.key];

    if (!currentFile) {
      this.onAlert?.(`Por favor selecione o arquivo da etapa: ${currentMeta.title}`, "danger");
      return;
    }

    if (this.currentStep < this.totalSteps) {
      this.currentStep++;
      this.renderStep();
    } else {
      await this.runAnalysis();
    }
  }

  async runAnalysis() {
    if (!this.files.branchSales || !this.files.branchStock || !this.files.matrixSales || !this.files.matrixStock) {
      this.onAlert?.("Todos os 4 relatórios devem ser carregados para processar a análise.", "danger");
      return;
    }

    try {
      this.btnNext.disabled = true;
      this.btnNext.textContent = "⏳ Analisando Estoque e Demandas...";
      this.onAlert?.("Processando os 4 relatórios e cruzando dados de filiais e matriz...", "info");

      const analysisResult = await ApiClient.analyzeMultiReports(this.files);
      this.onAlert?.(
        `Análise concluída com sucesso! ${analysisResult.summary.normal_items_count} itens aprovados para transferência Matriz → Filial.`,
        "success"
      );
      this.onAnalysisComplete?.(analysisResult, this.files);

    } catch (err) {
      this.onAlert?.(`Erro na análise: ${err.message}`, "danger");
    } finally {
      this.btnNext.disabled = false;
      this.renderStep();
    }
  }

  renderStep() {
    const meta = this.getCurrentMeta();
    const currentFile = this.files[meta.key];

    if (this.stepTitle) this.stepTitle.textContent = meta.title;
    if (this.stepSubtitle) this.stepSubtitle.textContent = meta.subtitle;

    // Update File Preview or Upload Dropzone
    if (currentFile) {
      if (this.fileInfoCard) this.fileInfoCard.classList.remove("hidden");
      if (this.dropZone) this.dropZone.classList.add("has-file");
      if (this.fileNameDisplay) this.fileNameDisplay.textContent = currentFile.name;
      if (this.fileSizeDisplay) {
        const sizeKb = (currentFile.size / 1024).toFixed(1);
        this.fileSizeDisplay.textContent = `${sizeKb} KB • Pronto para processamento`;
      }
    } else {
      if (this.fileInfoCard) this.fileInfoCard.classList.add("hidden");
      if (this.dropZone) this.dropZone.classList.remove("has-file");
    }

    // Navigation buttons state
    if (this.btnPrev) {
      this.btnPrev.disabled = this.currentStep === 1;
      this.btnPrev.style.visibility = this.currentStep === 1 ? "hidden" : "visible";
    }

    if (this.btnNext) {
      this.btnNext.disabled = !currentFile;
      if (this.currentStep === this.totalSteps) {
        this.btnNext.textContent = "Executar Análise de Transferência ⚡";
        this.btnNext.className = "btn-primary btn-wizard-action btn-wizard-finish";
      } else {
        this.btnNext.textContent = "Próxima Etapa →";
        this.btnNext.className = "btn-primary btn-wizard-action";
      }
    }

    // Stepper Dots Update
    this.stepperDots.forEach((dot, index) => {
      const stepNumber = index + 1;
      const hasFile = !!this.files[this.stepsMeta[index].key];

      dot.classList.remove("active", "completed");
      if (stepNumber === this.currentStep) {
        dot.classList.add("active");
      } else if (stepNumber < this.currentStep || hasFile) {
        dot.classList.add("completed");
      }
    });
  }

  collapse() {
    this.wizardContainer?.classList.add("hidden");
    this.summaryBar?.classList.remove("hidden");
    if (this.btnMinimizeWizard) this.btnMinimizeWizard.classList.remove("hidden");
    this.updateSummaryBar();
  }

  expand() {
    this.wizardContainer?.classList.remove("hidden");
    this.summaryBar?.classList.add("hidden");
    if (this.btnMinimizeWizard) this.btnMinimizeWizard.classList.remove("hidden");
  }

  toggle() {
    if (this.wizardContainer?.classList.contains("hidden")) {
      this.expand();
    } else {
      this.collapse();
    }
  }

  updateSummaryBar() {
    if (!this.summaryDetails) return;
    const fileCount = Object.values(this.files).filter(Boolean).length;
    const salesFileName = this.files.branchSales?.name || "";
    if (salesFileName) {
      this.summaryDetails.textContent = `${fileCount} relatórios carregados (${salesFileName} e outros)`;
    } else {
      this.summaryDetails.textContent = `${fileCount} relatórios carregados e analisados com sucesso`;
    }
  }

  reset() {
    this.currentStep = 1;
    this.files = {
      branchSales: null,
      branchStock: null,
      matrixSales: null,
      matrixStock: null
    };
    if (this.fileInput) this.fileInput.value = "";
    this.summaryBar?.classList.add("hidden");
    this.btnMinimizeWizard?.classList.add("hidden");
    this.wizardContainer?.classList.remove("hidden");
    this.renderStep();
  }
}

