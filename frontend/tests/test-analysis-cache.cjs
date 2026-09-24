const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = process.argv[2] || require('node:path').resolve(__dirname, '../..');
const disk = new Map();
let blocked = false;
function boot() {
  let ready;
  const alerts = [];
  const elements = new Map();
  const context = vm.createContext({
    console: { warn() {} },
    localStorage: {
      getItem: key => disk.get(key) ?? null,
      setItem: (key, value) => { if (blocked) throw Error('quota'); disk.set(key, value); },
      removeItem: key => disk.delete(key)
    },
    document: { getElementById: id => elements.get(id) || null,
      querySelectorAll: () => [], addEventListener: (_, fn) => { ready = fn; } },
    window: { addEventListener() {} },
    ModalController: class { updateBadgeUI() {} fillForm() {} },
    confirm: () => true,
    ApiClient: {}, escapeHtml: String
  });
  for (const file of ['config.js', 'services/storageManager.js', 'components/tableController.js', 'components/wizardController.js']) {
    vm.runInContext(fs.readFileSync(`${root}/frontend/js/${file}`, 'utf8')
      .replace(/^import .*;\r?\n/gm, '').replace(/export (const|class) /g, '$1 '), context);
  }
  const table = vm.runInContext('new TableController({onAlert: (...args) => globalThis.alerts.push(args)})',
    Object.assign(context, { alerts }));
  const storage = vm.runInContext('StorageManager', context);
  return { context, table, storage, elements, start() {
    const BaseTable = vm.runInContext('TableController', context);
    const BaseWizard = vm.runInContext('WizardController', context);
    context.TrackedTable = class extends BaseTable { constructor(args) { super(args); context.restoredTable = this; } };
    context.TrackedWizard = class extends BaseWizard { constructor(args) { super(args); context.restoredWizard = this; } };
    vm.runInContext(fs.readFileSync(`${root}/frontend/js/app.js`, 'utf8').replace(/^import .*;\r?\n/gm, '').replace('new TableController(', 'new TrackedTable(').replace('new WizardController(', 'new TrackedWizard('), context);
    ready();
  }, alerts };
}
const product = code => ({ sku: code, description: 'Produto', quantity: 2, unit_price: 3, total_price: 6 });
const first = boot();
first.table.setAnalysisResult({ approved_normal: [product('A'), product('B')],
  approved_reverse: [product('C')], removed_items: [product('D')], purchase_alerts: [product('D')], summary: {} }, 'vendas.xls');
function change(table, method, cls, value) {
  table[method]({ target: { dataset: { idx: '0' }, classList: { contains: c => c === cls }, value, closest: () => null } });
}
change(first.table, 'handleNormalInlineEdit', 'qty-input', '7');
change(first.table, 'handleReverseInlineEdit', 'price-input', '9');
first.table.handleNormalTableClicks({ target: { closest: selector => selector === '.btn-delete-row' ? { dataset: { idx: '1' } } : null } });
first.storage.saveBookmarks(['A']);
const second = boot();
second.start();
const restored = second.context.restoredTable;
assert.equal(restored.data.filename, 'vendas.xls');
assert.equal(restored.data.approvedNormal.length, 1);
assert.equal(restored.data.approvedNormal[0].quantity, 7);
assert.equal(restored.data.approvedNormal[0].total_price, 21);
assert.equal(restored.data.approvedReverse[0].unit_price, 9);
assert.equal(restored.data.removedItems[0].sku, 'D');
assert.equal(restored.data.purchaseAlerts[0].sku, 'D');
assert.equal(second.storage.getBookmarks()[0], 'A');
assert.equal(second.context.restoredWizard.restoredFilename, 'vendas.xls');
blocked = true;
first.table.persistAnalysis();
assert.match(first.alerts.at(-1)[0], /Não foi possível salvar/);
blocked = false;
const empty = boot();
empty.table.setAnalysisResult({ approved_normal: [], approved_reverse: [], removed_items: [], purchase_alerts: [] });
assert.equal(empty.storage.getCachedAnalysis().approvedNormal.length, 0);
empty.storage.saveEmitter({ cnpj: 'matrix' });
empty.storage.saveRecipient({ cnpj: 'branch' });
assert.equal(empty.storage.purgeAllSessionData(), true);
assert.equal(empty.storage.getCachedAnalysis(), null);
assert.equal(empty.storage.getEmitter().cnpj, 'matrix');
assert.equal(empty.storage.getRecipient(), null);
disk.set('nfe_transfer_multi_analysis_v1', '{bad json');
assert.equal(boot().storage.getCachedAnalysis(), null);
console.log('PASS: bootstrap restoration, both directions, edits, deletion, alerts, bookmarks, empty result, purge, corrupt cache and quota failure');
