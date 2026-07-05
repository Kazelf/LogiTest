import psycopg
from fastapi import APIRouter, HTTPException, Query, status

from app.modules.test_generation import service
from app.modules.test_generation.schemas import (
    GenerateTestCaseRequest,
    GenerateTestCaseResponse,
    GeneratedArtifactDetail,
    GeneratedTestCaseFilters,
    GeneratedTestFramework,
    TestCaseArtifactListResponse,
    TestCaseDetailResponse,
    TestCaseListResponse,
)

router = APIRouter(prefix="/api/test-generation", tags=["test-generation"])


@router.post("/generate", response_model=GenerateTestCaseResponse)
def generate_test_case(request: GenerateTestCaseRequest) -> dict[str, object]:
    try:
        return service.generate_test_case(
            journey_id=request.journey_id,
            overwrite=request.overwrite,
            frameworks=request.frameworks,
            write_files=request.write_files,
        )
    except service.JourneyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey not found.",
        ) from exc
    except (service.JourneyMissingExampleSessionError, service.JourneyHasNoLogsError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Journey does not have enough replay data to generate a test case.",
        ) from exc
    except service.TestCaseAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Test case already exists.",
        ) from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc


@router.get("/test-cases", response_model=TestCaseListResponse)
def list_test_cases(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    journey_id: str | None = None,
    test_case_status: str | None = Query(default=None, alias="status"),
) -> dict[str, object]:
    try:
        filters = GeneratedTestCaseFilters(journey_id=journey_id, status=test_case_status)
        return service.list_test_cases(limit=limit, offset=offset, filters=filters)
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc


@router.get("/test-cases/{test_case_id}/artifacts", response_model=TestCaseArtifactListResponse)
def list_test_case_artifacts(test_case_id: str) -> dict[str, object]:
    try:
        return service.list_test_case_artifacts(test_case_id)
    except service.TestCaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found.",
        ) from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc


@router.get("/test-cases/{test_case_id}/artifacts/{framework}", response_model=GeneratedArtifactDetail)
def get_test_case_artifact(test_case_id: str, framework: GeneratedTestFramework) -> dict[str, object]:
    try:
        return service.get_test_case_artifact(test_case_id, framework)
    except service.TestCaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found.",
        ) from exc
    except service.TestCaseArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case artifact not found.",
        ) from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc


@router.get("/test-cases/{test_case_id}", response_model=TestCaseDetailResponse)
def get_test_case_detail(test_case_id: str) -> dict[str, object]:
    try:
        return service.get_test_case_detail(test_case_id)
    except service.TestCaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found.",
        ) from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
