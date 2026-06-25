---
phase: 6
title: "End-to-End Hosted Smoke Test and Documentation"
status: pending
priority: P2
effort: "1h"
dependencies: [1, 2, 3, 4, 5]
---

# Phase 06: End-to-End Hosted Smoke Test and Documentation

## Overview

Verify the hosted free deployment path and document the exact setup steps so the deployment can be repeated.

## Requirements

- Functional: CI and Docker validation workflow results are visible in GitHub Actions.
- Functional: hosted API, hosted demo backend, hosted frontend all respond.
- Functional: database connectivity is confirmed.
- Functional: documentation explains the Elasticsearch local-only limitation.
- Non-functional: setup guide must be clear enough to repeat without guessing.

## Architecture

Documentation should live near the app:

```text
logitest-ai/docs/github-actions-ci-cd.md
logitest-ai/docs/free-cloud-deployment.md
```

If keeping docs minimal, combine both into one:

```text
logitest-ai/docs/free-cloud-ci-cd-deployment.md
```

## Related Code Files

- Create: `logitest-ai/docs/free-cloud-ci-cd-deployment.md`
- Read: `plans/20260624-logitest-free-cloud-ci-cd-deployment/plan.md`
- Read: `logitest-ai/README.md`

## Implementation Steps

1. Run or inspect CI on GitHub.
2. Run or inspect Docker build validation on GitHub.
3. Smoke test Render API:

```powershell
Invoke-RestMethod https://<api-service>.onrender.com/health
```

4. Smoke test Render demo backend:

```powershell
Invoke-RestMethod https://<demo-service>.onrender.com/api/products
```

5. Open Vercel frontend in a browser.
6. Record final URLs:

```text
Frontend: https://...
API: https://...
Demo backend: https://...
Database: Neon project name only, never password/URL
```

7. Write deployment guide covering:

- GitHub Actions.
- Neon database setup.
- Render API setup.
- Render demo backend setup.
- Vercel frontend setup.
- Environment variables.
- Smoke tests.
- Known limitations.

## Success Criteria

- [ ] Hosted frontend URL works.
- [ ] Hosted API health check works.
- [ ] Hosted demo backend route works.
- [ ] CI workflow is documented.
- [ ] Deployment setup is documented.
- [ ] Elasticsearch limitation is explicit.
- [ ] No secrets appear in documentation.

## Risk Assessment

Risk: A hosted demo may look incomplete because Elasticsearch is not deployed.

Mitigation: Document two modes clearly:

- Hosted free demo: API/frontend/database plus mock/fallback flow.
- Full local defense demo: Docker Compose with Elasticsearch.

