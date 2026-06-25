---
phase: 2
title: "Add Docker Build Validation Gate"
status: completed
priority: P2
effort: "1h"
dependencies: [1]
---

# Phase 02: Add Docker Build Validation Gate

## Overview

Add a separate workflow that validates Dockerfiles and Docker Compose syntax. This keeps Docker-specific failures isolated from fast unit CI.

## Requirements

- Functional: workflow runs on `push` to `main` and manual `workflow_dispatch`.
- Functional: `docker compose config` validates the Compose file.
- Functional: existing API, web, and demo Dockerfiles build.
- Non-functional: workflow should not push images to any registry.

## Architecture

Use one workflow file at the Git repository root:

```text
.github/workflows/docker-build.yml
```

Run Docker validation on GitHub-hosted Ubuntu runners where Docker is available.

## Related Code Files

- Create: `.github/workflows/docker-build.yml`
- Read: `logitest-ai/docker-compose.yml`
- Read: `logitest-ai/apps/api/Dockerfile`
- Read: `logitest-ai/apps/web/Dockerfile`
- Read: `logitest-ai/demo-system/Dockerfile`

## Implementation Steps

1. Create `.github/workflows/docker-build.yml`.
2. Use `actions/checkout`.
3. Set working directory to `logitest-ai`.
4. Run:

```bash
docker compose config
docker build -f apps/api/Dockerfile apps/api
docker build -f apps/web/Dockerfile .
docker build -f demo-system/Dockerfile .
```

5. If the web Dockerfile expects monorepo root context, keep context as `.`.
6. If API Dockerfile expects app-only context, keep context as `apps/api`.
7. If demo-system Dockerfile copies root workspace files, keep context as `.`.

## Success Criteria

- [ ] Docker workflow can be started manually.
- [x] Compose syntax is validated by workflow definition and local `docker compose config`.
- [ ] API Docker image builds on GitHub runner.
- [ ] Web Docker image builds on GitHub runner.
- [ ] Demo backend Docker image builds on GitHub runner.
- [x] No registry credentials are required.

## Risk Assessment

Risk: Dockerfiles are currently development-first and may not be optimized for cloud production.

Mitigation: Treat this workflow as build validation only. Deploy through native Vercel/Render runtime for the free MVP path.

## Completion Notes

Implemented `.github/workflows/docker-build.yml` with a single `docker-build` job.

Note: the workflow lives at `D:\ViettelDigitalTalent\LogiTest\.github\workflows\docker-build.yml` because the Git repository root is `D:\ViettelDigitalTalent\LogiTest`; the job runs commands inside `logitest-ai`.

The demo backend image uses root context `.` because `demo-system/Dockerfile` copies root `package.json` and `package-lock.json`.
