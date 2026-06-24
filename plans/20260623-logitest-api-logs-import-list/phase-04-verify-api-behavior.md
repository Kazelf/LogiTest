---
phase: 4
title: "Verify API behavior"
status: completed
priority: P2
effort: "1h"
dependencies: [phase-02, phase-03]
---

# Phase 4: Verify API Behavior

## Overview

Add tests and verification commands for route behavior, validation, DB failure handling, and optional live PostgreSQL smoke checks.

## Requirements

- Functional: tests confirm both new endpoints are registered and return expected shapes.
- Functional: validation tests cover pagination bounds.
- Functional: DB failure maps to `503`.
- Non-functional: default test suite should not require Docker daemon.
- Non-functional: live DB verification command should be documented for local demo.

## Architecture

Testing layers:

1. FastAPI `TestClient` route tests.
2. Monkeypatch service functions for success and failure cases.
3. Optional DB-backed smoke test only when Docker/Postgres is running.

Suggested commands:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
python -m pytest
```

Optional live check:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose up -d database
Get-Content .\database\migrations\001_init_logitest_schema.sql | docker compose exec -T database psql -U logitest -d logitest_ai
cd .\apps\api
uvicorn app.main:app --reload
```

Then call:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/logs/import-mock
Invoke-RestMethod http://localhost:8000/api/logs?limit=5
```

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_logs_api.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_health.py` only if shared fixtures are needed.
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\README.md` if adding manual verification commands.

## Implementation Steps

1. Add import endpoint success test with monkeypatched service result.
2. Add import endpoint DB failure test.
3. Add list endpoint success test with monkeypatched service result.
4. Add pagination validation tests for invalid limits and offsets.
5. Add service-level test for query builder if SQL construction is separated.
6. Run `python -m pytest` in `apps/api`.
7. If Docker daemon is available, run optional live smoke check.
8. Document any blocked live verification clearly.

## Success Criteria

- [x] All API tests pass without Docker.
- [x] Existing health test still passes.
- [x] Optional live smoke check succeeds or blocker is documented.
- [x] README includes manual verification commands if useful.

## Verification Result

- `python -m pytest` in `logitest-ai/apps/api`: 8 passed, 1 Starlette/httpx deprecation warning.
- `python -m compileall app` in `logitest-ai/apps/api`: compiled 7 packages.
- Live Docker/PostgreSQL smoke test not run because Docker Desktop daemon is not available: `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`.

## Risk Assessment

- Risk: tests over-mock and miss SQL bugs.
  Mitigation: include at least one service/query-builder test verifying generated filters and params.
- Risk: local environment lacks running Postgres.
  Mitigation: make live verification optional and explicit.

## Security Considerations

- Include a test or code review check that user input appears only in SQL params, never interpolated SQL strings.
