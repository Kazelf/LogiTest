from __future__ import annotations

from typing import Any

from app.modules.execution import service as execution_service

TestRunNotFoundError = execution_service.TestRunNotFoundError


def list_test_run_reports(*, limit: int, offset: int, status: str | None = None) -> dict[str, Any]:
    return execution_service.list_test_runs(limit=limit, offset=offset, status=status)


def get_test_run_report(run_id: str) -> dict[str, Any]:
    return execution_service.get_test_run(run_id)
