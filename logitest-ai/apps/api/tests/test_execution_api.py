import psycopg
from fastapi.testclient import TestClient

from app.main import app
from app.modules.execution import service

client = TestClient(app)


def test_run_test_case_api_returns_persisted_run(monkeypatch) -> None:
    expected = _run_response()

    def fake_run_test_case(
        test_case_id: str,
        *,
        target_base_url: str | None,
        target_environment: str,
        timeout_seconds: float,
    ) -> dict:
        assert test_case_id == "test-case-id"
        assert target_base_url == "http://localhost:3001"
        assert target_environment == "staging"
        assert timeout_seconds == 5
        return expected

    monkeypatch.setattr(service, "run_test_case", fake_run_test_case)

    response = client.post(
        "/api/execution/test-cases/test-case-id/run",
        json={"target_base_url": "http://localhost:3001", "timeout_seconds": 5},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_execution_routes_map_errors(monkeypatch) -> None:
    def raise_not_found(*args, **kwargs) -> None:
        raise service.TestCaseNotFoundError("missing")

    monkeypatch.setattr(service, "run_test_case", raise_not_found)
    assert client.post("/api/execution/test-cases/missing/run", json={}).status_code == 404

    def raise_empty(*args, **kwargs) -> None:
        raise service.TestCaseHasNoStepsError("empty")

    monkeypatch.setattr(service, "run_test_case", raise_empty)
    assert client.post("/api/execution/test-cases/empty/run", json={}).status_code == 422

    def raise_database(*args, **kwargs) -> None:
        raise psycopg.OperationalError("down")

    monkeypatch.setattr(service, "list_test_case_runs", raise_database)
    assert client.get("/api/execution/test-cases/test-case-id/runs").status_code == 503


def test_list_test_case_runs_api(monkeypatch) -> None:
    expected = {"items": [_run_response()], "limit": 5, "offset": 10, "total": 1}

    def fake_list_test_case_runs(test_case_id: str, *, limit: int, offset: int) -> dict:
        assert test_case_id == "test-case-id"
        assert limit == 5
        assert offset == 10
        return expected

    monkeypatch.setattr(service, "list_test_case_runs", fake_list_test_case_runs)

    response = client.get("/api/execution/test-cases/test-case-id/runs", params={"limit": 5, "offset": 10})

    assert response.status_code == 200
    assert response.json() == expected


def _run_response() -> dict:
    return {
        "id": "run-id",
        "test_case_id": "test-case-id",
        "status": "passed",
        "target_environment": "staging",
        "started_at": "2026-06-25T00:00:00Z",
        "finished_at": "2026-06-25T00:00:01Z",
        "duration_ms": 100,
        "actual_response": {"steps": []},
        "diff_result": {"differences": []},
        "error_message": None,
        "runner_metadata": {"runner": "test"},
        "created_at": "2026-06-25T00:00:01Z",
    }
