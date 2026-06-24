---
phase: 2
title: "Implement script renderers and file output"
status: completed
priority: P2
effort: "2h"
dependencies: [phase-01]
---

# Phase 02: Implement Script Renderers And File Output

## Overview

Implement deterministic renderers that convert the existing API test case JSON spec into TypeScript test code for Playwright API, Jest/Supertest, and Mocha/Supertest.

## Requirements

- Functional: render code from `steps`, `assertions`, and `golden_response` without LLM.
- Functional: support `GET`, `POST`, `PUT`, `PATCH`, `DELETE` style methods.
- Functional: include status assertions and top-level response property assertions.
- Functional: optionally write generated files to controlled paths.
- Non-functional: generated code should be readable and demo-friendly, not necessarily executable in this repo yet.

## Architecture

Add renderer helpers inside `test_generation`:

```text
test_case spec
-> render_script(framework, test_case)
   -> render_playwright_api(...)
   -> render_jest_supertest(...)
   -> render_mocha_supertest(...)
-> maybe_write_generated_file(framework, test_case_name, code)
```

Output folders:

```text
logitest-ai/generated-tests/playwright/*.spec.ts
logitest-ai/generated-tests/jest/*.spec.ts
logitest-ai/generated-tests/mocha/*.spec.ts
```

File path safety:

- Caller cannot provide arbitrary path.
- Filename built from sanitized test case name.
- Resolve path and assert it stays under `generated-tests/` before writing.

## Related Code Files

- Create or modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\renderers.py`
- Modify: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api\app\modules\test_generation\service.py`
- Create directory at runtime only: `D:\ViettelDigitalTalent\LogiTest\logitest-ai\generated-tests\...`

## Implementation Steps

1. Define renderer input shape using existing serialized test case fields.
2. Implement reusable helpers:
   - slugify/sanitize filename.
   - TypeScript object literal rendering via JSON serialization.
   - HTTP method mapping.
   - response property assertion generation.
3. Implement `render_playwright_api` using `@playwright/test` request fixture.
4. Implement `render_jest_supertest` using `supertest` and Jest `expect`.
5. Implement `render_mocha_supertest` using `supertest` plus Chai `expect`.
6. Implement optional `write_generated_file(framework, name, code)` with safe base path.
7. Unit test renderers without DB.

## Success Criteria

- [x] Each framework renderer outputs recognizable TypeScript test code.
- [x] Rendered code includes all steps in order.
- [x] Rendered code includes status assertions.
- [x] Response body property assertions are derived from `response_schema` assertions or `golden_response` object keys.
- [x] File write path cannot escape `generated-tests/`.

## Risk Assessment

- Risk: generated code may not run without dependencies. Mitigation: explicitly document this task generates artifacts only; execution comes later.
- Risk: code formatting gets messy. Mitigation: deterministic simple templates; no formatter dependency in this phase.
