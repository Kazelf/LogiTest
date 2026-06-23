# LogiTest AI

AI-driven behavioral regression testing platform.

## Architecture

This MVP uses a hybrid architecture:

- LogiTest AI Platform: modular monolith for fast local development and demo.
- Demo Target System: microservice simulation used as the system under test.

## Main Components

- `apps/web`: Next.js frontend dashboard.
- `apps/api`: Python FastAPI backend API organized as a modular monolith.
- `services/ai-engine`: behavior analysis and test generation service/module.
- `packages/shared`: shared types, schemas, and utilities.
- `target-system`: mock microservices that generate realistic cross-service behavior and logs.
- `docker`: optional local infrastructure configuration.
- `scripts`: local automation scripts for seed/import/demo tasks.
- `docs`: project-specific technical notes.

## Target System Services

- `target-system/gateway`: API gateway entrypoint for demo user flows.
- `target-system/auth-service`: login, logout, and user session behavior.
- `target-system/product-service`: product search and product detail behavior.
- `target-system/order-service`: cart, order, and checkout behavior.
- `target-system/payment-service`: payment simulation behavior.

The target system is intentionally separate from the LogiTest AI platform so the demo can show a realistic microservice system being tested, while the testing platform remains simple and maintainable for the MVP.

## Local Development

Run the frontend dashboard:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\web
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

## Workspace And Docker Development

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

Run the Docker development stack:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose up --build
```

The Docker stack exposes:

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- PostgreSQL: `localhost:5432`, database `logitest_ai`, user `logitest`, password `logitest`

Stop the Docker development stack:

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
docker compose down
```

## Current Status

Task 1.1 is complete: monorepo structure has been created.
Task 1.2 is complete: Next.js frontend app has been created in `apps/web`.
Task 1.3 is complete: FastAPI backend app has been created in `apps/api`.
Task 1.4 is complete: shared TypeScript and Zod schema package has been created in `packages/shared`.
Task 1.5 is complete: development Dockerfiles have been created for `apps/web` and `apps/api`.
Task 1.6 is complete: Docker Compose stack has been created with `web`, `api`, and `database`.
