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

module.exports = { maskSensitive };
