---
title: "Mentor-aligned MVP roadmap: e-commerce logs to API regression reports"
description: "Realign LogiTest AI to the mentor-approved MVP: Express modular-monolith e-commerce demo system, Elasticsearch local, FastAPI platform ingestion/analyzer/generator/execution, Jest/Supertest API tests, and dashboard demo flow."
status: in-progress
priority: P1
effort: 8d
branch: master
tags: [roadmap, architecture, demo-system, elasticsearch, backend, dashboard, test-generation, execution]
blockedBy: [20260623-logitest-shared-docker-compose]
blocks: [20260624-logitest-test-execution-report-api]
created: 2026-06-24
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Realign project documentation and scope"
    status: completed
  - id: phase-02
    title: "Create Express e-commerce demo backend"
    status: completed
  - id: phase-03
    title: "Add Elasticsearch logging path and Compose services"
    status: completed
  - id: phase-04
    title: "Import Elasticsearch logs into FastAPI platform"
    status: pending
  - id: phase-05
    title: "Refocus journey analyzer on flows and chaining"
    status: pending
  - id: phase-06
    title: "Make Jest/Supertest generation the primary output"
    status: pending
  - id: phase-07
    title: "Rework execution and regression reporting against the demo backend"
    status: pending
  - id: phase-08
    title: "Build dashboard and demo script"
    status: pending
---

# Mentor-Aligned MVP Roadmap

## Overview

Realign the current LogiTest AI project with the mentor feedback in `D:\Downloads\thay-doi-can-thiet-cho-codex.md`.

The final MVP should prove one tight demo story:

```text
Postman / demo script
  -> Express e-commerce modular monolith
  -> structured API logs
  -> Elasticsearch local
  -> FastAPI ingestion + normalization
  -> journey detection with API chaining
  -> Jest + Supertest test generation
  -> execution against local/staging target
  -> golden response comparison
  -> Next.js dashboard report
```

## Current Codebase Context

- Monorepo root: `D:\ViettelDigitalTalent\LogiTest\logitest-ai`.
- Platform backend: FastAPI modular monolith in `apps/api`.
- Dashboard frontend: Next.js in `apps/web`, currently still a starter page.
- Database: PostgreSQL schema in `database/migrations/001_init_logitest_schema.sql`.
- Existing modules:
  - `ingestion`: mock JSON import, log/session list/detail APIs.
  - `session_reconstruction`: action classifier for e-commerce-like logs.
  - `behavior_mining`: rule-based journeys/personas.
  - `test_generation`: test case persistence plus Playwright/Jest/Mocha renderers.
  - `execution` and `reports`: placeholders only.
- Docker Compose has `database`, `api`, `web`, `elasticsearch`, and `demo-backend`.
- Existing mock dataset remains available as a fallback source.

## Key Decisions

- Keep LogiTest AI platform as **FastAPI Modular Monolith**. Do not rewrite it to Node/Nest just because the demo target system uses Node.
- Build the system under test as **Express.js e-commerce modular monolith**, not real microservices.
- Use **Elasticsearch local** as the primary demo log source, with mock JSON import as fallback.
- Make **Jest + Supertest** the primary generated test artifact.
- Treat Playwright, advanced persona detection, async callback flow, Kubernetes, RabbitMQ/Kafka, and LLM-heavy generation as future work unless time remains.
- Prefer deterministic rules and templates over free-form LLM generation for MVP reliability.

## Cross-Plan Dependencies

| Relationship | Plan | Status | Reason |
|---|---|---|---|
| Blocked by | `20260623-logitest-shared-docker-compose` | in-progress | Compose foundation exists but Docker daemon verification was blocked; new services depend on the stack shape. |
| Builds on | `20260623-logitest-api-logs-import-list` | completed | Provides log/session API patterns and mock fallback. |
| Builds on | `20260624-logitest-behavior-analysis-journey-persona-api` | completed | Provides behavior mining module to refocus on journey types and chaining. |
| Builds on | `20260624-logitest-script-generator-artifacts` | completed | Provides script artifact persistence and renderers. |
| Builds on | `20260624-logitest-test-case-generation-backend` | completed | Provides generated test case JSON specs. |
| Blocks / supersedes assumptions in | `20260624-logitest-test-execution-report-api` | pending | That plan targets mock staging routes inside FastAPI; this roadmap should redirect execution toward the real demo backend once available. |

## Requirements

- A local demo system exists and can generate realistic logs for login, search, cart/order, and optional payment callback.
- Logs are written to Elasticsearch with `session_id`, `trace_id`, `request_id`, request/response data, status, response time, service name, and environment.
- Platform can import logs from Elasticsearch and normalize them into PostgreSQL while retaining the existing mock JSON fallback.
- Journey analysis classifies `LOGIN_FLOW`, `SEARCH_FLOW`, `ORDER_CREATION_FLOW`, and optionally `ASYNC_PAYMENT_FLOW`.
- Analyzer detects output-input chaining, especially `orderId` from `POST /api/orders` used by `GET /api/orders/:id`.
- Generated test code defaults to Jest + Supertest and supports extracted variables.
- Execution runs generated specs against the demo backend, compares actual responses with golden responses, and persists reports.
- Dashboard shows the full pipeline from raw logs to regression report.

## Non-Goals

- No Kubernetes.
- No real microservice split for the demo system.
- No RabbitMQ/Kafka unless implementing optional async payment flow after core demo is stable.
- No local LLM stack.
- No full-body response comparison by default.
- No authentication/authorization for LogiTest AI dashboard in this round.
- No production hardening, cloud deployment, or CI/CD gate unless the MVP demo is already complete.

## Proposed Phases

| Phase | Name | Status |
|---|---|---|
| 1 | [Realign project documentation and scope](./phase-01-realign-project-documentation-and-scope.md) | Completed |
| 2 | [Create Express e-commerce demo backend](./phase-02-create-express-ecommerce-demo-backend.md) | Completed |
| 3 | [Add Elasticsearch logging path and Compose services](./phase-03-add-elasticsearch-logging-path-and-compose-services.md) | Completed |
| 4 | [Import Elasticsearch logs into FastAPI platform](./phase-04-import-elasticsearch-logs-into-fastapi-platform.md) | Pending |
| 5 | [Refocus journey analyzer on flows and chaining](./phase-05-refocus-journey-analyzer-on-flows-and-chaining.md) | Pending |
| 6 | [Make Jest/Supertest generation the primary output](./phase-06-make-jest-supertest-generation-the-primary-output.md) | Pending |
| 7 | [Rework execution and regression reporting against the demo backend](./phase-07-rework-execution-and-regression-reporting-against-demo-backend.md) | Pending |
| 8 | [Build dashboard and demo script](./phase-08-build-dashboard-and-demo-script.md) | Pending |

## Acceptance Criteria

- `docker compose up --build` starts Postgres, Elasticsearch, FastAPI API, Next.js web, and demo e-commerce backend when Docker is available.
- Demo script/Postman collection creates at least three flows: login, search, order creation with chaining.
- Elasticsearch contains structured logs from the demo backend.
- `POST /api/logs/import-elasticsearch` imports those logs into PostgreSQL.
- Existing `POST /api/logs/import-mock` remains usable as demo fallback.
- `POST /api/behavior/analyze` persists journeys with explicit flow type and chaining metadata.
- `POST /api/test-generation/generate` defaults to Jest + Supertest output.
- Generated Jest/Supertest code replays a journey in order and reuses extracted variables.
- `POST /api/execution/test-cases/{id}/run` executes against the demo backend target URL and stores `test_runs`.
- Regression comparator ignores dynamic fields and reports status/schema/business-field/response-time differences.
- Dashboard can walk the defense script: import logs, analyze journey, view chaining, generate test, run test, show pass/fail, show regression.
- Backend tests and frontend lint/build checks pass or have documented environment blockers.

## Validation Commands

Run from `D:\ViettelDigitalTalent\LogiTest\logitest-ai`:

```powershell
npm install
npm run build --workspace @logitest/shared
npm run build --workspace web
docker compose config
docker compose up --build
```

Run from `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`:

```powershell
python -m pytest
```

Run demo smoke checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:3001/health
Invoke-RestMethod http://localhost:9200
```

## Risks

- Docker Desktop may be unavailable locally, as previous plans already hit a daemon blocker. Keep unit tests and `docker compose config` as partial verification, but do not claim end-to-end demo readiness until Compose actually runs.
- Elasticsearch adds memory/startup cost. Mitigation: keep mock JSON fallback and document how to demo without ES if needed.
- Existing execution plan targets mock staging routes inside FastAPI, which is now less compelling. Mitigation: update execution work to use the Express demo backend as the target.
- Chaining detection can overfit to `orderId`. Mitigation: implement generic recursive field matching but document `orderId` as the MVP proof case.
- Dashboard scope can balloon. Mitigation: one operational dashboard with tabs is enough; avoid marketing pages and decorative UI.

## CLI Note

`ck` is not available in this environment (`ck` command not found). This plan is written manually using the repository's existing plan structure.
