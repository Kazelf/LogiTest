import psycopg
from fastapi import APIRouter, HTTPException, Query, status

from app.modules.ingestion import service
from app.modules.ingestion.elasticsearch_client import ElasticsearchImportError
from app.modules.ingestion.schemas import (
    ImportElasticsearchLogsRequest,
    ImportElasticsearchLogsResponse,
    ImportMockLogsResponse,
    ImportShopLiteLogsResponse,
    LogFilters,
    LogListResponse,
    SessionDetailResponse,
    SessionFilters,
    SessionListResponse,
)

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/import-mock", response_model=ImportMockLogsResponse)
def import_mock_logs() -> dict[str, object]:
    try:
        return service.import_mock_logs_from_dataset()
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mock log import failed.",
        ) from exc


@router.post("/import-elasticsearch", response_model=ImportElasticsearchLogsResponse)
def import_elasticsearch_logs(request: ImportElasticsearchLogsRequest) -> dict[str, object]:
    try:
        return service.import_elasticsearch_logs(request)
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
    except ElasticsearchImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Elasticsearch log import failed.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Elasticsearch log import failed.",
        ) from exc

@router.post("/import-shoplite", response_model=ImportShopLiteLogsResponse)
def import_shoplite_logs() -> dict[str, object]:
    try:
        return service.import_shoplite_logs_from_jsonl()
    except service.ShopLiteLogFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ShopLite log file not found: {exc}",
        ) from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ShopLite log import failed.",
        ) from exc

@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: str | None = None,
    source: str | None = None,
) -> dict[str, object]:
    try:
        filters = SessionFilters(user_id=user_id, source=source)
        return service.list_sessions(limit=limit, offset=offset, filters=filters)
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc


@router.get("/sessions/{external_session_id}", response_model=SessionDetailResponse)
def get_session_detail(external_session_id: str) -> dict[str, object]:
    try:
        return service.get_session_detail(external_session_id)
    except service.SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        ) from exc
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc


@router.get("", response_model=LogListResponse)
def list_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session_id: str | None = None,
    trace_id: str | None = None,
    endpoint: str | None = None,
    level: str | None = None,
) -> dict[str, object]:
    try:
        filters = LogFilters(session_id=session_id, trace_id=trace_id, endpoint=endpoint, level=level)
        return service.list_logs(limit=limit, offset=offset, filters=filters)
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
