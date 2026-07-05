const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:4000";

function sessionId() {
  const existing = localStorage.getItem("shoplite_session_id");
  if (existing) return existing;
  const next = `sess_${crypto.randomUUID()}`;
  localStorage.setItem("shoplite_session_id", next);
  return next;
}

function traceId() {
  return localStorage.getItem("shoplite_trace_id");
}

export function getToken() {
  return localStorage.getItem("shoplite_token");
}

export function setToken(token) {
  if (token) localStorage.setItem("shoplite_token", token);
  else localStorage.removeItem("shoplite_token");
}

export async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    "x-session-id": sessionId(),
    ...(options.headers || {})
  };
  const existingTraceId = traceId();
  if (existingTraceId) headers["x-trace-id"] = existingTraceId;

  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined
  });
  const responseSessionId = response.headers.get("x-session-id");
  const responseTraceId = response.headers.get("x-trace-id");
  if (responseSessionId) localStorage.setItem("shoplite_session_id", responseSessionId);
  if (responseTraceId) localStorage.setItem("shoplite_trace_id", responseTraceId);

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.message || "API request failed");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}
