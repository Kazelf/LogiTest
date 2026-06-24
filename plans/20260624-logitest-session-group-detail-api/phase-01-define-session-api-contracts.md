---
phase: 1
title: "Define session API contracts"
status: completed
priority: P2
effort: "1h"
dependencies: []
---

# Phase 1: Define Session API Contracts

## Overview

Add Pydantic schemas and route/service function signatures for grouped session summaries and session detail responses.

## Requirements

- Functional: define response models for session list and detail.
- Functional: define filter model for session list filters.
- Non-functional: keep schema names clear and colocated in `ingestion/schemas.py`.
- Non-functional: do not expose raw log payloads by default.

## Architecture

New schemas:

- `SessionSummaryItem`
- `SessionListResponse`
- `SessionDetail`
- `SessionDetailLogItem`
- `SessionDetailResponse`
- `SessionFilters`

Reuse existing log summary naming where practical, but avoid redundant `session_external_id` inside detail logs.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\schemas.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\service.py`

## Implementation Steps

1. Add session summary schema with `id`, `external_session_id`, `user_id`, timestamps, counts, `source`, `services`, `created_at`.
2. Add session detail schema with `metadata` included.
3. Add detail log item schema using summary log fields only.
4. Add list response schema with `items`, `limit`, `offset`, `total`.
5. Add `SessionFilters` with optional `user_id` and `source`.

## Success Criteria

- [x] Response schemas express all API contract fields.
- [x] Pagination fields enforce `limit` 1-200 and `offset >= 0`.
- [x] No raw `request_payload`, `response_body`, or `raw_log` in response schemas.

## Risk Assessment

Risk: duplicating log summary schema creates drift.
Mitigation: reuse field naming and serialization helper patterns from `LogListItem`.

