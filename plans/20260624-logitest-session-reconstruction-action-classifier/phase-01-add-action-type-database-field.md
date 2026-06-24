---
phase: 1
title: "Add action_type database field"
status: completed
priority: P2
effort: "1h"
dependencies: []
---

# Phase 01: Add Action Type Database Field

## Overview

Extend the existing `logs` table so classified action types can be persisted for later API/dashboard tasks.

## Requirements

- Functional: add `logs.action_type` as `TEXT NOT NULL DEFAULT 'unknown'`.
- Functional: add an index for future action-type filtering.
- Non-functional: keep current DB naming and direct SQL migration style.
- Non-functional: avoid PostgreSQL enum because action labels may evolve during MVP work.

## Architecture

The project currently uses a single SQL migration file instead of Alembic. Update the existing schema definition so fresh local environments create the new column and index by default. If the developer has an existing local database, document that they may need to re-run setup or apply an equivalent `ALTER TABLE` manually until migration tooling exists.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\database\migrations\001_init_logitest_schema.sql`
- Optionally modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\database\README.md`

## Implementation Steps

1. Add `action_type TEXT NOT NULL DEFAULT 'unknown'` to the `logs` table definition.
2. Add `CREATE INDEX IF NOT EXISTS idx_logs_action_type ON logs(action_type);` near the existing `logs` indexes.
3. Document the manual update note if the database README already explains local setup.
4. Do not modify API schemas in this phase.

## Success Criteria

- [x] Fresh schema creation includes the `action_type` column.
- [x] Fresh schema creation includes `idx_logs_action_type`.
- [x] No API response model includes `action_type` yet.

## Risk Assessment

Existing local databases created before this phase will not automatically have the column. Keep the plan honest: either reset local DB for MVP or run a manual `ALTER TABLE` until formal migrations are introduced.
