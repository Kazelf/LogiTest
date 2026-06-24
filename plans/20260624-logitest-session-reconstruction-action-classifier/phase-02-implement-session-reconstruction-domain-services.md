---
phase: 2
title: "Implement session reconstruction domain services"
status: pending
priority: P2
effort: "2h"
dependencies: [phase-01]
---

# Phase 02: Implement Session Reconstruction Domain Services

## Overview

Create pure backend services for grouping logs by session, sorting logs by timestamp, and classifying action types without changing API contracts.

## Requirements

- Functional: group logs by `session_id`, falling back to `session_external_id`, then `"unknown"`.
- Functional: sort logs by raw `timestamp` or DB/API-style `occurred_at`.
- Functional: put invalid or missing timestamps last.
- Functional: classify ecommerce action types with deterministic rules.
- Non-functional: keep functions pure and unit-testable without database access.

## Architecture

Use the existing empty `session_reconstruction` module as the domain home. The ingestion module can call this service later, but the service itself should not import FastAPI, psycopg, or database connection code.

Recommended public functions:

```python
group_logs_by_session(logs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]
sort_logs_by_timestamp(logs: list[dict[str, Any]], *, ascending: bool = True) -> list[dict[str, Any]]
classify_action(log: dict[str, Any]) -> ActionClassification
classify_logs(logs: list[dict[str, Any]]) -> list[dict[str, Any]]
```

## Related Code Files

- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\session_reconstruction\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\session_reconstruction\__init__.py`
- Create: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_session_reconstruction_service.py`

## Implementation Steps

1. Define action type constants as plain strings.
2. Add a frozen dataclass or Pydantic model for internal classification output.
3. Implement robust timestamp parsing for ISO strings ending in `Z`, timezone-aware datetimes, and missing values.
4. Implement grouping with `"unknown"` bucket fallback.
5. Implement sorting without mutating the input list.
6. Implement classifier rules in specific-to-generic order.
7. Add unit tests for grouping, sorting, and each classifier rule.

## Success Criteria

- [ ] Grouping preserves logs and uses `"unknown"` for missing session IDs.
- [ ] Sorting handles `timestamp`, `occurred_at`, datetime values, and invalid values.
- [ ] Classifier returns expected action type for all mock ecommerce flow endpoints.
- [ ] Service tests run without PostgreSQL.

## Risk Assessment

Classifier rules can become brittle if endpoint shapes change. Keep endpoint matching small and explicit, then add tests for every supported action label.
