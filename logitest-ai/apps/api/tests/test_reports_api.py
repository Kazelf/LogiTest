import psycopg
from fastapi.testclient import TestClient

from app.main import app
from app.modules.reports import service

client = TestClient(app)


def test_report_routes_return_runs(monkeypatch) -> None:
    run = _run_response()

    def fake_list_test_run_reports(*, limit: int, offset: int, status: str | None) -> dict:
        assert limit == 5
        assert offset == 10
        assert status == "failed"
        return {"items": [run], "limit": limit, "offset": offset, "total": 1}

    def fake_get_test_run_report(run_id: str) -> dict:
        assert run_id == "run-id"
        return run

    monkeypatch.setattr(service, "list_test_run_reports", fake_list_test_run_reports)
    monkeypatch.setattr(service, "get_test_run_report", fake_get_test_run_report)

    list_response = client.get("/api/reports/test-runs", params={"limit": 5, "offset": 10, "status": "failed"})
    detail_response = client.get("/api/reports/test-runs/run-id")

    assert list_response.status_code == 200
    assert list_response.json() == {"items": [run], "limit": 5, "offset": 10, "total": 1}
    assert detail_response.status_code == 200
    assert detail_response.json() == run


def test_report_routes_map_errors(monkeypatch) -> None:
    def raise_not_found(run_id: str) -> None:
        raise service.TestRunNotFoundError(run_id)

    monkeypatch.setattr(service, "get_test_run_report", raise_not_found)
    response = client.get("/api/reports/test-runs/missing")
    assert response.status_code == 404
    assert response.json() == {"detail": "Test run not found."}

    def raise_database(*args, **kwargs) -> None:
        raise psycopg.OperationalError("down")

    monkeypatch.setattr(service, "list_test_run_reports", raise_database)
    assert client.get("/api/reports/test-runs").status_code == 503


def _run_response() -> dict:
    return {
        "id": "run-id",
        "test_case_id": "test-case-id",
        "status": "failed",
        "target_environment": "staging",
        "started_at": "2026-06-25T00:00:00Z",
        "finished_at": "2026-06-25T00:00:01Z",
        "duration_ms": 100,
        "actual_response": {"steps": []},
        "diff_result": {"differences": [{"type": "business_field"}]},
        "error_message": None,
        "runner_metadata": {"runner": "test"},
        "created_at": "2026-06-25T00:00:01Z",
    }
