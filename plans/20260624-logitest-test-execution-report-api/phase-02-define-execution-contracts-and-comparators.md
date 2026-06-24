---
phase: 2
title: "Define execution contracts and comparators"
status: pending
priority: P2
effort: "2h"
dependencies: [phase-01]
---

# Phase 02: Define Execution Contracts And Comparators

## Overview

Define Pydantic schemas and pure comparison helpers for status code, schema keys, business data, and response time checks.

## Requirements

- Functional: define API request/response models for run and report endpoints.
- Functional: define pure comparator functions with deterministic output.
- Functional: aggregate per-step checks into a summary.
- Non-functional: comparators must be independently unit-testable without HTTP or DB.

## Architecture

Create execution module files:

```text
app/modules/execution/
  schemas.py
  comparators.py
```

Comparator output per step:

```json
{
  "order": 1,
  "endpoint": "/auth/login",
  "passed": true,
  "checks": {
    "status_code": {"passed": true, "expected": 200, "actual": 200},
    "schema": {"passed": true, "missing_keys": []},
    "business_data": {"passed": true, "differences": []},
    "response_time": {"passed": true, "expected_ms": 82, "actual_ms": 30, "threshold_ms": 282}
  }
}
```

Dynamic business fields to skip:

```text
id, token, timestamp, created_at, updated_at
```

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\execution\schemas.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\execution\comparators.py`
- Create tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_execution_comparators.py`

## Implementation Steps

1. Define `RunTestCaseRequest`, `RunTestCaseResponse`, `TestRunListResponse`, `TestRunDetailResponse`.
2. Implement `compare_status_code`.
3. Implement `compare_response_schema` using top-level keys from golden response.
4. Implement `compare_business_data` for stable scalar fields only.
5. Implement `compare_response_time` with threshold rule.
6. Implement `build_step_diff` and `summarize_diff_result`.
7. Unit test pass/fail cases for all comparators.

## Success Criteria

- [ ] Comparator tests cover status/schema/business/time pass and fail.
- [ ] Dynamic fields are skipped in business data comparison.
- [ ] Summary counts failed steps and failed check types.

## Risk Assessment

- Risk: schema comparison too shallow. Mitigation: acceptable MVP; document deeper JSON Schema validation as future work.
- Risk: business data comparison false positives on dynamic fields. Mitigation: conservative skip list for dynamic keys.
