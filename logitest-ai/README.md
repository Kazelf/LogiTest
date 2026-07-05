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

## Quick Start

Use this path for the normal demo. From the repository root, start the combined stack:

```powershell
cd D:\ViettelDigitalTalent\LogiTest
docker compose up --build
```

This builds one combined app container for LogiTest AI and ShopLite. PostgreSQL and Elasticsearch still run as dependency services.

Open the apps:

- LogiTest dashboard: `http://localhost:3000`
- ShopLite frontend: `http://localhost:5173`
- ShopLite API: `http://localhost:4000`
- FastAPI health check: `http://localhost:8000/health`

Generate fresh ShopLite traffic from `http://localhost:5173`, then return to the LogiTest dashboard and run:

```text
Import ShopLite -> Analyze -> select journey -> Generate Jest -> select test case -> Run Test -> Report
```

If the ShopLite import has no records, use `Import Mock` as the fallback path.

## Reset Analyzed Journeys

After changing journey classification rules, old rows in `journeys` can remain because journeys are upserted by `name`. If the dashboard still shows long journey names such as `unknown > unknown > ...`, clear the analyzed journey data once, then run `Analyze` again.

### Clear only journeys

Use this when you only want to remove old analyzed journeys. Existing test cases are kept, but their `journey_id` becomes `NULL`.

```powershell
cd D:\ViettelDigitalTalent\LogiTest
docker compose exec postgres psql -U logitest -d logitest_ai -c "DELETE FROM journeys;"
```

### Clear journeys and generated test cases

Use this before a clean demo when old generated tests were created from noisy journeys.

```powershell
cd D:\ViettelDigitalTalent\LogiTest
docker compose exec postgres psql -U logitest -d logitest_ai -c "DELETE FROM test_case_artifacts; DELETE FROM test_cases; DELETE FROM journeys;"
```

Then run `Analyze` again in the dashboard. You do not need to delete logs or sessions unless you want a full data reset.

## Current Repository State

Implemented foundation:

- `apps/web`: Next.js operational dashboard for the logs-to-regression-report demo.
- `apps/api`: FastAPI app scaffold with mock JSON and Elasticsearch log ingestion.
- `../shoplite`: Express + React mini e-commerce system with realistic journeys, JSONL request logs, and regression cases.
- `packages/shared`: shared TypeScript/Zod schema package.
- `database/migrations/001_init_logitest_schema.sql`: PostgreSQL schema for sessions, logs, journeys, test cases, artifacts, and runs.
- `mock-data/logs.json`: fallback e-commerce-like sample logs.
- Root `../docker-compose.yml`: combined local stack with LogiTest AI, ShopLite, PostgreSQL, and Elasticsearch.

Completed MVP path:

- Journey chaining metadata.
- Jest + Supertest as default generated artifact.
- Execution/reporting against ShopLite.
- Operational dashboard replacing the default starter page.

## Local Development

The Docker quick start above is the recommended route for demos. Use this manual mode when you need to debug a single service.

### Install JavaScript dependencies

Install LogiTest workspace dependencies:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
npm install
```

Build the shared TypeScript schemas:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
npm run build --workspace @logitest/shared
```

Install ShopLite dependencies:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\shoplite\server
npm install

cd D:\ViettelDigitalTalent\LogiTest\shoplite\client
npm install
```

### Start infrastructure

Start the root Docker stack for PostgreSQL and Elasticsearch:

```powershell
cd D:\ViettelDigitalTalent\LogiTest
docker compose up -d postgres elasticsearch
```

### Run ShopLite manually

Prepare the ShopLite database:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\shoplite\server
$env:DATABASE_URL="postgresql://shoplite:shoplite@localhost:5433/shoplite?schema=public"
npm.cmd run prisma:generate
npm.cmd run prisma:migrate
npm.cmd run seed
```

Run the ShopLite backend and frontend:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\shoplite\server
$env:DATABASE_URL="postgresql://shoplite:shoplite@localhost:5433/shoplite?schema=public"
$env:ENABLE_ELASTICSEARCH_LOGGING="true"
$env:ELASTICSEARCH_URL="http://localhost:9200"
npm.cmd run dev

cd D:\ViettelDigitalTalent\LogiTest\shoplite\client
npm.cmd run dev
```

### Run LogiTest manually

Run the FastAPI backend:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:DATABASE_URL="postgresql://logitest:logitest@localhost:5432/logitest_ai"
$env:ELASTICSEARCH_URL="http://localhost:9200"
$env:SHOPLITE_LOG_PATH="D:\ViettelDigitalTalent\LogiTest\shoplite\server\logs\request-logs.jsonl"
$env:STAGING_API_BASE_URL="http://localhost:4000"
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Run the frontend dashboard:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\web
npm.cmd run dev
```

### Docker services

Run the combined Docker stack from the repository root:

```powershell
cd D:\ViettelDigitalTalent\LogiTest
docker compose up --build
```

Current Docker services expose:

- LogiTest web: `http://localhost:3000`
- LogiTest API health: `http://localhost:8000/health`
- LogiTest PostgreSQL: `localhost:5432`, database `logitest_ai`, user `logitest`, password `logitest`
- Elasticsearch: `http://localhost:9200`
- ShopLite frontend: `http://localhost:5173`
- ShopLite API: `http://localhost:4000`
- ShopLite PostgreSQL: `localhost:5433`, database `shoplite`, user `shoplite`, password `shoplite`

Stop the Docker development stack:

```powershell
cd D:\ViettelDigitalTalent\LogiTest
docker compose down
```

### Tests

Run backend tests:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
$env:PYTHONPATH="D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api"
.\.venv\Scripts\python -m pytest
```

Run ShopLite tests:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\shoplite\server
npm.cmd test
```

Run the payment regression demo test:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\shoplite\server
npm.cmd run test:regression
```

## Environment Variables

Key local variables:

- `NEXT_PUBLIC_API_BASE_URL`: FastAPI platform URL for the dashboard.
- `DATABASE_URL`: PostgreSQL connection string.
- `ELASTICSEARCH_URL`: Elasticsearch URL from API containers.
- `SHOPLITE_LOG_PATH`: JSONL file path for the ShopLite log bridge.
- `STAGING_API_BASE_URL`: target URL for generated test execution, usually ShopLite at `http://localhost:4000`.
- `DEMO_LOG_INDEX`: Elasticsearch index for imported demo logs.
