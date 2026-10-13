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

  assert.equal(apiJs.includes("method: 'POST'"), false);
  assert.equal(apiJs.includes("method: 'PUT'"), false);
  assert.equal(apiJs.includes("method: 'PATCH'"), false);
  assert.equal(apiJs.includes("method: 'DELETE'"), false);

  // Verify no credentials / secrets are hardcoded
  assert.equal(appJs.includes('AI71_API_KEY'), false);
  assert.equal(appJs.includes('OPENAI_API_KEY'), false);
  assert.equal(appJs.includes('SECRET'), false);
  assert.equal(apiJs.includes('API_KEY'), false);
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
