---
title: "Task 4.4-4.7: Behavior analysis journeys personas API"
description: "Generate user journeys and simple personas from classified log sequences, add analyze behavior API, and list journeys/personas APIs."
status: completed
priority: P2
effort: 7h
branch: master
tags: [feature, backend, api, behavior-mining, journey, persona]
blockedBy: [20260623-logitest-db-schema-mock-import]
blocks: []
created: 2026-06-24
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Define behavior API contracts"
    status: completed
  - id: phase-02
    title: "Implement behavior mining services"
    status: completed
  - id: phase-03
    title: "Implement analyze behavior endpoint"
    status: completed
  - id: phase-04
    title: "Implement journey and persona list endpoints"
    status: completed
  - id: phase-05
    title: "Verify behavior API and documentation"
    status: completed
---

# Task 4.4-4.7 Plan

## Overview

Add MVP behavior mining APIs on top of the classified log data from Task 4.1-4.3. The system will derive user journeys from ordered session log sequences, derive simple personas with rules, persist results into existing `journeys` and `personas` tables, and expose APIs to analyze and list the results.

## Assumptions

- `POST /api/behavior/analyze` persists/upserts personas and journeys into PostgreSQL.
- `GET /api/behavior/journeys` and `GET /api/behavior/personas` return paginated list responses.
- Persona generation is rule-based for MVP:
  - Has `payment_success` -> `Buyer`.
  - Has `payment_failed` -> `Failed Payment User`.
  - Has product discovery actions without checkout/payment -> `Browser`.
  - Fallback -> `Unknown User`.
- No frontend, ML clustering, test case generation, auth, or raw payload-heavy response in this round.

## Requirements

- Task 4.4: generate user journeys from log sequences grouped by session and ordered by timestamp.
- Task 4.5: generate simple personas from session action sequences.
- Task 4.6: create an analyze behavior API that mines and persists behavior data from existing logs.
- Task 4.7: create list APIs for journeys and personas.
- Preserve current `/api/logs` contracts.
- Reuse the existing `behavior_mining` module and direct `psycopg` service pattern.

## Codebase Context

- Backend root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`.
- Current API entrypoint: `app/main.py` includes only the logs router.
- Existing DB connection pattern: `app/db/connection.py` and direct `psycopg` SQL with `dict_row`.
- Existing logs API pattern: `app/modules/ingestion/router.py`, `schemas.py`, `service.py`.
- Existing behavior module: `app/modules/behavior_mining/` currently has only `__init__.py`.
- Existing reconstruction service: `app/modules/session_reconstruction/service.py` provides action types, grouping, sorting, and classification utilities.
- Existing tables: `logs`, `sessions`, `personas`, `journeys` already exist in `database/migrations/001_init_logitest_schema.sql`.
- Import script currently seeds fixed personas/journeys; this task should mine from DB logs instead of hard-coding session-specific demo rows.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260623-logitest-db-schema-mock-import` | in-progress | Provides `logs`, `sessions`, `personas`, and `journeys` tables plus mock data semantics. |
| Builds on | `20260624-logitest-session-reconstruction-action-classifier` | completed | Reuses persisted `logs.action_type` and session reconstruction utilities. |
| Builds on | `20260624-logitest-session-group-detail-api` | completed | Reuses established API pagination/error patterns and session ordering semantics. |

## API Contract

### `POST /api/behavior/analyze`

Request body: none for MVP.

Response `200`:

```json
{
  "sessions_analyzed": 3,
  "personas_upserted": 3,
  "journeys_upserted": 3,
  "source": "logs",
  "method": "rule_based"
}
```

Failure behavior:

- Database unavailable: `503 {"detail":"Database is unavailable."}`.
- Unexpected mining error: `500 {"detail":"Behavior analysis failed."}`.

### `GET /api/behavior/journeys`

Query params: `limit` default 50 max 200, `offset` default 0, optional `persona_id`, optional `name` partial match.

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "persona_id": "uuid",
      "persona_name": "Buyer",
      "name": "Journey: login -> search_product -> view_product -> add_to_cart -> checkout -> payment_success -> view_order",
      "description": "Mined from 1 session(s).",
      "source_session_count": 1,
      "frequency_score": 0.3333,
      "risk_score": 0.62,
      "steps": [
        {"order": 1, "action_type": "login", "method": "POST", "endpoint": "/auth/login", "expected_status": 200}
      ],
      "example_session_id": "uuid",
      "created_at": "2026-06-24T00:00:00Z",
      "updated_at": "2026-06-24T00:00:00Z"
    }
  ],
  "limit": 50,
  "offset": 0,
  "total": 3
}
```

### `GET /api/behavior/personas`

Query params: `limit` default 50 max 200, `offset` default 0, optional `name` partial match.

Response `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Buyer",
      "description": "User completes checkout and successful payment.",
      "detection_method": "rule_based",
      "confidence_score": 0.95,
      "features": {"signals": ["checkout", "payment_success"]},
      "created_at": "2026-06-24T00:00:00Z",
      "updated_at": "2026-06-24T00:00:00Z"
    }
  ],
  "limit": 50,
  "offset": 0,
  "total": 3
}
```

## Behavior Mining Design

Read logs joined with sessions from DB ordered by session and `occurred_at ASC`:

```sql
SELECT
  logs.id,
  logs.session_id,
  sessions.external_session_id,
  logs.method,
  logs.endpoint,
  logs.status_code,
  logs.response_time_ms,
  logs.action_type,
  logs.occurred_at
FROM logs
LEFT JOIN sessions ON sessions.id = logs.session_id
ORDER BY sessions.external_session_id ASC NULLS LAST, logs.occurred_at ASC
```

For each session:

1. Sort logs chronologically.
2. Convert each log to a journey step with `order`, `action_type`, `method`, `endpoint`, `expected_status`, `response_time_ms`.
3. Build an action signature such as `login > search_product > view_product > add_to_cart > checkout > payment_success > view_order`.
4. Detect persona from the action set.
5. Group identical signatures to calculate `source_session_count` and `frequency_score`.
6. Upsert persona by `personas.name`.
7. Upsert journey by stable generated `journeys.name`.

Risk score MVP rules:

- `payment_failed` present: `0.90`.
- `checkout` or `payment_success` present: `0.62`.
- Otherwise: `0.25`.

## Non-Goals

- No frontend dashboard.
- No ML clustering/scikit-learn.
- No test case generation or mutation of `test_cases`.
- No auth/authorization.
- No new database tables.
- No schema migration unless implementation discovers an unavoidable index need.
- No endpoint to delete existing mined journeys/personas.
- No raw request payload/response body exposure in behavior list responses.

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Define behavior API contracts](./phase-01-define-behavior-api-contracts.md) | Completed |
| 2 | [Implement behavior mining services](./phase-02-implement-behavior-mining-services.md) | Completed |
| 3 | [Implement analyze behavior endpoint](./phase-03-implement-analyze-behavior-endpoint.md) | Completed |
| 4 | [Implement journey and persona list endpoints](./phase-04-implement-journey-and-persona-list-endpoints.md) | Completed |
| 5 | [Verify behavior API and documentation](./phase-05-verify-behavior-api-and-documentation.md) | Completed |

## Verification

- `python -m py_compile app\modules\behavior_mining\schemas.py app\modules\behavior_mining\service.py app\modules\behavior_mining\router.py app\main.py` passed from `apps/api`.
- `python -m pytest` passed from `apps/api`: 34 passed, 1 existing Starlette/httpx deprecation warning.

## Acceptance Criteria

- `POST /api/behavior/analyze` mines sessions from existing `logs` rows and persists personas/journeys.
- Analyze API returns counts for sessions analyzed, personas upserted, and journeys upserted.
- Persona generation follows the MVP rule set and stores results in `personas`.
- Journey generation stores ordered action steps in `journeys.steps` JSONB.
- Identical action sequences are grouped into a single journey with `source_session_count` and `frequency_score`.
- `GET /api/behavior/journeys` returns paginated journey list with persona name and steps.
- `GET /api/behavior/personas` returns paginated persona list.
- DB failures return `503` consistently with logs API patterns.
- Existing `/api/logs` tests remain unchanged and pass.
- New service and API tests run without a live database by monkeypatching service boundaries or fake DB cursors.

## Risks

- Existing import script already seeds personas/journeys with fixed rows, so analyze may upsert overlapping names. Mitigation: use stable names and `ON CONFLICT (name) DO UPDATE`, and document that analyze may refresh seeded data.
- `journeys.name` uniqueness forces one name per signature. Mitigation: derive deterministic names from action signatures and keep descriptions session-count based.
- Direct SQL can become bulky. Mitigation: isolate query builders and serializers inside `behavior_mining/service.py` instead of spreading SQL across router code.
- Ambiguous persona for mixed behavior. Mitigation: explicit precedence: payment failed > buyer > browser > unknown.

## Handoff

Recommended next command after review:

```powershell
/cook D:\ViettelDigitalTalent\LogiTest\plans\20260624-logitest-behavior-analysis-journey-persona-api\plan.md
```
