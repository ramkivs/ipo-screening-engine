import { JSDOM, VirtualConsole } from 'jsdom';
import assert from 'node:assert/strict';

const [url, evaluationId, comparisonMode = 'available'] = process.argv.slice(2);
if (!url || !evaluationId) throw new Error('usage: node workbench-hydration.browser.mjs URL EVALUATION_ID [available|404]');

const requests = [];
const submissions = [];
const errors = [];
const moduleNames = ['Financial Quality', 'Valuation', 'Proceeds & Lock-in', 'Governance', 'Business & Moat', 'Market Context'];
const syntheticModules = moduleNames.map((name, index) => ({
  module_id: String.fromCharCode(65 + index), name, baseline_points: 0,
  secondary_points: [17, 4.5, 15, 9, 15, 10][index], cap: [25, 20, 15, 15, 15, 10][index],
  delta: [0, 0, 4, 0, 7, 6][index], cap_applied: [2, 4, 5].includes(index),
  criteria: [{ criterion_id: `criterion_${index}`, label: `${name} criterion`, metric: `metric_${index}`, baseline_value: null, secondary_value: 'strong', score: 5, max: 5, state: index === 4 ? 'CAPPED' : 'SCORED', explanation: 'Matched governed test rule.' }],
}));
// These deliberately use the raw production shapes that previously tripped the
// empty-state fallback: Layer 1 score.modules and Layer 2C module_breakdown.
const withCriterionKey = (module, key, criteria = module.criteria) => {
  const { criteria: _discarded, ...summary } = module;
  return { ...summary, [key]: criteria };
};
const syntheticSecondary = {
  secondary: { score: 70.5, verdict: 'VERDICT_UNCERTAIN', confidence: 'High', completeness_pct: 96, knockout_status: 'CLEAR', knockouts: Array.from({ length: 6 }, (_, i) => ({ rule_id: `K${i + 1}`, state: 'CLEAR' })) },
  module_breakdown: syntheticModules.map((module, index) => withCriterionKey(module, ['criteria', 'criterion_details', 'inspection', 'items', 'rules', 'breakdown'][index], index === 2 ? { criteria: module.criteria } : module.criteria)),
};
const upgradedSecondary = {
  ...syntheticSecondary,
  secondary: { ...syntheticSecondary.secondary, score: 75.5, verdict: 'SUBSCRIBE' },
  module_breakdown: syntheticSecondary.module_breakdown.map(module => module.module_id === 'B' ? { ...module, secondary_points: 9.5, delta: 5 } : module),
};
const syntheticBaseline = {
  score: { final_score: 37, completeness: { percentage: 62 }, confidence: 'Low', modules: syntheticModules.map((module, index) => withCriterionKey({ module_id: module.module_id, name: module.name, score: module.baseline_points, max: module.cap, criteria: module.criteria }, ['criteria', 'breakdown', 'items', 'criteria', 'breakdown', 'items'][index], module.criteria.map(item => ({ ...item, value: item.baseline_value })))) },
  verdict: { verdict: 'AVOID' }, confidence: { completeness_pct: 62, level: 'Low' },
  knockouts: { results: Array.from({ length: 6 }, (_, i) => ({ rule_id: `K${i + 1}`, state: i === 1 ? 'TRIGGERED' : 'CLEAR' })) },
};
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', error => errors.push(String(error)));
virtualConsole.on('error', (...args) => errors.push(args.join(' ')));

const dom = await JSDOM.fromURL(url, {
  runScripts: 'dangerously',
  resources: 'usable',
  pretendToBeVisual: true,
  virtualConsole,
  beforeParse(window) {
    window.fetch = async (resource, options) => {
      const absolute = new URL(typeof resource === 'string' ? resource : (resource.url || resource.href), window.location.href).href;
      requests.push(absolute);
      if (options?.method === 'POST' && new URL(absolute).pathname.endsWith('/actions/inject-rescore')) {
        submissions.push(Object.fromEntries(options.body.entries()));
        return new Response(JSON.stringify({ detail: 'recalculation succeeded', evaluation_id: evaluationId }), { status: 200, headers: { 'content-type': 'application/json' } });
      }
      if (comparisonMode === '404' && new URL(absolute).pathname.startsWith('/api/v1/comparison/')) {
        return new Response(JSON.stringify({ detail: 'comparison unavailable' }), { status: 404, headers: { 'content-type': 'application/json' } });
      }
      if (comparisonMode === 'available' && new URL(absolute).pathname.startsWith('/api/v1/comparison/')) {
        return new Response(JSON.stringify({ baseline: syntheticBaseline, enriched: [submissions.length ? upgradedSecondary : syntheticSecondary], scenarios: [] }), { status: 200, headers: { 'content-type': 'application/json' } });
      }
      const response = await globalThis.fetch(absolute, options);
      if (new URL(absolute).pathname === '/api/v1/evaluations') {
        const rows = await response.json();
        const items = rows.map(({ id, ...row }) => ({ ...row, evaluation_id: id }));
        return new Response(JSON.stringify({ items }), { status: response.status, headers: { 'content-type': 'application/json' } });
      }
      return response;
    };
  },
});

const { document } = dom.window;
const deadline = Date.now() + 5000;
while (!requests.some(request => new URL(request).pathname === '/api/v1/evaluations')) {
  if (Date.now() > deadline) throw new Error('evaluation list request timed out');
  await new Promise(resolve => setTimeout(resolve, 25));
}
await new Promise(resolve => setTimeout(resolve, 25));

const controls = [...document.querySelectorAll('#inject-form [name],#scenario-form [name]')];
assert.equal(controls.length, 41);
assert.equal(document.querySelector('#evaluation').value, '');
assert.equal(document.querySelector('[name="baseline_id"]').value, '');
assert.equal(document.querySelector('[name="target_id"]').value, '');
assert.equal(document.querySelector('#comparison').children.length, 0);
assert.equal(controls.every(control => control.value === ''), true, 'all form controls must start blank');
assert.deepEqual(requests.map(request => new URL(request).pathname), ['/api/v1/evaluations']);

const evaluation = document.querySelector('#evaluation');
evaluation.value = evaluationId;
evaluation.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
const expectedCards = comparisonMode === '404' ? 0 : 3;
while (document.querySelector('[name="qib_x"]')?.value !== '25' || document.querySelector('#comparison').children.length !== expectedCards || requests.filter(request => new URL(request).pathname.startsWith('/api/v1/comparison/')).length !== 1) {
  if (Date.now() > deadline) throw new Error(`hydration timed out; requests=${JSON.stringify(requests)} status=${document.querySelector('#workbench-status')?.textContent}`);
  await new Promise(resolve => setTimeout(resolve, 25));
}

assert.equal(document.body.dataset.workbenchReady, 'true');
assert.equal(document.querySelector('#evaluation').value, evaluationId);
assert.equal(document.querySelector('[name="baseline_id"]').value, evaluationId);
assert.equal(document.querySelector('[name="target_id"]').value, evaluationId);
assert.equal(controls.every(control => control.dataset.hydrated === 'true'), true, 'all 41 controls must complete the hydration pass');
assert.equal(document.querySelector('#comparison').children.length, expectedCards);
if (comparisonMode === 'available') {
  assert.equal(document.querySelectorAll('.baseline-breakdown .module-accordion').length, 6, 'Layer 1 must render six structured modules');
  assert.equal(document.querySelector('.baseline-breakdown')?.classList.contains('card'), false, 'Layer 1 must not be a raw JSON card');
  assert.equal(document.querySelector('.baseline-breakdown .secondary-summary')?.textContent.includes('37.0'), true);
  assert.equal(document.querySelector('.baseline-breakdown .verdict-badge')?.textContent, 'AVOID');
  assert.equal(document.querySelector('.baseline-breakdown .secondary-summary')?.textContent.includes('62.0%'), true);
  assert.equal(document.querySelector('.baseline-breakdown .secondary-summary')?.textContent.includes('Low'), true);
  assert.equal(document.querySelector('.secondary-breakdown .secondary-summary')?.textContent.includes('70.5'), true);
  assert.equal(document.querySelector('.secondary-breakdown .verdict-badge')?.textContent, 'VERDICT_UNCERTAIN');
}

const expected = {
  bidding_day: 'DAY_1', observation_time: '2026-10-05T11:00:00Z', source_id: 'BROWSER-E2E',
  qib_x: '25', nii_x: '12', retail_x: '8', overall_x: '15',
  operating_cash_flow_3yr_cumulative: '100', net_income_3yr_cumulative: '300',
  trade_receivables_days: '100', net_working_capital_pct_revenue: '40',
  top_customer_revenue_pct: '55', loss_making_segments_present: 'true',
  promoter_pledged_shares_pct: '30', pre_issue_promoter_holding_pct: '50',
  contingent_liabilities_pct_net_worth: '50', material_regulatory_disputes_present: 'true',
  industry_cagr_pct: '15', moat_rating: 'strong_niche', top5_concentration_pct: '20', visibility_rating: 'strong',
  anchor_bucket: 'reputed', gmp_bucket: 'strong', market_regime_bucket: 'supportive',
  peer_delta: '0', rating: 'LOW', qualitative_delta: '0', justification: 'Operator scenario only',
};
for (const [name, value] of Object.entries(expected)) {
  assert.equal(document.querySelector(`[name="${name}"]`)?.value, value, `${name} was not hydrated`);
}

document.querySelector('[name="top_customer_revenue_pct"]').value = '0.5';
const moduleOverrides = {
  industry_cagr_pct: '16', moat_rating: 'leader_with_moat', top5_concentration_pct: '10', visibility_rating: 'moderate',
  use_of_proceeds_bucket: 'growth', lockin_bucket: 'intact', second_multiple_premium_pct: '-10', sector_ipo_relative: 'cheaper',
  anchor_bucket: 'mixed', gmp_bucket: 'flat', market_regime_bucket: 'neutral',
};
for (const [name, value] of Object.entries(moduleOverrides)) document.querySelector(`[name="${name}"]`).value = value;
document.querySelector('[name="publisher"]').value = 'TEST PUBLISHER';
document.querySelector('#inject-form').dispatchEvent(new dom.window.Event('submit', { bubbles: true, cancelable: true }));
const submissionDeadline = Date.now() + 5000;
while (submissions.length !== 1) {
  if (Date.now() > submissionDeadline) throw new Error(`recalculation submission timed out; status=${document.querySelector('#workbench-status')?.textContent}; errors=${JSON.stringify(errors)}; requests=${JSON.stringify(requests)}`);
  await new Promise(resolve => setTimeout(resolve, 25));
}
assert.equal(submissions[0].top_customer_revenue_pct, '0.5');
assert.equal(submissions[0].net_income_3yr_cumulative, undefined, 'unchanged hydrated targets must not be duplicated');
assert.equal(submissions[0].qib_x, undefined, 'unchanged market targets must not be duplicated');
for (const [name, value] of Object.entries(moduleOverrides)) assert.equal(submissions[0][name], value, `${name} was not serialized`);
if (comparisonMode === 'available') {
  while (document.querySelectorAll('.secondary-breakdown .module-accordion').length !== 6 || !document.querySelector('.secondary-breakdown .secondary-summary')?.textContent.includes('75.5')) {
    if (Date.now() > submissionDeadline) throw new Error('module accordion did not populate after recalculation');
    await new Promise(resolve => setTimeout(resolve, 25));
  }
  assert.equal(document.querySelectorAll('.baseline-breakdown .module-accordion').length, 6);
  assert.equal(document.querySelectorAll('.secondary-breakdown .module-accordion').length, 6);
  assert.equal(document.querySelector('.baseline-breakdown .secondary-summary')?.textContent.includes('37.0'), true);
  assert.equal(document.querySelector('.baseline-breakdown .verdict-badge')?.textContent, 'AVOID');
  assert.equal(document.querySelector('.baseline-breakdown .secondary-summary')?.textContent.includes('62.0%'), true);
  assert.equal(document.querySelector('.baseline-breakdown .secondary-summary')?.textContent.includes('Low'), true);
  assert.equal(document.querySelector('.secondary-breakdown .secondary-summary')?.textContent.includes('75.5'), true);
  assert.equal(document.querySelector('.secondary-breakdown .verdict-badge')?.textContent, 'SUBSCRIBE');
  assert.equal(document.querySelector('.secondary-breakdown .module-accordion[data-module="B"] summary')?.textContent.includes('9.5 / 20'), true);
  assert.equal(document.querySelectorAll('.secondary-breakdown .ko-pill.clear').length, 6);
  assert.equal(document.querySelector('#comparison').textContent.includes('No module inspection details are available'), false);
  assert.equal(document.querySelector('#comparison').textContent.includes('No criterion details recorded'), false);
  for (const accordion of document.querySelectorAll('.baseline-breakdown .module-accordion, .secondary-breakdown .module-accordion')) {
    const row = accordion.querySelector('.criteria-table tbody tr');
    assert.ok(row, `Module ${accordion.dataset.module} must have a criterion row`);
    assert.notEqual(row.querySelector('code')?.textContent, '', 'criterion metric key must be populated');
    assert.equal(row.textContent.includes('/ 5.0'), true, 'criterion score/max must be populated');
    assert.equal(row.textContent.includes('Matched governed test rule.'), true, 'rule explanation must be populated');
  }
  const capped = [...document.querySelectorAll('.secondary-breakdown .module-accordion')].filter(item => item.querySelector('.cap-label')).map(item => item.dataset.module);
  assert.deepEqual(capped, ['C', 'E', 'F']);
  const moduleE = document.querySelector('.secondary-breakdown .module-accordion[data-module="E"]');
  const moduleESummary = moduleE.querySelector('summary');
  assert.equal(moduleE.open, false);
  assert.equal(moduleESummary.tabIndex, 0, 'native summary must remain keyboard focusable');
  assert.equal(moduleESummary.getAttribute('aria-expanded'), 'false');
  moduleESummary.click();
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.equal(moduleE.open, true);
  assert.equal(moduleESummary.getAttribute('aria-expanded'), 'true');
  assert.equal(moduleE.querySelector('.criteria-table tbody')?.textContent.includes('Business & Moat criterion'), true);
  assert.equal(moduleE.querySelector('.state-pill')?.textContent, 'CAPPED');
  assert.equal(moduleE.querySelector('tbody')?.textContent.includes('Matched governed test rule.'), true);
}

const paths = requests.map(request => new URL(request).pathname);
assert.deepEqual(paths.slice(0, 3), [
  '/api/v1/evaluations',
  `/api/v1/evaluations/${encodeURIComponent(evaluationId)}/input`,
  `/api/v1/comparison/${encodeURIComponent(evaluationId)}`,
]);
assert.equal(paths.some(path => path.startsWith('/workbench/api/')), false);
assert.deepEqual(errors, []);
assert.equal(document.querySelector('#workbench-status').classList.contains('error'), false);

dom.window.close();
console.log(JSON.stringify({ controls: 41, hydrated: Object.keys(expected).length, comparisonMode, cards: expectedCards, requests: paths }));
