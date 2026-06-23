---
title: "Task 1.2 and 1.3: Scaffold LogiTest AI Next.js frontend and FastAPI backend"
status: completed
created: 2026-06-23
scope: project
source: skill:plan
blockedBy: []
blocks: []
phases:
  - id: phase-01
    title: "Normalize tech stack docs"
    status: completed
  - id: phase-02
    title: "Create Next.js frontend app"
    status: completed
  - id: phase-03
    title: "Create FastAPI backend app"
    status: completed
  - id: phase-04
    title: "Wire local development config"
    status: completed
  - id: phase-05
    title: "Verify scaffold"
    status: completed
---

# Task 1.2 and 1.3 Plan

## Goal

Create the initial LogiTest AI application scaffold under the existing monorepo:

- Task 1.2: create `logitest-ai/apps/web` as a Next.js dashboard app.
- Task 1.3: create `logitest-ai/apps/api` as a Python FastAPI modular monolith backend.
- Keep all docs aligned with the chosen stack: Next.js + Tailwind CSS + shadcn/ui for frontend, Python FastAPI for backend.

## Codebase Context

- Current root: `D:\ViettelDigitalTalent\LogiTest`.
- Existing monorepo: `D:\ViettelDigitalTalent\LogiTest\logitest-ai`.
- Task 1.1 already created folders: `apps`, `services`, `packages`, `target-system`, `docker`, `scripts`, `docs`.
- Source of truth for tech stack: `docs/logitest-ai-tech-stack.md`.
- Backend should follow FastAPI modular monolith, not Express.

## Final Folder Shape

```text
logitest-ai/
├── apps/
│   ├── web/                 # Next.js + Tailwind dashboard
│   └── api/                 # FastAPI backend
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   ├── db/
│       │   ├── modules/
│       │   │   ├── projects/
│       │   │   ├── ingestion/
│       │   │   ├── session_reconstruction/
│       │   │   ├── behavior_mining/
│       │   │   ├── test_generation/
│       │   │   ├── execution/
│       │   │   └── reports/
│       │   └── workers/
│       ├── tests/
│       └── requirements.txt
├── packages/
├── services/
├── target-system/
└── README.md
```

## Acceptance Criteria

- `logitest-ai/apps/web` exists and starts with `npm run dev`.
- `logitest-ai/apps/api` exists and starts with `uvicorn app.main:app --reload`.
- Backend exposes `GET /health` returning a simple JSON status.
- Documentation no longer describes LogiTest AI backend as Express.
- Commands are normal terminal commands, no hidden generator assumptions.
- No business modules are implemented beyond placeholder packages and health check.

## Out Of Scope

- Authentication, database schema, Elasticsearch integration, AI pipeline logic.
- Docker Compose services for Postgres/Elasticsearch/Kibana.
- shadcn component installation beyond preparing the Next.js/Tailwind app, unless needed immediately.
- Demo target microservices.

## Implementation Phases

1. [Phase 1: Normalize tech stack docs](phase-01-normalize-tech-stack-docs.md)
2. [Phase 2: Create Next.js frontend app](phase-02-create-nextjs-frontend.md)
3. [Phase 3: Create FastAPI backend app](phase-03-create-fastapi-backend.md)
4. [Phase 4: Wire local development config](phase-04-wire-local-dev-config.md)
5. [Phase 5: Verify scaffold](phase-05-verify-scaffold.md)

## Recommended Execution Order

Run phases in order. Phase 1 removes stack ambiguity first. Phase 2 and Phase 3 can be done independently after that, but Phase 4 and Phase 5 depend on both apps existing.

## Key Risks

- `create-next-app` may fail if `apps/web` is non-empty. Mitigation: inspect folder before running, remove only generated empty placeholder files if confirmed safe.
- Python environment may vary across machines. Mitigation: use `.venv` inside `apps/api` and record activation commands.
- README and docs can drift again. Mitigation: keep README wording generic but explicit: `Python FastAPI backend API organized as a modular monolith`.
