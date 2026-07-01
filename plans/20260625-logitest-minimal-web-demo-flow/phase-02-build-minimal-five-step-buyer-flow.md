---
phase: 2
title: "Build minimal five-step buyer flow"
status: completed
priority: P1
effort: "4h"
dependencies: ["phase-01"]
---

# Phase 02: Build Minimal Five-Step Buyer Flow

## Overview

Add a `/demo` route in the Next.js app that lets a user complete a visible e-commerce journey. The page should be plain and reliable, prioritizing clear API calls over visual polish.

## Requirements

- Functional: Render Login, Product Search, Product Detail/Cart, Checkout, and Order Result steps.
- Functional: Use default demo credentials and search keyword to speed up presentation.
- Functional: Persist one session id and one trace id for the whole flow.
- Functional: Use the returned `userId`, product id, cart data, and order id from real API responses.
- Functional: Show enough request/result status to prove the flow is calling backend APIs.
- Non-functional: Keep implementation local to the `/demo` route and simple React state.

## Architecture

Add:

```text
apps/web/src/app/demo/page.tsx
```

Recommended UI state:

```text
step: login | search | product | checkout | result
context: { sessionId, traceId, userId? }
loginResult
products
selectedProduct
cart
order
orderDetail
error
busyAction
```

Use one page with small internal components if that is faster. Avoid a new state library.

## Related Code Files

- Create: `logitest-ai/apps/web/src/app/demo/page.tsx`
- Optionally create: `logitest-ai/apps/web/src/app/demo/components/*.tsx` only if the single file becomes hard to read.

## Implementation Steps

1. Create `/demo` route with a simple layout and step indicator.
2. Generate `sessionId` and `traceId` once when the page loads.
3. Implement login form with defaults `buyer_001` and `password123`.
4. Implement product search form with default `headphones`.
5. Render returned products and allow selecting one product.
6. Fetch product detail before moving to detail/cart step.
7. Implement add-to-cart and cart display.
8. Implement checkout by creating an order from current cart.
9. Implement result screen by fetching order detail with the returned `orderId`.
10. Show current session/trace ids on the page for demo explanation.

## Success Criteria

- [ ] `/demo` loads without requiring existing dashboard data.
- [ ] User can complete login -> search -> detail -> add cart -> checkout -> order result.
- [ ] No order id is hard-coded.
- [ ] UI exposes session id and trace id used for log correlation.
- [ ] Browser-visible errors are clear when demo backend is offline.

## Risk Assessment

Keep this as a demo producer, not a full shopping app. The temptation to style and feature-build is the main risk; resist it unless it directly improves the defense story.
