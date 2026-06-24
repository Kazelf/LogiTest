from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.modules.test_generation.schemas import GeneratedTestFramework

PROJECT_ROOT = Path(__file__).resolve().parents[5]
GENERATED_TESTS_ROOT = PROJECT_ROOT / "generated-tests"

FRAMEWORK_DIRECTORIES = {
    GeneratedTestFramework.PLAYWRIGHT_API: "playwright",
    GeneratedTestFramework.JEST_SUPERTEST: "jest",
    GeneratedTestFramework.MOCHA_SUPERTEST: "mocha",
}


def render_script(*, framework: GeneratedTestFramework, test_case: dict[str, Any]) -> str:
    if framework == GeneratedTestFramework.PLAYWRIGHT_API:
        return render_playwright_api(test_case)
    if framework == GeneratedTestFramework.JEST_SUPERTEST:
        return render_jest_supertest(test_case)
    if framework == GeneratedTestFramework.MOCHA_SUPERTEST:
        return render_mocha_supertest(test_case)
    raise ValueError(f"Unsupported framework: {framework}")


def render_playwright_api(test_case: dict[str, Any]) -> str:
    lines = [
        'import { test, expect } from "@playwright/test";',
        "",
        f'test("{_escape_string(test_case["name"])}", async ({{ request }}) => {{',
    ]
    for step in test_case["steps"]:
        step_name = _step_var(step)
        method = _method(step)
        endpoint = _escape_string(str(step.get("endpoint") or "/"))
        payload = step.get("request_payload") or {}
        if _method_has_body(method):
            lines.extend(
                [
                    f'  const {step_name} = await request.{method}("{endpoint}", {{',
                    f"    data: {_to_ts_literal(payload)},",
                    "  });",
                ]
            )
        else:
            lines.append(f'  const {step_name} = await request.{method}("{endpoint}");')
        lines.append(f"  expect({step_name}.status()).toBe({step.get('expected_status')});")
        lines.extend(_render_playwright_body_assertions(step, step_name))
        lines.append("")
    lines.append("});")
    return "\n".join(lines)


def render_jest_supertest(test_case: dict[str, Any]) -> str:
    lines = [
        'import request from "supertest";',
        "",
        'const baseURL = process.env.TARGET_BASE_URL || "http://localhost:3001";',
        "",
        f'describe("{_escape_string(test_case["name"])}", () => {{',
        '  it("replays learned behavior journey", async () => {',
    ]
    for step in test_case["steps"]:
        lines.extend(_render_supertest_step(step, expect_style="jest"))
        lines.append("")
    lines.extend(["  });", "});"])
    return "\n".join(lines)


def render_mocha_supertest(test_case: dict[str, Any]) -> str:
    lines = [
        'import request from "supertest";',
        'import { expect } from "chai";',
        "",
        'const baseURL = process.env.TARGET_BASE_URL || "http://localhost:3001";',
        "",
        f'describe("{_escape_string(test_case["name"])}", () => {{',
        '  it("replays learned behavior journey", async () => {',
    ]
    for step in test_case["steps"]:
        lines.extend(_render_supertest_step(step, expect_style="mocha"))
        lines.append("")
    lines.extend(["  });", "});"])
    return "\n".join(lines)


def write_generated_file(*, framework: GeneratedTestFramework, test_case_name: str, code: str) -> str:
    directory_name = FRAMEWORK_DIRECTORIES[framework]
    file_name = f"{slugify(test_case_name)}.spec.ts"
    output_dir = GENERATED_TESTS_ROOT / directory_name
    output_path = (output_dir / file_name).resolve()
    root_path = GENERATED_TESTS_ROOT.resolve()
    if root_path != output_path and root_path not in output_path.parents:
        raise ValueError("Generated file path escapes generated-tests directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code, encoding="utf-8")
    return output_path.relative_to(PROJECT_ROOT).as_posix()


def slugify(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "generated-api-test"


def _render_playwright_body_assertions(step: dict[str, Any], step_name: str) -> list[str]:
    keys = _response_keys(step)
    if not keys:
        return []
    body_name = f"{step_name}Body"
    lines = [f"  const {body_name} = await {step_name}.json();"]
    for key in keys:
        lines.append(f'  expect({body_name}).toHaveProperty("{_escape_string(key)}");')
    return lines


def _render_supertest_step(step: dict[str, Any], *, expect_style: str) -> list[str]:
    step_name = _step_var(step)
    method = _method(step)
    endpoint = _escape_string(str(step.get("endpoint") or "/"))
    payload = step.get("request_payload") or {}
    lines = [f"    const {step_name} = await request(baseURL)", f'      .{method}("{endpoint}")']
    if _method_has_body(method):
        lines.append(f"      .send({_to_ts_literal(payload)})")
    lines[-1] = f"{lines[-1]};"
    if expect_style == "jest":
        lines.append(f"    expect({step_name}.status).toBe({step.get('expected_status')});")
        for key in _response_keys(step):
            lines.append(f'    expect({step_name}.body).toHaveProperty("{_escape_string(key)}");')
    else:
        lines.append(f"    expect({step_name}.status).to.equal({step.get('expected_status')});")
        for key in _response_keys(step):
            lines.append(f'    expect({step_name}.body).to.have.property("{_escape_string(key)}");')
    return lines


def _response_keys(step: dict[str, Any]) -> list[str]:
    golden_response = step.get("golden_response")
    if isinstance(golden_response, dict):
        return sorted(str(key) for key in golden_response.keys())
    return []


def _step_var(step: dict[str, Any]) -> str:
    return f"step{int(step.get('order') or 1)}"


def _method(step: dict[str, Any]) -> str:
    return str(step.get("method") or "GET").lower()


def _method_has_body(method: str) -> bool:
    return method in {"post", "put", "patch", "delete"}


def _to_ts_literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2).replace("\n", "\n      ")


def _escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
