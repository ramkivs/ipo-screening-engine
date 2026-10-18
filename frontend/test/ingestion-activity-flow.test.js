import test from 'node:test';
import assert from 'node:assert/strict';
import { App } from '../app.js';

// Integration test: a real document submission through the ingest view
// must display the Ingestion Activity panel populated with the actual
// backend events -- including a failed (blocked) ingestion.  The API
// double implements only the activity endpoints (start/poll); if the
// submission flow fell back to the legacy synchronous ingestDocument
// path, this test would fail.

function makeEl(id = '') {
  const listeners = {};
  const children = {};
  return {
    id,
    className: '',
    value: id === 'ingest-mode-select' ? 'final' : '',
    disabled: false,
    innerHTML: '',
    textContent: '',
    style: {},
    classList: { add: () => {}, remove: () => {}, toggle: () => {} },
    addEventListener: (evt, fn) => {
      (listeners[evt] = listeners[evt] || []).push(fn);
    },
    trigger: async (evt, arg) => {
      for (const fn of listeners[evt] || []) await fn(arg);
    },
    querySelector: (sel) => (children[sel] = children[sel] || makeEl(sel)),
    querySelectorAll: () => [],
  };
}

const VIEW_IDS = [
  'ingest-dropzone', 'ingest-file-input', 'ingest-file-preview', 'ingest-file-name',
  'ingest-file-size', 'ingest-file-remove-btn', 'ingest-mode-select', 'ingest-submit-btn',
  'ingest-error-box', 'ingest-outcome-container', 'ingest-stages-list', 'stage-ready',
  'stage-upload', 'stage-extract', 'stage-evaluate', 'stage-complete', 'ingest-activity-panel',
];

function setupDom() {
  const elements = {};
  for (const id of VIEW_IDS) elements['#' + id] = makeEl(id);
  const container = {
    innerHTML: '',
    querySelector: (sel) => elements[sel] || null,
    querySelectorAll: () => [],
  };
  const originalDocument = globalThis.document;
  const originalWindow = globalThis.window;
  globalThis.document = {
    getElementById: (id) => (id === 'ingest-view' ? container : null),
    querySelectorAll: () => [],
  };
  globalThis.window = {
    location: { hash: '#ingest', origin: 'http://127.0.0.1:8000' },
    addEventListener: () => {},
  };
  globalThis.localStorage = {
    _m: {},
    getItem(k) { return this._m[k] || null; },
    setItem(k, v) { this._m[k] = v; },
  };
  return {
    container,
    elements,
    restore() {
      globalThis.document = originalDocument;
      globalThis.window = originalWindow;
      delete globalThis.localStorage;
    },
  };
}

const BLOCKED_RECORD = {
  ingestion_id: 'ing-flow1',
  filename: 'U72900GJ2019PLC110816_JIO.pdf',
  mode: 'final',
  status: 'BLOCKED',
  started_at: '2026-10-18T00:00:00Z',
  finished_at: '2026-10-18T00:00:04Z',
  evaluation_run: false,
  persisted: false,
  evaluation_id: null,
  missing_fields: ['issue.price_band_low', 'issue.ofs'],
  error_code: 'AWAITING_ISSUE_TERMS',
  error_message: 'AWAITING_ISSUE_TERMS: required issue terms are unavailable.',
  result: null,
  events: [
    { sequence: 1, stage: 'upload', event_type: 'received', status: 'SUCCEEDED', message: 'File received by the ingestion service.', details: {} },
    { sequence: 2, stage: 'filing_extraction', event_type: 'completed', status: 'SUCCEEDED', message: 'Filing extraction completed.', details: {} },
    { sequence: 3, stage: 'official_discovery', event_type: 'source_attempt', status: 'FAILED', message: 'official-discovery: UNAVAILABLE -- https://www.bseindia.com/...: returned the exchange homepage, not an issue listing', details: { provider: 'official-discovery', outcome: 'UNAVAILABLE' } },
    { sequence: 4, stage: 'evaluation', event_type: 'not_run', status: 'SKIPPED', message: 'Evaluation was not run; nothing was persisted.', details: {} },
    { sequence: 5, stage: 'finalization', event_type: 'terminated', status: 'BLOCKED', message: 'Ingestion blocked: see stage events.', details: {} },
  ],
};

test('Activity flow - panel is locatable before submission (visible shell)', () => {
  const { container, restore } = setupDom();
  try {
    const app = new App();
    app.api = { startIngestion: async () => ({}), getIngestion: async () => BLOCKED_RECORD };
    app.renderIngestView();
    assert.ok(container.innerHTML.includes('id="ingest-activity-panel"'));
    assert.ok(container.innerHTML.includes('Ingestion Activity'));
    assert.ok(container.innerHTML.includes('No ingestion submitted yet'));
  } finally {
    restore();
  }
});

test('Activity flow - submission displays panel with real backend events (failed ingestion)', async () => {
  const { container, elements, restore } = setupDom();
  try {
    const app = new App();
    let startedWith = null;
    app.api = {
      startIngestion: async (file, opts) => {
        startedWith = { file, opts };
        return { ingestion_id: 'ing-flow1', status: 'RUNNING' };
      },
      getIngestion: async () => BLOCKED_RECORD,
      // no ingestDocument: the legacy sync path must not be used
    };
    app.renderIngestView();
    app.selectedIngestFile = { name: 'U72900GJ2019PLC110816_JIO.pdf', size: 2048 };
    await elements['#ingest-submit-btn'].trigger('click');

    assert.ok(startedWith, 'submission must use the ingestion-start endpoint');
    assert.equal(startedWith.file.name, 'U72900GJ2019PLC110816_JIO.pdf');

    const panelHtml = elements['#ingest-activity-panel'].innerHTML;
    assert.ok(panelHtml.includes('Ingestion Activity'), 'panel heading rendered');
    assert.ok(panelHtml.includes('U72900GJ2019PLC110816_JIO.pdf'), 'file name shown');
    assert.ok(panelHtml.includes('returned the exchange homepage'), 'precise backend failure event shown');
    assert.ok(panelHtml.includes('Evaluation was not run'), 'skipped evaluation event shown');
    assert.ok(panelHtml.includes('Terminal summary'), 'terminal summary shown');
    assert.ok(panelHtml.includes('issue.price_band_low'), 'unresolved terms listed');
    assert.ok(panelHtml.includes('Evaluation run: <strong>no</strong>'));
    assert.ok(panelHtml.includes('Persisted: <strong>no</strong>'));
    assert.equal(globalThis.localStorage.getItem('ipo.lastIngestionId'), 'ing-flow1');
  } finally {
    restore();
  }
});
