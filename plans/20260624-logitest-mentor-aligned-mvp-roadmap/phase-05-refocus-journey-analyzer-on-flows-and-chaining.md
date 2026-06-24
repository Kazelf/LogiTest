---
phase: 5
title: "Refocus journey analyzer on flows and chaining"
status: pending
priority: P1
effort: "1d"
dependencies: ["phase-04"]
---

# Phase 05: Refocus Journey Analyzer On Flows And Chaining

## Overview

Update behavior analysis so the demo emphasizes user journey detection and API chaining, not advanced persona detection.

## Requirements

- Functional: Classify journeys as `LOGIN_FLOW`, `SEARCH_FLOW`, `ORDER_CREATION_FLOW`, or optional `ASYNC_PAYMENT_FLOW`.
- Functional: Detect output-input chaining, especially `orderId`.
- Functional: Store chaining metadata in `journeys.steps`.
- Functional: Keep persona data optional and secondary.
- Non-functional: Rules must be deterministic and easy to explain during defense.

## Architecture

For each session:

```text
group by session_id
  -> sort by timestamp
  -> classify each endpoint/action
  -> classify journey type
  -> scan response fields and later endpoint/payload fields
  -> store steps with extract/use metadata
```

Example step metadata:

```json
{
  "order": 2,
  "method": "POST",
  "endpoint": "/api/orders",
  "expected_status": 201,
  "extract": {
    "orderId": "response.body.orderId"
  }
}
```

## Related Code Files

- Modify: `logitest-ai/apps/api/app/modules/session_reconstruction/service.py`
- Modify: `logitest-ai/apps/api/app/modules/behavior_mining/service.py`
- Modify: `logitest-ai/apps/api/app/modules/behavior_mining/schemas.py`
- Modify: `logitest-ai/apps/api/tests/test_session_reconstruction_service.py`
- Modify: `logitest-ai/apps/api/tests/test_behavior_mining_service.py`
- Modify: `logitest-ai/mock-data/logs.json` only if endpoint shape must match the demo backend.

## Implementation Steps

1. Normalize endpoint matching to support `/api/...` prefixes and existing mock paths.
2. Add journey type detection rules.
3. Add recursive response field extraction for stable IDs such as `orderId`, `order_id`, `cartId`, `productId`.
4. Add later-step use detection for path params and request payload references.
5. Persist `type`, `extract`, and `uses` metadata in journey steps.
6. Keep existing persona listing compatible, but reduce its importance in docs and dashboard.

## Success Criteria

- [ ] Login-only sessions produce `LOGIN_FLOW`.
- [ ] Search sessions produce `SEARCH_FLOW`.
- [ ] Cart/order sessions produce `ORDER_CREATION_FLOW`.
- [ ] Order journey includes an extracted `orderId` and a later use.
- [ ] Behavior mining tests cover prefixed `/api` endpoints.

## Risk Assessment

Chaining can become a research project. Limit MVP to deterministic field matching and document more advanced dataflow analysis as future work.

