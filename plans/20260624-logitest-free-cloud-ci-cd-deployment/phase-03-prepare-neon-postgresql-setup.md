---
phase: 3
title: "Prepare Neon PostgreSQL Setup"
status: completed
priority: P1
effort: "45m"
dependencies: []
---

# Phase 03: Prepare Neon PostgreSQL Setup

## Overview

Set up a free persistent PostgreSQL database on Neon and apply the existing LogiTest schema migration.

## Requirements

- Functional: Neon project exists.
- Functional: connection string is available for Render FastAPI.
- Functional: `database/migrations/001_init_logitest_schema.sql` is applied.
- Non-functional: connection string is never committed to git.

## Architecture

Neon becomes the hosted database for the Render FastAPI service:

```text
Render FastAPI service -> Neon PostgreSQL
```

Local Docker PostgreSQL remains available for local development.

## Related Code Files

- Read: `logitest-ai/database/migrations/001_init_logitest_schema.sql`
- Read: `logitest-ai/apps/api/app/core/settings.py`
- Read: `logitest-ai/.env.example`
- Optionally modify later: `logitest-ai/apps/api/README.md`

## Implementation Steps

1. Create Neon project `logitest-ai`.
2. Copy the connection string.
3. Ensure it includes SSL:

```text
?sslmode=require
```

4. Apply migration using `psql`:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
psql "<NEON_DATABASE_URL>" -f database\migrations\001_init_logitest_schema.sql
```

5. If `psql` is unavailable, paste the migration SQL into the Neon SQL Editor.
6. Store the connection string only in Render environment variables.

## Success Criteria

- [x] Neon database exists.
- [x] LogiTest tables exist after migration.
- [x] Render-ready `DATABASE_URL` is available.
- [x] No database credentials are committed.

## Risk Assessment

Risk: Existing backend code may assume local PostgreSQL hostname or no SSL.

Mitigation: Use `DATABASE_URL` from environment and include `sslmode=require`. Keep local `.env.example` as documentation only.

## Completion Notes

Completed on 2026-06-25 based on user confirmation:

- Neon PostgreSQL database was created.
- `database/migrations/001_init_logitest_schema.sql` was applied successfully.
- Database password was rotated after the connection string was shared in chat.
- The rotated connection string is ready to be stored in Render environment variables.

Secret hygiene verification:

- Searched the repository for Neon secret patterns and host fragments.
- No real Neon password or connection string was found in tracked project files.
- Documentation retains only placeholders such as `<NEON_DATABASE_URL>`.
