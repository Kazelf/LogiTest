---
phase: 3
title: "Implement sequential executor and persistence"
status: pending
priority: P2
effort: "3h"
dependencies: [phase-01, phase-02]
---

# Phase 03: Implement Sequential Executor And Persistence

## Overview

Implement the service that loads a test case, calls each step sequentially, compares actual responses, and persists a `test_runs` result.

## Requirements

- Functional: load `test_cases` row by ID.
- Functional: execute steps in order using `httpx`.
- Functional: measure response time for each step.
- Functional: persist `actual_response`, `diff_result`, `duration_ms`, and run `status`.
- Functional: handle malformed test cases and target failures as `error` runs.
- Non-functional: service tests should not require a live DB or external server.

## Architecture

Execution flow:

```text
run_test_case(test_case_id, target_environment, target_base_url)
-> fetch test case spec
-> started_at = now
-> for step in sorted steps:
     call target endpoint
     record status/body/time
     compare status/schema/business/time
-> summarize diff
-> status = passed|failed|error
-> insert test_runs row
-> return run summary
```

Use `httpx.Client` for real calls. Tests can inject/monkeypatch an HTTP client or step caller helper.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\execution\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\core\settings.py` if adding default target base URL.
- Create tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_execution_service.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\database\migrations\001_init_logitest_schema.sql`

## Implementation Steps

1. Add domain errors: `TestCaseNotFoundError`, `TestCaseExecutionError`, `TestRunNotFoundError` if useful.
2. Implement `_fetch_test_case_for_execution` selecting `id`, `name`, `steps`, `assertions`, `golden_response`.
3. Implement `_call_step(client, base_url, step)`.
4. Implement `_build_actual_response` and per-step diff generation.
5. Implement `_insert_test_run` using existing `test_runs` columns.
6. Ensure exceptions still persist an `error` run when a `test_case_id` exists and execution begins.
7. Add service tests with fake cursor and fake step caller.

## Success Criteria

- [ ] Steps execute in order.
- [ ] Passed diff creates `test_runs.status='passed'`.
- [ ] Failed comparison creates `test_runs.status='failed'`.
- [ ] Target/executor error creates `test_runs.status='error'` with `error_message`.
- [ ] Insert SQL uses `Jsonb` for actual/diff/metadata.

## Risk Assessment

- Risk: synchronous API call blocks too long. Mitigation: MVP only; add per-step timeout and keep mock target local.
- Risk: self-calling same FastAPI server can deadlock under single-worker dev server. Mitigation: tests monkeypatch caller; live smoke uses Uvicorn capable of concurrent requests, or target base can be external later.
