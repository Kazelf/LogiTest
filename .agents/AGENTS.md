## Skills → Pattern Mapping

| #   | Skill         | Pattern          | SDLC Phase     | Demo    |
| --- | ------------- | ---------------- | -------------- | ------- |
| 1   | `/fix`        | Single Agent     | Bug Fix        | Demo 01 |
| 2   | `/brainstorm` | Multi-Agent      | Ideation       | Demo 02 |
| 3   | `/plan`       | Sequential       | Planning       | Demo 03 |
| 4   | `/cook`       | Parallel         | Implementation | Demo 04 |
| 5   | `/loop`       | Conditional+Loop | Incident Fix   | Demo 05 |
| —   | `/scout`      | (internal)       | Discovery      | —       |
| —   | `/git`        | (finalize)       | Commit         | Demo 06 |
| —   | `/docs`       | (finalize)       | Documentation  | Demo 06 |

## Full Lifecycle (Demo 06)

```
/brainstorm → /plan → /cook → /loop → /git → /docs
```

## Agents

Sub-agents that skills delegate to:

- `planner` — Creates implementation plans
- `tester` — Runs test suites, validates
- `code-reviewer` — Reviews code quality
- `debugger` — Investigates root causes
- `docs-manager` — Updates documentation
- `fullstack-developer` — Implements features (parallel mode)
- `git-manager` — Git operations
- `researcher` — Researches solutions

## Project

Express + TypeScript demo app with planted bugs for demonstration.

```bash
npm install     # Install deps
npm test        # Shows planted bug (TypeError in auth)
./reset.sh      # Reset to demo-ready state
```
