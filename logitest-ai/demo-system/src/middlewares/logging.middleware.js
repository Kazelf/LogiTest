const { maskSensitive } = require("../shared/logger");

function loggingMiddleware() {
  return (req, res, next) => {
    const originalJson = res.json.bind(res);
    let responseBody = {};

    res.json = (body) => {
      responseBody = body;
      return originalJson(body);
    };

    res.on("finish", () => {
      const context = req.context || {};
      const responseTimeMs = Date.now() - (context.startedAt || Date.now());
      const log = {
        timestamp: new Date().toISOString(),
        level: res.statusCode >= 500 ? "error" : "info",
        service_name: "demo-ecommerce",
        environment: process.env.NODE_ENV || "demo",
        session_id: context.sessionId,
        trace_id: context.traceId,
        request_id: context.requestId,
        user_id: req.user?.id || context.userId,
        method: req.method,
        endpoint: req.originalUrl,
        request_headers: maskSensitive({
          authorization: req.header("authorization"),
          "x-session-id": req.header("x-session-id"),
          "x-trace-id": req.header("x-trace-id"),
          "x-request-id": req.header("x-request-id"),
          "x-user-id": req.header("x-user-id"),
        }),
        request_payload: maskSensitive(req.body || {}),
        response_status: res.statusCode,
        response_body: maskSensitive(responseBody),
        response_time_ms: responseTimeMs,
      };

      console.log(JSON.stringify(log));
    });

    next();
  };
}

module.exports = { loggingMiddleware };
