# LogiTest

LogiTest is an AI-driven behavioral regression testing platform for backend
APIs. It turns structured API logs into user journeys, generated API test
cases, executable Jest/Supertest scripts, test runs, and regression reports.

The repository contains both the testing platform and a demo system under test:

- **LogiTest AI**: a FastAPI API plus a Next.js dashboard for log ingestion,
  behavior mining, test generation, execution, and reporting.
- **ShopLite**: a React + Express e-commerce demo app that produces realistic
  backend request/response logs.

ShopLite is only the case study. The platform is designed to work with any
web-based product that can provide structured API logs with session, trace,
request, response, status, timing, and business-context fields.

## Why It Exists

Regression testing is hard to keep fresh when APIs, data states, and user flows
change quickly. Manual test suites often lag behind the behavior that users
actually perform in staging or production-like environments.

LogiTest uses backend logs as a source of testing knowledge:

```text
User activity in ShopLite
        |
        v
Structured API logs
        |
        v
Elasticsearch / JSONL ingestion
        |
        v
Session grouping + journey mining
        |
        v
Generated API test cases and Jest/Supertest scripts
        |
        v
Execution against staging target
        |
        v
Golden Response comparison and regression report
```

The goal is not to replace QA engineers. The goal is to help QA teams discover
important real-world journeys faster, generate runnable regression tests from
those journeys, and keep every test traceable back to the logs that created it.

## Core System Features

- **Structured log ingestion** from Elasticsearch, JSONL, and mock data.
- **PII-aware log normalization** for sensitive fields such as passwords,
  tokens, authorization headers, and user identifiers.
- **Session reconstruction** using `session_id`, `trace_id`, timestamps, API
  method, endpoint, payload, response body, and status code.
- **Behavior mining** that groups ordered API calls into meaningful journeys
  such as login, search/filter, cart, checkout, payment, and order detail.
- **Hybrid AI engine** that combines deterministic parsing/rules with optional
  Gemini-based behavior explanation.
- **API chaining detection** so generated tests can reuse values such as
  `product_id` or `order_id` from earlier responses in later requests.
- **Golden Response assertions** for status code, response schema, stable
  business fields, ignored dynamic fields, and response-time thresholds.
- **Jest/Supertest artifact generation** for runnable backend API regression
  tests.
- **Execution and reporting** with pass/fail status, actual response, diff
  output, ignored dynamic fields, severity, and trace/session provenance.
- **Demo evidence mode** for presenting the product even before live traffic is
  available.

## Creative Contribution

The main contribution is the log-to-regression pipeline: instead of asking QA to
write every regression case from requirements, LogiTest derives candidate tests
from behavior that already happened.

Key ideas from the report implemented or represented in the MVP:

- **Behavior-first testing**: user journeys are reconstructed from backend API
  logs, making test generation grounded in observed behavior.
- **Generic platform, specific demo**: e-commerce is used for clarity, but the
  pipeline applies to other domains with structured API logs.
- **Hybrid AI control**: rule-based parsing, masking, grouping, chaining, and
  comparison stay deterministic; Gemini is used only to explain journeys and
  assist with draft test descriptions.
- **Golden Response design**: tests do not compare entire responses blindly.
  Dynamic fields such as IDs, timestamps, tokens, totals that naturally change,
  and request IDs are ignored or handled separately, while business fields stay
  assertable.
- **Traceable test provenance**: reports can link a generated test back to the
  journey, session, and log evidence that produced it.
- **Human-in-the-loop QA workflow**: generated journeys and test cases are
  drafts for QA review before they become part of a formal regression suite.

## Repository Structure

```text
.
|-- docker-compose.yml          # full local demo stack
|-- Dockerfile                  # combined app image for LogiTest AI + ShopLite
|-- docker/                     # entrypoint and PostgreSQL init scripts
|-- logitest-ai/                # FastAPI API, Next.js dashboard, DB migrations
|-- shoplite/                   # React + Express e-commerce demo app
|-- scripts/traffic-generator/  # optional synthetic traffic helper
`-- reports/                    # generated/demo report artifacts
```

## Technology Stack

| Area | Technology | Role |
| --- | --- | --- |
| Dashboard | Next.js, React, TypeScript | QA-facing operational UI |
| Platform API | FastAPI, Python | Ingestion, mining, generation, execution, reports |
| Shared schemas | TypeScript package | Shared validation contracts |
| Demo app frontend | React + Vite | E-commerce UI for producing behavior |
| Demo app backend | Node.js + Express | System under test and structured log source |
| Test generation | Jest + Supertest | Generated backend API regression scripts |
| Databases | PostgreSQL | LogiTest metadata and ShopLite business data |
| Log storage | Elasticsearch | Searchable structured request/response logs |
| AI provider | Gemini API, optional | Journey explanation and draft assistance |
| Local runtime | Docker Compose | Reproducible demo environment |

## Quick Start With Docker

Requirement: Docker Desktop.

From the repository root:

```powershell
docker compose up --build
```

When the stack is ready:

| Service | URL |
| --- | --- |
| LogiTest dashboard | `http://localhost:3000` |
| LogiTest API health | `http://localhost:8000/health` |
| ShopLite frontend | `http://localhost:5173` |
| ShopLite API health | `http://localhost:4000/health` |
| Elasticsearch | `http://localhost:9200` |
| LogiTest PostgreSQL | `localhost:5432`, database `logitest_ai` |
| ShopLite PostgreSQL | `localhost:5433`, database `shoplite` |

The Docker stack creates both databases, runs migrations, seeds ShopLite demo
data, enables Elasticsearch logging, and starts the LogiTest dashboard,
LogiTest API, ShopLite API, and ShopLite frontend.

## Demo Flow

1. Open ShopLite at `http://localhost:5173`.
2. Sign in with a demo account such as
   `normal_buyer@example.com` / `Password123`.
3. Create e-commerce traffic: search products, view details, add to cart,
   checkout, pay, and view order details.
4. Open the LogiTest dashboard at `http://localhost:3000`.
5. Click `Run Full Pipeline`.
6. Review `Logs`, `Sessions`, `Journeys`, `Test Cases`, `Runs`, and `Report`.

Manual dashboard flow:

```text
Import from ES -> Analyze -> Generate Jest -> Run Test -> Report
```

For a presentation without live traffic, click `Load Demo Evidence`. It loads a
read-only snapshot and does not write to PostgreSQL.

## Demo Journeys

ShopLite includes realistic behavior paths:

- Normal buyer: login, search, product detail, cart, checkout, payment, order
  detail.
- Product browser: search, filter, sort, view product detail, no checkout.
- Returning buyer: existing cart, voucher, checkout, payment, order history.
- Hesitant buyer: repeated cart updates, removal, clear cart, empty checkout
  error.
- Voucher hunter: voucher failure, add more products, voucher success.
- Out-of-stock edge case: stock decreases before checkout.
- Payment regression: payment succeeds but order status remains
  `PENDING_PAYMENT`.

## Payment Regression Toggle

The main regression demo is controlled by:

```env
ENABLE_PAYMENT_REGRESSION_BUG=true
```

When enabled, ShopLite returns `payment_status = SUCCESS`, but the order remains
`PENDING_PAYMENT`. The generated or dedicated regression test expects the order
to become `PAID`, so the report highlights a high-risk business mismatch.

## Local Development

Start only the infrastructure:

```powershell
docker compose up -d postgres elasticsearch
```

### LogiTest API

```powershell
cd .\logitest-ai\apps\api
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:DATABASE_URL="postgresql://logitest:logitest@localhost:5432/logitest_ai"
$env:ELASTICSEARCH_URL="http://localhost:9200"
$env:STAGING_API_BASE_URL="http://localhost:4000"
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

### LogiTest Dashboard

```powershell
cd .\logitest-ai
npm install
npm run build --workspace @logitest/shared
npm run dev --workspace web
```

### ShopLite API

```powershell
cd .\shoplite\server
npm install
$env:DATABASE_URL="postgresql://shoplite:shoplite@localhost:5433/shoplite?schema=public"
$env:ENABLE_ELASTICSEARCH_LOGGING="true"
$env:ELASTICSEARCH_URL="http://localhost:9200"
npm run prisma:generate
npm run prisma:migrate
npm run seed
npm run dev
```

### ShopLite Frontend

```powershell
cd .\shoplite\client
npm install
npm run dev
```

## Tests

LogiTest API:

```powershell
cd .\logitest-ai\apps\api
$env:PYTHONPATH=(Get-Location).Path
.\.venv\Scripts\python -m pytest
```

ShopLite API:

```powershell
cd .\shoplite\server
npm test
```

Payment regression demo:

```powershell
cd .\shoplite\server
npm run test:regression
```

## Reset Local Data

Remove all PostgreSQL and Elasticsearch volumes:

```powershell
docker compose down -v
docker compose up --build
```

Clear only analyzed LogiTest journeys and generated tests:

```powershell
docker compose exec postgres psql -U logitest -d logitest_ai -c "DELETE FROM test_case_artifacts; DELETE FROM test_cases; DELETE FROM journeys;"
```

## Key Environment Variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URL for the LogiTest API |
| `SHOPLITE_DATABASE_URL` | PostgreSQL URL for ShopLite |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint |
| `DEMO_LOG_INDEX` | Log index used by LogiTest ingestion |
| `SHOPLITE_LOG_INDEX` | Log index written by ShopLite |
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI base URL used by the dashboard |
| `STAGING_API_BASE_URL` | Target API for generated tests, usually ShopLite |
| `ENABLE_ELASTICSEARCH_LOGGING` | Enables ShopLite log indexing |
| `ENABLE_PAYMENT_REGRESSION_BUG` | Enables the intentional payment regression |
| `GEMINI_API_KEY` | Optional Gemini key; without it, rule-based fallback is used |

## More Documentation

- `logitest-ai/README.md`: MVP architecture, dashboard flow, and defense demo.
- `logitest-ai/apps/api/README.md`: FastAPI endpoints and smoke commands.
- `logitest-ai/database/README.md`: PostgreSQL schema and migrations.
- `shoplite/README.md`: demo accounts, journeys, logs, and regression case.
