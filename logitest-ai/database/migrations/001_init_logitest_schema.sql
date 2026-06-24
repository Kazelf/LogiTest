CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    CREATE TYPE test_case_type AS ENUM ('api', 'e2e');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE test_case_status AS ENUM ('draft', 'generated', 'approved', 'deprecated');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE test_run_status AS ENUM ('queued', 'running', 'passed', 'failed', 'error', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_session_id TEXT NOT NULL UNIQUE,
    user_id TEXT,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    request_count INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'mock_json',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    external_log_id TEXT UNIQUE,
    trace_id TEXT,
    user_id TEXT,
    service_name TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'info',
    method TEXT,
    endpoint TEXT,
    status_code INTEGER,
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_body JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_time_ms INTEGER,
    action_type TEXT NOT NULL DEFAULT 'unknown',
    raw_log JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    detection_method TEXT NOT NULL DEFAULT 'rule_based',
    confidence_score NUMERIC(5,4),
    features JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    source_session_count INTEGER NOT NULL DEFAULT 0,
    frequency_score NUMERIC(8,4),
    risk_score NUMERIC(8,4),
    steps JSONB NOT NULL,
    example_session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID REFERENCES journeys(id) ON DELETE SET NULL,
    persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    type test_case_type NOT NULL DEFAULT 'api',
    status test_case_status NOT NULL DEFAULT 'draft',
    steps JSONB NOT NULL,
    assertions JSONB NOT NULL DEFAULT '[]'::jsonb,
    golden_response JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_code TEXT,
    generated_by TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_case_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    framework TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'typescript',
    file_path TEXT,
    code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (test_case_id, framework)
);

CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    status test_run_status NOT NULL DEFAULT 'queued',
    target_environment TEXT NOT NULL DEFAULT 'staging',
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    duration_ms INTEGER,
    actual_response JSONB NOT NULL DEFAULT '{}'::jsonb,
    diff_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    runner_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_logs_session_occurred_at ON logs(session_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_logs_trace_id ON logs(trace_id);
CREATE INDEX IF NOT EXISTS idx_logs_endpoint ON logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_logs_occurred_at ON logs(occurred_at);
CREATE INDEX IF NOT EXISTS idx_logs_action_type ON logs(action_type);
CREATE INDEX IF NOT EXISTS idx_logs_raw_log_gin ON logs USING GIN(raw_log);
CREATE INDEX IF NOT EXISTS idx_sessions_external_session_id ON sessions(external_session_id);
CREATE INDEX IF NOT EXISTS idx_journeys_persona_id ON journeys(persona_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_journey_id ON test_cases(journey_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_status ON test_cases(status);
CREATE INDEX IF NOT EXISTS idx_test_case_artifacts_test_case_id ON test_case_artifacts(test_case_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_test_case_id ON test_runs(test_case_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_status_created_at ON test_runs(status, created_at);
