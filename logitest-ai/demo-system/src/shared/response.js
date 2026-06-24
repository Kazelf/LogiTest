function ok(data, meta = {}) {
  return {
    success: true,
    data,
    meta,
  };
}

function created(data, meta = {}) {
  return ok(data, meta);
}

function fail(code, message) {
  return {
    success: false,
    error: {
      code,
      message,
    },
  };
}

module.exports = { created, fail, ok };
