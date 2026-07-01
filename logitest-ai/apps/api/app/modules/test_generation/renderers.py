from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.modules.test_generation.schemas import GeneratedTestFramework

DYNAMIC_RESPONSE_KEYS = {
    "cartId",
    "cart_id",
    "createdAt",
    "created_at",
    "id",
    "orderId",
    "order_id",
    "productId",
    "product_id",
    "requestId",
    "request_id",
    "timestamp",
    "token",
    "traceId",
    "trace_id",
    "updatedAt",
    "updated_at",
    "userId",
    "user_id",
}

def _find_project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "package.json").exists() and (parent / "apps" / "api").exists():
            return parent
    return Path(__file__).resolve().parents[3]

PROJECT_ROOT = _find_project_root()
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
        'const baseURL = process.env.TARGET_BASE_URL || "http://localhost:4000";',
        "",
        f'describe("{_escape_string(test_case["name"])}", () => {{',
        '  it("replays learned behavior journey", async () => {',
    ]
    extractions: dict[str, dict[str, Any]] = {}
    for step in test_case["steps"]:
        lines.extend(_render_supertest_step(step, expect_style="jest", extractions=extractions))
        extractions.update(_step_extractions(step))
        lines.append("")
    lines.extend(["  });", "});"])
    return "\n".join(lines)


def render_mocha_supertest(test_case: dict[str, Any]) -> str:
    lines = [
        'import request from "supertest";',
        'import { expect } from "chai";',
        "",
        'const baseURL = process.env.TARGET_BASE_URL || "http://localhost:4000";',
        "",
        f'describe("{_escape_string(test_case["name"])}", () => {{',
        '  it("replays learned behavior journey", async () => {',
    ]
    extractions: dict[str, dict[str, Any]] = {}
    for step in test_case["steps"]:
        lines.extend(_render_supertest_step(step, expect_style="mocha", extractions=extractions))
        extractions.update(_step_extractions(step))
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


def _render_supertest_step(step: dict[str, Any], *, expect_style: str, extractions: dict[str, dict[str, Any]] | None = None) -> list[str]:
    extractions = extractions or {}
    step_name = _step_var(step)
    method = _method(step)
    endpoint = _endpoint_literal(str(step.get("endpoint") or "/"), step.get("uses") or {}, extractions)
    payload = step.get("request_payload") or {}
    lines = [f"    const {step_name}Start = Date.now();", f"    const {step_name} = await request(baseURL)", f"      .{method}({endpoint})"]
    if _method_has_body(method):
        lines.append(f"      .send({_to_ts_literal_with_vars(payload, extractions)})")
    lines[-1] = f"{lines[-1]};"
    if expect_style == "jest":
        lines.append(f"    expect({step_name}.status).toBe({step.get('expected_status')});")
        for key in _response_keys(step):
            lines.append(f'    expect({step_name}.body).toHaveProperty("{_escape_string(key)}");')
        for path, value in _stable_response_fields(step):
            lines.append(f"    expect({_body_path_accessor(step_name, path)}).toEqual({_to_ts_literal(value)});")
        lines.extend(_render_jest_response_time_assertion(step, step_name))
    else:
        lines.append(f"    expect({step_name}.status).to.equal({step.get('expected_status')});")
        for key in _response_keys(step):
            lines.append(f'    expect({step_name}.body).to.have.property("{_escape_string(key)}");')
        for path, value in _stable_response_fields(step):
            lines.append(f"    expect({_body_path_accessor(step_name, path)}).to.deep.equal({_to_ts_literal(value)});")
        lines.extend(_render_mocha_response_time_assertion(step, step_name))
    for field_name, extraction in _step_extractions(step).items():
        lines.append(f"    const {extraction['variable']} = {_response_path_accessor(step_name, extraction['path'])};")
    return lines


def _response_keys(step: dict[str, Any]) -> list[str]:
    golden_response = step.get("golden_response")
    if isinstance(golden_response, dict):
        return sorted(str(key) for key in golden_response.keys())
    return []

def _stable_response_fields(step: dict[str, Any]) -> list[tuple[str, Any]]:
    golden_response = step.get("golden_response")
    return _iter_stable_response_fields(golden_response) if isinstance(golden_response, dict) else []

def _iter_stable_response_fields(value: Any, path: str = "body") -> list[tuple[str, Any]]:
    fields: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, entry_value in value.items():
            if key in DYNAMIC_RESPONSE_KEYS:
                continue
            entry_path = f"{path}.{key}"
            if isinstance(entry_value, dict):
                fields.extend(_iter_stable_response_fields(entry_value, entry_path))
            elif isinstance(entry_value, list):
                continue
            elif isinstance(entry_value, (str, int, float, bool)) or entry_value is None:
                fields.append((entry_path, entry_value))
    return fields

def _render_jest_response_time_assertion(step: dict[str, Any], step_name: str) -> list[str]:
    threshold = _response_time_threshold(step)
    return [f"    expect(Date.now() - {step_name}Start).toBeLessThanOrEqual({threshold});"] if threshold else []

def _render_mocha_response_time_assertion(step: dict[str, Any], step_name: str) -> list[str]:
    threshold = _response_time_threshold(step)
    return [f"    expect(Date.now() - {step_name}Start).to.be.at.most({threshold});"] if threshold else []

def _response_time_threshold(step: dict[str, Any]) -> int | None:
    response_time_ms = step.get("response_time_ms")
    if isinstance(response_time_ms, int) and response_time_ms > 0:
        return max(1000, response_time_ms * 3)
    return None

def _step_extractions(step: dict[str, Any]) -> dict[str, dict[str, Any]]:
    golden_response = step.get("golden_response") if isinstance(step.get("golden_response"), dict) else {}
    return {
        field_name: {
            "path": str(path),
            "value": _value_at_response_path(golden_response, str(path)),
            "variable": _variable_name(field_name),
        }
        for field_name, path in (step.get("extract") or {}).items()
    }

def _endpoint_literal(endpoint: str, uses: dict[str, Any], extractions: dict[str, dict[str, Any]]) -> str:
    rendered = endpoint
    used_variable = False
    for field_name, location in uses.items():
        extraction = extractions.get(field_name)
        if location != "path" or not extraction or extraction.get("value") in (None, ""):
            continue
        value = str(extraction["value"])
        if value in rendered:
            rendered = rendered.replace(value, f"${{{extraction['variable']}}}")
            used_variable = True
    if used_variable:
        return f"`{_escape_template(rendered)}`"
    return f'"{_escape_string(rendered)}"'

def _to_ts_literal_with_vars(value: Any, extractions: dict[str, dict[str, Any]]) -> str:
    variable = _matching_extraction_variable(value, extractions)
    if variable is not None:
        return variable
    if isinstance(value, dict):
        if not value:
            return "{}"
        entries = [
            f"{json.dumps(str(key), ensure_ascii=False)}: {_to_ts_literal_with_vars(entry_value, extractions)}"
            for key, entry_value in value.items()
        ]
        return "{\n        " + ",\n        ".join(entries) + "\n      }"
    if isinstance(value, list):
        if not value:
            return "[]"
        return "[" + ", ".join(_to_ts_literal_with_vars(item, extractions) for item in value) + "]"
    return _to_ts_literal(value)

def _matching_extraction_variable(value: Any, extractions: dict[str, dict[str, Any]]) -> str | None:
    for extraction in extractions.values():
        extracted_value = extraction.get("value")
        if extracted_value is not None and (value == extracted_value or str(value) == str(extracted_value)):
            return str(extraction["variable"])
    return None

def _value_at_response_path(response_body: dict[str, Any], path: str) -> Any:
    current: Any = response_body
    normalized = path.removeprefix("response.body").removeprefix("body").lstrip(".")
    if not normalized:
        return current
    for segment in normalized.split("."):
        if isinstance(current, dict):
            current = current.get(segment)
        else:
            return None
    return current

def _response_path_accessor(step_name: str, path: str) -> str:
    normalized = path.removeprefix("response.body").removeprefix("body").lstrip(".")
    return ".".join([f"{step_name}.body", *[segment for segment in normalized.split(".") if segment]])

def _body_path_accessor(step_name: str, path: str) -> str:
    normalized = path.removeprefix("body").lstrip(".")
    return ".".join([f"{step_name}.body", *[segment for segment in normalized.split(".") if segment]])

def _variable_name(field_name: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in str(field_name))
    parts = [part for part in cleaned.split("_") if part]
    if not parts:
        return "extractedValue"
    return parts[0][:1].lower() + parts[0][1:] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


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

def _escape_template(value: str) -> str:
    return value.replace("\\", "\\\\").replace("`", "\\`")
