const assert = require("node:assert/strict");
const test = require("node:test");

const { indexLogDocument, maskSensitive, writeStructuredLog } = require("../src/shared/logger");

test("maskSensitive masks nested sensitive fields", () => {
  const masked = maskSensitive({
    username: "buyer_001",
    password: "password123",
    profile: {
      email: "buyer@example.com",
      token: "secret-token",
    },
    items: [{ accessToken: "access-token", productId: "prod-001" }],
  });

  assert.deepEqual(masked, {
    username: "buyer_001",
    password: "***MASKED***",
    profile: {
      email: "***MASKED***",
      token: "***MASKED***",
    },
    items: [{ accessToken: "***MASKED***", productId: "prod-001" }],
  });
});

test("indexLogDocument writes to the configured Elasticsearch index", async () => {
  const calls = [];
  const fetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true };
  };

  const result = await indexLogDocument(
    { request_id: "req-test", response_status: 200 },
    {
      fetch,
      index: "demo-index",
      url: "http://elasticsearch:9200/",
    },
  );

  assert.deepEqual(result, { indexed: true });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "http://elasticsearch:9200/demo-index/_doc");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.headers["content-type"], "application/json");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    request_id: "req-test",
    response_status: 200,
  });
});

test("writeStructuredLog keeps requests safe when Elasticsearch indexing fails", async () => {
  const messages = { logs: [], warnings: [] };
  const consoleLogger = {
    log(message) {
      messages.logs.push(message);
    },
    warn(message) {
      messages.warnings.push(message);
    },
  };

  const result = await writeStructuredLog(
    { request_id: "req-test", response_status: 200 },
    {
      consoleLogger,
      fetch: async () => ({ ok: false, status: 503 }),
      index: "demo-index",
      url: "http://elasticsearch:9200",
    },
  );

  assert.deepEqual(result, { indexed: false, reason: "indexing_failed" });
  assert.equal(messages.logs.length, 1);
  assert.deepEqual(JSON.parse(messages.logs[0]), {
    request_id: "req-test",
    response_status: 200,
  });
  assert.equal(messages.warnings.length, 1);
  assert.match(messages.warnings[0], /Elasticsearch log indexing skipped/);
});
