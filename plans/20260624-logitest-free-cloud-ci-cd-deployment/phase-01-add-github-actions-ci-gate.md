---
phase: 1
title: "Add GitHub Actions CI Gate"
status: completed
priority: P1
effort: "1h"
dependencies: []
---

# Phase 01: Add GitHub Actions CI Gate

## Overview

Create the main CI workflow for pull requests and pushes. It should verify all currently implemented code paths without requiring cloud credentials or running services.

## Requirements

- Functional: CI runs for `push` and `pull_request` targeting `main`.
- Functional: CI installs Node workspace dependencies with `npm ci`.
- Functional: CI builds `@logitest/shared`.
- Functional: CI lints and builds `apps/web`.
- Functional: CI runs `demo-system` tests.
- Functional: CI installs Python backend dependencies and runs `pytest`.
- Non-functional: CI should not need Docker, PostgreSQL, Elasticsearch, Vercel, Render, or Neon.

## Architecture

Use one workflow file at the Git repository root:

```text
.github/workflows/ci.yml
```

Suggested jobs:

- `node-ci`: shared package, web lint/build, demo tests.
- `api-ci`: FastAPI pytest.

Splitting jobs keeps failures easier to read.

## Related Code Files

- Create: `.github/workflows/ci.yml`
- Read: `logitest-ai/package.json`
- Read: `logitest-ai/apps/web/package.json`
- Read: `logitest-ai/demo-system/package.json`
- Read: `logitest-ai/apps/api/requirements.txt`

## Implementation Steps

1. Create `.github/workflows/ci.yml`.
2. Use `actions/checkout`.
3. Use `actions/setup-node` with Node LTS.
4. Cache npm dependencies through `setup-node` with `cache: npm` and `cache-dependency-path: logitest-ai/package-lock.json`.
5. Run `npm ci` from `logitest-ai`.
6. Run:

```bash
npm run build:shared
npm run lint --workspace web
npm run build:web
npm run test:demo
```

7. Use `actions/setup-python` with Python 3.12 for backend tests.
8. Run:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
```

from `logitest-ai/apps/api`.

## Success Criteria

- [ ] CI appears in GitHub Actions after push.
- [x] Node job local equivalents pass.
- [x] API job local equivalent passes.
- [x] No cloud secrets are required.
- [x] A failing frontend build or backend test fails the workflow.

## Risk Assessment

Risk: Frontend build can fail if the shared package exports TypeScript source in a way Next.js cannot consume in CI.

Mitigation: Keep `npm run build:shared` before `npm run build:web`, and fix workspace package output only if CI exposes a real error.

## Completion Notes

Implemented `.github/workflows/ci.yml` with separate `node-ci` and `api-ci` jobs.

Note: the workflow lives at `D:\ViettelDigitalTalent\LogiTest\.github\workflows\ci.yml` because the Git repository root is `D:\ViettelDigitalTalent\LogiTest`; the jobs still run commands inside `logitest-ai`.

Local verification on 2026-06-24:

- `npm.cmd run build:shared` passed.
- `npm.cmd run lint --workspace web` passed.
- `npm.cmd run build:web` passed.
- `npm.cmd run test:demo` passed.
- `python -m pytest` passed with 54 tests and 1 existing warning.
