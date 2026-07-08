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
  path?: string;
  loaded_records: number;
  imported_logs?: number;
  sessions: number;
  counts: Record<string, number>;
  limit?: number | null;
  page_size?: number;
  new_only?: boolean;
};

export type ClearDatabaseResponse = {
  cleared: boolean;
  deleted: Record<string, number>;
  elasticsearch?: Record<string, unknown> | null;
};

export type DemoSnapshot = {
  mode: string;
  source: string;
  summary: {
    logs: number;
    sessions: number;
    journeys: number;
    generated_tests: number;
    runs: number;
    passed: number;
    failed: number;
    regression_caught: string;
  };
  pipeline: Array<{ label: string; status: string; detail: string }>;
  journeys: Array<{
    name: string;
    persona: string;
    support: number;
    confidence: number;
    risk: string;
    sessions: string[];
    endpoints: string[];
    status: string;
  }>;
  oracle: {
    assert: string[];
    ignore: string[];
    threshold: string;
  };
  provenance: Record<string, string>;
  regression: Record<string, string>;
  evaluation: Record<string, string | number>;
  mvp: string[];
  production: string[];
};

export const DEMO_SNAPSHOT_FALLBACK: DemoSnapshot = {
  mode: "Demo Snapshot",
  source: "Frontend fallback, no database writes",
  summary: {
    logs: 250,
    sessions: 18,
    journeys: 7,
    generated_tests: 7,
    runs: 7,
    passed: 6,
    failed: 1,
    regression_caught: "Payment status mismatch",
  },
  pipeline: [
    { label: "Import Logs", status: "completed", detail: "250 ShopLite API logs" },
    { label: "Normalize & Mask", status: "completed", detail: "PII-safe request/response fields" },
    { label: "Detect Journeys", status: "completed", detail: "7 mined behavior flows" },
    { label: "Score Risk/Confidence", status: "completed", detail: "MVP rules + session support" },
    { label: "Generate Test Cases", status: "completed", detail: "7 API regression cases" },
    { label: "Generate Jest/Supertest", status: "completed", detail: "Runnable framework artifacts" },
    { label: "Run on Staging/UAT", status: "failed", detail: "1 deterministic assertion failed" },
    { label: "Build Regression Report", status: "completed", detail: "Payment mismatch explained" },
  ],
  journeys: [
    {
      name: "Guest product browsing",
      persona: "Guest shopper",
      support: 6,
      confidence: 0.8,
      risk: "Low",
      sessions: ["sess-demo-001", "sess-demo-004"],
      endpoints: ["GET /api/products", "GET /api/products/:id"],
      status: "reviewed",
    },
    {
      name: "Search/filter product",
      persona: "Intent shopper",
      support: 4,
      confidence: 0.7,
      risk: "Medium",
      sessions: ["sess-demo-002", "sess-demo-006"],
      endpoints: ["GET /api/products?search=", "GET /api/products?category="],
      status: "reviewed",
    },
    {
      name: "Add to cart",
      persona: "Buyer",
      support: 5,
      confidence: 0.75,
      risk: "Medium",
      sessions: ["sess-demo-003", "sess-demo-007"],
      endpoints: ["POST /api/cart/items", "GET /api/cart"],
      status: "approved",
    },
    {
      name: "Checkout success",
      persona: "Buyer",
      support: 3,
      confidence: 0.65,
      risk: "High",
      sessions: ["sess-demo-008"],
      endpoints: ["POST /api/orders", "POST /api/payments"],
      status: "approved",
    },
    {
      name: "Payment regression",
      persona: "Buyer",
      support: 2,
      confidence: 0.6,
      risk: "High",
      sessions: ["sess-demo-009"],
      endpoints: ["POST /api/payments", "GET /api/orders/:id"],
      status: "draft",
    },
    {
      name: "Cart validation failure",
      persona: "Buyer",
      support: 2,
      confidence: 0.6,
      risk: "Medium",
      sessions: ["sess-demo-010"],
      endpoints: ["POST /api/cart/items"],
      status: "reviewed",
    },
    {
      name: "Admin cancel order",
      persona: "Admin",
      support: 1,
      confidence: 0.55,
      risk: "High",
      sessions: ["sess-demo-011"],
      endpoints: ["PATCH /api/admin/orders/:id/cancel"],
      status: "draft",
    },
  ],
  oracle: {
    assert: ["status_code", "order_status", "payment_status", "total_amount", "items.length"],
    ignore: ["id", "createdAt", "updatedAt", "token", "trace_id", "request_id"],
    threshold: "p95 response time <= 800 ms",
  },
  provenance: {
    session_id: "sess-demo-009",
    journey_id: "journey-payment-regression",
    test_case_id: "tc-payment-status",
    artifact_id: "artifact-jest-supertest-payment",
    run_id: "run-demo-007",
    report: "report-payment-status-mismatch",
  },
  regression: {
    status: "failed",
    failed_assertion: "payment_status",
    expected: "paid",
    actual: "pending",
    diff: "payment_status: paid -> pending",
    severity: "High",
    suspected_cause: "Payment service did not persist final status after checkout.",
    related_journey: "Payment regression",
    related_trace: "trace-demo-pay-007",
    framework: "Jest/Supertest",
  },
  evaluation: {
    journey_detection_precision: "6/7 reviewer accepted",
    runnable_scripts: "7/8 generated scripts ran successfully",
    regression_detection: "4/5 fault scenarios caught",
    false_positives: 1,
    average_review_time: "3.5 min/test",
  },
  mvp: [
    "Express e-commerce modular monolith",
    "Elasticsearch local / JSONL logs",
    "Rule-based journey detection + Gemini assist",
    "Jest/Supertest API tests",
    "Manual/batch runner",
    "Basic pass/fail report",
  ],
  production: [
    "Distributed services, queue, scalable workers",
    "Process mining / sequence mining / clustering",
    "Approval workflow and audit logs",
    "CI/CD integration",
    "Async/callback testing",
    "RBAC, retention policy, secret manager",
    "Trend dashboard and failure clustering",
  ],
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
  action_type: string;
  request_payload: Record<string, unknown>;
  response_body: Record<string, unknown>;
  raw_log: Record<string, unknown>;
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
  behavior_analysis: BehaviorAnalysis;
  example_session_id: string | null;
  created_at: string;
  updated_at: string;
};

export type BehaviorAnalysis = {
  behaviorName?: string;
  behaviorType?: string;
  userGoal?: string;
  ai_provider?: string;
  ai_model?: string | null;
  fallback_used?: boolean;
  prompt_version?: string;
  stepSummary?: Array<{
    step?: number;
    api?: string;
    meaning?: string;
    importantPayload?: string[];
    importantResponse?: string[];
    inputFromPreviousStep?: string;
  }>;
  chaining?: Array<Record<string, unknown>>;
  riskNotes?: string[];
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

export type PageQuery = {
  limit: number;
  offset: number;
};

export const api = {
  getDemoSnapshot: () => request<DemoSnapshot>("/api/demo/snapshot"),
  importMockLogs: () => request<ImportResponse>("/api/logs/import-mock", { method: "POST" }),
  importElasticsearchLogs: (options: { newOnly?: boolean; limit?: number | null } = {}) =>
    request<ImportResponse>("/api/logs/import-elasticsearch", {
      method: "POST",
      body: JSON.stringify({
        limit: options.limit ?? null,
        page_size: 500,
        new_only: options.newOnly ?? true,
      }),
    }),
  listLogs: (page: PageQuery) => request<ListResponse<LogItem>>("/api/logs", { query: page }),
  listSessions: (page: PageQuery) =>
    request<ListResponse<SessionItem>>("/api/logs/sessions", { query: page }),
  getSession: (sessionId: string) => request<SessionDetail>(`/api/logs/sessions/${sessionId}`),
  analyzeJourneys: () => request<AnalyzeResponse>("/api/behavior/analyze", { method: "POST" }),
  listJourneys: (page: PageQuery) =>
    request<ListResponse<JourneyItem>>("/api/behavior/journeys", { query: page }),
  getJourney: (journeyId: string) => request<JourneyItem>(`/api/behavior/journeys/${journeyId}`),
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
  listTestCases: (page: PageQuery) =>
    request<ListResponse<TestCaseItem>>("/api/test-generation/test-cases", {
      query: page,
    }),
  getTestCase: (testCaseId: string) =>
    request<TestCaseDetail>(`/api/test-generation/test-cases/${testCaseId}`),
  runTestCase: (testCaseId: string, targetBaseUrl?: string) =>
    request<TestRun>(`/api/execution/test-cases/${testCaseId}/run`, {
      method: "POST",
      body: JSON.stringify({
        ...(targetBaseUrl ? { target_base_url: targetBaseUrl } : {}),
        target_environment: "demo",
        timeout_seconds: 10,
      }),
    }),
  listRuns: (page: PageQuery) =>
    request<ListResponse<TestRun>>("/api/reports/test-runs", { query: page }),
  getRun: (runId: string) => request<TestRun>(`/api/reports/test-runs/${runId}`),
  clearDatabase: () => request<ClearDatabaseResponse>("/api/logs/database", { method: "DELETE" }),
};
