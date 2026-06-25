---
phase: 4
title: "Import Elasticsearch logs into FastAPI platform"
status: completed
priority: P1
effort: "1d"
dependencies: ["phase-03"]
---

# Phase 04: Import Elasticsearch Logs Into FastAPI Platform

## Overview

Extend the existing FastAPI ingestion module from mock-only import to Elasticsearch import, normalization, masking, and PostgreSQL persistence.

## Requirements

- Functional: Add API to import logs from Elasticsearch by index and optional time range.
- Functional: Normalize demo backend logs into existing `logs` and `sessions` tables.
- Functional: Preserve `POST /api/logs/import-mock`.
- Functional: Add missing schema fields only through a new migration.
- Non-functional: Unit tests should not require a live Elasticsearch instance.

## Architecture

Add a small connector boundary:

```text
ingestion/router.py
  -> ingestion/service.py
  -> elasticsearch_client.py
  -> normalize/mask/upsert
```

The platform should still use direct `psycopg` like existing modules.

## Related Code Files

- Modify: `logitest-ai/apps/api/app/modules/ingestion/router.py`
- Modify: `logitest-ai/apps/api/app/modules/ingestion/service.py`
- Modify: `logitest-ai/apps/api/app/modules/ingestion/schemas.py`
- Create: `logitest-ai/apps/api/app/modules/ingestion/elasticsearch_client.py`
- Create: `logitest-ai/database/migrations/002_add_elasticsearch_log_fields.sql`
- Modify: `logitest-ai/apps/api/app/core/settings.py`
- Modify: `logitest-ai/docker-compose.yml`
- Modify: `logitest-ai/apps/api/tests/test_logs_api.py`
- Create: `logitest-ai/apps/api/tests/test_elasticsearch_client.py`
- Create: `logitest-ai/apps/api/tests/test_elasticsearch_ingestion_service.py`

## Implementation Steps

1. Add `elasticsearch` Python client dependency or use `httpx` for minimal REST queries.
2. Add request/response schemas for Elasticsearch import.
3. Add migration for `request_id`, `request_headers`, `environment`, `normalized_endpoint`, `source_index`, `ingested_at` if needed.
4. Implement sensitive-field masking shared by mock and ES import paths.
5. Implement normalizer from ES `_source` to DB fields.
6. Upsert sessions and logs idempotently using `external_log_id` or deterministic hash fallback.
7. Add API tests with mocked ES client responses.

## Success Criteria

- [x] `POST /api/logs/import-elasticsearch` returns imported counts.
- [x] Imported logs are persisted through the same `logs` table used by `GET /api/logs`.
- [x] Existing mock import tests still pass.
- [x] No sensitive value is stored unmasked from ES import.
- [x] Import can filter by index and time range.

## Validation Notes

- `python -m pytest` from `logitest-ai/apps/api` passed with 65/65 tests.
- `npm.cmd run test:demo` from `logitest-ai` passed with 6/6 tests.
- `docker compose config` passed.
- `docker compose up --build -d database elasticsearch api demo-backend` could not be verified because Docker Desktop daemon was unavailable: `dockerDesktopLinuxEngine` pipe not found.

## Risk Assessment

Main risk: schema drift between demo logs and mock logs. Mitigate with a single normalization function and tests for both source types.
