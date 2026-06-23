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

## Current Status

Task 1.1 is complete: monorepo structure has been created. Application code, Docker setup, database schema, and APIs will be added in later tasks.
