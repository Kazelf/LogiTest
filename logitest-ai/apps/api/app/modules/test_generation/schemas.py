from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GeneratedTestFramework(StrEnum):
    PLAYWRIGHT_API = "playwright_api"
    JEST_SUPERTEST = "jest_supertest"
    MOCHA_SUPERTEST = "mocha_supertest"


class GeneratedArtifactSummary(BaseModel):
    id: str | None = None
    framework: GeneratedTestFramework
    language: str
    file_path: str | None = None


class GeneratedArtifactDetail(GeneratedArtifactSummary):
    code: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GenerateTestCaseRequest(BaseModel):
    journey_id: str
    overwrite: bool = True
    frameworks: list[GeneratedTestFramework] = Field(default_factory=lambda: [GeneratedTestFramework.JEST_SUPERTEST])
    write_files: bool = False


class GenerateTestCaseResponse(BaseModel):
    test_case_id: str
    journey_id: str
    name: str
    status: str
    step_count: int
    artifacts: list[GeneratedArtifactSummary] = Field(default_factory=list)


class GeneratedTestCaseFilters(BaseModel):
    journey_id: str | None = None
    status: str | None = None


class TestCaseListItem(BaseModel):
    id: str
    journey_id: str | None
    persona_id: str | None
    journey_name: str | None
    persona_name: str | None
    name: str
    description: str | None
    type: str
    status: str
    step_count: int
    generated_by: str
    created_at: datetime
    updated_at: datetime


class TestCaseListResponse(BaseModel):
    items: list[TestCaseListItem]
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
    total: int


class TestCaseDetailResponse(BaseModel):
    id: str
    journey_id: str | None
    persona_id: str | None
    journey_name: str | None
    persona_name: str | None
    name: str
    description: str | None
    type: str
    status: str
    steps: list[dict[str, Any]]
    assertions: list[dict[str, Any]]
    golden_response: dict[str, Any]
    generated_code: str | None
    generated_by: str
    artifacts: list[GeneratedArtifactDetail] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TestCaseArtifactListResponse(BaseModel):
    items: list[GeneratedArtifactDetail]
    total: int
