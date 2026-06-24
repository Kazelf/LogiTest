const crypto = require("crypto");

function requestContext() {
  return (req, res, next) => {
    const sessionId = req.header("x-session-id") || `sess_${crypto.randomUUID()}`;
    const traceId = req.header("x-trace-id") || `trace_${crypto.randomUUID()}`;
    const requestId = req.header("x-request-id") || `req_${crypto.randomUUID()}`;
    const userId = req.header("x-user-id") || null;

    req.context = {
      sessionId,
      traceId,
      requestId,
      userId,
      startedAt: Date.now(),
    };

    res.setHeader("x-session-id", sessionId);
    res.setHeader("x-trace-id", traceId);
    res.setHeader("x-request-id", requestId);

    next();
  };
}

module.exports = { requestContext };
