import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiClient, ApiError } from '../api.js';
import { App } from '../app.js';

// Step 5 (Step 4 Area C): bounded manual issue-term entry UI workflow.
// Manual values are provenance-labelled MANUAL_ENTRY and never verified.

function makeElement(id = '') {
  return {
    id,
    value: '',
    checked: false,
    disabled: false,
    innerHTML: '',
    textContent: '',
    style: {},
    listeners: {},
    addEventListener(type, fn) { this.listeners[type] = fn; },
  };
}

function makePanelContainer() {
  const elements = new Map();
  const container = makeElement('outcome');
  container.querySelector = (selector) => {
    if (!elements.has(selector)) elements.set(selector, makeElement(selector));
    return elements.get(selector);
  };
  container.querySelectorAll = () => [];
  container._elements = elements;
  return container;
}

test('Step5 ApiClient - ingestManualTerms posts terms/explanation to the manual-terms endpoint', async () => {
  const originalFetch = globalThis.fetch;
  let captured = null;
  try {
    globalThis.fetch = async (url, options) => {
      captured = { url, options };
      return { ok: true, status: 201, json: async () => ({ evaluation_id: 'E1' }) };
    };
    const client = new ApiClient();
    const res = await client.ingestManualTerms(new Blob(['%PDF-1.4']), {
      mode: 'final',
      terms: { price_band_low: 208, price_band_high: 220, lot_size: 68, ofs: 3300 },
      explanation: 'exchange announcement dated 2026-10-10',
      confirmConflicts: false,
    });
    assert.equal(res.evaluation_id, 'E1');
    assert.ok(captured.url.includes('/ingest/manual-terms'));
    const body = captured.options.body;
    assert.equal(body.get('price_band_low'), '208');
    assert.equal(body.get('price_band_high'), '220');
    assert.equal(body.get('lot_size'), '68');
    assert.equal(body.get('ofs'), '3300');
    assert.equal(body.get('explanation'), 'exchange announcement dated 2026-10-10');
    assert.equal(body.get('confirm_conflicts'), null);
    // No hidden route around validation: no path/fallback parameters exist.
    assert.equal(body.get('reference_base_path'), null);
    assert.equal(body.get('allow_fixture_fallbacks'), null);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Step5 ApiClient - an explicit OFS of 0 is preserved and absent fields are never fabricated', async () => {
  const originalFetch = globalThis.fetch;
  let captured = null;
  try {
    globalThis.fetch = async (url, options) => {
      captured = { url, options };
      return { ok: true, status: 201, json: async () => ({ evaluation_id: 'E2' }) };
    };
    const client = new ApiClient();
    await client.ingestManualTerms(new Blob(['%PDF-1.4']), {
      mode: 'final',
      terms: { price_band_low: 208, price_band_high: 220, lot_size: 68, ofs: 0 },
      explanation: 'broker platform page shows no offer for sale',
    });
    const body = captured.options.body;
    // Explicit zero is an operator statement of "no OFS", preserved as-is.
    assert.equal(body.get('ofs'), '0');
    // A field the operator did not supply is simply absent: no defaults.
    const captured2 = { body: null };
    globalThis.fetch = async (url, options) => {
      captured2.body = options.body;
      return { ok: true, status: 201, json: async () => ({ evaluation_id: 'E3' }) };
    };
    await client.ingestManualTerms(new Blob(['%PDF-1.4']), {
      mode: 'final',
      terms: { price_band_low: 208, price_band_high: 220, lot_size: 68 },
      explanation: 'broker platform page',
    });
    assert.equal(captured2.body.get('ofs'), null);
    assert.equal(captured2.body.get('price_band_low'), '208');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Step5 ApiClient - conflict and awaiting payloads surface structured details', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: false,
      status: 409,
      json: async () => ({
        detail: {
          code: 'ISSUE_TERM_CONFLICT',
          message: 'conflict',
          conflicts: [{ field: 'issue.price_band_low', manual_value: 200, existing_value: 208, existing_origin: 'FILING_EXTRACTION' }],
        },
      }),
    });
    const client = new ApiClient();
    await assert.rejects(
      () => client.ingestManualTerms(new Blob(['%PDF-1.4']), { terms: { price_band_low: 200 }, explanation: 'x' }),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.code, 'ISSUE_TERM_CONFLICT');
        assert.equal(err.details.conflicts[0].existing_value, 208);
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Step5 App - manual panel offers all five enterable terms and marks non-enterable blockers', () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'awaiting',
    details: {
      missing_fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue', 'open_date'],
      resolution: { reporting_unit: 'INR_LAKHS' },
    },
  }, 'final');
  const html = container.innerHTML;
  assert.ok(html.includes('AWAITING ISSUE TERMS'));
  assert.ok(html.includes('Manual entry is not official-source verification'));
  // All five issue terms are enterable, including issue.ofs and the
  // fresh-issue amount (the Jio dead-end correction, 2026-10-19).
  assert.ok(html.includes('may be entered manually below'));
  assert.ok(html.includes('id="mt-price-band-low"'));
  assert.ok(html.includes('id="mt-price-band-high"'));
  assert.ok(html.includes('id="mt-lot-size"'));
  assert.ok(html.includes('id="mt-ofs"'));
  assert.ok(html.includes('id="mt-fresh-issue"'));
  assert.ok(html.includes('Offer For Sale (OFS)'));
  assert.ok(html.includes('Fresh Issue Amount'));
  // The monetary fields state the canonical unit from the engine payload.
  assert.ok(html.includes('amount in ₹ lakh'));
  // Terms outside the manual contract stay blockers.
  assert.ok(html.includes('cannot be entered manually'));
  assert.ok(html.includes('issue.open_date'));
  assert.ok(!html.includes('issue.fresh_issue</code> — <strong>cannot'));
  // The workflow contract is stated: all five required, broker platform
  // source of values, unverified status, invalid/incomplete blocked.
  assert.ok(html.includes('All five issue terms above are required'));
  assert.ok(html.includes('broker platform'));
  assert.ok(html.includes('MANUAL_ENTRY'));
  assert.ok(html.includes('Invalid or incomplete values prevent evaluation'));
  assert.ok(html.includes('mt-explanation'));
});

test('Step5 ApiClient - ingestManualTerms posts the fresh-issue amount including explicit 0', async () => {
  const originalFetch = globalThis.fetch;
  const captured = [];
  try {
    globalThis.fetch = async (url, options) => {
      captured.push({ url, options });
      return { ok: true, status: 201, json: async () => ({ evaluation_id: 'E2' }) };
    };
    const client = new ApiClient();
    await client.ingestManualTerms(new Blob(['%PDF-1.4']), {
      mode: 'final',
      terms: { price_band_low: 208, price_band_high: 220, lot_size: 68, ofs: 3300, fresh_issue: 14500 },
      explanation: 'broker platform IPO page',
    });
    await client.ingestManualTerms(new Blob(['%PDF-1.4']), {
      mode: 'final',
      terms: { fresh_issue: 0 },
      explanation: 'operator statement: pure-OFS offer',
    });
    assert.equal(captured[0].options.body.get('fresh_issue'), '14500');
    // Explicit 0 is an operator statement, preserved exactly (never omitted).
    assert.equal(captured[1].options.body.get('fresh_issue'), '0');
    assert.equal(captured[1].options.body.get('ofs'), null);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Step5 App - OFS unit label follows the reporting unit from the awaiting payload', () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const crores = makePanelContainer();
  app.renderManualTermsPanel(crores, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'awaiting',
    details: { missing_fields: ['ofs'], resolution: { reporting_unit: 'INR_CRORES' } },
  }, 'final');
  assert.ok(crores.innerHTML.includes('amount in ₹ crore'));
  const fallback = makePanelContainer();
  app.renderManualTermsPanel(fallback, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'awaiting',
    details: { missing_fields: ['ofs'] },
  }, 'final');
  assert.ok(fallback.innerHTML.includes('reporting unit'));
});

test('Step5 App - five-field submission posts the fresh-issue amount and shows it as manual', async () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const calls = [];
  app.api = {
    ingestManualTerms: async (file, options) => {
      calls.push(options);
      return {
        evaluation_id: 'EVAL-5', company_name: 'Jio', ipo_id: 'JIO', evaluation_mode: 'FINAL',
        final_score: 61.0, verdict: 'CONSIDER', is_duplicate: false,
        issue_terms: {
          status: 'UNAVAILABLE',
          manual_entry: {
            fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue'],
            values: { price_band_low: 1065, price_band_high: 1119, lot_size: 12, ofs: 0, fresh_issue: 1485000 },
            explanation: 'broker platform IPO page, 2026-10-19',
            provenance: 'MANUAL_ENTRY',
            verified: false,
            reporting_unit: 'INR_LAKHS',
          },
        },
      };
    },
  };
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS', message: 'awaiting',
    details: { missing_fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue'], resolution: { reporting_unit: 'INR_LAKHS' } },
  }, 'final');
  container.querySelector('#mt-price-band-low').value = '1065';
  container.querySelector('#mt-price-band-high').value = '1119';
  container.querySelector('#mt-lot-size').value = '12';
  container.querySelector('#mt-ofs').value = '0';
  container.querySelector('#mt-fresh-issue').value = '1485000';
  container.querySelector('#mt-explanation').value = 'broker platform IPO page, 2026-10-19';
  await container.querySelector('#mt-submit-btn').listeners.click();

  assert.equal(calls.length, 1);
  assert.equal(calls[0].terms.fresh_issue, 1485000);
  assert.equal(calls[0].terms.ofs, 0);
  const html = container.innerHTML;
  assert.ok(html.includes('MANUALLY ENTERED (Not Source-Verified)'));
  assert.ok(html.includes('issue.fresh_issue'));
  assert.ok(html.includes('1485000'));
});

test('Step5 App - four-field submission posts every supplied term including OFS', async () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const calls = [];
  app.api = {
    ingestManualTerms: async (file, options) => {
      calls.push(options);
      return {
        evaluation_id: 'EVAL-4', company_name: 'Acme', ipo_id: 'ACME', evaluation_mode: 'FINAL',
        final_score: 61.2, verdict: 'CONSIDER', is_duplicate: false,
        issue_terms: {
          status: 'UNAVAILABLE',
          manual_entry: {
            fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs'],
            values: { price_band_low: 208, price_band_high: 220, lot_size: 68, ofs: 3300 },
            explanation: 'broker platform IPO page, 2026-10-18',
            provenance: 'MANUAL_ENTRY',
            verified: false,
            reporting_unit: 'INR_LAKHS',
          },
        },
      };
    },
  };
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS', message: 'awaiting',
    details: { missing_fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs'] },
  }, 'final');
  container.querySelector('#mt-price-band-low').value = '208';
  container.querySelector('#mt-price-band-high').value = '220';
  container.querySelector('#mt-lot-size').value = '68';
  container.querySelector('#mt-ofs').value = '3300';
  container.querySelector('#mt-explanation').value = 'broker platform IPO page, 2026-10-18';
  await container.querySelector('#mt-submit-btn').listeners.click();

  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0].terms, { price_band_low: 208, price_band_high: 220, lot_size: 68, ofs: 3300 });
  // The result surface shows the exact evaluated values with manual provenance.
  const html = container.innerHTML;
  assert.ok(html.includes('MANUALLY ENTERED (Not Source-Verified)'));
  assert.ok(html.includes('issue.ofs'));
  assert.ok(html.includes('3300'));
  assert.ok(html.includes('208'));
  assert.ok(html.includes('MANUAL_ENTRY'));
  assert.ok(html.includes('broker platform IPO page, 2026-10-18'));
});

test('Step5 App - conflict blocks until explicitly confirmed, then proceeds unpromoted', async () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const calls = [];
  app.api = {
    ingestManualTerms: async (file, options) => {
      calls.push(options);
      if (!options.confirmConflicts) {
        const err = new ApiError(409, 'ISSUE_TERM_CONFLICT', 'conflict');
        err.details = { conflicts: [{ field: 'issue.price_band_low', manual_value: 200, existing_value: 208, existing_origin: 'FILING_EXTRACTION' }] };
        throw err;
      }
      return {
        evaluation_id: 'EVAL-1', company_name: 'Acme', ipo_id: 'ACME', evaluation_mode: 'FINAL',
        final_score: 40, verdict: 'INSUFFICIENT_DATA', is_duplicate: false,
        issue_terms: { manual_entry: { fields: ['price_band_low'], values: { price_band_low: 200 }, explanation: 'operator note' } },
      };
    },
  };
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS', message: 'awaiting', details: { missing_fields: ['price_band_low'] },
  }, 'final');

  container.querySelector('#mt-price-band-low').value = '200';
  container.querySelector('#mt-explanation').value = 'operator note';
  const submit = container.querySelector('#mt-submit-btn');

  // First submission: conflict surfaces, nothing proceeds.
  await submit.listeners.click();
  assert.equal(calls.length, 1);
  assert.equal(calls[0].confirmConflicts, false);
  assert.ok(container.querySelector('#mt-conflicts').innerHTML.includes('Conflicts must be resolved explicitly'));
  assert.ok(container.querySelector('#mt-conflicts').innerHTML.includes('never displaced'));

  // Clicking again without the confirmation tick stays blocked.
  await submit.listeners.click();
  assert.equal(calls.length, 1);
  assert.ok(container.querySelector('#mt-status').innerHTML.includes('Tick the confirmation'));

  // Tick + resubmit: proceeds, still labelled manual.
  container.querySelector('#mt-confirm-conflicts').checked = true;
  await submit.listeners.click();
  assert.equal(calls.length, 2);
  assert.equal(calls[1].confirmConflicts, true);
  assert.ok(container.innerHTML.includes('MANUALLY ENTERED (Not Source-Verified)'));
  assert.ok(container.innerHTML.includes('issue.price_band_low'));
  assert.ok(container.innerHTML.includes('200'));
  assert.ok(container.innerHTML.includes('Open Full Evaluation Scorecard'));
});

test('Step5 App - manual panel requires values and an explanation before submitting', async () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  let called = 0;
  app.api = { ingestManualTerms: async () => { called += 1; throw new Error('unreachable'); } };
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS', message: 'awaiting', details: { missing_fields: ['lot_size'] },
  }, 'final');
  const submit = container.querySelector('#mt-submit-btn');
  await submit.listeners.click();
  assert.equal(called, 0);
  assert.ok(container.querySelector('#mt-status').innerHTML.includes('Enter at least one term'));
  container.querySelector('#mt-lot-size').value = '68';
  await submit.listeners.click();
  assert.equal(called, 0);
  assert.ok(container.querySelector('#mt-status').innerHTML.includes('explanation is required'));
});

test('Step5 App - awaiting panel surfaces official-source resolution diagnostics', () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'awaiting',
    details: {
      missing_fields: ['price_band_low', 'ofs'],
      resolution: {
        providers: [
          { provider: 'official-prospectus', outcome: 'REJECTED', detail: 'retrieved document is not an established final Prospectus: no CIN' },
          { provider: 'official-url', outcome: 'UNAVAILABLE', detail: 'no official notice URL configured for this issuer' },
        ],
      },
    },
  }, 'final');
  assert.ok(container.innerHTML.includes('Official-source resolution diagnostics'));
  assert.ok(container.innerHTML.includes('official-prospectus'));
  assert.ok(container.innerHTML.includes('REJECTED'));
});

test('Step5 App - official-source diagnostics show UNAVAILABLE for the Windows failure pattern', () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'AWAITING_ISSUE_TERMS: required issue terms are unavailable.',
    details: {
      missing_fields: ['price_band_low', 'ofs'],
      resolution: {
        status: 'UNAVAILABLE',
        providers: [
          {
            provider: 'official-discovery',
            outcome: 'UNAVAILABLE',
            detail: 'no valid official listing could be retrieved: no issue entries in the served HTML; JavaScript application shell; listing retrieval failed (HTTPError)',
            listing_searched: false,
          },
        ],
      },
    },
  }, 'final');
  assert.ok(container.innerHTML.includes('Official-source resolution diagnostics'));
  assert.ok(container.innerHTML.includes('official-discovery'));
  assert.ok(container.innerHTML.includes('UNAVAILABLE'));
  assert.ok(!container.innerHTML.includes('UNPUBLISHED'));
});

test('Step5 App - every official source is shown with whether its listing was really searched', () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'AWAITING_ISSUE_TERMS: required issue terms are unavailable.',
    details: {
      missing_fields: ['price_band_low', 'ofs'],
      resolution: {
        status: 'UNAVAILABLE',
        providers: [
          {
            provider: 'official-discovery',
            outcome: 'UNAVAILABLE',
            detail: 'no valid official listing could be retrieved',
            listing_searched: false,
            searched_listings: [],
            sources: [
              { url: 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo', classification: 'empty', searched: false, issue_entries: 0, detail: 'no issue entries in the served HTML' },
              { url: 'https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&Type=P', classification: 'shell', searched: false, issue_entries: 0, detail: 'JavaScript application shell' },
              { url: 'https://www.bseindia.com/publicissue.html', classification: 'shell', searched: false, issue_entries: 0, detail: 'JavaScript application shell' },
              { url: 'https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes', classification: 'failed', searched: false, issue_entries: 0, detail: 'listing retrieval failed (HTTPError)' },
            ],
          },
        ],
      },
    },
  }, 'final');
  const html = container.innerHTML;
  assert.ok(html.includes('https://www.nseindia.com/market-data/all-upcoming-issues-ipo'));
  assert.ok(html.includes('https://www.bseindia.com/markets/PublicIssues/IPOIssues?id=1&amp;Type=P'));
  assert.ok(html.includes('https://www.sebi.gov.in/sebiweb/home/handleAction?doListing=yes'));
  assert.ok(html.includes('listing not searched'));
  assert.ok(!html.includes('listing searched ('));
  assert.ok(html.includes('UNAVAILABLE'));
  assert.ok(!html.includes('UNPUBLISHED'));
});

// ---------------------------------------------------------------------------
// Audit-log recording of manual issue-term submissions (2026-10-19).
// The manual submission has a durable ingestion-activity record; the
// UI/API path must preserve its correlation and present it (the defect:
// submissions were processed but the audit log "recorded nothing" --
// the error responses dropped the ingestion id and the manual flow
// never displayed the record).
// ---------------------------------------------------------------------------

async function withBrowserDoubles(run) {
  const originalDocument = globalThis.document;
  const originalLocalStorage = globalThis.localStorage;
  const store = new Map();
  const panelEl = makeElement('ingest-activity-panel');
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
  globalThis.document = {
    querySelector: (sel) => (sel === '#ingest-activity-panel' ? panelEl : null),
    getElementById: () => null,
  };
  try {
    return await run({ store, panelEl });
  } finally {
    globalThis.document = originalDocument;
    globalThis.localStorage = originalLocalStorage;
  }
}

test('Step5 ApiClient - ingestManualTerms errors preserve the audit-log correlation ids', async () => {
  const originalFetch = globalThis.fetch;
  try {
    // The local API's HTTPException handler returns the detail dict as
    // the flat error body (no `detail`/`error` nesting).
    globalThis.fetch = async () => ({
      ok: false,
      status: 400,
      json: async () => ({
        error: 'Bad Request',
        code: 'VALIDATION_ERROR',
        message: 'Manually entered issue.ofs must be zero or a positive amount.',
        issues: ['issue.ofs'],
        ingestion_id: 'ing-abc123',
        correlation_id: 'ing-abc123',
        activity_url: '/api/v1/ingestions/ing-abc123',
      }),
    });
    const client = new ApiClient();
    await assert.rejects(
      () => client.ingestManualTerms(new Blob(['%PDF-1.4']), {
        mode: 'final', terms: { ofs: -5 }, explanation: 'x',
      }),
      (err) => {
        // The defect: the id was previously dropped (and the flat error
        // contract unread), leaving the submission's audit record
        // unreachable from the failure.
        assert.equal(err.details.ingestion_id, 'ing-abc123');
        assert.equal(err.details.correlation_id, 'ing-abc123');
        assert.equal(err.details.activity_url, '/api/v1/ingestions/ing-abc123');
        return true;
      },
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Step5 App - successful manual submission registers and displays the audit record', async () => {
  await withBrowserDoubles(async ({ store, panelEl }) => {
    const app = new App();
    app.selectedIngestFile = new Blob(['%PDF-1.4']);
    let fetchedId = null;
    app.api = {
      ingestManualTerms: async () => ({
        evaluation_id: 'EVAL-9', company_name: 'Acme', ipo_id: 'ACME', evaluation_mode: 'FINAL',
        final_score: 61.2, verdict: 'CONSIDER', is_duplicate: false,
        ingestion_id: 'ing-audit1', correlation_id: 'ing-audit1',
        issue_terms: {
          manual_entry: {
            fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs'],
            values: { price_band_low: 208, price_band_high: 220, lot_size: 68, ofs: 3300 },
            explanation: 'broker platform IPO page', provenance: 'MANUAL_ENTRY', verified: false,
          },
        },
      }),
      getIngestion: async (id) => {
        fetchedId = id;
        return {
          ingestion_id: id, status: 'SUCCEEDED', evaluation_run: true, persisted: true,
          events: [
            { sequence: 1, stage: 'term_resolution', event_type: 'manual_submission', status: 'SUCCEEDED', message: 'received' },
            { sequence: 2, stage: 'term_resolution', event_type: 'manual_entry', status: 'SUCCEEDED', message: 'applied' },
          ],
        };
      },
    };
    const container = makePanelContainer();
    app.renderManualTermsPanel(container, {
      code: 'AWAITING_ISSUE_TERMS', message: 'awaiting',
      details: { missing_fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs'] },
    }, 'final');
    container.querySelector('#mt-price-band-low').value = '208';
    container.querySelector('#mt-price-band-high').value = '220';
    container.querySelector('#mt-lot-size').value = '68';
    container.querySelector('#mt-ofs').value = '3300';
    container.querySelector('#mt-explanation').value = 'broker platform IPO page';
    await container.querySelector('#mt-submit-btn').listeners.click();

    // The record is fetched and registered as the latest ingestion.
    assert.equal(fetchedId, 'ing-audit1');
    assert.equal(store.get('ipo.lastIngestionId'), 'ing-audit1');
    // The result panel shows the audit reference to the recorded trace.
    assert.ok(container.innerHTML.includes('ing-audit1'));
    assert.ok(container.innerHTML.includes('Audit trace recorded'));
    // The Ingestion Activity audit surface was refreshed with the record
    // (the panel within the "Workflow Progress & Audit Status" card).
    assert.ok(panelEl.innerHTML.includes('Ingestion Activity'));
    assert.ok(panelEl.innerHTML.includes('manual_submission'));
    assert.ok(panelEl.innerHTML.includes('manual_entry'));
    assert.ok(panelEl.innerHTML.includes('ing-audit1'));
  });
});

test('Step5 App - rejected manual submission shows its audit reference', async () => {
  await withBrowserDoubles(async ({ store, panelEl }) => {
    const app = new App();
    app.selectedIngestFile = new Blob(['%PDF-1.4']);
    app.api = {
      ingestManualTerms: async () => {
        const err = new ApiError(400, 'VALIDATION_ERROR', 'Manually entered issue.ofs must be zero or a positive amount.');
        err.details = {
          ingestion_id: 'ing-rej1', correlation_id: 'ing-rej1',
          activity_url: '/api/v1/ingestions/ing-rej1', issues: ['issue.ofs'],
        };
        throw err;
      },
      getIngestion: async (id) => ({
        ingestion_id: id, status: 'FAILED', error_code: 'VALIDATION_ERROR', evaluation_run: false, persisted: false,
        events: [
          { sequence: 1, stage: 'term_resolution', event_type: 'manual_submission', status: 'SUCCEEDED', message: 'received' },
          { sequence: 2, stage: 'term_resolution', event_type: 'manual_validation', status: 'FAILED', message: 'rejected' },
        ],
      }),
    };
    const container = makePanelContainer();
    app.renderManualTermsPanel(container, {
      code: 'AWAITING_ISSUE_TERMS', message: 'awaiting', details: { missing_fields: ['ofs'] },
    }, 'final');
    container.querySelector('#mt-ofs').value = '-5';
    container.querySelector('#mt-explanation').value = 'broker platform page';
    await container.querySelector('#mt-submit-btn').listeners.click();

    const status = container.querySelector('#mt-status').innerHTML;
    assert.ok(status.includes('VALIDATION_ERROR'));
    assert.ok(status.includes('ing-rej1'));
    // The rejected submission is registered and shown in the audit surface.
    assert.equal(store.get('ipo.lastIngestionId'), 'ing-rej1');
    assert.ok(panelEl.innerHTML.includes('manual_validation'));
  });
});

test('Step5 App - conflict response carries its audit reference', async () => {
  await withBrowserDoubles(async ({ store, panelEl }) => {
    const app = new App();
    app.selectedIngestFile = new Blob(['%PDF-1.4']);
    app.api = {
      ingestManualTerms: async () => {
        const err = new ApiError(409, 'ISSUE_TERM_CONFLICT', 'conflict');
        err.details = {
          ingestion_id: 'ing-conf1', correlation_id: 'ing-conf1',
          activity_url: '/api/v1/ingestions/ing-conf1',
          conflicts: [{ field: 'issue.price_band_low', manual_value: 200, existing_value: 208, existing_origin: 'FILING_EXTRACTION' }],
        };
        throw err;
      },
      getIngestion: async (id) => ({
        ingestion_id: id, status: 'BLOCKED', error_code: 'ISSUE_TERM_CONFLICT', evaluation_run: false, persisted: false,
        events: [{ sequence: 1, stage: 'term_resolution', event_type: 'conflict', status: 'BLOCKED', message: 'confirmation required' }],
      }),
    };
    const container = makePanelContainer();
    app.renderManualTermsPanel(container, {
      code: 'AWAITING_ISSUE_TERMS', message: 'awaiting', details: { missing_fields: ['price_band_low'] },
    }, 'final');
    container.querySelector('#mt-price-band-low').value = '200';
    container.querySelector('#mt-explanation').value = 'operator note';
    await container.querySelector('#mt-submit-btn').listeners.click();

    const status = container.querySelector('#mt-status').innerHTML;
    assert.ok(status.includes('ing-conf1'));
    assert.equal(store.get('ipo.lastIngestionId'), 'ing-conf1');
    assert.ok(panelEl.innerHTML.includes('conflict'));
  });
});

test('Step5 App - failures without an audit id keep the established unavailable wording', async () => {
  await withBrowserDoubles(async ({ store, panelEl }) => {
    const app = new App();
    app.selectedIngestFile = new Blob(['%PDF-1.4']);
    app.api = {
      ingestManualTerms: async () => {
        const err = new ApiError(500, 'INGESTION_INTERNAL_ERROR', 'Unexpected ingestion error');
        err.details = {};
        throw err;
      },
      getIngestion: async () => { throw new Error('unreachable'); },
    };
    const container = makePanelContainer();
    app.renderManualTermsPanel(container, {
      code: 'AWAITING_ISSUE_TERMS', message: 'awaiting', details: { missing_fields: ['ofs'] },
    }, 'final');
    container.querySelector('#mt-ofs').value = '3300';
    container.querySelector('#mt-explanation').value = 'note';
    await container.querySelector('#mt-submit-btn').listeners.click();
    assert.ok(container.querySelector('#mt-status').innerHTML.includes('INGESTION_INTERNAL_ERROR'));
    assert.equal(store.has('ipo.lastIngestionId'), false);
  });
});
