---
phase: 4
title: "Verify classifier and reconstruction behavior"
status: completed
priority: P2
effort: "1h"
dependencies: [phase-02, phase-03]
---

# Phase 04: Verify Classifier And Reconstruction Behavior

## Overview

Run focused tests and update lightweight documentation so the next API-response task can build on stable behavior.

## Requirements

- Functional: tests cover group, sort, classifier, and import persistence behavior.
- Functional: existing API tests keep passing.
- Non-functional: verification must not require Docker or a live PostgreSQL instance.

## Architecture

Use pure unit tests for reconstruction/classifier logic and monkeypatch/fake cursor tests for import behavior. Keep live DB smoke testing optional because earlier plans already note Docker may be unavailable.

## Related Code Files

- Modify/create tests under `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests`
- Optionally modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\README.md`
- Optionally modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\README.md`

## Implementation Steps

1. Run backend tests from `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api`.
2. Verify tests do not require database connectivity.
3. Add README notes only if useful for later task handoff.
4. Record manual smoke commands for optional local DB validation.
5. Sync plan status after implementation using the plan workflow.

## Success Criteria

- [x] `python -m pytest` passes in `apps/api`.
- [x] Tests prove missing session IDs group under `"unknown"`.
- [x] Tests prove invalid timestamps sort last.
- [x] Tests prove classifier rule precedence for search vs product detail and payment success vs payment failure.
- [x] Documentation or plan notes mention that API exposure is intentionally deferred.

## Risk Assessment

Over-testing implementation details can make refactors annoying. Prefer testing public service functions and observable import behavior, not every private helper.
