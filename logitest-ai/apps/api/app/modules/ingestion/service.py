from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.db import connection
from app.modules.ingestion.schemas import LogFilters, SessionFilters

PROJECT_ROOT = Path(__file__).resolve().parents[5]
IMPORT_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "import_mock_logs.py"
MOCK_LOGS_SOURCE = "mock-data/logs.json"


class SessionNotFoundError(Exception):
    pass


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
