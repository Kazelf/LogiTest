---
phase: 2
title: "Implement behavior mining services"
status: completed
priority: P2
effort: "2.5h"
dependencies: [phase-01]
---

# Phase 02: Implement Behavior Mining Services

## Overview

Implement the backend service layer that reads classified logs, derives journeys/personas, and persists the mined records into existing tables.

## Requirements

- Functional: fetch logs joined with sessions ordered chronologically per session.
- Functional: generate journey steps from log sequence action types.
- Functional: generate personas from action sets using MVP precedence rules.
- Functional: group identical action signatures into one journey.
- Functional: upsert personas and journeys idempotently.
- Non-functional: keep SQL parameterized and isolated in service functions.

## Architecture

Create `app/modules/behavior_mining/service.py` using the same direct `psycopg` style as ingestion. Service functions should own SQL and serialization; router functions should only map HTTP concerns. Reuse action constants from `session_reconstruction` to avoid string drift.

Suggested public functions:

```python
analyze_behavior() -> dict[str, Any]
list_journeys(limit: int, offset: int, filters: JourneyFilters) -> dict[str, Any]
list_personas(limit: int, offset: int, filters: PersonaFilters) -> dict[str, Any]
```

Useful internal helpers:

```python
_detect_persona(action_types: set[str]) -> PersonaSpec
_build_journey_signature(steps: list[dict[str, Any]]) -> str
_build_journey_name(signature: str) -> str
_calculate_risk_score(action_types: set[str]) -> float
```

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\__init__.py`
- Create tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_behavior_mining_service.py`

## Implementation Steps

1. Query logs joined with sessions and include `logs.action_type`.
2. Group rows by DB `session_id` or external session ID fallback.
3. Convert each ordered session into steps with `order`, `action_type`, `method`, `endpoint`, `expected_status`, and optional `response_time_ms`.
4. Detect persona with precedence: failed payment, buyer, browser, unknown.
5. Group sessions by identical action signature.
6. Upsert personas by `personas.name` and collect IDs.
7. Upsert journeys by `journeys.name`, linking persona and example session.
8. Return deterministic summary counts.
9. Add unit tests for persona detection, risk score, signature grouping, and serialization helpers.

## Success Criteria

- [x] Mining service can derive Buyer, Browser, Failed Payment User, and Unknown User.
- [x] Identical action sequences collapse into one journey.
- [x] Upsert SQL uses existing unique constraints and parameter binding.
- [x] Service tests do not require a live PostgreSQL database.

## Risk Assessment

The import script's seeded journeys may overlap with mined journeys. Use stable mined names and upsert by name; avoid deleting any existing records in this phase.
