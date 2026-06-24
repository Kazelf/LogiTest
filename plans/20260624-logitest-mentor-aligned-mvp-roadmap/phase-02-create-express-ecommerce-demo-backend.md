---
phase: 2
title: "Create Express e-commerce demo backend"
status: completed
priority: P1
effort: "1.5d"
dependencies: ["phase-01"]
---

# Phase 02: Create Express E-Commerce Demo Backend

## Overview

Add a real system under test that can generate user behavior logs. This should be an Express modular monolith, not a real microservice fleet.

## Requirements

- Functional: Provide login, product search, product detail, cart, order creation, order detail, and optional payment endpoints.
- Functional: Provide deterministic seed data for repeatable demo/test generation.
- Functional: Return stable response shapes with enough fields for golden response comparison.
- Functional: Expose a deliberate regression toggle for defense demo.
- Non-functional: Keep state simple and local; in-memory state or a small JSON-backed store is acceptable for MVP.

## Architecture

Suggested structure:

```text
logitest-ai/demo-system/
  package.json
  Dockerfile
  src/
    app.js
    server.js
    data/seed.js
    modules/
      auth/
      products/
      cart/
      orders/
      payments/
    middlewares/
      request-context.middleware.js
      logging.middleware.js
    shared/
      response.js
      logger.js
```

API path conventions should align with existing classifier expectations where practical:

- `POST /api/auth/login`
- `GET /api/products?keyword=headphones`
- `GET /api/products/:id`
- `GET /api/cart`
- `POST /api/cart/items`
- `POST /api/orders`
- `GET /api/orders/:id`
- optional `POST /api/payments`
- optional `POST /api/payment-callback`

## Related Code Files

- Create: `logitest-ai/demo-system/package.json`
- Create: `logitest-ai/demo-system/Dockerfile`
- Create: `logitest-ai/demo-system/src/**`
- Create: `logitest-ai/demo-system/postman/**` or `logitest-ai/scripts/simulate_demo_flow.*`

## Implementation Steps

1. Scaffold a small Express app with JSON middleware and `/health`.
2. Add seed users, products, carts, and orders.
3. Implement auth/product/cart/order routes.
4. Make `POST /api/orders` return an `orderId` and `GET /api/orders/:id` consume it.
5. Add `REGRESSION_MODE=true` behavior, for example returning an incorrect order status or missing business field.
6. Add a demo script or Postman collection that performs login -> search -> cart/order -> order detail.
7. Add unit/smoke tests if the demo-system test runner is introduced.

## Success Criteria

- [x] `npm start` in `demo-system` serves `/health`.
- [x] Demo flow can be run repeatedly and produces deterministic business responses.
- [x] Order creation flow proves output-input chaining with `orderId`.
- [x] Regression toggle changes a business field or schema in an obvious way.

## Risk Assessment

Main risk: overbuilding a business app. Avoid user registration, inventory persistence, real auth, payment providers, or database dependency unless needed for the demo.
