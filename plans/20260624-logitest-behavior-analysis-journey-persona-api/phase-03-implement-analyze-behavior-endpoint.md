---
phase: 3
title: "Implement analyze behavior endpoint"
status: completed
priority: P2
effort: "1h"
dependencies: [phase-01, phase-02]
---

# Phase 03: Implement Analyze Behavior Endpoint

## Overview

Expose `POST /api/behavior/analyze` to run the mining service against existing logs and persist the derived behavior records.

## Requirements

- Functional: register a new behavior router under `/api/behavior`.
- Functional: `POST /api/behavior/analyze` returns analyze summary counts.
- Functional: database connection errors map to HTTP 503.
- Functional: unexpected mining errors map to HTTP 500.
- Non-functional: keep route handlers thin and delegate work to service layer.

## Architecture

Create `behavior_mining/router.py` with `APIRouter(prefix="/api/behavior", tags=["behavior"])` and include it in `app/main.py`. Follow error mapping style from the ingestion router.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\main.py`
- Create/modify tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_behavior_api.py`

## Implementation Steps

1. Add the router and analyze endpoint with `AnalyzeBehaviorResponse`.
2. Include the router in FastAPI app startup.
3. Map `psycopg.OperationalError` to 503 with `Database is unavailable.`.
4. Map generic exceptions to 500 with `Behavior analysis failed.`.
5. Add route tests with monkeypatched service success and failure paths.

## Success Criteria

- [x] `POST /api/behavior/analyze` returns expected summary payload.
- [x] DB errors return 503.
- [x] Generic analysis errors return 500.
- [x] Existing `/health` and `/api/logs` routes remain registered.

## Risk Assessment

Analyze is a write operation. Keep it as POST, not GET, and make upserts idempotent so repeated calls are safe for MVP demos.
