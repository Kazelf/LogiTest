from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.core.metrics import (
    REGRESSION_DETECTED_TOTAL,
    TEST_EXECUTION_DURATION_SECONDS,
    TEST_EXECUTION_FAIL_TOTAL,
    TEST_EXECUTION_PASS_TOTAL,
    TEST_EXECUTION_TOTAL,
)
from app.core.settings import settings
from app.db import connection
from app.modules.execution.comparator import compare_steps

RUNNER_NAME = "logitest-json-step-runner"
DYNAMIC_RESPONSE_KEYS = {
    "cartId",
    "cart_id",
    "cartItemId",
    "cart_item_id",
    "createdAt",
    "created_at",
    "id",
    "orderId",
    "order_id",
    "orderItemId",
    "order_item_id",
    "paymentId",
    "payment_id",
    "productId",
    "product_id",
    "requestId",
    "request_id",
    "removedCartItemId",
    "removed_cart_item_id",
    "timestamp",
    "token",
    "traceId",
    "trace_id",
    "updatedAt",
    "updated_at",
    "userId",
    "user_id",
}


class TestCaseNotFoundError(Exception):
    pass


class TestCaseHasNoStepsError(Exception):
    pass


class TestRunNotFoundError(Exception):
    pass


def run_test_case(
    test_case_id: str,
    *,
    target_base_url: str | None = None,
    target_environment: str = "staging",
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    base_url = _normalize_base_url(target_base_url or settings.staging_api_base_url)
    started_at = datetime.now(timezone.utc)
    start = perf_counter()
    error_message: str | None = None

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            test_case = _fetch_test_case(cur, test_case_id)
            if test_case is None:
                raise TestCaseNotFoundError(test_case_id)

            steps = list(test_case.get("steps") or [])
            if not steps:
                raise TestCaseHasNoStepsError(test_case_id)

            try:
                actual_response = _execute_steps(steps, base_url=base_url, timeout_seconds=timeout_seconds)
                diff_result = _compare_results(steps, list(test_case.get("assertions") or []), actual_response["steps"])
                status = "passed" if diff_result["status"] == "passed" else "failed"
            except Exception as exc:
                actual_response = {"steps": []}
                diff_result = {"status": "failed", "differences": [], "diffs": [], "summary": "error", "counts": {"passed": 0, "failed": 0, "errored": 1}}
                status = "error"
                error_message = str(exc)

            finished_at = datetime.now(timezone.utc)
            duration_ms = int((perf_counter() - start) * 1000)
            run = _insert_test_run(
                cur,
                test_case_id=test_case_id,
                status=status,
                target_environment=target_environment,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                actual_response=actual_response,
                diff_result=diff_result,
                error_message=error_message,
                runner_metadata={
                    "runner": RUNNER_NAME,
                    "target_base_url": base_url,
                    "timeout_seconds": timeout_seconds,
                    "test_case_name": test_case.get("name"),
                },
            )
            conn.commit()

    TEST_EXECUTION_TOTAL.inc()
    TEST_EXECUTION_DURATION_SECONDS.observe(duration_ms / 1000)
    if status == "passed":
        TEST_EXECUTION_PASS_TOTAL.inc()
    else:
        TEST_EXECUTION_FAIL_TOTAL.inc()
    if _has_regression(diff_result):
        REGRESSION_DETECTED_TOTAL.inc()
    return run


def list_test_case_runs(test_case_id: str, *, limit: int, offset: int) -> dict[str, Any]:
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if _fetch_test_case(cur, test_case_id) is None:
                raise TestCaseNotFoundError(test_case_id)
            cur.execute("SELECT COUNT(*) AS total FROM test_runs WHERE test_case_id = %s", [test_case_id])
            total = int(cur.fetchone()["total"])
            cur.execute(
                """
                SELECT
                    id,
                    test_case_id,
                    status::text AS status,
                    target_environment,
                    started_at,
                    finished_at,
                    duration_ms,
                    actual_response,
                    diff_result,
                    error_message,
                    runner_metadata,
                    created_at
                FROM test_runs
                WHERE test_case_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                [test_case_id, limit, offset],
            )
            rows = cur.fetchall()

    return {"items": [_serialize_test_run_row(row) for row in rows], "limit": limit, "offset": offset, "total": total}


def get_test_run(run_id: str) -> dict[str, Any]:
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    test_case_id,
                    status::text AS status,
                    target_environment,
                    started_at,
                    finished_at,
                    duration_ms,
                    actual_response,
                    diff_result,
                    error_message,
                    runner_metadata,
                    created_at
                FROM test_runs
                WHERE id = %s
                """,
                [run_id],
            )
            row = cur.fetchone()
            if row is None:
                raise TestRunNotFoundError(run_id)

    return _serialize_test_run_row(row)


def list_test_runs(*, limit: int, offset: int, status: str | None = None) -> dict[str, Any]:
    where_sql = "WHERE status = %s" if status else ""
    where_params: list[Any] = [status] if status else []
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM test_runs {where_sql}", where_params)
            total = int(cur.fetchone()["total"])
            cur.execute(
                f"""
                SELECT
                    id,
                    test_case_id,
                    status::text AS status,
                    target_environment,
                    started_at,
                    finished_at,
                    duration_ms,
                    actual_response,
                    diff_result,
                    error_message,
                    runner_metadata,
                    created_at
                FROM test_runs
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                [*where_params, limit, offset],
            )
            rows = cur.fetchall()

    return {"items": [_serialize_test_run_row(row) for row in rows], "limit": limit, "offset": offset, "total": total}


def _fetch_test_case(cur: Any, test_case_id: str) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT id, name, steps, assertions
        FROM test_cases
        WHERE id = %s
        """,
        [test_case_id],
    )
    return cur.fetchone()


def _execute_steps(steps: list[dict[str, Any]], *, base_url: str, timeout_seconds: float) -> dict[str, Any]:
    variables: dict[str, Any] = {}
    auth_token: str | None = None
    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=timeout_seconds) as client:
        _reset_demo_state(client, base_url)
        for step in steps:
            method = str(step.get("method") or "GET").upper()
            endpoint = str(step.get("endpoint") or "/")
            request_payload = _replace_request_body_uses(step.get("request_payload") or {}, step.get("uses") or {}, variables)
            resolved_endpoint = _replace_path_uses(endpoint, step.get("uses") or {}, variables)
            request_payload, headers = _prepare_request(step, method, resolved_endpoint, request_payload, auth_token, variables)
            step_start = perf_counter()
            request_kwargs: dict[str, Any] = {"json": request_payload if method != "GET" else None}
            if headers:
                request_kwargs["headers"] = headers
            response = client.request(
                method,
                _build_url(base_url, resolved_endpoint),
                **request_kwargs,
            )
            duration_ms = int((perf_counter() - step_start) * 1000)
            response_body = _response_body(response)
            auth_token = _extract_auth_token(response_body) or auth_token
            extracted, missing_extracts = _capture_extracts(step.get("extract") or {}, response_body, variables)
            _capture_common_variables(response_body, variables)
            result = {
                "order": int(step.get("order") or len(results) + 1),
                "method": method,
                "endpoint": endpoint,
                "resolved_endpoint": resolved_endpoint,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_body": _response_body_for_golden(response_body, step.get("golden_response")),
                "extracted": extracted,
                "missing_extracts": missing_extracts,
            }
            results.append(result)

    return {"steps": results, "variable_count": len(variables)}


def _compare_results(
    steps: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
    actual_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    return compare_steps(steps, assertions, actual_steps)

def _has_regression(diff_result: dict[str, Any]) -> bool:
    counts = diff_result.get("counts") if isinstance(diff_result.get("counts"), dict) else {}
    return bool(diff_result.get("diffs") or diff_result.get("differences") or int(counts.get("failed") or 0) > 0)

def _insert_test_run(
    cur: Any,
    *,
    test_case_id: str,
    status: str,
    target_environment: str,
    started_at: datetime,
    finished_at: datetime,
    duration_ms: int,
    actual_response: dict[str, Any],
    diff_result: dict[str, Any],
    error_message: str | None,
    runner_metadata: dict[str, Any],
) -> dict[str, Any]:
    cur.execute(
        """
        INSERT INTO test_runs (
            test_case_id,
            status,
            target_environment,
            started_at,
            finished_at,
            duration_ms,
            actual_response,
            diff_result,
            error_message,
            runner_metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING
            id,
            test_case_id,
            status::text AS status,
            target_environment,
            started_at,
            finished_at,
            duration_ms,
            actual_response,
            diff_result,
            error_message,
            runner_metadata,
            created_at
        """,
        (
            test_case_id,
            status,
            target_environment,
            started_at,
            finished_at,
            duration_ms,
            Jsonb(actual_response),
            Jsonb(diff_result),
            error_message,
            Jsonb(runner_metadata),
        ),
    )
    return _serialize_test_run_row(cur.fetchone())


def _capture_extracts(extracts: dict[str, str], response_body: Any, variables: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    captured: dict[str, Any] = {}
    missing: list[dict[str, str]] = []
    for name, path in extracts.items():
        value = _value_at_path({"response": {"body": response_body}, "body": response_body}, str(path))
        if value is None:
            value = _fallback_extract(str(name), response_body)
        if value is not None:
            variables[str(name)] = value
            captured[str(name)] = value
        else:
            missing.append({"name": str(name), "path": str(path)})
    return captured, missing

def _fallback_extract(name: str, response_body: Any) -> Any:
    if not isinstance(response_body, dict):
        return None
    if name in response_body:
        return response_body[name]
    normalized = name.replace("_", "").lower()
    if normalized == "productid":
        products = response_body.get("products")
        if isinstance(products, list) and products and isinstance(products[0], dict):
            return products[0].get("product_id") or products[0].get("productId")
        items = response_body.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0].get("product_id") or items[0].get("productId")
    return None


def _prepare_request(
    step: dict[str, Any],
    method: str,
    endpoint: str,
    payload: Any,
    auth_token: str | None,
    variables: dict[str, Any],
) -> tuple[Any, dict[str, str]]:
    headers: dict[str, str] = {}
    if not isinstance(payload, dict):
        return payload, headers

    body = dict(payload)
    authorization = body.pop("authorization", None)
    if auth_token and (authorization or not endpoint.endswith("/auth/login")):
        headers["Authorization"] = f"Bearer {auth_token}"
    if endpoint.startswith("/api/payments") and "order_id" in body and "order_id" in variables:
        body["order_id"] = variables["order_id"]
    if method == "POST" and endpoint.endswith("/auth/login"):
        if body.get("email") == "***MASKED***":
            body["email"] = _demo_email(step.get("golden_response") or {})
        if body.get("password") == "***MASKED***":
            body["password"] = "Password123"
    return body, headers

def _extract_auth_token(response_body: Any) -> str | None:
    if not isinstance(response_body, dict):
        return None
    token = response_body.get("accessToken") or response_body.get("token")
    return str(token) if token else None

def _capture_common_variables(response_body: Any, variables: dict[str, Any]) -> None:
    if not isinstance(response_body, dict):
        return
    for key in ("order_id", "orderId", "payment_id", "paymentId", "cart_id", "cartId", "user_id", "userId"):
        if response_body.get(key) not in (None, "", [], {}):
            variables[_snake_name(key)] = response_body[key]
    for container in (response_body, response_body.get("cart"), response_body.get("user")):
        if isinstance(container, dict):
            for key in ("cart_id", "cartId", "user_id", "userId"):
                if container.get(key) not in (None, "", [], {}):
                    variables[_snake_name(key)] = container[key]
    products = response_body.get("products")
    items = response_body.get("items")
    if not isinstance(items, list) and isinstance(response_body.get("cart"), dict):
        items = response_body["cart"].get("items")
    if isinstance(products, list) and products and isinstance(products[0], dict) and products[0].get("product_id"):
        variables.setdefault("product_id", products[0]["product_id"])
    if isinstance(items, list) and items and isinstance(items[0], dict):
        if items[0].get("product_id"):
            variables["product_id"] = items[0]["product_id"]
        if items[0].get("cart_item_id"):
            variables["cart_item_id"] = items[0]["cart_item_id"]

def _response_body_for_golden(actual: Any, golden: Any) -> Any:
    if not isinstance(actual, dict) or not isinstance(golden, dict):
        return actual
    if {"result_count", "first_result_id", "first_result_name"} & golden.keys() and isinstance(actual.get("products"), list):
        first = actual["products"][0] if actual["products"] else {}
        return {
            "result_count": actual.get("count", len(actual["products"])),
            "first_result_id": first.get("product_id") if isinstance(first, dict) else None,
            "first_result_name": first.get("name") if isinstance(first, dict) else None,
        }
    if "product_name" in golden and "name" in actual:
        return {**actual, "product_name": actual.get("name")}
    return actual

def _demo_email(golden_response: dict[str, Any]) -> str:
    user = golden_response.get("user") if isinstance(golden_response, dict) else {}
    by_name = {
        "Normal Buyer": "normal_buyer@example.com",
        "Product Browser": "browser_user@example.com",
        "Hesitant Buyer": "hesitant_buyer@example.com",
        "Voucher Hunter": "voucher_hunter@example.com",
        "Error Case User": "error_case_user@example.com",
        "ShopLite Admin": "admin@example.com",
    }
    return by_name.get(str(user.get("name") if isinstance(user, dict) else ""), "normal_buyer@example.com")

def _replace_path_uses(endpoint: str, uses: dict[str, str], variables: dict[str, Any]) -> str:
    resolved = endpoint
    for name, location in uses.items():
        if location != "path" or name not in variables:
            continue
        resolved = _replace_last_path_value(resolved, str(variables[name]))
    if ":id" in resolved:
        for name in ("order_id", "orderId", "product_id", "productId", "id"):
            if name in variables:
                resolved = resolved.replace(":id", str(variables[name]))
                break
    return _replace_known_resource_path(resolved, variables)

def _replace_known_resource_path(endpoint: str, variables: dict[str, Any]) -> str:
    replacements = {
        "/api/cart/items/": "cart_item_id",
        "/api/orders/": "order_id",
    }
    for prefix, name in replacements.items():
        if endpoint.startswith(prefix) and endpoint != prefix and variables.get(name):
            return prefix + str(variables[name])
    return endpoint


def _replace_request_body_uses(value: Any, uses: dict[str, str], variables: dict[str, Any]) -> Any:
    replacements = {name: variables[name] for name, location in uses.items() if location == "request.body" and name in variables}
    if not replacements:
        return value
    return _replace_matching_values(value, replacements)


def _replace_matching_values(value: Any, replacements: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {
            key: _replacement_for_key(key, replacements)
            if _replacement_for_key(key, replacements) is not None
            else _replace_matching_values(entry, replacements)
            for key, entry in value.items()
        }
    if isinstance(value, list):
        return [_replace_matching_values(entry, replacements) for entry in value]
    return next(iter(replacements.values())) if value in replacements.values() else value


def _replacement_for_key(key: str, replacements: dict[str, Any]) -> Any:
    if key in replacements:
        return replacements[key]
    normalized_key = key.replace("_", "").lower()
    for replacement_key, replacement_value in replacements.items():
        if replacement_key.replace("_", "").lower() == normalized_key:
            return replacement_value
    return None


def _replace_last_path_value(endpoint: str, value: str) -> str:
    parts = endpoint.rstrip("/").split("/")
    if not parts:
        return endpoint
    parts[-1] = value
    return "/".join(parts)


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


def _response_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}


def _build_url(base_url: str, endpoint: str) -> str:
    return urljoin(f"{base_url}/", endpoint.lstrip("/"))


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")

def _reset_demo_state(client: httpx.Client, base_url: str) -> None:
    parsed = urlparse(base_url)
    is_local_shoplite = parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port == 4000
    headers = None
    if not is_local_shoplite:
        if not settings.demo_control_token:
            return
        headers = {"x-demo-control-token": settings.demo_control_token}

    if not is_local_shoplite and parsed.scheme not in {"http", "https"}:
        return
    try:
        client.post(_build_url(base_url, "/api/demo/reset-state"), headers=headers)
    except Exception:
        return

def _snake_name(value: str) -> str:
    output = []
    for char in value:
        if char.isupper():
            output.extend(["_", char.lower()])
        else:
            output.append(char)
    return "".join(output).lstrip("_")


def _serialize_test_run_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "test_case_id": str(row["test_case_id"]),
        "actual_response": row.get("actual_response") or {},
        "diff_result": row.get("diff_result") or {},
        "runner_metadata": row.get("runner_metadata") or {},
    }
