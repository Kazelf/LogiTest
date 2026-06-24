---
phase: 3
title: "Implement session detail endpoint"
status: completed
priority: P2
effort: "1.5h"
dependencies: [phase-01, phase-02]
---

# Phase 3: Implement Session Detail Endpoint

## Overview

Implement `GET /api/logs/sessions/{external_session_id}` to return a single session plus logs ordered chronologically.

## Requirements

- Functional: find session by `sessions.external_session_id`.
- Functional: return session metadata and `log_count`.
- Functional: return logs ordered by `logs.occurred_at ASC`.
- Functional: return `404` when session does not exist.
- Non-functional: do not expose raw payload/body fields in this MVP response.

## Architecture

Service flow:

1. Query session by external ID with count aggregation.
2. If no row, return `None` or raise a domain-specific not-found signal.
3. Query logs for that session ID ordered by `occurred_at ASC`.
4. Router converts not-found to `HTTPException(404, "Session not found.")`.

Log fields should mirror existing list log summary fields minus redundant `session_external_id`.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\schemas.py`

## Implementation Steps

1. Add `SessionNotFoundError` or return `None` from service; pick the simpler pattern that keeps router readable.
2. Add service function `get_session_detail(external_session_id: str)`.
3. Use parameterized SQL for the external session lookup.
4. Query logs using internal `sessions.id` after session is found.
5. Serialize UUIDs, metadata JSON, timestamps, and log rows.
6. Add router handler `GET /sessions/{external_session_id}`.
7. Map not found to `404`; map DB outage to `503`.

## Success Criteria

- [x] Existing session returns `session` object and `logs` array.
- [x] Logs are ordered oldest-to-newest by `occurred_at ASC`.
- [x] Missing session returns `404 {"detail":"Session not found."}`.
- [x] DB outage returns `503 {"detail":"Database is unavailable."}`.

## Risk Assessment

Risk: path route catches `/sessions` list route incorrectly.
Mitigation: define exact `/sessions` route and variable `/sessions/{external_session_id}` explicitly; FastAPI handles exact route cleanly.

Risk: metadata may be `None` or unexpected type.
Mitigation: schema expects `dict`; serializer coalesces falsey metadata to `{}`.

