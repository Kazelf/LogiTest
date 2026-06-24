from app.modules.test_generation import renderers
from app.modules.test_generation.schemas import GeneratedTestFramework


def test_render_playwright_api_generates_ordered_request_steps() -> None:
    code = renderers.render_script(framework=GeneratedTestFramework.PLAYWRIGHT_API, test_case=_test_case())

    assert 'import { test, expect } from "@playwright/test";' in code
    assert 'request.post("/auth/login"' in code
    assert 'data: {' in code
    assert 'request.get("/products")' in code
    assert 'expect(step1.status()).toBe(200);' in code
    assert 'expect(step1Body).toHaveProperty("token");' in code


def test_render_jest_supertest_generates_api_script() -> None:
    code = renderers.render_script(framework=GeneratedTestFramework.JEST_SUPERTEST, test_case=_test_case())

    assert 'import request from "supertest";' in code
    assert 'const baseURL = process.env.TARGET_BASE_URL || "http://localhost:3001";' in code
    assert '.post("/auth/login")' in code
    assert 'expect(step1.status).toBe(200);' in code
    assert 'expect(step1.body).toHaveProperty("token");' in code


def test_render_mocha_supertest_generates_api_script() -> None:
    code = renderers.render_script(framework=GeneratedTestFramework.MOCHA_SUPERTEST, test_case=_test_case())

    assert 'import { expect } from "chai";' in code
    assert '.post("/auth/login")' in code
    assert 'expect(step1.status).to.equal(200);' in code
    assert 'expect(step1.body).to.have.property("token");' in code


def test_write_generated_file_uses_sanitized_framework_directory(tmp_path, monkeypatch) -> None:
    project_root = tmp_path / "logitest-ai"
    generated_root = project_root / "generated-tests"
    monkeypatch.setattr(renderers, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(renderers, "GENERATED_TESTS_ROOT", generated_root)

    file_path = renderers.write_generated_file(
        framework=GeneratedTestFramework.PLAYWRIGHT_API,
        test_case_name="API test - Successful buyer checkout",
        code="test code",
    )

    assert file_path == "generated-tests/playwright/api-test-successful-buyer-checkout.spec.ts"
    assert (generated_root / "playwright" / "api-test-successful-buyer-checkout.spec.ts").read_text(encoding="utf-8") == "test code"


def _test_case() -> dict:
    return {
        "name": "API test - Successful buyer checkout",
        "steps": [
            {
                "order": 1,
                "method": "POST",
                "endpoint": "/auth/login",
                "request_payload": {"email": "user@example.com"},
                "expected_status": 200,
                "golden_response": {"token": "abc"},
            },
            {
                "order": 2,
                "method": "GET",
                "endpoint": "/products",
                "request_payload": {},
                "expected_status": 200,
                "golden_response": {"items": []},
            },
        ],
    }
