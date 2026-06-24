---
phase: 1
title: "Create mock staging API"
status: pending
priority: P2
effort: "1.5h"
dependencies: []
---

# Phase 01: Create Mock Staging API

## Overview

Add mock staging routes under the same FastAPI app so the executor has a predictable target system for MVP replay tests.

## Requirements

- Functional: expose endpoints matching current mock log/test case flows.
- Functional: return stable JSON bodies and realistic status codes.
- Functional: include at least one toggleable regression scenario if simple.
- Non-functional: keep routes isolated under `/mock-staging`; do not mix with LogiTest APIs.

## Architecture

Create a mock target module:

```text
app/modules/mock_staging/
  __init__.py
  router.py
```

Initial routes:

```text
POST /mock-staging/auth/login
GET  /mock-staging/products
GET  /mock-staging/products/{product_id}
POST /mock-staging/cart/items
POST /mock-staging/orders
POST /mock-staging/payments
GET  /mock-staging/orders/{order_id}
```

The executor strips/combines base URL and step endpoint, so generated test case endpoints like `/auth/login` map cleanly when `target_base_url` is `/mock-staging`.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\mock_staging\__init__.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\mock_staging\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\main.py`
- Add tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_mock_staging_api.py`

## Implementation Steps

1. Add router with prefix `/mock-staging` and tag `mock-staging`.
2. Implement stable e-commerce-style endpoint responses using plain dictionaries.
3. Include response bodies with keys expected by mock logs: token/user/status/items/product/order/payment fields where applicable.
4. Include router in `app/main.py`.
5. Add API tests validating representative routes.

## Success Criteria

- [ ] Mock staging routes return deterministic JSON.
- [ ] Route paths match generated test case endpoints when using `/mock-staging` as base.
- [ ] Existing LogiTest API prefixes remain unchanged.

## Risk Assessment

- Risk: mock responses drift from generated golden responses. Mitigation: align keys/status fields with current `mock-data/logs.json` and generated test case shape.
- Risk: embedding mock target into LogiTest app is not production architecture. Mitigation: explicitly scope as MVP; external target system can replace it later.
