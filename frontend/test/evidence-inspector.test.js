import test from 'node:test';
import assert from 'node:assert/strict';
import { App } from '../app.js';

// Regression: list-valued filing evidence (e.g. EV-issue-ofs_sellers)
// carries a recorded quotation and FILING verification but no scalar
// extracted_value. The inspector previously let the missing scalar take
// precedence and labelled it "UNKNOWN / UNVERIFIED (Missing or
// Incomplete Data)", misrepresenting recorded filing provenance.

function makeSlot() {
  return {
    innerHTML: '',
    querySelector: () => null,
  };
}

function renderInspector(item) {
  const app = new App();
  const slot = makeSlot();
  const original = globalThis.document;
  globalThis.document = { getElementById: (id) => (id === 'evidence-inspector-slot' ? slot : null) };
  try {
    app.openEvidenceInspector(item);
  } finally {
    globalThis.document = original;
  }
  return slot.innerHTML;
}

const SELLER_LIST_ITEM = {
  evidence_id: 'EV-issue-ofs_sellers',
  field: 'issue.ofs_sellers',
  source: 'RHP-FILING-644be76e',
  document: 'filing.pdf',
  page: 1,
  locator: 'Cover page, Details of the Offer for Sale',
  quote: 'VAMAN PRESTRESSING COMPANY PRIVATE LIMITED ("SELLING SHAREHOLDER")',
  quote_kind: 'RECORDED',
  verification: 'FILING',
  extracted_value: null,
  value_summary: '1 entries: VAMAN PRESTRESSING COMPANY PRIVATE LIMITED',
  extraction_method: 'DETERMINISTIC_PDF',
  unit: null,
  note: null,
};

test('Evidence inspector - recorded filing list evidence is not UNKNOWN/UNVERIFIED', () => {
  const html = renderInspector(SELLER_LIST_ITEM);
  assert.ok(!html.includes('UNKNOWN / UNVERIFIED'), html.slice(0, 400));
  assert.ok(html.includes('SOURCE EVIDENCE (Extracted from Filing)'));
  // The structured summary is shown; no scalar value is invented.
  assert.ok(html.includes('1 entries: VAMAN PRESTRESSING COMPANY PRIVATE LIMITED'));
});

test('Evidence inspector - genuinely absent evidence stays UNKNOWN/UNVERIFIED', () => {
  const html = renderInspector({
    ...SELLER_LIST_ITEM,
    evidence_id: 'EV-issue.post_issue_eps',
    quote: null,
    quote_kind: null,
    verification: 'UNVERIFIED',
    extracted_value: null,
    value_summary: null,
  });
  assert.ok(html.includes('UNKNOWN / UNVERIFIED (Missing or Incomplete Data)'));
});

test('Evidence inspector - derived value without quote stays DERIVED', () => {
  const html = renderInspector({
    ...SELLER_LIST_ITEM,
    evidence_id: 'EV-issue.ofs',
    quote: null,
    quote_kind: null,
    verification: 'DERIVED',
    extracted_value: 3300.0,
    value_summary: null,
    extraction_method: 'DERIVED',
  });
  assert.ok(html.includes('DERIVED VALUE (Engine-Computed Metric)'));
  assert.ok(!html.includes('UNKNOWN / UNVERIFIED'));
});
