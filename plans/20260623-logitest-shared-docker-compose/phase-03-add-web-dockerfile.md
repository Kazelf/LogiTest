---
phase: 3
title: "Add Next.js development Dockerfile"
status: in-progress
priority: P1
effort: "1h"
dependencies: ["phase-01"]
---

# Phase 3: Add Next.js Development Dockerfile

## Overview

Add a development Dockerfile for the Next.js app that works with the new npm workspace and can run `next dev` inside Docker Compose.

## Requirements

- Functional: image installs workspace dependencies from the `logitest-ai` root.
- Functional: container runs the web app on `0.0.0.0:3000`.
- Functional: web app can resolve `@logitest/shared`.
- Non-functional: do not bake host `node_modules`, `.next`, or build output into the image.
- Non-functional: keep the image simple for development; production standalone output is out of scope.

## Architecture

Build the web image from the monorepo root context so npm can see both `apps/web` and `packages/shared`. The Dockerfile can live in `apps/web/Dockerfile`, while Compose sets `context: .` and `dockerfile: apps/web/Dockerfile`.

The container command should run the web workspace script, for example `npm run dev --workspace web -- --hostname 0.0.0.0`.

## Related Code Files

- Create: `logitest-ai/apps/web/Dockerfile`
- Modify or reference: `logitest-ai/package.json`
- Modify or reference: `logitest-ai/apps/web/package.json`
- Modify if needed: `logitest-ai/apps/web/next.config.ts`
- Reference: `logitest-ai/packages/shared/package.json`

## Implementation Steps

1. Create `apps/web/Dockerfile` using a Node LTS Alpine or slim image.
2. Set `WORKDIR /app`.
3. Copy root package manifests and workspace package manifests first for dependency caching.
4. Copy `apps/web/package.json` and `packages/shared/package.json` before install.
5. Run `npm install` from `/app`.
6. Copy `apps/web` and `packages/shared` into the image.
7. Expose `3000`.
8. Run the web dev server on `0.0.0.0`.
9. If Next.js cannot compile the shared package, update `next.config.ts` with `transpilePackages`.

## Success Criteria

- [ ] Compose can build the web image from the monorepo root.
- [ ] Container starts Next.js dev server on port `3000`.
- [x] Web dependency resolution includes `@logitest/shared`.
- [ ] Web remains usable via `http://localhost:3000`.

## Risk Assessment

Risk: npm workspace install inside Docker may fail if the root lockfile is absent or inconsistent.

Mitigation: create/update root lockfile through `npm install` during implementation and commit it if generated.

Risk: bind mounts can hide image-installed `node_modules`.

Mitigation: if Compose mounts source, use an anonymous volume for `/app/node_modules` or avoid full-root bind mount. Prefer mounting `apps/web`, `packages/shared`, and preserving container `node_modules`.

## Verification Note

Dockerfile was created, but Docker image build could not be verified because Docker Desktop daemon was not available at 
pipe:////./pipe/dockerDesktopLinuxEngine. Frontend lint and direct TypeScript compile passed.

