"""
Company Research Report mode.

Phase 2:
- Adds structured JSON fields in addition to the Markdown report.
- Validates required JSON fields before saving.
- Saves historical analysis only if the structure is valid.
- Stores full JSON in openai_analysis.raw_response_json.
- Maps key fields into existing openai_analysis columns.
- Keeps current cost control.
- Does not change database schema.
- Does not modify Streamlit.

Run:
    python -m src.company_research_report
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
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


ANALYSIS_MODE = "company_research_report"
PROMPT_VERSION = "company_report_v0.2"
SCHEMA_VERSION = "company_report_v0.2"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "prompts" / "company_research_report_v0_2.txt"

ALLOWED_FINAL_CATEGORIES = {
    "🟢 Interesante para investigar",
    "🟡 Mantener en vigilancia",
    "🔴 Descartar por ahora",
    "⚫ Datos insuficientes",
}

ALLOWED_CONFIDENCE_LEVELS = {"alto", "medio", "bajo"}

REQUIRED_FIELDS = [
    "ticker",
    "company_name",
    "sector",
    "analysis_date",
    "business_quality_score",
    "financial_health_score",
    "growth_score",
    "valuation_score",
    "risk_score",
    "moat_score",
    "confidence_score",
    "final_category",
    "confidence_level",
    "top_strengths",
    "top_risks",
    "bull_case",
    "base_case",
    "bear_case",
    "catalysts",
    "watchlist_metrics",
    "missing_data",
    "model_used",
    "estimated_cost_usd",
    "markdown_report",
]

SCORE_FIELDS = [
    "business_quality_score",
    "financial_health_score",
    "growth_score",
    "valuation_score",
    "risk_score",
    "moat_score",
    "confidence_score",
]

LIST_FIELDS = [
    "top_strengths",
    "top_risks",
    "catalysts",
    "watchlist_metrics",
    "missing_data",
]


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


def utc_now_iso() -> str:
    """
    Return current UTC datetime as ISO string.
    """

    return datetime.now(timezone.utc).isoformat()


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


def load_company_report_prompt() -> str:
    """
    Load the Company Research Report v0.2 prompt.
    """

    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt not found: {PROMPT_PATH}. "
            "Copy company_research_report_v0_2.txt into the prompts folder first."
        )

    return PROMPT_PATH.read_text(encoding="utf-8")


def build_company_input(row: pd.Series) -> dict[str, Any]:
    """
    Build the input object for the Company Research Report.
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
    company_input["analysis_mode"] = ANALYSIS_MODE
    company_input["prompt_version"] = PROMPT_VERSION
    company_input["schema_version"] = SCHEMA_VERSION

    return make_json_safe(company_input)


def build_input_text(prompt: str, company_input: dict[str, Any]) -> str:
    """
    Build the final OpenAI input text.
    """

    return (
        f"{prompt}\n\n"
        "COMPANY_INPUT:\n"
        f"{json.dumps(company_input, indent=2, ensure_ascii=False)}\n\n"
        "Return only the JSON object."
    )


def parse_report_response(response_text: str) -> dict[str, Any]:
    """
    Parse OpenAI response as JSON.
    """

    try:
        report = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "OpenAI response was not valid JSON. "
            f"JSON error: {exc}\n\nRaw response:\n{response_text}"
        ) from exc

    if not isinstance(report, dict):
        raise ValueError("OpenAI response JSON must be an object.")

    return report


def normalize_report_metadata(
    report: dict[str, Any],
    company_input: dict[str, Any],
    model: str,
    estimated_cost: float,
) -> dict[str, Any]:
    """
    Fill metadata fields controlled by the application.

    This avoids asking the model to know the actual model name or final cost.
    """

    normalized = dict(report)

    normalized["ticker"] = normalized.get("ticker") or company_input.get("ticker")
    normalized["company_name"] = normalized.get("company_name") or company_input.get("company_name")
    normalized["sector"] = normalized.get("sector") or company_input.get("sector")
    normalized["analysis_date"] = normalized.get("analysis_date") or utc_now_iso()
    normalized["model_used"] = model
    normalized["estimated_cost_usd"] = round(float(estimated_cost), 6)

    return normalized


def _is_valid_score(value: Any) -> bool:
    """
    Validate score values.

    Valid values:
    - None
    - int/float between 0 and 100
    """

    if value is None:
        return True

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return 0 <= float(value) <= 100


def validate_company_report_v2(report: dict[str, Any]) -> list[str]:
    """
    Validate required fields for the Company Research Report v0.2.

    Returns a list of errors. Empty list means valid.
    """

    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in report:
            errors.append(f"missing_field:{field}")

    for score_field in SCORE_FIELDS:
        if score_field in report and not _is_valid_score(report.get(score_field)):
            errors.append(f"invalid_score:{score_field}")

    for list_field in LIST_FIELDS:
        if list_field in report and not isinstance(report.get(list_field), list):
            errors.append(f"field_must_be_list:{list_field}")

    if report.get("final_category") not in ALLOWED_FINAL_CATEGORIES:
        errors.append("invalid_final_category")

    if report.get("confidence_level") not in ALLOWED_CONFIDENCE_LEVELS:
        errors.append("invalid_confidence_level")

    if not isinstance(report.get("markdown_report"), str) or not report.get("markdown_report", "").strip():
        errors.append("markdown_report_missing_or_empty")

    return errors


def _extract_executive_summary(markdown_report: str) -> str:
    """
    Extract a short executive summary from markdown_report.
    """

    if "## 1. Resumen ejecutivo" in markdown_report:
        section = markdown_report.split("## 1. Resumen ejecutivo", 1)[-1]
        next_section = section.split("## 2.", 1)[0]
        return next_section.strip()

    return markdown_report[:900].strip()


def report_v2_to_openai_analysis_payload(
    report: dict[str, Any],
    signal_id: int,
    run_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: float,
) -> dict[str, Any]:
    """
    Map valid Company Research Report v0.2 to existing openai_analysis columns.
    """

    markdown_report = report.get("markdown_report") or ""
    executive_summary = _extract_executive_summary(markdown_report)

    strengths = report.get("top_strengths", [])
    risks = report.get("top_risks", [])
    catalysts = report.get("catalysts", [])
    missing_data = report.get("missing_data", [])
    watchlist = report.get("watchlist_metrics", [])

    score_summary = {
        "business_quality_score": report.get("business_quality_score"),
        "financial_health_score": report.get("financial_health_score"),
        "growth_score": report.get("growth_score"),
        "valuation_score": report.get("valuation_score"),
        "risk_score": report.get("risk_score"),
        "moat_score": report.get("moat_score"),
        "confidence_score": report.get("confidence_score"),
    }

    return {
        "signal_id": signal_id,
        "run_id": run_id,
        "ticker": report.get("ticker"),
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "summary_thesis": executive_summary,
        "opportunity_type": ANALYSIS_MODE,
        "opportunity_phase": report.get("final_category"),
        "suggested_category": report.get("final_category"),
        "confidence_level": report.get("confidence_level"),
        "hype_risk": None,
        "source_quality": None,
        "reason_to_pass": report.get("final_category"),
        "missing_key_data": json.dumps(make_json_safe(missing_data), ensure_ascii=False),
        "event_to_confirm": json.dumps(make_json_safe(catalysts), ensure_ascii=False),
        "source_to_verify": json.dumps(make_json_safe(missing_data), ensure_ascii=False),
        "verifiable_facts_json": json.dumps(make_json_safe(strengths), ensure_ascii=False),
        "reasonable_inferences_json": json.dumps(make_json_safe([report.get("base_case")]), ensure_ascii=False),
        "speculative_elements_json": json.dumps(
            make_json_safe([report.get("bull_case"), report.get("bear_case")]),
            ensure_ascii=False,
        ),
        "contradictions_json": json.dumps([], ensure_ascii=False),
        "checklist_json": json.dumps(make_json_safe(watchlist), ensure_ascii=False),
        "why_it_could_work": report.get("bull_case"),
        "why_it_could_fail": report.get("bear_case"),
        "discrepancy_with_python": json.dumps(make_json_safe(score_summary), ensure_ascii=False),
        "raw_response_json": json.dumps(make_json_safe(report), ensure_ascii=False),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "cache_hit": 0,
    }


def generate_company_research_report_v2_top1(mode: str = "demo") -> dict[str, Any]:
    """
    Generate and persist one valid Company Research Report v0.2.

    Historical analysis is saved only if validation passes.
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

    prompt = load_company_report_prompt()
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
    raw_report = parse_report_response(response_text)

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

    report = normalize_report_metadata(
        report=raw_report,
        company_input=company_input,
        model=model,
        estimated_cost=estimated_cost,
    )

    validation_errors = validate_company_report_v2(report)

    if validation_errors:
        raise ValueError(
            "Company Research Report v0.2 validation failed. "
            "No historical analysis was saved.\n"
            f"Errors: {validation_errors}\n\n"
            f"Raw response:\n{json.dumps(make_json_safe(raw_report), indent=2, ensure_ascii=False)}"
        )

    payload = report_v2_to_openai_analysis_payload(
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
        "analysis_mode": ANALYSIS_MODE,
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "analysis_id": analysis_id,
        "cost_id": cost_id,
        "openai_analyzed_companies": openai_analyzed_companies,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "final_category": report.get("final_category"),
        "confidence_level": report.get("confidence_level"),
        "business_quality_score": report.get("business_quality_score"),
        "financial_health_score": report.get("financial_health_score"),
        "growth_score": report.get("growth_score"),
        "valuation_score": report.get("valuation_score"),
        "risk_score": report.get("risk_score"),
        "moat_score": report.get("moat_score"),
        "confidence_score": report.get("confidence_score"),
        "top_strengths": report.get("top_strengths"),
        "top_risks": report.get("top_risks"),
        "missing_data": report.get("missing_data"),
        "validation_errors": [],
        "markdown_report_preview": str(report.get("markdown_report", ""))[:1800],
    }


# Backward-compatible function name.
def generate_company_research_report_top1(mode: str = "demo") -> dict[str, Any]:
    """
    Backward-compatible wrapper.

    Phase 2 now runs v0.2 by default.
    """

    return generate_company_research_report_v2_top1(mode=mode)


if __name__ == "__main__":
    mode = "demo"

    print("Company Research Report v0.2")
    print("============================")

    status = get_openai_status()

    print("\nConfiguration:")
    for key, value in status.items():
        print(f"- {key}: {value}")

    print("\nRunning top-1 Company Research Report v0.2...")

    try:
        summary = generate_company_research_report_v2_top1(mode=mode)
    except Exception as exc:
        print("\nERROR:")
        print(str(exc))
        raise SystemExit(1)

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
            "confidence_level",
            "input_tokens",
            "output_tokens",
            "estimated_cost",
        ]
        available_columns = [column for column in columns_to_show if column in analysis_df.columns]
        print(analysis_df[available_columns].head(10).to_string(index=False))
