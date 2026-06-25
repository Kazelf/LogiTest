---
phase: 4
title: "Verify browser flow and log generation"
status: in-progress
priority: P1
effort: "2h"
dependencies: ["phase-03"]
---

# Phase 04: Verify Browser Flow And Log Generation

## Overview

Verify both frontend correctness and the real reason this feature exists: browser actions produce structured backend logs that can enter the existing pipeline.

## Requirements

- Functional: Run frontend build/lint checks.
- Functional: Smoke test the `/demo` buyer flow against the real demo backend.
- Functional: Confirm logs are emitted by backend middleware and are importable from Elasticsearch when ES is running.
- Non-functional: Document environment blockers precisely if Docker, Elasticsearch, or browser testing is unavailable.

## Architecture

Validation should cover two layers:

```text
Static/build verification:
  npm run build --workspace web
  npm run lint --workspace web

End-to-end demo verification:
  web /demo -> demo-backend -> Elasticsearch -> dashboard Import ES
```

## Related Code Files

- Read/verify: `logitest-ai/apps/web/src/app/demo/page.tsx`
- Read/verify: `logitest-ai/apps/web/src/app/lib/demo-api.ts`
- Read/verify: `logitest-ai/demo-system/src/middlewares/logging.middleware.js`

## Implementation Steps

1. Run `npm run build --workspace @logitest/shared`.
2. Run `npm run build --workspace web`.
3. Run `npm run lint --workspace web`.
4. Run `docker compose config`.
5. Start services if Docker is available.
6. Open `http://localhost:3000/demo`.
7. Complete login, search, product detail, add cart, checkout, and result.
8. Check demo backend output or Elasticsearch for logs with the generated session id.
9. Return to dashboard and use `Import ES`.
10. Verify the imported session appears in the Sessions tab.

## Success Criteria

- [ ] Build and lint pass, or exact blockers are documented.
- [ ] `/demo` completes the full buyer flow with real backend responses.
- [ ] Backend structured logs include the same session id shown in the UI.
- [ ] Elasticsearch import brings the generated session into LogiTest.
- [ ] Dashboard can analyze the generated journey after import.

## Risk Assessment

Docker availability has been a previous blocker in this project. If Docker is unavailable, still verify local Next.js build and direct demo backend behavior, then mark full Elasticsearch proof as blocked by Docker daemon availability rather than claiming end-to-end success.
