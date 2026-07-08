from __future__ import annotations

from typing import Any

DEFAULT_IGNORED_PATHS = {
    "$.accessToken",
    "$.cartItemId",
    "$.cart_item_id",
    "$.createdAt",
    "$.created_at",
    "$.data.id",
    "$.data.orderId",
    "$.data.order_id",
    "$.meta.trace_id",
    "$.paymentId",
    "$.payment_id",
    "$.refreshToken",
    "$.removed_cart_item_id",
    "$.requestId",
    "$.request_id",
    "$.sessionId",
    "$.session_id",
    "$.token",
    "$.traceId",
    "$.trace_id",
    "$.updatedAt",
    "$.updated_at",
}

DEFAULT_IGNORED_KEYS = {
    "accessToken",
    "cartId",
    "cart_id",
    "cartItemId",
    "cart_item_id",
    "count",
    "createdAt",
    "created_at",
    "discount_amount",
    "id",
    "items",
    "line_total",
    "orderId",
    "order_id",
    "orderItemId",
    "order_item_id",
    "orders",
    "paymentId",
    "payment_id",
    "productId",
    "product_id",
    "quantity",
    "refreshToken",
    "removedCartItemId",
    "removed_cart_item_id",
    "result_count",
    "requestId",
    "request_id",
    "sessionId",
    "session_id",
    "stock",
    "subtotal_amount",
    "token",
    "total_amount",
    "traceId",
    "trace_id",
    "unit_price",
    "updatedAt",
    "updated_at",
    "userId",
    "user_id",
}

TYPE_MAP = {
    "status_code": "status_code",
    "schema": "schema",
    "business_field": "business_field",
    "response_time": "response_time",
    "chaining": "chaining",
}

def compare_steps(
    expected_steps: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
    actual_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    diffs: list[dict[str, Any]] = []
    ignored_fields: set[str] = set()
    actual_by_order = {int(step["order"]): step for step in actual_steps}
    expected_by_order = {int(step.get("order") or index + 1): step for index, step in enumerate(expected_steps)}
    used_extracts = {str(name) for step in expected_steps for name in (step.get("uses") or {}).keys()}

    for order, expected_step in expected_by_order.items():
        actual_step = actual_by_order.get(order)
        if actual_step is None:
            diffs.append(_diff(order, "schema", "$", expected_step.get("endpoint"), None, "high", "Expected step was not executed."))
            continue

        expected_status = expected_step.get("expected_status")
        if expected_status is not None and actual_step.get("status_code") != expected_status:
            diffs.append(
                _diff(
                    order,
                    "status_code",
                    "$.status_code",
                    expected_status,
                    actual_step.get("status_code"),
                    "high",
                    "Status code mismatch.",
                )
            )

        golden_response = expected_step.get("golden_response")
        if isinstance(golden_response, dict):
            actual_body = actual_step.get("response_body")
            _compare_schema(order, golden_response, actual_body, "$", diffs)
            _compare_business_fields(order, golden_response, actual_body, "$", diffs, ignored_fields)

        for name, path in (expected_step.get("extract") or {}).items():
            if str(name) not in used_extracts:
                continue
            if name in (actual_step.get("extracted") or {}):
                continue
            if _value_at_path({"response": {"body": actual_step.get("response_body")}, "body": actual_step.get("response_body")}, str(path)) is None:
                diffs.append(
                    _diff(
                        order,
                        "chaining",
                        _json_path(str(path)),
                        "value to extract",
                        None,
                        "high",
                        f"Chained variable '{name}' was missing.",
                    )
                )

    for assertion in assertions:
        if assertion.get("type") != "response_time_ms":
            continue
        order = int(assertion.get("order") or 0)
        max_ms = ((assertion.get("expected") or {}).get("max_ms")) if isinstance(assertion.get("expected"), dict) else None
        actual_step = actual_by_order.get(order)
        actual_ms = actual_step.get("duration_ms") if actual_step else None
        if isinstance(max_ms, int) and isinstance(actual_ms, int) and actual_ms > max_ms:
            diffs.append(_diff(order, "response_time", "$.duration_ms", max_ms, actual_ms, "medium", "Response time threshold exceeded."))

    status = "passed" if not diffs else "failed"
    passed_steps = len(actual_steps) - len({diff["order"] for diff in diffs})
    summary = f"{status}: {len(diffs)} diff(s), {len(ignored_fields)} ignored dynamic field(s)."
    return {
        "status": status,
        "summary": summary,
        "diffs": diffs,
        "differences": diffs,
        "ignoredFields": sorted(ignored_fields),
        "counts": {"passed": max(passed_steps, 0), "failed": len(diffs), "errored": 0},
    }

def _compare_schema(order: int, golden: Any, actual: Any, path: str, diffs: list[dict[str, Any]]) -> None:
    if isinstance(golden, dict):
        if not isinstance(actual, dict):
            diffs.append(_diff(order, "schema", path, "object", type(actual).__name__, "high", "Response schema type mismatch."))
            return
        for key, expected_value in golden.items():
            child_path = f"{path}.{key}"
            if _is_ignored(child_path):
                continue
            if key not in actual:
                diffs.append(_diff(order, "schema", child_path, "present", "missing", "high", "Required response field is missing."))
                continue
            if isinstance(expected_value, (dict, list)):
                _compare_schema(order, expected_value, actual[key], child_path, diffs)
    elif isinstance(golden, list):
        if not isinstance(actual, list):
            diffs.append(_diff(order, "schema", path, "array", type(actual).__name__, "high", "Response schema type mismatch."))
            return
        if golden and actual:
            _compare_schema(order, golden[0], actual[0], f"{path}[0]", diffs)

def _compare_business_fields(
    order: int,
    expected: Any,
    actual: Any,
    path: str,
    diffs: list[dict[str, Any]],
    ignored_fields: set[str],
) -> None:
    if _is_ignored(path):
        ignored_fields.add(path)
        return
    if isinstance(expected, dict):
        for key, value in expected.items():
            _compare_business_fields(order, value, actual.get(key) if isinstance(actual, dict) else None, f"{path}.{key}", diffs, ignored_fields)
        return
    if isinstance(expected, list):
        if not isinstance(actual, list):
            diffs.append(_diff(order, "business_field", path, expected, actual, "medium", "Business field array changed."))
            return
        if len(actual) != len(expected):
            diffs.append(_diff(order, "business_field", path, len(expected), len(actual), "medium", "Business array length changed."))
        for index, value in enumerate(expected):
            if index < len(actual):
                _compare_business_fields(order, value, actual[index], f"{path}[{index}]", diffs, ignored_fields)
        return
    if isinstance(expected, (str, int, float, bool)) or expected is None:
        if expected == "***MASKED***":
            ignored_fields.add(path)
            return
        if actual != expected:
            diffs.append(_diff(order, "business_field", path, expected, actual, "medium", "Business field mismatch."))

def _is_ignored(path: str) -> bool:
    key = path.rsplit(".", 1)[-1].split("[", 1)[0]
    return path in DEFAULT_IGNORED_PATHS or key in DEFAULT_IGNORED_KEYS

def _diff(order: int, diff_type: str, path: str, expected: Any, actual: Any, severity: str, message: str) -> dict[str, Any]:
    return {
        "order": order,
        "type": TYPE_MAP[diff_type],
        "path": path,
        "expected": expected,
        "actual": actual,
        "severity": severity,
        "message": message,
    }

def _value_at_path(source: Any, path: str) -> Any:
    current = source
    for token in path.replace("[", ".").replace("]", "").split("."):
        if token == "":
            continue
        if isinstance(current, dict):
            current = current.get(token)
        elif isinstance(current, list) and token.isdigit():
            index = int(token)
            current = current[index] if index < len(current) else None
        else:
            return None
    return current

def _json_path(path: str) -> str:
    return "$." + path.removeprefix("response.body.").removeprefix("body.").lstrip(".")
