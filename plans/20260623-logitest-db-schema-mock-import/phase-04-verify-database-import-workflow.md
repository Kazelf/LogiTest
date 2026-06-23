---
phase: 4
title: "Verify database import workflow"
status: in-progress
priority: P1
effort: "1h"
dependencies: ["phase-01", "phase-02", "phase-03"]
---

# Phase 4: Verify Database Import Workflow

## Overview

Verify that the migration and import script work against the Docker Compose PostgreSQL service and produce the expected MVP data.

## Requirements

- Functional: database service starts successfully.
- Functional: SQL schema applies successfully.
- Functional: import script runs successfully.
- Functional: verification queries show expected row counts.
- Non-functional: do not wipe existing developer data unless the user explicitly asks.

## Architecture

Verification uses the existing Docker Compose database service and host-side Python script execution.

```text
PowerShell
  -> docker compose up -d database
  -> psql inside database container
  -> host Python import script
  -> psql verification queries
```

## Related Code Files

- Read: `logitest-ai/docker-compose.yml`
- Read: `logitest-ai/database/migrations/001_init_logitest_schema.sql`
- Run: `logitest-ai/scripts/import_mock_logs.py`

## Implementation Steps

1. Start database:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
   docker compose up -d database
   ```

2. Apply schema:

   ```powershell
   Get-Content .\database\migrations\001_init_logitest_schema.sql | docker compose exec -T database psql -U logitest -d logitest_ai
   ```

3. Install Python dependency locally if missing:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
   .\.venv\Scripts\python -m pip install -r requirements.txt
   ```

4. Run import from monorepo root:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
   .\apps\api\.venv\Scripts\python .\scripts\import_mock_logs.py
   ```

5. Verify row counts:

   ```powershell
   docker compose exec database psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM logs;"
   docker compose exec database psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM sessions;"
   docker compose exec database psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM personas;"
   docker compose exec database psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM journeys;"
   docker compose exec database psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM test_cases;"
   ```

6. Re-run the import script once and confirm counts do not duplicate.

## Success Criteria

- [ ] Database container is running and reachable.
- [ ] Migration applies with no SQL errors.
- [ ] Import script exits successfully.
- [ ] `logs` count is at least 12.
- [ ] `sessions` count is at least 3.
- [ ] `personas` count is at least 3.
- [ ] `journeys` count is at least 3.
- [ ] `test_cases` count is at least 3.
- [ ] Re-running import does not increase counts unexpectedly.

## Risk Assessment

Risk: Docker Desktop may not be running.

Mitigation: if `docker compose up -d database` fails due to daemon availability, report the blocker and leave code changes intact for later verification.

Risk: Existing database has conflicting manually created tables.

Mitigation: inspect errors first. Only reset the Docker volume after explicit user approval.

## Verification Note

Offline checks passed: JSON parsing, Python compilation, mock load/group flow, and existing API pytest suite. Live Docker PostgreSQL checks are blocked because Docker Desktop daemon is not running: `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`.
