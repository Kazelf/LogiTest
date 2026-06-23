---
phase: 3
title: "Create seed and import script"
status: completed
priority: P1
effort: "2h"
dependencies: ["phase-01", "phase-02"]
---

# Phase 3: Create Seed And Import Script

## Overview

Create an idempotent Python script that imports the mock log dataset into PostgreSQL and seeds derived MVP data for personas, journeys, and test cases.

## Requirements

- Functional: add PostgreSQL driver dependency.
- Functional: read database connection from `DATABASE_URL`.
- Functional: fallback to local Docker database URL when env is missing.
- Functional: read `mock-data/logs.json` regardless of the shell's current working directory.
- Functional: upsert sessions and logs using stable external IDs.
- Functional: seed personas, journeys, and generated test cases.
- Non-functional: keep the script deterministic, readable, and safe to run multiple times.

## Architecture

The script is a local automation tool, not a long-running backend component. It should connect to Postgres using `psycopg`, perform explicit SQL statements, and commit after successful import.

Data flow:

```text
mock-data/logs.json
  -> import_mock_logs.py
  -> sessions/logs
  -> personas/journeys/test_cases
```

Idempotency should be based on stable natural keys:

- `sessions.external_session_id`
- `logs.external_log_id`
- `personas.name`
- `journeys.name`
- `test_cases.name`

## Related Code Files

- Modify: `logitest-ai/apps/api/requirements.txt`
- Create: `logitest-ai/scripts/import_mock_logs.py`

## Implementation Steps

1. Add `psycopg[binary]` to `apps/api/requirements.txt`.
2. Create `logitest-ai/scripts/` if it does not exist.
3. Implement path resolution from `Path(__file__).resolve().parents[1]` to locate `mock-data/logs.json`.
4. Normalize `postgresql://` URLs for `psycopg` if needed.
5. Load and validate mock records at a practical level:
   - required keys exist
   - timestamp is parseable
   - payload and response body are JSON-compatible
6. Upsert sessions:
   - group by `session_id`
   - compute `started_at`, `ended_at`, and `request_count`
   - preserve `user_id` from records
7. Upsert logs:
   - map external `session_id` to internal UUID
   - insert normalized fields and full `raw_log`
   - update existing rows when `external_log_id` already exists
8. Seed personas:
   - `Buyer`
   - `Browser`
   - `Failed Payment User`
9. Seed journeys using the mock sequences:
   - `Successful buyer checkout`
   - `Product browsing without purchase`
   - `Checkout with failed payment`
10. Seed one generated API test case per journey.
11. Print a concise summary of inserted/upserted counts.

## Success Criteria

- [x] Script can load mock data from the monorepo root.
- [ ] Script can be run more than once without duplicating rows.
- [ ] `logs` count equals the number of mock log records.
- [ ] `sessions` count matches distinct mock sessions.
- [ ] `personas` contains at least the three planned personas.
- [ ] `journeys` and `test_cases` contain seeded demo records.

## Implementation Note

Created `logitest-ai/scripts/import_mock_logs.py` and added `psycopg[binary]` to API requirements. The script compiled and its JSON load/group path verified 16 logs across 3 sessions. Database write checks are covered by Phase 4.

## Risk Assessment

Risk: `psycopg[binary]` in app requirements means Docker image rebuild is needed before use inside the API container.

Mitigation: document that host script execution needs the dependency installed locally; Docker runtime use requires `docker compose build api` later.

Risk: The script may grow into hidden application logic.

Mitigation: keep it as a seed/import utility only. Real ingestion, reconstruction, and generation modules should own production behavior later.
