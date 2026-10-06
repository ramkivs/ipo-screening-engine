import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ApiClient, ApiError } from '../api.js';
import { App } from '../app.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// -----------------------------------------------------------------------------
// 1. ApiClient Ingestion Protocol Tests
// -----------------------------------------------------------------------------

test('UI-7 ApiClient - ingestDocument builds FormData and transmits to endpoint', async () => {
  const mockResponse = {
    evaluation_id: 'APEX-HOUSING-FINANCE-LIMITED-20261006-120000Z-final-79385bca',
    ipo_id: 'APEX-HOUSING-FINANCE-LIMITED',
    company_name: 'APEX HOUSING FINANCE LIMITED',
    evaluation_mode: 'FINAL',
    result_hash: '79385bca35358a030d61d5e12d16f6fb78b9183f2e99971aa8d82aec7dd88cfa',
    final_score: 40.0,
    verdict: 'INSUFFICIENT_DATA',
    confidence: 'Low',
    is_duplicate: false,
    message: 'Filing successfully ingested, extracted, and evaluated.',
    evaluation_url: '/#evaluations/APEX-HOUSING-FINANCE-LIMITED-20261006-120000Z-final-79385bca',
    evaluation: null
  };

  const originalFetch = globalThis.fetch;
  let capturedUrl = null;
  let capturedOptions = null;

  try {
    globalThis.fetch = async (url, options) => {
      capturedUrl = url;
      capturedOptions = options;
      return {
        ok: true,
        status: 201,
        json: async () => mockResponse
      };
    };

    const client = new ApiClient();
    const fakeFile = { name: 'sample_rhp.pdf', size: 1024, type: 'application/pdf' };
    const res = await client.ingestDocument(fakeFile, { mode: 'final' });

    assert.deepEqual(res, mockResponse);
    assert.ok(capturedUrl.endsWith('/api/v1/ingest/document'));
    assert.equal(capturedOptions.method, 'POST');
    assert.ok(capturedOptions.body instanceof FormData);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('UI-7 ApiClient - ingestDocument handles validation errors and payload limits', async () => {
  const client = new ApiClient();

  // Rejects null file
  await assert.rejects(
    async () => client.ingestDocument(null),
    (err) => {
      assert.ok(err instanceof ApiError);
      assert.equal(err.code, 'INVALID_FILE');
      return true;
    }
  );

  // Rejects 413 Payload Too Large from server
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: false,
      status: 413,
      json: async () => ({
        code: 'PAYLOAD_TOO_LARGE',
        message: 'File size exceeds 50 MB limit.'
      })
    });

    await assert.rejects(
      async () => client.ingestDocument({ name: 'huge.pdf' }),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 413);
        assert.equal(err.code, 'PAYLOAD_TOO_LARGE');
        assert.ok(err.message.includes('50 MB limit'));
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('UI-7 ApiClient - ingestDocument does not expose or send reference_base_path parameter', async () => {
  const originalFetch = globalThis.fetch;
  let capturedBody = null;

  try {
    globalThis.fetch = async (url, options) => {
      capturedBody = options.body;
      return {
        ok: true,
        status: 201,
        json: async () => ({ evaluation_id: 'test_eval' })
      };
    };

    const client = new ApiClient();
    const fakeFile = new Blob(['%PDF-1.4 mock content']);
    // Even if caller erroneously attempts to pass reference_base_path in options
    await client.ingestDocument(fakeFile, {
      mode: 'final',
      referenceBasePath: '/tmp/malicious/path.json',
      reference_base_path: '/tmp/malicious/path.json'
    });

    assert.ok(capturedBody instanceof FormData);
    assert.equal(capturedBody.get('reference_base_path'), null, 'FormData must not contain reference_base_path');
    assert.equal(capturedBody.get('referenceBasePath'), null, 'FormData must not contain referenceBasePath');
    assert.equal(capturedBody.get('mode'), 'final');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// -----------------------------------------------------------------------------
// 2. UI Upload Surface & Workflow Architecture Tests
// -----------------------------------------------------------------------------

test('UI-7 App - Ingestion View layout and Distinction Banner rendering', () => {
  const app = new App();

  // Create mock DOM container
  const dummyContainer = {
    innerHTML: '',
    querySelector: () => null,
    querySelectorAll: () => []
  };

  const originalGetElementById = globalThis.document ? globalThis.document.getElementById : undefined;
  globalThis.document = globalThis.document || {};
  globalThis.document.getElementById = (id) => {
    if (id === 'ingest-view') return dummyContainer;
    return null;
  };
  globalThis.document.querySelectorAll = () => [];

  try {
    app.renderIngestView();

    assert.ok(dummyContainer.innerHTML.includes('IPO Ingestion &amp; Deterministic Evaluation Pipeline'));
    assert.ok(dummyContainer.innerHTML.includes('UI-7 Architectural Boundary'));
    assert.ok(dummyContainer.innerHTML.includes('Zero Browser Authority'));
    assert.ok(dummyContainer.innerHTML.includes('Immutable Audit Trail'));
    assert.ok(dummyContainer.innerHTML.includes('id="ingest-dropzone"'));
    assert.ok(dummyContainer.innerHTML.includes('id="ingest-file-input"'));
    assert.ok(dummyContainer.innerHTML.includes('id="ingest-submit-btn"'));
    assert.ok(dummyContainer.innerHTML.includes('id="ingest-stages-list"'));
    assert.ok(dummyContainer.innerHTML.includes('stage-ready'));
    assert.ok(dummyContainer.innerHTML.includes('stage-upload'));
    assert.ok(dummyContainer.innerHTML.includes('stage-extract'));
    assert.ok(dummyContainer.innerHTML.includes('stage-evaluate'));
    assert.ok(dummyContainer.innerHTML.includes('stage-complete'));
  } finally {
    if (originalGetElementById) {
      globalThis.document.getElementById = originalGetElementById;
    }
  }
});

test('UI-7 App - Idempotency handling preserves existing evaluations without errors', async () => {
  const mockDuplicateResponse = {
    evaluation_id: 'APEX-HOUSING-FINANCE-LIMITED-20261006-120000Z-final-79385bca',
    ipo_id: 'APEX-HOUSING-FINANCE-LIMITED',
    company_name: 'APEX HOUSING FINANCE LIMITED',
    evaluation_mode: 'FINAL',
    result_hash: '79385bca35358a030d61d5e12d16f6fb78b9183f2e99971aa8d82aec7dd88cfa',
    final_score: 40.0,
    verdict: 'INSUFFICIENT_DATA',
    confidence: 'Low',
    is_duplicate: true,
    message: 'Identical evaluation record already exists in immutable store.',
    evaluation_url: '/#evaluations/APEX-HOUSING-FINANCE-LIMITED-20261006-120000Z-final-79385bca',
    evaluation: null
  };

  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: true,
      status: 200,
      json: async () => mockDuplicateResponse
    });

    const client = new ApiClient();
    const res = await client.ingestDocument(new Blob(['%PDF-1.4 mock']), { mode: 'final' });
    assert.equal(res.is_duplicate, true);
    assert.equal(res.evaluation_id, 'APEX-HOUSING-FINANCE-LIMITED-20261006-120000Z-final-79385bca');
    assert.ok(res.message.includes('already exists'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('UI-7 App - Helper formatBytes formats file sizes correctly', () => {
  const app = new App();
  assert.equal(app.formatBytes(0), '0 B');
  assert.equal(app.formatBytes(500), '500.0 B');
  assert.equal(app.formatBytes(1024), '1.0 KB');
  assert.equal(app.formatBytes(10 * 1024 * 1024), '10.0 MB');
  assert.equal(app.formatBytes(50 * 1024 * 1024), '50.0 MB');
});

test('UI-7 App - UI submission path invokes initialized ApiClient.ingestDocument without wiring errors', async () => {
  function makeMockElement(id = '') {
    const listeners = {};
    return {
      id,
      className: '',
      value: id === 'ingest-mode-select' ? 'final' : '',
      disabled: false,
      innerHTML: '',
      textContent: '',
      style: {},
      classList: { add: () => {}, remove: () => {} },
      addEventListener: (evt, fn) => {
        listeners[evt] = listeners[evt] || [];
        listeners[evt].push(fn);
      },
      trigger: async (evt, arg) => {
        if (listeners[evt]) {
          for (const fn of listeners[evt]) await fn(arg);
        }
      },
      querySelector: () => null,
      querySelectorAll: () => []
    };
  }

  const elements = {
    '#ingest-dropzone': makeMockElement('ingest-dropzone'),
    '#ingest-file-input': makeMockElement('ingest-file-input'),
    '#ingest-file-preview': makeMockElement('ingest-file-preview'),
    '#ingest-file-name': makeMockElement('ingest-file-name'),
    '#ingest-file-size': makeMockElement('ingest-file-size'),
    '#ingest-file-remove-btn': makeMockElement('ingest-file-remove-btn'),
    '#ingest-mode-select': makeMockElement('ingest-mode-select'),
    '#ingest-submit-btn': makeMockElement('ingest-submit-btn'),
    '#ingest-error-box': makeMockElement('ingest-error-box'),
    '#ingest-outcome-container': makeMockElement('ingest-outcome-container'),
    '#ingest-stages-list': makeMockElement('ingest-stages-list'),
    '#stage-ready': makeMockElement('stage-ready'),
    '#stage-upload': makeMockElement('stage-upload'),
    '#stage-extract': makeMockElement('stage-extract'),
    '#stage-evaluate': makeMockElement('stage-evaluate'),
    '#stage-complete': makeMockElement('stage-complete'),
  };

  const container = {
    querySelector: (sel) => elements[sel] || null,
    querySelectorAll: () => []
  };

  let capturedFile = null;
  let capturedOptions = null;
  const mockApi = {
    ingestDocument: async (file, options) => {
      capturedFile = file;
      capturedOptions = options;
      return {
        evaluation_id: 'R-K-FASHION-20261007-120000Z-final-12345678',
        ipo_id: 'R-K-FASHION',
        company_name: 'R.K Fashion accessories',
        evaluation_mode: 'FINAL',
        result_hash: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        final_score: 52.0,
        verdict: 'CONSIDER',
        confidence: 'Medium',
        is_duplicate: false,
        message: 'Filing successfully evaluated'
      };
    }
  };

  const app = new App(mockApi);
  app.bindIngestEvents(container);

  // User selects filing PDF (e.g. 16.5 MB real prospectus)
  const testFile = { name: 'U18109WB2010PLC144256-R.K Fashion accessories.pdf', size: 16.5 * 1024 * 1024, type: 'application/pdf' };
  app.selectedIngestFile = testFile;

  // Trigger submission
  await elements['#ingest-submit-btn'].trigger('click');

  // Assert API client was invoked directly without undefined reference error
  assert.equal(capturedFile, testFile);
  assert.deepEqual(capturedOptions, { mode: 'final' });
  assert.equal(elements['#ingest-error-box'].style.display, 'none');
  assert.equal(elements['#ingest-outcome-container'].style.display, 'block');
  assert.ok(elements['#ingest-outcome-container'].innerHTML.includes('R.K Fashion accessories'));
  assert.ok(elements['#ingest-outcome-container'].innerHTML.includes('52.0'));
});

test('UI-7 App - Zero client-side scoring / calculation invariant', () => {
  const appJsPath = path.resolve(__dirname, '../app.js');
  const appJs = fs.readFileSync(appJsPath, 'utf8');

  // Verify that ingestion workflow does not calculate scores in the browser
  assert.equal(appJs.includes('calculateScore'), false, 'app.js must not calculate scores');
  assert.equal(appJs.includes('deriveVerdict'), false, 'app.js must not derive verdicts');
  assert.equal(appJs.includes('computeResultHash'), false, 'app.js must not compute cryptographic hashes');

  // Verify no erroneous this.apiClient property accesses (must use this.api consistently)
  assert.equal(appJs.includes('this.apiClient'), false, 'app.js must not reference this.apiClient; use this.api consistently');

  // Verify no hardcoded credentials
  assert.equal(appJs.includes('API_KEY'), false);
  assert.equal(appJs.includes('AWS_SECRET'), false);
});
