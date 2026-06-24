---
phase: 3
title: "Implement list logs endpoint"
status: completed
priority: P2
effort: "2h"
dependencies: [phase-01]
---

# Phase 3: Implement List Logs Endpoint

## Overview

Expose `GET /api/logs` for inspecting normalized logs with pagination and basic filters.

## Requirements

- Functional: returns logs sorted by `occurred_at DESC`.
- Functional: supports `limit`, `offset`, `session_id`, `trace_id`, `endpoint`, `level`.
- Functional: returns `total` count for the same filter set.
- Non-functional: SQL must be parameterized; dynamic clauses must be whitelisted.
- Non-functional: response should not include full `request_payload`, `response_body`, or `raw_log` in MVP list view.

## Architecture

Query shape:

```sql
SELECT
  logs.id,
  logs.external_log_id,
  sessions.external_session_id AS session_external_id,
  logs.trace_id,
  logs.user_id,
  logs.service_name,
  logs.level,
  logs.method,
  logs.endpoint,
  logs.status_code,
  logs.response_time_ms,
  logs.occurred_at
FROM logs
LEFT JOIN sessions ON sessions.id = logs.session_id
WHERE <whitelisted filters>
ORDER BY logs.occurred_at DESC
LIMIT %s OFFSET %s;
```

Use a separate `COUNT(*)` query with same `WHERE` clauses.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\schemas.py`

## Implementation Steps

1. Add Pydantic query validation in router: `limit` 1-200, `offset` >= 0.
2. Add list response schema and item schema.
3. Build `WHERE` clauses from fixed filter names only.
4. Use `ILIKE` for endpoint filter to support simple search.
5. Execute count query first or second; both must use same filter params.
6. Convert row timestamps to JSON-compatible Pydantic response.
7. Map DB connection failure to `503`.

## Success Criteria

- [x] `GET /api/logs` returns `items`, `limit`, `offset`, `total`.
- [x] `limit=0` and `limit=201` fail validation.
- [x] `session_id=session-buyer-001` filters through joined `sessions.external_session_id`.
- [x] SQL uses parameter binding for all user input.
- [x] Empty database returns `items: []` and `total: 0` by query behavior.

## Risk Assessment

- Risk: endpoint substring filter can be slow later.
  Mitigation: acceptable for MVP; indexed exact endpoint can be added later if needed.
- Risk: total count can cost extra on large DB.
  Mitigation: mock/MVP scale tiny; revisit cursor pagination later.

## Security Considerations

- Whitelist filters, never interpolate user input into SQL.
- Exclude payload/body/raw JSON from list response to reduce accidental sensitive data exposure.
