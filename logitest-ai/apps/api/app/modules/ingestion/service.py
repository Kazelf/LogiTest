from __future__ import annotations

import importlib.util
import hashlib
import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.core.settings import settings
from app.db import connection
from app.modules.ingestion import elasticsearch_client
from app.modules.ingestion.schemas import ImportElasticsearchLogsRequest, LogFilters, SessionFilters
from app.modules.session_reconstruction import classify_action, group_logs_by_session, sort_logs_by_timestamp

def _find_project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts" / "import_mock_logs.py").exists():
            return parent
    return Path(__file__).resolve().parents[3]

PROJECT_ROOT = _find_project_root()
IMPORT_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_mock_logs.py"
MOCK_LOGS_SOURCE = "mock-data/logs.json"
SHOPLITE_LOG_SOURCE = "shoplite_jsonl"
DEFAULT_SHOPLITE_LOG_PATH = PROJECT_ROOT.parent / "shoplite" / "server" / "logs" / "request-logs.jsonl"


class SessionNotFoundError(Exception):
    pass

class ShopLiteLogFileNotFoundError(Exception):
    pass

SENSITIVE_KEYS = {
    "authorization",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "accesstoken",
    "refreshtoken",
    "email",
    "phone",
}


@lru_cache(maxsize=1)
def _load_import_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("logitest_import_mock_logs", IMPORT_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load import script at {IMPORT_SCRIPT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_mock_logs_from_dataset() -> dict[str, Any]:
    importer = _load_import_module()
    records = importer.load_logs()
    grouped_records = importer.group_by_session(records)

    with connection.connect() as conn:
        session_ids = importer.upsert_sessions(conn, grouped_records)
        importer.upsert_logs(conn, records, session_ids)
        persona_ids = importer.upsert_personas(conn)
        journey_ids = importer.upsert_journeys(conn, grouped_records, session_ids, persona_ids)
        importer.upsert_test_cases(conn, grouped_records, persona_ids, journey_ids)
        counts = importer.fetch_counts(conn)
        conn.commit()

    return {
        "source": MOCK_LOGS_SOURCE,
        "loaded_records": len(records),
        "sessions": len(grouped_records),
        "counts": counts,
    }

def import_elasticsearch_logs(request: ImportElasticsearchLogsRequest) -> dict[str, Any]:
    index = request.index or settings.demo_log_index
    start_time = request.start_time
    if request.new_only and start_time is None:
        start_time = _latest_imported_log_timestamp(index)
    start_exclusive = request.new_only and request.start_time is None and start_time is not None

    hits = elasticsearch_client.search_logs(
        index=index,
        start_time=start_time,
        end_time=request.end_time,
        limit=request.limit,
        page_size=request.page_size,
        start_exclusive=start_exclusive,
    )
    records = [_normalize_elasticsearch_hit(hit, index=index) for hit in hits]
    grouped_records = _group_normalized_records(records)

    with connection.connect() as conn:
        session_ids = _upsert_elasticsearch_sessions(conn, grouped_records, index=index)
        _upsert_elasticsearch_logs(conn, records, session_ids, index=index)
        counts = _fetch_ingestion_counts(conn)
        conn.commit()

    return {
        "source": "elasticsearch",
        "index": index,
        "loaded_records": len(hits),
        "imported_logs": len(records),
        "sessions": len(grouped_records),
        "counts": counts,
        "limit": request.limit,
        "page_size": request.page_size,
        "new_only": request.new_only,
    }


def import_shoplite_logs_from_jsonl() -> dict[str, Any]:
    source_path = _resolve_shoplite_log_path()
    raw_records = _load_jsonl_records(source_path)
    records = [_normalize_shoplite_log(record, source_path=source_path) for record in raw_records]
    grouped_records = _group_normalized_records(records)

    with connection.connect() as conn:
        session_ids = _upsert_elasticsearch_sessions(
            conn,
            grouped_records,
            index=source_path.name,
            source=SHOPLITE_LOG_SOURCE,
        )
        _upsert_elasticsearch_logs(conn, records, session_ids, index=source_path.name)
        counts = _fetch_ingestion_counts(conn)
        conn.commit()

    return {
        "source": SHOPLITE_LOG_SOURCE,
        "path": str(source_path),
        "loaded_records": len(raw_records),
        "imported_logs": len(records),
        "sessions": len(grouped_records),
        "counts": counts,
    }

def list_logs(*, limit: int, offset: int, filters: LogFilters) -> dict[str, Any]:
    where_sql, where_params = _build_log_filters(filters)

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM logs
        LEFT JOIN sessions ON sessions.id = logs.session_id
        {where_sql}
    """
    list_sql = f"""
        SELECT
            logs.id,
            logs.external_log_id,
            sessions.external_session_id AS session_external_id,
            logs.trace_id,
            logs.user_id,
            logs.service_name,
            logs.level,
            logs.method,
            logs.endpoint,
            logs.status_code,
            logs.action_type,
            logs.request_payload,
            logs.response_body,
            logs.raw_log,
            logs.response_time_ms,
            logs.occurred_at
        FROM logs
        LEFT JOIN sessions ON sessions.id = logs.session_id
        {where_sql}
        ORDER BY logs.occurred_at DESC
        LIMIT %s OFFSET %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(count_sql, where_params)
            total = int(cur.fetchone()["total"])

            cur.execute(list_sql, [*where_params, limit, offset])
            rows = cur.fetchall()

    return {
        "items": [_serialize_log_row(row) for row in rows],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def list_sessions(*, limit: int, offset: int, filters: SessionFilters) -> dict[str, Any]:
    where_sql, where_params = _build_session_filters(filters)

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM sessions
        {where_sql}
    """
    list_sql = f"""
        SELECT
            sessions.id,
            sessions.external_session_id,
            sessions.user_id,
            sessions.started_at,
            sessions.ended_at,
            sessions.request_count,
            sessions.source,
            sessions.created_at,
            COUNT(logs.id)::int AS log_count,
            COALESCE(
                array_agg(DISTINCT logs.service_name) FILTER (WHERE logs.service_name IS NOT NULL),
                ARRAY[]::text[]
            ) AS services
        FROM sessions
        LEFT JOIN logs ON logs.session_id = sessions.id
        {where_sql}
        GROUP BY
            sessions.id,
            sessions.external_session_id,
            sessions.user_id,
            sessions.started_at,
            sessions.ended_at,
            sessions.request_count,
            sessions.source,
            sessions.created_at
        ORDER BY sessions.started_at DESC NULLS LAST, sessions.created_at DESC
        LIMIT %s OFFSET %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(count_sql, where_params)
            total = int(cur.fetchone()["total"])

            cur.execute(list_sql, [*where_params, limit, offset])
            rows = cur.fetchall()

    return {
        "items": [_serialize_session_summary_row(row) for row in rows],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def get_session_detail(external_session_id: str) -> dict[str, Any]:
    session_sql = """
        SELECT
            sessions.id,
            sessions.external_session_id,
            sessions.user_id,
            sessions.started_at,
            sessions.ended_at,
            sessions.request_count,
            sessions.source,
            sessions.metadata,
            sessions.created_at,
            COUNT(logs.id)::int AS log_count
        FROM sessions
        LEFT JOIN logs ON logs.session_id = sessions.id
        WHERE sessions.external_session_id = %s
        GROUP BY
            sessions.id,
            sessions.external_session_id,
            sessions.user_id,
            sessions.started_at,
            sessions.ended_at,
            sessions.request_count,
            sessions.source,
            sessions.metadata,
            sessions.created_at
    """
    logs_sql = """
        SELECT
            logs.id,
            logs.external_log_id,
            logs.trace_id,
            logs.user_id,
            logs.service_name,
            logs.level,
            logs.method,
            logs.endpoint,
            logs.status_code,
            logs.response_time_ms,
            logs.occurred_at
        FROM logs
        WHERE logs.session_id = %s
        ORDER BY logs.occurred_at ASC
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(session_sql, [external_session_id])
            session_row = cur.fetchone()
            if session_row is None:
                raise SessionNotFoundError(external_session_id)

            cur.execute(logs_sql, [session_row["id"]])
            log_rows = cur.fetchall()

    return {
        "session": _serialize_session_detail_row(session_row),
        "logs": [_serialize_session_detail_log_row(row) for row in log_rows],
    }


def _normalize_elasticsearch_hit(hit: dict[str, Any], *, index: str) -> dict[str, Any]:
    source = hit.get("_source") or {}
    if not isinstance(source, dict):
        source = {}

    masked_source = mask_sensitive(source)
    timestamp = str(masked_source.get("timestamp") or datetime.now(timezone.utc).isoformat())
    response_status = masked_source.get("response_status", masked_source.get("status_code"))
    endpoint = masked_source.get("endpoint")
    external_log_id = _build_external_log_id(hit=hit, source=masked_source, index=index)

    return {
        "external_log_id": external_log_id,
        "timestamp": timestamp,
        "level": masked_source.get("level") or ("error" if _as_int(response_status, 0) >= 500 else "info"),
        "service_name": masked_source.get("service_name") or "demo-ecommerce",
        "trace_id": masked_source.get("trace_id"),
        "session_id": masked_source.get("session_id") or "unknown-session",
        "request_id": masked_source.get("request_id"),
        "user_id": masked_source.get("user_id"),
        "method": masked_source.get("method"),
        "endpoint": endpoint,
        "normalized_endpoint": normalize_endpoint(endpoint),
        "request_headers": masked_source.get("request_headers") or {},
        "request_payload": masked_source.get("request_payload") or {},
        "response_status": _as_int(response_status, None),
        "response_body": masked_source.get("response_body") or {},
        "response_time_ms": _as_int(masked_source.get("response_time_ms"), None),
        "environment": masked_source.get("environment"),
        "source_index": index,
        "raw_log": {
            **masked_source,
            "_elasticsearch": {
                "id": hit.get("_id"),
                "index": hit.get("_index") or index,
            },
        },
    }

def _resolve_shoplite_log_path() -> Path:
    configured = settings.shoplite_log_path
    path = Path(configured).expanduser() if configured else DEFAULT_SHOPLITE_LOG_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    if not path.exists():
        raise ShopLiteLogFileNotFoundError(str(path))
    return path

def _load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Invalid JSONL object at {path}:{line_number}")
            records.append(record)
    return records

def _normalize_shoplite_log(record: dict[str, Any], *, source_path: Path) -> dict[str, Any]:
    masked_record = mask_sensitive(record)
    timestamp = str(masked_record.get("timestamp") or datetime.now(timezone.utc).isoformat())
    response_status = masked_record.get("response_status", masked_record.get("status_code"))
    endpoint = masked_record.get("endpoint")
    request_body = masked_record.get("request_body", masked_record.get("request_payload"))
    service_name = masked_record.get("service_name") or masked_record.get("service") or "shoplite-api"
    external_log_id = _build_external_log_id(
        hit={},
        source={
            "external_log_id": masked_record.get("external_log_id"),
            "timestamp": timestamp,
            "session_id": masked_record.get("session_id"),
            "request_id": masked_record.get("request_id"),
            "method": masked_record.get("method"),
            "endpoint": endpoint,
            "response_status": response_status,
        },
        index=SHOPLITE_LOG_SOURCE,
    )

    return {
        "external_log_id": external_log_id,
        "timestamp": timestamp,
        "level": masked_record.get("level") or ("error" if _as_int(response_status, 0) >= 500 else "info"),
        "service_name": service_name,
        "trace_id": masked_record.get("trace_id"),
        "session_id": masked_record.get("session_id") or "unknown-session",
        "request_id": masked_record.get("request_id"),
        "user_id": masked_record.get("user_id"),
        "method": masked_record.get("method"),
        "endpoint": endpoint,
        "normalized_endpoint": normalize_endpoint(endpoint),
        "request_headers": masked_record.get("request_headers") or {},
        "request_payload": request_body or {},
        "response_status": _as_int(response_status, None),
        "response_body": masked_record.get("response_body") or {},
        "response_time_ms": _as_int(masked_record.get("response_time_ms"), None),
        "environment": masked_record.get("environment"),
        "source_index": source_path.name,
        "raw_log": {
            **masked_record,
            "_shoplite": {
                "path": str(source_path),
            },
        },
    }

def _build_external_log_id(*, hit: dict[str, Any], source: dict[str, Any], index: str) -> str:
    external_log_id = source.get("external_log_id")
    if external_log_id:
        return str(external_log_id)

    hit_id = hit.get("_id")
    if hit_id:
        return f"es:{index}:{hit_id}"

    fingerprint_source = {
        "timestamp": source.get("timestamp"),
        "session_id": source.get("session_id"),
        "request_id": source.get("request_id"),
        "method": source.get("method"),
        "endpoint": source.get("endpoint"),
    }
    fingerprint = hashlib.sha256(repr(sorted(fingerprint_source.items())).encode("utf-8")).hexdigest()
    return f"es:{index}:{fingerprint[:24]}"

def _group_normalized_records(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sessions = group_logs_by_session(records)
    return {session_id: sort_logs_by_timestamp(session_records) for session_id, session_records in sessions.items()}

def _upsert_elasticsearch_sessions(
    conn: psycopg.Connection,
    grouped_records: dict[str, list[dict[str, Any]]],
    *,
    index: str,
    source: str = "elasticsearch",
) -> dict[str, str]:
    session_ids: dict[str, str] = {}

    with conn.cursor() as cur:
        for external_session_id, records in grouped_records.items():
            timestamps = [parse_timestamp(record["timestamp"]) for record in records]
            user_ids = [record.get("user_id") for record in records if record.get("user_id")]
            user_id = user_ids[0] if user_ids else None
            metadata = {
                "source_index": index,
                "services": sorted({record["service_name"] for record in records}),
            }

            cur.execute(
                """
                INSERT INTO sessions (
                    external_session_id,
                    user_id,
                    started_at,
                    ended_at,
                    request_count,
                    source,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_session_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    started_at = EXCLUDED.started_at,
                    ended_at = EXCLUDED.ended_at,
                    request_count = EXCLUDED.request_count,
                    source = EXCLUDED.source,
                    metadata = EXCLUDED.metadata
                RETURNING id
                """,
                (
                    external_session_id,
                    user_id,
                    min(timestamps),
                    max(timestamps),
                    len(records),
                    source,
                    Jsonb(metadata),
                ),
            )
            session_ids[external_session_id] = str(cur.fetchone()[0])

    return session_ids

def _upsert_elasticsearch_logs(
    conn: psycopg.Connection,
    records: list[dict[str, Any]],
    session_ids: dict[str, str],
    *,
    index: str,
) -> None:
    with conn.cursor() as cur:
        for record in records:
            cur.execute(
                """
                INSERT INTO logs (
                    session_id,
                    external_log_id,
                    trace_id,
                    request_id,
                    user_id,
                    service_name,
                    level,
                    method,
                    endpoint,
                    normalized_endpoint,
                    status_code,
                    request_headers,
                    request_payload,
                    response_body,
                    response_time_ms,
                    environment,
                    source_index,
                    action_type,
                    raw_log,
                    occurred_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_log_id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    trace_id = EXCLUDED.trace_id,
                    request_id = EXCLUDED.request_id,
                    user_id = EXCLUDED.user_id,
                    service_name = EXCLUDED.service_name,
                    level = EXCLUDED.level,
                    method = EXCLUDED.method,
                    endpoint = EXCLUDED.endpoint,
                    normalized_endpoint = EXCLUDED.normalized_endpoint,
                    status_code = EXCLUDED.status_code,
                    request_headers = EXCLUDED.request_headers,
                    request_payload = EXCLUDED.request_payload,
                    response_body = EXCLUDED.response_body,
                    response_time_ms = EXCLUDED.response_time_ms,
                    environment = EXCLUDED.environment,
                    source_index = EXCLUDED.source_index,
                    action_type = EXCLUDED.action_type,
                    raw_log = EXCLUDED.raw_log,
                    occurred_at = EXCLUDED.occurred_at
                """,
                (
                    session_ids[record["session_id"]],
                    record["external_log_id"],
                    record["trace_id"],
                    record["request_id"],
                    record["user_id"],
                    record["service_name"],
                    record["level"],
                    record["method"],
                    record["endpoint"],
                    record["normalized_endpoint"],
                    record["response_status"],
                    Jsonb(record["request_headers"]),
                    Jsonb(record["request_payload"]),
                    Jsonb(record["response_body"]),
                    record["response_time_ms"],
                    record["environment"],
                    index,
                    classify_action(record).action_type,
                    Jsonb(record["raw_log"]),
                    parse_timestamp(record["timestamp"]),
                ),
            )

def mask_sensitive(value: Any) -> Any:
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]

    if isinstance(value, dict):
        return {
            key: "***MASKED***" if key.lower() in SENSITIVE_KEYS else mask_sensitive(entry_value)
            for key, entry_value in value.items()
        }

    return value

def normalize_endpoint(endpoint: Any) -> str | None:
    if not endpoint:
        return None

    path = str(endpoint).split("?", 1)[0]
    segments = []
    for segment in path.split("/"):
        if _looks_dynamic_path_segment(segment):
            segments.append(":id")
        else:
            segments.append(segment)
    return "/".join(segments)

def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed

def _looks_dynamic_path_segment(segment: str) -> bool:
    if not segment:
        return False
    return bool(
        re.fullmatch(r"[0-9a-f]{8,}(-[0-9a-f]{4,})*", segment)
        or re.fullmatch(r"(order|prod|cart|pay|user)-[a-z0-9-]+", segment)
    )

def _as_int(value: Any, default: int | None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _fetch_ingestion_counts(conn: psycopg.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in ["sessions", "logs"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = int(cur.fetchone()[0])
    return counts

def _latest_imported_log_timestamp(index: str) -> datetime | None:
    with connection.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(occurred_at) FROM logs WHERE source_index = %s", [index])
            return cur.fetchone()[0]

def _build_log_filters(filters: LogFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if filters.session_id:
        clauses.append("sessions.external_session_id = %s")
        params.append(filters.session_id)
    if filters.trace_id:
        clauses.append("logs.trace_id = %s")
        params.append(filters.trace_id)
    if filters.endpoint:
        clauses.append("logs.endpoint ILIKE %s")
        params.append(f"%{filters.endpoint}%")
    if filters.level:
        clauses.append("logs.level = %s")
        params.append(filters.level)

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


def _build_session_filters(filters: SessionFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if filters.user_id:
        clauses.append("sessions.user_id = %s")
        params.append(filters.user_id)
    if filters.source:
        clauses.append("sessions.source = %s")
        params.append(filters.source)

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


def _serialize_log_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
    }


def _serialize_session_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "services": list(row.get("services") or []),
    }


def _serialize_session_detail_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "metadata": row.get("metadata") or {},
    }


def _serialize_session_detail_log_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
    }
