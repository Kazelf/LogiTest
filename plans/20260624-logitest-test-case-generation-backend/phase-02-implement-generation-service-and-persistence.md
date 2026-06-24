---
phase: 2
title: "Implement generation service and persistence"
status: completed
priority: P2
effort: "2.5h"
dependencies: [phase-01]
---

# Phase 02: Implement Generation Service And Persistence

## Overview

Implement deterministic generation logic in the `test_generation` module. The service fetches a journey, resolves its example session logs, builds JSON specs, and upserts into `test_cases`.

## Requirements

- Functional: generate one API test case from one `journey_id`.
- Functional: fetch logs through `journeys.example_session_id`, ordered by `logs.occurred_at ASC`.
- Functional: upsert by deterministic test case name when `overwrite=true`.
- Functional: reject duplicate generation when `overwrite=false` and a same-name test case exists.
- Non-functional: direct `psycopg` SQL only, following existing service pattern.

## Architecture

Data flow:

```text
journey_id
-> SELECT journey + persona
-> validate example_session_id exists
-> SELECT logs by session_id ordered by occurred_at
-> build steps/assertions/golden_response/generated_code
-> INSERT ... ON CONFLICT (name) DO UPDATE
-> return generated summary
```

Errors:

- `JourneyNotFoundError`: no journey for ID.
- `JourneyMissingExampleSessionError`: journey cannot generate replay data.
- `JourneyHasNoLogsError`: example session has no logs.
- `TestCaseAlreadyExistsError`: `overwrite=false` and deterministic name exists.

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\service.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\behavior_mining\service.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\scripts\import_mock_logs.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\database\migrations\001_init_logitest_schema.sql`

## Implementation Steps

1. Create dataclasses or helper functions for internal generation drafts if it keeps SQL serialization simple.
2. Implement `_fetch_journey(cur, journey_id)` selecting `journeys.id`, `journeys.name`, `description`, `persona_id`, `personas.name AS persona_name`, `example_session_id`.
3. Implement `_fetch_session_logs(cur, session_id)` selecting `service_name`, `method`, `endpoint`, `status_code`, `request_payload`, `response_body`, `response_time_ms`, `action_type`, `occurred_at`.
4. Implement `_build_steps(rows)` with stable `order` starting at 1.
5. Implement `_build_assertions(steps)`:
   - Always add `status_code` assertion.
   - Add `response_schema` assertion for object responses, using top-level keys as `required`.
6. Implement `_build_golden_response(journey, rows)` with `step_count`, final status/body, and `source` IDs.
7. Implement `build_generated_code_stub(name, steps)` modeled after import script, but with useful comments and no real execution yet.
8. Implement `generate_test_case(journey_id: str, overwrite: bool = True)` with transaction commit after upsert.
9. Implement serializers for test case list/detail rows.

## SQL Notes

Use `Jsonb(...)` for `steps`, `assertions`, and `golden_response`. Use `ON CONFLICT (name) DO UPDATE` only when overwrite is true. Since `test_cases.name` is unique, the deterministic name can be:

```text
API test - {journey.name without leading "Journey: " if present}
```

## Success Criteria

- [x] Service can generate a complete test case from fake cursor data in unit tests.
- [x] Persistence writes `type='api'`, `status='generated'`, `generated_by='test_generation_service'`.
- [x] Re-generation with overwrite updates existing row.
- [x] Missing journey/session/log data raises explicit domain errors.
- [x] No live DB required for service unit tests.

## Risk Assessment

- Risk: `behavior_mining` currently stores sparse `journeys.steps`. Mitigation: use logs through `example_session_id` as source of truth.
- Risk: request payload may include sensitive fields. Mitigation: no new masking in this phase; document as follow-up because source mock data is already controlled.
- Risk: generated code implies runnable tests. Mitigation: call it stub and keep execution out of scope.
