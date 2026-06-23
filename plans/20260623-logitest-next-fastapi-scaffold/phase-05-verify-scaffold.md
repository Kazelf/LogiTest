---
phase: 5
title: "Verify scaffold"
status: pending
priority: P1
effort: "30m"
dependencies: [phase-02, phase-03, phase-04]
---

# Phase 5: Verify Scaffold

## Overview

Run lightweight checks to prove both generated apps are valid and the docs are synchronized.

## Requirements

- Functional: frontend and backend run locally.
- Non-functional: validation should be repeatable by another developer.

## Architecture

No architecture changes. This phase validates the scaffold produced by previous phases.

## Related Code Files

- Read: `logitest-ai/apps/web/package.json`
- Read: `logitest-ai/apps/api/requirements.txt`
- Read: `logitest-ai/apps/api/tests/test_health.py`
- Read: `logitest-ai/README.md`

## Implementation Steps

1. Verify frontend build or lint:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\web
   npm run lint
   npm run build
   ```

2. Verify backend tests:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
   .\.venv\Scripts\python -m pytest
   ```

3. Verify backend health endpoint manually:

   ```powershell
   .\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
   Invoke-RestMethod http://localhost:8000/health
   ```

4. Verify docs wording:

   ```powershell
   rg -n "Express|express|Supertest" D:\ViettelDigitalTalent\LogiTest\docs D:\ViettelDigitalTalent\LogiTest\logitest-ai\README.md -g "*.md"
   ```

## Success Criteria

- [ ] `npm run build` succeeds for frontend.
- [ ] `pytest` succeeds for backend.
- [ ] `/health` returns status `ok`.
- [ ] No stale Express/Supertest wording remains in project docs for LogiTest AI backend.

## Risk Assessment

Medium-low risk. `npm run lint` may not exist depending on the latest `create-next-app` template. If missing, rely on `npm run build` for scaffold validation.
