"""
OpenAI smoke test module.

This module performs a minimal real OpenAI API connectivity test.

Purpose:
- Validate OPENAI_API_KEY.
- Validate configured model availability.
- Make one tiny JSON response request.
- Print token usage when available.
- Estimate cost using .env rates.
- Do not touch SQLite.
- Do not analyze companies.
- Do not modify project data.

Recommended use:
1. Set ENABLE_OPENAI=true in .env.
2. Set a real OPENAI_API_KEY.
3. Keep MAX_OPENAI_COMPANIES_PER_RUN=1.
4. Run:

   python -m src.openai_smoke_test

If ENABLE_OPENAI=false, this module exits safely without calling the API.
"""

from __future__ import annotations

import json
import os
from typing import Any

from src.openai_client import (
    OpenAIConfigurationError,
    OpenAIDisabledError,
    estimate_request_cost,
    get_openai_client,
    get_openai_status,
    get_selected_model,
    safe_client_check,
    validate_openai_ready,
)


def _env_float(name: str, default: float = 0.0) -> float:
    """
    Read float from environment variables.
    """

    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return float(value)
    except ValueError:
        return default


def _get_usage_value(usage: Any, *names: str) -> int:
    """
    Safely read usage fields from OpenAI SDK response objects or dictionaries.
    """

    if usage is None:
        return 0

    for name in names:
        if isinstance(usage, dict) and name in usage:
            return int(usage.get(name) or 0)

        if hasattr(usage, name):
            return int(getattr(usage, name) or 0)

    return 0


def _extract_response_text(response: Any) -> str:
    """
    Extract text from a Responses API response.
    """

    if hasattr(response, "output_text") and response.output_text:
        return str(response.output_text)

    if isinstance(response, dict) and response.get("output_text"):
        return str(response["output_text"])

    try:
        return str(response)
    except Exception:
        return ""


def run_smoke_test(use_strong_model: bool = False) -> dict[str, Any]:
    """
    Run a minimal OpenAI API smoke test.
    """

    status = get_openai_status()
    readiness = safe_client_check(use_strong_model=use_strong_model)

    if not readiness["ready"]:
        return {
            "ok": False,
            "called_api": False,
            "reason": readiness["message"],
            "status": status,
            "response_text": None,
            "parsed_json": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0.0,
        }

    model = get_selected_model(use_strong_model=use_strong_model)

    validate_openai_ready(use_strong_model=use_strong_model)
    client = get_openai_client(use_strong_model=use_strong_model)

    prompt = (
        "Return only valid JSON with exactly these keys: "
        "status, message. "
        "Use status='ok' and message='OpenAI smoke test successful'."
    )

    response = client.responses.create(
        model=model,
        input=prompt,
        text={
            "format": {
                "type": "json_object",
            }
        },
    )

    response_text = _extract_response_text(response)

    try:
        parsed_json = json.loads(response_text)
    except json.JSONDecodeError:
        parsed_json = None

    usage = getattr(response, "usage", None)

    input_tokens = _get_usage_value(
        usage,
        "input_tokens",
        "prompt_tokens",
    )
    output_tokens = _get_usage_value(
        usage,
        "output_tokens",
        "completion_tokens",
    )

    estimated_cost = estimate_request_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_per_1m=_env_float("OPENAI_INPUT_COST_PER_1M", 0.0),
        output_cost_per_1m=_env_float("OPENAI_OUTPUT_COST_PER_1M", 0.0),
    )

    return {
        "ok": parsed_json is not None and parsed_json.get("status") == "ok",
        "called_api": True,
        "reason": None,
        "status": status,
        "model": model,
        "response_text": response_text,
        "parsed_json": parsed_json,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
    }


if __name__ == "__main__":
    print("OpenAI smoke test")
    print("=================")

    status = get_openai_status()

    print("\nConfiguration:")
    for key, value in status.items():
        if (
            key in {"api_key_defined", "api_key_looks_placeholder"}
            or "budget" in key
            or "model" in key
            or "enable" in key
            or "companies" in key
        ):
            print(f"- {key}: {value}")

    print("\nReadiness:")
    readiness = safe_client_check(use_strong_model=False)
    for key, value in readiness.items():
        print(f"- {key}: {value}")

    if not readiness["ready"]:
        print("\nNo API call was made.")
        print("Fix .env first, then run this command again.")
        raise SystemExit(0)

    print("\nCalling OpenAI API with a minimal JSON request...")

    try:
        result = run_smoke_test(use_strong_model=False)
    except (OpenAIDisabledError, OpenAIConfigurationError) as exc:
        print(f"\nOpenAI configuration error: {exc}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"\nOpenAI smoke test failed: {exc}")
        raise SystemExit(1)

    print("\nSmoke test result:")
    print(f"- ok: {result['ok']}")
    print(f"- called_api: {result['called_api']}")
    print(f"- model: {result.get('model')}")
    print(f"- input_tokens: {result['input_tokens']}")
    print(f"- output_tokens: {result['output_tokens']}")
    print(f"- estimated_cost: ${result['estimated_cost']:.6f}")

    print("\nResponse text:")
    print(result["response_text"])

    print("\nParsed JSON:")
    print(json.dumps(result["parsed_json"], indent=2, ensure_ascii=False))

    if result["ok"]:
        print("\nSmoke test completed successfully.")
    else:
        print("\nSmoke test completed, but response JSON did not match the expected shape.")
