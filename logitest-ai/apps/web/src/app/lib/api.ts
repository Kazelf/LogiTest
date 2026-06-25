export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

type QueryValue = string | number | boolean | null | undefined;

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

async function request<T>(
  path: string,
  options: RequestInit & { query?: Record<string, QueryValue> } = {},
) {
  const { query, headers, ...init } = options;
  const response = await fetch(buildUrl(path, query), {
    ...init,
    headers: {
      "content-type": "application/json",
      ...headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      detail = await response.text();
    }
    throw new Error(`${response.status} ${detail}`);
  }

  return (await response.json()) as T;
}

export type ListResponse<T> = {
  items: T[];
  limit: number;
  offset: number;
  total: number;
};

export type ImportResponse = {
  source: string;
  index?: string;
  loaded_records: number;
  imported_logs?: number;
  sessions: number;
  counts: Record<string, number>;
};

export type LogItem = {
  id: string;
  external_log_id: string | null;
  session_external_id: string | null;
  trace_id: string | null;
  user_id: string | null;
  service_name: string;
  level: string;
  method: string | null;
  endpoint: string | null;
  status_code: number | null;
  response_time_ms: number | null;
  occurred_at: string;
};

export type SessionItem = {
  id: string;
  external_session_id: string;
  user_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  request_count: number;
  log_count: number;
  source: string;
  services: string[];
  created_at: string;
};

export type SessionDetail = {
  session: SessionItem & { metadata: Record<string, unknown> };
  logs: LogItem[];
};

export type JourneyItem = {
  id: string;
  persona_id: string | null;
  persona_name: string | null;
  name: string;
  description: string | null;
  source_session_count: number;
  frequency_score: number | null;
  risk_score: number | null;
  steps: JourneyStep[];
  example_session_id: string | null;
  created_at: string;
  updated_at: string;
};

export type JourneyStep = {
  order?: number;
  method?: string;
  endpoint?: string;
  status_code?: number;
  action_type?: string;
  extract?: Record<string, string>;
  uses?: Record<string, unknown>;
  [key: string]: unknown;
};

export type AnalyzeResponse = {
  sessions_analyzed: number;
  personas_upserted: number;
  journeys_upserted: number;
  source: string;
  method: string;
};

export type GenerateResponse = {
  test_case_id: string;
  journey_id: string;
  name: string;
  status: string;
  step_count: number;
  artifacts: ArtifactSummary[];
};

export type ArtifactSummary = {
  id: string | null;
  framework: string;
  language: string;
  file_path: string | null;
};

export type ArtifactDetail = ArtifactSummary & {
  code: string;
  created_at: string | null;
  updated_at: string | null;
};

export type TestCaseItem = {
  id: string;
  journey_id: string | null;
  persona_id: string | null;
  journey_name: string | null;
  persona_name: string | null;
  name: string;
  description: string | null;
  type: string;
  status: string;
  step_count: number;
  generated_by: string;
  created_at: string;
  updated_at: string;
};

export type TestCaseDetail = TestCaseItem & {
  steps: Record<string, unknown>[];
  assertions: Record<string, unknown>[];
  golden_response: Record<string, unknown>;
  generated_code: string | null;
  artifacts: ArtifactDetail[];
};

export type TestRun = {
  id: string;
  test_case_id: string;
  status: string;
  target_environment: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  actual_response: Record<string, unknown>;
  diff_result: Record<string, unknown>;
  error_message: string | null;
  runner_metadata: Record<string, unknown>;
  created_at: string | null;
};

export const api = {
  importMockLogs: () => request<ImportResponse>("/api/logs/import-mock", { method: "POST" }),
  importElasticsearchLogs: () =>
    request<ImportResponse>("/api/logs/import-elasticsearch", {
      method: "POST",
      body: JSON.stringify({ limit: 200 }),
    }),
  listLogs: () => request<ListResponse<LogItem>>("/api/logs", { query: { limit: 50 } }),
  listSessions: () =>
    request<ListResponse<SessionItem>>("/api/logs/sessions", { query: { limit: 50 } }),
  getSession: (sessionId: string) => request<SessionDetail>(`/api/logs/sessions/${sessionId}`),
  analyzeJourneys: () => request<AnalyzeResponse>("/api/behavior/analyze", { method: "POST" }),
  listJourneys: () =>
    request<ListResponse<JourneyItem>>("/api/behavior/journeys", { query: { limit: 50 } }),
  generateTest: (journeyId: string) =>
    request<GenerateResponse>("/api/test-generation/generate", {
      method: "POST",
      body: JSON.stringify({
        journey_id: journeyId,
        overwrite: true,
        frameworks: ["jest_supertest"],
        write_files: false,
      }),
    }),
  listTestCases: () =>
    request<ListResponse<TestCaseItem>>("/api/test-generation/test-cases", {
      query: { limit: 50 },
    }),
  getTestCase: (testCaseId: string) =>
    request<TestCaseDetail>(`/api/test-generation/test-cases/${testCaseId}`),
  runTestCase: (testCaseId: string, targetBaseUrl: string) =>
    request<TestRun>(`/api/execution/test-cases/${testCaseId}/run`, {
      method: "POST",
      body: JSON.stringify({
        target_base_url: targetBaseUrl,
        target_environment: "demo",
        timeout_seconds: 10,
      }),
    }),
  listRuns: () =>
    request<ListResponse<TestRun>>("/api/reports/test-runs", { query: { limit: 50 } }),
  getRun: (runId: string) => request<TestRun>(`/api/reports/test-runs/${runId}`),
};
