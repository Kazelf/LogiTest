---
title: "Task 4.1-4.3: Session reconstruction services and persisted action classifier"
description: "Add backend services to group logs by session, sort logs chronologically, classify action types with rules, and persist action_type on logs."
status: pending
priority: P2
effort: 6h
branch: master
tags: [feature, backend, database, session-reconstruction, classifier]
blockedBy: [20260623-logitest-db-schema-mock-import]
blocks: []
created: 2026-06-24
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Add action_type database field"
    status: pending
  - id: phase-02
    title: "Implement session reconstruction domain services"
    status: pending
  - id: phase-03
    title: "Persist classified actions during import"
    status: pending
  - id: phase-04
    title: "Verify classifier and reconstruction behavior"
    status: pending
---

# Task 4.1-4.3 Plan

## Overview

Implement backend-only support for session reconstruction and rule-based action classification. This task does not expose `action_type` in API responses yet; API response changes are reserved for later tasks.

## Requirements

- Task 4.1: provide a service that groups logs by session identifier.
- Task 4.2: provide a service that sorts logs by timestamp chronologically.
- Task 4.3: provide a rule-based classifier that recognizes action type from API log fields.
- Persist the classifier result in PostgreSQL on `logs.action_type`.
- Logs without a session identifier must be grouped into the `"unknown"` bucket.
- Keep current FastAPI response contracts stable.

## Codebase Context

- Project root: `D:\ViettelDigitalTalent\LogiTest`.
- Monorepo root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai`.
- Backend: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`.
- Existing ingestion service: `app/modules/ingestion/service.py` uses direct `psycopg` SQL.
- Empty target module exists: `app/modules/session_reconstruction/`.
- Mock import script: `scripts/import_mock_logs.py` already has `group_by_session`, `parse_timestamp`, and `upsert_logs`.
- DB schema: `database/migrations/001_init_logitest_schema.sql` creates `sessions` and `logs`.
- Current API tests: `apps/api/tests/test_logs_api.py` use FastAPI `TestClient` and monkeypatch service boundaries.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260623-logitest-db-schema-mock-import` | in-progress | Provides the existing `logs` table, mock dataset, and import script this plan extends. |
| Builds on | `20260624-logitest-session-group-detail-api` | completed | Keeps current session list/detail APIs stable while adding lower-level reconstruction services. |

## Final Design

Add `logs.action_type` as `TEXT NOT NULL DEFAULT 'unknown'` with an index. Do not use a PostgreSQL enum yet because classifier labels are likely to evolve during MVP iteration.

Create a small domain service in `app/modules/session_reconstruction/service.py` with pure functions:

```python
group_logs_by_session(logs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]
sort_logs_by_timestamp(logs: list[dict[str, Any]], *, ascending: bool = True) -> list[dict[str, Any]]
classify_action(log: dict[str, Any]) -> ActionClassification
classify_logs(logs: list[dict[str, Any]]) -> list[dict[str, Any]]
```

Recommended classifier result shape:

```python
@dataclass(frozen=True)
class ActionClassification:
    action_type: str
    confidence: float
    signals: tuple[str, ...]
```

Only `action_type` is persisted in this task. `confidence` and `signals` stay internal until a later API or auditability task needs them.

## Action Type Rules

| Action type | Initial rule |
|---|---|
| `login` | `POST /auth/login` with 2xx status |
| `search_product` | `GET /products` with a query string containing `query=` |
| `view_product` | `GET /products/{id}` without search query |
| `add_to_cart` | `POST /cart/items` with 2xx/201 status |
| `checkout` | `POST /orders` with 2xx/201 status |
| `payment_success` | `POST /payments` with 2xx status and response body status `paid` |
| `payment_failed` | `POST /payments` with 4xx status or response body status `declined` |
| `view_order` | `GET /orders/{id}` |
| `unknown` | Fallback for unmatched or malformed logs |

## Non-Goals

- No API response changes.
- No frontend changes.
- No ML classifier.
- No PostgreSQL enum for action types.
- No backfill endpoint.
- No Alembic adoption.
- No auth/authorization changes.

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Add action_type database field](./phase-01-add-action-type-database-field.md) | Pending |
| 2 | [Implement session reconstruction domain services](./phase-02-implement-session-reconstruction-domain-services.md) | Pending |
| 3 | [Persist classified actions during import](./phase-03-persist-classified-actions-during-import.md) | Pending |
| 4 | [Verify classifier and reconstruction behavior](./phase-04-verify-classifier-and-reconstruction-behavior.md) | Pending |

## Acceptance Criteria

- `logs` table has `action_type TEXT NOT NULL DEFAULT 'unknown'`.
- `logs.action_type` has an index for future filtering/reporting.
- Grouping service buckets missing session IDs under `"unknown"`.
- Sorting service handles raw `timestamp` and DB/API-style `occurred_at` fields.
- Sorting puts invalid or missing timestamps last.
- Classifier recognizes the ecommerce mock flow action types listed above.
- Import script and API import path persist `action_type` when inserting/upserting logs.
- Existing FastAPI response contracts remain unchanged.
- Unit tests cover grouping, sorting, classifier rules, and import integration at service/script boundary.
- Backend tests pass without requiring a running Docker database.

## Risks

- Existing plan `20260623-logitest-db-schema-mock-import` is still marked in-progress due to DB verification. Mitigation: make this plan blocked by it and keep most tests pure/unit-level.
- Updating the initial migration can be awkward if a local database is already created. Mitigation: document that MVP local DB may need migration re-run or manual `ALTER TABLE` until formal migration tooling exists.
- Duplicating helpers between script and API service could drift. Mitigation: put classifier/group/sort logic in backend module and import it from the script where practical.
- Rule order matters, especially `/products?query=` versus `/products/{id}`. Mitigation: test specific rules before generic path rules.

## Handoff

Recommended next command after review:

```powershell
/cook D:\ViettelDigitalTalent\LogiTest\plans\20260624-logitest-session-reconstruction-action-classifier\plan.md
```
