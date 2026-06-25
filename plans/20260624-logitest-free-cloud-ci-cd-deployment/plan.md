---
title: "Free cloud CI/CD and deployment plan for LogiTest AI"
status: pending
created: 2026-06-24
updated: 2026-06-24
blockedBy: [20260624-logitest-mentor-aligned-mvp-roadmap]
blocks: []
scope: project
---

# Free Cloud CI/CD and Deployment Plan

## Problem Statement

LogiTest AI needs a practical, mostly-free CI/CD and deployment path for the current MVP stack:

- `apps/web`: Next.js dashboard.
- `apps/api`: FastAPI backend.
- `demo-system`: Express demo e-commerce backend.
- `database`: PostgreSQL schema and migrations.
- Elasticsearch remains local-first for MVP demo reliability.

The goal is not production-grade cloud operations. The goal is a repeatable GitHub-based workflow that verifies code quality, deploys demo-accessible services, and avoids paid infrastructure unless the project later needs it.

## Recommended Platform Decision

Use this split:

| Component | Platform | Reason |
|---|---|---|
| Next.js dashboard | Vercel Hobby | Best fit for Next.js, GitHub import, automatic preview deployments, HTTPS by default. |
| FastAPI backend | Render Free Web Service | Simple Python web service deployment, GitHub auto-deploy, enough for MVP demo. |
| Express demo backend | Render Free Web Service | Simple Node web service deployment, separate URL for generated tests and dashboard integration. |
| PostgreSQL | Neon Free | Persistent free PostgreSQL is more suitable than Render free PostgreSQL, which is time-limited. |
| Elasticsearch | Local Docker Compose only | Free cloud Elasticsearch is not stable long-term; keep fallback JSON/import flow for hosted demo. |

## Scope

In scope:

- Add GitHub Actions CI workflow for Node, Next.js, Express, shared TypeScript, and FastAPI tests.
- Add Docker build validation workflow for existing Dockerfiles and Compose config.
- Document manual setup for Neon, Render, Vercel, and required environment variables.
- Define smoke checks after deployment.
- Keep hosted MVP usable without cloud Elasticsearch by relying on fallback/mock import path where needed.

Out of scope:

- Paid production infrastructure.
- Kubernetes, service mesh, or cloud Elasticsearch.
- Docker image registry publishing.
- Full zero-downtime deployment strategy.
- Secrets rotation automation.
- Custom domain setup.

## Architecture

```text
GitHub repository
  |
  | pull_request / push
  v
GitHub Actions CI
  |-- npm ci
  |-- shared package build
  |-- web lint + build
  |-- demo-system tests
  |-- FastAPI pytest
  |-- Dockerfile / Compose validation

Production-like free demo
  |
  |-- Vercel: apps/web
  |       NEXT_PUBLIC_API_BASE_URL=https://logitest-api.onrender.com
  |
  |-- Render: apps/api
  |       DATABASE_URL=postgresql://...neon...
  |       DEMO_BACKEND_URL=https://logitest-demo.onrender.com
  |       ELASTICSEARCH_URL=disabled or local-only placeholder
  |
  |-- Render: demo-system
  |       REGRESSION_MODE=false
  |
  |-- Neon: PostgreSQL
```

## Key Constraints and Decisions

- Render Free services can sleep. Demo must be warmed up before presenting.
- Hosted Elasticsearch is intentionally skipped because long-lived free options are poor.
- CI must not require Docker daemon for unit tests. Docker validation can run in GitHub Actions where Docker is available.
- Database migration should be an explicit setup step, not hidden inside app startup.
- Deployment environment variables must be documented, not hardcoded.

## Phases

1. [Phase 01: Add GitHub Actions CI Gate](phase-01-add-github-actions-ci-gate.md)
2. [Phase 02: Add Docker Build Validation Gate](phase-02-add-docker-build-validation-gate.md)
3. [Phase 03: Prepare Neon PostgreSQL Setup](phase-03-prepare-neon-postgresql-setup.md)
4. [Phase 04: Prepare Render Services](phase-04-prepare-render-services.md)
5. [Phase 05: Prepare Vercel Frontend Deployment](phase-05-prepare-vercel-frontend-deployment.md)
6. [Phase 06: End-to-End Hosted Smoke Test and Documentation](phase-06-end-to-end-hosted-smoke-test-and-documentation.md)

## Detailed Setup Guide

### 1. GitHub Repository Setup

1. Push the current repo to GitHub.
2. Confirm the repository root contains `logitest-ai/`.
3. In GitHub, open `Actions` and enable workflows if GitHub asks.
4. Use `main` as the protected branch later, after CI is green.

Recommended branch rule after CI works:

- Require pull request before merge.
- Require `CI` workflow to pass.
- Require `Docker Build Validation` workflow to pass only if Dockerfiles are stable.

### 2. Neon PostgreSQL Setup

1. Create a Neon account.
2. Create a new project named `logitest-ai`.
3. Choose the nearest free region.
4. Copy the pooled or direct connection string.
5. Store the URL for Render API service:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST/logitest_ai?sslmode=require
```

6. Apply migration from local machine:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
psql "postgresql://USER:PASSWORD@HOST/logitest_ai?sslmode=require" -f database\migrations\001_init_logitest_schema.sql
```

If `psql` is not installed, use Neon's SQL Editor and paste the SQL from:

```text
database/migrations/001_init_logitest_schema.sql
```

### 3. Render FastAPI Service Setup

Create a Render Web Service:

- Name: `logitest-api`
- Repository: GitHub repo containing this project.
- Root directory: `logitest-ai/apps/api`
- Runtime: Python
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
DATABASE_URL=<Neon connection string>
DEMO_BACKEND_URL=https://<render-demo-service>.onrender.com
ELASTICSEARCH_URL=
STAGING_API_BASE_URL=https://<render-demo-service>.onrender.com
DEMO_LOG_INDEX=logitest-demo-logs
```

Smoke check:

```powershell
Invoke-RestMethod https://<render-api-service>.onrender.com/health
```

Expected result: healthy response from FastAPI.

### 4. Render Express Demo Service Setup

Create a second Render Web Service:

- Name: `logitest-demo`
- Repository: same GitHub repo.
- Root directory: `logitest-ai/demo-system`
- Runtime: Node
- Build command:

```bash
npm install
```

- Start command:

```bash
npm start
```

Environment variables:

```text
REGRESSION_MODE=false
```

Smoke checks:

```powershell
Invoke-RestMethod https://<render-demo-service>.onrender.com/api/products
```

Then test regression mode later by setting:

```text
REGRESSION_MODE=true
```

and redeploying the Render service.

### 5. Vercel Next.js Setup

Create a Vercel project:

- Import same GitHub repository.
- Framework preset: Next.js.
- Root directory: `logitest-ai/apps/web`.
- Install command:

```bash
npm install
```

- Build command:

```bash
npm run build
```

Environment variables:

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-api-service>.onrender.com
```

After deploy:

1. Open the Vercel URL.
2. Confirm dashboard loads.
3. Confirm API calls use the Render FastAPI URL, not localhost.

### 6. GitHub Actions Secrets

For the initial CI plan, no secrets are required.

Add secrets only if later workflows need deployment API tokens:

```text
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
RENDER_API_KEY
NEON_DATABASE_URL
```

For the first version, prefer platform-native GitHub integration in Vercel and Render instead of custom deploy scripts. It is simpler and less fragile.

## Verification Commands

Local checks before pushing:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
npm ci
npm run build:shared
npm run lint --workspace web
npm run build:web
npm run test:demo
```

Backend checks:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
python -m pip install -r requirements.txt
python -m pytest
```

Docker checks when Docker Desktop is running:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose config
docker build -f apps\api\Dockerfile apps\api
docker build -f apps\web\Dockerfile .
docker build -f demo-system\Dockerfile demo-system
```

## Success Criteria

- GitHub Actions CI passes on pull requests.
- Docker validation workflow catches broken Dockerfiles or Compose syntax.
- Neon database contains the LogiTest schema.
- Render FastAPI `/health` endpoint responds over HTTPS.
- Render demo backend responds over HTTPS.
- Vercel frontend loads and points to the Render API URL.
- Hosted demo path is documented with the Elasticsearch limitation clearly stated.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Render Free services sleep | First request slow during demo | Warm API and demo backend URLs before presenting. |
| Cloud Elasticsearch not free long-term | Hosted demo cannot use live ES import | Keep Elasticsearch local; use mock-data fallback for hosted demo. |
| Neon connection requires SSL | Backend DB connection may fail | Use `sslmode=require` in `DATABASE_URL`. |
| Monorepo root differs across platforms | Build commands may fail | Set root directories explicitly in Vercel/Render. |
| Dockerfiles are dev-first | Cloud Docker deployment may be inefficient | Use native Render/Vercel runtime for free demo; keep Docker validation for local/demo parity. |

## Implementation Notes

- Prefer GitHub Actions for validation, not deployment orchestration, in the first version.
- Let Vercel and Render perform auto-deploy from GitHub after CI is stable.
- Later, if paid/prod deployment is required, add explicit deployment workflows with environment protection and deployment secrets.

