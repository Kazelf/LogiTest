from datetime import datetime, timezone

import httpx
import pytest

from app.modules.ingestion import elasticsearch_client
from app.modules.ingestion.elasticsearch_client import ElasticsearchImportError


def test_build_search_query_uses_match_all_without_time_range() -> None:
    query = elasticsearch_client._build_search_query(start_time=None, end_time=None, limit=25)

    assert query == {
        "query": {"match_all": {}},
        "size": 25,
        "sort": [{"timestamp": {"order": "asc"}}],
    }


def test_build_search_query_uses_timestamp_range_when_provided() -> None:
    start_time = datetime(2026, 6, 24, 10, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 6, 24, 11, 0, tzinfo=timezone.utc)

    query = elasticsearch_client._build_search_query(
        start_time=start_time,
        end_time=end_time,
        limit=50,
    )

    assert query["size"] == 50
    assert query["query"]["bool"]["filter"] == [
        {
            "range": {
                "timestamp": {
                    "gte": "2026-06-24T10:00:00+00:00",
                    "lte": "2026-06-24T11:00:00+00:00",
                }
            }
        }
    ]


def test_search_logs_posts_to_configured_index(monkeypatch) -> None:
    calls = []

    def fake_post(url: str, json: dict, timeout: float) -> httpx.Response:
        calls.append({"url": url, "json": json, "timeout": timeout})
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"hits": {"hits": [{"_id": "log-1", "_source": {"request_id": "req-1"}}]}},
        )

    monkeypatch.setattr(elasticsearch_client.httpx, "post", fake_post)
    monkeypatch.setattr(elasticsearch_client.settings, "elasticsearch_url", "http://elasticsearch:9200")

    hits = elasticsearch_client.search_logs(index="logitest-demo-logs", limit=10)

    assert hits == [{"_id": "log-1", "_source": {"request_id": "req-1"}}]
    assert calls[0]["url"] == "http://elasticsearch:9200/logitest-demo-logs/_search"
    assert calls[0]["json"]["size"] == 10
    assert calls[0]["timeout"] == 10.0


def test_search_logs_wraps_http_errors(monkeypatch) -> None:
    def fake_post(url: str, json: dict, timeout: float) -> httpx.Response:
        return httpx.Response(503, request=httpx.Request("POST", url))

    monkeypatch.setattr(elasticsearch_client.httpx, "post", fake_post)

    with pytest.raises(ElasticsearchImportError):
        elasticsearch_client.search_logs(index="logitest-demo-logs")
