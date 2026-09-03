#!/usr/bin/env python3
"""Build deterministic v2.38K US experimental scores from the v2.38J matrix."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38K-us-experimental-scoring"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38k_us_experimental_scoring"
MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38j_us_candidate_feature_matrix/us_candidate_feature_matrix_v2_38j.csv"
CONTRACT = ROOT / "config/us_experimental_scoring_contract_v1.json"

PILLAR_WEIGHTS = {
    "fundamentals_quality": 0.30,
    "growth_momentum": 0.20,
    "profitability_cashflow": 0.20,
    "price_momentum_trend": 0.20,
    "risk_liquidity": 0.10,
}

SCORE_FIELDS = [
    "research_rank", "asset_id", "ticker", "company_name", "exchange", "cik",
    "candidate_matrix_status", "evidence_level", "experimental_score", "score_bucket",
    "fundamentals_quality_score", "growth_momentum_score",
    "profitability_cashflow_score", "price_momentum_trend_score",
    "risk_liquidity_score", "top_positive_drivers", "top_risk_drivers",
    "missing_reason", "experimental_score_notes", "scoring_calculated",
    "ranking_calculated", "recommendation_generated", "phase",
]

COMPONENT_FIELDS = [
    "asset_id", "ticker", "component", "weight", "raw_component_score",
    "weighted_points", "input_fields", "phase",
]

QUALITY_FIELDS = [
    "asset_id", "ticker", "candidate_matrix_status", "score_bucket",
    "scorable", "research_rank", "experimental_score", "quality_notes", "phase",
]

REJECTION_FIELDS = ["asset_id", "ticker", "company_name", "exchange", "reason", "phase"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def as_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def as_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def rounded(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, 4)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def points_from_ratio(value: float | None, anchors: list[tuple[float, float]]) -> float:
    if value is None:
        return 0.0
    anchors = sorted(anchors)
    if value <= anchors[0][0]:
        return anchors[0][1]
    if value >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= value <= x1:
            pct = (value - x0) / (x1 - x0)
            return y0 + pct * (y1 - y0)
    return 0.0


def flag_points(value: bool | None, true_points: float, false_points: float = 0.0) -> float:
    if value is None:
        return 0.0
    return true_points if value else false_points


def fundamentals_quality(row: dict[str, str]) -> float:
    score = 20.0
    score += points_from_ratio(as_float(row.get("revenue_growth_yoy")), [(-0.2, 0), (0.0, 8), (0.3, 18), (0.8, 25)])
    score += points_from_ratio(as_float(row.get("net_margin")), [(-0.2, 0), (0.0, 8), (0.15, 18), (0.35, 25)])
    score += points_from_ratio(as_float(row.get("free_cash_flow_margin")), [(-0.2, 0), (0.0, 7), (0.12, 16), (0.3, 20)])
    debt = as_float(row.get("debt_to_assets"))
    if debt is not None:
        score += points_from_ratio(1.0 - debt, [(0.0, 0), (0.25, 8), (0.55, 18), (0.85, 25)])
    return rounded(clamp(score)) or 0.0


def growth_momentum(row: dict[str, str]) -> float:
    score = 0.0
    score += points_from_ratio(as_float(row.get("revenue_growth_yoy")), [(-0.1, 0), (0.0, 15), (0.15, 35), (0.5, 50)])
    score += flag_points(as_bool(row.get("growth_positive_flag")), 20)
    score += flag_points(as_bool(row.get("price_acceleration_flag")), 15)
    score += points_from_ratio(as_float(row.get("return_3m")), [(-0.2, 0), (0.0, 5), (0.12, 12), (0.35, 15)])
    return rounded(clamp(score)) or 0.0


def profitability_cashflow(row: dict[str, str]) -> float:
    score = 0.0
    score += points_from_ratio(as_float(row.get("net_margin")), [(-0.15, 0), (0.0, 15), (0.1, 32), (0.25, 40)])
    score += points_from_ratio(as_float(row.get("free_cash_flow_margin")), [(-0.15, 0), (0.0, 12), (0.1, 28), (0.25, 35)])
    score += flag_points(as_bool(row.get("profitability_positive_flag")), 25)
    return rounded(clamp(score)) or 0.0


def price_momentum_trend(row: dict[str, str]) -> float:
    score = 0.0
    score += points_from_ratio(as_float(row.get("return_12m")), [(-0.4, 0), (0.0, 15), (0.25, 35), (0.8, 45)])
    score += points_from_ratio(as_float(row.get("return_6m")), [(-0.25, 0), (0.0, 8), (0.18, 18), (0.5, 22)])
    score += points_from_ratio(as_float(row.get("price_vs_sma_200")), [(-0.25, 0), (0.0, 8), (0.15, 17), (0.4, 20)])
    score += flag_points(as_bool(row.get("trend_positive_flag")), 8)
    score += flag_points(as_bool(row.get("recent_high_breakout_flag")), 5)
    return rounded(clamp(score)) or 0.0


def risk_liquidity(row: dict[str, str]) -> float:
    score = 100.0
    volatility = as_float(row.get("volatility_6m")) or as_float(row.get("volatility_3m"))
    drawdown = as_float(row.get("max_drawdown_12m")) or as_float(row.get("max_drawdown_6m"))
    debt = as_float(row.get("debt_to_assets"))
    if volatility is not None:
        score -= points_from_ratio(volatility, [(0.0, 0), (0.25, 8), (0.55, 22), (1.0, 35)])
    if drawdown is not None:
        score -= points_from_ratio(abs(drawdown), [(0.0, 0), (0.15, 6), (0.35, 18), (0.7, 30)])
    if debt is not None:
        score -= points_from_ratio(debt, [(0.0, 0), (0.35, 4), (0.75, 13), (1.0, 20)])
    if as_bool(row.get("liquidity_available_flag")) is False:
        score -= 15
    return rounded(clamp(score)) or 0.0


def bucket(score: float | None, status: str) -> str:
    if status == "CANDIDATE_MATRIX_BLOCKED":
        return "BLOCKED"
    if status != "CANDIDATE_MATRIX_READY" or score is None:
        return "REVIEW_REQUIRED"
    if score >= 75:
        return "INVESTIGATE_HIGH"
    if score >= 60:
        return "INVESTIGATE_MEDIUM"
    return "INVESTIGATE_LOW"


def explain(row: dict[str, str], components: dict[str, float]) -> tuple[str, str]:
    positives: list[str] = []
    risks: list[str] = []
    if as_float(row.get("revenue_growth_yoy")) is not None and as_float(row.get("revenue_growth_yoy")) > 0:
        positives.append("positive revenue growth")
    if as_bool(row.get("profitability_positive_flag")):
        positives.append("positive profitability/FCF signal")
    if as_bool(row.get("trend_positive_flag")):
        positives.append("positive price trend")
    if as_float(row.get("return_12m")) is not None and as_float(row.get("return_12m")) > 0:
        positives.append("positive 12m momentum")
    if as_bool(row.get("balance_sheet_risk_flag")):
        risks.append("balance-sheet risk flag")
    if as_float(row.get("max_drawdown_12m")) is not None and as_float(row.get("max_drawdown_12m")) < -0.35:
        risks.append("large 12m drawdown")
    if as_float(row.get("volatility_6m")) is not None and as_float(row.get("volatility_6m")) > 0.55:
        risks.append("high 6m volatility")
    if components["risk_liquidity"] < 55:
        risks.append("risk/liquidity component below 55")
    return "; ".join(positives[:4]) or "limited positive signal detail", "; ".join(risks[:4]) or "no dominant risk flag in tracked fields"


def score_row(row: dict[str, str]) -> tuple[float | None, dict[str, float]]:
    components = {
        "fundamentals_quality": fundamentals_quality(row),
        "growth_momentum": growth_momentum(row),
        "profitability_cashflow": profitability_cashflow(row),
        "price_momentum_trend": price_momentum_trend(row),
        "risk_liquidity": risk_liquidity(row),
    }
    if row.get("candidate_matrix_status") != "CANDIDATE_MATRIX_READY":
        return None, components
    score = sum(components[name] * weight for name, weight in PILLAR_WEIGHTS.items())
    return rounded(clamp(score)), components


def build(input_matrix: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_csv(input_matrix)
    scored: list[dict[str, Any]] = []
    component_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    seen: set[str] = set()

    for source in rows:
        asset_id = source.get("asset_id", "")
        ticker = source.get("ticker", "")
        if not asset_id or not ticker or asset_id in seen:
            rejections.append({
                "asset_id": asset_id,
                "ticker": ticker,
                "company_name": source.get("company_name", ""),
                "exchange": source.get("exchange", ""),
                "reason": "duplicate_or_invalid_identity",
                "phase": PHASE,
            })
            continue
        seen.add(asset_id)
        score, components = score_row(source)
        score_bucket = bucket(score, source.get("candidate_matrix_status", ""))
        positives, risks = explain(source, components)
        out = {
            "research_rank": "",
            "asset_id": asset_id,
            "ticker": ticker,
            "company_name": source.get("company_name", ""),
            "exchange": source.get("exchange", ""),
            "cik": source.get("cik", ""),
            "candidate_matrix_status": source.get("candidate_matrix_status", ""),
            "evidence_level": source.get("evidence_level", ""),
            "experimental_score": score,
            "score_bucket": score_bucket,
            "fundamentals_quality_score": components["fundamentals_quality"],
            "growth_momentum_score": components["growth_momentum"],
            "profitability_cashflow_score": components["profitability_cashflow"],
            "price_momentum_trend_score": components["price_momentum_trend"],
            "risk_liquidity_score": components["risk_liquidity"],
            "top_positive_drivers": positives,
            "top_risk_drivers": risks,
            "missing_reason": source.get("missing_reason", ""),
            "experimental_score_notes": "Research-only experimental score; not a recommendation, prediction, buy/sell/hold signal or financial advice.",
            "scoring_calculated": True,
            "ranking_calculated": True,
            "recommendation_generated": False,
            "phase": PHASE,
        }
        scored.append(out)
        for component, raw_score in components.items():
            component_rows.append({
                "asset_id": asset_id,
                "ticker": ticker,
                "component": component,
                "weight": PILLAR_WEIGHTS[component],
                "raw_component_score": raw_score,
                "weighted_points": rounded(raw_score * PILLAR_WEIGHTS[component]),
                "input_fields": component_input_fields(component),
                "phase": PHASE,
            })

    ranked = [r for r in scored if r["experimental_score"] != "" and r["experimental_score"] is not None]
    ranked.sort(key=lambda r: (-float(r["experimental_score"]), str(r["ticker"]), str(r["asset_id"])))
    for rank, row in enumerate(ranked, 1):
        row["research_rank"] = rank
    scored.sort(key=lambda r: (int(r["research_rank"]) if r["research_rank"] else 10**9, str(r["asset_id"])))

    for row in scored:
        quality_rows.append({
            "asset_id": row["asset_id"],
            "ticker": row["ticker"],
            "candidate_matrix_status": row["candidate_matrix_status"],
            "score_bucket": row["score_bucket"],
            "scorable": bool(row["research_rank"]),
            "research_rank": row["research_rank"],
            "experimental_score": row["experimental_score"],
            "quality_notes": "scored_ready_matrix_row" if row["research_rank"] else "not_scored_requires_more_evidence",
            "phase": PHASE,
        })

    write_csv(output_dir / "us_experimental_scores_v2_38k.csv", SCORE_FIELDS, scored)
    write_csv(output_dir / "us_experimental_score_components_v2_38k.csv", COMPONENT_FIELDS, component_rows)
    write_csv(output_dir / "us_experimental_score_quality_v2_38k.csv", QUALITY_FIELDS, quality_rows)
    write_csv(output_dir / "us_experimental_score_rejections_v2_38k.csv", REJECTION_FIELDS, rejections)

    scores = [float(r["experimental_score"]) for r in ranked]
    bucket_counts = Counter(str(r["score_bucket"]) for r in scored)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_US_EXPERIMENTAL_SCORING_NOT_RECOMMENDATIONS",
        "input_candidates": len(rows),
        "scored_companies": len(ranked),
        "unscored_companies": len(scored) - len(ranked),
        "rejected_rows": len(rejections),
        "score_min": rounded(min(scores)) if scores else None,
        "score_max": rounded(max(scores)) if scores else None,
        "score_mean": rounded(sum(scores) / len(scores)) if scores else None,
        "score_bucket_counts": {name: bucket_counts.get(name, 0) for name in ["INVESTIGATE_HIGH", "INVESTIGATE_MEDIUM", "INVESTIGATE_LOW", "REVIEW_REQUIRED", "BLOCKED"]},
        "pillar_weights": PILLAR_WEIGHTS,
        "guardrails": {
            "network_calls": 0,
            "phase9c_authorized": False,
            "scoring_calculated": True,
            "ranking_calculated": True,
            "recommendations_generated": False,
            "broker_actions_allowed": False,
            "financial_advice": False,
        },
    }
    (output_dir / "us_experimental_score_aggregate_report_v2_38k.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    (output_dir / "README.md").write_text("# v2.38K US experimental scoring\n\nBuilds a deterministic research-only score over v2.38J US candidate matrix rows. It ranks only complete `CANDIDATE_MATRIX_READY` rows and leaves partial evidence as `REVIEW_REQUIRED`. It does not generate recommendations or financial advice.\n", encoding="utf-8", newline="\n")
    (output_dir / "US_EXPERIMENTAL_SCORING_CONTRACT_v2_38k.md").write_text("# US Experimental Scoring Contract v2.38K\n\nThis phase introduces a frozen, deterministic 0-100 research score with five pillars: fundamentals quality, growth momentum, profitability/cashflow, price momentum/trend and risk/liquidity. The score is a prioritization aid only; it is not a prediction, recommendation, buy/sell/hold decision, or phase 9C promotion.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9K US Experimental Scoring Gate v2.38K

Status: {report['status']}

- Input candidates: {report['input_candidates']}
- Scored companies: {report['scored_companies']}
- Unscored companies: {report['unscored_companies']}
- Rejected rows: {report['rejected_rows']}
- Score range: {report['score_min']} - {report['score_max']}

Guardrails: no network calls, no recommendations, no financial advice, no broker actions and no phase 9C authorization.
"""
    (output_dir / "PHASE9K_US_EXPERIMENTAL_SCORING_GATE_v2_38k.md").write_text(gate, encoding="utf-8", newline="\n")

    public = [
        "README.md",
        "US_EXPERIMENTAL_SCORING_CONTRACT_v2_38k.md",
        "PHASE9K_US_EXPERIMENTAL_SCORING_GATE_v2_38k.md",
        "us_experimental_scores_v2_38k.csv",
        "us_experimental_score_components_v2_38k.csv",
        "us_experimental_score_quality_v2_38k.csv",
        "us_experimental_score_rejections_v2_38k.csv",
        "us_experimental_score_aggregate_report_v2_38k.json",
    ]
    manifest = {
        "phase": PHASE,
        "outputs": {name: {"bytes": (output_dir / name).stat().st_size, "sha256": sha256(output_dir / name)} for name in public},
        "guardrails": report["guardrails"],
    }
    (output_dir / "us_experimental_score_manifest_v2_38k.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ["status", "input_candidates", "scored_companies", "unscored_companies", "rejected_rows"]}, sort_keys=True))
    return report


def component_input_fields(component: str) -> str:
    return {
        "fundamentals_quality": "revenue_growth_yoy|net_margin|free_cash_flow_margin|debt_to_assets",
        "growth_momentum": "revenue_growth_yoy|growth_positive_flag|price_acceleration_flag|return_3m",
        "profitability_cashflow": "net_margin|free_cash_flow_margin|profitability_positive_flag",
        "price_momentum_trend": "return_12m|return_6m|price_vs_sma_200|trend_positive_flag|recent_high_breakout_flag",
        "risk_liquidity": "volatility_6m|volatility_3m|max_drawdown_12m|max_drawdown_6m|debt_to_assets|liquidity_available_flag",
    }[component]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-matrix", type=Path, default=MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    build(args.input_matrix, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
