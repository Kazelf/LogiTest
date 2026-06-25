from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from urllib.parse import urljoin

import httpx
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.core.settings import settings
from app.db import connection

RUNNER_NAME = "logitest-json-step-runner"
DYNAMIC_RESPONSE_KEYS = {
    "cartId",
    "cart_id",
    "createdAt",
    "created_at",
    "id",
    "orderId",
    "order_id",
    "paymentId",
    "payment_id",
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
                status = "passed" if not diff_result["differences"] else "failed"
            except Exception as exc:
                actual_response = {"steps": []}
                diff_result = {"differences": [], "summary": {"passed": 0, "failed": 0, "errored": 1}}
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
    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=timeout_seconds) as client:
        for step in steps:
            method = str(step.get("method") or "GET").upper()
            endpoint = str(step.get("endpoint") or "/")
            request_payload = _replace_request_body_uses(step.get("request_payload") or {}, step.get("uses") or {}, variables)
            resolved_endpoint = _replace_path_uses(endpoint, step.get("uses") or {}, variables)
            step_start = perf_counter()
            response = client.request(method, _build_url(base_url, resolved_endpoint), json=request_payload if method != "GET" else None)
            duration_ms = int((perf_counter() - step_start) * 1000)
            response_body = _response_body(response)
            result = {
                "order": int(step.get("order") or len(results) + 1),
                "method": method,
                "endpoint": endpoint,
                "resolved_endpoint": resolved_endpoint,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_body": response_body,
            }
            results.append(result)
            _capture_extracts(step.get("extract") or {}, response_body, variables)

    return {"steps": results, "variable_count": len(variables)}


def _compare_results(
    steps: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
    actual_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    differences: list[dict[str, Any]] = []
    actual_by_order = {int(step["order"]): step for step in actual_steps}
    steps_by_order = {int(step.get("order") or index + 1): step for index, step in enumerate(steps)}

    for order, expected_step in steps_by_order.items():
        actual_step = actual_by_order.get(order)
        if actual_step is None:
            differences.append({"order": order, "type": "missing_step", "expected": expected_step.get("endpoint"), "actual": None})
            continue
        expected_status = expected_step.get("expected_status")
        if expected_status is not None and actual_step.get("status_code") != expected_status:
            differences.append(
                {"order": order, "type": "status_code", "expected": expected_status, "actual": actual_step.get("status_code")}
            )

        golden_response = expected_step.get("golden_response")
        if isinstance(golden_response, dict):
            actual_body = actual_step.get("response_body")
            differences.extend(_compare_schema(order, golden_response, actual_body))
            differences.extend(_compare_stable_fields(order, golden_response, actual_body))

    for assertion in assertions:
        if assertion.get("type") != "response_time_ms":
            continue
        order = int(assertion.get("order") or 0)
        max_ms = ((assertion.get("expected") or {}).get("max_ms")) if isinstance(assertion.get("expected"), dict) else None
        actual_step = actual_by_order.get(order)
        if isinstance(max_ms, int) and actual_step and isinstance(actual_step.get("duration_ms"), int) and actual_step["duration_ms"] > max_ms:
            differences.append({"order": order, "type": "response_time_ms", "expected": {"max_ms": max_ms}, "actual": actual_step["duration_ms"]})

    passed = len(actual_steps) - len({diff["order"] for diff in differences})
    return {"differences": differences, "summary": {"passed": max(passed, 0), "failed": len(differences), "errored": 0}}


def _compare_schema(order: int, golden: dict[str, Any], actual: Any) -> list[dict[str, Any]]:
    if not isinstance(actual, dict):
        return [{"order": order, "type": "response_schema", "expected": sorted(golden.keys()), "actual": type(actual).__name__}]
    missing = sorted(key for key in golden.keys() if key not in actual)
    if not missing:
        return []
    return [{"order": order, "type": "response_schema", "expected": sorted(golden.keys()), "actual": {"missing": missing}}]


def _compare_stable_fields(order: int, golden: Any, actual: Any, path: str = "body") -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    if isinstance(golden, dict):
        for key, expected_value in golden.items():
            if key in DYNAMIC_RESPONSE_KEYS:
                continue
            actual_value = actual.get(key) if isinstance(actual, dict) else None
            differences.extend(_compare_stable_fields(order, expected_value, actual_value, f"{path}.{key}"))
    elif isinstance(golden, list):
        if not isinstance(actual, list):
            differences.append({"order": order, "type": "business_field", "expected": {"path": path, "value": golden}, "actual": actual})
        else:
            for index, expected_item in enumerate(golden):
                actual_item = actual[index] if index < len(actual) else None
                differences.extend(_compare_stable_fields(order, expected_item, actual_item, f"{path}[{index}]"))
    elif isinstance(golden, (str, int, float, bool)) or golden is None:
        if actual != golden:
            differences.append({"order": order, "type": "business_field", "expected": {"path": path, "value": golden}, "actual": actual})
    return differences


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


def _capture_extracts(extracts: dict[str, str], response_body: Any, variables: dict[str, Any]) -> None:
    for name, path in extracts.items():
        value = _value_at_path({"response": {"body": response_body}, "body": response_body}, str(path))
        if value is not None:
            variables[str(name)] = value


def _replace_path_uses(endpoint: str, uses: dict[str, str], variables: dict[str, Any]) -> str:
    resolved = endpoint
    for name, location in uses.items():
        if location != "path" or name not in variables:
            continue
        resolved = _replace_last_path_value(resolved, str(variables[name]))
    return resolved


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


def _serialize_test_run_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "test_case_id": str(row["test_case_id"]),
        "actual_response": row.get("actual_response") or {},
        "diff_result": row.get("diff_result") or {},
        "runner_metadata": row.get("runner_metadata") or {},
    }
