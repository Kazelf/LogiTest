---
phase: 8
title: "Build dashboard and demo script"
status: completed
priority: P2
effort: "1.5d"
dependencies: ["phase-07"]
---

# Phase 08: Build Dashboard And Demo Script

## Overview

Replace the starter Next.js page with an operational dashboard that walks the defense demo from logs to regression report.

## Requirements

- Functional: Show raw logs, sessions, journeys, journey detail, generated tests, script viewer, execution results, and regression report.
- Functional: Provide buttons for import logs, analyze journeys, generate tests, and run tests.
- Functional: Include a script/Postman collection to create demo behavior logs.
- Functional: Surface the chaining proof clearly in journey detail.
- Non-functional: Dashboard should be dense, utilitarian, and demo-friendly. Avoid marketing-page layout.

## Architecture

Keep the first version as a single operational page with tabs/sections:

```text
Pipeline controls
Raw Logs | Sessions | Journeys | Test Cases | Runs | Report
```

Use simple API client helpers against `NEXT_PUBLIC_API_BASE_URL`.

## Related Code Files

- Modify: `logitest-ai/apps/web/src/app/page.tsx`
- Modify/Create: `logitest-ai/apps/web/src/app/components/**`
- Modify/Create: `logitest-ai/apps/web/src/app/lib/api.ts`
- Modify: `logitest-ai/apps/web/src/app/globals.css`
- Create: `logitest-ai/scripts/simulate_demo_flow.ps1` or `logitest-ai/demo-system/postman/logitest-demo.postman_collection.json`
- Modify: `logitest-ai/README.md`

## Implementation Steps

1. Add small typed API client helpers.
2. Replace starter page with dashboard shell and controls.
3. Add raw logs and session panels.
4. Add journeys list/detail with chaining visualization.
5. Add generated test list and code viewer.
6. Add execution run list/detail and regression summary.
7. Add demo script and README defense script.
8. Verify desktop and mobile layout with browser testing if a dev server can run.

## Success Criteria

- [x] Dashboard no longer shows the default Next.js starter content.
- [x] User can run the demo pipeline from the UI or with documented commands.
- [x] Generated Jest/Supertest code is viewable.
- [x] Regression report clearly shows expected vs actual differences.
- [x] `npm run lint --workspace web` and `npm run build --workspace web` pass or have documented blockers.

## Risk Assessment

Dashboard scope can eat the schedule. Keep it operational and compact: tables, tabs, detail panels, and action buttons are enough for MVP.
