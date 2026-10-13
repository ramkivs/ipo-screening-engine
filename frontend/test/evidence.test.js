import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ApiClient, ApiError } from '../api.js';
import { App } from '../app.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Mock evaluation & evidence fixtures
const mockEvaluation = {
  evaluation_id: "eval_20261006_vishal_001",
  ipo_id: "VISHAL-NIRMITI-LIMITED",
  company_name: "Vishal Nirmiti Limited",
  evaluation_mode: "FINAL",
  evaluation_timestamp: "2026-10-06T12:00:00Z",
  engine_version: "1.5.0",
  spec_version: "1.5",
  config_version: "1.5.0",
  config_hash: "cfghash_1234567890abcdef",
  input_snapshot_hash: "inphash_4388606993c604bb56d5f3cab1e9b061414fbfca63c6ac2c7b4e2638484f0614",
  source_manifest_hash: "manifesthash_3bd2a7b2f803afb46b0a2e4e455b8176c938c3c2c34164b37cac31c93de55fd7",
  result_hash: "e84f8bc0f9b942c43f937fa3b12fdba3c3ef23cc613e9d921a749b12955619e1",
  verdict: { verdict: "INSUFFICIENT_DATA" },
  score: {
    final_score: 35.0,
    base_score: 38.0,
    lower_bound: 25.0,
    upper_bound: 62.0,
    confidence: "LOW",
    completeness_pct: 73.0,
    available_points: 73.0,
    unknown_points: 27.0,
    penalties_total: 10.0,
    modules: []
  },
  knockouts: { status: "UNVERIFIED", rules: [] },
  penalties: [],
  missing_unverified: []
};

const mockEvidenceResponse = {
  evaluation_id: "eval_20261006_vishal_001",
  source_manifest_hash: "manifesthash_3bd2a7b2f803afb46b0a2e4e455b8176c938c3c2c34164b37cac31c93de55fd7",
  evidence_count: 4,
  items: [
    {
      evidence_id: "EV-cfo-fy26",
      field: "cfo_fy26",
      document: "VISHAL-NIRMITI-LIMITED-RHP.pdf",
      page: 74,
      locator: "Restated Statement of Cash Flows",
      quote: "Net cash generated from operating activities for Fiscal 2026 was ₹2,715.47 lakhs.",
      extracted_value: 27.15,
      unit: "INR_CRORES"
    },
    {
      evidence_id: "EV-pat-fy26",
      field: "pat_fy26",
      document: "VISHAL-NIRMITI-LIMITED-RHP.pdf",
      page: 72,
      locator: "Restated Statement of Profit and Loss",
      quote: "Profit after tax for the year ended March 31, 2026 stood at ₹1,518.52 lakhs.",
      extracted_value: 15.18,
      unit: "INR_CRORES"
    },
    {
      evidence_id: "EV-litigation-promoter",
      field: "promoter_litigation_count",
      document: "VISHAL-NIRMITI-LIMITED-RHP.pdf",
      page: 182,
      locator: "Outstanding Litigation and Material Developments",
      quote: "There are no outstanding criminal proceedings or material tax litigations against our Promoters.",
      extracted_value: 0,
      unit: "COUNT"
    },
    {
      evidence_id: "EV-going-concern",
      field: "going_concern_uncertainty",
      document: "VISHAL-NIRMITI-LIMITED-RHP.pdf",
      page: null,
      locator: null,
      quote: null,
      extracted_value: null,
      unit: null
    }
  ]
};

test('UI-3 ApiClient - getEvidence and getEvaluationEvidence protocols', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];

  try {
    globalThis.fetch = async (url) => {
      calls.push(url);
      return {
        ok: true,
        status: 200,
        json: async () => ({ status: 'ok' })
      };
    };

    const client = new ApiClient();
    await client.getEvaluationEvidence('eval_123');
    await client.getEvidence('EV-cfo-fy26');
    await client.getEvidence('eval_123:EV-cfo-fy26');

    assert.ok(calls[0].endsWith('/api/v1/evaluations/eval_123/evidence'));
    assert.ok(calls[1].endsWith('/api/v1/evidence/EV-cfo-fy26'));
    assert.ok(calls[2].endsWith('/api/v1/evidence/eval_123%3AEV-cfo-fy26'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('UI-3 ApiClient - rejects missing evidence identifiers', async () => {
  const client = new ApiClient();
  await assert.rejects(
    async () => client.getEvidence(''),
    (err) => {
      assert.ok(err instanceof ApiError);
      assert.equal(err.code, 'INVALID_IDENTIFIER');
      return true;
    }
  );
  await assert.rejects(
    async () => client.getEvaluationEvidence(null),
    (err) => {
      assert.ok(err instanceof ApiError);
      assert.equal(err.code, 'INVALID_IDENTIFIER');
      return true;
    }
  );
});

test('UI-3 App - Provenance & Cryptographic Audit Panel formatting', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.evidenceState = {
    evaluationId: mockEvaluation.evaluation_id,
    evaluation: mockEvaluation,
    evidenceResp: mockEvidenceResponse,
    filterText: '',
    category: 'ALL'
  };

  app.renderEvidenceExplorerContent(mockContainer);
  const html = mockContainer.innerHTML;

  // Asserts provenance panel exists and has ARIA landmark
  assert.ok(html.includes('role="region"'));
  assert.ok(html.includes('aria-label="Cryptographic Provenance Fingerprints"'));

  // Asserts all 4 cryptographic hashes are present
  assert.ok(html.includes(mockEvaluation.result_hash), 'Must include Result Hash');
  assert.ok(html.includes(mockEvaluation.source_manifest_hash), 'Must include Source Manifest Hash');
  assert.ok(html.includes(mockEvaluation.input_snapshot_hash), 'Must include Input Snapshot Hash');
  assert.ok(html.includes(mockEvaluation.config_hash), 'Must include Config Hash');

  // Asserts immutable label
  assert.ok(html.includes('IMMUTABLE RECORD'));

  // Asserts copy buttons
  assert.ok(html.includes(`data-copy="${mockEvaluation.result_hash}"`));
});

test('UI-3 App - Contract Guidance & Distinction between Source Evidence vs Derived Values', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.evidenceState = {
    evaluationId: mockEvaluation.evaluation_id,
    evaluation: mockEvaluation,
    evidenceResp: mockEvidenceResponse,
    filterText: '',
    category: 'ALL'
  };

  app.renderEvidenceExplorerContent(mockContainer);
  const html = mockContainer.innerHTML;

  // Verifies explicit contract guidance callout
  assert.ok(html.includes('Source Evidence vs. Derived Provenance'));
  assert.ok(html.includes('not direct quotes from source filings'));

  // Verifies badge distinction classes in CSS
  const stylesCss = fs.readFileSync(path.resolve(__dirname, '../styles.css'), 'utf8');
  assert.ok(stylesCss.includes('.badge-source-evidence'));
  assert.ok(stylesCss.includes('.badge-derived-value'));
  assert.ok(stylesCss.includes('.badge-unknown-evidence'));
});

test('UI-3 App - Verbatim Quote Preservation and Fail-Closed Unknown Semantics', () => {
  const app = new App();

  // Test item with quote
  const quoteItem = mockEvidenceResponse.items[0];
  assert.ok(quoteItem.quote.includes('2,715.47 lakhs'));

  // Test item with missing/null values
  const missingItem = mockEvidenceResponse.items[3];
  assert.equal(missingItem.extracted_value, null);
  assert.equal(missingItem.quote, null);

  // Fail-closed verification: null extracted value rendered as UNKNOWN, never 0.00
  const renderedUnknown = app.renderMetricValue(missingItem.extracted_value, 'UNKNOWN');
  assert.ok(renderedUnknown.includes('UNKNOWN'));
  assert.equal(renderedUnknown.includes('0.00'), false);
  assert.equal(renderedUnknown.includes('0'), false);
});

test('UI-3 App - Source document, page, and locator presentation security', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');

  // Ensure NO server filesystem paths are constructed or exposed
  assert.equal(appJs.includes('/home/user'), false);
  assert.equal(appJs.includes('/etc/'), false);
  assert.equal(appJs.includes('/var/'), false);
  assert.equal(appJs.includes('file://'), false);

  // Ensure document name is rendered with safe HTML escaping
  const app = new App();
  assert.equal(
    app.escape('VISHAL-NIRMITI-LIMITED-RHP.pdf'),
    'VISHAL-NIRMITI-LIMITED-RHP.pdf'
  );
  assert.equal(
    app.escape('<script>alert(1)</script>.pdf'),
    '&lt;script&gt;alert(1)&lt;/script&gt;.pdf'
  );
});

test('UI-3 App - Scorecard-to-evidence navigation integration', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');

  // Verify Scorecard header contains link to evidence explorer
  assert.ok(appJs.includes('#evidence/'), 'Scorecard must link to Evidence view #evidence/');
  assert.ok(appJs.includes('Inspect Evidence &amp; Provenance &rarr;'));

  // Verify Scorecard criteria rows link to evidence citations
  assert.ok(appJs.includes('Inspect Citation [EV] &rarr;'));

  // Verify Return to Scorecard link in Evidence Explorer
  assert.ok(appJs.includes('&larr; Return to Scorecard'));
});

test('UI-3 App - Evidence Detail Inspector dialog structure', () => {
  const stylesCss = fs.readFileSync(path.resolve(__dirname, '../styles.css'), 'utf8');

  // Asserts drawer/modal styles exist
  assert.ok(stylesCss.includes('.inspector-backdrop'));
  assert.ok(stylesCss.includes('.inspector-drawer'));
  assert.ok(stylesCss.includes('.raw-json-box'));
  assert.ok(stylesCss.includes('.btn-evidence-link'));
});
