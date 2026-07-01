describe("elasticsearchLogger", () => {
  const originalEnv = process.env;
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
    global.fetch = jest.fn();
  });

  afterEach(() => {
    process.env = originalEnv;
    global.fetch = originalFetch;
  });

  test("does not index when Elasticsearch logging is disabled", async () => {
    process.env.ENABLE_ELASTICSEARCH_LOGGING = "false";
    process.env.ELASTICSEARCH_URL = "http://localhost:9200";

    const { indexRequestLog } = require("../src/config/elasticsearchLogger");
    const indexed = await indexRequestLog({ service: "shoplite-api" });

    expect(indexed).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  test("indexes request log with LogiTest-compatible fields", async () => {
    process.env.ENABLE_ELASTICSEARCH_LOGGING = "true";
    process.env.ELASTICSEARCH_URL = "http://localhost:9200/";
    process.env.SHOPLITE_LOG_INDEX = "logitest-demo-logs";
    global.fetch.mockResolvedValue({ ok: true });

    const { indexRequestLog } = require("../src/config/elasticsearchLogger");
    const indexed = await indexRequestLog({
      timestamp: "2026-07-01T10:00:00.000Z",
      service: "shoplite-api",
      session_id: "sess-1",
      method: "POST",
      endpoint: "/api/auth/login",
      request_body: { email: "***MASKED***" },
      response_status: 200,
      response_body: { ok: true }
    });

    expect(indexed).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:9200/logitest-demo-logs/_doc",
      expect.objectContaining({
        method: "POST",
        headers: { "content-type": "application/json" }
      })
    );
    const [, options] = global.fetch.mock.calls[0];
    const body = JSON.parse(options.body);
    expect(body.service_name).toBe("shoplite-api");
    expect(body.status_code).toBe(200);
    expect(body.request_payload).toEqual({ email: "***MASKED***" });
  });
});
