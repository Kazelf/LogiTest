---
phase: 3
title: "Create FastAPI backend app"
status: pending
priority: P1
effort: "45m"
dependencies: [phase-01]
---

# Phase 3: Create FastAPI Backend App

## Overview

Create the backend scaffold in `logitest-ai/apps/api` using Python FastAPI and a modular monolith folder layout.

## Requirements

- Functional: backend starts locally and exposes `GET /health`.
- Non-functional: folder structure should support future modules for ingestion, mining, generation, execution, and reports.

## Architecture

FastAPI app entrypoint is `app/main.py`. Domain modules live under `app/modules`. Shared app config belongs in `app/core`; future persistence code belongs in `app/db`.

## Related Code Files

- Create: `logitest-ai/apps/api/app/main.py`
- Create: `logitest-ai/apps/api/app/core/__init__.py`
- Create: `logitest-ai/apps/api/app/db/__init__.py`
- Create: `logitest-ai/apps/api/app/modules/*/__init__.py`
- Create: `logitest-ai/apps/api/app/workers/__init__.py`
- Create: `logitest-ai/apps/api/tests/test_health.py`
- Create: `logitest-ai/apps/api/requirements.txt`
- Create: `logitest-ai/apps/api/README.md`

## Implementation Steps

1. Create backend folders:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
   New-Item -ItemType Directory -Force .\apps\api\app\core, .\apps\api\app\db, .\apps\api\app\workers, .\apps\api\tests | Out-Null
   New-Item -ItemType Directory -Force .\apps\api\app\modules\projects, .\apps\api\app\modules\ingestion, .\apps\api\app\modules\session_reconstruction, .\apps\api\app\modules\behavior_mining, .\apps\api\app\modules\test_generation, .\apps\api\app\modules\execution, .\apps\api\app\modules\reports | Out-Null
   ```

2. Add Python package markers:

   ```powershell
   Get-ChildItem .\apps\api\app -Directory -Recurse | ForEach-Object { New-Item -ItemType File -Force (Join-Path $_.FullName "__init__.py") | Out-Null }
   New-Item -ItemType File -Force .\apps\api\app\__init__.py | Out-Null
   ```

3. Create virtual environment:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
   py -m venv .venv
   .\.venv\Scripts\python -m pip install --upgrade pip
   ```

4. Create `requirements.txt` with:

   ```text
   fastapi
   uvicorn[standard]
   pydantic-settings
   pytest
   httpx
   ```

5. Install dependencies:

   ```powershell
   .\.venv\Scripts\python -m pip install -r requirements.txt
   ```

6. Create `app/main.py` with a minimal health endpoint:

   ```python
   from fastapi import FastAPI

   app = FastAPI(title="LogiTest AI API")


   @app.get("/health")
   def health_check() -> dict[str, str]:
       return {"status": "ok"}
   ```

7. Create `tests/test_health.py`:

   ```python
   from fastapi.testclient import TestClient

   from app.main import app


   client = TestClient(app)


   def test_health_check_returns_ok() -> None:
       response = client.get("/health")
       assert response.status_code == 200
       assert response.json() == {"status": "ok"}
   ```

8. Run backend:

   ```powershell
   .\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
   ```

## Success Criteria

- [ ] `apps/api/app/main.py` exists.
- [ ] `apps/api/requirements.txt` exists.
- [ ] `GET http://localhost:8000/health` returns `{ "status": "ok" }`.
- [ ] `pytest` passes for the health endpoint.

## Risk Assessment

Medium risk because local Python launcher names differ. If `py` is unavailable, use `python -m venv .venv` or the project-approved Python executable.

