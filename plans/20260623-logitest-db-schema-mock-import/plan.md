---
title: "Task 2.2-2.4: Initialize database schema, mock logs, and import script"
status: in-progress
created: 2026-06-23
scope: project
source: skill:plan
blockedBy: [20260623-logitest-shared-docker-compose]
blocks: [20260623-logitest-api-logs-import-list, 20260624-logitest-session-group-detail-api, 20260624-logitest-session-reconstruction-action-classifier, 20260624-logitest-behavior-analysis-journey-persona-api]
phases:
  - id: phase-01
    title: "Create SQL schema migration"
    status: completed
  - id: phase-02
    title: "Create mock log JSON dataset"
    status: completed
  - id: phase-03
    title: "Create seed and import script"
    status: completed
  - id: phase-04
    title: "Verify database import workflow"
    status: in-progress
---

# Task 2.2-2.4 Plan

## Goal

Implement the first persistent data layer for LogiTest AI using the approved lightweight approach:

- Task 2.2: create a SQL schema init/migration.
- Task 2.3: create mock structured log JSON.
- Task 2.4: create a seed/import script that loads mock logs into PostgreSQL.

The output should be simple enough for the MVP demo, deterministic to run locally, and easy to later migrate to Alembic/SQLAlchemy if the project needs ORM-managed migrations.

## Codebase Context

- Project root: `D:\ViettelDigitalTalent\LogiTest`.
- Monorepo root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai`.
- Backend: FastAPI app in `logitest-ai/apps/api` with only `GET /health` implemented.
- Database: PostgreSQL 16 service named `database` in `logitest-ai/docker-compose.yml`.
- Current API requirements: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `pytest`, `httpx`.
- Existing docs describe modules for ingestion, session reconstruction, behavior mining, test generation, execution, and reports.
- The Docker Compose plan is still marked in-progress, but `docker-compose.yml` exists. This plan depends on that local database service being available.

## Confirmed Approach

Use SQL migration plus a direct Python import script with `psycopg`.

Rejected for this round:

- Alembic + SQLAlchemy models: more production-shaped, but too much setup for the current thin backend.
- Docker entrypoint init scripts: convenient only for a brand-new database volume and awkward after the Postgres volume already exists.

## Target Folder Shape

```text
logitest-ai/
|-- database/
|   |-- README.md
|   `-- migrations/
|       `-- 001_init_logitest_schema.sql
|-- mock-data/
|   `-- logs.json
|-- scripts/
|   `-- import_mock_logs.py
`-- apps/
    `-- api/
        `-- requirements.txt
```

## Data Model

The SQL migration should create the six MVP tables from Task 2.1:

- `sessions`: reconstructed user sessions keyed by external session ID.
- `logs`: normalized structured logs imported from Elasticsearch-like JSON.
- `personas`: detected behavior personas such as Buyer, Browser, Failed Payment User.
- `journeys`: mined endpoint sequences and behavior flows.
- `test_cases`: generated API/E2E test specifications and golden responses.
- `test_runs`: execution results for generated test cases.

Use `JSONB` for variable structures: request payloads, response bodies, raw logs, journey steps, assertions, golden responses, actual responses, and diff results.

## Runtime Commands

Expected local workflow after implementation:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose up -d database
Get-Content .\database\migrations\001_init_logitest_schema.sql | docker compose exec -T database psql -U logitest -d logitest_ai
python .\scripts\import_mock_logs.py
```

If running the script from a shell that does not expose `DATABASE_URL`, it should fallback to:

```text
postgresql://logitest:logitest@localhost:5432/logitest_ai
```

## Acceptance Criteria

- `001_init_logitest_schema.sql` can be applied repeatedly after dropping/recreating the database volume or on a fresh DB.
- The migration creates all six required tables plus useful indexes.
- `mock-data/logs.json` contains realistic structured log records for at least three sessions.
- `import_mock_logs.py` imports sessions and logs idempotently using stable external IDs.
- The import script seeds basic personas, journeys, and generated test cases.
- Verification SQL returns non-zero counts for `logs`, `sessions`, `journeys`, and `test_cases`, and at least three personas.

## Non-Goals

- No FastAPI CRUD endpoints in this plan.
- No dashboard UI changes in this plan.
- No Elasticsearch connector in this plan; mock JSON stands in for the ingestion source.
- No Playwright or pytest execution runner in this plan.
- No Alembic setup unless explicitly requested later.

## Risks

- Existing Postgres volume may contain old partial tables.
  Mitigation: document verification and reset commands, but do not destructive-reset automatically.
- Python script may run from different working directories.
  Mitigation: resolve paths relative to the script location, not the current shell directory.
- Docker database hostname differs between host and container.
  Mitigation: script defaults to `localhost`; Compose API continues to use service name `database`.

## Phase Summary

1. Create SQL schema migration.
2. Create realistic mock log JSON.
3. Create idempotent seed/import script.
4. Verify migration and import workflow against Docker PostgreSQL.

## Implementation Status

- Phase 1 completed: SQL schema migration and database README were created.
- Phase 2 completed: mock JSON dataset was created and parses successfully.
- Phase 3 completed: import script was created, `psycopg[binary]` was added, and the script's load/group flow was verified.
- Phase 4 is in progress: Docker CLI is available, but Docker Desktop daemon is not running, so live PostgreSQL migration/import verification is blocked until the daemon starts.

