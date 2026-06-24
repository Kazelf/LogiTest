from app.modules.test_generation import service
from app.modules.test_generation.schemas import GeneratedTestCaseFilters, GeneratedTestFramework


def test_build_test_case_draft_uses_logs_as_replay_source() -> None:
    journey = _journey()
    logs = [
        _log("POST", "/auth/login", 200, {"email": "user@example.com"}, {"token": "abc"}, "login"),
        _log("POST", "/payments", 201, {"order_id": "order-001"}, {"status": "paid"}, "payment_success"),
    ]

    draft = service._build_test_case_draft(journey, logs)

    assert draft["name"] == "API test - Successful buyer checkout"
    assert draft["journey_id"] == "journey-id"
    assert draft["persona_id"] == "persona-id"
    assert draft["steps"][0] == {
        "order": 1,
        "action_type": "login",
        "service_name": "auth-service",
        "method": "POST",
        "endpoint": "/auth/login",
        "request_payload": {"email": "user@example.com"},
        "expected_status": 200,
        "golden_response": {"token": "abc"},
        "response_time_ms": 80,
    }
    assert {"order": 1, "type": "status_code", "expected": 200} in draft["assertions"]
    assert {
        "order": 2,
        "type": "response_schema",
        "expected": {"type": "object", "required": ["status"]},
    } in draft["assertions"]
    assert draft["golden_response"] == {
        "step_count": 2,
        "final_status_code": 201,
        "final_response_body": {"status": "paid"},
        "source": {"journey_id": "journey-id", "example_session_id": "session-id"},
    }
    assert "def test_api_test_successful_buyer_checkout" in draft["generated_code"]


def test_build_test_case_filters_uses_parameterized_conditions() -> None:
    where_sql, params = service._build_test_case_filters(
        GeneratedTestCaseFilters(journey_id="journey-id' OR 1=1 --", status="generated")
    )

    assert where_sql == "WHERE test_cases.journey_id = %s AND test_cases.status = %s"
    assert params == ["journey-id' OR 1=1 --", "generated"]


def test_serialize_rows_normalizes_ids_and_json_defaults() -> None:
    list_row = service._serialize_test_case_list_row(
        {
            "id": "test-case-id",
            "journey_id": None,
            "persona_id": "persona-id",
            "journey_name": None,
            "persona_name": "Buyer",
            "name": "API test - Buyer",
            "description": None,
            "type": "api",
            "status": "generated",
            "step_count": None,
            "generated_by": "test_generation_service",
            "created_at": "created",
            "updated_at": "updated",
        }
    )
    detail_row = service._serialize_test_case_detail_row(
        {
            **list_row,
            "steps": None,
            "assertions": None,
            "golden_response": None,
            "generated_code": None,
        }
    )

    assert list_row["id"] == "test-case-id"
    assert list_row["journey_id"] is None
    assert list_row["persona_id"] == "persona-id"
    assert list_row["step_count"] == 0
    assert detail_row["steps"] == []
    assert detail_row["assertions"] == []
    assert detail_row["golden_response"] == {}


def test_generate_test_case_persists_generated_draft(monkeypatch) -> None:
    fake_connection = FakeConnection()
    monkeypatch.setattr(service.connection, "connect", lambda: fake_connection)

    result = service.generate_test_case(journey_id="journey-id", overwrite=True)

    assert result == {
        "test_case_id": "test-case-id",
        "journey_id": "journey-id",
        "name": "API test - Successful buyer checkout",
        "status": "generated",
        "step_count": 1,
        "artifacts": [
            {
                "id": "artifact-id",
                "framework": "playwright_api",
                "language": "typescript",
                "file_path": None,
            }
        ],
    }
    assert fake_connection.committed is True
    insert_sql, insert_params = next(
        execution for execution in fake_connection.cursor_instance.executions if "INSERT INTO test_cases" in execution[0]
    )
    assert "INSERT INTO test_cases" in insert_sql
    assert "ON CONFLICT (name) DO UPDATE" in insert_sql
    assert insert_params[2] == "API test - Successful buyer checkout"
    assert insert_params[4] == "api"
    assert insert_params[5] == "generated"
    assert "@playwright/test" in insert_params[9]
    assert insert_params[10] == "test_generation_service"
    artifact_sql, artifact_params = fake_connection.cursor_instance.executions[-1]
    assert "INSERT INTO test_case_artifacts" in artifact_sql
    assert artifact_params[0] == "test-case-id"
    assert artifact_params[1] == "playwright_api"


def test_generate_test_case_rejects_duplicate_when_overwrite_false(monkeypatch) -> None:
    fake_connection = FakeConnection(existing_test_case=True)
    monkeypatch.setattr(service.connection, "connect", lambda: fake_connection)

    try:
        service.generate_test_case(journey_id="journey-id", overwrite=False)
    except service.TestCaseAlreadyExistsError:
        pass
    else:
        raise AssertionError("Expected duplicate generation to fail")

    assert fake_connection.committed is False


def test_normalize_frameworks_removes_duplicates_and_preserves_order() -> None:
    frameworks = service._normalize_frameworks(
        [
            GeneratedTestFramework.JEST_SUPERTEST,
            GeneratedTestFramework.PLAYWRIGHT_API,
            GeneratedTestFramework.JEST_SUPERTEST,
        ]
    )

    assert frameworks == [GeneratedTestFramework.JEST_SUPERTEST, GeneratedTestFramework.PLAYWRIGHT_API]


def _journey() -> dict:
    return {
        "id": "journey-id",
        "persona_id": "persona-id",
        "persona_name": "Buyer",
        "name": "Journey: Successful buyer checkout",
        "description": "Buyer flow",
        "example_session_id": "session-id",
    }


def _log(method: str, endpoint: str, status_code: int, request_payload: dict, response_body: dict, action_type: str) -> dict:
    return {
        "service_name": "auth-service",
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "request_payload": request_payload,
        "response_body": response_body,
        "response_time_ms": 80,
        "action_type": action_type,
    }


class FakeConnection:
    def __init__(self, *, existing_test_case: bool = False) -> None:
        self.cursor_instance = FakeCursor(existing_test_case=existing_test_case)
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self, row_factory=None):
        return self.cursor_instance

    def commit(self) -> None:
        self.committed = True


class FakeCursor:
    def __init__(self, *, existing_test_case: bool) -> None:
        self.existing_test_case = existing_test_case
        self.executions: list[tuple[str, object]] = []
        self.last_sql = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str, params: object) -> None:
        self.last_sql = sql
        self.executions.append((sql, params))

    def fetchone(self) -> dict | None:
        if "FROM journeys" in self.last_sql:
            return _journey()
        if "FROM test_cases WHERE name" in self.last_sql:
            return {"id": "existing-test-case-id"} if self.existing_test_case else None
        if "INSERT INTO test_cases" in self.last_sql:
            return {"id": "test-case-id"}
        if "INSERT INTO test_case_artifacts" in self.last_sql:
            return {
                "id": "artifact-id",
                "framework": "playwright_api",
                "language": "typescript",
                "file_path": None,
            }
        raise AssertionError(f"Unexpected fetchone SQL: {self.last_sql}")

    def fetchall(self) -> list[dict]:
        if "FROM logs" in self.last_sql:
            return [_log("POST", "/auth/login", 200, {"email": "user@example.com"}, {"token": "abc"}, "login")]
        raise AssertionError(f"Unexpected fetchall SQL: {self.last_sql}")
