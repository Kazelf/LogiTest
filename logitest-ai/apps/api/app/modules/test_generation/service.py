from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db import connection
from app.modules.test_generation import renderers
from app.modules.test_generation.schemas import GeneratedTestCaseFilters, GeneratedTestFramework

GENERATED_BY = "test_generation_service"
TEST_CASE_STATUS_GENERATED = "generated"
TEST_CASE_TYPE_API = "api"
CHAINING_METADATA_KEYS = {"extract", "uses", "type", "journey_type"}
DYNAMIC_RESPONSE_KEYS = {
    "accessToken",
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
    "refreshToken",
    "removedCartItemId",
    "removed_cart_item_id",
    "sessionId",
    "session_id",
    "timestamp",
    "token",
    "traceId",
    "trace_id",
    "updatedAt",
    "updated_at",
    "userId",
    "user_id",
}


class JourneyNotFoundError(Exception):
    pass


class JourneyMissingExampleSessionError(Exception):
    pass


class JourneyHasNoLogsError(Exception):
    pass


class TestCaseNotFoundError(Exception):
    pass


class TestCaseAlreadyExistsError(Exception):
    pass


class TestCaseArtifactNotFoundError(Exception):
    pass


def generate_test_case(
    *,
    journey_id: str,
    overwrite: bool = True,
    frameworks: list[GeneratedTestFramework] | None = None,
    write_files: bool = False,
) -> dict[str, Any]:
    requested_frameworks = _normalize_frameworks(frameworks)
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            journey = _fetch_journey(cur, journey_id)
            if journey is None:
                raise JourneyNotFoundError(journey_id)
            if journey.get("example_session_id") is None:
                raise JourneyMissingExampleSessionError(journey_id)

            logs = _fetch_session_logs(cur, str(journey["example_session_id"]))
            if not logs:
                raise JourneyHasNoLogsError(journey_id)

            draft = _build_test_case_draft(journey, logs)
            artifact_drafts = _build_artifact_drafts(draft, requested_frameworks, write_files=write_files)
            if artifact_drafts:
                draft["generated_code"] = artifact_drafts[0]["code"]
            existing_id = _fetch_test_case_id_by_name(cur, draft["name"])
            if existing_id is not None and not overwrite:
                raise TestCaseAlreadyExistsError(draft["name"])

            test_case_id = _upsert_test_case(cur, draft, overwrite=overwrite)
            artifact_summaries = [_upsert_test_case_artifact(cur, test_case_id, artifact) for artifact in artifact_drafts]
            conn.commit()

    return {
        "test_case_id": test_case_id,
        "journey_id": str(journey["id"]),
        "name": draft["name"],
        "status": TEST_CASE_STATUS_GENERATED,
        "step_count": len(draft["steps"]),
        "artifacts": artifact_summaries,
    }


def list_test_cases(*, limit: int, offset: int, filters: GeneratedTestCaseFilters) -> dict[str, Any]:
    where_sql, where_params = _build_test_case_filters(filters)
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM test_cases
        LEFT JOIN journeys ON journeys.id = test_cases.journey_id
        LEFT JOIN personas ON personas.id = test_cases.persona_id
        {where_sql}
    """
    list_sql = f"""
        SELECT
            test_cases.id,
            test_cases.journey_id,
            test_cases.persona_id,
            journeys.name AS journey_name,
            personas.name AS persona_name,
            test_cases.name,
            test_cases.description,
            test_cases.type::text AS type,
            test_cases.status::text AS status,
            jsonb_array_length(test_cases.steps) AS step_count,
            test_cases.generated_by,
            test_cases.created_at,
            test_cases.updated_at
        FROM test_cases
        LEFT JOIN journeys ON journeys.id = test_cases.journey_id
        LEFT JOIN personas ON personas.id = test_cases.persona_id
        {where_sql}
        ORDER BY test_cases.updated_at DESC, test_cases.created_at DESC
        LIMIT %s OFFSET %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(count_sql, where_params)
            total = int(cur.fetchone()["total"])
            cur.execute(list_sql, [*where_params, limit, offset])
            rows = cur.fetchall()

    return {
        "items": [_serialize_test_case_list_row(row) for row in rows],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def get_test_case_detail(test_case_id: str) -> dict[str, Any]:
    sql = """
        SELECT
            test_cases.id,
            test_cases.journey_id,
            test_cases.persona_id,
            journeys.name AS journey_name,
            personas.name AS persona_name,
            test_cases.name,
            test_cases.description,
            test_cases.type::text AS type,
            test_cases.status::text AS status,
            test_cases.steps,
            test_cases.assertions,
            test_cases.golden_response,
            test_cases.generated_code,
            test_cases.generated_by,
            test_cases.created_at,
            test_cases.updated_at
        FROM test_cases
        LEFT JOIN journeys ON journeys.id = test_cases.journey_id
        LEFT JOIN personas ON personas.id = test_cases.persona_id
        WHERE test_cases.id = %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, [test_case_id])
            row = cur.fetchone()
            if row is None:
                raise TestCaseNotFoundError(test_case_id)
            row["artifacts"] = _fetch_test_case_artifacts(cur, test_case_id)

    return _serialize_test_case_detail_row(row)


def list_test_case_artifacts(test_case_id: str) -> dict[str, Any]:
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if not _test_case_exists(cur, test_case_id):
                raise TestCaseNotFoundError(test_case_id)
            artifacts = _fetch_test_case_artifacts(cur, test_case_id)

    return {"items": artifacts, "total": len(artifacts)}


def get_test_case_artifact(test_case_id: str, framework: GeneratedTestFramework) -> dict[str, Any]:
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if not _test_case_exists(cur, test_case_id):
                raise TestCaseNotFoundError(test_case_id)
            artifact = _fetch_test_case_artifact(cur, test_case_id, framework)
            if artifact is None:
                raise TestCaseArtifactNotFoundError(f"{test_case_id}:{framework}")

    return artifact


def _fetch_journey(cur: Any, journey_id: str) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT
            journeys.id,
            journeys.persona_id,
            personas.name AS persona_name,
            journeys.name,
            journeys.description,
            journeys.example_session_id,
            journeys.steps
        FROM journeys
        LEFT JOIN personas ON personas.id = journeys.persona_id
        WHERE journeys.id = %s
        """,
        [journey_id],
    )
    return cur.fetchone()


def _fetch_session_logs(cur: Any, session_id: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT
            logs.service_name,
            logs.method,
            logs.endpoint,
            logs.status_code,
            logs.request_payload,
            logs.response_body,
            logs.raw_log,
            logs.response_time_ms,
            logs.action_type,
            logs.occurred_at
        FROM logs
        WHERE logs.session_id = %s
        ORDER BY logs.occurred_at ASC
        """,
        [session_id],
    )
    return list(cur.fetchall())


def _fetch_test_case_id_by_name(cur: Any, name: str) -> str | None:
    cur.execute("SELECT id FROM test_cases WHERE name = %s", [name])
    row = cur.fetchone()
    return str(row["id"]) if row else None


def _build_test_case_draft(journey: dict[str, Any], logs: list[dict[str, Any]]) -> dict[str, Any]:
    steps = _build_steps(logs, journey_steps=list(journey.get("steps") or []))
    assertions = _build_assertions(steps)
    name = _build_test_case_name(str(journey["name"]))
    description = f"Generated API test case from journey '{journey['name']}'."
    golden_response = _build_golden_response(journey, steps)

    return {
        "journey_id": str(journey["id"]),
        "persona_id": str(journey["persona_id"]) if journey.get("persona_id") else None,
        "name": name,
        "description": description,
        "steps": steps,
        "assertions": assertions,
        "golden_response": golden_response,
        "generated_code": build_generated_code_stub(name, steps),
    }


def _normalize_frameworks(frameworks: list[GeneratedTestFramework] | None) -> list[GeneratedTestFramework]:
    requested = frameworks or [GeneratedTestFramework.JEST_SUPERTEST]
    normalized: list[GeneratedTestFramework] = []
    for framework in requested:
        if framework not in normalized:
            normalized.append(framework)
    return normalized


def _build_artifact_drafts(
    draft: dict[str, Any],
    frameworks: list[GeneratedTestFramework],
    *,
    write_files: bool,
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for framework in frameworks:
        code = renderers.render_script(framework=framework, test_case=draft)
        file_path = renderers.write_generated_file(framework=framework, test_case_name=draft["name"], code=code) if write_files else None
        artifacts.append(
            {
                "framework": framework,
                "language": "typescript",
                "file_path": file_path,
                "code": code,
            }
        )
    return artifacts


def _build_steps(logs: list[dict[str, Any]], journey_steps: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    replay_logs = _replay_logs_for_journey(logs, journey_steps or [])
    metadata_by_order = {
        int(step.get("order")): {key: step[key] for key in CHAINING_METADATA_KEYS if key in step}
        for step in journey_steps or []
        if step.get("order") is not None
    }
    steps: list[dict[str, Any]] = []
    for row in replay_logs:
        if row.get("status_code") == 304:
            continue
        order = len(steps) + 1
        step = {
            "order": order,
            "action_type": row.get("action_type") or "unknown",
            "service_name": row.get("service_name"),
            "method": row.get("method"),
            "endpoint": _concrete_endpoint(row),
            "request_payload": _demo_request_payload(row),
            "expected_status": row.get("status_code"),
            "golden_response": row.get("response_body") or {},
            "response_time_ms": row.get("response_time_ms"),
        }
        step.update(metadata_by_order.get(order, {}))
        steps.append(step)
    return _make_steps_self_contained(steps)

def _make_steps_self_contained(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps = [dict(step) for step in steps]
    checkout_index = _first_checkout_preview_index(steps)
    if checkout_index is not None and not _has_successful_add_to_cart_before(steps, checkout_index):
        steps.insert(checkout_index, _synthetic_add_to_cart_step(steps[checkout_index]))
        checkout_index += 1

    payment_index = _first_payment_index(steps)
    if payment_index is not None and checkout_index is not None and not _has_order_creation_before(steps, payment_index):
        checkout = steps[checkout_index] if checkout_index is not None else {}
        steps.insert(payment_index, _synthetic_create_order_step(checkout))

    _wire_order_id_uses(steps)
    return _renumber_steps(steps)

def _first_checkout_preview_index(steps: list[dict[str, Any]]) -> int | None:
    for index, step in enumerate(steps):
        if step.get("endpoint") == "/api/checkout" and _is_success_status(step.get("expected_status")):
            return index
    return None

def _first_payment_index(steps: list[dict[str, Any]]) -> int | None:
    for index, step in enumerate(steps):
        if str(step.get("endpoint") or "").startswith("/api/payments/"):
            return index
    return None

def _has_successful_add_to_cart_before(steps: list[dict[str, Any]], end: int) -> bool:
    return any(
        step.get("action_type") == "add_to_cart" and _is_success_status(step.get("expected_status"))
        for step in steps[:end]
    )

def _has_order_creation_before(steps: list[dict[str, Any]], end: int) -> bool:
    return any(
        step.get("method") == "POST" and step.get("endpoint") == "/api/orders" and _is_success_status(step.get("expected_status"))
        for step in steps[:end]
    )

def _synthetic_add_to_cart_step(checkout_step: dict[str, Any]) -> dict[str, Any]:
    cart = checkout_step.get("golden_response", {}).get("cart", {}) if isinstance(checkout_step.get("golden_response"), dict) else {}
    item = (cart.get("items") or [{}])[0] if isinstance(cart, dict) else {}
    product_id = item.get("product_id")
    quantity = item.get("quantity") or 1
    golden_response = {
        "product_id": product_id,
        "cart": cart,
    }
    if item.get("cart_item_id"):
        golden_response["cart_item_id"] = item["cart_item_id"]

    return {
        "action_type": "add_to_cart",
        "service_name": checkout_step.get("service_name"),
        "method": "POST",
        "endpoint": "/api/cart/items",
        "request_payload": {"product_id": product_id, "quantity": quantity},
        "expected_status": 201,
        "golden_response": golden_response,
        "response_time_ms": checkout_step.get("response_time_ms"),
    }

def _synthetic_create_order_step(checkout_step: dict[str, Any]) -> dict[str, Any]:
    checkout_body = checkout_step.get("golden_response") if isinstance(checkout_step.get("golden_response"), dict) else {}
    cart = checkout_body.get("cart", {}) if isinstance(checkout_body.get("cart"), dict) else {}
    items = [
        {
            "order_item_id": item.get("cart_item_id"),
            "product_id": item.get("product_id"),
            "name": item.get("name"),
            "quantity": item.get("quantity"),
            "unit_price": item.get("price"),
            "line_total": item.get("line_total"),
        }
        for item in cart.get("items", [])
        if isinstance(item, dict)
    ]

    return {
        "action_type": "checkout",
        "service_name": checkout_step.get("service_name"),
        "method": "POST",
        "endpoint": "/api/orders",
        "request_payload": {"shipping_address": checkout_body.get("shipping_address")},
        "expected_status": 201,
        "golden_response": {
            "order_id": "generated_order_id",
            "order_status": "PENDING_PAYMENT",
            "payment_status": "PENDING",
            "subtotal_amount": checkout_body.get("subtotal_amount"),
            "discount_amount": checkout_body.get("discount_amount"),
            "total_amount": checkout_body.get("total_amount"),
            "voucher_code": cart.get("voucher_code"),
            "shipping_address": checkout_body.get("shipping_address"),
            "items": items,
        },
        "response_time_ms": checkout_step.get("response_time_ms"),
        "extract": {"order_id": "response.body.order_id"},
    }

def _wire_order_id_uses(steps: list[dict[str, Any]]) -> None:
    has_order_id = any("order_id" in (step.get("extract") or {}) for step in steps)
    if not has_order_id:
        return
    for step in steps:
        endpoint = str(step.get("endpoint") or "")
        if endpoint.startswith("/api/payments/") and "order_id" in (step.get("request_payload") or {}):
            step.setdefault("uses", {})["order_id"] = "request.body"
        if endpoint.startswith("/api/orders/"):
            step["endpoint"] = "/api/orders/:id"
            step.setdefault("uses", {})["order_id"] = "path"

def _renumber_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**step, "order": index + 1} for index, step in enumerate(steps)]

def _is_success_status(status: Any) -> bool:
    try:
        value = int(status)
    except (TypeError, ValueError):
        return False
    return 200 <= value < 300

def _replay_logs_for_journey(logs: list[dict[str, Any]], journey_steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = [str(step.get("action_type")) for step in journey_steps if step.get("action_type")]
    if not wanted:
        return logs

    selected: list[dict[str, Any]] = []
    search_from = 0
    for action_type in wanted:
        for index in range(search_from, len(logs)):
            row = logs[index]
            if row.get("status_code") == 304:
                continue
            if str(row.get("action_type") or "unknown") != action_type:
                continue
            selected.append(row)
            search_from = index + 1
            break
    return selected or logs

def _concrete_endpoint(row: dict[str, Any]) -> str | None:
    endpoint = row.get("endpoint")
    raw_log = row.get("raw_log") if isinstance(row.get("raw_log"), dict) else {}
    path_params = raw_log.get("path_params") if isinstance(raw_log.get("path_params"), dict) else {}
    if isinstance(endpoint, str) and ":id" in endpoint and path_params.get("id"):
        endpoint = endpoint.replace(":id", str(path_params["id"]))
    query = raw_log.get("query") if isinstance(raw_log.get("query"), dict) else {}
    if isinstance(endpoint, str) and query and "?" not in endpoint:
        return f"{endpoint}?{urlencode(query, doseq=True)}"
    return endpoint

def _demo_request_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row.get("request_payload") or {})
    if str(row.get("method") or "").upper() == "POST" and str(row.get("endpoint") or "").endswith("/auth/login"):
        if payload.get("email") == "***MASKED***":
            payload["email"] = _demo_email(row.get("response_body") or {})
        if payload.get("password") == "***MASKED***":
            payload["password"] = "Password123"
        payload.pop("authorization", None)
    return payload

def _demo_email(response_body: dict[str, Any]) -> str:
    user = response_body.get("user") if isinstance(response_body, dict) else {}
    by_name = {
        "Normal Buyer": "normal_buyer@example.com",
        "Product Browser": "browser_user@example.com",
        "Hesitant Buyer": "hesitant_buyer@example.com",
        "Voucher Hunter": "voucher_hunter@example.com",
        "Error Case User": "error_case_user@example.com",
        "ShopLite Admin": "admin@example.com",
    }
    return by_name.get(str(user.get("name") if isinstance(user, dict) else ""), "normal_buyer@example.com")


def _build_assertions(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    for step in steps:
        assertions.append(
            {
                "order": step["order"],
                "type": "status_code",
                "expected": step.get("expected_status"),
            }
        )

        golden_response = step.get("golden_response")
        if isinstance(golden_response, dict):
            assertions.append(
                {
                    "order": step["order"],
                    "type": "response_schema",
                    "expected": {
                        "type": "object",
                        "required": sorted(golden_response.keys()),
                    },
                }
            )

            for path, value in _iter_stable_business_fields(golden_response):
                assertions.append(
                    {
                        "order": step["order"],
                        "type": "business_field",
                        "expected": {"path": path, "value": value},
                    }
                )

        response_time_ms = step.get("response_time_ms")
        if isinstance(response_time_ms, int) and response_time_ms > 0:
            assertions.append(
                {
                    "order": step["order"],
                    "type": "response_time_ms",
                    "expected": {"max_ms": max(1000, response_time_ms * 3)},
                }
            )
    return assertions

def _iter_stable_business_fields(value: Any, path: str = "body") -> list[tuple[str, Any]]:
    fields: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, entry_value in value.items():
            if key in DYNAMIC_RESPONSE_KEYS:
                continue
            entry_path = f"{path}.{key}"
            if isinstance(entry_value, (dict, list)):
                fields.extend(_iter_stable_business_fields(entry_value, entry_path))
            elif entry_value == "***MASKED***":
                continue
            elif isinstance(entry_value, (str, int, float, bool)) or entry_value is None:
                fields.append((entry_path, entry_value))
    return fields


def _build_golden_response(journey: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    final_step = steps[-1] if steps else {}
    return {
        "step_count": len(steps),
        "final_status_code": final_step.get("expected_status"),
        "final_response_body": final_step.get("golden_response") or {},
        "source": {
            "journey_id": str(journey["id"]),
            "example_session_id": str(journey["example_session_id"]),
        },
    }


def _build_test_case_name(journey_name: str) -> str:
    normalized = journey_name.removeprefix("Journey: ").strip()
    return f"API test - {normalized}"


def build_generated_code_stub(name: str, steps: list[dict[str, Any]]) -> str:
    slug = _slugify(name)
    lines = [f"def test_{slug}(api_client):", f"    # Generated API test case with {len(steps)} step(s)."]
    for step in steps:
        lines.append(
            f"    # {step['order']}. {step.get('method') or 'GET'} {step.get('endpoint') or '/'} -> {step.get('expected_status')}"
        )
    lines.append("    assert True")
    return "\n".join(lines)


def _slugify(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "_" for char in value]
    slug = "".join(chars).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "generated_api_test"


def _upsert_test_case(cur: Any, draft: dict[str, Any], *, overwrite: bool) -> str:
    if overwrite:
        sql = """
            INSERT INTO test_cases (
                journey_id,
                persona_id,
                name,
                description,
                type,
                status,
                steps,
                assertions,
                golden_response,
                generated_code,
                generated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                journey_id = EXCLUDED.journey_id,
                persona_id = EXCLUDED.persona_id,
                description = EXCLUDED.description,
                type = EXCLUDED.type,
                status = EXCLUDED.status,
                steps = EXCLUDED.steps,
                assertions = EXCLUDED.assertions,
                golden_response = EXCLUDED.golden_response,
                generated_code = EXCLUDED.generated_code,
                generated_by = EXCLUDED.generated_by,
                updated_at = now()
            RETURNING id
        """
    else:
        sql = """
            INSERT INTO test_cases (
                journey_id,
                persona_id,
                name,
                description,
                type,
                status,
                steps,
                assertions,
                golden_response,
                generated_code,
                generated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

    cur.execute(
        sql,
        (
            draft["journey_id"],
            draft["persona_id"],
            draft["name"],
            draft["description"],
            TEST_CASE_TYPE_API,
            TEST_CASE_STATUS_GENERATED,
            Jsonb(draft["steps"]),
            Jsonb(draft["assertions"]),
            Jsonb(draft["golden_response"]),
            draft["generated_code"],
            GENERATED_BY,
        ),
    )
    return str(cur.fetchone()["id"])


def _upsert_test_case_artifact(cur: Any, test_case_id: str, artifact: dict[str, Any]) -> dict[str, Any]:
    cur.execute(
        """
        INSERT INTO test_case_artifacts (
            test_case_id,
            framework,
            language,
            file_path,
            code
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (test_case_id, framework) DO UPDATE SET
            language = EXCLUDED.language,
            file_path = EXCLUDED.file_path,
            code = EXCLUDED.code,
            updated_at = now()
        RETURNING id, framework, language, file_path
        """,
        (
            test_case_id,
            str(artifact["framework"]),
            artifact["language"],
            artifact["file_path"],
            artifact["code"],
        ),
    )
    return _serialize_artifact_summary_row(cur.fetchone())


def _test_case_exists(cur: Any, test_case_id: str) -> bool:
    cur.execute("SELECT 1 FROM test_cases WHERE id = %s", [test_case_id])
    return cur.fetchone() is not None


def _fetch_test_case_artifacts(cur: Any, test_case_id: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id, framework, language, file_path, code, created_at, updated_at
        FROM test_case_artifacts
        WHERE test_case_id = %s
        ORDER BY framework ASC
        """,
        [test_case_id],
    )
    return [_serialize_artifact_detail_row(row) for row in cur.fetchall()]


def _fetch_test_case_artifact(cur: Any, test_case_id: str, framework: GeneratedTestFramework) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT id, framework, language, file_path, code, created_at, updated_at
        FROM test_case_artifacts
        WHERE test_case_id = %s AND framework = %s
        """,
        [test_case_id, str(framework)],
    )
    row = cur.fetchone()
    return _serialize_artifact_detail_row(row) if row else None


def _build_test_case_filters(filters: GeneratedTestCaseFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if filters.journey_id:
        clauses.append("test_cases.journey_id = %s")
        params.append(filters.journey_id)
    if filters.status:
        clauses.append("test_cases.status = %s")
        params.append(filters.status)
    return ("WHERE " + " AND ".join(clauses), params) if clauses else ("", params)


def _serialize_test_case_list_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "journey_id": str(row["journey_id"]) if row.get("journey_id") else None,
        "persona_id": str(row["persona_id"]) if row.get("persona_id") else None,
        "step_count": int(row.get("step_count") or 0),
    }


def _serialize_test_case_detail_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "journey_id": str(row["journey_id"]) if row.get("journey_id") else None,
        "persona_id": str(row["persona_id"]) if row.get("persona_id") else None,
        "steps": list(row.get("steps") or []),
        "assertions": list(row.get("assertions") or []),
        "golden_response": row.get("golden_response") or {},
        "artifacts": list(row.get("artifacts") or []),
    }


def _serialize_artifact_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "framework": row["framework"],
        "language": row["language"],
        "file_path": row.get("file_path"),
    }


def _serialize_artifact_detail_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_serialize_artifact_summary_row(row),
        "code": row["code"],
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }
