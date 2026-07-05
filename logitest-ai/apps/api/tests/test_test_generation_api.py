import psycopg
from fastapi.testclient import TestClient

from app.main import app
from app.modules.test_generation import service
from app.modules.test_generation.schemas import GeneratedTestCaseFilters, GeneratedTestFramework

client = TestClient(app)


def test_generate_test_case_returns_generated_summary(monkeypatch) -> None:
    expected = {
        "test_case_id": "test-case-id",
        "journey_id": "journey-id",
        "name": "API test - Successful buyer checkout",
        "status": "generated",
        "step_count": 6,
        "artifacts": [
            {
                "id": "artifact-id",
                "framework": "playwright_api",
                "language": "typescript",
                "file_path": None,
            }
        ],
    }

    def fake_generate_test_case(*, journey_id: str, overwrite: bool, frameworks: list[GeneratedTestFramework], write_files: bool) -> dict:
        assert journey_id == "journey-id"
        assert overwrite is True
        assert frameworks == [GeneratedTestFramework.PLAYWRIGHT_API, GeneratedTestFramework.JEST_SUPERTEST]
        assert write_files is False
        return expected

    monkeypatch.setattr(service, "generate_test_case", fake_generate_test_case)

    response = client.post(
        "/api/test-generation/generate",
        json={"journey_id": "journey-id", "overwrite": True, "frameworks": ["playwright_api", "jest_supertest"]},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_generate_test_case_defaults_to_jest_supertest(monkeypatch) -> None:
    expected = {
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

    def fake_generate_test_case(*, journey_id: str, overwrite: bool, frameworks: list[GeneratedTestFramework], write_files: bool) -> dict:
        assert journey_id == "journey-id"
        assert frameworks == [GeneratedTestFramework.JEST_SUPERTEST]
        return expected

    monkeypatch.setattr(service, "generate_test_case", fake_generate_test_case)

    response = client.post("/api/test-generation/generate", json={"journey_id": "journey-id"})

    assert response.status_code == 200
    assert response.json() == expected

def test_generate_test_case_maps_domain_errors(monkeypatch) -> None:
    def raise_not_found(*, journey_id: str, overwrite: bool, frameworks: list[GeneratedTestFramework], write_files: bool) -> None:
        raise service.JourneyNotFoundError(journey_id)

    monkeypatch.setattr(service, "generate_test_case", raise_not_found)
    response = client.post("/api/test-generation/generate", json={"journey_id": "missing"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Journey not found."}

    def raise_no_replay_data(*, journey_id: str, overwrite: bool, frameworks: list[GeneratedTestFramework], write_files: bool) -> None:
        raise service.JourneyHasNoLogsError(journey_id)

    monkeypatch.setattr(service, "generate_test_case", raise_no_replay_data)
    response = client.post("/api/test-generation/generate", json={"journey_id": "journey-id"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Journey does not have enough replay data to generate a test case."}

    def raise_duplicate(*, journey_id: str, overwrite: bool, frameworks: list[GeneratedTestFramework], write_files: bool) -> None:
        raise service.TestCaseAlreadyExistsError("API test - duplicate")

    monkeypatch.setattr(service, "generate_test_case", raise_duplicate)
    response = client.post("/api/test-generation/generate", json={"journey_id": "journey-id", "overwrite": False})
    assert response.status_code == 409
    assert response.json() == {"detail": "Test case already exists."}


def test_generate_test_case_maps_database_errors(monkeypatch) -> None:
    def raise_database_error(*, journey_id: str, overwrite: bool, frameworks: list[GeneratedTestFramework], write_files: bool) -> None:
        raise psycopg.OperationalError("connection failed")

    monkeypatch.setattr(service, "generate_test_case", raise_database_error)

    response = client.post("/api/test-generation/generate", json={"journey_id": "journey-id"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_list_test_cases_returns_paginated_items(monkeypatch) -> None:
    expected = {
        "items": [
            {
                "id": "test-case-id",
                "journey_id": "journey-id",
                "persona_id": "persona-id",
                "journey_name": "Successful buyer checkout",
                "persona_name": "Buyer",
                "name": "API test - Successful buyer checkout",
                "description": "Generated API test case",
                "type": "api",
                "status": "generated",
                "step_count": 6,
                "generated_by": "test_generation_service",
                "created_at": "2026-06-24T00:00:00Z",
                "updated_at": "2026-06-24T00:00:00Z",
            }
        ],
        "limit": 5,
        "offset": 10,
        "total": 1,
    }

    def fake_list_test_cases(*, limit: int, offset: int, filters: GeneratedTestCaseFilters) -> dict:
        assert limit == 5
        assert offset == 10
        assert filters.journey_id == "journey-id"
        assert filters.status == "generated"
        return expected

    monkeypatch.setattr(service, "list_test_cases", fake_list_test_cases)

    response = client.get(
        "/api/test-generation/test-cases",
        params={"limit": 5, "offset": 10, "journey_id": "journey-id", "status": "generated"},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_get_test_case_detail_returns_json_spec(monkeypatch) -> None:
    expected = {
        "id": "test-case-id",
        "journey_id": "journey-id",
        "persona_id": "persona-id",
        "journey_name": "Successful buyer checkout",
        "persona_name": "Buyer",
        "name": "API test - Successful buyer checkout",
        "description": "Generated API test case",
        "type": "api",
        "status": "generated",
        "steps": [{"order": 1, "method": "POST", "endpoint": "/auth/login"}],
        "assertions": [{"order": 1, "type": "status_code", "expected": 200}],
        "golden_response": {"step_count": 1},
        "generated_code": "def test_api_test(api_client):\n    assert True",
        "generated_by": "test_generation_service",
        "artifacts": [],
        "created_at": "2026-06-24T00:00:00Z",
        "updated_at": "2026-06-24T00:00:00Z",
    }

    def fake_get_test_case_detail(test_case_id: str) -> dict:
        assert test_case_id == "test-case-id"
        return expected

    monkeypatch.setattr(service, "get_test_case_detail", fake_get_test_case_detail)

    response = client.get("/api/test-generation/test-cases/test-case-id")

    assert response.status_code == 200
    assert response.json() == expected


def test_test_case_routes_validate_pagination_bounds() -> None:
    assert client.get("/api/test-generation/test-cases", params={"limit": 0}).status_code == 422
    assert client.get("/api/test-generation/test-cases", params={"limit": 501}).status_code == 422
    assert client.get("/api/test-generation/test-cases", params={"offset": -1}).status_code == 422


def test_generate_test_case_rejects_invalid_framework() -> None:
    response = client.post("/api/test-generation/generate", json={"journey_id": "journey-id", "frameworks": ["unknown"]})

    assert response.status_code == 422


def test_artifact_routes_return_list_and_detail(monkeypatch) -> None:
    artifact = {
        "id": "artifact-id",
        "framework": "playwright_api",
        "language": "typescript",
        "file_path": "generated-tests/playwright/api-test.spec.ts",
        "code": "import { test } from \"@playwright/test\";",
        "created_at": "2026-06-24T00:00:00Z",
        "updated_at": "2026-06-24T00:00:00Z",
    }

    def fake_list_artifacts(test_case_id: str) -> dict:
        assert test_case_id == "test-case-id"
        return {"items": [artifact], "total": 1}

    def fake_get_artifact(test_case_id: str, framework: GeneratedTestFramework) -> dict:
        assert test_case_id == "test-case-id"
        assert framework == GeneratedTestFramework.PLAYWRIGHT_API
        return artifact

    monkeypatch.setattr(service, "list_test_case_artifacts", fake_list_artifacts)
    monkeypatch.setattr(service, "get_test_case_artifact", fake_get_artifact)

    list_response = client.get("/api/test-generation/test-cases/test-case-id/artifacts")
    detail_response = client.get("/api/test-generation/test-cases/test-case-id/artifacts/playwright_api")

    assert list_response.status_code == 200
    assert list_response.json() == {"items": [artifact], "total": 1}
    assert detail_response.status_code == 200
    assert detail_response.json() == artifact


def test_read_routes_map_errors(monkeypatch) -> None:
    def raise_list_database_error(*, limit: int, offset: int, filters: GeneratedTestCaseFilters) -> None:
        raise psycopg.OperationalError("connection failed")

    def raise_detail_not_found(test_case_id: str) -> None:
        raise service.TestCaseNotFoundError(test_case_id)

    monkeypatch.setattr(service, "list_test_cases", raise_list_database_error)
    monkeypatch.setattr(service, "get_test_case_detail", raise_detail_not_found)

    assert client.get("/api/test-generation/test-cases").status_code == 503
    response = client.get("/api/test-generation/test-cases/missing")
    assert response.status_code == 404
    assert response.json() == {"detail": "Test case not found."}


def test_artifact_routes_map_errors(monkeypatch) -> None:
    def raise_artifact_not_found(test_case_id: str, framework: GeneratedTestFramework) -> None:
        raise service.TestCaseArtifactNotFoundError(f"{test_case_id}:{framework}")

    monkeypatch.setattr(service, "get_test_case_artifact", raise_artifact_not_found)

    response = client.get("/api/test-generation/test-cases/test-case-id/artifacts/playwright_api")

    assert response.status_code == 404
    assert response.json() == {"detail": "Test case artifact not found."}
