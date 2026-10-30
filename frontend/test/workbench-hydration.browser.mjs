import { JSDOM, VirtualConsole } from 'jsdom';
import assert from 'node:assert/strict';

const [url, evaluationId, comparisonMode = 'available'] = process.argv.slice(2);
if (!url || !evaluationId) throw new Error('usage: node workbench-hydration.browser.mjs URL EVALUATION_ID [available|404]');

const requests = [];
const submissions = [];
const errors = [];
const moduleNames = ['Financial Quality', 'Valuation', 'Proceeds & Lock-in', 'Governance', 'Business & Moat', 'Market Context'];
const syntheticSecondary = {
  secondary: { score: 82, verdict: 'SUBSCRIBE', confidence: 'High', knockout_status: 'CLEAR', knockouts: Array.from({ length: 6 }, (_, i) => ({ rule_id: `K${i + 1}`, state: 'CLEAR' })) },
  inspection: { completeness_pct: 96, confidence: 'High', modules: moduleNames.map((name, index) => ({
    module_id: String.fromCharCode(65 + index), name, baseline_points: 0,
    secondary_points: [20, 16, 15, 12, 15, 10][index], cap: [25, 20, 15, 15, 15, 10][index],
    delta: [20, 16, 15, 12, 15, 10][index], cap_applied: [2, 4, 5].includes(index),
    criteria: [{ criterion_id: `criterion_${index}`, label: `${name} criterion`, metric: `metric_${index}`, baseline_value: null, secondary_value: 'strong', score: 5, max: 5, state: index === 4 ? 'CAPPED' : 'SCORED', explanation: 'Matched governed test rule.' }],
  })) },
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
      if (submissions.length && new URL(absolute).pathname.startsWith('/api/v1/comparison/')) {
        return new Response(JSON.stringify({ baseline: { badge: '[LAYER_1_BASE]' }, enriched: [syntheticSecondary], scenarios: [] }), { status: 200, headers: { 'content-type': 'application/json' } });
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
  while (document.querySelectorAll('.module-accordion').length !== 6) {
    if (Date.now() > submissionDeadline) throw new Error('module accordion did not populate after recalculation');
    await new Promise(resolve => setTimeout(resolve, 25));
  }
  assert.equal(document.querySelector('.secondary-summary')?.textContent.includes('82.0'), true);
  assert.equal(document.querySelector('.verdict-badge')?.textContent, 'SUBSCRIBE');
  assert.equal(document.querySelectorAll('.ko-pill.clear').length, 6);
  const capped = [...document.querySelectorAll('.module-accordion')].filter(item => item.querySelector('.cap-label')).map(item => item.dataset.module);
  assert.deepEqual(capped, ['C', 'E', 'F']);
  const moduleE = document.querySelector('.module-accordion[data-module="E"]');
  assert.equal(moduleE.open, false);
  moduleE.querySelector('summary').click();
  assert.equal(moduleE.open, true);
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
