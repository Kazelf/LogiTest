---
title: "Task 6.1-6.8: Test execution runner and report APIs"
description: "Add mock staging APIs, execute generated test case JSON specs step by step, compare actual responses, persist test runs, and expose run/report APIs."
status: pending
priority: P2
effort: 10h
branch: master
tags: [feature, backend, api, database, execution, reports]
blockedBy: [20260624-logitest-mentor-aligned-mvp-roadmap, 20260624-logitest-test-case-generation-backend, 20260624-logitest-script-generator-artifacts]
blocks: []
created: 2026-06-24
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Create mock staging API"
    status: pending
  - id: phase-02
    title: "Define execution contracts and comparators"
    status: pending
  - id: phase-03
    title: "Implement sequential executor and persistence"
    status: pending
  - id: phase-04
    title: "Expose run and report APIs"
    status: pending
  - id: phase-05
    title: "Verify tests and documentation"
    status: pending
---

# Task 6.1-6.8 Plan

## Overview

Implement MVP test execution for generated API test case JSON specs. The executor will call each step against a mock staging API, compare response code/schema/business data/response time, store a `test_runs` row, and expose APIs to run test cases and inspect reports.

## Confirmed Decisions

- Execute JSON specs from `test_cases.steps`, not generated Playwright/Jest/Mocha files.
- Add mock staging routes inside the existing FastAPI app under `/mock-staging` for MVP simplicity.
- Run synchronously in the request/response cycle. No queue/background worker yet.
- Use `httpx` for HTTP calls.
- Use existing `test_runs` table. No migration needed unless implementation finds unavoidable gaps.
- Store detailed actual responses in `test_runs.actual_response` and comparison report in `test_runs.diff_result`.
- Keep generated script artifacts as export/demo artifacts only.

## Codebase Context

- Backend root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`.
- Existing placeholder modules: `app/modules/execution/__init__.py` and `app/modules/reports/__init__.py`.
- Existing API pattern: module-level `schemas.py`, `service.py`, `router.py`; direct `psycopg`; tests monkeypatch service/fake cursors.
- Existing DB table: `test_runs` already has `actual_response`, `diff_result`, `error_message`, and `runner_metadata` JSONB fields.
- Current test case input: `test_cases.steps`, `test_cases.assertions`, `test_cases.golden_response` from Task 5.
- Current generated scripts: `test_case_artifacts`; out of scope for execution in this task.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260624-logitest-mentor-aligned-mvp-roadmap` | pending | Mentor-aligned roadmap changes the execution target from FastAPI mock staging routes toward the real Express demo backend. Reconcile Phase 1-4 before implementation. |
| Blocked by | `20260624-logitest-test-case-generation-backend` | completed | Provides generated `test_cases` JSON specs and list/detail APIs. |
| Blocked by | `20260624-logitest-script-generator-artifacts` | completed | Clarifies generated scripts are artifacts only, not executor input. |
| Builds on | `20260623-logitest-db-schema-mock-import` | in-progress | Provides `test_runs` schema; live DB verification may depend on Docker availability. |

## Target API Shape

### Run one test case

```http
POST /api/execution/test-cases/{test_case_id}/run
```

Request:

```json
{
  "target_environment": "mock_staging",
  "target_base_url": "http://localhost:8000/mock-staging"
}
```

Response:

```json
{
  "id": "uuid",
  "test_case_id": "uuid",
  "status": "passed",
  "target_environment": "mock_staging",
  "duration_ms": 120,
  "summary": {
    "total_steps": 6,
    "failed_steps": 0
  }
}
```

### Report APIs

```http
GET /api/execution/runs
GET /api/execution/runs/{run_id}
GET /api/execution/test-cases/{test_case_id}/runs
```

Detail returns persisted `actual_response`, `diff_result`, and metadata.

## Comparator Rules

- Response code: `actual_status == expected_status`.
- Response schema: actual JSON object must contain top-level keys from expected/golden response.
- Business data: exact-match stable scalar fields; skip dynamic keys containing `id`, `token`, `timestamp`, `created_at`, `updated_at`.
- Response time: `actual_ms <= max(expected_ms * 2, expected_ms + 200)` when expected time exists.

## Non-Goals

- No execution of generated Playwright/Jest/Mocha files.
- No async queue/background jobs.
- No retries.
- No auth/authorization.
- No frontend report UI.
- No deep JSON Schema library.
- No external target-system microservices in this round.

## Reconciliation Note

This plan was written before the mentor-aligned scope update. If implemented after `20260624-logitest-mentor-aligned-mvp-roadmap`, replace the FastAPI-only mock staging assumption with the Express demo backend target from that roadmap. Keep JSON-step execution if it remains the most reliable MVP path, but use `STAGING_API_BASE_URL` / `DEMO_BACKEND_URL` instead of hard-coding `/mock-staging` as the main target.

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Create mock staging API](./phase-01-create-mock-staging-api.md) | Pending |
| 2 | [Define execution contracts and comparators](./phase-02-define-execution-contracts-and-comparators.md) | Pending |
| 3 | [Implement sequential executor and persistence](./phase-03-implement-sequential-executor-and-persistence.md) | Pending |
| 4 | [Expose run and report APIs](./phase-04-expose-run-and-report-apis.md) | Pending |
| 5 | [Verify tests and documentation](./phase-05-verify-tests-and-documentation.md) | Pending |

## Acceptance Criteria

- Mock staging API exposes enough endpoints to replay current generated e-commerce-like test cases.
- `POST /api/execution/test-cases/{test_case_id}/run` loads a test case and executes steps in order.
- Executor records actual status/body/response time per step.
- Comparator produces pass/fail results for response code, schema, business data, and response time.
- A `test_runs` row is inserted for each run.
- Run status is `passed`, `failed`, or `error` according to comparison/execution outcome.
- Report APIs return list/detail run data from `test_runs`.
- Existing Task 5 APIs continue passing.
- Tests pass without a live database by using fake cursors or monkeypatching service boundaries.

## CLI Note

`npx claudekit plan create` was attempted, but the available CLI returned `unknown command 'plan'`. This plan was written manually using the repository's existing plan structure.
