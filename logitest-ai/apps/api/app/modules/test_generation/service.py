from __future__ import annotations

from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db import connection
from app.modules.test_generation import renderers
from app.modules.test_generation.schemas import GeneratedTestCaseFilters, GeneratedTestFramework

GENERATED_BY = "test_generation_service"
TEST_CASE_STATUS_GENERATED = "generated"
TEST_CASE_TYPE_API = "api"


class JourneyNotFoundError(Exception):
    pass


class JourneyMissingExampleSessionError(Exception):
    pass


class JourneyHasNoLogsError(Exception):
    pass


class TestCaseNotFoundError(Exception):
    pass


class TestCaseAlreadyExistsError(Exception):
    pass


class TestCaseArtifactNotFoundError(Exception):
    pass


def generate_test_case(
    *,
    journey_id: str,
    overwrite: bool = True,
    frameworks: list[GeneratedTestFramework] | None = None,
    write_files: bool = False,
) -> dict[str, Any]:
    requested_frameworks = _normalize_frameworks(frameworks)
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            journey = _fetch_journey(cur, journey_id)
            if journey is None:
                raise JourneyNotFoundError(journey_id)
            if journey.get("example_session_id") is None:
                raise JourneyMissingExampleSessionError(journey_id)

            logs = _fetch_session_logs(cur, str(journey["example_session_id"]))
            if not logs:
                raise JourneyHasNoLogsError(journey_id)

            draft = _build_test_case_draft(journey, logs)
            artifact_drafts = _build_artifact_drafts(draft, requested_frameworks, write_files=write_files)
            if artifact_drafts:
                draft["generated_code"] = artifact_drafts[0]["code"]
            existing_id = _fetch_test_case_id_by_name(cur, draft["name"])
            if existing_id is not None and not overwrite:
                raise TestCaseAlreadyExistsError(draft["name"])

            test_case_id = _upsert_test_case(cur, draft, overwrite=overwrite)
            artifact_summaries = [_upsert_test_case_artifact(cur, test_case_id, artifact) for artifact in artifact_drafts]
            conn.commit()

    return {
        "test_case_id": test_case_id,
        "journey_id": str(journey["id"]),
        "name": draft["name"],
        "status": TEST_CASE_STATUS_GENERATED,
        "step_count": len(draft["steps"]),
        "artifacts": artifact_summaries,
    }


def list_test_cases(*, limit: int, offset: int, filters: GeneratedTestCaseFilters) -> dict[str, Any]:
    where_sql, where_params = _build_test_case_filters(filters)
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM test_cases
        LEFT JOIN journeys ON journeys.id = test_cases.journey_id
        LEFT JOIN personas ON personas.id = test_cases.persona_id
        {where_sql}
    """
    list_sql = f"""
        SELECT
            test_cases.id,
            test_cases.journey_id,
            test_cases.persona_id,
            journeys.name AS journey_name,
            personas.name AS persona_name,
            test_cases.name,
            test_cases.description,
            test_cases.type::text AS type,
            test_cases.status::text AS status,
            jsonb_array_length(test_cases.steps) AS step_count,
            test_cases.generated_by,
            test_cases.created_at,
            test_cases.updated_at
        FROM test_cases
        LEFT JOIN journeys ON journeys.id = test_cases.journey_id
        LEFT JOIN personas ON personas.id = test_cases.persona_id
        {where_sql}
        ORDER BY test_cases.updated_at DESC, test_cases.created_at DESC
        LIMIT %s OFFSET %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(count_sql, where_params)
            total = int(cur.fetchone()["total"])
            cur.execute(list_sql, [*where_params, limit, offset])
            rows = cur.fetchall()

    return {
        "items": [_serialize_test_case_list_row(row) for row in rows],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


def get_test_case_detail(test_case_id: str) -> dict[str, Any]:
    sql = """
        SELECT
            test_cases.id,
            test_cases.journey_id,
            test_cases.persona_id,
            journeys.name AS journey_name,
            personas.name AS persona_name,
            test_cases.name,
            test_cases.description,
            test_cases.type::text AS type,
            test_cases.status::text AS status,
            test_cases.steps,
            test_cases.assertions,
            test_cases.golden_response,
            test_cases.generated_code,
            test_cases.generated_by,
            test_cases.created_at,
            test_cases.updated_at
        FROM test_cases
        LEFT JOIN journeys ON journeys.id = test_cases.journey_id
        LEFT JOIN personas ON personas.id = test_cases.persona_id
        WHERE test_cases.id = %s
    """

    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, [test_case_id])
            row = cur.fetchone()
            if row is None:
                raise TestCaseNotFoundError(test_case_id)
            row["artifacts"] = _fetch_test_case_artifacts(cur, test_case_id)

    return _serialize_test_case_detail_row(row)


def list_test_case_artifacts(test_case_id: str) -> dict[str, Any]:
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if not _test_case_exists(cur, test_case_id):
                raise TestCaseNotFoundError(test_case_id)
            artifacts = _fetch_test_case_artifacts(cur, test_case_id)

    return {"items": artifacts, "total": len(artifacts)}


def get_test_case_artifact(test_case_id: str, framework: GeneratedTestFramework) -> dict[str, Any]:
    with connection.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if not _test_case_exists(cur, test_case_id):
                raise TestCaseNotFoundError(test_case_id)
            artifact = _fetch_test_case_artifact(cur, test_case_id, framework)
            if artifact is None:
                raise TestCaseArtifactNotFoundError(f"{test_case_id}:{framework}")

    return artifact


def _fetch_journey(cur: Any, journey_id: str) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT
            journeys.id,
            journeys.persona_id,
            personas.name AS persona_name,
            journeys.name,
            journeys.description,
            journeys.example_session_id
        FROM journeys
        LEFT JOIN personas ON personas.id = journeys.persona_id
        WHERE journeys.id = %s
        """,
        [journey_id],
    )
    return cur.fetchone()


def _fetch_session_logs(cur: Any, session_id: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT
            logs.service_name,
            logs.method,
            logs.endpoint,
            logs.status_code,
            logs.request_payload,
            logs.response_body,
            logs.response_time_ms,
            logs.action_type,
            logs.occurred_at
        FROM logs
        WHERE logs.session_id = %s
        ORDER BY logs.occurred_at ASC
        """,
        [session_id],
    )
    return list(cur.fetchall())


def _fetch_test_case_id_by_name(cur: Any, name: str) -> str | None:
    cur.execute("SELECT id FROM test_cases WHERE name = %s", [name])
    row = cur.fetchone()
    return str(row["id"]) if row else None


def _build_test_case_draft(journey: dict[str, Any], logs: list[dict[str, Any]]) -> dict[str, Any]:
    steps = _build_steps(logs)
    assertions = _build_assertions(steps)
    name = _build_test_case_name(str(journey["name"]))
    description = f"Generated API test case from journey '{journey['name']}'."
    golden_response = _build_golden_response(journey, logs)

    return {
        "journey_id": str(journey["id"]),
        "persona_id": str(journey["persona_id"]) if journey.get("persona_id") else None,
        "name": name,
        "description": description,
        "steps": steps,
        "assertions": assertions,
        "golden_response": golden_response,
        "generated_code": build_generated_code_stub(name, steps),
    }


def _normalize_frameworks(frameworks: list[GeneratedTestFramework] | None) -> list[GeneratedTestFramework]:
    requested = frameworks or [GeneratedTestFramework.PLAYWRIGHT_API]
    normalized: list[GeneratedTestFramework] = []
    for framework in requested:
        if framework not in normalized:
            normalized.append(framework)
    return normalized


def _build_artifact_drafts(
    draft: dict[str, Any],
    frameworks: list[GeneratedTestFramework],
    *,
    write_files: bool,
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for framework in frameworks:
        code = renderers.render_script(framework=framework, test_case=draft)
        file_path = renderers.write_generated_file(framework=framework, test_case_name=draft["name"], code=code) if write_files else None
        artifacts.append(
            {
                "framework": framework,
                "language": "typescript",
                "file_path": file_path,
                "code": code,
            }
        )
    return artifacts


def _build_steps(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "order": index + 1,
            "action_type": row.get("action_type") or "unknown",
            "service_name": row.get("service_name"),
            "method": row.get("method"),
            "endpoint": row.get("endpoint"),
            "request_payload": row.get("request_payload") or {},
            "expected_status": row.get("status_code"),
            "golden_response": row.get("response_body") or {},
            "response_time_ms": row.get("response_time_ms"),
        }
        for index, row in enumerate(logs)
    ]


def _build_assertions(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    for step in steps:
        assertions.append(
            {
                "order": step["order"],
                "type": "status_code",
                "expected": step.get("expected_status"),
            }
        )

        golden_response = step.get("golden_response")
        if isinstance(golden_response, dict):
            assertions.append(
                {
                    "order": step["order"],
                    "type": "response_schema",
                    "expected": {
                        "type": "object",
                        "required": sorted(golden_response.keys()),
                    },
                }
            )
    return assertions


def _build_golden_response(journey: dict[str, Any], logs: list[dict[str, Any]]) -> dict[str, Any]:
    final_log = logs[-1]
    return {
        "step_count": len(logs),
        "final_status_code": final_log.get("status_code"),
        "final_response_body": final_log.get("response_body") or {},
        "source": {
            "journey_id": str(journey["id"]),
            "example_session_id": str(journey["example_session_id"]),
        },
    }


def _build_test_case_name(journey_name: str) -> str:
    normalized = journey_name.removeprefix("Journey: ").strip()
    return f"API test - {normalized}"


def build_generated_code_stub(name: str, steps: list[dict[str, Any]]) -> str:
    slug = _slugify(name)
    lines = [f"def test_{slug}(api_client):", f"    # Generated API test case with {len(steps)} step(s)."]
    for step in steps:
        lines.append(
            f"    # {step['order']}. {step.get('method') or 'GET'} {step.get('endpoint') or '/'} -> {step.get('expected_status')}"
        )
    lines.append("    assert True")
    return "\n".join(lines)


def _slugify(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "_" for char in value]
    slug = "".join(chars).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "generated_api_test"


def _upsert_test_case(cur: Any, draft: dict[str, Any], *, overwrite: bool) -> str:
    if overwrite:
        sql = """
            INSERT INTO test_cases (
                journey_id,
                persona_id,
                name,
                description,
                type,
                status,
                steps,
                assertions,
                golden_response,
                generated_code,
                generated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                journey_id = EXCLUDED.journey_id,
                persona_id = EXCLUDED.persona_id,
                description = EXCLUDED.description,
                type = EXCLUDED.type,
                status = EXCLUDED.status,
                steps = EXCLUDED.steps,
                assertions = EXCLUDED.assertions,
                golden_response = EXCLUDED.golden_response,
                generated_code = EXCLUDED.generated_code,
                generated_by = EXCLUDED.generated_by,
                updated_at = now()
            RETURNING id
        """
    else:
        sql = """
            INSERT INTO test_cases (
                journey_id,
                persona_id,
                name,
                description,
                type,
                status,
                steps,
                assertions,
                golden_response,
                generated_code,
                generated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

    cur.execute(
        sql,
        (
            draft["journey_id"],
            draft["persona_id"],
            draft["name"],
            draft["description"],
            TEST_CASE_TYPE_API,
            TEST_CASE_STATUS_GENERATED,
            Jsonb(draft["steps"]),
            Jsonb(draft["assertions"]),
            Jsonb(draft["golden_response"]),
            draft["generated_code"],
            GENERATED_BY,
        ),
    )
    return str(cur.fetchone()["id"])


def _upsert_test_case_artifact(cur: Any, test_case_id: str, artifact: dict[str, Any]) -> dict[str, Any]:
    cur.execute(
        """
        INSERT INTO test_case_artifacts (
            test_case_id,
            framework,
            language,
            file_path,
            code
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (test_case_id, framework) DO UPDATE SET
            language = EXCLUDED.language,
            file_path = EXCLUDED.file_path,
            code = EXCLUDED.code,
            updated_at = now()
        RETURNING id, framework, language, file_path
        """,
        (
            test_case_id,
            str(artifact["framework"]),
            artifact["language"],
            artifact["file_path"],
            artifact["code"],
        ),
    )
    return _serialize_artifact_summary_row(cur.fetchone())


def _test_case_exists(cur: Any, test_case_id: str) -> bool:
    cur.execute("SELECT 1 FROM test_cases WHERE id = %s", [test_case_id])
    return cur.fetchone() is not None


def _fetch_test_case_artifacts(cur: Any, test_case_id: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id, framework, language, file_path, code, created_at, updated_at
        FROM test_case_artifacts
        WHERE test_case_id = %s
        ORDER BY framework ASC
        """,
        [test_case_id],
    )
    return [_serialize_artifact_detail_row(row) for row in cur.fetchall()]


def _fetch_test_case_artifact(cur: Any, test_case_id: str, framework: GeneratedTestFramework) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT id, framework, language, file_path, code, created_at, updated_at
        FROM test_case_artifacts
        WHERE test_case_id = %s AND framework = %s
        """,
        [test_case_id, str(framework)],
    )
    row = cur.fetchone()
    return _serialize_artifact_detail_row(row) if row else None


def _build_test_case_filters(filters: GeneratedTestCaseFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if filters.journey_id:
        clauses.append("test_cases.journey_id = %s")
        params.append(filters.journey_id)
    if filters.status:
        clauses.append("test_cases.status = %s")
        params.append(filters.status)
    return ("WHERE " + " AND ".join(clauses), params) if clauses else ("", params)


def _serialize_test_case_list_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "journey_id": str(row["journey_id"]) if row.get("journey_id") else None,
        "persona_id": str(row["persona_id"]) if row.get("persona_id") else None,
        "step_count": int(row.get("step_count") or 0),
    }


def _serialize_test_case_detail_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "id": str(row["id"]),
        "journey_id": str(row["journey_id"]) if row.get("journey_id") else None,
        "persona_id": str(row["persona_id"]) if row.get("persona_id") else None,
        "steps": list(row.get("steps") or []),
        "assertions": list(row.get("assertions") or []),
        "golden_response": row.get("golden_response") or {},
        "artifacts": list(row.get("artifacts") or []),
    }


def _serialize_artifact_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "framework": row["framework"],
        "language": row["language"],
        "file_path": row.get("file_path"),
    }


def _serialize_artifact_detail_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_serialize_artifact_summary_row(row),
        "code": row["code"],
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }
