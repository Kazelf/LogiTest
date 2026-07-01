from app.modules.ingestion import service
from pathlib import Path


def test_normalize_elasticsearch_hit_masks_sensitive_fields_and_maps_core_fields() -> None:
    hit = {
        "_id": "es-doc-1",
        "_index": "logitest-demo-logs",
        "_source": {
            "timestamp": "2026-06-24T10:00:00.000Z",
            "level": "info",
            "service_name": "demo-ecommerce",
            "environment": "demo",
            "session_id": "session-demo-001",
            "trace_id": "trace-demo-001",
            "request_id": "req-demo-001",
            "user_id": "user-buyer-001",
            "method": "POST",
            "endpoint": "/api/auth/login",
            "request_headers": {"Authorization": "Bearer secret"},
            "request_payload": {"username": "buyer_001", "password": "password123"},
            "response_status": 200,
            "response_body": {"token": "demo-token-user-buyer-001"},
            "response_time_ms": 42,
        },
    }

    record = service._normalize_elasticsearch_hit(hit, index="logitest-demo-logs")

    assert record["external_log_id"] == "es:logitest-demo-logs:es-doc-1"
    assert record["session_id"] == "session-demo-001"
    assert record["request_id"] == "req-demo-001"
    assert record["response_status"] == 200
    assert record["normalized_endpoint"] == "/api/auth/login"
    assert record["request_headers"]["Authorization"] == "***MASKED***"
    assert record["request_payload"]["password"] == "***MASKED***"
    assert record["response_body"]["token"] == "***MASKED***"
    assert record["raw_log"]["request_payload"]["password"] == "***MASKED***"


def test_normalize_endpoint_replaces_known_dynamic_segments() -> None:
    assert service.normalize_endpoint("/api/orders/order-001?expand=items") == "/api/orders/:id"
    assert service.normalize_endpoint("/api/products/prod-headphone-001") == "/api/products/:id"
    assert service.normalize_endpoint("/health") == "/health"


def test_build_external_log_id_uses_deterministic_hash_without_es_id() -> None:
    source = {
        "timestamp": "2026-06-24T10:00:00.000Z",
        "session_id": "session-demo-001",
        "request_id": "req-demo-001",
        "method": "GET",
        "endpoint": "/health",
    }

    first = service._build_external_log_id(hit={}, source=source, index="logitest-demo-logs")
    second = service._build_external_log_id(hit={}, source=source, index="logitest-demo-logs")

    assert first == second
    assert first.startswith("es:logitest-demo-logs:")

def test_normalize_shoplite_log_maps_jsonl_fields() -> None:
    record = {
        "timestamp": "2026-07-01T15:00:00.000Z",
        "environment": "production-demo",
        "service": "shoplite-api",
        "session_id": "sess-shoplite-001",
        "trace_id": "trace-shoplite-001",
        "user_id": "user-001",
        "method": "POST",
        "endpoint": "/api/auth/login",
        "request_body": {"email": "normal_buyer@example.com", "password": "Password123"},
        "response_status": 200,
        "response_body": {"accessToken": "secret-token", "user": {"id": "user-001"}},
        "response_time_ms": 25,
    }

    normalized = service._normalize_shoplite_log(record, source_path=Path("request-logs.jsonl"))

    assert normalized["service_name"] == "shoplite-api"
    assert normalized["session_id"] == "sess-shoplite-001"
    assert normalized["normalized_endpoint"] == "/api/auth/login"
    assert normalized["request_payload"]["email"] == "***MASKED***"
    assert normalized["request_payload"]["password"] == "***MASKED***"
    assert normalized["response_body"]["accessToken"] == "***MASKED***"
    assert normalized["response_status"] == 200
    assert normalized["external_log_id"].startswith("es:shoplite_jsonl:")
