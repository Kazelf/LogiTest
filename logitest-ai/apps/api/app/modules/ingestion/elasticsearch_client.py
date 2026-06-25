from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.core.settings import settings


class ElasticsearchImportError(Exception):
    pass


def search_logs(
    *,
    index: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    query = _build_search_query(start_time=start_time, end_time=end_time, limit=limit)
    url = f"{settings.elasticsearch_url.rstrip('/')}/{index}/_search"

    try:
        response = httpx.post(url, json=query, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ElasticsearchImportError("Elasticsearch search failed.") from exc

    payload = response.json()
    hits = payload.get("hits", {}).get("hits", [])
    if not isinstance(hits, list):
        raise ElasticsearchImportError("Elasticsearch response has invalid hits shape.")

    return hits


def _build_search_query(
    *,
    start_time: datetime | None,
    end_time: datetime | None,
    limit: int,
) -> dict[str, Any]:
    filters: list[dict[str, Any]] = []
    range_filter: dict[str, str] = {}

    if start_time is not None:
        range_filter["gte"] = start_time.isoformat()
    if end_time is not None:
        range_filter["lte"] = end_time.isoformat()
    if range_filter:
        filters.append({"range": {"timestamp": range_filter}})

    query: dict[str, Any] = {"match_all": {}}
    if filters:
        query = {"bool": {"filter": filters}}

    return {
        "query": query,
        "size": limit,
        "sort": [{"timestamp": {"order": "asc"}}],
    }
