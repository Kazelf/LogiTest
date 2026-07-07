from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

LOG_INGESTION_TOTAL = Counter("log_ingestion_total", "Total logs ingested into LogiTest AI.")
JOURNEY_DETECTED_TOTAL = Counter("journey_detected_total", "Total journeys detected by behavior analysis.")
TEST_CASE_GENERATED_TOTAL = Counter("test_case_generated_total", "Total generated test cases.")
TEST_ARTIFACT_GENERATED_TOTAL = Counter("test_artifact_generated_total", "Total generated test artifacts.")
TEST_EXECUTION_TOTAL = Counter("test_execution_total", "Total test executions.")
TEST_EXECUTION_PASS_TOTAL = Counter("test_execution_pass_total", "Total passing test executions.")
TEST_EXECUTION_FAIL_TOTAL = Counter("test_execution_fail_total", "Total failing or errored test executions.")
REGRESSION_DETECTED_TOTAL = Counter("regression_detected_total", "Total regressions or diffs detected.")
AI_REQUEST_TOTAL = Counter("ai_request_total", "Total AI engine requests.")
AI_ERROR_TOTAL = Counter("ai_error_total", "Total AI engine errors.")

API_REQUEST_DURATION_SECONDS = Histogram(
    "api_request_duration_seconds",
    "FastAPI HTTP request duration in seconds.",
    ["method", "path", "status_code"],
)
TEST_EXECUTION_DURATION_SECONDS = Histogram(
    "test_execution_duration_seconds",
    "Generated test execution duration in seconds.",
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
