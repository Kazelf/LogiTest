---
phase: 4
title: "Expose run and report APIs"
status: pending
priority: P2
effort: "2h"
dependencies: [phase-02, phase-03]
---

# Phase 04: Expose Run And Report APIs

## Overview

Expose FastAPI endpoints to run a test case and inspect persisted test run reports.

## Requirements

- Functional: add run endpoint for a single test case.
- Functional: add paginated list of runs.
- Functional: add run detail endpoint.
- Functional: add list runs by test case endpoint.
- Non-functional: follow existing router error mapping patterns.

## Architecture

Router prefix:

```python
router = APIRouter(prefix="/api/execution", tags=["execution"])
```

Endpoints:

```text
POST /api/execution/test-cases/{test_case_id}/run
GET  /api/execution/runs
GET  /api/execution/runs/{run_id}
GET  /api/execution/test-cases/{test_case_id}/runs
```

Error mapping:

- Missing test case/run -> `404`.
- DB unavailable -> `503`.
- Malformed request -> FastAPI `422`.
- Execution target failure that is captured in a run -> `200` with run status `error`, not HTTP 500.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\execution\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\main.py`
- Extend: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\execution\service.py`
- Create tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_execution_api.py`

## Implementation Steps

1. Add router and include it in `app/main.py`.
2. Implement `POST /test-cases/{test_case_id}/run`.
3. Implement `list_test_runs(limit, offset, status, test_case_id?)` service helper.
4. Implement `get_test_run_detail(run_id)` service helper.
5. Implement route tests using monkeypatched service functions.
6. Validate pagination bounds match existing API conventions: `limit` 1-200, `offset >= 0`.

## Success Criteria

- [ ] Run endpoint returns persisted run summary.
- [ ] List endpoint returns paginated runs.
- [ ] Detail endpoint returns actual/diff JSON.
- [ ] Existing API tests keep passing.

## Risk Assessment

- Risk: report response too large. Mitigation: list response excludes full actual/diff; detail response includes them.
- Risk: route order conflict with `/test-cases/{id}/run` and `/runs/{id}`. Mitigation: distinct static prefixes under `/api/execution`.
