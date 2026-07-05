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
from app.modules.execution.comparator import compare_steps

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
        for step in steps:
            method = str(step.get("method") or "GET").upper()
            endpoint = str(step.get("endpoint") or "/")
            request_payload = _replace_request_body_uses(step.get("request_payload") or {}, step.get("uses") or {}, variables)
            resolved_endpoint = _replace_path_uses(endpoint, step.get("uses") or {}, variables)
            request_payload, headers = _prepare_request(method, resolved_endpoint, request_payload, auth_token)
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
            result = {
                "order": int(step.get("order") or len(results) + 1),
                "method": method,
                "endpoint": endpoint,
                "resolved_endpoint": resolved_endpoint,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_body": response_body,
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
        if value is not None:
            variables[str(name)] = value
            captured[str(name)] = value
        else:
            missing.append({"name": str(name), "path": str(path)})
    return captured, missing


def _prepare_request(method: str, endpoint: str, payload: Any, auth_token: str | None) -> tuple[Any, dict[str, str]]:
    headers: dict[str, str] = {}
    if not isinstance(payload, dict):
        return payload, headers

    body = dict(payload)
    authorization = body.pop("authorization", None)
    if auth_token and (authorization or not endpoint.endswith("/auth/login")):
        headers["Authorization"] = f"Bearer {auth_token}"
    if method == "POST" and endpoint.endswith("/auth/login") and body.get("password") == "***MASKED***":
        body["password"] = "Password123"
    return body, headers

def _extract_auth_token(response_body: Any) -> str | None:
    if not isinstance(response_body, dict):
        return None
    token = response_body.get("accessToken") or response_body.get("token")
    return str(token) if token else None

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
