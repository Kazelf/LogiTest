---
phase: 2
title: "Implement grouped sessions endpoint"
status: completed
priority: P2
effort: "1.5h"
dependencies: [phase-01]
---

# Phase 2: Implement Grouped Sessions Endpoint

## Overview

Implement `GET /api/logs/sessions` to list sessions grouped with log counts and service names.

## Requirements

- Functional: return paginated sessions with `log_count` and `services`.
- Functional: support optional exact filters `user_id` and `source`.
- Functional: return `total` for matching filter set.
- Non-functional: parameterized SQL only.
- Non-functional: no DB connection at import time.

## Architecture

Query shape:

```sql
SELECT
  sessions.id,
  sessions.external_session_id,
  sessions.user_id,
  sessions.started_at,
  sessions.ended_at,
  sessions.request_count,
  sessions.source,
  sessions.created_at,
  COUNT(logs.id)::int AS log_count,
  COALESCE(array_agg(DISTINCT logs.service_name) FILTER (WHERE logs.service_name IS NOT NULL), '{}') AS services
FROM sessions
LEFT JOIN logs ON logs.session_id = sessions.id
WHERE <optional whitelisted filters>
GROUP BY sessions.id
ORDER BY sessions.started_at DESC NULLS LAST, sessions.created_at DESC
LIMIT %s OFFSET %s;
```

Use a separate `COUNT(*) FROM sessions` query with identical session filters.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\schemas.py`

## Implementation Steps

1. Add `_build_session_filters(filters: SessionFilters)` with fixed clauses only.
2. Add service function `list_sessions(limit, offset, filters)`.
3. Add serialization helper that stringifies UUID and converts `services` to list.
4. Add router handler `GET /sessions` before any variable session route.
5. Map `psycopg.OperationalError` to existing `503` error response.

## Success Criteria

- [x] `GET /api/logs/sessions` returns `items`, `limit`, `offset`, `total`.
- [x] `limit=0`, `limit=201`, and negative `offset` fail with `422`.
- [x] `user_id` and `source` filters use SQL parameters.
- [x] Sessions without logs return `log_count: 0` and `services: []`.

## Risk Assessment

Risk: `array_agg` returns driver-specific array type.
Mitigation: normalize to `list(row["services"] or [])` in serializer.

Risk: total count differs from list filters.
Mitigation: share `_build_session_filters` between both queries.

