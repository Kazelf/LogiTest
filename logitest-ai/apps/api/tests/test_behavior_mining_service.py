from decimal import Decimal

from app.modules.behavior_mining import service
from app.modules.behavior_mining.schemas import JourneyFilters, PersonaFilters


def test_detect_persona_uses_expected_precedence() -> None:
    assert service._detect_persona({"payment_failed", "payment_success"}).name == "Failed Payment User"
    assert service._detect_persona({"payment_success"}).name == "Buyer"
    assert service._detect_persona({"search_product"}).name == "Browser"
    assert service._detect_persona({"search_product", "checkout"}).name == "Unknown User"
    assert service._detect_persona({"unknown"}).name == "Unknown User"


def test_build_journey_drafts_groups_identical_action_sequences() -> None:
    session_groups = {
        "session-a": [
            _row("db-session-a", "login", 1),
            _row("db-session-a", "search_product", 2),
            _row("db-session-a", "view_product", 3),
        ],
        "session-b": [
            _row("db-session-b", "login", 1),
            _row("db-session-b", "search_product", 2),
            _row("db-session-b", "view_product", 3),
        ],
        "session-c": [
            _row("db-session-c", "login", 1),
            _row("db-session-c", "payment_failed", 2),
        ],
    }

    drafts = service._build_journey_drafts(session_groups)

    assert len(drafts) == 2
    browser_draft = next(draft for draft in drafts if draft.persona_name == "Browser")
    failed_payment_draft = next(draft for draft in drafts if draft.persona_name == "Failed Payment User")
    assert browser_draft.source_session_count == 2
    assert browser_draft.frequency_score == 0.6667
    assert browser_draft.risk_score == 0.25
    assert failed_payment_draft.source_session_count == 1
    assert failed_payment_draft.risk_score == 0.9


def test_build_filter_helpers_use_parameterized_conditions() -> None:
    persona_sql, persona_params = service._build_persona_filters(PersonaFilters(name="buyer%' OR 1=1 --"))
    journey_sql, journey_params = service._build_journey_filters(
        JourneyFilters(persona_id="persona-id", name="checkout%' OR 1=1 --")
    )

    assert persona_sql == "WHERE personas.name ILIKE %s"
    assert persona_params == ["%buyer%' OR 1=1 --%"]
    assert journey_sql == "WHERE journeys.persona_id = %s AND journeys.name ILIKE %s"
    assert journey_params == ["persona-id", "%checkout%' OR 1=1 --%"]


def test_serialize_rows_normalizes_ids_json_and_decimals() -> None:
    persona = service._serialize_persona_row(
        {
            "id": "persona-id",
            "name": "Buyer",
            "description": None,
            "detection_method": "rule_based",
            "confidence_score": Decimal("0.9500"),
            "features": None,
            "created_at": "created",
            "updated_at": "updated",
        }
    )
    journey = service._serialize_journey_row(
        {
            "id": "journey-id",
            "persona_id": None,
            "persona_name": None,
            "name": "Journey: unknown",
            "description": None,
            "source_session_count": 1,
            "frequency_score": Decimal("0.3333"),
            "risk_score": Decimal("0.2500"),
            "steps": None,
            "example_session_id": None,
            "created_at": "created",
            "updated_at": "updated",
        }
    )

    assert persona["id"] == "persona-id"
    assert persona["confidence_score"] == 0.95
    assert persona["features"] == {}
    assert journey["frequency_score"] == 0.3333
    assert journey["risk_score"] == 0.25
    assert journey["steps"] == []
    assert journey["behavior_analysis"]["ai_provider"] == "rule_based"
    assert journey["behavior_analysis"]["fallback_used"] is True


def test_upsert_helpers_write_personas_and_journeys() -> None:
    cursor = FakeCursor()
    persona = service.PersonaSpec("Buyer", "desc", 0.95, {"signals": ["payment_success"]})
    persona_ids = service._upsert_personas(cursor, [persona])
    draft = service.JourneyDraft(
        name="Journey: login > payment_success",
        description="Mined from 1 session(s).",
        persona_name="Buyer",
        journey_type=service.JOURNEY_ASYNC_PAYMENT_FLOW,
        source_session_count=1,
        frequency_score=1.0,
        risk_score=0.62,
        steps=[{"order": 1, "action_type": "login"}],
        example_session_id="session-id",
    )

    upserted = service._upsert_journeys(cursor, [draft], persona_ids)

    assert persona_ids == {"Buyer": "persona-id"}
    assert upserted == 1
    assert "INSERT INTO personas" in cursor.executions[0][0]
    assert "ON CONFLICT (name) DO UPDATE" in cursor.executions[0][0]
    assert "INSERT INTO journeys" in cursor.executions[1][0]
    assert cursor.executions[1][1][0] == "persona-id"


def test_detect_journey_type_prioritizes_demo_flows() -> None:
    assert service._detect_journey_type({"login"}) == service.JOURNEY_LOGIN_FLOW
    assert service._detect_journey_type({"login", "search_product"}) == service.JOURNEY_SEARCH_FLOW
    assert service._detect_journey_type({"login", "search_product", "checkout"}) == service.JOURNEY_ORDER_CREATION_FLOW
    assert service._detect_journey_type({"checkout", "payment_success"}) == service.JOURNEY_ASYNC_PAYMENT_FLOW

def test_build_journey_drafts_adds_flow_type_to_steps() -> None:
    drafts = service._build_journey_drafts(
        {
            "session-login": [_row("db-session-login", "login", 1)],
            "session-search": [
                _row("db-session-search", "login", 1),
                _row("db-session-search", "search_product", 2),
            ],
            "session-order": [
                _row("db-session-order", "login", 1),
                _row("db-session-order", "checkout", 2),
            ],
        }
    )

    flow_types = {draft.journey_type for draft in drafts}
    assert service.JOURNEY_LOGIN_FLOW in flow_types
    assert service.JOURNEY_SEARCH_FLOW in flow_types
    assert service.JOURNEY_ORDER_CREATION_FLOW in flow_types
    assert all(step["type"] == draft.journey_type for draft in drafts for step in draft.steps)

def test_build_journey_drafts_omits_unknown_and_collapses_duplicate_actions() -> None:
    drafts = service._build_journey_drafts(
        {
            "session-order": [
                _row("db-session-order", "unknown", 1),
                _row("db-session-order", "login", 2),
                _row("db-session-order", "search_product", 3),
                _row("db-session-order", "view_product", 4),
                _row("db-session-order", "search_product", 5),
                _row("db-session-order", "unknown", 6),
                _row("db-session-order", "add_to_cart", 7),
                _row("db-session-order", "unknown", 8),
                _row("db-session-order", "add_to_cart", 9),
                _row("db-session-order", "checkout", 10),
                _row("db-session-order", "checkout", 11),
                _row("db-session-order", "view_order", 12),
                _row("db-session-order", "view_order", 13),
            ]
        }
    )

    assert len(drafts) == 1
    assert drafts[0].name == "Journey: ORDER_CREATION_FLOW - login > search_product > view_product > add_to_cart > checkout > view_order"
    assert [step["action_type"] for step in drafts[0].steps] == [
        "login",
        "search_product",
        "view_product",
        "add_to_cart",
        "checkout",
        "view_order",
    ]
    assert [step["order"] for step in drafts[0].steps] == [1, 2, 3, 4, 5, 6]

def test_build_journey_drafts_reclassifies_imported_unknown_actions() -> None:
    drafts = service._build_journey_drafts(
        {
            "session-order": [
                _row("db-session-order", "unknown", 1, method="POST", endpoint="/api/auth/login", status_code=200),
                _row(
                    "db-session-order",
                    "unknown",
                    2,
                    method="POST",
                    endpoint="/api/vouchers/apply",
                    raw_log={"action_name": "APPLY_VOUCHER"},
                    status_code=200,
                ),
                _row(
                    "db-session-order",
                    "unknown",
                    3,
                    method="GET",
                    endpoint="/api/orders",
                    raw_log={"action_name": "VIEW_ORDER_HISTORY"},
                    status_code=200,
                ),
            ]
        }
    )

    assert len(drafts) == 1
    assert drafts[0].name == "Journey: ORDER_CREATION_FLOW - login > checkout > view_order"

def test_build_steps_extracts_and_uses_order_id_chaining() -> None:
    steps = service._build_steps(
        [
            _row(
                "db-session-order",
                "checkout",
                1,
                method="POST",
                endpoint="/api/orders",
                response_body={"orderId": "order-123", "status": "created"},
                status_code=201,
            ),
            _row(
                "db-session-order",
                "view_order",
                2,
                method="GET",
                endpoint="/api/orders/order-123",
                request_payload={"orderId": "order-123"},
            ),
        ]
    )

    assert steps[0]["extract"] == {"orderId": "response.body.orderId"}
    assert steps[1]["uses"] == {"orderId": "path"}
    assert steps[0]["important_response_fields"] == ["orderId", "status"]
    assert "response_body" not in steps[0]

def test_clear_journeys_deletes_stale_analysis_rows() -> None:
    cursor = FakeCursor()

    service._clear_journeys(cursor)

    assert cursor.executions[-1] == ("DELETE FROM journeys", ())

def test_build_behavior_analysis_uses_gemini_when_available(monkeypatch) -> None:
    service._cached_gemini_behavior.cache_clear()
    monkeypatch.setattr(service.gemini_client, "gemini_available", lambda: True)
    monkeypatch.setattr(
        service.gemini_client,
        "generate_behavior_explanation",
        lambda name, steps: {
            "behaviorName": "Gemini Checkout",
            "behaviorType": "normal",
            "userGoal": "Generated by Gemini",
            "stepSummary": [],
            "chaining": [],
            "riskNotes": [],
        },
    )
    monkeypatch.setattr(
        service.gemini_client,
        "metadata",
        lambda *, fallback_used: {
            "ai_provider": "gemini" if not fallback_used else "rule_based",
            "ai_model": "gemini-test" if not fallback_used else None,
            "fallback_used": fallback_used,
            "prompt_version": "test",
        },
    )

    analysis = service._build_behavior_analysis("Journey: checkout", [{"order": 1, "method": "POST", "endpoint": "/api/orders"}])

    assert analysis["behaviorName"] == "Gemini Checkout"
    assert analysis["ai_provider"] == "gemini"
    assert analysis["ai_model"] == "gemini-test"
    assert analysis["fallback_used"] is False

def _row(
    session_id: str,
    action_type: str,
    order: int,
    *,
    method: str = "GET",
    endpoint: str | None = None,
    request_payload: dict | None = None,
    response_body: dict | None = None,
    raw_log: dict | None = None,
    status_code: int = 200,
) -> dict:
    return {
        "session_id": session_id,
        "method": method,
        "endpoint": endpoint or f"/step/{order}",
        "status_code": status_code,
        "response_time_ms": 50,
        "action_type": action_type,
        "request_payload": request_payload or {},
        "response_body": response_body or {},
        "raw_log": raw_log or {},
    }


class FakeCursor:
    def __init__(self) -> None:
        self.executions: list[tuple[str, tuple]] = []
        self.fetchone_results = [{"id": "persona-id"}, {"id": "journey-id"}]

    def execute(self, sql: str, params: tuple) -> None:
        self.executions.append((sql, params))

    def fetchone(self) -> dict:
        return self.fetchone_results.pop(0)
