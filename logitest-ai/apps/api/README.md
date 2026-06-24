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

Before the live API smoke test, start the database and apply the migration from the monorepo root:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose up -d database
Get-Content .\database\migrations\001_init_logitest_schema.sql | docker compose exec -T database psql -U logitest -d logitest_ai
```


