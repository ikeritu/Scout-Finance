"""
Structured Equity Research v0.2.

This module runs one real OpenAI analysis for the top-ranked company using
a richer equity-research-style schema.

Design goals:
- Do not rewrite the project.
- Do not change database schema.
- Do not touch Streamlit yet.
- Store the full structured report in openai_analysis.raw_response_json.
- Map only key fields to the existing openai_analysis columns.
- Keep cost control.
- Recommended first use: top 1 company only.

Run:
    python -m src.openai_equity_research_v2
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from config import get_paths
from src.database import get_connection
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
    summarize_persisted_openai_analysis,
    update_run_openai_count,
)
from src.results import get_latest_run_id, get_top_signals_enriched, load_openai_analysis


PROMPT_VERSION_V2 = "v0.2"
SCHEMA_VERSION_V2 = "v0.2"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH_V2 = PROJECT_ROOT / "prompts" / "openai_analysis_v0_2.txt"


def _env_float(name: str, default: float = 0.0) -> float:
    """
    Read float value from environment variables.
    """

    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return float(value)
    except ValueError:
        return default


def make_json_safe(value: Any) -> Any:
    """
    Convert pandas/numpy values into JSON-serializable Python values.
    """

    if value is None:
        return None

    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]

    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except Exception:
            return str(value)

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


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

    return str(response)


def load_prompt_v2() -> str:
    """
    Load the structured equity research prompt.
    """

    if not PROMPT_PATH_V2.exists():
        raise FileNotFoundError(
            f"Prompt not found: {PROMPT_PATH_V2}. "
            "Copy openai_analysis_v0_2.txt into the prompts folder first."
        )

    return PROMPT_PATH_V2.read_text(encoding="utf-8")


def build_company_input(row: pd.Series) -> dict[str, Any]:
    """
    Build compact but rich company input from an enriched signal row.
    """

    fields = [
        "ticker",
        "company_name",
        "sector",
        "industry",
        "exchange",
        "currency",
        "price_at_signal",
        "price",
        "previous_close",
        "volume",
        "avg_volume_50d",
        "relative_volume",
        "change_1d",
        "change_5d",
        "change_20d",
        "ma20",
        "ma50",
        "above_ma20",
        "above_ma50",
        "high_52w",
        "low_52w",
        "distance_to_52w_high",
        "distance_to_52w_low",
        "market_cap",
        "data_source",
        "data_quality_score",
        "data_quality_label",
        "score_volume",
        "score_momentum",
        "score_liquidity",
        "score_context",
        "score_raw",
        "score_adjusted",
        "score_priority",
        "score_confidence",
        "score_risk",
        "category_final",
        "opportunity_phase",
        "reason_to_pass_quant",
        "missing_key_data_quant",
        "scoring_version",
    ]

    company_input = {field: row.get(field) for field in fields if field in row.index}
    company_input["prompt_version"] = PROMPT_VERSION_V2
    company_input["schema_version"] = SCHEMA_VERSION_V2

    return make_json_safe(company_input)


def build_input_text(prompt: str, company_input: dict[str, Any]) -> str:
    """
    Build final input text for OpenAI.
    """

    return (
        f"{prompt}\n\n"
        "COMPANY_INPUT:\n"
        f"{json.dumps(company_input, indent=2, ensure_ascii=False)}\n\n"
        "Return only the JSON object."
    )


def parse_response_json(response_text: str) -> dict[str, Any]:
    """
    Parse OpenAI text as JSON.
    """

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"OpenAI response was not valid JSON: {exc}\n{response_text}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("OpenAI response JSON must be an object.")

    return parsed


def _get_nested(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    """
    Safely read nested dictionary values.
    """

    current: Any = data

    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)

    return current if current is not None else default


def validate_structured_report(report: dict[str, Any]) -> list[str]:
    """
    Validate the main expected v0.2 fields.
    """

    required_fields = [
        "schema_version",
        "analysis_type",
        "ticker",
        "company_name",
        "executive_summary",
        "facts_interpretation_hypotheses",
        "business_model",
        "financial_health",
        "moat_competitive_advantage",
        "valuation",
        "risks",
        "catalysts",
        "scenarios",
        "watchlist_signals_next_quarters",
        "module_scores",
        "missing_data",
        "data_to_verify",
        "prudent_conclusion",
        "markdown_report",
    ]

    errors: list[str] = []

    for field in required_fields:
        if field not in report:
            errors.append(f"missing_field:{field}")

    if report.get("schema_version") != SCHEMA_VERSION_V2:
        errors.append("unexpected_schema_version")

    if not isinstance(report.get("risks", []), list):
        errors.append("risks_must_be_list")

    if not isinstance(report.get("missing_data", []), list):
        errors.append("missing_data_must_be_list")

    return errors


def report_to_openai_analysis_payload(
    report: dict[str, Any],
    signal_id: int,
    run_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: float,
) -> dict[str, Any]:
    """
    Map v0.2 structured report to existing openai_analysis table columns.

    Full report is stored in raw_response_json.
    """

    validation_errors = validate_structured_report(report)

    summary = _get_nested(report, ["executive_summary", "summary"])
    research_priority = _get_nested(report, ["executive_summary", "initial_research_priority"])
    conclusion = _get_nested(report, ["prudent_conclusion", "conclusion"])
    research_action = _get_nested(report, ["prudent_conclusion", "research_action"])
    confidence = _get_nested(report, ["prudent_conclusion", "confidence_level"])
    hype_risk = _get_nested(report, ["prudent_conclusion", "hype_risk"])

    missing_data = report.get("missing_data", [])
    data_to_verify = report.get("data_to_verify", [])

    reason_to_pass = conclusion or summary
    if validation_errors:
        reason_to_pass = f"{reason_to_pass or ''} | validation_warnings: {validation_errors}".strip(" |")

    facts_block = report.get("facts_interpretation_hypotheses", {})
    facts = facts_block.get("facts", []) if isinstance(facts_block, dict) else []
    interpretations = facts_block.get("interpretations", []) if isinstance(facts_block, dict) else []
    hypotheses = facts_block.get("hypotheses", []) if isinstance(facts_block, dict) else []

    return {
        "signal_id": signal_id,
        "run_id": run_id,
        "ticker": report.get("ticker"),
        "model": model,
        "prompt_version": PROMPT_VERSION_V2,
        "schema_version": SCHEMA_VERSION_V2,
        "summary_thesis": summary,
        "opportunity_type": report.get("analysis_type"),
        "opportunity_phase": research_action,
        "suggested_category": research_priority,
        "confidence_level": confidence,
        "hype_risk": hype_risk,
        "source_quality": _get_nested(report, ["executive_summary", "confidence"]),
        "reason_to_pass": reason_to_pass,
        "missing_key_data": json.dumps(make_json_safe(missing_data), ensure_ascii=False),
        "event_to_confirm": json.dumps(make_json_safe(report.get("catalysts", [])), ensure_ascii=False),
        "source_to_verify": json.dumps(make_json_safe(data_to_verify), ensure_ascii=False),
        "verifiable_facts_json": json.dumps(make_json_safe(facts), ensure_ascii=False),
        "reasonable_inferences_json": json.dumps(make_json_safe(interpretations), ensure_ascii=False),
        "speculative_elements_json": json.dumps(make_json_safe(hypotheses), ensure_ascii=False),
        "contradictions_json": json.dumps([], ensure_ascii=False),
        "checklist_json": json.dumps(make_json_safe(report.get("watchlist_signals_next_quarters", [])), ensure_ascii=False),
        "why_it_could_work": _get_nested(report, ["scenarios", "bull", "description"]),
        "why_it_could_fail": _get_nested(report, ["scenarios", "bear", "description"]),
        "discrepancy_with_python": json.dumps(make_json_safe(report.get("module_scores", {})), ensure_ascii=False),
        "raw_response_json": json.dumps(make_json_safe(report), ensure_ascii=False),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "cache_hit": 0,
    }


def analyze_top1_structured(mode: str = "demo") -> dict[str, Any]:
    """
    Run a real structured v0.2 analysis for the top-ranked company.
    """

    validate_company_limit(1)
    validate_openai_ready(use_strong_model=False)

    run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        raise ValueError("No runs found. Execute python -m src.pipeline first.")

    top_df = get_top_signals_enriched(run_id=run_id, mode=mode, top_n=1)

    if top_df.empty:
        raise ValueError("No signals found for latest run.")

    row = top_df.iloc[0]
    signal_id = int(row["id"])
    ticker = str(row["ticker"])
    company_name = str(row.get("company_name") or "")

    prompt = load_prompt_v2()
    company_input = build_company_input(row)
    input_text = build_input_text(prompt, company_input)

    model = get_selected_model(use_strong_model=False)
    client = get_openai_client(use_strong_model=False)

    response = client.responses.create(
        model=model,
        input=input_text,
        text={
            "format": {
                "type": "json_object",
            }
        },
    )

    response_text = _extract_response_text(response)
    report = parse_response_json(response_text)

    usage = getattr(response, "usage", None)
    input_tokens = _get_usage_value(usage, "input_tokens", "prompt_tokens")
    output_tokens = _get_usage_value(usage, "output_tokens", "completion_tokens")

    estimated_cost = estimate_request_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_per_1m=_env_float("OPENAI_INPUT_COST_PER_1M", 0.0),
        output_cost_per_1m=_env_float("OPENAI_OUTPUT_COST_PER_1M", 0.0),
    )

    validate_budget(
        estimated_cost=estimated_cost,
        spent_today=0.0,
        spent_this_month=0.0,
    )

    payload = report_to_openai_analysis_payload(
        report=report,
        signal_id=signal_id,
        run_id=run_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=estimated_cost,
    )

    db_path = get_paths(mode)["db_path"]

    with get_connection(db_path) as conn:
        analysis_id = insert_openai_analysis(conn, payload)
        cost_id = insert_cost_log(conn, payload)
        openai_analyzed_companies = update_run_openai_count(conn, run_id)
        conn.commit()

    return {
        "run_id": run_id,
        "mode": mode,
        "signal_id": signal_id,
        "ticker": ticker,
        "company_name": company_name,
        "model": model,
        "analysis_id": analysis_id,
        "cost_id": cost_id,
        "openai_analyzed_companies": openai_analyzed_companies,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "schema_version": SCHEMA_VERSION_V2,
        "prompt_version": PROMPT_VERSION_V2,
        "executive_summary": _get_nested(report, ["executive_summary", "summary"]),
        "research_action": _get_nested(report, ["prudent_conclusion", "research_action"]),
        "confidence_level": _get_nested(report, ["prudent_conclusion", "confidence_level"]),
        "hype_risk": _get_nested(report, ["prudent_conclusion", "hype_risk"]),
        "overall_research_score": _get_nested(report, ["module_scores", "overall_research_score"]),
        "validation_errors": validate_structured_report(report),
        "markdown_report_preview": str(report.get("markdown_report", ""))[:1000],
    }


if __name__ == "__main__":
    mode = "demo"

    print("Structured Equity Research v0.2")
    print("================================")

    status = get_openai_status()

    print("\nConfiguration:")
    for key, value in status.items():
        print(f"- {key}: {value}")

    print("\nRunning structured top-1 analysis...")

    summary = analyze_top1_structured(mode=mode)

    print("\nPersistence summary:")
    for key, value in summary.items():
        if key != "markdown_report_preview":
            print(f"- {key}: {value}")

    print("\nMarkdown report preview:")
    print(summary["markdown_report_preview"])

    print("\nPersisted analysis summary:")
    persisted_summary = summarize_persisted_openai_analysis(
        run_id=summary["run_id"],
        mode=mode,
    )

    for key, value in persisted_summary.items():
        print(f"- {key}: {value}")

    print("\nLatest OpenAI analysis rows:")
    analysis_df = load_openai_analysis(run_id=summary["run_id"], mode=mode)
    if analysis_df.empty:
        print("No OpenAI analysis rows found.")
    else:
        columns_to_show = [
            "id",
            "signal_id",
            "ticker",
            "model",
            "prompt_version",
            "schema_version",
            "summary_thesis",
            "suggested_category",
            "hype_risk",
            "confidence_level",
            "input_tokens",
            "output_tokens",
            "estimated_cost",
        ]
        available_columns = [column for column in columns_to_show if column in analysis_df.columns]
        print(analysis_df[available_columns].head(10).to_string(index=False))
