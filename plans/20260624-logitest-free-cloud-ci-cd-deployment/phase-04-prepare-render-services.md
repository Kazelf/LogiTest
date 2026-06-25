---
phase: 4
title: "Prepare Render Services"
status: in-progress
priority: P1
effort: "1.5h"
dependencies: [3]
---

# Phase 04: Prepare Render Services

## Overview

Deploy the FastAPI platform backend and Express demo backend as separate Render Free Web Services.

## Requirements

- Functional: FastAPI service responds on `/health`.
- Functional: Demo Express backend responds on product/auth/order routes used by the demo.
- Functional: API service has `DATABASE_URL`, `DEMO_BACKEND_URL`, and `STAGING_API_BASE_URL` configured.
- Non-functional: services are acceptable for MVP/demo use even if they sleep.

## Architecture

```text
Render service: logitest-api
  root: logitest-ai/apps/api
  start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  db: Neon

Render service: logitest-demo
  root: logitest-ai/demo-system
  start: npm start
```

## Related Code Files

- Read: `logitest-ai/apps/api/requirements.txt`
- Read: `logitest-ai/apps/api/app/main.py`
- Read: `logitest-ai/demo-system/package.json`
- Read: `logitest-ai/demo-system/src/server.js`
- Create: `render.yaml`
- Create: `logitest-ai/docs/render-services.md`

## Implementation Steps

1. Create Render Web Service `logitest-demo`.
2. Configure:

```text
Root Directory: logitest-ai/demo-system
Build Command: npm install
Start Command: npm start
```

3. Set environment variables:

```text
REGRESSION_MODE=false
```

4. Deploy and smoke check:

```powershell
Invoke-RestMethod https://<demo-service>.onrender.com/api/products
```

5. Create Render Web Service `logitest-api`.
6. Configure:

```text
Root Directory: logitest-ai/apps/api
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

7. Set environment variables:

```text
DATABASE_URL=<Neon connection string>
DEMO_BACKEND_URL=https://<demo-service>.onrender.com
STAGING_API_BASE_URL=https://<demo-service>.onrender.com
ELASTICSEARCH_URL=
DEMO_LOG_INDEX=logitest-demo-logs
```

8. Deploy and smoke check:

```powershell
Invoke-RestMethod https://<api-service>.onrender.com/health
```

## Success Criteria

- [ ] Demo backend deploys successfully.
- [ ] FastAPI backend deploys successfully.
- [ ] `/health` works on Render FastAPI.
- [ ] Demo backend route works on Render.
- [ ] FastAPI can connect to Neon.
- [ ] Service URLs are recorded for Vercel setup.
- [x] Render Blueprint file exists without committed secrets.
- [x] Render setup guide exists with env vars and smoke checks.

## Risk Assessment

Risk: Render Free service sleeps and first request may time out during a presentation.

Mitigation: Open both Render service URLs 2-3 minutes before demo.

Risk: Build command may run from the wrong directory.

Mitigation: Set Render root directory explicitly for each service.

## Progress Notes

Prepared repo-side Render deployment artifacts on 2026-06-25:

- Added root `render.yaml` for Render Blueprint deployment.
- Added `logitest-ai/docs/render-services.md` with setup steps, env vars, and smoke checks.
- Kept `DATABASE_URL`, `DEMO_BACKEND_URL`, and `STAGING_API_BASE_URL` as `sync: false` in the Blueprint so real values are entered in Render and not committed.

Remaining external verification:

- Create/apply the Render Blueprint from GitHub.
- Enter the rotated Neon `DATABASE_URL`.
- Enter the deployed demo backend URL for `DEMO_BACKEND_URL` and `STAGING_API_BASE_URL`.
- Verify demo backend `/health` and `/api/products`.
- Verify FastAPI `/health`.
