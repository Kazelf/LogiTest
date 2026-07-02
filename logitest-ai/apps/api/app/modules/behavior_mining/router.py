import psycopg
from fastapi import APIRouter, HTTPException, Query, status

from app.modules.behavior_mining import service
from app.modules.behavior_mining.schemas import (
    AnalyzeBehaviorResponse,
    JourneyFilters,
    JourneyListResponse,
    PersonaFilters,
    PersonaListResponse,
)

router = APIRouter(prefix="/api/behavior", tags=["behavior"])


@router.post("/analyze", response_model=AnalyzeBehaviorResponse)
def analyze_behavior() -> dict[str, object]:
    try:
        return service.analyze_behavior()
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Behavior analysis failed.",
        ) from exc


@router.get("/journeys", response_model=JourneyListResponse)
def list_journeys(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    persona_id: str | None = None,
    name: str | None = None,
) -> dict[str, object]:
    try:
        filters = JourneyFilters(persona_id=persona_id, name=name)
        return service.list_journeys(limit=limit, offset=offset, filters=filters)
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc


@router.get("/personas", response_model=PersonaListResponse)
def list_personas(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    name: str | None = None,
) -> dict[str, object]:
    try:
        filters = PersonaFilters(name=name)
        return service.list_personas(limit=limit, offset=offset, filters=filters)
    except psycopg.OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc
