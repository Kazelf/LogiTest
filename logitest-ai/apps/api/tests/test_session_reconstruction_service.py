from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.session_reconstruction import (
    ACTION_ADD_TO_CART,
    ACTION_CHECKOUT,
    ACTION_LOGIN,
    ACTION_PAYMENT_FAILED,
    ACTION_PAYMENT_SUCCESS,
    ACTION_SEARCH_PRODUCT,
    ACTION_UNKNOWN,
    ACTION_VIEW_ORDER,
    ACTION_VIEW_PRODUCT,
    UNKNOWN_SESSION_ID,
    classify_action,
    classify_logs,
    group_logs_by_session,
    sort_logs_by_timestamp,
)


def test_group_logs_by_session_uses_unknown_for_missing_session_ids() -> None:
    logs = [
        {"external_log_id": "1", "session_id": "session-a"},
        {"external_log_id": "2", "session_external_id": "session-b"},
        {"external_log_id": "3", "session_id": ""},
        {"external_log_id": "4"},
    ]

    grouped = group_logs_by_session(logs)

    assert [log["external_log_id"] for log in grouped["session-a"]] == ["1"]
    assert [log["external_log_id"] for log in grouped["session-b"]] == ["2"]
    assert [log["external_log_id"] for log in grouped[UNKNOWN_SESSION_ID]] == ["3", "4"]


def test_sort_logs_by_timestamp_supports_timestamp_and_occurred_at_with_invalid_last() -> None:
    newest = {"external_log_id": "newest", "timestamp": "2026-06-23T09:00:20Z"}
    oldest = {"external_log_id": "oldest", "occurred_at": datetime(2026, 6, 23, 9, 0, tzinfo=timezone.utc)}
    middle = {"external_log_id": "middle", "timestamp": "2026-06-23T09:00:10Z"}
    invalid = {"external_log_id": "invalid", "timestamp": "not-a-date"}

    sorted_logs = sort_logs_by_timestamp([newest, invalid, oldest, middle])

    assert [log["external_log_id"] for log in sorted_logs] == ["oldest", "middle", "newest", "invalid"]
    assert [log["external_log_id"] for log in sort_logs_by_timestamp(sorted_logs, ascending=False)] == [
        "newest",
        "middle",
        "oldest",
        "invalid",
    ]


def test_classify_action_recognizes_ecommerce_action_types() -> None:
    examples = [
        ({"method": "POST", "endpoint": "/auth/login", "response_status": 200}, ACTION_LOGIN),
        ({"method": "GET", "endpoint": "/products?query=headphones", "response_status": 200}, ACTION_SEARCH_PRODUCT),
        ({"method": "GET", "endpoint": "/products/prod-headphone-001", "response_status": 200}, ACTION_VIEW_PRODUCT),
        ({"method": "POST", "endpoint": "/cart/items", "response_status": 201}, ACTION_ADD_TO_CART),
        ({"method": "POST", "endpoint": "/orders", "response_status": 201}, ACTION_CHECKOUT),
        (
            {"method": "POST", "endpoint": "/payments", "response_status": 200, "response_body": {"status": "paid"}},
            ACTION_PAYMENT_SUCCESS,
        ),
        (
            {"method": "POST", "endpoint": "/payments", "response_status": 402, "response_body": {"status": "declined"}},
            ACTION_PAYMENT_FAILED,
        ),
        ({"method": "GET", "endpoint": "/orders/order-buyer-001", "response_status": 200}, ACTION_VIEW_ORDER),
        ({"method": "DELETE", "endpoint": "/sessions/current", "response_status": 204}, ACTION_UNKNOWN),
    ]

    for log, expected_action_type in examples:
        assert classify_action(log).action_type == expected_action_type


def test_classify_action_prioritizes_payment_decline_over_2xx_success() -> None:
    classification = classify_action(
        {"method": "POST", "endpoint": "/payments", "response_status": 200, "response_body": {"status": "declined"}}
    )

    assert classification.action_type == ACTION_PAYMENT_FAILED


def test_classify_logs_returns_copies_with_action_type() -> None:
    logs = [{"method": "POST", "endpoint": "/auth/login", "response_status": 200}]

    classified = classify_logs(logs)

    assert classified == [{"method": "POST", "endpoint": "/auth/login", "response_status": 200, "action_type": ACTION_LOGIN}]
    assert "action_type" not in logs[0]


def test_import_mock_logs_persists_classified_action_type() -> None:
    importer = _load_import_script()
    conn = FakeConnection()
    record = {
        "external_log_id": "log-buyer-001-login",
        "timestamp": "2026-06-23T09:00:00Z",
        "level": "info",
        "service_name": "auth-service",
        "trace_id": "trace-buyer-001-login",
        "session_id": "session-buyer-001",
        "user_id": "user-buyer-001",
        "method": "POST",
        "endpoint": "/auth/login",
        "request_payload": {"username": "buyer_001"},
        "response_status": 200,
        "response_body": {"status": "ok"},
        "response_time_ms": 82,
    }

    importer.upsert_logs(conn, [record], {"session-buyer-001": "db-session-id"})

    sql, params = conn.cursor_instance.executions[0]
    assert "action_type" in sql
    assert "action_type = EXCLUDED.action_type" in sql
    assert params[12] == ACTION_LOGIN


def _load_import_script() -> Any:
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "import_mock_logs.py"
    spec = importlib.util.spec_from_file_location("test_import_mock_logs", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()

    def cursor(self) -> "FakeCursor":
        return self.cursor_instance


class FakeCursor:
    def __init__(self) -> None:
        self.executions: list[tuple[str, tuple[Any, ...]]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...]) -> None:
        self.executions.append((sql, params))
