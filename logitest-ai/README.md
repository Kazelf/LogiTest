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
Postman / demo script
        |
        v
demo-system/ Express e-commerce backend
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

- `demo-system`: planned Express.js e-commerce backend used as the system under test.
- `apps/web`: Next.js frontend dashboard.
- `apps/api`: Python FastAPI backend API organized as a modular monolith.
- `packages/shared`: shared TypeScript schemas and utilities.
- `mock-data`: fallback JSON logs for demo safety.
- `database`: PostgreSQL schema and migrations.
- `scripts`: local automation scripts for import/demo tasks.
- `generated-tests`: generated API test artifacts.

## Demo Flow

The intended defense demo flow is:

1. Start the local stack with Docker Compose.
2. Run a Postman collection or demo script against `demo-system`.
3. Demo backend writes structured logs to Elasticsearch.
4. Import Elasticsearch logs into LogiTest AI.
5. Analyze journeys and show login/search/order flows.
6. Show API chaining, especially `POST /api/orders` -> `GET /api/orders/:id`.
7. Generate Jest + Supertest API tests.
8. Run generated tests against the demo backend.
9. Show pass/fail execution result.
10. Enable regression mode in the demo backend.
11. Run tests again and show the regression report.

## Current Repository State

Implemented foundation:

- `apps/web`: Next.js app scaffold.
- `apps/api`: FastAPI app scaffold and current backend modules.
- `demo-system`: Express e-commerce modular monolith with login, product, cart, order, payment, request context, and structured console logging.
- `packages/shared`: shared TypeScript/Zod schema package.
- `database/migrations/001_init_logitest_schema.sql`: PostgreSQL schema for sessions, logs, journeys, test cases, artifacts, and runs.
- `mock-data/logs.json`: fallback e-commerce-like sample logs.
- `docker-compose.yml`: current stack with `web`, `api`, and `database`.

Planned next components:

- Elasticsearch service in Docker Compose.
- Elasticsearch import endpoint.
- Journey chaining metadata.
- Jest + Supertest as default generated artifact.
- Execution/reporting against the demo backend.
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

Run the demo e-commerce backend:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
npm.cmd start --workspace demo-system
```

Run the demo backend tests:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
npm.cmd run test:demo
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

Target Docker stack will also expose:

- Demo backend: `http://localhost:3001`
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
- `ELASTICSEARCH_URL`: Elasticsearch URL from API/demo containers.
- `DEMO_BACKEND_URL`: demo e-commerce backend URL.
- `STAGING_API_BASE_URL`: target URL for generated test execution.
- `DEMO_LOG_INDEX`: Elasticsearch index for demo backend logs.
- `REGRESSION_MODE`: optional demo backend toggle for intentional regression.

## Implementation Plan

Current mentor-aligned roadmap:

```text
D:\ViettelDigitalTalent\LogiTest\plans\20260624-logitest-mentor-aligned-mvp-roadmap\plan.md
```
