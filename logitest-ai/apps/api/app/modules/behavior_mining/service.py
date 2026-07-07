from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from functools import lru_cache
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db import connection
from app.modules.behavior_mining.schemas import JourneyFilters, PersonaFilters
from app.modules.ai import gemini_client
from app.modules.session_reconstruction import (
    ACTION_ADD_TO_CART,
    ACTION_LOGIN,
    ACTION_CHECKOUT,
    ACTION_PAYMENT_FAILED,
    ACTION_PAYMENT_SUCCESS,
    ACTION_SEARCH_PRODUCT,
    ACTION_UNKNOWN,
    ACTION_VIEW_ORDER,
    ACTION_VIEW_PRODUCT,
    classify_action,
)

ANALYSIS_METHOD = "rule_based"
ANALYSIS_SOURCE = "logs"
JOURNEY_ASYNC_PAYMENT_FLOW = "ASYNC_PAYMENT_FLOW"
JOURNEY_LOGIN_FLOW = "LOGIN_FLOW"
JOURNEY_ORDER_CREATION_FLOW = "ORDER_CREATION_FLOW"
JOURNEY_SEARCH_FLOW = "SEARCH_FLOW"
JOURNEY_UNKNOWN_FLOW = "UNKNOWN_FLOW"
CHAINING_FIELD_NAMES = {
    "cartId",
    "cart_id",
    "cartItemId",
    "cart_item_id",
    "orderId",
    "order_id",
    "paymentId",
    "payment_id",
    "productId",
    "product_id",
    "userId",
    "user_id",
}


@dataclass(frozen=True)
class PersonaSpec:
    name: str
    description: str
    confidence_score: float
    features: dict[str, Any]


@dataclass(frozen=True)
class JourneyDraft:
    name: str
    description: str
    persona_name: str
    journey_type: str
    source_session_count: int
    frequency_score: float
    risk_score: float
    steps: list[dict[str, Any]]
    example_session_id: str | None


def analyze_behavior() -> dict[str, Any]:
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(_FETCH_LOG_ROWS_SQL)
            rows = cur.fetchall()

            session_groups = _group_rows_by_session(rows)
            journey_drafts = _build_journey_drafts(session_groups)
            persona_specs = {_detect_persona(_action_set(draft.steps)).name: _detect_persona(_action_set(draft.steps)) for draft in journey_drafts}

            persona_ids = _upsert_personas(cur, persona_specs.values())
            _clear_journeys(cur)
            journeys_upserted = _upsert_journeys(cur, journey_drafts, persona_ids)
            conn.commit()

    return {
        "sessions_analyzed": len(session_groups),
        "personas_upserted": len(persona_specs),
        "journeys_upserted": journeys_upserted,
        "source": ANALYSIS_SOURCE,
        "method": ANALYSIS_METHOD,
    }


def list_personas(*, limit: int, offset: int, filters: PersonaFilters) -> dict[str, Any]:
    where_sql, where_params = _build_persona_filters(filters)
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM personas
        {where_sql}
    """
    list_sql = f"""
        SELECT
            id,
            name,
            description,
            detection_method,
            confidence_score,
            features,
            created_at,
            updated_at
        FROM personas
        {where_sql}
        ORDER BY name ASC, created_at DESC
        LIMIT %s OFFSET %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(count_sql, where_params)
            total = int(cur.fetchone()["total"])
            cur.execute(list_sql, [*where_params, limit, offset])
            rows = cur.fetchall()

    return {
        "items": [_serialize_persona_row(row) for row in rows],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def list_journeys(*, limit: int, offset: int, filters: JourneyFilters) -> dict[str, Any]:
    where_sql, where_params = _build_journey_filters(filters)
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM journeys
        LEFT JOIN personas ON personas.id = journeys.persona_id
        {where_sql}
    """
    list_sql = f"""
        SELECT
            journeys.id,
            journeys.persona_id,
            personas.name AS persona_name,
            journeys.name,
            journeys.description,
            journeys.source_session_count,
            journeys.frequency_score,
            journeys.risk_score,
            journeys.steps,
            journeys.example_session_id,
            journeys.created_at,
            journeys.updated_at
        FROM journeys
        LEFT JOIN personas ON personas.id = journeys.persona_id
        {where_sql}
        ORDER BY journeys.updated_at DESC, journeys.created_at DESC
        LIMIT %s OFFSET %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(count_sql, where_params)
            total = int(cur.fetchone()["total"])
            cur.execute(list_sql, [*where_params, limit, offset])
            rows = cur.fetchall()

    return {
        "items": [_serialize_journey_row(row) for row in rows],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def _group_rows_by_session(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sessions: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        session_key = str(row.get("session_id") or row.get("external_session_id") or "unknown")
        sessions.setdefault(session_key, []).append(row)
    return sessions


def _build_journey_drafts(session_groups: dict[str, list[dict[str, Any]]]) -> list[JourneyDraft]:
    total_sessions = len(session_groups)
    if total_sessions == 0:
        return []

    grouped_by_signature: dict[str, list[dict[str, Any]]] = {}
    for records in session_groups.values():
        steps = _build_steps(records)
        if not steps:
            continue
        signature = _build_journey_signature(steps)
        grouped_by_signature.setdefault(signature, []).append(
            {
                "steps": steps,
                "session_id": records[0].get("session_id"),
            }
        )

    drafts: list[JourneyDraft] = []
    for signature, examples in grouped_by_signature.items():
        steps = examples[0]["steps"]
        action_types = _action_set(steps)
        persona = _detect_persona(action_types)
        journey_type = _detect_journey_type(action_types)
        source_session_count = len(examples)
        drafts.append(
            JourneyDraft(
                name=_build_journey_name(journey_type, signature),
                description=f"{journey_type} mined from {source_session_count} session(s).",
                persona_name=persona.name,
                journey_type=journey_type,
                source_session_count=source_session_count,
                frequency_score=round(source_session_count / total_sessions, 4),
                risk_score=_calculate_risk_score(action_types),
                steps=_apply_journey_type(steps, journey_type),
                example_session_id=str(examples[0]["session_id"]) if examples[0].get("session_id") else None,
            )
        )

    return drafts


def _build_steps(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps = []
    previous_action_type = None
    seen_action_types = set()
    for record in records:
        action_type = _resolve_action_type(record)
        if action_type == ACTION_UNKNOWN or action_type == previous_action_type or action_type in seen_action_types:
            continue

        steps.append(
            {
                "order": len(steps) + 1,
                "action_type": action_type,
                "method": record.get("method"),
                "endpoint": record.get("endpoint"),
                "expected_status": record.get("status_code"),
                "response_time_ms": record.get("response_time_ms"),
                "request_payload": record.get("request_payload") or {},
                "response_body": record.get("response_body") or {},
            }
        )
        previous_action_type = action_type
        seen_action_types.add(action_type)

    annotated_steps = _annotate_chaining(steps)
    for step in annotated_steps:
        step["important_payload_fields"] = _payload_fields(step)
        step["important_response_fields"] = _response_fields(step)
        step.pop("request_payload", None)
        step.pop("response_body", None)
    return annotated_steps

def _detect_journey_type(action_types: set[str]) -> str:
    if {ACTION_PAYMENT_FAILED, ACTION_PAYMENT_SUCCESS} & action_types:
        return JOURNEY_ASYNC_PAYMENT_FLOW
    if {ACTION_ADD_TO_CART, ACTION_CHECKOUT, ACTION_VIEW_ORDER} & action_types:
        return JOURNEY_ORDER_CREATION_FLOW
    if {ACTION_SEARCH_PRODUCT, ACTION_VIEW_PRODUCT} & action_types:
        return JOURNEY_SEARCH_FLOW
    if ACTION_LOGIN in action_types:
        return JOURNEY_LOGIN_FLOW
    return JOURNEY_UNKNOWN_FLOW

def _apply_journey_type(steps: list[dict[str, Any]], journey_type: str) -> list[dict[str, Any]]:
    return [{**step, "type": journey_type, "journey_type": journey_type} for step in steps]

def _annotate_chaining(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    extracted: list[dict[str, Any]] = []

    for step_index, step in enumerate(steps):
        for field_name, field_value, path in _iter_stable_response_fields(step.get("response_body") or {}):
            if field_value in (None, "", [], {}):
                continue
            token = {
                "step_index": step_index,
                "field_name": field_name,
                "field_value": field_value,
                "path": path,
            }
            extracted.append(token)
            step.setdefault("extract", {})[field_name] = path

    for token in extracted:
        for later_step in steps[token["step_index"] + 1 :]:
            use_location = _find_value_use(later_step, token["field_value"])
            if use_location is None:
                continue
            later_step.setdefault("uses", {})[token["field_name"]] = use_location

    return steps

def _resolve_action_type(record: dict[str, Any]) -> str:
    action_type = str(record.get("action_type") or ACTION_UNKNOWN)
    if action_type != ACTION_UNKNOWN:
        return action_type
    return classify_action(record).action_type

def _iter_stable_response_fields(value: Any, path: str = "response.body") -> list[tuple[str, Any, str]]:
    fields: list[tuple[str, Any, str]] = []
    if isinstance(value, dict):
        for key, entry_value in value.items():
            entry_path = f"{path}.{key}"
            if key in CHAINING_FIELD_NAMES:
                fields.append((_field_name_for_path(key, entry_path), entry_value, entry_path))
            fields.extend(_iter_stable_response_fields(entry_value, entry_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            fields.extend(_iter_stable_response_fields(item, f"{path}[{index}]"))
    return fields

def _find_value_use(step: dict[str, Any], value: Any) -> str | None:
    value_text = str(value)
    endpoint = str(step.get("endpoint") or "")
    if value_text and value_text in endpoint:
        return "path"
    if _contains_value(step.get("request_payload") or {}, value):
        return "request.body"
    return None

def _contains_value(candidate: Any, expected: Any) -> bool:
    if isinstance(candidate, dict):
        return any(_contains_value(value, expected) for value in candidate.values())
    if isinstance(candidate, list):
        return any(_contains_value(value, expected) for value in candidate)
    return candidate == expected or str(candidate) == str(expected)

def _field_name_for_path(key: str, path: str) -> str:
    if "[" not in path:
        return key
    suffix = path.rsplit("[", 1)[-1].split("]", 1)[0]
    return f"{key}_{suffix}" if suffix.isdigit() else key


def _detect_persona(action_types: set[str]) -> PersonaSpec:
    if ACTION_PAYMENT_FAILED in action_types:
        return PersonaSpec(
            name="Failed Payment User",
            description="User reaches checkout but receives a failed payment response.",
            confidence_score=0.93,
            features={"signals": [ACTION_CHECKOUT, ACTION_PAYMENT_FAILED]},
        )
    if ACTION_PAYMENT_SUCCESS in action_types:
        return PersonaSpec(
            name="Buyer",
            description="User completes checkout and successful payment.",
            confidence_score=0.95,
            features={"signals": [ACTION_CHECKOUT, ACTION_PAYMENT_SUCCESS]},
        )
    has_product_discovery = bool({ACTION_SEARCH_PRODUCT, ACTION_VIEW_PRODUCT} & action_types)
    has_checkout_or_payment = bool({ACTION_CHECKOUT, ACTION_PAYMENT_FAILED, ACTION_PAYMENT_SUCCESS} & action_types)
    if has_product_discovery and not has_checkout_or_payment:
        return PersonaSpec(
            name="Browser",
            description="User discovers or views products without completing checkout.",
            confidence_score=0.90,
            features={"signals": sorted({ACTION_SEARCH_PRODUCT, ACTION_VIEW_PRODUCT} & action_types), "excludes": [ACTION_CHECKOUT]},
        )
    return PersonaSpec(
        name="Unknown User",
        description="User behavior does not match an MVP persona rule.",
        confidence_score=0.50,
        features={"signals": sorted(action_types) if action_types else [ACTION_UNKNOWN]},
    )


def _action_set(steps: list[dict[str, Any]]) -> set[str]:
    return {str(step.get("action_type") or ACTION_UNKNOWN) for step in steps}


def _build_journey_signature(steps: list[dict[str, Any]]) -> str:
    return " > ".join(str(step.get("action_type") or ACTION_UNKNOWN) for step in steps)


def _build_journey_name(journey_type: str, signature: str) -> str:
    return f"Journey: {journey_type} - {signature}"


def _calculate_risk_score(action_types: set[str]) -> float:
    if ACTION_PAYMENT_FAILED in action_types:
        return 0.90
    if ACTION_CHECKOUT in action_types or ACTION_PAYMENT_SUCCESS in action_types:
        return 0.62
    return 0.25


def _upsert_personas(cur: Any, persona_specs: Any) -> dict[str, str]:
    persona_ids: dict[str, str] = {}
    for persona in persona_specs:
        cur.execute(
            """
            INSERT INTO personas (name, description, detection_method, confidence_score, features)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                description = EXCLUDED.description,
                detection_method = EXCLUDED.detection_method,
                confidence_score = EXCLUDED.confidence_score,
                features = EXCLUDED.features,
                updated_at = now()
            RETURNING id
            """,
            (persona.name, persona.description, ANALYSIS_METHOD, persona.confidence_score, Jsonb(persona.features)),
        )
        persona_ids[persona.name] = str(cur.fetchone()["id"])
    return persona_ids


def _upsert_journeys(cur: Any, journey_drafts: list[JourneyDraft], persona_ids: dict[str, str]) -> int:
    for draft in journey_drafts:
        cur.execute(
            """
            INSERT INTO journeys (
                persona_id,
                name,
                description,
                source_session_count,
                frequency_score,
                risk_score,
                steps,
                example_session_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                persona_id = EXCLUDED.persona_id,
                description = EXCLUDED.description,
                source_session_count = EXCLUDED.source_session_count,
                frequency_score = EXCLUDED.frequency_score,
                risk_score = EXCLUDED.risk_score,
                steps = EXCLUDED.steps,
                example_session_id = EXCLUDED.example_session_id,
                updated_at = now()
            RETURNING id
            """,
            (
                persona_ids[draft.persona_name],
                draft.name,
                draft.description,
                draft.source_session_count,
                draft.frequency_score,
                draft.risk_score,
                Jsonb(draft.steps),
                draft.example_session_id,
            ),
        )
        cur.fetchone()
    return len(journey_drafts)

def _clear_journeys(cur: Any) -> None:
    cur.execute("DELETE FROM journeys", ())


def _build_persona_filters(filters: PersonaFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if filters.name:
        clauses.append("personas.name ILIKE %s")
        params.append(f"%{filters.name}%")
    return ("WHERE " + " AND ".join(clauses), params) if clauses else ("", params)


def _build_journey_filters(filters: JourneyFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if filters.persona_id:
        clauses.append("journeys.persona_id = %s")
        params.append(filters.persona_id)
    if filters.name:
        clauses.append("journeys.name ILIKE %s")
        params.append(f"%{filters.name}%")
    return ("WHERE " + " AND ".join(clauses), params) if clauses else ("", params)


def _serialize_persona_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "confidence_score": _to_float(row.get("confidence_score")),
        "features": row.get("features") or {},
    }


def _serialize_journey_row(row: dict[str, Any]) -> dict[str, Any]:
    steps = list(row.get("steps") or [])
    return {
        **row,
        "id": str(row["id"]),
        "persona_id": str(row["persona_id"]) if row.get("persona_id") else None,
        "example_session_id": str(row["example_session_id"]) if row.get("example_session_id") else None,
        "frequency_score": _to_float(row.get("frequency_score")),
        "risk_score": _to_float(row.get("risk_score")),
        "steps": steps,
        "behavior_analysis": _build_behavior_analysis(str(row.get("name") or "Journey"), steps),
    }

def _build_behavior_analysis(name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    safe_steps = _safe_analysis_steps(steps)
    if gemini_client.gemini_available():
        generated = _cached_gemini_behavior(name, json.dumps(safe_steps, sort_keys=True))
        if generated:
            return {**generated, **gemini_client.metadata(fallback_used=False)}
    fallback = _build_rule_based_behavior_analysis(name, steps)
    return {**fallback, **gemini_client.metadata(fallback_used=True)}

@lru_cache(maxsize=128)
def _cached_gemini_behavior(name: str, steps_json: str) -> dict[str, Any] | None:
    return gemini_client.generate_behavior_explanation(name, json.loads(steps_json))

def _safe_analysis_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "order": step.get("order"),
            "action_type": step.get("action_type"),
            "method": step.get("method"),
            "endpoint": step.get("endpoint"),
            "expected_status": step.get("expected_status"),
            "important_payload_fields": step.get("important_payload_fields") or _payload_fields(step),
            "important_response_fields": step.get("important_response_fields") or _response_fields(step),
            "extract": step.get("extract") or {},
            "uses": step.get("uses") or {},
        }
        for step in steps
    ]

def _build_rule_based_behavior_analysis(name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    action_types = _action_set(steps)
    behavior_type = "error" if ACTION_PAYMENT_FAILED in action_types else "normal"
    if any(int(step.get("expected_status") or 0) >= 400 for step in steps):
        behavior_type = "abnormal"
    checkout_like = bool({ACTION_CHECKOUT, ACTION_VIEW_ORDER, ACTION_PAYMENT_SUCCESS} & action_types)
    behavior_name = "Successful Checkout Journey" if checkout_like and behavior_type == "normal" else name.removeprefix("Journey: ").strip()
    step_summary = [_explain_step(index + 1, step) for index, step in enumerate(steps)]
    chaining = []
    for index, step in enumerate(steps):
        for field, path in (step.get("extract") or {}).items():
            for later_index, later_step in enumerate(steps[index + 1 :], start=index + 2):
                if field in (later_step.get("uses") or {}):
                    chaining.append(
                        {
                            "fromStep": index + 1,
                            "fromPath": _json_path(str(path)),
                            "toStep": later_index,
                            "toPath": "path parameter" if later_step["uses"][field] == "path" else str(later_step["uses"][field]),
                        }
                    )
    return {
        "behaviorName": behavior_name,
        "behaviorType": behavior_type,
        "userGoal": _user_goal(action_types),
        "stepSummary": step_summary,
        "chaining": chaining,
        "riskNotes": _risk_notes(checkout_like, behavior_type),
    }

def _explain_step(number: int, step: dict[str, Any]) -> dict[str, Any]:
    api = f"{step.get('method') or 'GET'} {step.get('endpoint') or '/'}"
    return {
        "step": number,
        "api": api,
        "meaning": _step_meaning(str(step.get("action_type") or ""), api),
        "importantPayload": _payload_fields(step),
        "importantResponse": _response_fields(step),
        **({"inputFromPreviousStep": ", ".join(step.get("uses", {}).keys())} if step.get("uses") else {}),
    }

def _step_meaning(action_type: str, api: str) -> str:
    meanings = {
        ACTION_LOGIN: "User authenticates before continuing.",
        ACTION_SEARCH_PRODUCT: "User searches or filters products.",
        ACTION_VIEW_PRODUCT: "User views product detail before deciding.",
        ACTION_ADD_TO_CART: "User adds an item to the cart.",
        ACTION_CHECKOUT: "User submits checkout or creates an order.",
        ACTION_VIEW_ORDER: "User checks the created order status.",
        ACTION_PAYMENT_SUCCESS: "Payment succeeds and should update the order.",
        ACTION_PAYMENT_FAILED: "Payment fails and should preserve the failure behavior.",
    }
    return meanings.get(action_type, f"User calls {api}.")

def _payload_fields(step: dict[str, Any]) -> list[str]:
    summarized = step.get("important_payload_fields")
    if isinstance(summarized, list):
        return [str(field) for field in summarized]
    payload = step.get("request_payload") or {}
    if isinstance(payload, dict) and payload:
        return sorted(payload.keys())
    endpoint = str(step.get("endpoint") or "")
    if "/orders" in endpoint and str(step.get("method") or "").upper() == "POST":
        return ["shipping_address", "cartItems", "paymentMethod"]
    if "/cart/items" in endpoint:
        return ["product_id", "quantity"]
    return []

def _response_fields(step: dict[str, Any]) -> list[str]:
    summarized = step.get("important_response_fields")
    if isinstance(summarized, list):
        return [str(field) for field in summarized]
    response = step.get("response_body") or step.get("golden_response") or {}
    if isinstance(response, dict) and response:
        return sorted(response.keys())
    endpoint = str(step.get("endpoint") or "")
    if "/orders" in endpoint:
        return ["order_id", "order_status", "items", "total_amount"]
    if "/cart" in endpoint:
        return ["items", "total_amount"]
    if "/auth/login" in endpoint:
        return ["accessToken", "user"]
    return []

def _user_goal(action_types: set[str]) -> str:
    if ACTION_PAYMENT_FAILED in action_types:
        return "User attempts checkout and receives a failed payment response."
    if {ACTION_CHECKOUT, ACTION_VIEW_ORDER, ACTION_PAYMENT_SUCCESS} & action_types:
        return "User creates an order and verifies the resulting order behavior."
    if {ACTION_SEARCH_PRODUCT, ACTION_VIEW_PRODUCT} & action_types:
        return "User discovers products before purchasing."
    return "User performs a logged API behavior."

def _risk_notes(checkout_like: bool, behavior_type: str) -> list[str]:
    if checkout_like:
        return [
            "This journey is high value because it covers checkout and order status.",
            "Regression in this flow may block revenue-related user behavior.",
        ]
    if behavior_type != "normal":
        return ["This journey protects expected error handling behavior."]
    return ["This journey protects a common user behavior."]

def _json_path(path: str) -> str:
    return "$." + path.removeprefix("response.body.").removeprefix("body.").lstrip(".")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


_FETCH_LOG_ROWS_SQL = """
    SELECT
        logs.id,
        logs.session_id,
        sessions.external_session_id,
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
    LEFT JOIN sessions ON sessions.id = logs.session_id
    ORDER BY sessions.external_session_id ASC NULLS LAST, logs.occurred_at ASC
"""
