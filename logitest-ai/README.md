# LogiTest AI

AI-driven behavioral regression testing platform.

## MVP Direction

This MVP follows the mentor-aligned scope:

- Demo system under test: **Express.js e-commerce modular monolith**.
- Log source: **Elasticsearch local** as the primary source.
- Fallback source: `mock-data/logs.json`.
- LogiTest AI platform: **FastAPI modular monolith**.
- Dashboard: **Next.js**.
- Test generation: **Jest + Supertest** API regression tests first.
- Future work: Playwright, real microservices, Kubernetes, advanced persona detection, and async callback flows.

## Architecture

```text
ShopLite user journey
        |
        v
shoplite/ Express e-commerce system
        |
        | structured API logs
        v
Elasticsearch local
        |
        v
apps/api FastAPI platform
        |
        v
PostgreSQL + generated test artifacts + test runs
        |
        v
apps/web Next.js dashboard
```

## Main Components

- `../shoplite`: Express + React e-commerce system used as the system under test.
- `apps/web`: Next.js frontend dashboard.
- `apps/api`: Python FastAPI backend API organized as a modular monolith.
- `packages/shared`: shared TypeScript schemas and utilities.
- `mock-data`: fallback JSON logs for demo safety.
- `database`: PostgreSQL schema and migrations.
- `scripts`: local automation scripts for import tasks.
- `generated-tests`: generated API test artifacts.

## Demo Flow

The intended defense demo flow is:

1. Start the local stack with Docker Compose.
2. Run user journeys against ShopLite.
3. ShopLite writes structured API logs.
4. Import Elasticsearch logs into LogiTest AI.
5. Analyze journeys and show login/search/order flows.
6. Show API chaining, especially `POST /api/orders` -> `GET /api/orders/:id`.
7. Generate Jest + Supertest API tests.
8. Run generated tests against ShopLite.
9. Show pass/fail execution result.
10. Enable ShopLite's regression bug toggle.
11. Run tests again and show the regression report.

### Defense Demo Script

Start the LogiTest stack, generate behavior in ShopLite, then drive the platform from the dashboard:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose up --build
```

In another terminal:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\shoplite
docker compose up -d

cd D:\ViettelDigitalTalent\LogiTest\shoplite\server
npm run dev

cd D:\ViettelDigitalTalent\LogiTest\shoplite\client
npm run dev
```

Open `http://localhost:3000`, then use:

```text
Import ShopLite -> Analyze -> select journey -> Generate Jest -> select test case -> Run Test -> Report
```

If ShopLite logs are not available yet, use `Import Mock` in the dashboard as the fallback demo path.

## Current Repository State

Implemented foundation:

- `apps/web`: Next.js operational dashboard for the logs-to-regression-report demo.
- `apps/api`: FastAPI app scaffold with mock JSON and Elasticsearch log ingestion.
- `../shoplite`: Express + React mini e-commerce system with realistic journeys, JSONL request logs, and regression cases.
- `packages/shared`: shared TypeScript/Zod schema package.
- `database/migrations/001_init_logitest_schema.sql`: PostgreSQL schema for sessions, logs, journeys, test cases, artifacts, and runs.
- `mock-data/logs.json`: fallback e-commerce-like sample logs.
- `docker-compose.yml`: current LogiTest stack with `web`, `api`, `database`, and `elasticsearch`.

Completed MVP path:

- Journey chaining metadata.
- Jest + Supertest as default generated artifact.
- Execution/reporting against ShopLite.
- Operational dashboard replacing the default starter page.

## Local Development

Install workspace dependencies from the monorepo root:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
npm install
```

Build the shared TypeScript schemas:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
npm run build --workspace @logitest/shared
```

Run the frontend dashboard:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\web
npm.cmd run dev
```

Run ShopLite backend and frontend:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\shoplite
docker compose up -d

cd D:\ViettelDigitalTalent\LogiTest\shoplite\server
npm.cmd run dev

cd D:\ViettelDigitalTalent\LogiTest\shoplite\client
npm.cmd run dev
```

Run the FastAPI backend:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Run backend tests:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
.\.venv\Scripts\python -m pytest
```

Run the current Docker development stack:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose up --build
```

Current Docker stack exposes:

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- PostgreSQL: `localhost:5432`, database `logitest_ai`, user `logitest`, password `logitest`
- ShopLite API: `http://localhost:4000`
- ShopLite frontend: `http://localhost:5173`
- Elasticsearch: `http://localhost:9200`

Stop the Docker development stack:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose down
```

## Environment Variables

Key local variables:

- `NEXT_PUBLIC_API_BASE_URL`: FastAPI platform URL for the dashboard.
- `DATABASE_URL`: PostgreSQL connection string.
- `ELASTICSEARCH_URL`: Elasticsearch URL from API containers.
- `SHOPLITE_LOG_PATH`: JSONL file path for the ShopLite log bridge.
- `STAGING_API_BASE_URL`: target URL for generated test execution, usually ShopLite at `http://localhost:4000`.
- `DEMO_LOG_INDEX`: Elasticsearch index for imported demo logs.

## Implementation Plan

Current mentor-aligned roadmap:

```text
D:\ViettelDigitalTalent\LogiTest\plans\20260624-logitest-mentor-aligned-mvp-roadmap\plan.md
```
