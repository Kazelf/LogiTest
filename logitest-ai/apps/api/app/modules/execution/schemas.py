from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunTestCaseRequest(BaseModel):
    target_base_url: str | None = None
    target_environment: str = "staging"
    timeout_seconds: float = Field(default=10.0, gt=0, le=60)


class TestRunStepResult(BaseModel):
    order: int
    method: str
    endpoint: str
    resolved_endpoint: str
    status_code: int | None = None
    duration_ms: int | None = None
    response_body: Any = None
    error: str | None = None


class TestRunResponse(BaseModel):
    id: str
    test_case_id: str
    status: str
    target_environment: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    actual_response: dict[str, Any]
    diff_result: dict[str, Any]
    error_message: str | None
    runner_metadata: dict[str, Any]
    created_at: datetime | None = None


class TestRunListResponse(BaseModel):
    items: list[TestRunResponse]
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
    total: int
