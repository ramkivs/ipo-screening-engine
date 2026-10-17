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
      terms: { price_band_low: 208, price_band_high: 220, lot_size: 68 },
      explanation: 'exchange announcement dated 2026-10-10',
      confirmConflicts: false,
    });
    assert.equal(res.evaluation_id, 'E1');
    assert.ok(captured.url.includes('/ingest/manual-terms'));
    const body = captured.options.body;
    assert.equal(body.get('price_band_low'), '208');
    assert.equal(body.get('price_band_high'), '220');
    assert.equal(body.get('lot_size'), '68');
    assert.equal(body.get('explanation'), 'exchange announcement dated 2026-10-10');
    assert.equal(body.get('confirm_conflicts'), null);
    // No hidden route around validation: no path/fallback parameters exist.
    assert.equal(body.get('reference_base_path'), null);
    assert.equal(body.get('allow_fixture_fallbacks'), null);
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

test('Step5 App - manual panel lists missing terms and marks non-enterable blockers', () => {
  const app = new App();
  app.selectedIngestFile = new Blob(['%PDF-1.4']);
  const container = makePanelContainer();
  app.renderManualTermsPanel(container, {
    code: 'AWAITING_ISSUE_TERMS',
    message: 'awaiting',
    details: { missing_fields: ['price_band_low', 'lot_size', 'ofs'] },
  }, 'final');
  assert.ok(container.innerHTML.includes('AWAITING ISSUE TERMS'));
  assert.ok(container.innerHTML.includes('Manual entry is not official-source verification'));
  assert.ok(container.innerHTML.includes('cannot be entered manually'));
  assert.ok(container.innerHTML.includes('mt-explanation'));
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
        issue_terms: { manual_entry: { fields: ['price_band_low'] } },
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
  assert.ok(container.innerHTML.includes('Manually entered (unverified)'));
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
