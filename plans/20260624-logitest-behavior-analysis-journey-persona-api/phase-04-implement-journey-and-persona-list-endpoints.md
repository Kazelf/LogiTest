---
phase: 4
title: "Implement journey and persona list endpoints"
status: completed
priority: P2
effort: "1.5h"
dependencies: [phase-01, phase-02, phase-03]
---

# Phase 04: Implement Journey And Persona List Endpoints

## Overview

Expose read APIs so clients can inspect mined journeys and personas after analysis runs.

## Requirements

- Functional: `GET /api/behavior/journeys` returns paginated journey records.
- Functional: `GET /api/behavior/personas` returns paginated persona records.
- Functional: support optional name filters and `persona_id` filter for journeys.
- Functional: database connection errors map to HTTP 503.
- Non-functional: use whitelisted parameterized filter builders.

## Architecture

Mirror the ingestion module's list API shape: `items`, `limit`, `offset`, `total`. Keep filters simple and exact/ILIKE-based. Join journeys to personas for `persona_name` in journey list responses.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\service.py`
- Modify tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_behavior_api.py`

## Implementation Steps

1. Add list journey route with pagination and filters.
2. Add list persona route with pagination and filters.
3. Add service count/list SQL functions for both resources.
4. Serialize UUIDs to strings and normalize JSONB nulls to `{}` or `[]`.
5. Add tests for success, validation bounds, DB failures, and filter builder parameterization.

## Success Criteria

- [x] Journey list route returns `items`, `limit`, `offset`, and `total`.
- [x] Persona list route returns `items`, `limit`, `offset`, and `total`.
- [x] Pagination validation rejects invalid bounds.
- [x] SQL filters are parameterized and whitelist-based.

## Risk Assessment

Returning large `steps` JSON arrays can grow response size later. Accept for MVP, but keep default pagination at 50 and max at 200 like existing APIs.
