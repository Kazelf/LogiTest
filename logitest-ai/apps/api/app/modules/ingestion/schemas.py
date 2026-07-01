from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ImportMockLogsResponse(BaseModel):
    source: str
    loaded_records: int
    sessions: int
    counts: dict[str, int]


class ImportElasticsearchLogsRequest(BaseModel):
    index: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = Field(default=200, ge=1, le=1000)

class ImportElasticsearchLogsResponse(BaseModel):
    source: str
    index: str
    loaded_records: int
    imported_logs: int
    sessions: int
    counts: dict[str, int]

class ImportShopLiteLogsResponse(BaseModel):
    source: str
    path: str
    loaded_records: int
    imported_logs: int
    sessions: int
    counts: dict[str, int]

class LogListItem(BaseModel):
    id: str
    external_log_id: str | None
    session_external_id: str | None
    trace_id: str | None
    user_id: str | None
    service_name: str
    level: str
    method: str | None
    endpoint: str | None
    status_code: int | None
    response_time_ms: int | None
    occurred_at: datetime


class LogListResponse(BaseModel):
    items: list[LogListItem]
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    total: int


class LogFilters(BaseModel):
    session_id: str | None = None
    trace_id: str | None = None
    endpoint: str | None = None
    level: str | None = None


class SessionFilters(BaseModel):
    user_id: str | None = None
    source: str | None = None


class SessionSummaryItem(BaseModel):
    id: str
    external_session_id: str
    user_id: str | None
    started_at: datetime | None
    ended_at: datetime | None
    request_count: int
    log_count: int
    source: str
    services: list[str]
    created_at: datetime


class SessionListResponse(BaseModel):
    items: list[SessionSummaryItem]
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    total: int


class SessionDetail(BaseModel):
    id: str
    external_session_id: str
    user_id: str | None
    started_at: datetime | None
    ended_at: datetime | None
    request_count: int
    log_count: int
    source: str
    metadata: dict[str, Any]
    created_at: datetime


class SessionDetailLogItem(BaseModel):
    id: str
    external_log_id: str | None
    trace_id: str | None
    user_id: str | None
    service_name: str
    level: str
    method: str | None
    endpoint: str | None
    status_code: int | None
    response_time_ms: int | None
    occurred_at: datetime


class SessionDetailResponse(BaseModel):
    session: SessionDetail
    logs: list[SessionDetailLogItem]


ImportCounts = dict[str, int]
Row = dict[str, Any]
