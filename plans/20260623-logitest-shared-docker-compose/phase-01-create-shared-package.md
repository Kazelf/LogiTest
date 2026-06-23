---
phase: 1
title: "Create TypeScript shared schema package"
status: completed
priority: P1
effort: "1h"
dependencies: []
---

# Phase 1: Create TypeScript Shared Schema Package

## Overview

Create `packages/shared` as a real npm workspace package named `@logitest/shared`. Add simple Zod schemas and inferred TypeScript types that can be imported by the Next.js app.

## Requirements

- Functional: `@logitest/shared` exports `HealthResponseSchema`, `ApiErrorSchema`, `HealthResponse`, and `ApiError`.
- Functional: `apps/web` declares a dependency on `@logitest/shared`.
- Functional: running `npm install` from `logitest-ai/` installs both workspace packages.
- Non-functional: avoid domain schemas that are not backed by existing backend behavior.
- Non-functional: keep the package small and framework-agnostic.

## Architecture

Add a root npm workspace so `apps/web` and `packages/shared` install together. The shared package builds TypeScript declarations and JavaScript output into `dist/`, while source remains under `src/`.

Use Zod as a runtime validation library and infer TypeScript types from schemas. Do not attempt Python/TypeScript schema sharing in this phase.

## Related Code Files

- Create: `logitest-ai/package.json`
- Create: `logitest-ai/packages/shared/package.json`
- Create: `logitest-ai/packages/shared/tsconfig.json`
- Create: `logitest-ai/packages/shared/src/index.ts`
- Create: `logitest-ai/packages/shared/src/schemas.ts`
- Modify: `logitest-ai/apps/web/package.json`
- Optional modify: `logitest-ai/apps/web/next.config.ts`
- Optional delete: `logitest-ai/packages/shared/.gitkeep`

## Implementation Steps

1. Create root `logitest-ai/package.json` with `private: true` and workspaces `apps/web` and `packages/shared`.
2. Create `packages/shared/package.json` with:
   - `name: "@logitest/shared"`
   - `type: "module"`
   - `main`, `module`, and `types` pointing to `dist/`.
   - `scripts.build: "tsc -p tsconfig.json"`.
   - `dependencies.zod`.
   - `devDependencies.typescript`.
3. Create `packages/shared/tsconfig.json` with declaration output enabled and `outDir: "dist"`.
4. Create `src/schemas.ts` with `HealthResponseSchema` and `ApiErrorSchema` plus inferred types.
5. Re-export from `src/index.ts`.
6. Update `apps/web/package.json` to depend on `@logitest/shared` using workspace/local dependency compatible with npm.
7. If Next.js fails to compile workspace source/package, add `transpilePackages: ["@logitest/shared"]` to `apps/web/next.config.ts`.
8. Run workspace install and shared package build.

## Success Criteria

- [x] `npm install` succeeds from `logitest-ai/`.
- [x] `npm run build --workspace @logitest/shared` succeeds.
- [x] `apps/web` can import `HealthResponseSchema` or `HealthResponse` from `@logitest/shared`.
- [x] No backend code changes are required.

## Risk Assessment

Risk: npm may not accept the chosen workspace dependency syntax depending on the local npm version.

Mitigation: if `"workspace:*"` fails, use `"file:../../packages/shared"` in `apps/web/package.json`, which is acceptable for this repo and Docker build.

Risk: root lockfile and app lockfile may drift.

Mitigation: prefer root `npm install` going forward and document that root workspace install is authoritative.

