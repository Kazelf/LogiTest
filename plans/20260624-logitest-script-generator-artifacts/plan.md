---
title: "Task 5.4-5.5: Multi-framework script generator and test case artifact APIs"
description: "Generate Playwright, Jest/Supertest, and Mocha/Supertest scripts from API test case specs, persist artifacts, and expose them through test case APIs."
status: completed
priority: P2
effort: 8h
branch: master
tags: [feature, backend, api, database, test-generation]
blockedBy: [20260624-logitest-test-case-generation-backend]
blocks: []
created: 2026-06-24
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Design artifact schema and API contracts"
    status: completed
  - id: phase-02
    title: "Implement script renderers and file output"
    status: completed
  - id: phase-03
    title: "Persist artifacts and extend APIs"
    status: completed
  - id: phase-04
    title: "Verify tests and documentation"
    status: completed
---

# Task 5.4-5.5 Plan

## Overview

Extend the current test generation backend into a script generator. The system will render generated API test case JSON specs into automated test code for `playwright_api`, `jest_supertest`, and `mocha_supertest`, persist generated artifacts, optionally write files under `generated-tests/`, and expose artifacts through list/detail APIs.

## Confirmed Decisions

- Generate API-oriented scripts only. No Playwright UI test generation because current data source is backend logs, not UI actions/selectors.
- Support three framework modes: `playwright_api`, `jest_supertest`, `mocha_supertest`.
- Add `test_case_artifacts` table instead of overloading `test_cases.generated_code` with multiple scripts.
- Keep `test_cases.generated_code` for backward compatibility, storing the default or first generated artifact code.
- Detail API returns artifact metadata and code; list API remains compact.
- Optional file writing uses safe generated filenames under `logitest-ai/generated-tests/<framework>/`.
- Do not run generated scripts yet. Do not install Playwright/Jest/Mocha dependencies in this task.

## Codebase Context

- Backend root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`.
- Current module: `app/modules/test_generation/` already has schemas, service, router, and tests.
- Current endpoints: `POST /api/test-generation/generate`, `GET /api/test-generation/test-cases`, `GET /api/test-generation/test-cases/{test_case_id}`.
- Current DB table: `test_cases` has `steps`, `assertions`, `golden_response`, `generated_code`, but only one code slot.
- Existing DB style: raw SQL migration in `database/migrations/001_init_logitest_schema.sql`; direct `psycopg` in service layer.
- Existing test style: pytest with fake cursors/connections and API monkeypatching. No live DB required.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260624-logitest-test-case-generation-backend` | completed | Provides API test case JSON spec generation and current list/detail endpoints. |
| Builds on | `20260623-logitest-db-schema-mock-import` | in-progress | Provides base DB migration pattern and `test_cases` table. |
| Builds on | `20260624-logitest-behavior-analysis-journey-persona-api` | completed | Provides journey data used before test case generation. |

## Target API Shape

### Generate from journey and render artifacts

```http
POST /api/test-generation/generate
```

Request:

```json
{
  "journey_id": "uuid",
  "overwrite": true,
  "frameworks": ["playwright_api", "jest_supertest", "mocha_supertest"],
  "write_files": true
}
```

Response:

```json
{
  "test_case_id": "uuid",
  "journey_id": "uuid",
  "name": "API test - Successful buyer checkout",
  "status": "generated",
  "step_count": 6,
  "artifacts": [
    {
      "framework": "playwright_api",
      "language": "typescript",
      "file_path": "generated-tests/playwright/api-test-successful-buyer-checkout.spec.ts"
    }
  ]
}
```

### List and detail test cases

```http
GET /api/test-generation/test-cases
GET /api/test-generation/test-cases/{test_case_id}
GET /api/test-generation/test-cases/{test_case_id}/artifacts
GET /api/test-generation/test-cases/{test_case_id}/artifacts/{framework}
```

List remains compact. Detail returns `steps`, `assertions`, `golden_response`, current `generated_code`, and `artifacts`.

## Non-Goals

- No generated script execution.
- No install/config for Playwright, Jest, Mocha, Supertest, Chai.
- No UI Playwright tests.
- No frontend dashboard.
- No LLM code generation.
- No arbitrary output path supplied by API clients.

## Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Design artifact schema and API contracts](./phase-01-design-artifact-schema-and-api-contracts.md) | Completed |
| 2 | [Implement script renderers and file output](./phase-02-implement-script-renderers-and-file-output.md) | Completed |
| 3 | [Persist artifacts and extend APIs](./phase-03-persist-artifacts-and-extend-apis.md) | Completed |
| 4 | [Verify tests and documentation](./phase-04-verify-tests-and-documentation.md) | Completed |

## Acceptance Criteria

- Migration creates `test_case_artifacts` with `UNIQUE (test_case_id, framework)` and cascade delete.
- `POST /api/test-generation/generate` can render one or more requested frameworks.
- Supported frameworks: `playwright_api`, `jest_supertest`, `mocha_supertest`.
- Invalid framework returns `422` before persistence.
- Artifacts are upserted per `(test_case_id, framework)`.
- If `write_files=true`, generated files are written only under `logitest-ai/generated-tests/` with sanitized filenames.
- Detail API returns artifacts with code; list API remains lightweight.
- Existing Task 5.1-5.3 behavior stays backward compatible for callers that only send `journey_id` and `overwrite`.
- Backend tests pass without a live database.

## CLI Note

`npx claudekit plan create` was attempted, but the available CLI returned `unknown command 'plan'`. This plan was written manually using the repository's existing plan structure.

## Implementation Status

- Phase 1 completed: added `test_case_artifacts` migration and framework/artifact API schemas.
- Phase 2 completed: added deterministic renderers for `playwright_api`, `jest_supertest`, and `mocha_supertest`, plus safe file output under `generated-tests/`.
- Phase 3 completed: generation now persists artifacts, mirrors first artifact to `test_cases.generated_code`, and exposes artifact list/detail APIs.
- Phase 4 completed: added renderer/API/service tests and updated API/database docs.

## Verification

- `python -m py_compile app\modules\test_generation\schemas.py app\modules\test_generation\renderers.py app\modules\test_generation\service.py app\modules\test_generation\router.py app\main.py` passed from `apps/api`.
- `python -m pytest` passed from `apps/api`: 54 passed, 1 existing Starlette/httpx deprecation warning.
