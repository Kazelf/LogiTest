ALTER TABLE logs
    ADD COLUMN IF NOT EXISTS request_id TEXT,
    ADD COLUMN IF NOT EXISTS request_headers JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS environment TEXT,
    ADD COLUMN IF NOT EXISTS normalized_endpoint TEXT,
    ADD COLUMN IF NOT EXISTS source_index TEXT,
    ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_logs_request_id ON logs(request_id);
CREATE INDEX IF NOT EXISTS idx_logs_source_index ON logs(source_index);
CREATE INDEX IF NOT EXISTS idx_logs_normalized_endpoint ON logs(normalized_endpoint);
