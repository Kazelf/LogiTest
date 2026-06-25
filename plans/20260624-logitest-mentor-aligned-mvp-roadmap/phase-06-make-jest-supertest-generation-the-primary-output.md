---
phase: 6
title: "Make Jest/Supertest generation the primary output"
status: completed
priority: P1
effort: "1d"
dependencies: ["phase-05"]
---

# Phase 06: Make Jest/Supertest Generation The Primary Output

## Overview

Change the generator from Playwright-first artifacts to Jest + Supertest API regression tests that preserve request order and use extracted variables.

## Requirements

- Functional: Default generation framework is `jest_supertest`.
- Functional: Rendered tests support variable extraction and injection.
- Functional: Assertions cover status, schema keys, stable business fields, and response time threshold.
- Functional: Dynamic fields are not compared by default.
- Non-functional: Generated code should be readable enough to show in the dashboard.

## Architecture

The generated artifact remains persisted in `test_case_artifacts`, but the primary demo artifact should be:

```text
generated-tests/jest/<journey-name>.spec.ts
```

Generated code should use `request(baseURL)` and local variables:

```ts
const createOrder = await request(baseURL).post("/api/orders").send(payload);
const orderId = createOrder.body.orderId;
const orderDetail = await request(baseURL).get(`/api/orders/${orderId}`);
```

## Related Code Files

- Modify: `logitest-ai/apps/api/app/modules/test_generation/schemas.py`
- Modify: `logitest-ai/apps/api/app/modules/test_generation/service.py`
- Modify: `logitest-ai/apps/api/app/modules/test_generation/renderers.py`
- Modify: `logitest-ai/apps/api/tests/test_test_generation_service.py`
- Modify: `logitest-ai/apps/api/tests/test_test_generation_renderers.py`
- Modify: `logitest-ai/apps/api/tests/test_test_generation_api.py`

## Implementation Steps

1. Change `GenerateTestCaseRequest.frameworks` default to `[JEST_SUPERTEST]`.
2. Include chaining metadata from `journeys.steps` in generated test case steps.
3. Update Jest renderer to emit extraction variables.
4. Update endpoint/payload interpolation for later steps.
5. Add response-time and stable business-field assertion support.
6. Keep Playwright and Mocha renderers available as optional artifacts.

## Success Criteria

- [x] API generation without explicit framework returns a Jest + Supertest artifact.
- [x] Generated Jest code extracts `orderId` from create-order response.
- [x] Generated Jest code uses extracted `orderId` in order-detail request.
- [x] Existing Playwright/Mocha tests continue passing where applicable.
- [x] Generated tests do not assert full dynamic bodies by default.

## Risk Assessment

Renderer logic can become string-template spaghetti. Keep helper functions small and cover generated snippets with focused tests.
