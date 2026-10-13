import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiClient, ApiError } from '../api.js';

test('ApiClient - Initialisation and read-only protocol', () => {
  const client = new ApiClient('/custom/base');
  assert.equal(client.baseUrl, '/custom/base');
  assert.equal(client.apiPrefix, '/custom/base/api/v1');

  // Default baseUrl
  const defaultClient = new ApiClient();
  assert.equal(defaultClient.baseUrl, '');
  assert.equal(defaultClient.apiPrefix, '/api/v1');

  // Verify strictly NO mutation methods exist
  const forbiddenMethods = [
    'post', 'put', 'patch', 'delete',
    'create', 'update', 'remove', 'mutate',
    'activatePolicy', 'setPolicy', 'calculateScore',
    '_post', '_put', '_delete'
  ];
  for (const method of forbiddenMethods) {
    assert.equal(typeof defaultClient[method], 'undefined', `Client must not expose ${method}`);
  }
});

test('ApiClient - System endpoints (getHealth, getMeta, getConfigurationStatus)', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  try {
    globalThis.fetch = async (url, options) => {
      calls.push({ url, options });
      return {
        ok: true,
        status: 200,
        json: async () => ({ status: 'ok' })
      };
    };

    const client = new ApiClient();
    await client.getHealth();
    await client.getMeta();
    await client.getConfigurationStatus();

    assert.ok(calls[0].url.endsWith('/api/v1/health'));
    assert.equal(calls[0].options.method, 'GET');
    assert.ok(calls[1].url.endsWith('/api/v1/meta'));
    assert.equal(calls[1].options.method, 'GET');
    assert.ok(calls[2].url.endsWith('/api/v1/configuration/current'));
    assert.equal(calls[2].options.method, 'GET');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ApiClient - listIpos builds query parameters accurately', async () => {
  const mockPayload = {
    items: [],
    total: 0,
    page: 2,
    page_size: 25,
    pages: 1
  };

  const originalFetch = globalThis.fetch;
  let requestedUrl = null;
  try {
    globalThis.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        status: 200,
        json: async () => mockPayload
      };
    };

    const client = new ApiClient();
    const result = await client.listIpos({ page: 2, pageSize: 25, search: 'Tech Corp', sectorProfile: 'TECHNOLOGY' });
    assert.deepEqual(result, mockPayload);
    const parsed = new URL(requestedUrl);
    assert.equal(parsed.pathname, '/api/v1/ipos');
    assert.equal(parsed.searchParams.get('page'), '2');
    assert.equal(parsed.searchParams.get('page_size'), '25');
    assert.equal(parsed.searchParams.get('search'), 'Tech Corp');
    assert.equal(parsed.searchParams.get('sector_profile'), 'TECHNOLOGY');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ApiClient - listEvaluations builds query parameters accurately', async () => {
  const mockPayload = { items: [], total: 0, page: 1, page_size: 10 };
  const originalFetch = globalThis.fetch;
  let requestedUrl = null;
  try {
    globalThis.fetch = async (url) => {
      requestedUrl = url;
      return {
        ok: true,
        status: 200,
        json: async () => mockPayload
      };
    };

    const client = new ApiClient();
    await client.listEvaluations({
      page: 1,
      pageSize: 10,
      ipoId: 'ipo_001',
      verdict: 'APPLY',
      mode: 'FINAL'
    });
    const parsed = new URL(requestedUrl);
    assert.equal(parsed.pathname, '/api/v1/evaluations');
    assert.equal(parsed.searchParams.get('page'), '1');
    assert.equal(parsed.searchParams.get('page_size'), '10');
    assert.equal(parsed.searchParams.get('ipo_id'), 'ipo_001');
    assert.equal(parsed.searchParams.get('verdict'), 'APPLY');
    assert.equal(parsed.searchParams.get('mode'), 'FINAL');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ApiClient - Detail endpoints encode URL parameters correctly', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  try {
    globalThis.fetch = async (url) => {
      calls.push(url);
      return {
        ok: true,
        status: 200,
        json: async () => ({ id: 'mock' })
      };
    };

    const client = new ApiClient();
    await client.getIpo('ipo/123?test');
    await client.getIpoHistory('ipo/123?test');
    await client.getEvaluation('eval/456');
    await client.getEvaluationEvidence('eval/456');
    await client.getPostListing('eval/456');
    await client.getPerformance('eval/456');
    await client.getBacktestAnalytics();
    await client.getCalibrationProposals();

    assert.ok(calls[0].endsWith('/api/v1/ipos/ipo%2F123%3Ftest'));
    assert.ok(calls[1].endsWith('/api/v1/ipos/ipo%2F123%3Ftest/history'));
    assert.ok(calls[2].endsWith('/api/v1/evaluations/eval%2F456'));
    assert.ok(calls[3].endsWith('/api/v1/evaluations/eval%2F456/evidence'));
    assert.ok(calls[4].endsWith('/api/v1/evaluations/eval%2F456/post-listing'));
    assert.ok(calls[5].endsWith('/api/v1/evaluations/eval%2F456/performance'));
    assert.ok(calls[6].endsWith('/api/v1/backtest/analytics'));
    assert.ok(calls[7].endsWith('/api/v1/calibration/proposals'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ApiClient - handles 404 and API error schemas', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({
        code: 'EVALUATION_NOT_FOUND',
        message: 'Evaluation eval_missing was not found'
      })
    });

    const client = new ApiClient();
    await assert.rejects(
      async () => client.getEvaluation('eval_missing'),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 404);
        assert.equal(err.code, 'EVALUATION_NOT_FOUND');
        assert.equal(err.message, 'Evaluation eval_missing was not found');
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ApiClient - handles network disconnection error cleanly', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => {
      throw new TypeError('Failed to fetch');
    };

    const client = new ApiClient();
    await assert.rejects(
      async () => client.getHealth(),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 0);
        assert.equal(err.code, 'NETWORK_ERROR');
        assert.ok(err.message.includes('Network failure'));
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('ApiClient - rejects empty or missing IDs in getIpo and getEvaluation', async () => {
  const client = new ApiClient();
  await assert.rejects(
    async () => client.getIpo(''),
    (err) => {
      assert.ok(err instanceof ApiError);
      assert.equal(err.code, 'INVALID_IDENTIFIER');
      return true;
    }
  );
  await assert.rejects(
    async () => client.getEvaluation(null),
    (err) => {
      assert.ok(err instanceof ApiError);
      assert.equal(err.code, 'INVALID_IDENTIFIER');
      return true;
    }
  );
});
