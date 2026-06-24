---
title: "Task 3.3-3.4: Group logs by session and session detail API"
description: "Add FastAPI endpoints to list log sessions with grouped summaries and fetch one session with ordered log details."
status: completed
priority: P2
effort: 5h
branch: master
tags: [feature, backend, api, database]
blockedBy: [20260623-logitest-db-schema-mock-import]
blocks: []
created: 2026-06-24
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Define session API contracts"
    status: completed
  - id: phase-02
    title: "Implement grouped sessions endpoint"
    status: completed
  - id: phase-03
    title: "Implement session detail endpoint"
    status: completed
  - id: phase-04
    title: "Verify tests and documentation"
    status: completed
---

# Task 3.3-3.4 Plan

## Overview

Add two backend APIs on top of the existing `/api/logs` FastAPI router:

- Task 3.3: `GET /api/logs/sessions` groups logs by session and returns session summaries.
- Task 3.4: `GET /api/logs/sessions/{external_session_id}` returns one session plus its ordered logs.

Use the existing `psycopg` direct-SQL pattern from Task 3.1/3.2. Do not add SQLAlchemy, new DB tables, or frontend work.

## Codebase Context

- Backend: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`.
- Existing router: `app/modules/ingestion/router.py`, prefix `/api/logs`.
- Existing service: `app/modules/ingestion/service.py`, direct `psycopg` queries with parameter binding.
- Existing schemas: `app/modules/ingestion/schemas.py`, Pydantic response models.
- Existing tests: `apps/api/tests/test_logs_api.py`, FastAPI `TestClient` with monkeypatched service functions.
- DB schema: `sessions` and `logs`, with indexes on `logs(session_id, occurred_at)`, `sessions.external_session_id`, and `logs.occurred_at`.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260623-logitest-db-schema-mock-import` | in-progress | Provides `sessions`/`logs` schema and imported mock data semantics. |
| Builds on | `20260623-logitest-api-logs-import-list` | completed | Reuses existing `/api/logs` router, service, schemas, tests, and DB error handling pattern. |

## API Contract

### `GET /api/logs/sessions`

Query params: `limit` default 50 max 200, `offset` default 0, optional exact `user_id`, optional exact `source`.

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "external_session_id": "session-buyer-001",
      "user_id": "user-buyer-001",
      "started_at": "2026-06-23T09:00:00Z",
      "ended_at": "2026-06-23T09:01:20Z",
      "request_count": 7,
      "log_count": 7,
      "source": "mock_json",
      "services": ["auth-service", "order-service", "product-service"],
      "created_at": "2026-06-23T09:02:00Z"
    }
  ],
  "limit": 50,
  "offset": 0,
  "total": 3
}
```

Sort newest sessions first by `started_at DESC NULLS LAST`, then `created_at DESC`.

### `GET /api/logs/sessions/{external_session_id}`

Response `200`:

```json
{
  "session": {
    "id": "uuid",
    "external_session_id": "session-buyer-001",
    "user_id": "user-buyer-001",
    "started_at": "2026-06-23T09:00:00Z",
    "ended_at": "2026-06-23T09:01:20Z",
    "request_count": 7,
    "log_count": 7,
    "source": "mock_json",
    "metadata": {"source_file": "mock-data/logs.json"},
    "created_at": "2026-06-23T09:02:00Z"
  },
  "logs": [
    {
      "id": "uuid",
      "external_log_id": "log-buyer-001-login",
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
  ]
}
```

Failure behavior:

- Unknown `external_session_id`: `404 {"detail":"Session not found."}`.
- Database unavailable: `503 {"detail":"Database is unavailable."}`.

## Recommended Approach

Keep both APIs in the existing ingestion router under `/api/logs/sessions`.

Why:

- KISS: existing logs router already owns import/list log behavior.
- DRY: reuse `LogListItem`-like summary fields for session detail logs.
- Low blast radius: no schema migration, no frontend, no ORM.

Rejected for this task:

- New `/api/sessions` router: cleaner later, but premature while `session_reconstruction` module is empty.
- `GET /api/logs?group_by=session`: response shape changes by query param and becomes awkward for clients/tests.
- Returning full request/response/raw JSON in session detail: useful for deep debugging, but unnecessary and more sensitive for MVP.

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Define session API contracts](./phase-01-define-session-api-contracts.md) | Completed |
| 2 | [Implement grouped sessions endpoint](./phase-02-implement-grouped-sessions-endpoint.md) | Completed |
| 3 | [Implement session detail endpoint](./phase-03-implement-session-detail-endpoint.md) | Completed |
| 4 | [Verify tests and documentation](./phase-04-verify-tests-and-documentation.md) | Completed |

## Acceptance Criteria

- `GET /api/logs/sessions` returns session summaries with `log_count`, `services`, pagination, and `total`.
- `GET /api/logs/sessions` supports `user_id` and `source` exact filters.
- `GET /api/logs/sessions/{external_session_id}` returns session metadata plus logs ordered by `occurred_at ASC`.
- Missing session returns `404`.
- DB connection failures return `503`, matching existing logs API behavior.
- Tests cover success, validation bounds, 404, 503, and parameterized filter behavior.
- Unit/API tests pass without Docker.

## Non-Goals

- No frontend dashboard.
- No auth/authorization.
- No database migration.
- No session mining/reconstruction algorithm.
- No raw payload/body exposure in session detail.
- No cursor pagination yet.

## Risks

- Current DB verification plan is still marked in-progress because Docker daemon may be unavailable. Mitigation: make tests mock service boundary; document optional live smoke commands.
- `services` aggregation can return null if a session has no logs. Mitigation: coalesce to empty list in SQL or service serialization.
- Session detail path may conflict with `/api/logs` list route only if route order is careless. Mitigation: use explicit `/sessions` and `/sessions/{external_session_id}` paths.

## Handoff

Recommended next command after review:

```powershell
/cook D:\ViettelDigitalTalent\LogiTest\plans\20260624-logitest-session-group-detail-api\plan.md
```

