function createHttpError(status, errorCode, message, details) {
  const error = new Error(message || errorCode);
  error.status = status;
  error.errorCode = errorCode;
  error.details = details;
  return error;
}

function notFoundHandler(req, res) {
  res.status(404).json({
    error_code: "NOT_FOUND",
    message: `Route not found: ${req.method} ${req.originalUrl}`
  });
}

function errorHandler(err, req, res, next) {
  const status = err.status || 500;
  const payload = {
    error_code: err.errorCode || "INTERNAL_SERVER_ERROR",
    message: err.message || "Unexpected server error"
  };

  if (err.details) {
    payload.details = err.details;
  }

  res.status(status).json(payload);
}

module.exports = { createHttpError, errorHandler, notFoundHandler };
