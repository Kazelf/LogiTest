---
phase: 1
title: "Create API database and router foundation"
status: completed
priority: P2
effort: "1.5h"
dependencies: []
---

# Phase 1: Create API Database and Router Foundation

## Overview

Create the minimal backend structure needed for log APIs: database settings/connection helper, ingestion router, and response/request schemas.

## Requirements

- Functional: API can include a router under `/api/logs` without breaking existing `GET /health`.
- Functional: database URL reads from `DATABASE_URL`, matching existing script fallback behavior.
- Non-functional: no ORM; keep direct `psycopg` for consistency with current repo.
- Non-functional: structure should be easy to test by dependency injection or monkeypatching.

## Architecture

Suggested file shape:

```text
logitest-ai/apps/api/app/
|-- core/
|   `-- settings.py
|-- db/
|   `-- connection.py
`-- modules/
    `-- ingestion/
        |-- router.py
        |-- schemas.py
        `-- service.py
```

Data flow:

1. `main.py` creates FastAPI app.
2. `main.py` includes `ingestion.router` with prefix `/api/logs`.
3. Router calls service functions.
4. Service uses `db.connection.get_database_url()` / connection factory.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\main.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\core\settings.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\db\connection.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\router.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\schemas.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\service.py`

## Implementation Steps

1. Add settings helper with default `postgresql://logitest:logitest@localhost:5432/logitest_ai`.
2. Add connection helper returning `psycopg.connect(database_url)`.
3. Define Pydantic response schemas for import summary and list results.
4. Add empty/stub ingestion router with planned route placeholders or routes in later phases.
5. Include router in `main.py` with prefix `/api/logs` and tag `logs`.

## Success Criteria

- [x] `GET /health` still returns `{"status":"ok"}`.
- [x] FastAPI app imports without side effects or DB connection at import time.
- [x] Router prefix is stable: `/api/logs`.
- [x] Settings and connection helper can be monkeypatched in tests.

## Risk Assessment

- Risk: connecting to DB during module import breaks tests.
  Mitigation: only connect inside service functions.
- Risk: too many abstractions too early.
  Mitigation: keep helpers tiny and only for DB URL/connection boundary.

## Security Considerations

- Do not log full `DATABASE_URL`.
- Keep CORS/auth unchanged; auth is out of scope for this MVP task.
