---
phase: 3
title: "Expose backend APIs"
status: completed
priority: P2
effort: "1.25h"
dependencies: [phase-01, phase-02]
---

# Phase 03: Expose Backend APIs

## Overview

Add a FastAPI router for test generation. The API should expose generation and read endpoints using the same error handling style as existing logs and behavior routes.

## Requirements

- Functional: `POST /api/test-generation/generate` triggers service generation and persistence.
- Functional: `GET /api/test-generation/test-cases` lists generated test cases with pagination.
- Functional: `GET /api/test-generation/test-cases/{test_case_id}` returns one detail view.
- Non-functional: map DB availability failures to `503` and domain validation failures to clear HTTP status codes.

## Architecture

Router prefix:

```python
router = APIRouter(prefix="/api/test-generation", tags=["test-generation"])
```

Endpoint behavior:

- `POST /generate`: body is `GenerateTestCaseRequest`; response is `GenerateTestCaseResponse`.
- `GET /test-cases`: query params `limit`, `offset`, optional `journey_id`, optional `status` if easy.
- `GET /test-cases/{test_case_id}`: detail response includes `steps`, `assertions`, `golden_response`, and `generated_code`.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\main.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\router.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\router.py`

## Implementation Steps

1. Create router and import schemas/service.
2. Add `generate_test_case` endpoint and map service errors:
   - missing journey -> `404`.
   - missing example session or no logs -> `422`.
   - duplicate with `overwrite=false` -> `409`.
   - `psycopg.OperationalError` -> `503`.
3. Add list endpoint using service `list_test_cases`.
4. Add detail endpoint using service `get_test_case_detail`.
5. Include router in `app/main.py`.

## Success Criteria

- [x] API contract matches schemas.
- [x] Router is included in the FastAPI app.
- [x] Existing routes remain unchanged.
- [x] API tests can monkeypatch service calls and validate status mapping.

## Risk Assessment

- Risk: endpoint naming drifts from frontend expectations later. Mitigation: use explicit `/api/test-generation` namespace now; frontend can consume stable routes later.
- Risk: overloading generator module with read APIs. Mitigation: acceptable for MVP; split into `test_cases` module only when execution/reporting grows.
