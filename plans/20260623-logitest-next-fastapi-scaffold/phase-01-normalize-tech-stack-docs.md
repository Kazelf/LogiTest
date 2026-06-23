---
phase: 1
title: "Normalize tech stack docs"
status: pending
priority: P1
effort: "15m"
dependencies: []
---

# Phase 1: Normalize Tech Stack Docs

## Overview

Make documentation consistently say that LogiTest AI backend uses Python FastAPI, not Express.

## Requirements

- Functional: remove stale Express references for the LogiTest AI backend.
- Non-functional: keep wording consistent with `docs/logitest-ai-tech-stack.md`.

## Architecture

This is documentation alignment only. The backend architecture remains FastAPI modular monolith.

## Related Code Files

- Modify: `logitest-ai/README.md`
- Modify: `docs/AI-Driven-Behavioral-Testing-Platform.md`
- Modify: `docs/logitest-ai-tech-stack.md` if API testing stack mentions Node-only tooling.

## Implementation Steps

1. Search for stale stack terms:

   ```powershell
   rg -n "Express|express|Supertest|apps/api" D:\ViettelDigitalTalent\LogiTest\docs D:\ViettelDigitalTalent\LogiTest\logitest-ai\README.md -g "*.md"
   ```

2. Replace LogiTest AI backend wording with FastAPI wording.
3. Replace Node-only API testing wording with `pytest + requests / httpx`.
4. Re-run the search and confirm no Express reference remains for LogiTest AI backend.

## Success Criteria

- [ ] `rg -n "Express|express|Supertest" D:\ViettelDigitalTalent\LogiTest\docs D:\ViettelDigitalTalent\LogiTest\logitest-ai\README.md -g "*.md"` returns no stale backend app references.
- [ ] README says `apps/api` is Python FastAPI.
- [ ] Tech stack docs align with FastAPI backend testing.

## Risk Assessment

Low risk. Main risk is changing historical concept docs too aggressively. Only update lines that describe the selected implementation stack.
