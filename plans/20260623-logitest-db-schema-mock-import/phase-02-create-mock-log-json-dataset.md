---
phase: 2
title: "Create mock log JSON dataset"
status: completed
priority: P1
effort: "1h"
dependencies: ["phase-01"]
---

# Phase 2: Create Mock Log JSON Dataset

## Overview

Create a realistic structured log dataset that simulates Elasticsearch output from a target e-commerce microservice system. The dataset will drive import, session reconstruction, persona detection, journey creation, and test case generation demos.

## Requirements

- Functional: create `mock-data/logs.json` as a JSON array.
- Functional: include at least three distinct user sessions.
- Functional: include enough records to reconstruct meaningful endpoint sequences.
- Functional: include success and failure paths.
- Functional: include fields required by the schema and import script.
- Non-functional: avoid real secrets, tokens, passwords, emails, phone numbers, or payment data.

## Architecture

The dataset represents normalized JSON logs that could have come from Elasticsearch. Each log record should map cleanly to the `logs` table and include the external session ID used to upsert `sessions`.

Recommended sessions:

```text
session-buyer-001:
login -> search products -> view product -> add cart -> checkout -> payment -> view order

session-browser-001:
login -> search products -> view product -> view another product

session-failed-payment-001:
login -> view product -> add cart -> checkout -> payment failed
```

## Related Code Files

- Create: `logitest-ai/mock-data/logs.json`

## Implementation Steps

1. Create `logitest-ai/mock-data/`.
2. Add `logs.json` as a formatted JSON array.
3. Include stable `external_log_id` values such as `log-buyer-001-login`.
4. Include required fields per record:
   - `external_log_id`
   - `timestamp`
   - `level`
   - `service_name`
   - `trace_id`
   - `session_id`
   - `user_id`
   - `method`
   - `endpoint`
   - `request_payload`
   - `response_status`
   - `response_body`
   - `response_time_ms`
5. Use timestamps that sort correctly inside each session.
6. Include at least one failed response, such as `402` or `500`, for the failed payment path.
7. Validate the file is valid JSON before moving on.

## Success Criteria

- [x] `logs.json` parses as valid JSON.
- [x] Dataset includes at least 12 log records.
- [x] Dataset includes at least three distinct `session_id` values.
- [x] Every record includes stable `external_log_id` and `trace_id`.
- [x] No mock record includes real sensitive data.

## Implementation Note

Created `logitest-ai/mock-data/logs.json` with 16 records across buyer, browser, and failed-payment sessions.

## Risk Assessment

Risk: Mock data may be too toy-like to demonstrate the product value.

Mitigation: include cross-service flow, response bodies, timings, and one failed journey so the dashboard/reporting layer later has meaningful examples.
