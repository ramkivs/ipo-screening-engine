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

// The Windows acceptance failure (ingestion ing-5aa6dd92cd7640a8, at
// 3fea259): both BSE listings returned JavaScript shells, SEBI failed
// with an HTTPError and the NSE response carried only page chrome.
// The backend verdict is UNAVAILABLE -- the panel must say so, and
// must never present the unsubstantiated UNPUBLISHED conclusion.
const WINDOWS_PATTERN_EVENTS = [
  { sequence: 1, stage: 'upload', event_type: 'received', status: 'SUCCEEDED', message: 'Upload received.', details: {} },
  {
    sequence: 2, stage: 'official_discovery', event_type: 'source_attempt', status: 'FAILED',
    message: 'official-discovery: UNAVAILABLE -- no valid official listing could be retrieved',
    details: { provider: 'official-discovery', outcome: 'UNAVAILABLE', listing_searched: false },
  },
  {
    sequence: 3, stage: 'official_discovery', event_type: 'source_attempt', status: 'FAILED',
    message: 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo: returned a page with no recognizable listing content and no issue entries in the served HTML (the listing table may be populated by JavaScript; a listing was not searched)',
    details: { provider: 'official-discovery', outcome: 'UNAVAILABLE' },
  },
  {
    sequence: 4, stage: 'official_discovery', event_type: 'source_attempt', status: 'FAILED',
    message: 'https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P: returned a JavaScript application shell with no issue rows in the served HTML (a listing was not searched)',
    details: { provider: 'official-discovery', outcome: 'UNAVAILABLE' },
  },
  {
    sequence: 5, stage: 'official_discovery', event_type: 'source_attempt', status: 'FAILED',
    message: 'https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes&sid=1&ssid=7&smid=0: listing retrieval failed (HTTPError)',
    details: { provider: 'official-discovery', outcome: 'UNAVAILABLE' },
  },
  {
    sequence: 6, stage: 'official_discovery', event_type: 'completed', status: 'BLOCKED',
    message: 'Official discovery outcome: UNAVAILABLE.',
    details: { status: 'UNAVAILABLE' },
  },
  { sequence: 7, stage: 'evaluation', event_type: 'not_run', status: 'SKIPPED', message: 'Evaluation was not run; nothing was persisted.', details: {} },
  { sequence: 8, stage: 'persistence', event_type: 'not_attempted', status: 'SKIPPED', message: 'No evaluation artifact was persisted.', details: {} },
];

test('Activity App - the Windows failure pattern renders UNAVAILABLE and never UNPUBLISHED', () => {
  const app = new App();
  const container = mockContainer();
  app.renderIngestionActivity(container, {
    ingestion_id: 'ing-5aa6dd92cd7640a8',
    filename: 'U72900GJ2019PLC110816_JIO.pdf',
    mode: 'final',
    status: 'BLOCKED',
    started_at: '2026-10-18T00:00:00Z',
    finished_at: '2026-10-18T00:00:41Z',
    evaluation_run: false,
    persisted: false,
    evaluation_id: null,
    missing_fields: ['issue.price_band_low', 'issue.price_band_high', 'issue.lot_size', 'issue.ofs'],
    error_code: 'AWAITING_ISSUE_TERMS',
    error_message: 'AWAITING_ISSUE_TERMS: required issue terms are unavailable.',
    events: WINDOWS_PATTERN_EVENTS,
  });
  const html = container.panel.innerHTML;
  assert.ok(html.includes('Official discovery outcome: UNAVAILABLE'));
  assert.ok(!html.includes('UNPUBLISHED'), 'the unsubstantiated unpublished conclusion must never be shown');
  // every unusable source is visible with its own reason
  assert.ok(html.includes('no issue entries'), 'the chrome-only NSE response is reported');
  assert.ok(html.includes('shell'), 'the JavaScript shell listings are reported');
  assert.ok(html.includes('HTTPError'), 'the SEBI retrieval failure is reported');
  // the safeguards hold: nothing evaluated, nothing persisted
  assert.ok(html.includes('Evaluation run: <strong>no</strong>'));
  assert.ok(html.includes('Persisted: <strong>no</strong>'));
  assert.ok(html.includes('issue.price_band_low'));
});

test('Activity App - fresh-only blocker is not described as unpublished pricing or manual recovery', () => {
  const app = new App();
  const container = mockContainer();
  app.renderIngestionActivity(container, {
    ingestion_id: 'ing-controlled', status: 'BLOCKED', evaluation_run: false,
    persisted: false, missing_fields: ['issue.fresh_issue'], events: [],
  });
  const html = container.panel.innerHTML;
  assert.ok(html.includes('issue.fresh_issue'));
  assert.ok(html.includes('Evaluation run: <strong>no</strong>'));
  assert.ok(html.includes('Persisted: <strong>no</strong>'));
  assert.ok(html.includes('Retry automatic official discovery'));
  assert.ok(html.includes('Missing evidence does not prove that terms are unpublished'));
  assert.ok(!html.includes('use the bounded manual entry'));
  assert.ok(!html.includes('retry after the official terms are published'));
});
