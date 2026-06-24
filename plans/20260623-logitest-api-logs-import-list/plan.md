---
title: "Task 3.1-3.2: Import mock logs API and list logs API"
description: "Add FastAPI endpoints to import existing mock logs into PostgreSQL and list normalized logs for MVP inspection."
status: completed
priority: P2
effort: 6h
branch: master
tags: [feature, backend, api, database]
blockedBy: [20260623-logitest-db-schema-mock-import]
blocks: []
created: 2026-06-23
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Create API database and router foundation"
    status: completed
  - id: phase-02
    title: "Implement mock log import endpoint"
    status: completed
  - id: phase-03
    title: "Implement list logs endpoint"
    status: completed
  - id: phase-04
    title: "Verify API behavior"
    status: completed
---

# Task 3.1-3.2 Plan

## Overview

Add two MVP backend APIs for LogiTest AI:

- Task 3.1: `POST /api/logs/import-mock` imports the existing mock log dataset into PostgreSQL.
- Task 3.2: `GET /api/logs` lists normalized logs with pagination and basic filters.

Keep implementation aligned with current codebase: FastAPI, direct `psycopg`, existing SQL schema, existing `scripts/import_mock_logs.py` import logic. No ORM migration yet.

## Codebase Context

- Project root: `D:\ViettelDigitalTalent\LogiTest`.
- Monorepo root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai`.
- Backend: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`.
- Current API entrypoint: `apps/api/app/main.py`, only `GET /health` exists.
- Database schema: `database/migrations/001_init_logitest_schema.sql` creates `sessions`, `logs`, `personas`, `journeys`, `test_cases`, `test_runs`.
- Mock data: `mock-data/logs.json`.
- Existing import script: `scripts/import_mock_logs.py`, already validates JSON and performs idempotent upserts.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260623-logitest-db-schema-mock-import` | in-progress | API depends on `logs`/`sessions` schema and mock import logic. |

Transitive dependency: `20260623-logitest-db-schema-mock-import` is blocked by `20260623-logitest-shared-docker-compose` for full DB verification. Unit/API tests can still be written without Docker by mocking database calls.

## Recommended Approach

Use a thin FastAPI module with direct `psycopg` access and reuse/tidy existing import script functions.

Why:

- KISS: repo already uses `psycopg`; avoid SQLAlchemy setup for two endpoints.
- DRY: import endpoint should reuse validation/upsert logic from `scripts/import_mock_logs.py` or move shared logic into an API-importable module.
- MVP-friendly: supports local demo quickly while keeping later ORM/Alembic migration possible.

Rejected now:

- SQLAlchemy repository layer: better later, unnecessary ceremony now.
- Shelling out to `python scripts/import_mock_logs.py` from API: brittle, hard to test, poor error handling.
- Upload-based arbitrary JSON import: useful later, larger validation/security surface now.

## API Contract

### `POST /api/logs/import-mock`

Request body: none.

Response `200`:

```json
{
  "source": "mock-data/logs.json",
  "loaded_records": 18,
  "sessions": 3,
  "counts": {
    "sessions": 3,
    "logs": 18,
    "personas": 3,
    "journeys": 3,
    "test_cases": 3
  }
}
```

Failure behavior:

- Invalid mock data: `500` with concise error message.
- Database unavailable: `503` with concise error message.
- No partial silent success; transaction commits only after full import flow succeeds.

### `GET /api/logs`

Query params:

- `limit`: integer, default `50`, min `1`, max `200`.
- `offset`: integer, default `0`, min `0`.
- `session_id`: optional external session id filter, e.g. `session-buyer-001`.
- `trace_id`: optional exact trace filter.
- `endpoint`: optional endpoint substring/exact strategy; pick substring `ILIKE` for MVP search.
- `level`: optional exact level filter.

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "external_log_id": "log-buyer-001-login",
      "session_external_id": "session-buyer-001",
      "trace_id": "trace-buyer-001-login",
      "user_id": "user-buyer-001",
      "service_name": "auth-service",
      "level": "info",
      "method": "POST",
      "endpoint": "/auth/login",
      "status_code": 200,
      "response_time_ms": 82,
      "occurred_at": "2026-06-23T09:00:00Z"
    }
  ],
  "limit": 50,
  "offset": 0,
  "total": 18
}
```

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Create API database and router foundation](./phase-01-create-api-database-and-router-foundation.md) | Completed |
| 2 | [Implement mock log import endpoint](./phase-02-implement-mock-log-import-endpoint.md) | Completed |
| 3 | [Implement list logs endpoint](./phase-03-implement-list-logs-endpoint.md) | Completed |
| 4 | [Verify API behavior](./phase-04-verify-api-behavior.md) | Completed |

## Acceptance Criteria

- `POST /api/logs/import-mock` imports existing mock logs idempotently.
- Repeated import calls do not duplicate `logs` or `sessions`.
- `GET /api/logs` returns paginated logs sorted by `occurred_at DESC`.
- Filters work for `session_id`, `trace_id`, `endpoint`, and `level`.
- Tests cover route registration, request validation, success response shape, DB failure handling, and SQL parameter safety.
- Implementation does not require Docker for unit tests; DB-backed smoke test can be documented separately.

## Non-Goals

- No arbitrary JSON upload endpoint.
- No Elasticsearch connector.
- No authentication/authorization layer yet.
- No frontend dashboard changes.
- No SQLAlchemy/Alembic migration in this task.
- No test generation/execution API changes.

## Risks

- DB daemon may not be running locally.
  Mitigation: unit tests mock DB boundary; document live verification command separately.
- Import logic duplication between script and API.
  Mitigation: extract shared import functions or import script module cleanly.
- Returning raw payloads may expose sensitive mock values.
  Mitigation: list endpoint returns normalized summary fields only for MVP.
- Dynamic filter SQL injection risk.
  Mitigation: build fixed whitelist conditions and pass values as psycopg parameters.

## Handoff

Recommended next command after review:

```powershell
/cook D:\ViettelDigitalTalent\LogiTest\plans\20260623-logitest-api-logs-import-list\plan.md
```
