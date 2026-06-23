---
phase: 4
title: "Compose web, api, and database stack"
status: in-progress
priority: P1
effort: "1h"
dependencies: ["phase-02", "phase-03"]
---

# Phase 4: Compose Web, API, And Database Stack

## Overview

Create the root Docker Compose file and ignore rules needed to run the local development stack. Verify that web, API, and PostgreSQL start together.

## Requirements

- Functional: `docker compose up --build` starts `web`, `api`, and `database`.
- Functional: `web` maps host `3000` to container `3000`.
- Functional: `api` maps host `8000` to container `8000`.
- Functional: `database` maps host `5432` to container `5432`.
- Functional: Postgres uses database name `logitest_ai`, user `logitest`, password `logitest`.
- Functional: API receives `DATABASE_URL=postgresql://logitest:logitest@database:5432/logitest_ai`.
- Functional: web receives `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.
- Non-functional: Docker context excludes heavy generated folders.

## Architecture

Compose owns local orchestration:

```text
browser -> web:3000
web -> api via NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
api -> database via internal DNS name database:5432
```

The database service should have a named volume for persistence and a healthcheck using `pg_isready`.

## Related Code Files

- Create: `logitest-ai/docker-compose.yml`
- Create: `logitest-ai/.dockerignore`
- Modify: `logitest-ai/README.md`
- Optional modify: `logitest-ai/.env.example`

## Implementation Steps

1. Create root `.dockerignore` excluding:
   - `.git`
   - `node_modules`
   - `.next`
   - `dist`
   - `build`
   - `.venv`
   - `__pycache__`
   - `.pytest_cache`
   - `.mypy_cache`
   - local env files except examples if needed.
2. Create `docker-compose.yml` at `logitest-ai/` with services:
   - `database`: `postgres:16-alpine`, env vars, volume, healthcheck.
   - `api`: build from `apps/api/Dockerfile`, depends on database health, exposes `8000`, sets env.
   - `web`: build from `apps/web/Dockerfile`, depends on api, exposes `3000`, sets env.
3. Configure dev bind mounts carefully:
   - API can mount `./apps/api:/app`.
   - Web may mount `./apps/web:/app/apps/web` and `./packages/shared:/app/packages/shared` while preserving container `node_modules`.
4. Update README with Compose commands:
   - `docker compose up --build`
   - `docker compose down`
   - health check URL.
5. Run `docker compose config`.
6. Run `docker compose up --build`.
7. Verify API health and web URL.
8. Shut down stack after verification unless the user asks to keep it running.

## Success Criteria

- [x] `docker compose config` succeeds.
- [ ] `docker compose up --build` starts all three services.
- [ ] `database` reaches healthy state.
- [ ] `Invoke-RestMethod http://localhost:8000/health` returns `status: ok`.
- [ ] `http://localhost:3000` serves the Next.js app.
- [x] README documents how to run and stop the dev stack.

## Risk Assessment

Risk: Port `3000`, `8000`, or `5432` may already be used on the machine.

Mitigation: document default ports and, if verification hits conflicts, temporarily override host ports or stop conflicting local processes after user confirmation.

Risk: `.env.example` currently references `postgres` as DB host while the required service name is `database`.

Mitigation: Compose should explicitly provide the correct `DATABASE_URL`. Optionally update `.env.example` to use `database` if Docker Compose is now the canonical local infra path.

Risk: Windows file watching can be inconsistent through Docker bind mounts.

Mitigation: set polling env vars only if hot reload fails; do not add them preemptively unless needed.

## Verification Note

Compose config passed. Runtime checks requiring docker compose build or docker compose up --build are blocked until Docker Desktop daemon is running.

