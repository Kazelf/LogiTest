---
phase: 1
title: "Define test case JSON contract"
status: completed
priority: P2
effort: "1h"
dependencies: []
---

# Phase 01: Define Test Case JSON Contract

## Overview

Define the backend request/response schemas and the persisted JSON shape for generated API test cases. This phase makes the format explicit before persistence logic is added.

## Requirements

- Functional: define Pydantic models for generate request, generate response, list item, detail response, step spec, assertion spec, and golden response summary.
- Functional: validate `journey_id` as a string UUID-like value at API boundary where practical.
- Non-functional: keep format deterministic and runner-friendly; no LLM-shaped free text blobs in core fields.

## Architecture

Create `app/modules/test_generation/schemas.py` with Pydantic models that mirror existing module style:

```json
{
  "steps": [
    {
      "order": 1,
      "action_type": "login",
      "service_name": "auth-service",
      "method": "POST",
      "endpoint": "/auth/login",
      "request_payload": {},
      "expected_status": 200,
      "golden_response": {},
      "response_time_ms": 80
    }
  ],
  "assertions": [
    {"order": 1, "type": "status_code", "expected": 200},
    {"order": 1, "type": "response_schema", "expected": {"type": "object", "required": []}}
  ],
  "golden_response": {
    "step_count": 1,
    "final_status_code": 200,
    "final_response_body": {},
    "source": {"journey_id": "uuid", "example_session_id": "uuid"}
  }
}
```

The DB already stores these as separate `JSONB` columns: `steps`, `assertions`, and `golden_response`.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\schemas.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\__init__.py` only if exports are useful.
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\schemas.py`

## Implementation Steps

1. Define `GenerateTestCaseRequest` with `journey_id: str` and `overwrite: bool = True`.
2. Define `GenerateTestCaseResponse` with `test_case_id`, `journey_id`, `name`, `status`, and `step_count`.
3. Define `TestCaseListItem` and `TestCaseDetailResponse` for read APIs.
4. Use `Field(ge/le)` constraints for pagination models if list endpoint uses `limit` and `offset` params.
5. Keep schemas tolerant of JSON dictionaries by using `dict[str, Any]` and `list[dict[str, Any]]` where DB JSONB is returned.

## Success Criteria

- [x] Schema module imports cleanly.
- [x] Models cover POST response and read APIs.
- [x] JSON format contains all fields agreed in brainstorming.
- [x] No DB/service code is mixed into schemas.

## Risk Assessment

- Risk: schema becomes too specific and blocks future runner needs. Mitigation: keep JSONB payload fields flexible while naming core keys consistently.
- Risk: duplicate schema definitions across modules. Mitigation: reuse simple Pydantic patterns from `behavior_mining` and do not introduce shared abstractions yet.
