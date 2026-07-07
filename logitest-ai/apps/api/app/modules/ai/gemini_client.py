from __future__ import annotations

import json
from typing import Any

from app.core.settings import settings
from app.modules.ai.prompts import PROMPT_VERSION, build_behavior_explanation_prompt

def gemini_available() -> bool:
    return bool(_api_key()) and settings.ai_provider.lower() == "gemini"

def generate_behavior_explanation(journey_name: str, steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    api_key = _api_key()
    if not api_key or settings.ai_provider.lower() != "gemini":
        return None
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=build_behavior_explanation_prompt(journey_name, steps),
        )
        parsed = _parse_json(response.text or "")
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        if settings.ai_fallback_rule_based:
            return None
        raise

def metadata(*, fallback_used: bool) -> dict[str, Any]:
    return {
        "ai_provider": "gemini" if gemini_available() and not fallback_used else "rule_based",
        "ai_model": settings.gemini_model if gemini_available() and not fallback_used else None,
        "fallback_used": fallback_used,
        "prompt_version": PROMPT_VERSION,
    }

def _api_key() -> str | None:
    return settings.gemini_api_key or settings.google_api_key

def _parse_json(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return json.loads(stripped)
