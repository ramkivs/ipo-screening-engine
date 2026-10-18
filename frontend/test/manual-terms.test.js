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

test('Step5 App - manual panel offers all four required terms and marks non-enterable blockers', () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'awaiting',
    details: {
      missing_fields: ['price_band_low', 'price_band_high', 'lot_size', 'ofs', 'fresh_issue'],
      resolution: { reporting_unit: 'INR_LAKHS' },
    },
  }, 'final');
  const html = container.innerHTML;
  assert.ok(html.includes('AWAITING ISSUE TERMS'));
  assert.ok(html.includes('Manual entry is not official-source verification'));
  // All four issue terms are enterable, including issue.ofs.
  assert.ok(html.includes('may be entered manually below'));
  assert.ok(html.includes('id="mt-price-band-low"'));
  assert.ok(html.includes('id="mt-price-band-high"'));
  assert.ok(html.includes('id="mt-lot-size"'));
  assert.ok(html.includes('id="mt-ofs"'));
  assert.ok(html.includes('Offer For Sale (OFS)'));
  // The OFS field states the canonical unit taken from the engine payload.
  assert.ok(html.includes('amount in ₹ lakh'));
  // Terms outside the manual contract (e.g. the fresh-issue amount) stay blockers.
  assert.ok(html.includes('cannot be entered manually'));
  assert.ok(html.includes('issue.fresh_issue'));
  // The workflow contract is stated: all four required, broker platform
  // source of values, unverified status, invalid/incomplete blocked.
  assert.ok(html.includes('All four issue terms above are required'));
  assert.ok(html.includes('broker platform'));
  assert.ok(html.includes('MANUAL_ENTRY'));
  assert.ok(html.includes('Invalid or incomplete values prevent evaluation'));
  assert.ok(html.includes('mt-explanation'));
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
