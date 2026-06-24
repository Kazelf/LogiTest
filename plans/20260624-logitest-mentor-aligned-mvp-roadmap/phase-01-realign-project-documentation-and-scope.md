---
phase: 1
title: "Realign project documentation and scope"
status: completed
priority: P1
effort: "4h"
dependencies: []
---

# Phase 01: Realign Project Documentation And Scope

## Overview

Update project documentation so the implementation team follows the mentor-approved MVP instead of the earlier microservice-heavy scope.

## Requirements

- Functional: Document the new demo target as Express e-commerce modular monolith.
- Functional: Keep LogiTest AI platform as FastAPI modular monolith.
- Functional: State Jest + Supertest API regression as the primary test generation target.
- Functional: Move Playwright, Kubernetes, advanced persona detection, LLM-heavy logic, and async callbacks to future work.
- Non-functional: Documentation must be concise enough to guide implementation and defense preparation.

## Architecture

The documentation should describe two bounded systems:

```text
demo-system/    -> system under test, emits logs
apps/api        -> LogiTest AI platform API and analyzer
apps/web        -> operational dashboard
```

Do not present the demo backend as real microservices. Mention that modular boundaries can be extracted later if needed.

## Related Code Files

- Modify: `docs/AI-Driven-Behavioral-Testing-Platform.md`
- Modify: `docs/logitest-ai-tech-stack.md`
- Modify: `logitest-ai/README.md`
- Modify: `logitest-ai/.env.example`

## Implementation Steps

1. Replace microservice-first demo language with modular-monolith e-commerce demo language.
2. Add an MVP scope section with must-have and future-work lists.
3. Update architecture diagrams to include Elasticsearch local and mock JSON fallback.
4. Update tech stack table to reflect Express demo backend, FastAPI platform, PostgreSQL, Elasticsearch, Next.js, Jest + Supertest.
5. Update local development commands and env names for `DEMO_BACKEND_URL`, `ELASTICSEARCH_URL`, and `STAGING_API_BASE_URL`.

## Success Criteria

- [x] Docs no longer imply real microservices are required for the demo.
- [x] Docs clearly state that Elasticsearch is primary and mock JSON is fallback.
- [x] Docs clearly state Jest + Supertest is primary and Playwright is optional/future.
- [x] README gives the intended local demo flow in order.

## Risk Assessment

Main risk: docs become another wishlist. Keep them tied to the phase plan and avoid adding new components that are not in this roadmap.
