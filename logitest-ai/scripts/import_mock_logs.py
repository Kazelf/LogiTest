from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_APP_PATH = PROJECT_ROOT / "apps" / "api"
if str(API_APP_PATH) not in sys.path:
    sys.path.insert(0, str(API_APP_PATH))

from app.modules.session_reconstruction import classify_action, group_logs_by_session, sort_logs_by_timestamp

MOCK_LOGS_PATH = PROJECT_ROOT / "mock-data" / "logs.json"
DEFAULT_DATABASE_URL = "postgresql://logitest:logitest@localhost:5432/logitest_ai"

REQUIRED_LOG_KEYS = {
    "external_log_id",
    "timestamp",
    "level",
    "service_name",
    "trace_id",
    "session_id",
    "user_id",
    "method",
    "endpoint",
    "request_payload",
    "response_status",
    "response_body",
    "response_time_ms",
}


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_logs() -> list[dict[str, Any]]:
    with MOCK_LOGS_PATH.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError(f"{MOCK_LOGS_PATH} must contain a JSON array")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Log record at index {index} must be an object")

        missing_keys = REQUIRED_LOG_KEYS - record.keys()
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"Log record at index {index} is missing: {missing}")

        parse_timestamp(record["timestamp"])

        if not isinstance(record["request_payload"], dict):
            raise ValueError(f"Log record {record['external_log_id']} request_payload must be an object")
        if not isinstance(record["response_body"], dict):
            raise ValueError(f"Log record {record['external_log_id']} response_body must be an object")

    return records


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def group_by_session(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sessions = group_logs_by_session(records)
    return {session_id: sort_logs_by_timestamp(session_records) for session_id, session_records in sessions.items()}


def upsert_sessions(conn: psycopg.Connection, grouped_records: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    session_ids: dict[str, str] = {}

    with conn.cursor() as cur:
        for external_session_id, records in grouped_records.items():
            timestamps = [parse_timestamp(record["timestamp"]) for record in records]
            user_ids = [record.get("user_id") for record in records if record.get("user_id")]
            user_id = user_ids[0] if user_ids else None
            metadata = {
                "source_file": str(MOCK_LOGS_PATH.relative_to(PROJECT_ROOT)),
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
                    "mock_json",
                    Jsonb(metadata),
                ),
            )
            session_ids[external_session_id] = str(cur.fetchone()[0])

    return session_ids


def upsert_logs(conn: psycopg.Connection, records: list[dict[str, Any]], session_ids: dict[str, str]) -> None:
    with conn.cursor() as cur:
        for record in records:
            cur.execute(
                """
                INSERT INTO logs (
                    session_id,
                    external_log_id,
                    trace_id,
                    user_id,
                    service_name,
                    level,
                    method,
                    endpoint,
                    status_code,
                    request_payload,
                    response_body,
                    response_time_ms,
                    action_type,
                    raw_log,
                    occurred_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_log_id) DO UPDATE SET
                    session_id = EXCLUDED.session_id,
                    trace_id = EXCLUDED.trace_id,
                    user_id = EXCLUDED.user_id,
                    service_name = EXCLUDED.service_name,
                    level = EXCLUDED.level,
                    method = EXCLUDED.method,
                    endpoint = EXCLUDED.endpoint,
                    status_code = EXCLUDED.status_code,
                    request_payload = EXCLUDED.request_payload,
                    response_body = EXCLUDED.response_body,
                    response_time_ms = EXCLUDED.response_time_ms,
                    action_type = EXCLUDED.action_type,
                    raw_log = EXCLUDED.raw_log,
                    occurred_at = EXCLUDED.occurred_at
                """,
                (
                    session_ids[record["session_id"]],
                    record["external_log_id"],
                    record["trace_id"],
                    record["user_id"],
                    record["service_name"],
                    record["level"],
                    record["method"],
                    record["endpoint"],
                    record["response_status"],
                    Jsonb(record["request_payload"]),
                    Jsonb(record["response_body"]),
                    record["response_time_ms"],
                    classify_action(record).action_type,
                    Jsonb(record),
                    parse_timestamp(record["timestamp"]),
                ),
            )


def upsert_personas(conn: psycopg.Connection) -> dict[str, str]:
    personas = [
        {
            "name": "Buyer",
            "description": "User completes product discovery, checkout, and payment successfully.",
            "confidence_score": 0.9500,
            "features": {"signals": ["checkout", "payment_success", "order_view"]},
        },
        {
            "name": "Browser",
            "description": "User searches and views products without purchasing.",
            "confidence_score": 0.9000,
            "features": {"signals": ["search", "product_view"], "excludes": ["checkout"]},
        },
        {
            "name": "Failed Payment User",
            "description": "User reaches checkout but receives a failed payment response.",
            "confidence_score": 0.9300,
            "features": {"signals": ["checkout", "payment_failed", "402"]},
        },
    ]
    persona_ids: dict[str, str] = {}

    with conn.cursor() as cur:
        for persona in personas:
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
                (
                    persona["name"],
                    persona["description"],
                    "seed_rule_based",
                    persona["confidence_score"],
                    Jsonb(persona["features"]),
                ),
            )
            persona_ids[persona["name"]] = str(cur.fetchone()[0])

    return persona_ids


def build_steps(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "order": index + 1,
            "method": record["method"],
            "endpoint": record["endpoint"],
            "service_name": record["service_name"],
            "expected_status": record["response_status"],
            "request_payload": record["request_payload"],
            "golden_response": record["response_body"],
        }
        for index, record in enumerate(records)
    ]


def upsert_journeys(
    conn: psycopg.Connection,
    grouped_records: dict[str, list[dict[str, Any]]],
    session_ids: dict[str, str],
    persona_ids: dict[str, str],
) -> dict[str, str]:
    journey_specs = [
        {
            "name": "Successful buyer checkout",
            "description": "Buyer logs in, finds a product, checks out, pays, and views the paid order.",
            "persona": "Buyer",
            "session": "session-buyer-001",
            "frequency_score": 0.7200,
            "risk_score": 0.6200,
        },
        {
            "name": "Product browsing without purchase",
            "description": "Browser logs in, searches products, and views product details without checkout.",
            "persona": "Browser",
            "session": "session-browser-001",
            "frequency_score": 0.6500,
            "risk_score": 0.2500,
        },
        {
            "name": "Checkout with failed payment",
            "description": "User checks out but receives a declined payment response.",
            "persona": "Failed Payment User",
            "session": "session-failed-payment-001",
            "frequency_score": 0.1800,
            "risk_score": 0.9000,
        },
    ]
    journey_ids: dict[str, str] = {}

    with conn.cursor() as cur:
        for journey in journey_specs:
            records = grouped_records[journey["session"]]
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
                    persona_ids[journey["persona"]],
                    journey["name"],
                    journey["description"],
                    1,
                    journey["frequency_score"],
                    journey["risk_score"],
                    Jsonb(build_steps(records)),
                    session_ids[journey["session"]],
                ),
            )
            journey_ids[journey["name"]] = str(cur.fetchone()[0])

    return journey_ids


def upsert_test_cases(
    conn: psycopg.Connection,
    grouped_records: dict[str, list[dict[str, Any]]],
    persona_ids: dict[str, str],
    journey_ids: dict[str, str],
) -> None:
    test_case_specs = [
        {
            "name": "API test - successful buyer checkout",
            "description": "Replays the successful buyer checkout flow and validates golden responses.",
            "journey": "Successful buyer checkout",
            "persona": "Buyer",
            "session": "session-buyer-001",
        },
        {
            "name": "API test - product browsing without purchase",
            "description": "Replays a browsing-only flow and verifies product response schemas.",
            "journey": "Product browsing without purchase",
            "persona": "Browser",
            "session": "session-browser-001",
        },
        {
            "name": "API test - checkout with failed payment",
            "description": "Replays a checkout flow that should preserve the payment decline behavior.",
            "journey": "Checkout with failed payment",
            "persona": "Failed Payment User",
            "session": "session-failed-payment-001",
        },
    ]

    with conn.cursor() as cur:
        for spec in test_case_specs:
            records = grouped_records[spec["session"]]
            steps = build_steps(records)
            assertions = [
                {
                    "order": step["order"],
                    "type": "status_code",
                    "expected": step["expected_status"],
                }
                for step in steps
            ]
            golden_response = {
                "final_status_code": records[-1]["response_status"],
                "final_response_body": records[-1]["response_body"],
                "step_count": len(records),
            }
            generated_code = build_generated_code_stub(spec["name"], steps)

            cur.execute(
                """
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
                """,
                (
                    journey_ids[spec["journey"]],
                    persona_ids[spec["persona"]],
                    spec["name"],
                    spec["description"],
                    "api",
                    "generated",
                    Jsonb(steps),
                    Jsonb(assertions),
                    Jsonb(golden_response),
                    generated_code,
                    "mock_import_script",
                ),
            )


def build_generated_code_stub(name: str, steps: list[dict[str, Any]]) -> str:
    slug = name.lower().replace(" - ", "_").replace(" ", "_")
    lines = [f"def test_{slug}(api_client):", f"    # Generated from {len(steps)} mock log steps."]
    for step in steps:
        lines.append(
            f"    # {step['order']}. {step['method']} {step['endpoint']} -> {step['expected_status']}"
        )
    lines.append("    assert True")
    return "\n".join(lines)


def fetch_counts(conn: psycopg.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in ["sessions", "logs", "personas", "journeys", "test_cases"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = int(cur.fetchone()[0])
    return counts


def main() -> None:
    records = load_logs()
    grouped_records = group_by_session(records)

    with psycopg.connect(get_database_url()) as conn:
        session_ids = upsert_sessions(conn, grouped_records)
        upsert_logs(conn, records, session_ids)
        persona_ids = upsert_personas(conn)
        journey_ids = upsert_journeys(conn, grouped_records, session_ids, persona_ids)
        upsert_test_cases(conn, grouped_records, persona_ids, journey_ids)
        counts = fetch_counts(conn)
        conn.commit()

    print("Mock data import completed.")
    print(f"Loaded records: {len(records)} logs across {len(grouped_records)} sessions.")
    for table, count in counts.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
