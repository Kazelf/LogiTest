# LogiTest AI API

FastAPI backend for the LogiTest AI modular monolith.

## Setup

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
py -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

## Test

```powershell
.\.venv\Scripts\python -m pytest
```

## Logs API

Import the bundled mock log dataset into PostgreSQL:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/logs/import-mock
```

List normalized logs with pagination and optional filters:

```powershell
Invoke-RestMethod "http://localhost:8000/api/logs?limit=5&offset=0&session_id=session-buyer-001"
```

Group logs by session:

```powershell
Invoke-RestMethod "http://localhost:8000/api/logs/sessions?limit=5"
```

Fetch one session with ordered log details:

```powershell
Invoke-RestMethod "http://localhost:8000/api/logs/sessions/session-buyer-001"
```

## Behavior API

Run behavior analysis from imported logs. This mines personas and journeys from existing `logs.action_type` values and upserts results into PostgreSQL:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/behavior/analyze
```

List mined journeys:

```powershell
Invoke-RestMethod "http://localhost:8000/api/behavior/journeys?limit=5"
```

List mined personas:

```powershell
Invoke-RestMethod "http://localhost:8000/api/behavior/personas?limit=5"
```

## Test Generation API

Generate and persist an API test case from a mined journey. Use a journey `id` returned by `/api/behavior/journeys`. If `frameworks` is omitted, the API renders `playwright_api` by default.

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/test-generation/generate `
  -ContentType "application/json" `
  -Body '{"journey_id":"<journey-id>","overwrite":true}'
```

Generate Playwright API, Jest/Supertest, and Mocha/Supertest artifacts in one request. Set `write_files` to `true` to write files under `generated-tests/`:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/test-generation/generate `
  -ContentType "application/json" `
  -Body '{"journey_id":"<journey-id>","overwrite":true,"frameworks":["playwright_api","jest_supertest","mocha_supertest"],"write_files":true}'
```

Generated scripts are stored as artifacts. This task generates code only; it does not install or execute Playwright, Jest, Mocha, Supertest, or Chai.

List generated test cases:

```powershell
Invoke-RestMethod "http://localhost:8000/api/test-generation/test-cases?limit=5&status=generated"
```

Fetch one generated test case with JSON steps, assertions, golden response, generated code mirror, and artifacts:

```powershell
Invoke-RestMethod "http://localhost:8000/api/test-generation/test-cases/<test-case-id>"
```

Fetch generated script artifacts:

```powershell
Invoke-RestMethod "http://localhost:8000/api/test-generation/test-cases/<test-case-id>/artifacts"
Invoke-RestMethod "http://localhost:8000/api/test-generation/test-cases/<test-case-id>/artifacts/playwright_api"
```

Optional local smoke order:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/logs/import-mock
Invoke-RestMethod -Method Post http://localhost:8000/api/behavior/analyze
Invoke-RestMethod "http://localhost:8000/api/behavior/journeys?limit=5"
Invoke-RestMethod "http://localhost:8000/api/behavior/personas?limit=5"
Invoke-RestMethod -Method Post http://localhost:8000/api/test-generation/generate `
  -ContentType "application/json" `
  -Body '{"journey_id":"<journey-id>","overwrite":true,"frameworks":["playwright_api","jest_supertest","mocha_supertest"],"write_files":true}'
Invoke-RestMethod "http://localhost:8000/api/test-generation/test-cases?limit=5"
```

Before the live API smoke test, start the database and apply the migration from the monorepo root:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose up -d database
Get-Content .\database\migrations\001_init_logitest_schema.sql | docker compose exec -T database psql -U logitest -d logitest_ai
```


