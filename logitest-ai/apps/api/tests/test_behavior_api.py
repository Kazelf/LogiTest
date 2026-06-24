import psycopg
from fastapi.testclient import TestClient

from app.main import app
from app.modules.behavior_mining import service
from app.modules.behavior_mining.schemas import JourneyFilters, PersonaFilters

client = TestClient(app)


def test_analyze_behavior_returns_summary(monkeypatch) -> None:
    expected = {
        "sessions_analyzed": 3,
        "personas_upserted": 3,
        "journeys_upserted": 3,
        "source": "logs",
        "method": "rule_based",
    }
    monkeypatch.setattr(service, "analyze_behavior", lambda: expected)

    response = client.post("/api/behavior/analyze")

    assert response.status_code == 200
    assert response.json() == expected


def test_analyze_behavior_maps_database_errors(monkeypatch) -> None:
    def raise_database_error() -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "analyze_behavior", raise_database_error)

    response = client.post("/api/behavior/analyze")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_analyze_behavior_maps_unexpected_errors(monkeypatch) -> None:
    def raise_unexpected_error() -> None:
        raise RuntimeError("bad mining state")

    monkeypatch.setattr(service, "analyze_behavior", raise_unexpected_error)

    response = client.post("/api/behavior/analyze")

    assert response.status_code == 500
    assert response.json() == {"detail": "Behavior analysis failed."}


def test_list_journeys_returns_paginated_items(monkeypatch) -> None:
    expected = {
        "items": [
            {
                "id": "journey-id",
                "persona_id": "persona-id",
                "persona_name": "Buyer",
                "name": "Journey: login > payment_success",
                "description": "Mined from 1 session(s).",
                "source_session_count": 1,
                "frequency_score": 0.3333,
                "risk_score": 0.62,
                "steps": [{"order": 1, "action_type": "login"}],
                "example_session_id": "session-id",
                "created_at": "2026-06-24T00:00:00Z",
                "updated_at": "2026-06-24T00:00:00Z",
            }
        ],
        "limit": 5,
        "offset": 10,
        "total": 1,
    }

    def fake_list_journeys(*, limit: int, offset: int, filters: JourneyFilters) -> dict:
        assert limit == 5
        assert offset == 10
        assert filters.persona_id == "persona-id"
        assert filters.name == "buyer"
        return expected

    monkeypatch.setattr(service, "list_journeys", fake_list_journeys)

    response = client.get(
        "/api/behavior/journeys",
        params={"limit": 5, "offset": 10, "persona_id": "persona-id", "name": "buyer"},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_list_personas_returns_paginated_items(monkeypatch) -> None:
    expected = {
        "items": [
            {
                "id": "persona-id",
                "name": "Buyer",
                "description": "User completes checkout and successful payment.",
                "detection_method": "rule_based",
                "confidence_score": 0.95,
                "features": {"signals": ["checkout", "payment_success"]},
                "created_at": "2026-06-24T00:00:00Z",
                "updated_at": "2026-06-24T00:00:00Z",
            }
        ],
        "limit": 5,
        "offset": 10,
        "total": 1,
    }

    def fake_list_personas(*, limit: int, offset: int, filters: PersonaFilters) -> dict:
        assert limit == 5
        assert offset == 10
        assert filters.name == "buyer"
        return expected

    monkeypatch.setattr(service, "list_personas", fake_list_personas)

    response = client.get("/api/behavior/personas", params={"limit": 5, "offset": 10, "name": "buyer"})

    assert response.status_code == 200
    assert response.json() == expected


def test_behavior_list_routes_validate_pagination_bounds() -> None:
    assert client.get("/api/behavior/journeys", params={"limit": 0}).status_code == 422
    assert client.get("/api/behavior/journeys", params={"limit": 201}).status_code == 422
    assert client.get("/api/behavior/journeys", params={"offset": -1}).status_code == 422
    assert client.get("/api/behavior/personas", params={"limit": 0}).status_code == 422
    assert client.get("/api/behavior/personas", params={"limit": 201}).status_code == 422
    assert client.get("/api/behavior/personas", params={"offset": -1}).status_code == 422


def test_behavior_list_routes_map_database_errors(monkeypatch) -> None:
    def raise_journey_database_error(*, limit: int, offset: int, filters: JourneyFilters) -> None:
        raise psycopg.OperationalError("connection failed")

    def raise_persona_database_error(*, limit: int, offset: int, filters: PersonaFilters) -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "list_journeys", raise_journey_database_error)
    monkeypatch.setattr(service, "list_personas", raise_persona_database_error)

    assert client.get("/api/behavior/journeys").status_code == 503
    assert client.get("/api/behavior/personas").status_code == 503
