const { env } = require("./env");

function isElasticsearchEnabled() {
  return Boolean(env.elasticsearchLogging && env.elasticsearchUrl);
}

async function indexRequestLog(logRecord) {
  if (!isElasticsearchEnabled()) {
    return false;
  }

  const baseUrl = env.elasticsearchUrl.replace(/\/$/, "");
  const index = encodeURIComponent(env.shopliteLogIndex);
  const response = await fetch(`${baseUrl}/${index}/_doc`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      ...logRecord,
      service_name: logRecord.service,
      status_code: logRecord.response_status,
      request_payload: logRecord.request_body
    })
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`Elasticsearch index failed: ${response.status} ${body}`);
  }

  return true;
}

module.exports = { indexRequestLog, isElasticsearchEnabled };
