# LogiTest AI Database

This folder contains the MVP PostgreSQL schema for LogiTest AI.

## Start PostgreSQL

```powershell
cd D:\ViettelDigitalTalent\LogiTest
docker compose up -d postgres
```

## Apply Schema

```powershell
Get-Content .\logitest-ai\database\migrations\001_init_logitest_schema.sql | docker compose exec -T postgres psql -U logitest -d logitest_ai
```

If your local database was created before `logs.action_type` existed, reset the local MVP database or apply the equivalent manual update:

```sql
ALTER TABLE logs ADD COLUMN IF NOT EXISTS action_type TEXT NOT NULL DEFAULT 'unknown';
CREATE INDEX IF NOT EXISTS idx_logs_action_type ON logs(action_type);
```

If your local database was created before generated script artifacts existed, re-apply the migration or create `test_case_artifacts` from `database/migrations/001_init_logitest_schema.sql`.

## Inspect Tables

```powershell
docker compose exec postgres psql -U logitest -d logitest_ai -c "\dt"
```

## Verify Seeded Data

```powershell
docker compose exec postgres psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM logs;"
docker compose exec postgres psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM sessions;"
docker compose exec postgres psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM personas;"
docker compose exec postgres psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM journeys;"
docker compose exec postgres psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM test_cases;"
docker compose exec postgres psql -U logitest -d logitest_ai -c "SELECT COUNT(*) FROM test_case_artifacts;"
```
