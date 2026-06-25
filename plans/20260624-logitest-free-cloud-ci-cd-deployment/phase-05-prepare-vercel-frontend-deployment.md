---
phase: 5
title: "Prepare Vercel Frontend Deployment"
status: pending
priority: P1
effort: "1h"
dependencies: [4]
---

# Phase 05: Prepare Vercel Frontend Deployment

## Overview

Deploy the Next.js dashboard to Vercel and point it at the Render FastAPI backend.

## Requirements

- Functional: Vercel imports the GitHub repo.
- Functional: root directory is `logitest-ai/apps/web`.
- Functional: frontend uses `NEXT_PUBLIC_API_BASE_URL` from Vercel environment variables.
- Functional: production build succeeds.
- Non-functional: no backend URL should be hardcoded in source.

## Architecture

```text
Vercel Next.js app -> Render FastAPI -> Neon PostgreSQL
                         |
                         v
                    Render demo backend
```

## Related Code Files

- Read: `logitest-ai/apps/web/package.json`
- Read: `logitest-ai/apps/web/next.config.ts`
- Read: `logitest-ai/apps/web/src/app/page.tsx`
- Read: `logitest-ai/packages/shared/package.json`

## Implementation Steps

1. In Vercel, import the GitHub repository.
2. Set:

```text
Framework Preset: Next.js
Root Directory: logitest-ai/apps/web
Install Command: npm install
Build Command: npm run build
```

3. Add environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://<api-service>.onrender.com
```

4. Deploy.
5. Open the Vercel URL.
6. Confirm API calls target the Render API URL.

## Success Criteria

- [ ] Vercel production deployment succeeds.
- [ ] Dashboard loads over HTTPS.
- [ ] Frontend environment points to Render API.
- [ ] No localhost API URL remains in the deployed app.

## Risk Assessment

Risk: Monorepo workspace dependency `@logitest/shared` may not install correctly when Vercel root is `apps/web`.

Mitigation: If Vercel fails to resolve the local package, change Vercel root to `logitest-ai` and set build command to:

```bash
npm run build:web
```

with output/project settings adjusted to `apps/web`. Prefer the simple root first; only escalate if the build fails.

