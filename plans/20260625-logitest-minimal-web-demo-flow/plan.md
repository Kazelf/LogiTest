---
title: "Minimal web demo flow for real backend log generation"
description: "Add a small user-facing Next.js flow that calls the Express demo backend APIs so defense demos can show real user actions producing real structured logs before Elasticsearch import, journey analysis, test generation, and regression execution."
status: in-progress
priority: P1
effort: 1d
branch: master
tags: [frontend, demo-flow, nextjs, demo-system, elasticsearch, logs]
blockedBy: [20260624-logitest-mentor-aligned-mvp-roadmap]
blocks: []
created: 2026-06-25
scope: project
source: skill:plan
phases:
  - id: phase-01
    title: "Add demo backend client and session header contract"
    status: completed
  - id: phase-02
    title: "Build minimal five-step buyer flow"
    status: completed
  - id: phase-03
    title: "Connect demo flow to pipeline handoff"
    status: completed
  - id: phase-04
    title: "Verify browser flow and log generation"
    status: in-progress
---

# Minimal Web Demo Flow Plan

## Goal

Add a very small frontend path that makes the MVP story visible:

```text
User thao tác trên web
  -> Next.js frontend calls Express demo backend
  -> demo backend writes structured logs
  -> Elasticsearch stores logs
  -> LogiTest imports logs
  -> AI analyzes journeys
  -> generates Jest/Supertest scripts
  -> runs regression tests
```

This plan intentionally does not replace the existing operational dashboard in `apps/web/src/app/page.tsx`. The dashboard already imports logs, analyzes journeys, generates tests, runs tests, and shows reports. The new work should add a separate minimal demo flow, likely at `/demo`, that produces real backend logs before the user returns to the dashboard pipeline.

## Codebase Context

- Monorepo: `D:\ViettelDigitalTalent\LogiTest\logitest-ai`.
- Existing dashboard frontend: `apps/web` using Next.js 16, React 19, Tailwind CSS.
- Current dashboard entry: `apps/web/src/app/page.tsx`; keep it as the pipeline dashboard.
- Existing platform API client: `apps/web/src/app/lib/api.ts`, pointed at FastAPI by `NEXT_PUBLIC_API_BASE_URL`.
- Existing demo backend: `demo-system`, Express modular monolith on port `3001`.
- Demo backend endpoints already exist:
  - `POST /api/auth/login`
  - `GET /api/products?keyword=...`
  - `GET /api/products/:productId`
  - `GET /api/cart`
  - `POST /api/cart/items`
  - `POST /api/orders`
  - `GET /api/orders/:orderId`
- Demo backend logging middleware already records structured logs with `session_id`, `trace_id`, `request_id`, `user_id`, request payload, response body, status, and latency.
- Docker Compose already starts `web`, `api`, `demo-backend`, `database`, and `elasticsearch`.

## Requirements

- Add a minimal user-facing web flow with 4-5 visible screens:
  - Login
  - Product search
  - Product detail/cart
  - Checkout
  - Order result
- Frontend must call the real Express demo backend, not FastAPI mock endpoints.
- Frontend must preserve one `x-session-id` and one `x-trace-id` across the whole buyer flow.
- After login, frontend must send `x-user-id` on later requests.
- The order result screen must use the real `orderId` returned by `POST /api/orders` when calling `GET /api/orders/:orderId`.
- Keep UI intentionally simple and demo-readable. No production polish, no auth security hardening, no new state library.
- Keep the existing dashboard available for the downstream pipeline.

## Non-Goals

- No full e-commerce frontend.
- No registration, profile, admin, payment provider, or inventory management.
- No redesign of the dashboard.
- No changes to journey mining, test generation, execution, or report algorithms unless a small frontend handoff needs a link/button.
- No fake logs written from the browser. Logs must come from backend middleware.

## Proposed Architecture

```text
apps/web/src/app/demo/page.tsx
  -> imports demo client
  -> manages five-step buyer flow in local React state
  -> calls demo-system API with stable correlation headers

apps/web/src/app/lib/demo-api.ts
  -> DEMO_API_BASE_URL from NEXT_PUBLIC_DEMO_API_BASE_URL or http://localhost:3001
  -> typed request helper for demo backend response envelope
  -> auth/products/cart/orders functions
```

Recommended environment variable:

```text
NEXT_PUBLIC_DEMO_API_BASE_URL=http://localhost:3001
```

Do not reuse `API_BASE_URL` from `lib/api.ts` because that points to the FastAPI platform API. The demo frontend needs a distinct client for the system under test.

## Demo Data Defaults

Use existing seed data:

- Username: `buyer_001`
- Password: `password123`
- Suggested search keyword: `headphones`
- Expected product: `prod-headphone-001`
- Expected user id: `user-buyer-001`

Generate IDs once per browser demo session:

```text
session_id = session-web-demo-{timestamp}
trace_id = trace-web-checkout-{timestamp}
request_id = req-web-{step}-{timestamp}
```

One stable session and trace across the journey makes reconstruction easier. A unique request id per request keeps logs production-like.

## Acceptance Criteria

- Opening `/demo` shows a login screen with default demo credentials.
- Login calls `POST /api/auth/login` on the demo backend and stores `userId`.
- Product search calls `GET /api/products?keyword=headphones` and renders real returned products.
- Product detail calls `GET /api/products/:id`.
- Add to cart calls `POST /api/cart/items`.
- Checkout calls `GET /api/cart` and `POST /api/orders`.
- Order result calls `GET /api/orders/:orderId` using the order id returned by the create order response.
- Every demo backend request includes the same `x-session-id` and `x-trace-id`.
- Authenticated steps include `x-user-id`.
- Demo backend console or Elasticsearch shows structured logs for the full flow.
- Existing dashboard still builds and remains reachable at `/`.
- Frontend lint/build pass, or blockers are documented with exact errors.

## Risks

- **CORS may block browser calls to `localhost:3001`.** Mitigate by adding narrow CORS support to `demo-system` only if browser testing proves it is required.
- **Next.js client-side env can be missing in Docker.** Mitigate with default `http://localhost:3001` for local browser demos and add `NEXT_PUBLIC_DEMO_API_BASE_URL` to Compose/web env.
- **Existing dashboard page is already dense.** Avoid merging demo flow into `/`; use `/demo` to prevent regression.
- **Cart/order state is in-memory.** This is acceptable for MVP; restarting demo backend resets data.
- **Repeated order IDs may differ after multiple runs.** The frontend must use returned `orderId`, not hard-code `order-001`.

## Validation Commands

Run from `D:\ViettelDigitalTalent\LogiTest\logitest-ai`:

```powershell
npm run build --workspace @logitest/shared
npm run build --workspace web
npm run lint --workspace web
docker compose config
```

Manual smoke when services are running:

```powershell
Invoke-RestMethod http://localhost:3001/health
Invoke-RestMethod http://localhost:3000/demo
Invoke-RestMethod http://localhost:9200
```

Browser smoke:

1. Open `http://localhost:3000/demo`.
2. Login with `buyer_001` / `password123`.
3. Search `headphones`.
4. Open product detail.
5. Add to cart.
6. Checkout and create order.
7. Confirm order result loads by returned `orderId`.
8. Import Elasticsearch logs from the dashboard and verify a new session appears.

## Phase Summary

| Phase | Name | Output |
|---|---|---|
| 1 | Add demo backend client and session header contract | Typed demo API client and env config |
| 2 | Build minimal five-step buyer flow | `/demo` route with login/search/detail/cart/checkout/result |
| 3 | Connect demo flow to pipeline handoff | Clear path back to dashboard import/analyze/generate/run |
| 4 | Verify browser flow and log generation | Build/lint plus manual log-generation proof |
