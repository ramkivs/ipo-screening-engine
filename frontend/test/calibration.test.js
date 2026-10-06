import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ApiClient } from '../api.js';
import { App } from '../app.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const mockConfigStatus = {
  active_configuration: {
    version: "1.5.0",
    status: "ACTIVE",
    is_active: true,
    config_hash: "382ff86cc9d753514509f89c096f3b262bd4e12e644e0d7d03fe811b44e0f1e8",
    description: "Production executable policy v1.5.0"
  },
  candidate_configuration: {
    version: "1.6.0",
    status: "READY_FOR_HUMAN_REVIEW",
    is_active: false,
    config_hash: "4ce1480c84e6ebfe22b96511f0f9b1b6577031bf272fe703c48f220a70def1f1",
    source_proposal_hash: "87bc9bcfa0bd9561adf3eb0be53a4291c465b5b02cd8561209f323e94a2249af",
    description: "Authorized candidate v1.6 configuration (strictly inactive, promotion gated)"
  },
  frozen_core_status: "VERIFIED",
  golden_result_status: "VERIFIED"
};

const mockProposalDetail = {
  proposal_id: "PROP-1.0.0",
  proposal_hash: "87bc9bcfa0bd9561adf3eb0be53a4291c465b5b02cd8561209f323e94a2249af",
  baseline_config_version: "1.5.0",
  candidate_config_version: "1.6.0",
  baseline_config_hash: "382ff86cc9d753514509f89c096f3b262bd4e12e644e0d7d03fe811b44e0f1e8",
  candidate_config_hash: "4ce1480c84e6ebfe22b96511f0f9b1b6577031bf272fe703c48f220a70def1f1",
  source_dataset_hash: "7cac90dbf32bd385e3627074407191f7f1778093ba14879a2247075e1309057e",
  source_analysis_hash: "2932cdf824b6f1a1939bad1b82f6da5e730ba5555b2c0da2573a6177c64f37b2",
  maturity_gate: "CALIBRATION_CANDIDATE",
  status: "READY_FOR_HUMAN_REVIEW",
  approval_status: "APPROVED",
  objective: "BALANCED_DIAGNOSTIC",
  module_weight_adjustments: {
    A: 30.0,
    B: 15.0,
    C: 15.0,
    D: 15.0,
    E: 15.0,
    F: 10.0
  },
  module_proposals: [
    {
      module_id: "A",
      module_name: "Financial Quality",
      current_weight: 25.0,
      proposed_weight: 30.0,
      status: "PROPOSED",
      rationale: "Increased +5 points reflecting stronger development rank correlation (0.164656)."
    },
    {
      module_id: "B",
      module_name: "Valuation",
      current_weight: 20.0,
      proposed_weight: 15.0,
      status: "PROPOSED",
      rationale: "Decreased -5 points reflecting weaker development rank correlation (-0.139969)."
    },
    {
      module_id: "C",
      module_name: "Offer Structure, Proceeds & Pre-IPO",
      current_weight: 15.0,
      proposed_weight: 15.0,
      status: "NO_CHANGE",
      rationale: "Baseline weight retained."
    },
    {
      module_id: "D",
      module_name: "Promoter & Governance",
      current_weight: 15.0,
      proposed_weight: 15.0,
      status: "NO_CHANGE",
      rationale: "Baseline weight retained."
    },
    {
      module_id: "E",
      module_name: "Business & Moat",
      current_weight: 15.0,
      proposed_weight: 15.0,
      status: "NO_CHANGE",
      rationale: "Baseline weight retained."
    },
    {
      module_id: "F",
      module_name: "Market & Demand Signals",
      current_weight: 10.0,
      proposed_weight: 10.0,
      status: "NO_CHANGE",
      rationale: "Baseline weight retained."
    }
  ],
  non_regression_results: [
    {
      check_name: "downside_protection",
      passed: true,
      baseline_value: "CLEAR",
      proposed_value: "CLEAR",
      details: "Knockout rules, penalty ceilings, and AVOID boundary remain intact."
    },
    {
      check_name: "holdout_stability",
      passed: true,
      baseline_value: "0.115372",
      proposed_value: "0.115372",
      details: "Holdout out-of-sample performance remains non-degraded."
    },
    {
      check_name: "deterministic_reproducibility",
      passed: true,
      baseline_value: "DETERMINISTIC",
      proposed_value: "DETERMINISTIC",
      details: "Pure standard library arithmetic ensures deterministic replay."
    }
  ]
};

test('UI-6 ApiClient - Calibration proposal retrieval protocol', async () => {
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
    await client.getCalibrationProposals();
    await client.getCalibrationProposal('v1.6.0');

    assert.ok(calls[0].endsWith('/api/v1/calibration/proposals'));
    assert.ok(calls[1].endsWith('/api/v1/calibration/proposals/v1.6.0'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('UI-6 App - Governance Lifecycle Chain preserves firewall against automated activation', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderCalibrationContent(mockContainer, {
    config: mockConfigStatus,
    proposalDetail: mockProposalDetail
  });

  const html = mockContainer.innerHTML;

  // Asserts governance chain steps
  assert.ok(html.includes('1. Empirical Evidence'));
  assert.ok(html.includes('2. Statistical Analysis'));
  assert.ok(html.includes('3. Calibration Proposal'));
  assert.ok(html.includes('4. Governance Approval'));
  assert.ok(html.includes('5. Release Activation'));
  assert.ok(html.includes('STRICTLY LOCKED (NO IN-BROWSER ACTIVATION)'));

  // Asserts explicit governance notice
  assert.ok(html.includes('ZERO activation authority'));
  assert.ok(html.includes('Activation of candidate policy <code>v1.6.0</code> requires offline human committee ratification'));
});

test('UI-6 App - Active Baseline (v1.5.0) presentation is strictly EXECUTABLE and clearly distinguished from candidate', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderCalibrationContent(mockContainer, {
    config: mockConfigStatus,
    proposalDetail: mockProposalDetail
  });

  const html = mockContainer.innerHTML;

  assert.ok(html.includes('Active Policy (v1.5.0)'));
  assert.ok(html.includes('● ACTIVE • EXECUTABLE'));
  assert.ok(html.includes(mockConfigStatus.active_configuration.config_hash.slice(0, 16)));
  assert.ok(html.includes('Frozen Core Engine:'));
  assert.ok(html.includes('VERIFIED'));
});

test('UI-6 App - Candidate Proposal (v1.6.0-draft) presentation is strictly INACTIVE and promotion gated', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderCalibrationContent(mockContainer, {
    config: mockConfigStatus,
    proposalDetail: mockProposalDetail
  });

  const html = mockContainer.innerHTML;

  assert.ok(html.includes('Candidate Proposal (v1.6.0-draft)'));
  assert.ok(html.includes('○ CANDIDATE • INACTIVE'));
  assert.ok(html.includes('PROP-1.0.0'));
  assert.ok(html.includes('READY_FOR_HUMAN_REVIEW'));
  assert.ok(html.includes('CALIBRATION_CANDIDATE'));
  assert.ok(html.includes('APPROVED (Program Authority)'));
});

test('UI-6 App - Current vs Proposed module weight shift comparison renders exact authoritative deltas', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderCalibrationContent(mockContainer, {
    config: mockConfigStatus,
    proposalDetail: mockProposalDetail
  });

  const html = mockContainer.innerHTML;

  // Module A: 25 -> 30 (+5.0 pts)
  assert.ok(html.includes('Financial Quality'));
  assert.ok(html.includes('25.0 pts'));
  assert.ok(html.includes('30.0 pts'));
  assert.ok(html.includes('+5.0 pts'));

  // Module B: 20 -> 15 (-5.0 pts)
  assert.ok(html.includes('Valuation'));
  assert.ok(html.includes('20.0 pts'));
  assert.ok(html.includes('15.0 pts'));
  assert.ok(html.includes('-5.0 pts'));

  // Unchanged Modules C-F: 15/15/15/10 (0.0 pts)
  assert.ok(html.includes('Offer Structure, Proceeds &amp; Pre-IPO'));
  assert.ok(html.includes('Promoter &amp; Governance'));
  assert.ok(html.includes('Business &amp; Moat'));
  assert.ok(html.includes('Market &amp; Demand Signals'));
  assert.ok(html.includes('0.0 pts'));

  // Total 100-point scale normalization
  assert.ok(html.includes('NORMALIZED'));
  assert.ok(html.includes('100-point total score invariant preserved'));
});

test('UI-6 App - Non-regression audit and downside protection checks rendering', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderCalibrationContent(mockContainer, {
    config: mockConfigStatus,
    proposalDetail: mockProposalDetail
  });

  const html = mockContainer.innerHTML;

  assert.ok(html.includes('Non-Regression &amp; Downside Protection Audit'));
  assert.ok(html.includes('downside_protection'));
  assert.ok(html.includes('holdout_stability'));
  assert.ok(html.includes('deterministic_reproducibility'));
  assert.ok(html.includes('Knockout rules, penalty ceilings, and AVOID boundary remain intact'));
  assert.ok(html.includes('Holdout out-of-sample performance remains non-degraded'));
});

test('UI-6 App - Cryptographic Provenance panel displays all SHA-256 digests with copy controls', () => {
  const app = new App();
  const mockContainer = { innerHTML: '' };

  app.renderCalibrationContent(mockContainer, {
    config: mockConfigStatus,
    proposalDetail: mockProposalDetail
  });

  const html = mockContainer.innerHTML;

  assert.ok(html.includes('Cryptographic Policy &amp; Proposal Provenance Fingerprints'));
  assert.ok(html.includes(mockProposalDetail.proposal_hash));
  assert.ok(html.includes(mockProposalDetail.baseline_config_hash));
  assert.ok(html.includes(mockProposalDetail.candidate_config_hash));
  assert.ok(html.includes(mockProposalDetail.source_dataset_hash));
  assert.ok(html.includes(mockProposalDetail.source_analysis_hash));
  assert.ok(html.includes('UI-1 Presentation API (docs/openapi/presentation-api-v1.yaml)'));
});

test('UI-6 App - Zero in-browser activation controls and zero mutation handlers', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');
  const indexHtml = fs.readFileSync(path.resolve(__dirname, '../index.html'), 'utf8');

  // Assert absence of activation buttons/handlers
  assert.equal(appJs.includes('activatePolicy'), false);
  assert.equal(appJs.includes('activateConfig'), false);
  assert.equal(appJs.includes('applyProposal'), false);
  assert.equal(appJs.includes('set_active'), false);
  assert.equal(appJs.includes('switchConfig'), false);

  assert.equal(indexHtml.includes('<button>Activate'), false);
  assert.equal(indexHtml.includes('btn-activate'), false);
});

test('UI-6 App - Zero browser-side calculation authority and zero credential leakage', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');

  // Verify zero calculation logic
  assert.equal(appJs.includes('computeWeights'), false);
  assert.equal(appJs.includes('calibratePolicy'), false);
  assert.equal(appJs.includes('optimizeWeights'), false);

  // Verify no server paths
  assert.equal(appJs.includes('/home/user'), false);
  assert.equal(appJs.includes('/etc/'), false);

  // Verify no credentials
  assert.equal(appJs.includes('AI71_API_KEY'), false);
  assert.equal(appJs.includes('OPENAI_API_KEY'), false);
});
