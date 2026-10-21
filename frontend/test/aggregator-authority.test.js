import test from 'node:test';
import assert from 'node:assert/strict';
import { App } from '../app.js';

test('aggregator warning is visible and HTML-escaped, never official', () => {
  const app = new App();
  const html = app.renderAuthorityWarnings({ authority_warnings: ['THIRD_PARTY_AGGREGATOR_OVERRIDE: <script>not official</script>'] });
  assert.ok(html.includes('Third-party authority override'));
  assert.ok(html.includes('THIRD_PARTY_AGGREGATOR_OVERRIDE'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(!html.includes('<script>'));
});

test('official evaluations without override have no warning banner', () => {
  assert.equal(new App().renderAuthorityWarnings({}), '');
});
