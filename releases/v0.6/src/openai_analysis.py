"""
OpenAI analysis module.

This module prepares the future company analysis layer powered by OpenAI.

Current scope:
- Build structured input for one company using enriched signal context.
- Load prompt templates from /prompts.
- Define the expected analysis schema.
- Validate and normalize analysis responses.
- Provide safe disabled behavior when ENABLE_OPENAI=false.
- Provide a placeholder analysis workflow without making API calls by default.

Not included in this phase:
- Real OpenAI API calls.
- News retrieval.
- Web search.
- Streamlit UI.
- Database writes to openai_analysis.
- Cost logging.
- Prompt optimization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config import PROMPT_VERSION, SCHEMA_VERSION
from src.openai_client import (
    disabled_response,
    get_openai_status,
    get_selected_model,
    is_openai_enabled,
    validate_company_limit,
)
from src.results import get_latest_run_id, get_top_signals_enriched


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PROJECT_ROOT / "prompts"

DEFAULT_ANALYSIS_PROMPT = PROMPTS_DIR / "openai_analysis_v0_1.txt"
DEFAULT_ANTI_HYPE_PROMPT = PROMPTS_DIR / "anti_hype_v0_1.txt"
DEFAULT_NEWS_CLASSIFIER_PROMPT = PROMPTS_DIR / "news_classifier_v0_1.txt"


EXPECTED_ANALYSIS_FIELDS = [
    "summary_thesis",
    "opportunity_type",
    "opportunity_phase",
    "suggested_category",
    "confidence_level",
    "hype_risk",
    "source_quality",
    "reason_to_pass",
    "missing_key_data",
    "event_to_confirm",
    "source_to_verify",
    "verifiable_facts",
    "reasonable_inferences",
    "speculative_elements",
    "contradictions",
    "checklist",
    "why_it_could_work",
    "why_it_could_fail",
    "discrepancy_with_python",
]


LIST_FIELDS = [
    "verifiable_facts",
    "reasonable_inferences",
    "speculative_elements",
    "contradictions",
    "checklist",
]


def load_prompt_template(prompt_path: str | Path) -> str:
    """
    Load a prompt template from disk.

    Parameters
    ----------
    prompt_path:
        Path to prompt file.

    Returns
    -------
    str
        Prompt text.

    Raises
    ------
    FileNotFoundError
        If the prompt file does not exist.
    """

    path = Path(prompt_path)

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    return path.read_text(encoding="utf-8")


def load_default_prompts() -> dict[str, str]:
    """
    Load default prompt templates.

    Returns
    -------
    dict[str, str]
        Prompt templates by name.
    """

    prompts: dict[str, str] = {}

    prompt_files = {
        "openai_analysis": DEFAULT_ANALYSIS_PROMPT,
        "anti_hype": DEFAULT_ANTI_HYPE_PROMPT,
        "news_classifier": DEFAULT_NEWS_CLASSIFIER_PROMPT,
    }

    for name, path in prompt_files.items():
        if path.exists():
            prompts[name] = load_prompt_template(path)
        else:
            prompts[name] = ""

    return prompts


def _row_get(row: pd.Series | dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a pandas Series or dictionary.
    """

    try:
        value = row.get(key, default)
    except AttributeError:
        return default

    return value


def build_company_analysis_input(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    """
    Build structured input for future OpenAI company analysis.

    This function expects an enriched signal row from get_top_signals_enriched(),
    but it also tolerates plain signal rows by returning None for missing fields.

    Parameters
    ----------
    row:
        One enriched signal row.

    Returns
    -------
    dict
        Compact company context.
    """

    return {
        "ticker": _row_get(row, "ticker"),
        "company_name": _row_get(row, "company_name"),
        "sector": _row_get(row, "sector"),
        "industry": _row_get(row, "industry"),
        "exchange": _row_get(row, "exchange"),
        "currency": _row_get(row, "currency"),
        "price_at_signal": _row_get(row, "price_at_signal", _row_get(row, "price")),
        "current_snapshot_price": _row_get(row, "price"),
        "previous_close": _row_get(row, "previous_close"),
        "volume": _row_get(row, "volume"),
        "avg_volume_50d": _row_get(row, "avg_volume_50d"),
        "relative_volume": _row_get(row, "relative_volume"),
        "change_1d": _row_get(row, "change_1d"),
        "change_5d": _row_get(row, "change_5d"),
        "change_20d": _row_get(row, "change_20d"),
        "ma20": _row_get(row, "ma20"),
        "ma50": _row_get(row, "ma50"),
        "above_ma20": _row_get(row, "above_ma20"),
        "above_ma50": _row_get(row, "above_ma50"),
        "high_52w": _row_get(row, "high_52w"),
        "low_52w": _row_get(row, "low_52w"),
        "distance_to_52w_high": _row_get(row, "distance_to_52w_high"),
        "distance_to_52w_low": _row_get(row, "distance_to_52w_low"),
        "market_cap": _row_get(row, "market_cap"),
        "data_source": _row_get(row, "data_source"),
        "data_quality_score": _row_get(row, "data_quality_score"),
        "data_quality_label": _row_get(row, "data_quality_label"),
        "score_volume": _row_get(row, "score_volume"),
        "score_momentum": _row_get(row, "score_momentum"),
        "score_liquidity": _row_get(row, "score_liquidity"),
        "score_context": _row_get(row, "score_context"),
        "score_raw": _row_get(row, "score_raw"),
        "score_adjusted": _row_get(row, "score_adjusted"),
        "score_priority": _row_get(row, "score_priority"),
        "score_confidence": _row_get(row, "score_confidence"),
        "score_risk": _row_get(row, "score_risk"),
        "category_final": _row_get(row, "category_final"),
        "opportunity_phase": _row_get(row, "opportunity_phase"),
        "reason_to_pass_quant": _row_get(row, "reason_to_pass_quant"),
        "missing_key_data_quant": _row_get(row, "missing_key_data_quant"),
        "scoring_version": _row_get(row, "scoring_version"),
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
    }


def build_analysis_prompt_payload(company_input: dict[str, Any]) -> dict[str, Any]:
    """
    Build a structured prompt payload.

    This function does not call OpenAI. It only prepares the future payload.

    Parameters
    ----------
    company_input:
        Structured company input.

    Returns
    -------
    dict
        Prompt payload.
    """

    prompts = load_default_prompts()

    return {
        "system_prompt": prompts.get("openai_analysis", ""),
        "anti_hype_prompt": prompts.get("anti_hype", ""),
        "news_classifier_prompt": prompts.get("news_classifier", ""),
        "company_input": company_input,
        "expected_output_fields": EXPECTED_ANALYSIS_FIELDS,
        "instructions": {
            "do_not_recommend_buy_or_sell": True,
            "focus": "prioritize companies for human equity research review",
            "separate_facts_inferences_and_speculation": True,
            "flag_missing_data": True,
            "flag_hype_risk": True,
        },
    }


def empty_analysis_result(
    ticker: str | None = None,
    reason: str = "OpenAI analysis not executed.",
) -> dict[str, Any]:
    """
    Return an empty normalized analysis result.

    Parameters
    ----------
    ticker:
        Optional ticker.
    reason:
        Reason why analysis is empty.

    Returns
    -------
    dict
        Empty analysis result matching the expected shape.
    """

    result: dict[str, Any] = {
        "ticker": ticker,
        "model": None,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "summary_thesis": None,
        "opportunity_type": None,
        "opportunity_phase": None,
        "suggested_category": None,
        "confidence_level": None,
        "hype_risk": None,
        "source_quality": None,
        "reason_to_pass": reason,
        "missing_key_data": None,
        "event_to_confirm": None,
        "source_to_verify": None,
        "verifiable_facts": [],
        "reasonable_inferences": [],
        "speculative_elements": [],
        "contradictions": [],
        "checklist": [],
        "why_it_could_work": None,
        "why_it_could_fail": None,
        "discrepancy_with_python": None,
        "raw_response": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost": 0.0,
        "cache_hit": False,
        "analysis_executed": False,
    }

    return result


def normalize_analysis_response(
    response: dict[str, Any] | str | None,
    ticker: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Normalize a response into the expected analysis shape.

    Parameters
    ----------
    response:
        Response dictionary, JSON string or None.
    ticker:
        Optional ticker.
    model:
        Optional model name.

    Returns
    -------
    dict
        Normalized analysis result.
    """

    if response is None:
        return empty_analysis_result(ticker=ticker, reason="No response provided.")

    if isinstance(response, str):
        try:
            parsed_response = json.loads(response)
        except json.JSONDecodeError:
            result = empty_analysis_result(
                ticker=ticker,
                reason="Response was not valid JSON.",
            )
            result["raw_response"] = response
            return result
    elif isinstance(response, dict):
        parsed_response = response
    else:
        result = empty_analysis_result(
            ticker=ticker,
            reason=f"Unsupported response type: {type(response).__name__}",
        )
        result["raw_response"] = str(response)
        return result

    result = empty_analysis_result(ticker=ticker, reason="")

    for field in EXPECTED_ANALYSIS_FIELDS:
        value = parsed_response.get(field)

        if field in LIST_FIELDS:
            if value is None:
                value = []
            elif isinstance(value, list):
                value = value
            else:
                value = [str(value)]

        result[field] = value

    result["ticker"] = ticker or parsed_response.get("ticker")
    result["model"] = model
    result["raw_response"] = parsed_response
    result["analysis_executed"] = True

    return result


def validate_analysis_result(result: dict[str, Any]) -> list[str]:
    """
    Validate a normalized analysis result.

    Returns a list of validation errors. Empty list means valid enough.

    Parameters
    ----------
    result:
        Normalized result.

    Returns
    -------
    list[str]
        Validation errors.
    """

    errors: list[str] = []

    for field in EXPECTED_ANALYSIS_FIELDS:
        if field not in result:
            errors.append(f"missing_field:{field}")

    for field in LIST_FIELDS:
        if field in result and not isinstance(result[field], list):
            errors.append(f"field_must_be_list:{field}")

    if result.get("summary_thesis") is None and result.get("analysis_executed"):
        errors.append("missing_summary_thesis")

    return errors


def result_to_database_payload(
    result: dict[str, Any],
    signal_id: int | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Convert normalized analysis result to a future database payload.

    This function does not write to SQLite.

    Parameters
    ----------
    result:
        Normalized analysis result.
    signal_id:
        Optional signal id.
    run_id:
        Optional run id.

    Returns
    -------
    dict
        Payload aligned with openai_analysis table columns.
    """

    return {
        "signal_id": signal_id,
        "run_id": run_id,
        "ticker": result.get("ticker"),
        "model": result.get("model"),
        "prompt_version": result.get("prompt_version", PROMPT_VERSION),
        "schema_version": result.get("schema_version", SCHEMA_VERSION),
        "summary_thesis": result.get("summary_thesis"),
        "opportunity_type": result.get("opportunity_type"),
        "opportunity_phase": result.get("opportunity_phase"),
        "suggested_category": result.get("suggested_category"),
        "confidence_level": result.get("confidence_level"),
        "hype_risk": result.get("hype_risk"),
        "source_quality": result.get("source_quality"),
        "reason_to_pass": result.get("reason_to_pass"),
        "missing_key_data": result.get("missing_key_data"),
        "event_to_confirm": result.get("event_to_confirm"),
        "source_to_verify": result.get("source_to_verify"),
        "verifiable_facts_json": json.dumps(
            result.get("verifiable_facts", []),
            ensure_ascii=False,
        ),
        "reasonable_inferences_json": json.dumps(
            result.get("reasonable_inferences", []),
            ensure_ascii=False,
        ),
        "speculative_elements_json": json.dumps(
            result.get("speculative_elements", []),
            ensure_ascii=False,
        ),
        "contradictions_json": json.dumps(
            result.get("contradictions", []),
            ensure_ascii=False,
        ),
        "checklist_json": json.dumps(
            result.get("checklist", []),
            ensure_ascii=False,
        ),
        "why_it_could_work": result.get("why_it_could_work"),
        "why_it_could_fail": result.get("why_it_could_fail"),
        "discrepancy_with_python": result.get("discrepancy_with_python"),
        "raw_response_json": json.dumps(
            result.get("raw_response"),
            ensure_ascii=False,
        ),
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
        "estimated_cost": result.get("estimated_cost", 0.0),
        "cache_hit": int(bool(result.get("cache_hit", False))),
    }


def analyze_company_placeholder(
    row: pd.Series | dict[str, Any],
    use_strong_model: bool = False,
) -> dict[str, Any]:
    """
    Placeholder company analysis.

    If OpenAI is disabled, returns a safe disabled result.
    If OpenAI is enabled, this still does not call the API in this phase.

    Parameters
    ----------
    row:
        Enriched signal row.
    use_strong_model:
        Whether strong model would be requested in a future phase.

    Returns
    -------
    dict
        Normalized placeholder result.
    """

    company_input = build_company_analysis_input(row)
    ticker = company_input.get("ticker")
    model = get_selected_model(use_strong_model=use_strong_model)

    if not is_openai_enabled():
        disabled = disabled_response("ENABLE_OPENAI=false. Analysis skipped.")
        result = empty_analysis_result(
            ticker=ticker,
            reason=disabled["reason"],
        )
        result["model"] = model
        result["cache_hit"] = disabled["cache_hit"]
        return result

    # Deliberately do not call OpenAI yet.
    result = empty_analysis_result(
        ticker=ticker,
        reason="OpenAI is enabled, but real calls are not implemented in this phase.",
    )
    result["model"] = model

    return result


def analyze_top_companies_placeholder(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = 5,
    use_strong_model: bool = False,
) -> list[dict[str, Any]]:
    """
    Run placeholder analysis for top enriched companies.

    This function validates the company limit and returns disabled/placeholder
    results without calling OpenAI.
    """

    validate_company_limit(top_n)

    top_df = get_top_signals_enriched(
        run_id=run_id,
        mode=mode,
        top_n=top_n,
    )

    results: list[dict[str, Any]] = []

    for _, row in top_df.iterrows():
        results.append(
            analyze_company_placeholder(
                row,
                use_strong_model=use_strong_model,
            )
        )

    return results


def summarize_analysis_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Summarize placeholder or future OpenAI analysis results.
    """

    if not results:
        return {
            "total_results": 0,
            "executed": 0,
            "skipped": 0,
            "estimated_cost": 0.0,
            "tickers": [],
        }

    executed = sum(1 for result in results if result.get("analysis_executed"))
    estimated_cost = sum(float(result.get("estimated_cost") or 0.0) for result in results)

    return {
        "total_results": len(results),
        "executed": executed,
        "skipped": len(results) - executed,
        "estimated_cost": round(estimated_cost, 6),
        "tickers": [result.get("ticker") for result in results],
    }


if __name__ == "__main__":
    mode = "demo"
    latest_run_id = get_latest_run_id(mode=mode)

    print("OpenAI configuration status:")
    status = get_openai_status()
    for key, value in status.items():
        print(f"- {key}: {value}")

    if latest_run_id is None:
        raise SystemExit("No runs found. Execute python -m src.pipeline first.")

    print(f"\nLatest run: {latest_run_id}")

    top_df = get_top_signals_enriched(
        run_id=latest_run_id,
        mode=mode,
        top_n=3,
    )

    print("\nTop enriched companies selected for placeholder analysis:")
    if top_df.empty:
        print("No enriched signals found.")
    else:
        columns_to_show = [
            "id",
            "ticker",
            "company_name",
            "sector",
            "industry",
            "market_cap",
            "relative_volume",
            "change_5d",
            "score_priority",
            "category_final",
        ]
        available_columns = [column for column in columns_to_show if column in top_df.columns]
        print(top_df[available_columns].to_string(index=False))

    print("\nPrompt payload preview for first company:")
    if not top_df.empty:
        first_row = top_df.iloc[0]
        company_input = build_company_analysis_input(first_row)
        prompt_payload = build_analysis_prompt_payload(company_input)

        print(json.dumps(
            {
                "company_input": prompt_payload["company_input"],
                "expected_output_fields": prompt_payload["expected_output_fields"],
                "instructions": prompt_payload["instructions"],
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        ))

    print("\nRunning placeholder analysis:")
    results = analyze_top_companies_placeholder(
        run_id=latest_run_id,
        mode=mode,
        top_n=3,
        use_strong_model=False,
    )

    summary = summarize_analysis_results(results)

    for key, value in summary.items():
        print(f"- {key}: {value}")

    print("\nFirst placeholder result:")
    if results:
        print(json.dumps(results[0], indent=2, ensure_ascii=False, default=str))

    print("\nDatabase payload preview:")
    if results and not top_df.empty:
        payload = result_to_database_payload(
            results[0],
            signal_id=int(top_df.iloc[0]["id"]),
            run_id=latest_run_id,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
