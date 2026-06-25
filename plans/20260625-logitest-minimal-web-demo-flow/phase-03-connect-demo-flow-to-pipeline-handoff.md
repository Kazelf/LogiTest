---
phase: 3
title: "Connect demo flow to pipeline handoff"
status: completed
priority: P2
effort: "2h"
dependencies: ["phase-02"]
---

# Phase 03: Connect Demo Flow To Pipeline Handoff

## Overview

Make it easy to move from the user-flow demo into the existing LogiTest dashboard pipeline. The goal is not to redesign the dashboard, only to make the demo sequence obvious.

## Requirements

- Functional: Add a dashboard link to open `/demo`.
- Functional: Add a `/demo` link back to `/` with wording that tells the presenter to import Elasticsearch logs next.
- Functional: Ensure the dashboard's existing `Import ES`, `Analyze`, `Generate Jest`, and `Run Test` actions still work after the demo flow.
- Non-functional: Keep dashboard changes minimal.

## Architecture

The existing dashboard remains at:

```text
apps/web/src/app/page.tsx
```

Add only a small navigation affordance:

```text
Dashboard -> Run Web Demo
Demo -> Back to Pipeline Dashboard
```

## Related Code Files

- Modify: `logitest-ai/apps/web/src/app/page.tsx`
- Modify: `logitest-ai/apps/web/src/app/demo/page.tsx`

## Implementation Steps

1. Add a simple link/button from dashboard header or action area to `/demo`.
2. Add a simple link/button from demo result screen back to `/`.
3. On the demo result screen, show the recommended next sequence:
   - Import ES
   - Analyze
   - Generate Jest
   - Run Test
4. Confirm dashboard API calls still point to FastAPI while demo calls point to Express.

## Success Criteria

- [ ] Presenter can start from dashboard, open web demo, complete flow, return to dashboard.
- [ ] UI makes the next pipeline step obvious without extra documentation.
- [ ] Existing dashboard behavior is not regressed.

## Risk Assessment

Do not duplicate dashboard pipeline controls inside `/demo`. Duplicating import/analyze/generate/run controls would create more maintenance surface and confuse the responsibility of the demo page.
