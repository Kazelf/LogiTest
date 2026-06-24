---
phase: 1
title: "Define behavior API contracts"
status: completed
priority: P2
effort: "1h"
dependencies: []
---

# Phase 01: Define Behavior API Contracts

## Overview

Add Pydantic request/response schemas for behavior analysis, journey list, and persona list APIs without implementing mining logic yet.

## Requirements

- Functional: define response model for `POST /api/behavior/analyze`.
- Functional: define paginated response models for journey and persona list APIs.
- Functional: support pagination fields matching existing logs API conventions.
- Non-functional: do not modify existing `/api/logs` schemas or response contracts.

## Architecture

Create behavior-specific schemas in the `behavior_mining` module. Keep response shapes explicit rather than returning raw DB rows. Store `steps` and `features` as JSON-compatible dictionaries/lists because the tables already use JSONB and the shape will evolve during MVP work.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\schemas.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\__init__.py`

## Implementation Steps

1. Define `AnalyzeBehaviorResponse` with `sessions_analyzed`, `personas_upserted`, `journeys_upserted`, `source`, `method`.
2. Define `PersonaListItem`, `PersonaListResponse`, and `PersonaFilters`.
3. Define `JourneyListItem`, `JourneyListResponse`, and `JourneyFilters`.
4. Use `Field(ge=1, le=200)` and `Field(ge=0)` for pagination consistency.
5. Keep schemas independent from ingestion schemas.

## Success Criteria

- [x] Behavior schemas exist and import cleanly.
- [x] Pagination validation matches `/api/logs` patterns.
- [x] No existing logs schemas are changed.

## Risk Assessment

Overly detailed response models can expose sensitive payloads too early. Keep list responses focused on mined behavior metadata, not raw request/response bodies.
