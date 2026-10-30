import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { App } from '../app.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('App - Formatting helpers produce valid accessible HTML markup', () => {
  const app = new App();

  // HTML escaping
  assert.equal(app.escape('<script>alert("xss")</script>'), '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');
  assert.equal(app.escape('A & B'), 'A &amp; B');
  assert.equal(app.escape(null), '');
  assert.equal(app.escape(undefined), '');

  // renderVerdictBadge
  const applyVerdict = app.renderVerdictBadge('APPLY');
  assert.ok(applyVerdict.includes('badge badge-apply'));
  assert.ok(applyVerdict.includes('APPLY'));

  const considerVerdict = app.renderVerdictBadge('CONSIDER');
  assert.ok(considerVerdict.includes('badge badge-consider'));
  assert.ok(considerVerdict.includes('CONSIDER'));

  const avoidVerdict = app.renderVerdictBadge('AVOID');
  assert.ok(avoidVerdict.includes('badge badge-avoid'));
  assert.ok(avoidVerdict.includes('AVOID'));

  const insufficientVerdict = app.renderVerdictBadge('INSUFFICIENT_DATA');
  assert.ok(insufficientVerdict.includes('badge badge-insufficient'));
  assert.ok(insufficientVerdict.includes('INSUFFICIENT DATA'));

  const unknownVerdict = app.renderVerdictBadge('UNKNOWN');
  assert.ok(unknownVerdict.includes('badge badge-unknown'));
  assert.ok(unknownVerdict.includes('UNKNOWN'));

  // renderSemanticStateBadge
  const stateScored = app.renderSemanticStateBadge('SCORED');
  assert.ok(stateScored.includes('badge-clear'));
  assert.ok(stateScored.includes('SCORED'));

  const stateUnknown = app.renderSemanticStateBadge('UNKNOWN');
  assert.ok(stateUnknown.includes('badge-unknown'));
  assert.ok(stateUnknown.includes('UNKNOWN'));

  const stateNA = app.renderSemanticStateBadge('NOT_APPLICABLE');
  assert.ok(stateNA.includes('badge-na'));
  assert.ok(stateNA.includes('NOT APPLICABLE'));

  // renderMetricValue
  assert.ok(app.renderMetricValue(null, 'UNKNOWN').includes('badge-unknown'));
  assert.ok(app.renderMetricValue(undefined, 'UNKNOWN').includes('badge-unknown'));
  assert.ok(app.renderMetricValue(null, 'NOT_APPLICABLE').includes('badge-na'));
  assert.equal(app.renderMetricValue(42.5, 'SCORED'), '<code>42.50</code>');
  assert.equal(app.renderMetricValue(true, 'SCORED'), '<code>True</code>');
  assert.equal(app.renderMetricValue(false, 'SCORED'), '<code>False</code>');
  assert.equal(app.renderMetricValue('SAMPLE', 'SCORED'), '<code>SAMPLE</code>');

  // formatDate
  assert.equal(app.formatDate(null), '—');
  assert.equal(app.formatDate('2026-10-06T12:00:00Z'), 'Tue, 06 Oct 2026 12:00:00 UTC');
});

test('App - Zero Score Calculation Invariant: source files contain no arithmetic weighting or scoring formulas', () => {
  const appJsPath = path.resolve(__dirname, '../app.js');
  const apiJsPath = path.resolve(__dirname, '../api.js');

  const appJs = fs.readFileSync(appJsPath, 'utf8');
  const apiJs = fs.readFileSync(apiJsPath, 'utf8');

  // Verify no weights or scoring formula calculations
  // Weight constants in v1.5: 0.25, 0.20, 0.15, 0.10, 0.30
  assert.equal(appJs.includes('* 0.25'), false, 'app.js must not calculate module weights');
  assert.equal(appJs.includes('* 0.20'), false, 'app.js must not calculate module weights');
  assert.equal(appJs.includes('* 0.15'), false, 'app.js must not calculate module weights');
  assert.equal(appJs.includes('* 0.10'), false, 'app.js must not calculate module weights');
  assert.equal(appJs.includes('* 0.30'), false, 'app.js must not calculate module weights');
  assert.equal(appJs.includes('calculateScore'), false, 'app.js must not calculate scores');
  assert.equal(appJs.includes('deriveVerdict'), false, 'app.js must not derive verdicts');

  // Verify no POST/PUT/PATCH/DELETE methods used
  assert.equal(appJs.includes("method: 'POST'"), false);
  assert.equal(appJs.includes("method: 'PUT'"), false);
  assert.equal(appJs.includes("method: 'PATCH'"), false);
  assert.equal(appJs.includes("method: 'DELETE'"), false);

  // The API client may POST only for its explicit ingestion and lifecycle actions.
  assert.equal(apiJs.includes("method: 'POST'"), true);
  assert.equal(apiJs.includes("method: 'PUT'"), false);
  assert.equal(apiJs.includes("method: 'PATCH'"), false);
  assert.equal(apiJs.includes("method: 'DELETE'"), false);
  assert.equal(apiJs.includes("async archiveEvaluation("), true);
  assert.equal(apiJs.includes("async ingestDocument("), true);

  // Verify no credentials / secrets are hardcoded
  assert.equal(appJs.includes('AI71_API_KEY'), false);
  assert.equal(appJs.includes('OPENAI_API_KEY'), false);
  assert.equal(appJs.includes('SECRET'), false);
  assert.equal(apiJs.includes('API_KEY'), false);
});

test('App - existing frontend exposes embedded Dual-Reality Workbench tab', () => {
  const appJs = fs.readFileSync(path.resolve(__dirname, '../app.js'), 'utf8');
  const indexHtml = fs.readFileSync(path.resolve(__dirname, '../index.html'), 'utf8');
  assert.ok(indexHtml.includes('id="nav-workbench"'));
  assert.ok(indexHtml.includes('id="workbench-frame"'));
  assert.ok(indexHtml.includes('Dual-Reality Workbench'));
  assert.ok(appJs.includes("segments[0] === 'workbench'"));
  assert.ok(appJs.includes("frame.setAttribute('src', '../workbench/')"));
  assert.ok(appJs.includes("document.readyState === 'loading'"));
  assert.ok(appJs.includes("data-app-ready"));
  assert.equal(indexHtml.includes('Initializing scorecard...'), false);
  assert.equal(indexHtml.includes('Initializing directory...'), false);
});

test('App - Governance Invariant: no policy activation or modification controls in frontend', () => {
  const appJsPath = path.resolve(__dirname, '../app.js');
  const indexHtmlPath = path.resolve(__dirname, '../index.html');

  const appJs = fs.readFileSync(appJsPath, 'utf8');
  const indexHtml = fs.readFileSync(indexHtmlPath, 'utf8');

  // No activation controls or proposal acceptance
  assert.equal(appJs.includes('activatePolicy'), false);
  assert.equal(appJs.includes('applyConfig'), false);
  assert.equal(appJs.includes('set_active'), false);
  assert.equal(indexHtml.includes('activate'), false);
  assert.equal(indexHtml.includes('Activate'), false);
});

test('App - Fail-Closed Invariant: missing/null values never default to zero', () => {
  const app = new App();
  // Ensure renderMetricValue of null or undefined does not return 0 or 0.00
  assert.notEqual(app.renderMetricValue(null, 'UNKNOWN'), '<code>0.00</code>');
  assert.notEqual(app.renderMetricValue(undefined, 'UNKNOWN'), '<code>0.00</code>');
  assert.ok(app.renderMetricValue(null, 'UNKNOWN').includes('UNKNOWN'));
});

test('Penalty rendering distinguishes an unevaluated penalty from a cleared one', () => {
  const app = new App();
  const html = app.renderPenaltyItems([
    {
      id: 'auditor_cfo_exit',
      label: 'Auditor/CFO resignation in last 2 years',
      points: 0,
      state: 'UNKNOWN',
      reason: 'the trigger could not be evaluated; the penalty is neither applied nor ignored, and is carried in the lower bound',
    },
    {
      id: 'receivable_days_up',
      label: 'Receivable days up >30% YoY',
      points: 0,
      state: 'SCORED',
      reason: 'not triggered',
    },
    {
      id: 'margin_spike',
      label: 'Margin up >500 bps YoY in either of the last two FYs',
      points: -3,
      state: 'SCORED',
      reason: 'triggered',
    },
  ]);

  // The zero-point UNKNOWN is explicitly "carried in range", never "cleared".
  assert.ok(html.includes('UNKNOWN \u2014 carried in range'));
  assert.ok(html.includes('carried in the lower bound'));
  assert.ok(html.includes('Not triggered'));
  assert.ok(html.includes('Applied'));
  assert.ok(html.includes('-3.0 pts'));
  // The reason text is escaped, not injected as HTML.
  assert.ok(!html.includes('<script>'));
  const escaped = app.renderPenaltyItems([
    { id: 'x', label: '<script>alert(1)</script>', points: 0, state: 'SCORED', reason: '<b>no</b>' },
  ]);
  assert.ok(escaped.includes('&lt;script&gt;'));
  assert.ok(!escaped.includes('<b>no</b>'));
});

test('Penalty rendering handles an empty list', () => {
  const app = new App();
  assert.ok(app.renderPenaltyItems([]).includes('Zero penalties triggered'));
  assert.ok(app.renderPenaltyItems(undefined).includes('Zero penalties triggered'));
});

test('Governance metric rendering keeps UNKNOWN distinct from a verified absence', () => {
  // A23-C: the presentation layer must never turn a missing governance input
  // into a favourable statement.  `sebi_ed_action_active` and
  // `litigation_bucket` are the two fields where an extraction defect used to
  // read as "no adverse action", so the three display states are pinned here:
  //   adverse evidence      -> the value itself, SCORED
  //   verified absence      -> the value itself (False / "clean"), SCORED
  //   no evidence supplied   -> UNKNOWN, and no favourable wording at all
  const app = new App();

  const adverse = app.renderMetricValue('criminal_or_regulatory', 'SCORED');
  assert.ok(adverse.includes('criminal_or_regulatory'));
  assert.ok(!adverse.includes('badge-unknown'));

  const verifiedAbsent = app.renderMetricValue(false, 'SCORED');
  assert.equal(verifiedAbsent, '<code>False</code>');

  // Missing / null / UNKNOWN -- each must render the unknown badge, and none of
  // them may produce text that reads as an all-clear.
  for (const [value, state] of [
    [null, 'UNKNOWN'],
    [undefined, 'UNKNOWN'],
    [false, 'UNKNOWN'],
    ['clean', 'UNKNOWN'],
    [null, 'SCORED'],
  ]) {
    const html = app.renderMetricValue(value, state);
    assert.ok(html.includes('badge-unknown'), `expected UNKNOWN badge for ${value}/${state}`);
    assert.ok(!/no active|not triggered|clear|no adverse/i.test(html), html);
  }

  // The state badge keeps the same three-way distinction.
  assert.ok(app.renderSemanticStateBadge('UNKNOWN').includes('UNKNOWN'));
  assert.ok(!app.renderSemanticStateBadge('UNKNOWN').includes('SCORED'));
  assert.ok(app.renderSemanticStateBadge('SCORED').includes('SCORED'));
  assert.ok(app.renderSemanticStateBadge('NOT_APPLICABLE').includes('NOT APPLICABLE'));

  // A missing verdict is UNKNOWN, never a pass.
  assert.ok(app.renderVerdictBadge(null).includes('UNKNOWN'));
  assert.ok(app.renderVerdictBadge(undefined).includes('UNKNOWN'));
});
