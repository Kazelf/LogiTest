const SENSITIVE_KEYS = new Set([
  "authorization",
  "password",
  "token",
  "accessToken",
  "refreshToken",
  "email",
  "phone",
]);

function maskSensitive(value) {
  if (Array.isArray(value)) {
    return value.map((item) => maskSensitive(item));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([, entryValue]) => entryValue !== undefined)
        .map(([key, entryValue]) => [
          key,
          SENSITIVE_KEYS.has(key) ? "***MASKED***" : maskSensitive(entryValue),
        ]),
    );
  }

  return value;
}

function getElasticsearchConfig() {
  return {
    index: process.env.DEMO_LOG_INDEX || "logitest-demo-logs",
    url: process.env.ELASTICSEARCH_URL,
  };
}

async function indexLogDocument(log, options = {}) {
  const config = {
    ...getElasticsearchConfig(),
    ...options,
  };

  if (!config.url) {
    return { indexed: false, reason: "elasticsearch_disabled" };
  }

  const fetchFn = config.fetch || globalThis.fetch;
  if (typeof fetchFn !== "function") {
    return { indexed: false, reason: "fetch_unavailable" };
  }

  const endpoint = `${config.url.replace(/\/$/, "")}/${encodeURIComponent(config.index)}/_doc`;
  const response = await fetchFn(endpoint, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(log),
  });

  if (!response.ok) {
    throw new Error(`Elasticsearch indexing failed with status ${response.status}`);
  }

  return { indexed: true };
}

function writeStructuredLog(log, options = {}) {
  const consoleLogger = options.consoleLogger || console;
  consoleLogger.log(JSON.stringify(log));

  return indexLogDocument(log, options).catch((error) => {
    const message = error instanceof Error ? error.message : "Unknown Elasticsearch logging error";
    consoleLogger.warn(`Elasticsearch log indexing skipped: ${message}`);
    return { indexed: false, reason: "indexing_failed" };
  });
}

module.exports = { indexLogDocument, maskSensitive, writeStructuredLog };
