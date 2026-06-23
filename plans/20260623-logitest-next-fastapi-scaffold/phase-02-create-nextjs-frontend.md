---
phase: 2
title: "Create Next.js frontend app"
status: pending
priority: P1
effort: "30m"
dependencies: [phase-01]
---

# Phase 2: Create Next.js Frontend App

## Overview

Create the initial dashboard app in `logitest-ai/apps/web` using Next.js, TypeScript, Tailwind CSS, ESLint, and the App Router.

## Requirements

- Functional: `apps/web` starts locally and renders the default app page.
- Non-functional: use TypeScript and Tailwind to match docs.

## Architecture

The frontend is a Next.js dashboard that will later call the FastAPI backend. For this task, only scaffold the app and keep the default page minimal.

## Related Code Files

- Create: `logitest-ai/apps/web/package.json`
- Create: `logitest-ai/apps/web/src/app/page.tsx`
- Create: `logitest-ai/apps/web/src/app/layout.tsx`
- Create: `logitest-ai/apps/web/src/app/globals.css`

## Implementation Steps

1. Move into monorepo root:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai
   ```

2. Confirm `apps/web` is empty or absent:

   ```powershell
   Get-ChildItem -Force .\apps\web -ErrorAction SilentlyContinue
   ```

3. Scaffold the app:

   ```powershell
   npx create-next-app@latest .\apps\web --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
   ```

4. If the CLI prompts for options, choose the defaults that preserve TypeScript, Tailwind, ESLint, App Router, and `src` directory.
5. Start the app:

   ```powershell
   cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\web
   npm run dev
   ```

## Success Criteria

- [ ] `apps/web/package.json` exists.
- [ ] `npm run dev` starts without compile errors.
- [ ] Browser can open `http://localhost:3000`.
- [ ] Tailwind CSS files exist and are wired by the generated Next.js app.

## Risk Assessment

Medium-low risk. `create-next-app` can refuse to scaffold into a non-empty folder. Inspect before deleting anything, because existing user files must not be removed casually.

