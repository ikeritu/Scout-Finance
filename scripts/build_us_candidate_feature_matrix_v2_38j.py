#!/usr/bin/env python3
"""Build deterministic v2.38J US candidate feature matrix without scoring."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38J-us-candidate-feature-matrix"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38j_us_candidate_feature_matrix"
IDENTITY = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation/us_sec_identity_overlay_v2_38d.csv"
FUNDAMENTALS = ROOT / "outputs/full_universe_source_acquisition/v2_38g_us_sec_fundamental_features/us_sec_fundamental_features_v2_38g.csv"
PRICES = ROOT / "outputs/full_universe_source_acquisition/v2_38h_us_price_features/us_price_features_v2_38h.csv"

FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "cik", "source_priority",
    "candidate_matrix_status", "fundamental_quality_status", "price_quality_status",
    "evidence_level", "missing_reason",
    "revenue_growth_yoy", "revenue_growth_3y", "gross_margin", "operating_margin",
    "net_margin", "free_cash_flow_margin", "debt_to_assets", "cash_to_assets",
    "shares_dilution_flag", "profitability_positive_flag", "growth_positive_flag",
    "balance_sheet_risk_flag",
    "return_1m", "return_3m", "return_6m", "return_12m", "volatility_3m",
    "volatility_6m", "max_drawdown_6m", "max_drawdown_12m", "price_vs_sma_50",
    "price_vs_sma_200", "sma_50_vs_sma_200", "trend_positive_flag",
    "recent_high_breakout_flag", "near_52w_high_flag", "recovery_from_drawdown_flag",
    "avg_volume_1m", "avg_volume_3m", "liquidity_available_flag",
    "fundamental_signal_summary", "price_signal_summary", "risk_signal_summary",
    "evidence_notes", "scoring_calculated", "ranking_calculated", "recommendation_generated",
    "phase",
]

QUALITY_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "candidate_matrix_status",
    "fundamental_quality_status", "price_quality_status", "evidence_level",
    "missing_reason", "phase",
]

REJECTION_FIELDS = ["asset_id", "ticker", "company_name", "exchange", "reason", "phase"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def bool_text(value: bool | None) -> str:
    if value is None:
        return ""
    return "true" if value else "false"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def one_by_asset(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    seen: dict[str, dict[str, str]] = {}
    rejected: list[dict[str, str]] = []
    for row in rows:
        asset_id = row.get("asset_id", "")
        if not asset_id or not row.get("ticker") or not row.get("company_name"):
            rejected.append({**row, "reason": "invalid_identity"})
            continue
        if asset_id in seen:
            rejected.append({**row, "reason": "duplicate_asset_id"})
            continue
        seen[asset_id] = row
    return seen, rejected


def classify(fund: dict[str, str] | None, price: dict[str, str] | None) -> tuple[str, str, str]:
    fund_status = (fund or {}).get("feature_quality_status", "")
    price_status = (price or {}).get("price_feature_quality_status", "")
    fund_ready = fund_status == "FEATURES_READY"
    price_ready = price_status == "PRICE_FEATURES_READY"
    fund_present = fund is not None
    price_present = price is not None
    if fund_ready and price_ready:
        return "CANDIDATE_MATRIX_READY", "high", ""
    if fund_present and not price_ready:
        return "CANDIDATE_MATRIX_PARTIAL_PRICE", "medium", "price_features_missing_or_partial"
    if price_present and not fund_ready:
        return "CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS", "medium", "fundamental_features_missing_or_partial"
    if fund_present or price_present:
        return "CANDIDATE_MATRIX_INSUFFICIENT_EVIDENCE", "low", "insufficient_feature_evidence"
    return "CANDIDATE_MATRIX_BLOCKED", "blocked", "no_feature_inputs"


def signal_summary(fund: dict[str, str] | None) -> str:
    if not fund:
        return "No local SEC fundamental feature row available."
    parts = []
    growth = as_float(fund.get("revenue_yoy_growth"))
    margin = as_float(fund.get("net_margin"))
    fcf = fund.get("positive_fcf_flag")
    if growth is not None:
        parts.append("revenue growth positive" if growth > 0 else "revenue growth non-positive")
    if margin is not None:
        parts.append("net margin positive" if margin > 0 else "net margin non-positive")
    if fcf:
        parts.append("positive FCF flag " + fcf)
    return "; ".join(parts) or "Fundamental fields present but limited."


def price_summary(price: dict[str, str] | None) -> str:
    if not price:
        return "No local price feature row available."
    parts = []
    for field, label in [("return_3m", "3m return"), ("return_12m", "12m return")]:
        value = as_float(price.get(field))
        if value is not None:
            parts.append(f"{label} {'positive' if value > 0 else 'non-positive'}")
    if price.get("trend_positive_flag"):
        parts.append("trend flag " + price["trend_positive_flag"])
    return "; ".join(parts) or "Price fields present but limited."


def risk_summary(fund: dict[str, str] | None, price: dict[str, str] | None) -> str:
    notes = []
    debt = as_float((fund or {}).get("liabilities_to_assets"))
    drawdown = as_float((price or {}).get("max_drawdown_12m"))
    if debt is not None:
        notes.append("balance-sheet leverage elevated" if debt > 0.75 else "balance-sheet leverage not elevated")
    if drawdown is not None:
        notes.append("12m drawdown severe" if drawdown < -0.5 else "12m drawdown within tracked range")
    return "; ".join(notes) or "Risk evidence incomplete."


def build(identity_path: Path, fundamentals_path: Path, prices_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    identity, identity_rejected = one_by_asset(read_csv(identity_path))
    fundamentals, fundamental_rejected = one_by_asset(read_csv(fundamentals_path))
    prices, price_rejected = one_by_asset(read_csv(prices_path))
    asset_ids = sorted(set(fundamentals) | set(prices))

    rows: list[dict[str, object]] = []
    rejections: list[dict[str, object]] = []
    for bad in identity_rejected + fundamental_rejected + price_rejected:
        rejections.append({
            "asset_id": bad.get("asset_id", ""),
            "ticker": bad.get("ticker", ""),
            "company_name": bad.get("company_name", ""),
            "exchange": bad.get("exchange", ""),
            "reason": bad.get("reason", "invalid_input_row"),
            "phase": PHASE,
        })

    for asset_id in asset_ids:
        fund = fundamentals.get(asset_id)
        price = prices.get(asset_id)
        ident = identity.get(asset_id, {})
        source = fund or price or ident
        if not source.get("ticker") or not source.get("company_name"):
            rejections.append({
                "asset_id": asset_id,
                "ticker": source.get("ticker", ""),
                "company_name": source.get("company_name", ""),
                "exchange": source.get("exchange", ""),
                "reason": "missing_join_identity",
                "phase": PHASE,
            })
            continue
        status, evidence_level, missing_reason = classify(fund, price)
        debt = as_float((fund or {}).get("liabilities_to_assets"))
        growth = as_float((fund or {}).get("revenue_yoy_growth"))
        net_margin = as_float((fund or {}).get("net_margin"))
        free_cash_flow = as_float((fund or {}).get("free_cash_flow_margin"))
        row = {
            "asset_id": asset_id,
            "ticker": source.get("ticker", ""),
            "company_name": source.get("company_name", ""),
            "exchange": source.get("exchange", ""),
            "cik": (fund or ident).get("cik", ""),
            "source_priority": "fundamental_and_price" if fund and price else ("fundamental_only" if fund else "price_only"),
            "candidate_matrix_status": status,
            "fundamental_quality_status": (fund or {}).get("feature_quality_status", "MISSING"),
            "price_quality_status": (price or {}).get("price_feature_quality_status", "MISSING"),
            "evidence_level": evidence_level,
            "missing_reason": missing_reason,
            "revenue_growth_yoy": (fund or {}).get("revenue_yoy_growth", ""),
            "revenue_growth_3y": "",
            "gross_margin": "",
            "operating_margin": "",
            "net_margin": (fund or {}).get("net_margin", ""),
            "free_cash_flow_margin": (fund or {}).get("free_cash_flow_margin", ""),
            "debt_to_assets": (fund or {}).get("liabilities_to_assets", ""),
            "cash_to_assets": "",
            "shares_dilution_flag": "",
            "profitability_positive_flag": bool_text((net_margin is not None and net_margin > 0) or (free_cash_flow is not None and free_cash_flow > 0)),
            "growth_positive_flag": bool_text(growth is not None and growth > 0),
            "balance_sheet_risk_flag": bool_text(debt is not None and debt > 0.75),
            "fundamental_signal_summary": signal_summary(fund),
            "price_signal_summary": price_summary(price),
            "risk_signal_summary": risk_summary(fund, price),
            "evidence_notes": "Prepared for future scoring; no recommendation language or ranking emitted.",
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendation_generated": False,
            "phase": PHASE,
        }
        for field in [
            "return_1m", "return_3m", "return_6m", "return_12m", "volatility_3m",
            "volatility_6m", "max_drawdown_6m", "max_drawdown_12m", "price_vs_sma_50",
            "price_vs_sma_200", "sma_50_vs_sma_200", "trend_positive_flag",
            "recent_high_breakout_flag", "near_52w_high_flag", "recovery_from_drawdown_flag",
            "avg_volume_1m", "avg_volume_3m", "liquidity_available_flag",
        ]:
            row[field] = (price or {}).get(field, "")
        rows.append(row)

    rows.sort(key=lambda r: str(r["asset_id"]))
    quality = [{field: row.get(field, "") for field in QUALITY_FIELDS} for row in rows]
    write_csv(output_dir / "us_candidate_feature_matrix_v2_38j.csv", FIELDS, rows)
    write_csv(output_dir / "us_candidate_feature_matrix_quality_v2_38j.csv", QUALITY_FIELDS, quality)
    write_csv(output_dir / "us_candidate_feature_matrix_rejections_v2_38j.csv", REJECTION_FIELDS, rejections)

    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["candidate_matrix_status"])
        counts[key] = counts.get(key, 0) + 1
    joined_both = sum(1 for asset_id in asset_ids if asset_id in fundamentals and asset_id in prices)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_US_CANDIDATE_FEATURE_MATRIX_NOT_SCORING",
        "candidates_total": len(rows),
        "matrix_ready": counts.get("CANDIDATE_MATRIX_READY", 0),
        "partial_price": counts.get("CANDIDATE_MATRIX_PARTIAL_PRICE", 0),
        "partial_fundamentals": counts.get("CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS", 0),
        "insufficient_evidence": counts.get("CANDIDATE_MATRIX_INSUFFICIENT_EVIDENCE", 0),
        "blocked": counts.get("CANDIDATE_MATRIX_BLOCKED", 0),
        "fundamental_input_companies": len(fundamentals),
        "price_input_companies": len(prices),
        "joined_both": joined_both,
        "only_fundamentals": len(fundamentals) - joined_both,
        "only_price": len(prices) - joined_both,
        "rejected_rows": len(rejections),
        "guardrails": {
            "network_calls": 0,
            "phase9c_authorized": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "scoring_calculated": False,
        },
    }
    (output_dir / "us_candidate_feature_matrix_aggregate_report_v2_38j.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    (output_dir / "README.md").write_text("# v2.38J US candidate feature matrix\n\nCombines local US SEC fundamental features with local US price features into a traceable candidate matrix for future scoring. It does not calculate scoring, ranking or recommendations.\n", encoding="utf-8", newline="\n")
    (output_dir / "US_CANDIDATE_FEATURE_MATRIX_CONTRACT_v2_38j.md").write_text("# US Candidate Feature Matrix Contract v2.38J\n\nThis phase joins identity, SEC fundamental features and local price features. The output is preparation for a future scoring phase only. It is not financial advice and does not predict returns.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9J US Candidate Matrix Gate v2.38J

Status: {report['status']}

- Candidates: {report['candidates_total']}
- Ready matrix rows: {report['matrix_ready']}
- Partial price rows: {report['partial_price']}
- Partial fundamental rows: {report['partial_fundamentals']}
- Rejected rows: {report['rejected_rows']}

Guardrails: no network calls, no scoring, no ranking, no recommendations, no phase 9C authorization.
"""
    (output_dir / "PHASE9J_US_CANDIDATE_MATRIX_GATE_v2_38j.md").write_text(gate, encoding="utf-8", newline="\n")

    public = [
        "README.md",
        "US_CANDIDATE_FEATURE_MATRIX_CONTRACT_v2_38j.md",
        "PHASE9J_US_CANDIDATE_MATRIX_GATE_v2_38j.md",
        "us_candidate_feature_matrix_v2_38j.csv",
        "us_candidate_feature_matrix_quality_v2_38j.csv",
        "us_candidate_feature_matrix_rejections_v2_38j.csv",
        "us_candidate_feature_matrix_aggregate_report_v2_38j.json",
    ]
    manifest = {
        "phase": PHASE,
        "outputs": {name: {"bytes": (output_dir / name).stat().st_size, "sha256": sha256(output_dir / name)} for name in public},
        "guardrails": report["guardrails"],
    }
    (output_dir / "us_candidate_feature_matrix_manifest_v2_38j.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ["status", "candidates_total", "matrix_ready", "partial_price", "partial_fundamentals", "rejected_rows"]}, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity-path", type=Path, default=IDENTITY)
    parser.add_argument("--fundamentals-path", type=Path, default=FUNDAMENTALS)
    parser.add_argument("--prices-path", type=Path, default=PRICES)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    build(args.identity_path, args.fundamentals_path, args.prices_path, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
