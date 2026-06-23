---
title: "Task 1.4-1.6: Shared TypeScript schemas and local Docker stack"
status: in-progress
created: 2026-06-23
scope: project
source: skill:plan
blockedBy: []
blocks: []
phases:
  - id: phase-01
    title: "Create TypeScript shared schema package"
    status: completed
  - id: phase-02
    title: "Add FastAPI development Dockerfile"
    status: in-progress
  - id: phase-03
    title: "Add Next.js development Dockerfile"
    status: in-progress
  - id: phase-04
    title: "Compose web, api, and database stack"
    status: in-progress
---

# Task 1.4-1.6 Plan

## Goal

Implement the next foundation layer for LogiTest AI:

- Task 1.4: create a shared TypeScript package for types and Zod schemas.
- Task 1.5: add development Dockerfiles for the frontend and backend.
- Task 1.6: add `docker-compose.yml` with `web`, `api`, and `database` services.

The result should support local demo development, not production deployment hardening.

## Confirmed Requirements

- Shared package is TypeScript + Zod only.
- Shared package only needs simple starter schemas.
- Dockerfiles are development-first.
- Database only needs to run as a container; backend DB integration, ORM, and migrations are out of scope.
- Acceptance criteria:
  - `npm install` from `logitest-ai/` installs workspace dependencies.
  - `packages/shared` exposes Zod schemas and inferred TypeScript types.
  - `apps/web` can import from `@logitest/shared`.
  - `docker compose up --build` starts `web`, `api`, and `database`.
  - Web is available at `http://localhost:3000`.
  - API health is available at `http://localhost:8000/health` and returns `{"status":"ok"}`.
  - Postgres is exposed on host port `5432` and has a healthcheck.

## Codebase Context

- Project root: `D:\ViettelDigitalTalent\LogiTest`.
- Monorepo root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai`.
- Existing app folders:
  - `logitest-ai/apps/web`: Next.js 16.2.9, React 19.2.4, TypeScript, npm lockfile.
  - `logitest-ai/apps/api`: FastAPI app with `app.main:app` and `GET /health`.
  - `logitest-ai/packages/shared`: currently only `.gitkeep`.
- Existing env template already defines:
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
  - `DATABASE_URL=postgresql://logitest:logitest@postgres:5432/logitest_ai`
- Previous scaffold plan is completed: `plans/20260623-logitest-next-fastapi-scaffold/plan.md`.

## Architecture Decision

Use a lightweight npm workspace rooted at `logitest-ai/`:

```text
logitest-ai/
|-- package.json                  # private workspace root
|-- docker-compose.yml
|-- .dockerignore
|-- apps/
|   |-- web/
|   |   |-- Dockerfile
|   |   `-- package.json          # depends on @logitest/shared
|   `-- api/
|       |-- Dockerfile
|       `-- requirements.txt
`-- packages/
    `-- shared/
        |-- package.json
        |-- tsconfig.json
        `-- src/
            |-- index.ts
            `-- schemas.ts
```

`packages/shared` is a real package named `@logitest/shared`. It owns Zod schemas and exported inferred types. FastAPI does not consume it in this task because cross-language contract generation is premature while backend domain models are not defined.

## Proposed Starter Schemas

Keep starter schemas intentionally small:

```ts
import { z } from "zod";

export const HealthResponseSchema = z.object({
  status: z.literal("ok"),
});

export const ApiErrorSchema = z.object({
  message: z.string(),
  code: z.string().optional(),
});

export type HealthResponse = z.infer<typeof HealthResponseSchema>;
export type ApiError = z.infer<typeof ApiErrorSchema>;
```

These schemas validate the existing health contract and provide a basic error shape without inventing domain models too early.

## Out Of Scope

- Backend importing or generating TypeScript schemas.
- OpenAPI type generation.
- SQLAlchemy, Alembic, Prisma, migrations, seed data, or actual database connectivity.
- Production Docker optimization, image publishing, CI pipelines.
- Elasticsearch, Kibana, target-system microservices.
- UI redesign beyond a minimal import verification if needed.

## Implementation Phases

1. [Phase 1: Create TypeScript shared schema package](phase-01-create-shared-package.md)
2. [Phase 2: Add FastAPI development Dockerfile](phase-02-add-api-dockerfile.md)
3. [Phase 3: Add Next.js development Dockerfile](phase-03-add-web-dockerfile.md)
4. [Phase 4: Compose web, api, and database stack](phase-04-compose-and-verify.md)

## Recommended Execution Order

Run phases sequentially. Phase 1 should land before the web Dockerfile so Docker install sees the final workspace graph. Phase 4 depends on both Dockerfiles.

## Validation Commands

Run from `D:\ViettelDigitalTalent\LogiTest\logitest-ai`:

```powershell
npm install
npm run build --workspace @logitest/shared
npm run build --workspace web
docker compose config
docker compose up --build
```

In another terminal while Compose is running:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Risks And Mitigations

- Risk: Docker context accidentally includes `apps/api/.venv`, `.next`, or `node_modules`.
  - Mitigation: add root `.dockerignore` before building images.
- Risk: Next.js cannot transpile a workspace package cleanly in dev.
  - Mitigation: add `transpilePackages: ["@logitest/shared"]` to `apps/web/next.config.ts` if needed.
- Risk: npm workspace install conflicts with existing `apps/web/package-lock.json`.
  - Mitigation: prefer root workspace install and allow root lockfile to become authoritative for workspace dependencies.
- Risk: Compose service name mismatch with existing `.env.example` using host `postgres` while requested service is `database`.
  - Mitigation: use `database` as service name and set Compose `DATABASE_URL` to `postgresql://logitest:logitest@database:5432/logitest_ai`; update docs if needed.

## Implementation Status

Implemented on 2026-06-23:

- Created root npm workspace and `@logitest/shared` TypeScript + Zod package.
- Wired `apps/web` to import `HealthResponseSchema` from `@logitest/shared`.
- Added development Dockerfiles for `apps/api` and `apps/web`.
- Added root `.dockerignore`, `.gitignore`, `docker-compose.yml`, and README Docker commands.
- Updated `.env.example` to use Compose service host `database` for `DATABASE_URL`.

Verification completed:

- `npm.cmd install`: passed.
- `npm.cmd run build --workspace @logitest/shared`: passed.
- `npm.cmd run lint --workspace web`: passed.
- `npx.cmd tsc --noEmit --project apps/web/tsconfig.json`: passed.
- `docker compose config`: passed.
- `apps/api/.venv/Scripts/python.exe -m pytest`: passed, 1 test.

Verification blocked:

- `docker compose build` and `docker compose up --build` could not run because Docker Desktop daemon was not available at `npipe:////./pipe/dockerDesktopLinuxEngine`.
- `npm.cmd run build --workspace web` produced `.next` build artifacts and no visible compile errors, but did not return a reliable exit marker through this PowerShell tool session. Frontend lint and direct TypeScript compile passed instead.
## Handoff

This is a low-to-moderate risk foundation plan. After review, the next practical step is `/cook D:\ViettelDigitalTalent\LogiTest\plans\20260623-logitest-shared-docker-compose\plan.md`.


