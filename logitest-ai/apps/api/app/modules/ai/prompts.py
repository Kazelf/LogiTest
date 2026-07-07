from __future__ import annotations

import json
from typing import Any

PROMPT_VERSION = "behavior-explanation-v1"

def build_behavior_explanation_prompt(journey_name: str, steps: list[dict[str, Any]]) -> str:
    payload = {
        "journeyName": journey_name,
        "steps": steps,
        "requiredOutput": {
            "behaviorName": "short name",
            "behaviorType": "normal | abnormal | error",
            "userGoal": "what the user is doing",
            "stepSummary": [
                {
                    "step": 1,
                    "api": "METHOD /path",
                    "meaning": "business meaning",
                    "importantPayload": ["field"],
                    "importantResponse": ["field"],
                    "inputFromPreviousStep": "optional chaining explanation",
                }
            ],
            "chaining": [
                {
                    "fromStep": 1,
                    "fromPath": "$.order_id",
                    "toStep": 2,
                    "toPath": "path parameter /orders/{order_id}",
                }
            ],
            "riskNotes": ["why regression matters"],
        },
    }
    return (
        "You explain API behavior for a regression-testing demo. "
        "Return only valid JSON with the requiredOutput shape. "
        "Do not decide pass/fail. Deterministic code decides pass/fail. "
        "Classify behaviorType as normal, abnormal, or error based on status codes and action names.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )
