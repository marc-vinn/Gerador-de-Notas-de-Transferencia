const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = process.argv[2] || require('node:path').resolve(__dirname, '../..');
function element() {
  const classes = new Set();
  return { value: '', style: {}, textContent: '', events: {}, disabled: false,
    classList: { add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c),
      toggle: (c, force) => force ? classes.add(c) : classes.delete(c) },
    addEventListener(name, fn) { this.events[name] = fn; } };
}
const elements = new Map(['alertBox', 'btnClearAnalysis', 'analysisNotice', 'metricsGrid', 'dataSection',
  'uploadWizard', 'wizardSummaryBar', 'wizardSummaryDetails', 'btnWizardNext', 'btnWizardPrev',
  'wizardFileInput', 'btnDownloadXmlNormal', 'btnDownloadXmlReverse'].map(id => [id, element()]));
const disk = new Map();
let ready, pendingResolve, pendingReject, calls = 0;
const context = vm.createContext({ console, TypeError,
  FormData: class { append() {} },
  fetch: () => { calls++; return new Promise((resolve, reject) => { pendingResolve = resolve; pendingReject = reject; }); },
  localStorage: { getItem: key => disk.get(key) ?? null, setItem: (key, value) => disk.set(key, value), removeItem: key => disk.delete(key) },
  document: { getElementById: id => elements.get(id) || null, querySelectorAll: () => [], addEventListener: (_, fn) => { ready = fn; } },
  window: { addEventListener() {} }, ModalController: class {}, escapeHtml: String, sanitizeDigits: String
});
for (const file of ['config.js', 'services/storageManager.js', 'services/apiClient.js', 'components/tableController.js', 'components/wizardController.js']) {
  vm.runInContext(fs.readFileSync(`${root}/frontend/js/${file}`, 'utf8').replace(/^import .*;\r?\n/gm, '').replace(/export (const|class) /g, '$1 '), context);
}
const storage = vm.runInContext('StorageManager', context);
const row = { sku: 'OLD', quantity: 1, unit_price: 10, total_price: 10 };
storage.saveCachedAnalysis({ approvedNormal: [row], approvedReverse: [], removedItems: [], purchaseAlerts: [], filename: 'old.xls', summary: {} });
storage.saveEmitter({ cnpj: 'matrix' }); storage.saveRecipient({ cnpj: 'branch' });
vm.runInContext(fs.readFileSync(`${root}/frontend/js/app.js`, 'utf8').replace(/^import .*;\r?\n/gm, '')
  .replace('const tableController =', 'const tableController = globalThis.table =')
  .replace('const wizardController =', 'const wizardController = globalThis.wizard ='), context);
ready();
const {table, wizard} = context;
const files = () => Object.fromEntries(['branchSales','branchStock','matrixSales','matrixStock'].map(key => [key, {name: `${key}.xls`, size: 100}]));
const reply = { success: true, approved_normal: [{ ...row, sku: 'NEW' }], approved_reverse: [], removed_items: [], purchase_alerts: [], summary: {normal_items_count: 1} };
const respond = data => pendingResolve({ ok: true, text: async () => JSON.stringify(data) });
(async () => {
  assert.match(elements.get('analysisNotice').textContent, /anterior recuperada/);
  assert.equal(storage.getCachedAnalysis().completedAt, null);
  wizard.files = files();
  const first = wizard.runAnalysis();
  assert.equal(table.analysisBlocked, true);
  assert.equal(elements.get('dataSection').classList.contains('hidden'), true);
  await wizard.runAnalysis(); assert.equal(calls, 1);
  pendingReject(new TypeError('Failed to fetch')); await first;
  assert.match(elements.get('alertBox').textContent, /falha de conexão/);
  assert.equal(storage.getCachedAnalysis().approvedNormal[0].sku, 'OLD');
  assert.equal(elements.get('btnDownloadXmlNormal').disabled, true);
  const second = wizard.runAnalysis(); respond(reply); await second;
  assert.equal(table.analysisBlocked, false);
  assert.equal(storage.getCachedAnalysis().approvedNormal[0].sku, 'NEW');
  assert.match(elements.get('analysisNotice').textContent, /Análise concluída em/);
  const third = wizard.runAnalysis();
  elements.get('btnClearAnalysis').events.click();
  assert.equal(storage.getCachedAnalysis(), null);
  assert.equal(storage.getEmitter().cnpj, 'matrix');
  assert.equal(storage.getRecipient().cnpj, 'branch');
  assert.equal(elements.get('uploadWizard').classList.contains('hidden'), false);
  assert.equal(wizard.currentStep, 1);
  assert.equal(Object.values(wizard.files).every(f => f === null), true);
  respond(reply); await third;
  assert.equal(storage.getCachedAnalysis(), null);
  assert.equal(table.data.approvedNormal.length, 0);
  assert.match(elements.get('alertBox').textContent, /Análise apagada/);
  wizard.files = files();
  const fourth = wizard.runAnalysis(); respond({ success: true }); await fourth;
  assert.match(elements.get('alertBox').textContent, /incompleta/);
  assert.equal(table.analysisBlocked, true);
  console.log('PASS: cached provenance, network failure, stale results hidden, duplicate request blocked, success replacement, clear button, company preservation, late response ignored, malformed response rejected');
})().catch(err => { console.error(err); process.exitCode = 1; });
