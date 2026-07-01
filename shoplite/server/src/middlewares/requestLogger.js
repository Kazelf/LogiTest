const fs = require("fs");
const path = require("path");
const { randomUUID } = require("crypto");
const { env } = require("../config/env");
const { prisma } = require("../config/prisma");
const { indexRequestLog } = require("../config/elasticsearchLogger");
const { getLogMetadata } = require("../modules/logs/logMetadata");

const logPath = path.join(__dirname, "..", "..", "logs", "request-logs.jsonl");
const sensitiveFields = new Set(["password", "passwordHash", "accessToken", "refreshToken", "authorization", "token"]);

function maskSensitive(value) {
  if (Array.isArray(value)) return value.map(maskSensitive);
  if (!value || typeof value !== "object") return value;

  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      key,
      sensitiveFields.has(key) ? "***MASKED***" : maskSensitive(item)
    ])
  );
}

function requestLogger(req, res, next) {
  const startedAt = Date.now();
  const traceId = req.headers["x-trace-id"] || `trace_${randomUUID()}`;
  const sessionId = req.headers["x-session-id"] || `sess_${randomUUID()}`;
  req.traceId = traceId;
  req.sessionId = sessionId;
  res.setHeader("x-trace-id", traceId);
  res.setHeader("x-session-id", sessionId);

  let responseBody = null;
  const originalJson = res.json.bind(res);
  res.json = (body) => {
    responseBody = body;
    return originalJson(body);
  };

  res.on("finish", async () => {
    const responseTimeMs = Date.now() - startedAt;
    const sanitizedRequestBody = maskSensitive({
      ...req.body,
      authorization: req.headers.authorization
    });
    const sanitizedResponseBody = maskSensitive(responseBody);
    const matchedPath = normalizeMatchedPath(req.route?.path ? req.baseUrl + req.route.path : req.path);
    const metadata = getLogMetadata(req.method, matchedPath, sanitizedResponseBody);

    const logRecord = {
      timestamp: new Date().toISOString(),
      environment: env.environment,
      service: "shoplite-api",
      session_id: sessionId,
      trace_id: traceId,
      user_id: req.user?.id || null,
      method: req.method,
      endpoint: req.originalUrl.split("?")[0],
      request_body: sanitizedRequestBody,
      response_status: res.statusCode,
      response_body: sanitizedResponseBody,
      response_time_ms: responseTimeMs,
      error_code: sanitizedResponseBody?.error_code || null,
      ...metadata
    };

    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.appendFile(logPath, `${JSON.stringify(logRecord)}\n`, () => {});

    indexRequestLog(logRecord).catch((error) => {
      console.error("Failed to index ShopLite request log in Elasticsearch:", error.message);
    });

    prisma.requestLog
      .create({
        data: {
          timestamp: new Date(logRecord.timestamp),
          environment: logRecord.environment,
          service: logRecord.service,
          sessionId: logRecord.session_id,
          traceId: logRecord.trace_id,
          userId: logRecord.user_id,
          method: logRecord.method,
          endpoint: logRecord.endpoint,
          requestBody: logRecord.request_body,
          responseStatus: logRecord.response_status,
          responseBody: logRecord.response_body,
          responseTimeMs: logRecord.response_time_ms,
          errorCode: logRecord.error_code,
          actionName: logRecord.action_name,
          businessEntity: logRecord.business_entity,
          businessEntityId: logRecord.business_entity_id,
          journeyHint: logRecord.journey_hint,
          previousStep: logRecord.previous_step,
          nextExpectedStep: logRecord.next_expected_step
        }
      })
      .catch(() => {});
  });

  next();
}

function normalizeMatchedPath(routePath) {
  if (!routePath || routePath === "/") return routePath;
  return routePath.endsWith("/") ? routePath.slice(0, -1) : routePath;
}

module.exports = { requestLogger, maskSensitive };
