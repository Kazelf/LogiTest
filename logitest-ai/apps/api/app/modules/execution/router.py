import psycopg
from fastapi import APIRouter, HTTPException, Query, status

from app.modules.execution import service
from app.modules.execution.schemas import RunTestCaseRequest, TestRunListResponse, TestRunResponse

router = APIRouter(prefix="/api/execution", tags=["execution"])


@router.post("/test-cases/{test_case_id}/run", response_model=TestRunResponse)
def run_test_case(test_case_id: str, request: RunTestCaseRequest | None = None) -> dict[str, object]:
    request = request or RunTestCaseRequest()
    try:
        return service.run_test_case(
            test_case_id,
            target_base_url=request.target_base_url,
            target_environment=request.target_environment,
            timeout_seconds=request.timeout_seconds,
        )
    except service.TestCaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found.") from exc
    except service.TestCaseHasNoStepsError as exc:
        raise HTTPException(status_code=422, detail="Test case has no executable steps.") from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable.") from exc


@router.get("/test-cases/{test_case_id}/runs", response_model=TestRunListResponse)
def list_test_case_runs(
    test_case_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    try:
        return service.list_test_case_runs(test_case_id, limit=limit, offset=offset)
    except service.TestCaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found.") from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable.") from exc
