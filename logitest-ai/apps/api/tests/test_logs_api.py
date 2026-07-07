from datetime import datetime, timezone

import psycopg
from fastapi.testclient import TestClient

from app.main import app
from app.modules.ingestion import service
from app.modules.ingestion.elasticsearch_client import ElasticsearchImportError
from app.modules.ingestion.schemas import ImportElasticsearchLogsRequest, LogFilters, SessionFilters

client = TestClient(app)


def test_import_mock_logs_returns_summary(monkeypatch) -> None:
    expected = {
        "source": "mock-data/logs.json",
        "loaded_records": 18,
        "sessions": 3,
        "counts": {
            "sessions": 3,
            "logs": 18,
            "personas": 3,
            "journeys": 3,
            "test_cases": 3,
        },
    }
    monkeypatch.setattr(service, "import_mock_logs_from_dataset", lambda: expected)

    response = client.post("/api/logs/import-mock")

    assert response.status_code == 200
    assert response.json() == expected


def test_import_mock_logs_maps_database_errors(monkeypatch) -> None:
    def raise_database_error() -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "import_mock_logs_from_dataset", raise_database_error)

    response = client.post("/api/logs/import-mock")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_import_elasticsearch_logs_returns_summary(monkeypatch) -> None:
    expected = {
        "source": "elasticsearch",
        "index": "logitest-demo-logs",
        "loaded_records": 2,
        "imported_logs": 2,
        "sessions": 1,
        "counts": {"sessions": 1, "logs": 2},
        "limit": 25,
        "page_size": 500,
        "new_only": False,
    }

    def fake_import(request: ImportElasticsearchLogsRequest) -> dict:
        assert request.index == "logitest-demo-logs"
        assert request.limit == 25
        return expected

    monkeypatch.setattr(service, "import_elasticsearch_logs", fake_import)

    response = client.post(
        "/api/logs/import-elasticsearch",
        json={"index": "logitest-demo-logs", "limit": 25},
    )

    assert response.status_code == 200
    assert response.json() == expected

def test_import_elasticsearch_falls_back_to_shoplite_database(monkeypatch) -> None:
    expected = {
        "source": "shoplite_database",
        "index": "logitest-demo-logs",
        "loaded_records": 1,
        "imported_logs": 1,
        "sessions": 1,
        "counts": {"sessions": 1, "logs": 1},
        "limit": 5,
        "page_size": 500,
        "new_only": True,
    }

    def fake_import(request: ImportElasticsearchLogsRequest, *, index: str | None = None) -> dict:
        assert request.new_only is True
        assert request.limit == 5
        assert index == "logitest-demo-logs"
        return expected

    monkeypatch.setattr(service.settings, "elasticsearch_url", "")
    monkeypatch.setattr(service.settings, "shoplite_database_url", "postgresql://shoplite")
    monkeypatch.setattr(service, "import_shoplite_logs_from_database", fake_import)

    response = client.post("/api/logs/import-elasticsearch", json={"limit": 5, "new_only": True})

    assert response.status_code == 200
    assert response.json() == expected

def test_import_shoplite_database_reads_request_logs_and_uses_stable_ids(monkeypatch) -> None:
    latest = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    source_conn = FakeShopLiteSourceConnection(
        [
            {
                "id": "req-1",
                "timestamp": datetime(2026, 7, 1, 10, 1, tzinfo=timezone.utc),
                "environment": "production-demo",
                "service": "shoplite-api",
                "session_id": "sess-1",
                "trace_id": "trace-1",
                "user_id": "user-1",
                "method": "POST",
                "endpoint": "/api/auth/login",
                "request_body": {"email": "buyer@example.com"},
                "response_status": 200,
                "response_body": {"ok": True},
                "response_time_ms": 12,
                "error_code": None,
                "action_name": "LOGIN",
                "business_entity": "user",
                "business_entity_id": "user-1",
                "journey_hint": "login",
                "previous_step": None,
                "next_expected_step": "browse",
            }
        ]
    )
    dest_conn = FakeImportDestinationConnection()
    captured: dict[str, object] = {}

    def fake_upsert_sessions(conn, grouped_records, *, index: str, source: str) -> dict[str, str]:
        captured["session_source"] = source
        captured["grouped_records"] = grouped_records
        return {"sess-1": "session-db-id"}

    def fake_upsert_logs(conn, records, session_ids, *, index: str) -> None:
        captured["records"] = records
        captured["session_ids"] = session_ids
        captured["index"] = index

    monkeypatch.setattr(service.settings, "shoplite_database_url", "postgresql://shoplite")
    monkeypatch.setattr(service.psycopg, "connect", lambda *args, **kwargs: source_conn)
    monkeypatch.setattr(service.connection, "connect", lambda: dest_conn)
    monkeypatch.setattr(service, "_latest_imported_log_timestamp", lambda index: latest)
    monkeypatch.setattr(service, "_upsert_elasticsearch_sessions", fake_upsert_sessions)
    monkeypatch.setattr(service, "_upsert_elasticsearch_logs", fake_upsert_logs)
    monkeypatch.setattr(service, "_fetch_ingestion_counts", lambda conn: {"sessions": 1, "logs": 1})

    result = service.import_shoplite_logs_from_database(
        ImportElasticsearchLogsRequest(limit=5, new_only=True),
        index="logitest-demo-logs",
    )

    assert result["source"] == "shoplite_database"
    assert result["imported_logs"] == 1
    assert source_conn.params == [latest, 5]
    assert '"timestamp"  > %s' in source_conn.sql
    assert dest_conn.committed is True
    assert captured["session_source"] == "shoplite_database"
    records = captured["records"]
    assert records[0]["external_log_id"] == "shoplite:req-1"
    assert records[0]["request_id"] == "req-1"
    assert records[0]["request_payload"] == {"email": "***MASKED***"}

def test_import_elasticsearch_logs_validates_limit_bounds() -> None:
    assert client.post("/api/logs/import-elasticsearch", json={"limit": 0}).status_code == 422
    assert client.post("/api/logs/import-elasticsearch", json={"limit": 10001}).status_code == 422
    assert client.post("/api/logs/import-elasticsearch", json={"page_size": 1001}).status_code == 422

def test_import_elasticsearch_logs_maps_database_errors(monkeypatch) -> None:
    def raise_database_error(request: ImportElasticsearchLogsRequest) -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "import_elasticsearch_logs", raise_database_error)

    response = client.post("/api/logs/import-elasticsearch", json={})

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}

def test_import_elasticsearch_logs_maps_elasticsearch_errors(monkeypatch) -> None:
    def raise_elasticsearch_error(request: ImportElasticsearchLogsRequest) -> None:
        raise ElasticsearchImportError("search failed")

    monkeypatch.setattr(service, "import_elasticsearch_logs", raise_elasticsearch_error)

    response = client.post("/api/logs/import-elasticsearch", json={})

    assert response.status_code == 502
    assert response.json() == {"detail": "Elasticsearch log import failed."}

def test_import_shoplite_logs_returns_summary(monkeypatch) -> None:
    expected = {
        "source": "shoplite_jsonl",
        "path": "D:/ViettelDigitalTalent/LogiTest/shoplite/server/logs/request-logs.jsonl",
        "loaded_records": 3,
        "imported_logs": 3,
        "sessions": 1,
        "counts": {"sessions": 1, "logs": 3},
    }
    monkeypatch.setattr(service, "import_shoplite_logs_from_jsonl", lambda: expected)

    response = client.post("/api/logs/import-shoplite")

    assert response.status_code == 200
    assert response.json() == expected

def test_import_shoplite_logs_maps_missing_file(monkeypatch) -> None:
    def raise_missing_file() -> None:
        raise service.ShopLiteLogFileNotFoundError("missing.jsonl")

    monkeypatch.setattr(service, "import_shoplite_logs_from_jsonl", raise_missing_file)

    response = client.post("/api/logs/import-shoplite")

    assert response.status_code == 404
    assert response.json() == {"detail": "ShopLite log file not found: missing.jsonl"}

def test_import_shoplite_logs_maps_database_errors(monkeypatch) -> None:
    def raise_database_error() -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "import_shoplite_logs_from_jsonl", raise_database_error)

    response = client.post("/api/logs/import-shoplite")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}

def test_clear_database_returns_deleted_counts(monkeypatch) -> None:
    expected = {"cleared": True, "deleted": {"logs": 10, "sessions": 2}, "elasticsearch": None}
    monkeypatch.setattr(service, "clear_database", lambda: expected)

    response = client.delete("/api/logs/database")

    assert response.status_code == 200
    assert response.json() == expected

def test_clear_database_maps_database_errors(monkeypatch) -> None:
    def raise_database_error() -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "clear_database", raise_database_error)

    response = client.delete("/api/logs/database")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}

def test_clear_database_maps_elasticsearch_errors(monkeypatch) -> None:
    def raise_elasticsearch_error() -> None:
        raise ElasticsearchImportError("delete failed")

    monkeypatch.setattr(service, "clear_database", raise_elasticsearch_error)

    response = client.delete("/api/logs/database")

    assert response.status_code == 502
    assert response.json() == {"detail": "Elasticsearch clear failed."}

def test_list_logs_returns_paginated_items(monkeypatch) -> None:
    expected = {
        "items": [
            {
                "id": "b1ee7525-0f2b-4d97-9860-ecfbbd723091",
                "external_log_id": "log-buyer-001-login",
                "session_external_id": "session-buyer-001",
                "trace_id": "trace-buyer-001-login",
                "user_id": "user-buyer-001",
                "service_name": "auth-service",
                "level": "info",
                "method": "POST",
                "endpoint": "/auth/login",
                "status_code": 200,
                "action_type": "login",
                "request_payload": {"email": "buyer@example.com"},
                "response_body": {"status": "ok"},
                "raw_log": {
                    "action_name": "LOGIN",
                    "request_payload": {"email": "buyer@example.com"},
                    "response_body": {"status": "ok"},
                },
                "response_time_ms": 82,
                "occurred_at": "2026-06-23T09:00:00Z",
            }
        ],
        "limit": 5,
        "offset": 10,
        "total": 18,
    }

    def fake_list_logs(*, limit: int, offset: int, filters: LogFilters) -> dict:
        assert limit == 5
        assert offset == 10
        assert filters.session_id == "session-buyer-001"
        assert filters.trace_id is None
        assert filters.endpoint == "login"
        assert filters.level == "info"
        return expected

    monkeypatch.setattr(service, "list_logs", fake_list_logs)

    response = client.get(
        "/api/logs",
        params={"limit": 5, "offset": 10, "session_id": "session-buyer-001", "endpoint": "login", "level": "info"},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_list_logs_validates_limit_bounds() -> None:
    assert client.get("/api/logs", params={"limit": 0}).status_code == 422
    assert client.get("/api/logs", params={"limit": 501}).status_code == 422


def test_list_logs_validates_offset_bounds() -> None:
    assert client.get("/api/logs", params={"offset": -1}).status_code == 422


def test_list_logs_maps_database_errors(monkeypatch) -> None:
    def raise_database_error(*, limit: int, offset: int, filters: LogFilters) -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "list_logs", raise_database_error)

    response = client.get("/api/logs")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_list_sessions_returns_grouped_summaries(monkeypatch) -> None:
    expected = {
        "items": [
            {
                "id": "a1ee7525-0f2b-4d97-9860-ecfbbd723091",
                "external_session_id": "session-buyer-001",
                "user_id": "user-buyer-001",
                "started_at": "2026-06-23T09:00:00Z",
                "ended_at": "2026-06-23T09:01:20Z",
                "request_count": 7,
                "log_count": 7,
                "source": "mock_json",
                "services": ["auth-service", "order-service", "product-service"],
                "created_at": "2026-06-23T09:02:00Z",
            }
        ],
        "limit": 5,
        "offset": 10,
        "total": 3,
    }

    def fake_list_sessions(*, limit: int, offset: int, filters: SessionFilters) -> dict:
        assert limit == 5
        assert offset == 10
        assert filters.user_id == "user-buyer-001"
        assert filters.source == "mock_json"
        return expected

    monkeypatch.setattr(service, "list_sessions", fake_list_sessions)

    response = client.get(
        "/api/logs/sessions",
        params={"limit": 5, "offset": 10, "user_id": "user-buyer-001", "source": "mock_json"},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_list_sessions_validates_pagination_bounds() -> None:
    assert client.get("/api/logs/sessions", params={"limit": 0}).status_code == 422
    assert client.get("/api/logs/sessions", params={"limit": 501}).status_code == 422
    assert client.get("/api/logs/sessions", params={"offset": -1}).status_code == 422


def test_list_sessions_maps_database_errors(monkeypatch) -> None:
    def raise_database_error(*, limit: int, offset: int, filters: SessionFilters) -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "list_sessions", raise_database_error)

    response = client.get("/api/logs/sessions")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_get_session_detail_returns_session_and_ordered_logs(monkeypatch) -> None:
    expected = {
        "session": {
            "id": "a1ee7525-0f2b-4d97-9860-ecfbbd723091",
            "external_session_id": "session-buyer-001",
            "user_id": "user-buyer-001",
            "started_at": "2026-06-23T09:00:00Z",
            "ended_at": "2026-06-23T09:01:20Z",
            "request_count": 7,
            "log_count": 2,
            "source": "mock_json",
            "services": [],
            "metadata": {"source_file": "mock-data/logs.json"},
            "created_at": "2026-06-23T09:02:00Z",
        },
        "logs": [
            {
                "id": "b1ee7525-0f2b-4d97-9860-ecfbbd723091",
                "external_log_id": "log-buyer-001-login",
                "trace_id": "trace-buyer-001-login",
                "user_id": "user-buyer-001",
                "service_name": "auth-service",
                "level": "info",
                "method": "POST",
                "endpoint": "/auth/login",
                "status_code": 200,
                "response_time_ms": 82,
                "occurred_at": "2026-06-23T09:00:00Z",
            },
            {
                "id": "c1ee7525-0f2b-4d97-9860-ecfbbd723091",
                "external_log_id": "log-buyer-001-search",
                "trace_id": "trace-buyer-001-search",
                "user_id": "user-buyer-001",
                "service_name": "product-service",
                "level": "info",
                "method": "GET",
                "endpoint": "/products?query=headphones",
                "status_code": 200,
                "response_time_ms": 96,
                "occurred_at": "2026-06-23T09:00:08Z",
            },
        ],
    }

    def fake_get_session_detail(external_session_id: str) -> dict:
        assert external_session_id == "session-buyer-001"
        return expected

    monkeypatch.setattr(service, "get_session_detail", fake_get_session_detail)

    response = client.get("/api/logs/sessions/session-buyer-001")

    assert response.status_code == 200
    assert response.json() == expected


def test_get_session_detail_returns_404_for_missing_session(monkeypatch) -> None:
    def raise_not_found(external_session_id: str) -> None:
        raise service.SessionNotFoundError(external_session_id)

    monkeypatch.setattr(service, "get_session_detail", raise_not_found)

    response = client.get("/api/logs/sessions/missing-session")

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found."}


def test_get_session_detail_maps_database_errors(monkeypatch) -> None:
    def raise_database_error(external_session_id: str) -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "get_session_detail", raise_database_error)

    response = client.get("/api/logs/sessions/session-buyer-001")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_build_log_filters_uses_whitelisted_parameterized_conditions() -> None:
    filters = LogFilters(
        session_id="session-buyer-001",
        trace_id="trace-buyer-001-login",
        endpoint="login%' OR 1=1 --",
        level="info",
    )

    where_sql, params = service._build_log_filters(filters)

    assert where_sql == (
        "WHERE sessions.external_session_id = %s AND logs.trace_id = %s "
        "AND logs.endpoint ILIKE %s AND logs.level = %s"
    )
    assert params == [
        "session-buyer-001",
        "trace-buyer-001-login",
        "%login%' OR 1=1 --%",
        "info",
    ]


def test_build_session_filters_uses_whitelisted_parameterized_conditions() -> None:
    filters = SessionFilters(user_id="user-buyer-001' OR 1=1 --", source="mock_json")

    where_sql, params = service._build_session_filters(filters)

    assert where_sql == "WHERE sessions.user_id = %s AND sessions.source = %s"
    assert params == ["user-buyer-001' OR 1=1 --", "mock_json"]


def test_serialize_session_summary_coalesces_empty_services() -> None:
    row = {
        "id": "a1ee7525-0f2b-4d97-9860-ecfbbd723091",
        "external_session_id": "session-empty-001",
        "user_id": None,
        "started_at": None,
        "ended_at": None,
        "request_count": 0,
        "log_count": 0,
        "source": "mock_json",
        "services": None,
        "created_at": "2026-06-23T09:02:00Z",
    }

    serialized = service._serialize_session_summary_row(row)

    assert serialized["id"] == "a1ee7525-0f2b-4d97-9860-ecfbbd723091"
    assert serialized["services"] == []

class FakeShopLiteSourceConnection:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.sql = ""
        self.params = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self):
        return self

    def execute(self, sql: str, params: list) -> None:
        self.sql = sql
        self.params = params

    def fetchall(self) -> list[dict]:
        return self.rows

class FakeImportDestinationConnection:
    def __init__(self) -> None:
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def commit(self) -> None:
        self.committed = True
