from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_snapshot_is_deterministic() -> None:
    first = client.get("/api/demo/snapshot")
    second = client.get("/api/demo/snapshot")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["summary"]["regression_caught"] == "Payment status mismatch"
