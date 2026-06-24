---
phase: 3
title: "Persist classified actions during import"
status: completed
priority: P2
effort: "2h"
dependencies: [phase-01, phase-02]
---

# Phase 03: Persist Classified Actions During Import

## Overview

Wire the rule-based classifier into the mock import path so every inserted or updated log row stores `action_type`.

## Requirements

- Functional: `scripts/import_mock_logs.py` writes `logs.action_type` during insert and conflict update.
- Functional: API import flow keeps reusing the script path and therefore also persists `action_type`.
- Functional: unmatched logs persist `unknown`.
- Non-functional: avoid duplicating classifier logic inside the import script.

## Architecture

The API service currently loads `scripts/import_mock_logs.py` dynamically. Update the script to import the domain classifier from the FastAPI app module, or move shared import helpers only if necessary. The preferred path is the smallest change: script calls `classify_action(record).action_type` before writing each log.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\scripts\import_mock_logs.py`
- Possibly modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\ingestion\service.py`
- Modify tests: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_logs_api.py`

## Implementation Steps

1. Add `action_type` to the `INSERT INTO logs (...)` column list.
2. Add `action_type = EXCLUDED.action_type` to the conflict update clause.
3. Pass the classifier result in the insert values.
4. Confirm API import path still works through the dynamically loaded script.
5. Add a focused test around import/upsert behavior where practical without a live DB, or unit-test the computed values via a fake cursor/connection.

## Success Criteria

- [x] Mock import writes non-unknown action types for known ecommerce records.
- [x] Conflict updates refresh `action_type` if rules change and import is re-run.
- [x] API import endpoint contract remains unchanged.
- [x] Existing import summary tests still pass.

## Risk Assessment

Importing app modules from a script can fail if `PYTHONPATH` is not set. If this happens, add a minimal path adjustment based on `PROJECT_ROOT / "apps" / "api"` inside the script, and keep it explicit.
