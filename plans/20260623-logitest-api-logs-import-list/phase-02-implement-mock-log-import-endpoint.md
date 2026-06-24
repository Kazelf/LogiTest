---
phase: 2
title: "Implement mock log import endpoint"
status: completed
priority: P2
effort: "1.5h"
dependencies: [phase-01]
---

# Phase 2: Implement Mock Log Import Endpoint

## Overview

Expose `POST /api/logs/import-mock` that imports the existing `mock-data/logs.json` dataset into PostgreSQL idempotently.

## Requirements

- Functional: endpoint imports sessions, logs, personas, journeys, and test cases using existing import semantics.
- Functional: repeated calls update existing rows, not duplicate them.
- Functional: endpoint returns loaded record count, session count, and table counts.
- Non-functional: no subprocess call to the import script.
- Non-functional: transaction commits only after full import succeeds.

## Architecture

Best implementation path:

1. Make `scripts/import_mock_logs.py` importable without running `main()`.
2. In API service, import/reuse `load_logs`, `group_by_session`, `upsert_sessions`, `upsert_logs`, `upsert_personas`, `upsert_journeys`, `upsert_test_cases`, `fetch_counts`.
3. Wrap the flow in service function `import_mock_logs()`.
4. Convert known failures into FastAPI `HTTPException` in router.

Avoid:

```python
subprocess.run(["python", "scripts/import_mock_logs.py"])
```

Reason: brittle path handling, weak error reporting, harder tests.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\scripts\import_mock_logs.py` only if importability/path behavior needs cleanup.
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\schemas.py`

## Implementation Steps

1. Verify `scripts/import_mock_logs.py` can be imported from API tests without executing `main()`.
2. Add service function `import_mock_logs_from_dataset()`.
3. Use database connection helper in service.
4. Execute the same import sequence as the script.
5. Commit after all upserts and count fetch succeed.
6. Add router handler `POST /import-mock`.
7. Map `psycopg.OperationalError` to `503`.
8. Map validation/unexpected import errors to `500` for MVP, with concise detail.

## Success Criteria

- [x] Endpoint response includes `source`, `loaded_records`, `sessions`, and `counts`.
- [x] Endpoint is idempotent due to existing `ON CONFLICT` logic.
- [x] Database unavailable returns `503`, not a stack trace.
- [x] Endpoint does not require request body.

## Risk Assessment

- Risk: API cannot import script due Python path from `apps/api`.
  Mitigation: add project root to path carefully or extract import logic into a shared module under `apps/api/app/modules/ingestion` and keep script calling it.
- Risk: import endpoint becomes too powerful for production.
  Mitigation: document as MVP/dev endpoint; auth/disable flag later.

## Security Considerations

- Do not expose raw exception details in HTTP responses.
- Keep endpoint limited to trusted local mock data. No arbitrary file path input.
