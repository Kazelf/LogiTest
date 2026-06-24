---
phase: 3
title: "Persist artifacts and extend APIs"
status: completed
priority: P2
effort: "2.5h"
dependencies: [phase-01, phase-02]
---

# Phase 03: Persist Artifacts And Extend APIs

## Overview

Wire script rendering into the existing generation flow, persist artifacts in PostgreSQL, and expose artifact data through test case detail and artifact-specific APIs.

## Requirements

- Functional: generation flow creates or updates `test_cases`, then creates or updates `test_case_artifacts` for requested frameworks.
- Functional: artifact upsert key is `(test_case_id, framework)`.
- Functional: detail API returns all artifacts for a test case.
- Functional: add artifact list/detail endpoints for lightweight code retrieval.
- Non-functional: preserve existing list endpoint shape as much as possible.

## Architecture

Service flow extension:

```text
generate_test_case(... frameworks, write_files)
-> existing journey/log fetch
-> existing test case draft + upsert
-> for each framework:
     render code
     optional write file
     upsert artifact
-> update test_cases.generated_code with first artifact code
-> return artifact summaries
```

New optional endpoints:

```text
GET /api/test-generation/test-cases/{test_case_id}/artifacts
GET /api/test-generation/test-cases/{test_case_id}/artifacts/{framework}
```

## Related Code Files

- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\service.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\router.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\schemas.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_test_generation_api.py`
- Reference: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\tests\test_test_generation_service.py`

## Implementation Steps

1. Extend `generate_test_case` signature with `frameworks` and `write_files`.
2. Keep default behavior working for old caller shape.
3. Add `_upsert_test_case_artifact` helper.
4. Add `_fetch_test_case_artifacts` and `_fetch_test_case_artifact` helpers.
5. Extend `get_test_case_detail` serializer to include artifacts.
6. Add service methods `list_test_case_artifacts` and `get_test_case_artifact`.
7. Add router endpoints and error mapping:
   - missing test case/artifact -> `404`.
   - DB unavailable -> `503`.
   - invalid framework handled by Pydantic -> `422`.
8. Update list/detail tests.

## Success Criteria

- [x] Multiple frameworks can be generated in one request.
- [x] Re-running generation updates artifacts instead of duplicating them.
- [x] Detail endpoint includes artifacts with code.
- [x] Artifact endpoints return expected metadata/code.
- [x] Old generate request body still works.

## Risk Assessment

- Risk: generated artifacts and `test_cases.generated_code` diverge. Mitigation: define `generated_code` as compatibility mirror of the first requested artifact.
- Risk: large code strings make detail responses heavy. Mitigation: list remains compact; dedicated artifact endpoint supports targeted retrieval.
