import psycopg
from fastapi import APIRouter, HTTPException, Query, status

from app.modules.reports import service
from app.modules.reports.schemas import TestRunListResponse, TestRunResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/test-runs", response_model=TestRunListResponse)
def list_test_run_reports(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    run_status: str | None = Query(default=None, alias="status"),
) -> dict[str, object]:
    try:
        return service.list_test_run_reports(limit=limit, offset=offset, status=run_status)
    except psycopg.OperationalError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable.") from exc


@router.get("/test-runs/{run_id}", response_model=TestRunResponse)
def get_test_run_report(run_id: str) -> dict[str, object]:
    try:
        return service.get_test_run_report(run_id)
    except service.TestRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found.") from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable.") from exc
