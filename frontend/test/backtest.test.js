import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ApiClient } from '../api.js';
import { App } from '../app.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const mockAnalytics = {
  analysis_hash: "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  dataset_hash: "d1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2",
  sample_maturity: {
    one_week: "DESCRIPTIVE_ONLY",
    one_month: "DESCRIPTIVE_ONLY",
    six_month: "DESCRIPTIVE_ONLY"
  },
  leakage_audit_passed: true,
  rank_ic: {
    horizon: "SIX_MONTH",
    spearman_ic: 0.164656,
    p_value: 0.12,
    sample_size: 1
  },
  hit_rates: {
    one_week: 100.0
  },
  avoided_loss_rates: {
    one_week: 100.0
  },
  decile_buckets: []
};

const mockDatasets = {
  datasets: [
    {
      dataset_id: "test_dataset_001",
      dataset_hash: "d1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2",
      row_count: 1,
      included_observation_count: 3,
      generated_at: "2026-10-06T12:00:00Z",
      status_counts: { COMPLETE: 1 }
    }
  ],
  total: 1
};

const mockConfig = {
  active_configuration: {
    version: "1.5.0",
    status: "ACTIVE"
  },
  candidate_configuration: {
    version: "1.6.0",
    status: "READY_FOR_HUMAN_REVIEW"
  }
};

test('UI-5 ApiClient - Backtest datasets and analytics endpoints', async () => {
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
    await client.getBacktestAnalytics();
    await client.getBacktestDatasets();

    assert.ok(calls[0].endsWith('/api/v1/backtest/analytics'));
    assert.ok(calls[1].endsWith('/api/v1/backtest/datasets'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('UI-5 App - Backtest Distinction Banner separating population analysis vs individual performance vs calibration', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderBacktestContent(mockContainer, {
    analytics: mockAnalytics,
    datasets: mockDatasets,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  assert.ok(html.includes('Historical Population Analysis'));
  assert.ok(html.includes('ACTIVE VIEW'));
  assert.ok(html.includes('Individual IPO Performance'));
  assert.ok(html.includes('Calibration Proposals'));
  assert.ok(html.includes('GATED'));
});

test('UI-5 App - Executive Analytics Summary KPI section rendering', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderBacktestContent(mockContainer, {
    analytics: mockAnalytics,
    datasets: mockDatasets,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  // Asserts KPI grid is present
  assert.ok(html.includes('role="region"'));
  assert.ok(html.includes('aria-label="Executive Analytics Summary"'));

  // Asserts Sample size
  assert.ok(html.includes('Analysis Sample Size (N)'));
  assert.ok(html.includes('1'));

  // Asserts Maturity badges
  assert.ok(html.includes('DESCRIPTIVE_ONLY'));

  // Asserts Rank IC formatting (+ sign for positive correlation)
  assert.ok(html.includes('+0.164656'));
  assert.ok(html.includes('0.1200'));

  // Asserts Hit rate and Avoided loss rate
  assert.ok(html.includes('100.0%'));

  // Asserts Leakage audit passed
  assert.ok(html.includes('PASSED'));
});

test('UI-5 App - Fail-Closed Invariant: missing metrics render UNAVAILABLE and never default to zero', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  const emptyAnalytics = {
    analysis_hash: "hash_001",
    dataset_hash: "hash_002",
    sample_maturity: {},
    leakage_audit_passed: false,
    rank_ic: null,
    hit_rates: null,
    avoided_loss_rates: null,
    decile_buckets: null
  };

  app.renderBacktestContent(mockContainer, {
    analytics: emptyAnalytics,
    datasets: null,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  // Missing Rank IC must be UNAVAILABLE, never 0 or 0.00%
  assert.ok(html.includes('UNAVAILABLE'));
  assert.equal(html.includes('+0.000000'), false);
  assert.equal(html.includes('0.00%'), false);

  // Missing hit rates must be UNAVAILABLE
  assert.ok(app.formatRatePct(null).includes('UNAVAILABLE'));
  assert.ok(app.formatRatePct(undefined).includes('UNAVAILABLE'));
  assert.ok(app.formatIcValue(null).includes('UNAVAILABLE'));
  assert.ok(app.formatPValue(null).includes('UNAVAILABLE'));
});

test('UI-5 App - Decile analysis handles insufficient sample size cleanly without fabricating deciles', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderBacktestContent(mockContainer, {
    analytics: mockAnalytics,
    datasets: mockDatasets,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  // Asserts decile notice when N < 100
  assert.ok(html.includes('Decile Partitioning: Insufficient Sample Size (N &lt; 100)'));
  assert.ok(html.includes('Zero browser calculation authority'));
});

test('UI-5 App - Decile analysis renders populated buckets when provided by authoritative API', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  const analyticsWithDeciles = {
    ...mockAnalytics,
    decile_buckets: [
      {
        bucket_number: 1,
        score_lower_bound: 10.0,
        score_upper_bound: 25.0,
        n: 12,
        mean_return: -4.5,
        mean_benchmark_return: 2.1,
        mean_excess_return: -6.6
      },
      {
        bucket_number: 10,
        score_lower_bound: 85.0,
        score_upper_bound: 98.0,
        n: 15,
        mean_return: 28.4,
        mean_benchmark_return: 3.2,
        mean_excess_return: 25.2
      }
    ]
  };

  app.renderBacktestContent(mockContainer, {
    analytics: analyticsWithDeciles,
    datasets: mockDatasets,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  assert.ok(html.includes('Decile 1'));
  assert.ok(html.includes('Decile 10'));
  assert.ok(html.includes('25.20%'));
  assert.ok(html.includes('-6.60%'));
});

test('UI-5 App - Vintage and Holdout sections report NOT EXPOSED without synthesizing fake data', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderBacktestContent(mockContainer, {
    analytics: mockAnalytics,
    datasets: mockDatasets,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  // Vintage stability section
  assert.ok(html.includes('Historical Vintage &amp; Cohort Stability'));
  assert.ok(html.includes('Status: NOT EXPOSED IN CURRENT API SCHEMA'));
  assert.ok(html.includes('Fail-closed policy: The browser presentation layer does not synthesize or fabricate historical cohorts'));

  // Holdout validation section
  assert.ok(html.includes('Out-of-Sample Temporal Holdout Partition'));
  assert.ok(html.includes('Status: NOT EXPOSED IN CURRENT API SCHEMA'));
  assert.ok(html.includes('Fail-closed policy: The browser presentation layer does not synthesize or fabricate holdout splits'));
});

test('UI-5 App - Point-in-Time Leakage Audit and Cryptographic Provenance panel', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderBacktestContent(mockContainer, {
    analytics: mockAnalytics,
    datasets: mockDatasets,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  // Leakage Audit
  assert.ok(html.includes('Point-in-Time Safety &amp; Leakage Audit'));
  assert.ok(html.includes('AUDIT PASSED'));
  assert.ok(html.includes('Prospectus Feature Freeze'));
  assert.ok(html.includes('Trading Day Calendar Alignment'));
  assert.ok(html.includes('Corporate Action Synchronization'));

  // Provenance Fingerprints
  assert.ok(html.includes(mockAnalytics.analysis_hash));
  assert.ok(html.includes(mockAnalytics.dataset_hash));
  assert.ok(html.includes('Active Frozen Core'));
});

test('UI-5 App - Calibration Governance Boundary preserves firewall against automated activation', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderBacktestContent(mockContainer, {
    analytics: mockAnalytics,
    datasets: mockDatasets,
    config: mockConfig
  });

  const html = mockContainer.innerHTML;

  assert.ok(html.includes('Calibration Governance Boundary'));
  assert.ok(html.includes('Evidence &rarr; Analysis &rarr; Proposal &ne; Approval &ne; Implementation &ne; Activation'));
  assert.ok(html.includes('● v1.5.0 (Executable)'));
  assert.ok(html.includes('○ v1.6.0 (READY_FOR_HUMAN_REVIEW)'));
  assert.ok(html.includes('Zero in-browser activation controls'));

  // Verify zero activation controls exist
  assert.equal(html.includes('<button>Activate'), false);
  assert.equal(html.includes('activatePolicy'), false);
  assert.equal(html.includes('applyProposal'), false);
});

test('UI-5 App - Zero browser-side analytical/return calculations and zero credential leakage', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');

  // Verify zero statistical formulas in frontend
  assert.equal(appJs.includes('calculateSpearman'), false);
  assert.equal(appJs.includes('computeRankIc'), false);
  assert.equal(appJs.includes('calculateHitRate'), false);
  assert.equal(appJs.includes('computeDeciles'), false);
  assert.equal(appJs.includes('calculatePValue'), false);

  // Verify no server paths
  assert.equal(appJs.includes('/home/user'), false);
  assert.equal(appJs.includes('/etc/'), false);

  // Verify no credentials
  assert.equal(appJs.includes('AI71_API_KEY'), false);
  assert.equal(appJs.includes('OPENAI_API_KEY'), false);
});
