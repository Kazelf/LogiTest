from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalyzeBehaviorResponse(BaseModel):
    sessions_analyzed: int
    personas_upserted: int
    journeys_upserted: int
    source: str
    method: str


class PersonaFilters(BaseModel):
    name: str | None = None


class PersonaListItem(BaseModel):
    id: str
    name: str
    description: str | None
    detection_method: str
    confidence_score: float | None
    features: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PersonaListResponse(BaseModel):
    items: list[PersonaListItem]
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
    total: int


class JourneyFilters(BaseModel):
    persona_id: str | None = None
    name: str | None = None


class JourneyListItem(BaseModel):
    id: str
    persona_id: str | None
    persona_name: str | None
    name: str
    description: str | None
    source_session_count: int
    frequency_score: float | None
    risk_score: float | None
    steps: list[dict[str, Any]]
    example_session_id: str | None
    created_at: datetime
    updated_at: datetime


class JourneyListResponse(BaseModel):
    items: list[JourneyListItem]
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
    total: int
