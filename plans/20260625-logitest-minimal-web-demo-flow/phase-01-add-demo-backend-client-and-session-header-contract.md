---
phase: 1
title: "Add demo backend client and session header contract"
status: completed
priority: P1
effort: "2h"
dependencies: []
---

# Phase 01: Add Demo Backend Client And Session Header Contract

## Overview

Create a small frontend client dedicated to the Express demo backend. Keep it separate from the existing FastAPI platform client so the UI can clearly call the real system under test.

## Requirements

- Functional: Add a browser-safe API client for demo backend endpoints.
- Functional: Read demo backend base URL from `NEXT_PUBLIC_DEMO_API_BASE_URL`, defaulting to `http://localhost:3001`.
- Functional: Support stable correlation headers: `x-session-id`, `x-trace-id`, `x-request-id`, `x-user-id`.
- Functional: Type the response envelope used by `demo-system`.
- Non-functional: Do not modify the existing FastAPI dashboard API client except for optional links/imports if needed later.

## Architecture

Add a new file:

```text
apps/web/src/app/lib/demo-api.ts
```

Proposed functions:

```text
login(credentials, context)
searchProducts(keyword, context)
getProduct(productId, context)
getCart(context)
addCartItem(productId, quantity, context)
createOrder(context)
getOrder(orderId, context)
```

The `context` object should carry:

```text
sessionId
traceId
requestId
userId optional
```

## Related Code Files

- Create: `logitest-ai/apps/web/src/app/lib/demo-api.ts`
- Modify: `logitest-ai/apps/web/.env.example`
- Modify: `logitest-ai/docker-compose.yml`

## Implementation Steps

1. Define `DEMO_API_BASE_URL` from `NEXT_PUBLIC_DEMO_API_BASE_URL`.
2. Implement a generic `demoRequest<T>()` helper.
3. Parse the demo backend response envelope `{ success, data, error, meta }`.
4. Throw useful errors for non-2xx responses and `success: false`.
5. Add typed helpers for auth, products, cart, and orders.
6. Add `NEXT_PUBLIC_DEMO_API_BASE_URL=http://localhost:3001` to frontend env examples and Docker Compose `web` service.

## Success Criteria

- [ ] Demo API client is independent from `apps/web/src/app/lib/api.ts`.
- [ ] Client sends correlation headers on every request.
- [ ] Client supports all endpoints needed for the buyer flow.
- [ ] Missing or failed backend responses surface readable errors in the UI.
- [ ] Environment variable is documented in `.env.example`.

## Risk Assessment

CORS may block browser requests. Do not add CORS preemptively unless browser smoke testing confirms it. If needed, add a narrow allow-list for `http://localhost:3000` in `demo-system`.
