import httpx

from app.modules.execution import service


def test_run_test_case_replays_steps_extracts_variables_and_persists_pass(monkeypatch) -> None:
    fake_connection = FakeConnection(
        test_case={
            "id": "test-case-id",
            "name": "API test - order",
            "steps": [
                {
                    "order": 1,
                    "method": "POST",
                    "endpoint": "/api/orders",
                    "request_payload": {},
                    "expected_status": 201,
                    "golden_response": {"data": {"orderId": "order-old", "status": "created"}},
                    "extract": {"orderId": "response.body.data.orderId"},
                },
                {
                    "order": 2,
                    "method": "GET",
                    "endpoint": "/api/orders/order-old",
                    "request_payload": {},
                    "expected_status": 200,
                    "golden_response": {"data": {"orderId": "order-old", "status": "created"}},
                    "uses": {"orderId": "path"},
                },
            ],
            "assertions": [],
        }
    )
    fake_client = FakeHttpClient(
        [
            httpx.Response(201, json={"data": {"orderId": "order-new", "status": "created"}}),
            httpx.Response(200, json={"data": {"orderId": "order-new", "status": "created"}}),
        ]
    )
    monkeypatch.setattr(service.connection, "connect", lambda: fake_connection)
    monkeypatch.setattr(service.httpx, "Client", lambda timeout: fake_client)

    run = service.run_test_case("test-case-id", target_base_url="http://demo.local", timeout_seconds=3)

    assert run["status"] == "passed"
    assert fake_connection.committed is True
    assert fake_client.requests[0] == ("POST", "http://demo.local/api/orders", {})
    assert fake_client.requests[1] == ("GET", "http://demo.local/api/orders/order-new", None)
    insert_sql, insert_params = fake_connection.cursor_instance.insert_execution
    assert "INSERT INTO test_runs" in insert_sql
    assert insert_params[1] == "passed"
    assert insert_params[6].obj["steps"][1]["resolved_endpoint"] == "/api/orders/order-new"


def test_compare_results_reports_regression_business_field_diff() -> None:
    diff = service._compare_results(
        [
            {
                "order": 1,
                "expected_status": 200,
                "golden_response": {"data": {"orderId": "order-001", "status": "created"}},
            }
        ],
        [],
        [
            {
                "order": 1,
                "status_code": 200,
                "duration_ms": 30,
                "response_body": {"data": {"orderId": "order-999", "status": "pending"}},
            }
        ],
    )

    assert diff["differences"] == [
        {"order": 1, "type": "business_field", "expected": {"path": "body.data.status", "value": "created"}, "actual": "pending"}
    ]
    assert diff["summary"]["failed"] == 1


def test_replace_request_body_uses_matches_camel_and_snake_keys() -> None:
    replaced = service._replace_request_body_uses(
        {"order_id": "order-old", "nested": {"paymentId": "payment-old"}},
        {"orderId": "request.body", "payment_id": "request.body"},
        {"orderId": "order-new", "payment_id": "payment-new"},
    )

    assert replaced == {"order_id": "order-new", "nested": {"paymentId": "payment-new"}}


def test_run_test_case_raises_not_found_without_persisting(monkeypatch) -> None:
    fake_connection = FakeConnection(test_case=None)
    monkeypatch.setattr(service.connection, "connect", lambda: fake_connection)

    try:
        service.run_test_case("missing")
    except service.TestCaseNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing test case to fail")

    assert fake_connection.committed is False


def test_list_and_get_runs_serialize_rows(monkeypatch) -> None:
    fake_connection = FakeConnection(test_case={"id": "test-case-id", "name": "case", "steps": [{}], "assertions": []})
    monkeypatch.setattr(service.connection, "connect", lambda: fake_connection)

    listed = service.list_test_case_runs("test-case-id", limit=5, offset=0)
    detail = service.get_test_run("run-id")

    assert listed["total"] == 1
    assert listed["items"][0]["id"] == "run-id"
    assert detail["test_case_id"] == "test-case-id"


class FakeHttpClient:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, str, dict | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def request(self, method: str, url: str, json: dict | None = None) -> httpx.Response:
        self.requests.append((method, url, json))
        return self.responses.pop(0)


class FakeConnection:
    def __init__(self, *, test_case: dict | None) -> None:
        self.cursor_instance = FakeCursor(test_case)
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
    def __init__(self, test_case: dict | None) -> None:
        self.test_case = test_case
        self.executions: list[tuple[str, object]] = []
        self.insert_execution: tuple[str, tuple] | None = None
        self.last_sql = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str, params: object) -> None:
        self.last_sql = sql
        self.executions.append((sql, params))
        if "INSERT INTO test_runs" in sql:
            self.insert_execution = (sql, params)

    def fetchone(self) -> dict | None:
        if "FROM test_cases" in self.last_sql:
            return self.test_case
        if "COUNT(*) AS total" in self.last_sql:
            return {"total": 1}
        if "FROM test_runs" in self.last_sql or "INSERT INTO test_runs" in self.last_sql:
            return _run_row()
        return None

    def fetchall(self) -> list[dict]:
        if "FROM test_runs" in self.last_sql:
            return [_run_row()]
        return []


def _run_row() -> dict:
    return {
        "id": "run-id",
        "test_case_id": "test-case-id",
        "status": "passed",
        "target_environment": "staging",
        "started_at": "started",
        "finished_at": "finished",
        "duration_ms": 10,
        "actual_response": {"steps": []},
        "diff_result": {"differences": []},
        "error_message": None,
        "runner_metadata": {"runner": "test"},
        "created_at": "created",
    }
