---
phase: 1
title: "Design artifact schema and API contracts"
status: completed
priority: P2
effort: "2h"
dependencies: []
---

# Phase 01: Design Artifact Schema And API Contracts

## Overview

Add a clean persistence model for multiple generated scripts per test case and update API schemas to represent requested frameworks and returned artifacts.

## Requirements

- Functional: introduce `test_case_artifacts` table for generated code artifacts.
- Functional: extend generation request with `frameworks` and `write_files` while preserving current request compatibility.
- Functional: extend generation/detail responses with artifact metadata.
- Non-functional: avoid stuffing multiple scripts into `test_cases.generated_code`.

## Architecture

New DB table:

```sql
CREATE TABLE IF NOT EXISTS test_case_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    framework TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'typescript',
    file_path TEXT,
    code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (test_case_id, framework)
);

CREATE INDEX IF NOT EXISTS idx_test_case_artifacts_test_case_id
    ON test_case_artifacts(test_case_id);
```

Framework enum values:

- `playwright_api`
- `jest_supertest`
- `mocha_supertest`

Backward compatibility rule: if request omits `frameworks`, default to `['playwright_api']` or an existing single-code default agreed in implementation. Keep `generated_code` populated with first rendered artifact.

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\database\migrations\001_init_logitest_schema.sql`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\schemas.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\service.py`

## Implementation Steps

1. Add `test_case_artifacts` table and index to existing idempotent SQL migration.
2. Add `GeneratedTestFramework` enum or literal validation in Pydantic schemas.
3. Extend `GenerateTestCaseRequest` with `frameworks: list[...] = ['playwright_api']` and `write_files: bool = False`.
4. Add artifact response models: `GeneratedArtifactSummary`, `GeneratedArtifactDetail`.
5. Extend `GenerateTestCaseResponse` with `artifacts`.
6. Extend `TestCaseDetailResponse` with `artifacts`, keeping existing fields unchanged.

## Success Criteria

- [x] SQL migration remains idempotent.
- [x] Schema defaults preserve old `journey_id` + `overwrite` requests.
- [x] Invalid framework values produce request validation failure.
- [x] Response models represent multiple artifacts cleanly.

## Risk Assessment

- Risk: editing original migration may not affect existing DB volume. Mitigation: also document manual SQL apply/reset workflow; MVP repo currently uses raw idempotent migration, not Alembic.
- Risk: framework enum names leak into UI later. Mitigation: use stable explicit values, not display labels.
