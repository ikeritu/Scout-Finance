"""
Scout Finance — Phase 3 Top N structured output runner.

Keeps previous top-1 behaviour by default and adds:
    python -m src.company_research_report_outputs --top-n 3

Generated files per company:
- outputs/analyses/TICKER_FECHA.md
- outputs/analyses/TICKER_FECHA.json
- outputs/analyses/TICKER_FECHA_scorecard.png
- outputs/analyses/TICKER_FECHA_scenarios.png
- outputs/analyses/TICKER_FECHA_executive_card.html
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis_schema import MOAT_FIELDS, SCORE_FIELDS
from src.openai_client import (
    estimate_request_cost,
    get_openai_client,
    get_openai_status,
    get_selected_model,
    validate_budget,
    validate_company_limit,
    validate_openai_ready,
)
from src.results import get_latest_run_id, get_top_signals_enriched
from src.save_outputs import save_analysis_outputs
from src.validate_analysis import validate_analysis_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "prompts" / "scout_finance_company_report_v0_3.txt"


def _env_float(name: str, default: float = 0.0) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
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


def make_json_safe(value: Any) -> Any:
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


def load_master_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt not found: {PROMPT_PATH}. "
            "Copy scout_finance_company_report_v0_3.txt into prompts first."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_company_input(row: pd.Series) -> dict[str, Any]:
    fields = [
        "ticker", "company_name", "sector", "industry", "exchange", "currency",
        "price_at_signal", "price", "previous_close", "volume", "avg_volume_50d",
        "relative_volume", "change_1d", "change_5d", "change_20d", "ma20", "ma50",
        "above_ma20", "above_ma50", "high_52w", "low_52w",
        "distance_to_52w_high", "distance_to_52w_low", "market_cap", "data_source",
        "data_quality_score", "data_quality_label", "score_volume", "score_momentum",
        "score_liquidity", "score_context", "score_raw", "score_adjusted",
        "score_priority", "score_confidence", "score_risk", "category_final",
        "opportunity_phase", "reason_to_pass_quant", "missing_key_data_quant",
        "scoring_version",
    ]
    company_input = {field: row.get(field) for field in fields if field in row.index}
    company_input["analysis_mode"] = "scout_finance_company_report_v0.3"
    company_input["analysis_date"] = datetime.now(timezone.utc).isoformat()
    return make_json_safe(company_input)


def build_openai_input(prompt: str, company_input: dict[str, Any]) -> str:
    return (
        f"{prompt}\n\n"
        "COMPANY_INPUT:\n"
        f"{json.dumps(company_input, indent=2, ensure_ascii=False)}\n\n"
        "Return only valid JSON with exactly these two keys: markdown_report and analysis_json."
    )


def parse_model_response(response_text: str) -> tuple[str, dict[str, Any]]:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "OpenAI returned invalid JSON. No output files were saved for this company.\n"
            f"JSON error: {exc}\n\nRaw response:\n{response_text}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError("OpenAI response must be a JSON object.")

    markdown_report = parsed.get("markdown_report")
    analysis_json = parsed.get("analysis_json")

    if not isinstance(markdown_report, str) or not markdown_report.strip():
        raise ValueError("Response missing non-empty markdown_report.")

    if not isinstance(analysis_json, dict):
        raise ValueError("Response missing analysis_json object.")

    return markdown_report, analysis_json


def _score_to_0_10(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if 0 <= number <= 10:
        return round(number, 2)
    if 10 < number <= 100:
        return round(number / 10, 2)
    return value


def _normalize_confidence_level(value: Any, scores: dict[str, Any]) -> str:
    text = str(value or "").strip().lower()
    if text in {"alto", "media-alta", "alta", "high"}:
        normalized = "alto"
    elif text in {"medio", "media", "medium", "low to medium", "medium-low", "low/medium"}:
        normalized = "medio"
    elif text in {"bajo", "baja", "low"}:
        normalized = "bajo"
    elif text in {"insuficiente", "insufficient", "not enough data", "datos insuficientes"}:
        normalized = "insuficiente"
    else:
        normalized = "bajo"

    try:
        evidence_quality = scores.get("evidence_quality_score")
        data_freshness = scores.get("data_freshness_score")
        confidence = scores.get("confidence_score")
        if evidence_quality is not None and float(evidence_quality) <= 4 and normalized == "alto":
            normalized = "medio"
        if data_freshness is not None and float(data_freshness) <= 4 and normalized == "alto":
            normalized = "medio"
        if confidence is not None and float(confidence) <= 4 and normalized == "alto":
            normalized = "medio"
    except (TypeError, ValueError):
        pass

    return normalized


def normalize_analysis_metadata(
    analysis_json: dict[str, Any],
    company_input: dict[str, Any],
    model: str,
    estimated_cost: float,
) -> dict[str, Any]:
    data = make_json_safe(dict(analysis_json))

    data["ticker"] = data.get("ticker") or company_input.get("ticker")
    data["company_name"] = data.get("company_name") or company_input.get("company_name")
    data["sector"] = data.get("sector") or company_input.get("sector")
    data["industry"] = data.get("industry") or company_input.get("industry")
    data["currency"] = data.get("currency") or company_input.get("currency")
    data["analysis_date"] = data.get("analysis_date") or company_input.get("analysis_date")

    scores = data.setdefault("scores", {})
    if isinstance(scores, dict):
        for field in SCORE_FIELDS:
            scores[field] = _score_to_0_10(scores.get(field))

    moat_breakdown = data.setdefault("moat_breakdown", {})
    if isinstance(moat_breakdown, dict):
        for field in MOAT_FIELDS:
            moat_breakdown[field] = _score_to_0_10(moat_breakdown.get(field))

    valuation_summary = data.setdefault("valuation_summary", {})
    if isinstance(valuation_summary, dict):
        valuation_summary["valuation_confidence"] = _score_to_0_10(
            valuation_summary.get("valuation_confidence")
        )

    final_result = data.setdefault("final_result", {})
    if isinstance(final_result, dict):
        final_result["confidence_level"] = _normalize_confidence_level(
            final_result.get("confidence_level"),
            scores if isinstance(scores, dict) else {},
        )

    sources = data.setdefault("sources", {})
    if isinstance(sources, dict):
        sources.setdefault("main_sources", [])
        sources.setdefault("source_warnings", [])
        sources.setdefault("data_limitations", [])
        if isinstance(sources.get("source_warnings"), list):
            sources["source_warnings"].append(
                f"Modelo usado: {model}; coste estimado llamada: ${estimated_cost:.6f}"
            )

    return data


def estimate_phase3_planned_cost(top_n: int) -> float:
    est_input_tokens = _env_int("OPENAI_EST_INPUT_TOKENS_PER_COMPANY", 3000)
    est_output_tokens = _env_int("OPENAI_EST_OUTPUT_TOKENS_PER_COMPANY", 1200)

    return estimate_request_cost(
        input_tokens=est_input_tokens * top_n,
        output_tokens=est_output_tokens * top_n,
        input_cost_per_1m=_env_float("OPENAI_INPUT_COST_PER_1M", 0.0),
        output_cost_per_1m=_env_float("OPENAI_OUTPUT_COST_PER_1M", 0.0),
    )


def analyze_and_save_company_row(row: pd.Series, prompt: str, model: str, client: Any) -> dict[str, Any]:
    company_input = build_company_input(row)
    ticker = str(company_input.get("ticker"))

    response = client.responses.create(
        model=model,
        input=build_openai_input(prompt, company_input),
        text={"format": {"type": "json_object"}},
    )

    response_text = _extract_response_text(response)
    markdown_report, raw_analysis_json = parse_model_response(response_text)

    usage = getattr(response, "usage", None)
    input_tokens = _get_usage_value(usage, "input_tokens", "prompt_tokens")
    output_tokens = _get_usage_value(usage, "output_tokens", "completion_tokens")

    estimated_cost = estimate_request_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_per_1m=_env_float("OPENAI_INPUT_COST_PER_1M", 0.0),
        output_cost_per_1m=_env_float("OPENAI_OUTPUT_COST_PER_1M", 0.0),
    )

    validate_budget(estimated_cost=estimated_cost, spent_today=0.0, spent_this_month=0.0)

    analysis_json = normalize_analysis_metadata(
        analysis_json=raw_analysis_json,
        company_input=company_input,
        model=model,
        estimated_cost=estimated_cost,
    )

    validation = validate_analysis_json(analysis_json)

    if not validation.is_valid:
        raise ValueError(
            "Structured analysis JSON validation failed. No output files were saved for this company.\n"
            f"Ticker: {ticker}\n"
            f"Errors: {validation.errors}\n"
            f"Warnings: {validation.warnings}"
        )

    saved_paths = save_analysis_outputs(
        ticker=ticker,
        markdown_report=markdown_report,
        json_data=analysis_json,
        output_dir=PROJECT_ROOT / "outputs" / "analyses",
        create_visualizations=True,
    )

    return {
        "ok": True,
        "ticker": ticker,
        "company_name": analysis_json.get("company_name"),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "final_category": analysis_json.get("final_result", {}).get("final_category"),
        "confidence_level": analysis_json.get("final_result", {}).get("confidence_level"),
        "confidence_score": analysis_json.get("scores", {}).get("confidence_score"),
        "validation_warnings": validation.warnings,
        "saved_paths": {key: str(value) for key, value in saved_paths.items()},
    }


def generate_phase2_outputs_top_n(mode: str = "demo", top_n: int = 1) -> dict[str, Any]:
    if top_n < 1:
        raise ValueError("top_n must be >= 1.")

    validate_company_limit(top_n)
    validate_openai_ready(use_strong_model=False)

    planned_cost = estimate_phase3_planned_cost(top_n)
    validate_budget(estimated_cost=planned_cost, spent_today=0.0, spent_this_month=0.0)

    run_id = get_latest_run_id(mode=mode)
    if run_id is None:
        raise ValueError("No runs found. Execute python -m src.pipeline first.")

    top_df = get_top_signals_enriched(run_id=run_id, mode=mode, top_n=top_n)
    if top_df.empty:
        raise ValueError("No signals found for latest run.")

    prompt = load_master_prompt()
    model = get_selected_model(use_strong_model=False)
    client = get_openai_client(use_strong_model=False)

    results = []
    errors = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_estimated_cost = 0.0

    for index, (_, row) in enumerate(top_df.iterrows(), start=1):
        ticker = str(row.get("ticker", f"row_{index}"))
        print(f"\n[{index}/{len(top_df)}] Analyzing {ticker}...")

        try:
            result = analyze_and_save_company_row(row=row, prompt=prompt, model=model, client=client)
            results.append(result)
            total_input_tokens += int(result.get("input_tokens") or 0)
            total_output_tokens += int(result.get("output_tokens") or 0)
            total_estimated_cost += float(result.get("estimated_cost") or 0.0)
            print(
                f"OK {ticker}: cost=${float(result.get('estimated_cost') or 0):.6f}; "
                f"category={result.get('final_category')}; confidence={result.get('confidence_score')}"
            )
        except Exception as exc:
            errors.append({"ticker": ticker, "error_type": exc.__class__.__name__, "message": str(exc)})
            print(f"ERROR {ticker}: {exc.__class__.__name__}: {exc}")

    return {
        "run_id": run_id,
        "mode": mode,
        "requested_top_n": top_n,
        "attempted_companies": len(top_df),
        "successful_companies": len(results),
        "failed_companies": len(errors),
        "planned_estimated_cost": planned_cost,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_estimated_cost": total_estimated_cost,
        "model": model,
        "results": results,
        "errors": errors,
    }


def generate_phase2_outputs_top1(mode: str = "demo") -> dict[str, Any]:
    return generate_phase2_outputs_top_n(mode=mode, top_n=1)


# Backward-compatible name expected by earlier scripts/messages.
def generate_phase2_outputs_top1_public(mode: str = "demo") -> dict[str, Any]:
    return generate_phase2_outputs_top1(mode=mode)


def print_summary(summary: dict[str, Any]) -> None:
    print("\nBatch summary:")
    print(f"- run_id: {summary.get('run_id')}")
    print(f"- mode: {summary.get('mode')}")
    print(f"- requested_top_n: {summary.get('requested_top_n')}")
    print(f"- attempted_companies: {summary.get('attempted_companies')}")
    print(f"- successful_companies: {summary.get('successful_companies')}")
    print(f"- failed_companies: {summary.get('failed_companies')}")
    print(f"- model: {summary.get('model')}")
    print(f"- planned_estimated_cost: ${float(summary.get('planned_estimated_cost') or 0):.6f}")
    print(f"- total_estimated_cost: ${float(summary.get('total_estimated_cost') or 0):.6f}")
    print(f"- total_input_tokens: {summary.get('total_input_tokens')}")
    print(f"- total_output_tokens: {summary.get('total_output_tokens')}")

    if summary.get("results"):
        print("\nSuccessful outputs:")
        for result in summary["results"]:
            print(
                f"- {result.get('ticker')} | {result.get('company_name')} | "
                f"{result.get('final_category')} | confidence={result.get('confidence_score')} | "
                f"cost=${float(result.get('estimated_cost') or 0):.6f}"
            )
            for key, path in result.get("saved_paths", {}).items():
                print(f"  - {key}: {path}")

    if summary.get("errors"):
        print("\nErrors:")
        for error in summary["errors"]:
            print(f"- {error.get('ticker')} | {error.get('error_type')}: {error.get('message')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Scout Finance structured outputs for top N companies.")
    parser.add_argument("--mode", default="demo", choices=["demo", "real"], help="Data mode to use. Default: demo.")
    parser.add_argument("--top-n", type=int, default=1, help="Number of top companies to analyze. Default: 1.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("Scout Finance — Phase 3 Top N outputs")
    print("====================================")

    print("\nConfiguration:")
    for key, value in get_openai_status().items():
        print(f"- {key}: {value}")

    print(f"\nRequested mode: {args.mode}")
    print(f"Requested top_n: {args.top_n}")
    print(f"Planned estimated cost: ${estimate_phase3_planned_cost(args.top_n):.6f}")

    print("\nGenerating outputs...")

    try:
        batch_summary = generate_phase2_outputs_top_n(mode=args.mode, top_n=args.top_n)
    except Exception as exc:
        print("\nERROR:")
        print(str(exc))
        raise SystemExit(1)

    print_summary(batch_summary)

    if batch_summary.get("failed_companies"):
        raise SystemExit(2)
