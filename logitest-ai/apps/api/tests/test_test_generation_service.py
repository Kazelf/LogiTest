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
                "framework": "jest_supertest",
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
    assert 'import request from "supertest";' in insert_params[9]
    assert insert_params[10] == "test_generation_service"
    artifact_sql, artifact_params = fake_connection.cursor_instance.executions[-1]
    assert "INSERT INTO test_case_artifacts" in artifact_sql
    assert artifact_params[0] == "test-case-id"
    assert artifact_params[1] == "jest_supertest"


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


def test_normalize_frameworks_defaults_to_jest_supertest() -> None:
    assert service._normalize_frameworks(None) == [GeneratedTestFramework.JEST_SUPERTEST]

def test_build_test_case_draft_merges_journey_chaining_metadata() -> None:
    journey = {
        **_journey(),
        "steps": [
            {"order": 1, "extract": {"orderId": "response.body.data.orderId"}, "type": "ORDER_CREATION_FLOW"},
            {"order": 2, "uses": {"orderId": "path"}, "type": "ORDER_CREATION_FLOW"},
        ],
    }
    logs = [
        _log("POST", "/api/orders", 201, {}, {"data": {"orderId": "order-001", "status": "created"}}, "checkout"),
        _log("GET", "/api/orders/order-001", 200, {}, {"data": {"orderId": "order-001", "status": "created"}}, "view_order"),
    ]

    draft = service._build_test_case_draft(journey, logs)

    assert draft["steps"][0]["extract"] == {"orderId": "response.body.data.orderId"}
    assert draft["steps"][1]["uses"] == {"orderId": "path"}
    assert {"order": 1, "type": "business_field", "expected": {"path": "body.data.status", "value": "created"}} in draft["assertions"]
    assert {"order": 1, "type": "response_time_ms", "expected": {"max_ms": 1000}} in draft["assertions"]

def test_build_test_case_draft_replays_journey_steps_not_noisy_session_history() -> None:
    journey = {
        **_journey(),
        "steps": [
            {"order": 1, "action_type": "login"},
            {"order": 2, "action_type": "add_to_cart"},
            {"order": 3, "action_type": "checkout", "extract": {"orderId": "response.body.orderId"}},
            {"order": 4, "action_type": "view_order", "uses": {"orderId": "path"}},
        ],
    }
    logs = [
        _log("POST", "/api/auth/login", 200, {"email": "user@example.com"}, {"token": "abc"}, "login"),
        _log("GET", "/api/products", 200, {}, {"result_count": 7}, "search_product"),
        _log("GET", "/api/products", 200, {}, {"result_count": 7}, "search_product"),
        _log("POST", "/api/cart/items", 201, {"product_id": "product-1"}, {"cart_item_id": "item-1"}, "add_to_cart"),
        _log("GET", "/api/products/product-1", 200, {}, {"product_id": "product-1"}, "view_product"),
        _log("POST", "/api/orders", 201, {}, {"orderId": "order-001", "status": "created"}, "checkout"),
        _log("GET", "/api/products", 304, {}, {}, "search_product"),
        _log("GET", "/api/orders/order-001", 200, {}, {"orderId": "order-001", "status": "created"}, "view_order"),
    ]

    draft = service._build_test_case_draft(journey, logs)

    assert [step["action_type"] for step in draft["steps"]] == ["login", "add_to_cart", "checkout", "view_order"]
    assert draft["steps"][2]["extract"] == {"orderId": "response.body.orderId"}
    assert draft["steps"][3]["uses"] == {"orderId": "path"}
    assert draft["golden_response"]["step_count"] == 4
    assert draft["golden_response"]["final_status_code"] == 200

def test_build_test_case_draft_makes_payment_flow_self_contained() -> None:
    journey = {
        **_journey(),
        "steps": [
            {"order": 1, "action_type": "search_product"},
            {"order": 2, "action_type": "add_to_cart"},
            {"order": 3, "action_type": "login"},
            {"order": 4, "action_type": "checkout"},
            {"order": 5, "action_type": "payment_success"},
            {"order": 6, "action_type": "view_order"},
        ],
    }
    checkout_body = {
        "checkout_ready": True,
        "cart": {
            "cart_id": "cart-1",
            "user_id": "user-1",
            "voucher_code": None,
            "items": [
                {
                    "cart_item_id": "cart-item-1",
                    "product_id": "product-1",
                    "name": "Dell Inspiron 15",
                    "brand": "Dell",
                    "price": 15000000,
                    "stock": 12,
                    "quantity": 1,
                    "line_total": 15000000,
                }
            ],
            "subtotal_amount": 15000000,
            "discount_amount": 0,
            "total_amount": 15000000,
        },
        "subtotal_amount": 15000000,
        "discount_amount": 0,
        "total_amount": 15000000,
        "shipping_address": "456 Browse Avenue",
    }
    logs = [
        _log("GET", "/api/products", 200, {}, {"result_count": 7}, "search_product"),
        _log("POST", "/api/cart/items", 401, {"product_id": "product-1", "quantity": 1}, {"message": "Missing bearer token"}, "add_to_cart"),
        _log("POST", "/api/auth/login", 200, {"email": "browser_user@example.com"}, {"accessToken": "token", "user": {"name": "Product Browser"}}, "login"),
        _log("POST", "/api/checkout", 200, {}, checkout_body, "checkout"),
        _log("POST", "/api/payments/simulate-success", 200, {"order_id": "old-order-id"}, {"payment_status": "SUCCESS"}, "payment_success"),
        _log("GET", "/api/orders/:id", 200, {}, {"order_status": "PAID"}, "view_order"),
    ]

    draft = service._build_test_case_draft(journey, logs)

    action_types = [step["action_type"] for step in draft["steps"]]
    assert action_types == [
        "search_product",
        "add_to_cart",
        "login",
        "add_to_cart",
        "checkout",
        "checkout",
        "payment_success",
        "view_order",
    ]
    generated_add_to_cart = draft["steps"][3]
    assert generated_add_to_cart["expected_status"] == 201
    assert generated_add_to_cart["request_payload"] == {"product_id": "product-1", "quantity": 1}
    create_order = draft["steps"][5]
    assert create_order["endpoint"] == "/api/orders"
    assert create_order["expected_status"] == 201
    assert create_order["extract"] == {"order_id": "response.body.order_id"}
    payment = draft["steps"][6]
    assert payment["uses"] == {"order_id": "request.body"}
    assert draft["steps"][7]["endpoint"] == "/api/orders/:id"
    assert draft["steps"][7]["uses"] == {"order_id": "path"}

def test_build_test_case_draft_preserves_get_query_filters() -> None:
    log = _log(
        "GET",
        "/api/products",
        200,
        {},
        {"result_count": 2, "first_result_name": "Logitech Mouse"},
        "search_product",
    )
    log["raw_log"] = {"query": {"category": "Accessories"}}

    draft = service._build_test_case_draft(_journey(), [log])

    assert draft["steps"][0]["endpoint"] == "/api/products?category=Accessories"

def test_build_test_case_draft_resolves_product_detail_placeholder() -> None:
    journey = {
        **_journey(),
        "steps": [
            {"order": 1, "action_type": "search_product"},
            {"order": 2, "action_type": "view_product"},
        ],
    }
    logs = [
        _log("GET", "/api/categories", 200, {}, {"categories": []}, "search_product"),
        _log(
            "GET",
            "/api/products/:id",
            200,
            {},
            {"product_id": "old-product", "name": "Dell Inspiron 15", "brand": "Dell", "category": "Laptop", "price": 15000000},
            "view_product",
        ),
    ]

    draft = service._build_test_case_draft(journey, logs)

    assert [step["endpoint"] for step in draft["steps"]] == [
        "/api/categories",
        "/api/products?keyword=Dell+Inspiron+15",
        "/api/products/:id",
    ]
    assert draft["steps"][1]["extract"] == {"product_id": "response.body.products[0].product_id"}
    assert draft["steps"][2]["uses"] == {"product_id": "path"}

def test_wire_order_id_uses_keeps_order_subresource_path() -> None:
    steps = [
        {
            "method": "POST",
            "endpoint": "/api/orders",
            "expected_status": 201,
            "extract": {"order_id": "response.body.order_id"},
        },
        {"method": "POST", "endpoint": "/api/orders/old-order/cancel", "expected_status": 200},
    ]

    service._wire_order_id_uses(steps)

    assert steps[1]["endpoint"] == "/api/orders/:id/cancel"
    assert steps[1]["uses"] == {"order_id": "path"}

def test_build_test_case_draft_adds_login_before_auth_only_journey() -> None:
    journey = {**_journey(), "steps": [{"order": 1, "action_type": "add_to_cart"}]}
    logs = [
        _log(
            "POST",
            "/api/cart/items",
            201,
            {"product_id": "product-1", "quantity": 1, "authorization": "***MASKED***"},
            {"cart": {}, "product_id": "product-1"},
            "add_to_cart",
        )
    ]

    draft = service._build_test_case_draft(journey, logs)

    assert [step["action_type"] for step in draft["steps"]] == ["login", "add_to_cart"]
    assert draft["steps"][0]["endpoint"] == "/api/auth/login"

def test_build_test_case_draft_makes_payment_only_journey_self_contained() -> None:
    journey = {**_journey(), "steps": [{"order": 1, "action_type": "payment_success"}]}
    logs = [
        _log(
            "POST",
            "/api/payments/simulate-success",
            200,
            {"order_id": "old-order-id", "authorization": "***MASKED***"},
            {"order_id": "old-order-id", "payment_status": "SUCCESS", "order_status": "PAID"},
            "payment_success",
        )
    ]

    draft = service._build_test_case_draft(journey, logs)

    assert [step["action_type"] for step in draft["steps"]] == [
        "login",
        "search_product",
        "add_to_cart",
        "checkout",
        "checkout",
        "payment_success",
    ]
    assert draft["steps"][2]["uses"] == {"product_id": "request.body"}
    assert draft["steps"][4]["extract"] == {"order_id": "response.body.order_id"}
    assert draft["steps"][5]["uses"] == {"order_id": "request.body"}

def test_build_test_case_draft_keeps_session_login_when_early_search_is_304() -> None:
    journey = {
        **_journey(),
        "steps": [
            {"order": 1, "action_type": "search_product"},
            {"order": 2, "action_type": "login"},
            {"order": 3, "action_type": "add_to_cart"},
        ],
    }
    logs = [
        _log("GET", "/api/products", 304, {"authorization": "***MASKED***"}, {"result_count": 1}, "search_product"),
        _log(
            "POST",
            "/api/auth/login",
            200,
            {"email": "***MASKED***", "password": "***MASKED***", "authorization": "***MASKED***"},
            {"accessToken": "***MASKED***", "user": {"name": "Product Browser", "address": "456 Browse Avenue"}},
            "login",
        ),
        _log("GET", "/api/products", 200, {"authorization": "***MASKED***"}, {"result_count": 1}, "search_product"),
        _log(
            "POST",
            "/api/cart/items",
            201,
            {"product_id": "product-1", "quantity": 1, "authorization": "***MASKED***"},
            {"cart": {}, "product_id": "product-1"},
            "add_to_cart",
        ),
    ]

    draft = service._build_test_case_draft(journey, logs)

    assert [step["action_type"] for step in draft["steps"]] == ["login", "search_product", "add_to_cart"]
    assert draft["steps"][0]["request_payload"] == {"email": "browser_user@example.com", "password": "Password123"}

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
                "framework": "jest_supertest",
                "language": "typescript",
                "file_path": None,
            }
        raise AssertionError(f"Unexpected fetchone SQL: {self.last_sql}")

    def fetchall(self) -> list[dict]:
        if "FROM logs" in self.last_sql:
            return [_log("POST", "/auth/login", 200, {"email": "user@example.com"}, {"token": "abc"}, "login")]
        raise AssertionError(f"Unexpected fetchall SQL: {self.last_sql}")
