---
phase: 2
title: "Add FastAPI development Dockerfile"
status: in-progress
priority: P1
effort: "45m"
dependencies: []
---

# Phase 2: Add FastAPI Development Dockerfile

## Overview

Add a development Dockerfile for `apps/api` that installs Python dependencies and runs FastAPI with uvicorn reload. The image should be simple and suitable for Docker Compose local development.

## Requirements

- Functional: image installs dependencies from `apps/api/requirements.txt`.
- Functional: container runs `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.
- Functional: `/health` is reachable on port `8000` when the container runs.
- Non-functional: do not copy local `.venv` into the image.
- Non-functional: keep the Dockerfile dev-oriented, not production hardened.

## Architecture

Use a slim Python base image. Set the working directory to `/app`, install requirements first for better cache reuse, then copy the backend source. Compose can later mount `apps/api` into `/app` for hot reload.

## Related Code Files

- Create: `logitest-ai/apps/api/Dockerfile`
- Later phase creates: `logitest-ai/.dockerignore`
- Reference: `logitest-ai/apps/api/requirements.txt`
- Reference: `logitest-ai/apps/api/app/main.py`

## Implementation Steps

1. Create `apps/api/Dockerfile` from `python:3.12-slim` or another stable supported Python slim image.
2. Set Python env flags such as `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`.
3. Set `WORKDIR /app`.
4. Copy `requirements.txt` and install with `python -m pip install --no-cache-dir -r requirements.txt`.
5. Copy app source into the image.
6. Expose `8000`.
7. Use `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]`.
8. Build the API image through Compose in Phase 4.

## Success Criteria

- [ ] `docker build -f apps/api/Dockerfile apps/api` succeeds, or Compose build succeeds using an equivalent context.
- [ ] Running the image exposes FastAPI on container port `8000`.
- [x] Local `.venv` is excluded from build context by the root `.dockerignore` in Phase 4.

## Risk Assessment

Risk: Using Python 3.14 locally but Python 3.12 in Docker may hide version-specific behavior.

Mitigation: current backend is minimal and dependencies support common Python versions. If strict parity is required later, pin the Docker image to the team's target Python version.

Risk: `--reload` watches too many files if the mount includes caches.

Mitigation: `.dockerignore` and volume choices should exclude virtualenvs/caches where practical.

## Verification Note

Dockerfile was created, but Docker image build could not be verified because Docker Desktop daemon was not available at 
pipe:////./pipe/dockerDesktopLinuxEngine.

