from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlsplit

ACTION_ADD_TO_CART = "add_to_cart"
ACTION_CHECKOUT = "checkout"
ACTION_LOGIN = "login"
ACTION_PAYMENT_FAILED = "payment_failed"
ACTION_PAYMENT_SUCCESS = "payment_success"
ACTION_SEARCH_PRODUCT = "search_product"
ACTION_UNKNOWN = "unknown"
ACTION_VIEW_ORDER = "view_order"
ACTION_VIEW_PRODUCT = "view_product"

UNKNOWN_SESSION_ID = "unknown"

SHOPLITE_ACTION_NAME_MAP = {
    "ADD_TO_CART": ACTION_ADD_TO_CART,
    "APPLY_VOUCHER": ACTION_CHECKOUT,
    "CHECKOUT": ACTION_CHECKOUT,
    "CREATE_ORDER": ACTION_CHECKOUT,
    "FILTER_PRODUCTS": ACTION_SEARCH_PRODUCT,
    "LIST_CATEGORIES": ACTION_SEARCH_PRODUCT,
    "LOGIN": ACTION_LOGIN,
    "PAYMENT_FAILED": ACTION_PAYMENT_FAILED,
    "PAYMENT_SUCCESS": ACTION_PAYMENT_SUCCESS,
    "REGISTER": ACTION_LOGIN,
    "REMOVE_VOUCHER": ACTION_CHECKOUT,
    "SEARCH_PRODUCTS": ACTION_SEARCH_PRODUCT,
    "SORT_PRODUCTS": ACTION_SEARCH_PRODUCT,
    "VIEW_ORDER_DETAIL": ACTION_VIEW_ORDER,
    "VIEW_ORDER_HISTORY": ACTION_VIEW_ORDER,
    "VIEW_PRODUCT_DETAIL": ACTION_VIEW_PRODUCT,
    "VIEW_PRODUCTS": ACTION_SEARCH_PRODUCT,
}


@dataclass(frozen=True)
class ActionClassification:
    action_type: str
    confidence: float
    signals: tuple[str, ...]


def group_logs_by_session(logs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for log in logs:
        session_id = log.get("session_id") or log.get("session_external_id") or UNKNOWN_SESSION_ID
        sessions[str(session_id)].append(log)

    return dict(sessions)


def sort_logs_by_timestamp(logs: list[dict[str, Any]], *, ascending: bool = True) -> list[dict[str, Any]]:
    valid: list[tuple[datetime, dict[str, Any]]] = []
    invalid: list[dict[str, Any]] = []

    for log in logs:
        parsed = _parse_log_timestamp(log)
        if parsed is None:
            invalid.append(log)
        else:
            valid.append((parsed, log))

    valid.sort(key=lambda item: item[0], reverse=not ascending)
    return [log for _, log in valid] + invalid


def classify_action(log: dict[str, Any]) -> ActionClassification:
    method = str(log.get("method") or "").upper()
    endpoint = str(log.get("endpoint") or "")
    status_code = _coerce_int(log.get("status_code", log.get("response_status")))
    response_body = log.get("response_body") if isinstance(log.get("response_body"), dict) else {}
    response_status = str(response_body.get("status") or "").lower()
    payment_status = str(response_body.get("payment_status") or "").lower()
    parsed_endpoint = urlsplit(endpoint)
    path = normalize_endpoint_path(parsed_endpoint.path)
    query = parse_qs(parsed_endpoint.query)
    base_signal = f"{method} {path}"
    metadata_action_type = _classify_from_action_name(log)

    if metadata_action_type is not None:
        return ActionClassification(metadata_action_type, 0.99, (base_signal, "action_name"))

    if method == "POST" and path == "/auth/login" and _is_success(status_code):
        return ActionClassification(ACTION_LOGIN, 0.95, (base_signal, f"status_code={status_code}"))

    if method == "GET" and path == "/products":
        query_signal = "query=query" if "query" in query or "keyword" in query else "product_list"
        return ActionClassification(ACTION_SEARCH_PRODUCT, 0.95, (base_signal, query_signal))

    if method == "GET" and path.startswith("/products/"):
        return ActionClassification(ACTION_VIEW_PRODUCT, 0.9, (base_signal,))

    if method == "POST" and path == "/cart/items" and _is_success(status_code):
        return ActionClassification(ACTION_ADD_TO_CART, 0.95, (base_signal, f"status_code={status_code}"))

    if method == "POST" and path == "/orders" and _is_success(status_code):
        return ActionClassification(ACTION_CHECKOUT, 0.9, (base_signal, f"status_code={status_code}"))

    if method == "POST" and path == "/checkout" and _is_success(status_code):
        return ActionClassification(ACTION_CHECKOUT, 0.9, (base_signal, f"status_code={status_code}"))

    if method == "POST" and path == "/payments":
        if _is_client_or_server_error(status_code) or response_status == "declined":
            return ActionClassification(
                ACTION_PAYMENT_FAILED,
                0.98,
                (base_signal, f"status_code={status_code}", f"response.status={response_status}"),
            )
        if _is_success(status_code) and response_status == "paid":
            return ActionClassification(
                ACTION_PAYMENT_SUCCESS,
                0.98,
                (base_signal, f"status_code={status_code}", "response.status=paid"),
            )

    if method == "POST" and path == "/payments/simulate-failed":
        return ActionClassification(
            ACTION_PAYMENT_FAILED,
            0.98,
            (base_signal, f"status_code={status_code}", f"response.payment_status={payment_status}"),
        )

    if method == "POST" and path == "/payments/simulate-success":
        return ActionClassification(
            ACTION_PAYMENT_SUCCESS,
            0.98,
            (base_signal, f"status_code={status_code}", f"response.payment_status={payment_status}"),
        )

    if method == "GET" and (path == "/orders" or path.startswith("/orders/")):
        return ActionClassification(ACTION_VIEW_ORDER, 0.9, (base_signal,))

    return ActionClassification(ACTION_UNKNOWN, 0.0, (base_signal,))


def classify_logs(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**log, "action_type": classify_action(log).action_type} for log in logs]


def normalize_endpoint_path(endpoint: str) -> str:
    path = urlsplit(str(endpoint or "")).path.rstrip("/") or "/"
    if path == "/api":
        return "/"
    if path.startswith("/api/"):
        return path[4:] or "/"
    return path

def _classify_from_action_name(log: dict[str, Any]) -> str | None:
    action_name = _metadata_value(log, "action_name")
    if action_name is None:
        return None
    return SHOPLITE_ACTION_NAME_MAP.get(str(action_name).upper())

def _metadata_value(log: dict[str, Any], key: str) -> Any:
    if log.get(key) not in (None, ""):
        return log.get(key)

    raw_log = log.get("raw_log")
    if isinstance(raw_log, dict) and raw_log.get(key) not in (None, ""):
        return raw_log.get(key)

    return None

def _parse_log_timestamp(log: dict[str, Any]) -> datetime | None:
    return _parse_timestamp(log.get("timestamp", log.get("occurred_at")))


def _parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_success(status_code: int | None) -> bool:
    return status_code is not None and 200 <= status_code < 300


def _is_client_or_server_error(status_code: int | None) -> bool:
    return status_code is not None and status_code >= 400
