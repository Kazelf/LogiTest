---
phase: 4
title: "Wire local development config"
status: pending
priority: P2
effort: "30m"
dependencies: [phase-02, phase-03]
---

# Phase 4: Wire Local Development Config

## Overview

Add small local-development documentation and environment defaults so both apps are easy to run consistently.

## Requirements

- Functional: developers can discover frontend and backend run commands from README files.
- Non-functional: avoid adding heavy monorepo tooling unless needed.

## Architecture

Keep each app self-contained for now. Frontend uses npm inside `apps/web`; backend uses Python virtual environment inside `apps/api`.

## Related Code Files

- Modify: `logitest-ai/README.md`
- Create or modify: `logitest-ai/apps/api/README.md`
- Create or modify: `logitest-ai/apps/web/.env.example` if frontend needs backend URL.
- Modify: `logitest-ai/.env.example` if shared env names already exist.

## Implementation Steps

1. Add frontend environment example if needed:

   ```text
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

2. Add backend README run commands:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
   .\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
   ```

3. Update root README app descriptions:

   ```text
   apps/web: Next.js frontend dashboard.
   apps/api: Python FastAPI backend API organized as a modular monolith.
   ```

4. Do not add Docker Compose in this task unless explicitly requested later.

## Success Criteria

- [ ] README gives correct run commands for both apps.
- [ ] Environment variable names are documented.
- [ ] No Express wording is reintroduced.

## Risk Assessment

Low risk. Biggest risk is prematurely adding workspace tooling. Keep this phase focused on documentation and env examples.

