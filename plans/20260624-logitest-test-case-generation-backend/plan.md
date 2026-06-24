---
title: "Task 5.1-5.3: API test case JSON generation backend"
description: "Add backend generation of API test case JSON specs from mined journeys and persist them into PostgreSQL test_cases."
status: completed
priority: P2
effort: 6h
branch: master
tags: [feature, backend, api, database, test-generation]
blockedBy: [20260623-logitest-db-schema-mock-import, 20260624-logitest-behavior-analysis-journey-persona-api]
blocks: []
created: 2026-06-24
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Define test case JSON contract"
    status: completed
  - id: phase-02
    title: "Implement generation service and persistence"
    status: completed
  - id: phase-03
    title: "Expose backend APIs"
    status: completed
  - id: phase-04
    title: "Verify tests and documentation"
    status: completed
---

# Task 5.1-5.3 Plan

## Overview

Implement backend support for generating API test case JSON specs from mined journeys, then save generated test cases into the existing `test_cases` table. This round stops at generate + persist; it does not execute tests, compare actual responses, or build UI.

## Confirmed Decisions

- Source data: use `journeys.example_session_id` to fetch ordered `logs` rows for request payloads and golden responses.
- Output format: store a stable JSON spec in `test_cases.steps`, `test_cases.assertions`, and `test_cases.golden_response`.
- Generated code: create only a lightweight pytest/httpx stub string in `test_cases.generated_code` for demo visibility.
- Persistence: reuse the existing `test_cases` table; avoid migration unless implementation finds a required missing column.
- API scope: backend only.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260623-logitest-db-schema-mock-import` | in-progress | Provides `test_cases`, `journeys`, `personas`, `sessions`, and `logs` schema. Live Docker DB verification may still be blocked by daemon availability. |
| Blocked by | `20260624-logitest-behavior-analysis-journey-persona-api` | completed | Provides mined journeys and `example_session_id` linkage used by the generator. |
| Builds on | `20260624-logitest-session-reconstruction-action-classifier` | completed | Reuses `logs.action_type` as part of generated steps. |

## Target API

```text
POST /api/test-generation/generate
GET  /api/test-generation/test-cases
GET  /api/test-generation/test-cases/{test_case_id}
```

`POST /generate` accepts `journey_id` and optional `overwrite`. It creates or refreshes one generated API test case.

## Non-Goals

- No test execution runner.
- No golden response comparison against staging/UAT.
- No frontend dashboard.
- No LLM generation.
- No schema migration unless unavoidable.
- No bulk-generate endpoint unless time remains after core flow.

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Define test case JSON contract](./phase-01-define-test-case-json-contract.md) | Completed |
| 2 | [Implement generation service and persistence](./phase-02-implement-generation-service-and-persistence.md) | Completed |
| 3 | [Expose backend APIs](./phase-03-expose-backend-apis.md) | Completed |
| 4 | [Verify tests and documentation](./phase-04-verify-tests-and-documentation.md) | Completed |

## Acceptance Criteria

- Given a journey with `example_session_id`, `POST /api/test-generation/generate` persists one `test_cases` row with `type='api'`, `status='generated'`, and `generated_by='test_generation_service'`.
- Generated steps include `order`, `action_type`, `service_name`, `method`, `endpoint`, `request_payload`, `expected_status`, `golden_response`, and `response_time_ms`.
- Generated assertions include status-code assertions for each step and schema assertions when response body is an object.
- `golden_response` stores final response summary, step count, and source journey/session IDs.
- Re-running with `overwrite=true` updates the same deterministic test case instead of duplicating rows.
- Database errors map to `503`; invalid or incomplete journey data maps to clear `404` or `422` API errors.
- Unit/API tests pass without requiring a live database.

## CLI Note

`npx claudekit plan create` was attempted, but the available CLI returned `unknown command 'plan'`. This plan was written manually using the repository's existing plan structure.

## Implementation Status

- Phase 1 completed: added Pydantic request/response/list/detail schemas for generated API test cases.
- Phase 2 completed: added deterministic generation service that builds steps, assertions, golden response summary, pytest stub, and persists to `test_cases`.
- Phase 3 completed: added `/api/test-generation/generate`, `/api/test-generation/test-cases`, and `/api/test-generation/test-cases/{test_case_id}` routes.
- Phase 4 completed: added service/API tests and README documentation.

## Verification

- `python -m py_compile app\modules\test_generation\schemas.py app\modules\test_generation\service.py app\modules\test_generation\router.py app\main.py` passed from `apps/api`.
- `python -m pytest` passed from `apps/api`: 46 passed, 1 existing Starlette/httpx deprecation warning.
