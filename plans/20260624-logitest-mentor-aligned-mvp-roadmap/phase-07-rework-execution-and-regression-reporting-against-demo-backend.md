---
phase: 7
title: "Rework execution and regression reporting against the demo backend"
status: pending
priority: P1
effort: "1d"
dependencies: ["phase-06"]
---

# Phase 07: Rework Execution And Regression Reporting Against The Demo Backend

## Overview

Implement execution/reporting in a way that supports the real demo backend rather than only mock staging routes inside FastAPI.

## Requirements

- Functional: Run generated test specs or equivalent persisted JSON steps against `STAGING_API_BASE_URL`.
- Functional: Store run status, duration, actual responses, comparison result, and errors in `test_runs`.
- Functional: Compare status code, response schema, stable business fields, and response time.
- Functional: Demonstrate regression by toggling demo backend behavior.
- Non-functional: Execution should be synchronous for MVP unless it proves too slow.

## Architecture

Two execution options:

1. Preferred MVP: execute persisted JSON steps with `httpx`, then keep generated Jest as visible artifact.
2. Optional later: invoke Jest runner for generated files.

The preferred route is less flashy but more reliable and already matches existing FastAPI test infrastructure.

## Related Code Files

- Modify/Create: `logitest-ai/apps/api/app/modules/execution/schemas.py`
- Modify/Create: `logitest-ai/apps/api/app/modules/execution/service.py`
- Modify/Create: `logitest-ai/apps/api/app/modules/execution/router.py`
- Modify/Create: `logitest-ai/apps/api/app/modules/reports/schemas.py`
- Modify/Create: `logitest-ai/apps/api/app/modules/reports/service.py`
- Modify/Create: `logitest-ai/apps/api/app/modules/reports/router.py`
- Modify: `logitest-ai/apps/api/app/main.py`
- Modify: `plans/20260624-logitest-test-execution-report-api/*` if that plan is executed instead of this phase.

## Implementation Steps

1. Reconcile the existing execution/report plan with this roadmap.
2. Add request/response schemas for run and report APIs.
3. Load `test_cases.steps` and replay them against target base URL.
4. Apply variable interpolation from chaining metadata.
5. Compare actual results against golden response rules.
6. Persist `test_runs`.
7. Add APIs for run list/detail and test-case run history.
8. Add tests using mocked HTTP client and fake DB cursor.

## Success Criteria

- [ ] `POST /api/execution/test-cases/{id}/run` can target the demo backend URL.
- [ ] Passing demo backend behavior stores `status='passed'`.
- [ ] Regression mode stores `status='failed'` with useful diff details.
- [ ] Report APIs return persisted `actual_response` and `diff_result`.
- [ ] Tests do not require live network or live database.

## Risk Assessment

Executing generated Jest directly adds process management and Node tooling complexity. Keep JSON-step execution as the MVP truth, and treat generated Jest files as exportable artifacts unless direct Jest execution becomes required.

