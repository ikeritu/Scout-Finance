"""
OpenAI real top-1 analysis runner.

This module makes one real OpenAI call for the top-ranked enriched signal
and persists the result into SQLite.

Safety design:
- Processes only top_n=1 by default.
- Requires ENABLE_OPENAI=true.
- Requires a real OPENAI_API_KEY.
- Uses the configured light model by default.
- Writes to openai_analysis and cost_log.
- Does not change scoring, market data or universe.

Run:
    python -m src.openai_real_top1
"""

from __future__ import annotations

from config import get_paths

import json
import os
from typing import Any

import pandas as pd

from src.openai_analysis import (
    EXPECTED_ANALYSIS_FIELDS,
    build_analysis_prompt_payload,
    build_company_analysis_input,
    normalize_analysis_response,
    result_to_database_payload,
    validate_analysis_result,
)
from src.openai_client import (
    estimate_request_cost,
    get_openai_client,
    get_openai_status,
    get_selected_model,
    validate_budget,
    validate_company_limit,
    validate_openai_ready,
)
from src.openai_persistence import (
    insert_cost_log,
    insert_openai_analysis,
    load_cost_log,
    load_openai_analysis,
    summarize_persisted_openai_analysis,
    update_run_openai_count,
)
from src.database import get_connection
from src.results import get_latest_run_id, get_top_signals_enriched


def make_json_safe(value):
    """
    Convert pandas/numpy values into JSON-serializable Python values.

    Important:
    - Handle containers before pd.isna().
    - pd.isna(list/array) can return multiple booleans and raise ambiguity errors.
    """

    if value is None:
        return None

    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]

    # Convert pandas/numpy scalar values to native Python values.
    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except Exception:
            return str(value)

    # Only call pd.isna on scalar-like values, not containers.
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


def _env_float(name: str, default: float = 0.0) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_usage_value(usage: Any, *names: str) -> int:
    if usage is None:
        return 0
    for name in names:
        if isinstance(usage, dict) and name in usage:
            return int(usage.get(name) or 0)
        if hasattr(usage, name):
            return int(getattr(usage, name) or 0)
    return 0


def _extract_response_text(response: Any) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return str(response.output_text)
    if isinstance(response, dict) and response.get("output_text"):
        return str(response["output_text"])
    return str(response)


def build_real_openai_input(row: pd.Series | dict[str, Any]) -> str:
    """
    Build the prompt text sent to OpenAI for a company row.
    """

    company_input = build_company_analysis_input(row)
    payload = build_analysis_prompt_payload(company_input)

    system_prompt = payload.get("system_prompt") or (
        "You are a senior equity research analyst. Return only valid JSON. "
        "Do not recommend buying, selling or holding."
    )
    anti_hype_prompt = payload.get("anti_hype_prompt") or (
        "Be skeptical. Flag hype, missing data, weak signals and speculation."
    )
    news_classifier_prompt = payload.get("news_classifier_prompt") or (
        "If no external news is provided, state that no catalyst has been verified."
    )

    prompt_payload = {
        "task": "Analyze this company as a candidate for human equity research review.",
        "strict_rules": [
            "Return only valid JSON.",
            "Do not include markdown.",
            "Do not recommend buy, sell or hold.",
            "Do not invent news, catalysts, sources or financial facts.",
            "Separate facts, inferences and speculation.",
            "Flag missing data and hype risk.",
        ],
        "expected_output_fields": EXPECTED_ANALYSIS_FIELDS,
        "company_input": company_input,
    }

    return (
        f"{system_prompt}\n\n"
        f"Anti-hype rules:\n{anti_hype_prompt}\n\n"
        f"News classification rules:\n{news_classifier_prompt}\n\n"
        "Input payload:\n"
        f"{json.dumps(make_json_safe(prompt_payload), indent=2, ensure_ascii=False)}"
    )


def analyze_row_with_openai(row: pd.Series | dict[str, Any], use_strong_model: bool = False) -> dict[str, Any]:
    """
    Make one real OpenAI call and return a normalized analysis result.
    """

    validate_openai_ready(use_strong_model=use_strong_model)

    model = get_selected_model(use_strong_model=use_strong_model)
    client = get_openai_client(use_strong_model=use_strong_model)
    company_input = build_company_analysis_input(row)
    ticker = company_input.get("ticker")
    input_text = build_real_openai_input(row)

    response = client.responses.create(
        model=model,
        input=input_text,
        text={"format": {"type": "json_object"}},
    )

    response_text = _extract_response_text(response)
    result = normalize_analysis_response(response_text, ticker=ticker, model=model)

    usage = getattr(response, "usage", None)
    input_tokens = _get_usage_value(usage, "input_tokens", "prompt_tokens")
    output_tokens = _get_usage_value(usage, "output_tokens", "completion_tokens")

    estimated_cost = estimate_request_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_per_1m=_env_float("OPENAI_INPUT_COST_PER_1M", 0.0),
        output_cost_per_1m=_env_float("OPENAI_OUTPUT_COST_PER_1M", 0.0),
    )

    validate_budget(estimated_cost=estimated_cost)

    result["ticker"] = ticker
    result["model"] = model
    result["input_tokens"] = input_tokens
    result["output_tokens"] = output_tokens
    result["estimated_cost"] = estimated_cost
    result["cache_hit"] = False
    result["analysis_executed"] = True

    validation_errors = validate_analysis_result(result)
    if validation_errors:
        existing = result.get("discrepancy_with_python") or ""
        result["discrepancy_with_python"] = (
            existing + f" | validation_warnings: {validation_errors}"
        ).strip(" |")

    return result


def persist_real_openai_top1(mode: str = "demo", run_id: str | None = None) -> dict[str, Any]:
    """
    Analyze only the top-ranked signal with real OpenAI and persist the result.
    """

    validate_company_limit(1)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        raise ValueError("No runs found. Execute python -m src.pipeline first.")

    top_df = get_top_signals_enriched(run_id=run_id, mode=mode, top_n=1)
    if top_df.empty:
        raise ValueError("No signals found for the latest run.")

    row = top_df.iloc[0]
    result = analyze_row_with_openai(row, use_strong_model=False)
    payload = result_to_database_payload(result, signal_id=int(row["id"]), run_id=run_id)

    db_path = get_paths(mode)["db_path"]

    with get_connection(db_path) as conn:
        analysis_id = insert_openai_analysis(conn, payload)
        cost_id = insert_cost_log(conn, payload)
        openai_count = update_run_openai_count(conn, run_id)
        conn.commit()

    return {
        "run_id": run_id,
        "mode": mode,
        "ticker": result.get("ticker"),
        "company_name": row.get("company_name"),
        "model": result.get("model"),
        "analysis_id": analysis_id,
        "cost_id": cost_id,
        "openai_analyzed_companies": openai_count,
        "input_tokens": result.get("input_tokens"),
        "output_tokens": result.get("output_tokens"),
        "estimated_cost": result.get("estimated_cost"),
        "summary_thesis": result.get("summary_thesis"),
        "suggested_category": result.get("suggested_category"),
        "hype_risk": result.get("hype_risk"),
        "confidence_level": result.get("confidence_level"),
    }


if __name__ == "__main__":
    mode = os.getenv("DEFAULT_MODE", "demo")

    print("OpenAI real top-1 analysis")
    print("==========================")

    status = get_openai_status()
    print("\nConfiguration:")
    for key, value in status.items():
        if (
            key in {"enable_openai", "api_key_defined", "api_key_looks_placeholder"}
            or "model" in key
            or "budget" in key
            or "companies" in key
        ):
            print(f"- {key}: {value}")

    print("\nRunning real top-1 analysis...")
    summary = persist_real_openai_top1(mode=mode)

    print("\nPersistence summary:")
    for key, value in summary.items():
        print(f"- {key}: {value}")

    print("\nPersisted analysis summary:")
    persisted_summary = summarize_persisted_openai_analysis(
        run_id=summary["run_id"],
        mode=mode,
    )
    for key, value in persisted_summary.items():
        print(f"- {key}: {value}")

    print("\nLatest OpenAI analysis rows:")
    analysis_df = load_openai_analysis(run_id=summary["run_id"], mode=mode)
    columns = [
        "id",
        "signal_id",
        "ticker",
        "model",
        "summary_thesis",
        "suggested_category",
        "hype_risk",
        "confidence_level",
        "input_tokens",
        "output_tokens",
        "estimated_cost",
    ]
    available_columns = [column for column in columns if column in analysis_df.columns]
    print(analysis_df[available_columns].head(5).to_string(index=False))

    print("\nLatest cost log rows:")
    cost_df = load_cost_log(run_id=summary["run_id"], mode=mode)
    columns = [
        "id",
        "signal_id",
        "ticker",
        "model",
        "purpose",
        "input_tokens",
        "output_tokens",
        "estimated_cost",
    ]
    available_columns = [column for column in columns if column in cost_df.columns]
    print(cost_df[available_columns].head(5).to_string(index=False))
