import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiClient, ApiError } from '../api.js';
import { App } from '../app.js';

test('Activity ApiClient - startIngestion posts FormData to the start endpoint', async () => {
  const originalFetch = globalThis.fetch;
  let capturedUrl = null;
  let capturedOptions = null;
  try {
    globalThis.fetch = async (url, options) => {
      capturedUrl = url;
      capturedOptions = options;
      return { ok: true, status: 202, json: async () => ({ ingestion_id: 'ing-abc', status: 'RUNNING' }) };
    };
    const client = new ApiClient();
    const res = await client.startIngestion({ name: 'jio.pdf' }, { mode: 'final' });
    assert.equal(res.ingestion_id, 'ing-abc');
    assert.ok(capturedUrl.endsWith('/api/v1/ingestions/start'));
    assert.equal(capturedOptions.method, 'POST');
    assert.ok(capturedOptions.body instanceof FormData);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Activity ApiClient - getIngestionEvents forwards after_sequence', async () => {
  const originalFetch = globalThis.fetch;
  let capturedUrl = null;
  try {
    globalThis.fetch = async (url) => {
      capturedUrl = url;
      return { ok: true, status: 200, json: async () => ({ events: [] }) };
    };
    const client = new ApiClient();
    await client.getIngestionEvents('ing-abc', 7);
    assert.ok(capturedUrl.includes('/api/v1/ingestions/ing-abc/events'));
    assert.ok(capturedUrl.includes('after_sequence=7'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

function mockContainer() {
  const panel = { innerHTML: '' };
  return { panel, querySelector: (sel) => (sel === '#ingest-activity-panel' ? panel : null) };
}

test('Activity App - renders ordered backend events with terminal summary', () => {
  const app = new App();
  const container = mockContainer();
  app.renderIngestionActivity(container, {
    ingestion_id: 'ing-abc',
    filename: 'U72900GJ2019PLC110816_JIO.pdf',
    mode: 'final',
    status: 'BLOCKED',
    started_at: '2026-10-18T00:00:00Z',
    finished_at: '2026-10-18T00:00:05Z',
    evaluation_run: false,
    persisted: false,
    evaluation_id: null,
    missing_fields: ['issue.price_band_low', 'issue.ofs'],
    error_message: 'AWAITING_ISSUE_TERMS: required issue terms are unavailable.',
    events: [
      { sequence: 1, stage: 'upload', event_type: 'received', status: 'SUCCEEDED', message: 'Upload received.', details: {} },
      { sequence: 2, stage: 'official_discovery', event_type: 'source_attempt', status: 'FAILED', message: 'official-discovery: UNAVAILABLE -- returned the exchange homepage', details: { provider: 'official-discovery' } },
      { sequence: 3, stage: 'evaluation', event_type: 'not_run', status: 'SKIPPED', message: 'Evaluation was not run.', details: {} },
    ],
  });
  const html = container.panel.innerHTML;
  assert.ok(html.includes('Ingestion Activity'));
  assert.ok(html.includes('BLOCKED'));
  assert.ok(html.includes('returned the exchange homepage'));
  assert.ok(html.includes('issue.ofs'));
  assert.ok(html.includes('Evaluation run: <strong>no</strong>'));
  assert.ok(html.includes('Persisted: <strong>no</strong>'));
  // ordered rendering: sequence 1 appears before sequence 3
  assert.ok(html.indexOf('Upload received.') < html.indexOf('Evaluation was not run.'));
});

test('Activity App - untrusted diagnostic text is escaped, never raw HTML', () => {
  const app = new App();
  const container = mockContainer();
  app.renderIngestionActivity(container, {
    ingestion_id: 'ing-x',
    filename: '<script>alert(1)</script>.pdf',
    mode: 'final',
    status: 'FAILED',
    started_at: '2026-10-18T00:00:00Z',
    finished_at: '2026-10-18T00:00:01Z',
    evaluation_run: false,
    persisted: false,
    events: [
      { sequence: 1, stage: 'official_discovery', event_type: 'source_attempt', status: 'FAILED', message: '<img src=x onerror=alert(1)>', details: {} },
    ],
  });
  const html = container.panel.innerHTML;
  assert.ok(!html.includes('<script>alert(1)</script>'));
  assert.ok(!html.includes('<img src=x onerror=alert(1)>'));
  assert.ok(html.includes('&lt;'));
});
