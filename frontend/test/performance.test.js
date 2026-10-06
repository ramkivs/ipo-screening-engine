import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ApiClient, ApiError } from '../api.js';
import { App } from '../app.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const mockEvaluation = {
  evaluation_id: "eval_20261006_vishal_final_001",
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
  }
};

const mockPerformanceSummary = {
  final_evaluation_id: "eval_20261006_vishal_final_001",
  ipo_id: "VISHAL-NIRMITI-LIMITED",
  company_name: "Vishal Nirmiti Limited",
  issue_price: "215.0",
  listing_date: "2026-10-14",
  horizons: {
    one_week: {
      status: "RECORDED",
      ipo_return_pct: "14.50",
      benchmark_return_pct: "1.20",
      excess_return_pct: "13.30"
    },
    one_month: {
      status: "RECORDED",
      ipo_return_pct: "22.80",
      benchmark_return_pct: "3.10",
      excess_return_pct: "19.70"
    },
    six_month: {
      status: "INCOMPLETE",
      ipo_return_pct: null,
      benchmark_return_pct: null,
      excess_return_pct: null
    }
  }
};

const mockPostListing = {
  final_evaluation_id: "eval_20261006_vishal_final_001",
  ipo_id: "VISHAL-NIRMITI-LIMITED",
  observation_count: 2,
  observations: [
    {
      observation_id: "OBS-VISHAL-1W",
      horizon: "1W",
      version: 1,
      target_date: "2026-10-21",
      actual_trading_date: "2026-10-21",
      status: "RECORDED",
      issue_price: "215.0",
      prices: {
        issue_price: 215.0,
        listing_open: 240.0,
        listing_close: 246.15,
        raw_observed_close: 246.15,
        corporate_action_factor: 1.0,
        adjusted_observed_close: 246.15
      },
      benchmark: {
        symbol: "NIFTY50",
        raw_listing_value: 24500.0,
        raw_observed_value: 24794.0,
        return_pct: 1.20
      },
      returns: {
        listing_gain_pct: 14.49,
        absolute_return_pct: 14.50,
        secondary_return_pct: 2.56,
        benchmark_return_pct: 1.20,
        excess_return_pct: 13.30
      }
    },
    {
      observation_id: "OBS-VISHAL-1M",
      horizon: "1M",
      version: 1,
      target_date: "2026-11-13",
      actual_trading_date: "2026-11-13",
      status: "RECORDED",
      issue_price: "215.0",
      prices: {
        issue_price: 215.0,
        listing_open: 240.0,
        listing_close: 246.15,
        raw_observed_close: 264.0,
        corporate_action_factor: 1.0,
        adjusted_observed_close: 264.0
      },
      benchmark: {
        symbol: "NIFTY50",
        raw_listing_value: 24500.0,
        raw_observed_value: 25260.0,
        return_pct: 3.10
      },
      returns: {
        listing_gain_pct: 14.49,
        absolute_return_pct: 22.80,
        secondary_return_pct: 10.0,
        benchmark_return_pct: 3.10,
        excess_return_pct: 19.70
      }
    }
  ]
};

const mockBacktestAnalytics = {
  analysis_hash: "analysis_hash_89abcdef01234567",
  dataset_hash: "dataset_hash_4567890abcdef123",
  sample_maturity: { "1W": 1, "1M": 1, "6M": 0 },
  leakage_audit_passed: true,
  rank_ic: { "1W": 0.45, "1M": 0.52 },
  hit_rates: { "1W": 0.68, "1M": 0.72 }
};

const mockCalibrationProposals = {
  proposals: [
    {
      proposal_id: "PROP-1.0.0",
      status: "READY_FOR_HUMAN_REVIEW",
      target_version: "v1.6.0",
      created_at: "2026-10-06T00:00:00Z",
      summary: "Calibrated weights: Module A 20%, Module E 35%"
    }
  ],
  total: 1
};

test('UI-4 ApiClient - Post-listing and performance presentation endpoints', async () => {
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
    await client.getPostListing('eval_123');
    await client.getPerformance('eval_123');
    await client.getBacktestAnalytics();
    await client.getCalibrationProposals();

    assert.ok(calls[0].endsWith('/api/v1/evaluations/eval_123/post-listing'));
    assert.ok(calls[1].endsWith('/api/v1/evaluations/eval_123/performance'));
    assert.ok(calls[2].endsWith('/api/v1/backtest/analytics'));
    assert.ok(calls[3].endsWith('/api/v1/calibration/proposals'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('UI-4 App - formatReturnPct preserves fail-closed semantics (never converts null to 0.00%)', () => {
  const app = new App();

  // Positive return formatting
  const pos = app.formatReturnPct(14.50);
  assert.ok(pos.includes('+14.50%'));
  assert.ok(pos.includes('return-badge-pos'));

  // Negative return formatting
  const neg = app.formatReturnPct(-7.25);
  assert.ok(neg.includes('-7.25%'));
  assert.ok(neg.includes('return-badge-neg'));

  // Neutral zero return formatting
  const zero = app.formatReturnPct(0.0);
  assert.ok(zero.includes('0.00%'));
  assert.ok(zero.includes('return-badge-neutral'));

  // Strict Fail-Closed Invariant: missing/null values MUST be UNAVAILABLE, NEVER 0.00%
  const nullRet = app.formatReturnPct(null);
  assert.ok(nullRet.includes('UNAVAILABLE'));
  assert.equal(nullRet.includes('0.00%'), false);

  const undefRet = app.formatReturnPct(undefined);
  assert.ok(undefRet.includes('UNAVAILABLE'));
  assert.equal(undefRet.includes('0.00%'), false);

  const emptyRet = app.formatReturnPct('');
  assert.ok(emptyRet.includes('UNAVAILABLE'));
  assert.equal(emptyRet.includes('0.00%'), false);
});

test('UI-4 App - Performance Summary KPI strip rendering', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderPerformanceContent(mockContainer, {
    evaluation: mockEvaluation,
    perfSummary: mockPerformanceSummary,
    postListing: mockPostListing,
    backtest: mockBacktestAnalytics,
    calibration: mockCalibrationProposals
  });

  const html = mockContainer.innerHTML;

  // Asserts KPI grid is present and labelled
  assert.ok(html.includes('role="region"'));
  assert.ok(html.includes('aria-label="Performance Summary KPIs"'));

  // Asserts Issue price display
  assert.ok(html.includes('₹215.00'));
  assert.ok(html.includes('2026-10-14'));

  // Asserts 1W, 1M, 6M returns
  assert.ok(html.includes('+14.50%'), 'Must show 1W IPO return');
  assert.ok(html.includes('+13.30%'), 'Must show 1W Excess Alpha');
  assert.ok(html.includes('+22.80%'), 'Must show 1M IPO return');
  assert.ok(html.includes('+19.70%'), 'Must show 1M Excess Alpha');

  // Asserts 6M incomplete status
  assert.ok(html.includes('INCOMPLETE'));
});

test('UI-4 App - Deterministic Performance Timeline rendering', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderPerformanceContent(mockContainer, {
    evaluation: mockEvaluation,
    perfSummary: mockPerformanceSummary,
    postListing: mockPostListing,
    backtest: mockBacktestAnalytics,
    calibration: mockCalibrationProposals
  });

  const html = mockContainer.innerHTML;

  // Timeline structure
  assert.ok(html.includes('aria-label="Lifecycle Performance Timeline"'));
  assert.ok(html.includes('1. FINAL Screening'));
  assert.ok(html.includes('2. Listing Day'));
  assert.ok(html.includes('3. 1-Week (1W)'));
  assert.ok(html.includes('4. 1-Month (1M)'));
  assert.ok(html.includes('5. 6-Month (6M)'));

  // Milestone statuses
  assert.ok(html.includes('RECORDED'));
  assert.ok(html.includes('COMPLETED'));
});

test('UI-4 App - Multi-horizon observation cards and corporate action adjustment factor', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderPerformanceContent(mockContainer, {
    evaluation: mockEvaluation,
    perfSummary: mockPerformanceSummary,
    postListing: mockPostListing,
    backtest: mockBacktestAnalytics,
    calibration: mockCalibrationProposals
  });

  const html = mockContainer.innerHTML;

  // Price metric table fields
  assert.ok(html.includes('Listing Day Open'));
  assert.ok(html.includes('Listing Day Close'));
  assert.ok(html.includes('Raw Observed Close'));
  assert.ok(html.includes('Adjusted Observed Close'));

  // Clean corporate action factor 1.0000
  assert.ok(html.includes('Factor: 1.0000 (Clean / Unadjusted)'));

  // Returns breakdown
  assert.ok(html.includes('Absolute Return'));
  assert.ok(html.includes('Listing Gain'));
  assert.ok(html.includes('Secondary Return'));
  assert.ok(html.includes('Excess Alpha vs Benchmark'));
  assert.ok(html.includes('NIFTY50'));
});

test('UI-4 App - Backtest & Calibration Governance Boundaries', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderPerformanceContent(mockContainer, {
    evaluation: mockEvaluation,
    perfSummary: mockPerformanceSummary,
    postListing: mockPostListing,
    backtest: mockBacktestAnalytics,
    calibration: mockCalibrationProposals
  });

  const html = mockContainer.innerHTML;

  // Backtest boundary
  assert.ok(html.includes('Aggregate Backtest Analytics Boundary'));
  assert.ok(html.includes('Individual Observation &ne; Aggregate Backtest Analysis'));
  assert.ok(html.includes(mockBacktestAnalytics.analysis_hash));
  assert.ok(html.includes(mockBacktestAnalytics.dataset_hash));

  // Calibration boundary
  assert.ok(html.includes('Calibration Governance Boundary'));
  assert.ok(html.includes('Evidence &rarr; Analysis &rarr; Proposal &ne; Approval &ne; Implementation &ne; Activation'));
  assert.ok(html.includes('READY_FOR_HUMAN_REVIEW'));
  assert.ok(html.includes('Zero in-browser activation controls'));

  // Verify zero activation controls exist
  assert.equal(html.includes('<button>Activate'), false);
  assert.equal(html.includes('activatePolicy'), false);
  assert.equal(html.includes('applyProposal'), false);
});

test('UI-4 App - Scorecard and Evidence Navigation integration', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');

  // Verify Scorecard header links to performance explorer
  assert.ok(appJs.includes('#performance/'));
  assert.ok(appJs.includes('Post-Listing Performance &rarr;'));

  // Verify Performance view links back to Scorecard and Evidence
  assert.ok(appJs.includes('&larr; Return to Scorecard'));
  assert.ok(appJs.includes('Inspect Evidence &rarr;'));
});

test('UI-4 App - Zero client-side return calculations and zero credential leakage', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');

  // Verify no calculation of returns: (p - p0)/p0 or r_ipo - r_bm
  assert.equal(appJs.includes('calculateReturn'), false);
  assert.equal(appJs.includes('computeExcess'), false);
  assert.equal(appJs.includes('computeAlpha'), false);

  // Verify no server paths
  assert.equal(appJs.includes('/home/user'), false);
  assert.equal(appJs.includes('/etc/'), false);

  // Verify no credentials
  assert.equal(appJs.includes('AI71_API_KEY'), false);
  assert.equal(appJs.includes('OPENAI_API_KEY'), false);
});
