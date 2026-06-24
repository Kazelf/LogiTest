---
phase: 3
title: "Add Elasticsearch logging path and Compose services"
status: pending
priority: P1
effort: "1d"
dependencies: ["phase-02"]
---

# Phase 03: Add Elasticsearch Logging Path And Compose Services

## Overview

Wire the demo backend to emit structured API logs into Elasticsearch local and update Docker Compose to run the full local demo stack.

## Requirements

- Functional: Demo backend writes one structured log per API request.
- Functional: Logs include session, trace, request, request payload, response body/status, response time, service, environment.
- Functional: Docker Compose includes Elasticsearch and demo backend.
- Functional: Mock JSON fallback remains unchanged.
- Non-functional: Logging failures should not break demo API requests.

## Architecture

Request lifecycle:

```text
request-context middleware
  -> route handler
  -> response capture
  -> logging middleware writes document to Elasticsearch index
```

Minimum log document:

```json
{
  "timestamp": "2026-06-24T10:00:00.000Z",
  "session_id": "sess_001",
  "trace_id": "trace_001",
  "request_id": "req_001",
  "user_id": "user_001",
  "method": "POST",
  "endpoint": "/api/orders",
  "request_headers": {},
  "request_payload": {},
  "response_status": 201,
  "response_body": {},
  "response_time_ms": 120,
  "service_name": "demo-ecommerce",
  "environment": "demo"
}
```

## Related Code Files

- Modify: `logitest-ai/docker-compose.yml`
- Modify: `logitest-ai/.env.example`
- Modify: `logitest-ai/demo-system/src/middlewares/request-context.middleware.js`
- Modify: `logitest-ai/demo-system/src/middlewares/logging.middleware.js`
- Modify: `logitest-ai/demo-system/src/shared/logger.js`

## Implementation Steps

1. Add Elasticsearch service with single-node local config and healthcheck.
2. Add optional Kibana only if it does not slow down the demo too much.
3. Add `demo-backend` service with `DEMO_LOG_INDEX`, `ELASTICSEARCH_URL`, and port mapping, likely `3001:3001`.
4. Implement request context IDs from incoming headers or generated UUIDs.
5. Capture response body safely for JSON responses.
6. Mask sensitive fields before indexing.
7. Verify Elasticsearch receives documents after the demo script runs.

## Success Criteria

- [ ] `docker compose config` is valid.
- [ ] Demo backend can run with Elasticsearch unavailable and still return API responses.
- [ ] With Elasticsearch available, demo requests create log documents.
- [ ] Sensitive fields such as `password` and `token` are masked in indexed logs.

## Risk Assessment

Elasticsearch can be heavy on local machines. Keep Kibana optional, document memory expectations, and preserve mock import as fallback.

