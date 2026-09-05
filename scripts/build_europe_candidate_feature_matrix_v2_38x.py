#!/usr/bin/env python3
"""Build deterministic v2.38X Europe candidate feature matrix without
scoring. Joins europe_fundamental_features_v2_38x.csv (this same block,
part 1) with the local Europe price features (v2.38P). No network."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38X-europe-candidate-feature-matrix"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38x_europe_candidate_feature_matrix"
FUNDAMENTALS = OUT / "europe_fundamental_features_v2_38x.csv"
PRICES = ROOT / "outputs/full_universe_source_acquisition/v2_38p_europe_price_features/europe_price_features_v2_38p.csv"

FIELDS = [
    "asset_id", "ticker", "company_name", "company_number", "source_priority",
    "candidate_matrix_status", "fundamental_quality_status", "price_quality_status",
    "evidence_level", "missing_reason",
    "net_margin", "operating_margin", "return_on_assets", "return_on_equity",
    "liabilities_to_assets", "cash_to_assets", "current_ratio",
    "profitability_positive_flag", "balance_strength_flag",
    "return_1m", "return_3m", "return_6m", "return_12m", "volatility_3m", "volatility_6m",
    "max_drawdown_6m", "max_drawdown_12m", "price_vs_sma_50", "price_vs_sma_200",
    "trend_positive_flag", "near_52w_high_flag", "liquidity_available_flag",
    "fundamental_signal_summary", "price_signal_summary",
    "evidence_notes", "scoring_calculated", "ranking_calculated", "recommendation_generated", "phase",
]
QUALITY_FIELDS = ["asset_id", "ticker", "company_name", "candidate_matrix_status", "fundamental_quality_status", "price_quality_status", "evidence_level", "missing_reason", "phase"]
REJECTION_FIELDS = ["asset_id", "ticker", "company_name", "reason", "phase"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def as_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def bool_text(value: bool | None) -> str:
    return "" if value is None else ("true" if value else "false")


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
    fund_ready = (fund or {}).get("feature_quality_status") == "FEATURES_READY"
    price_ready = (price or {}).get("price_quality_status") == "PRICE_FEATURES_READY"
    fund_present, price_present = fund is not None, price is not None
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
        return "No local Europe fundamental feature row available."
    margin = as_float(fund.get("net_margin"))
    parts = []
    if margin is not None:
        parts.append("net margin positive" if margin > 0 else "net margin non-positive")
    if fund.get("balance_strength_flag") == "True":
        parts.append("balance sheet strength flag true")
    return "; ".join(parts) or "Fundamental fields present but limited."


def price_summary(price: dict[str, str] | None) -> str:
    if not price:
        return "No local Europe price feature row available -- v2.38P/O have not collected real price history yet."
    return "Price fields present."


def build(fundamentals_path: Path, prices_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fundamentals, fund_rejected = one_by_asset(read_csv(fundamentals_path))
    prices, price_rejected = one_by_asset(read_csv(prices_path))
    asset_ids = sorted(set(fundamentals) | set(prices))

    rows: list[dict[str, object]] = []
    rejections: list[dict[str, object]] = [{"asset_id": b.get("asset_id", ""), "ticker": b.get("ticker", ""), "company_name": b.get("company_name", ""), "reason": b.get("reason", "invalid_input_row"), "phase": PHASE} for b in fund_rejected + price_rejected]

    for asset_id in asset_ids:
        fund = fundamentals.get(asset_id)
        price = prices.get(asset_id)
        source = fund or price
        if not source or not source.get("ticker") or not source.get("company_name"):
            rejections.append({"asset_id": asset_id, "ticker": (source or {}).get("ticker", ""), "company_name": (source or {}).get("company_name", ""), "reason": "missing_join_identity", "phase": PHASE})
            continue
        status, evidence_level, missing_reason = classify(fund, price)
        net_margin = as_float((fund or {}).get("net_margin"))
        row = {
            "asset_id": asset_id, "ticker": source.get("ticker", ""), "company_name": source.get("company_name", ""),
            "company_number": (fund or {}).get("company_number", ""),
            "source_priority": "fundamental_and_price" if fund and price else ("fundamental_only" if fund else "price_only"),
            "candidate_matrix_status": status, "fundamental_quality_status": (fund or {}).get("feature_quality_status", "MISSING"),
            "price_quality_status": (price or {}).get("price_quality_status", "MISSING"), "evidence_level": evidence_level, "missing_reason": missing_reason,
            "net_margin": (fund or {}).get("net_margin", ""), "operating_margin": (fund or {}).get("operating_margin", ""),
            "return_on_assets": (fund or {}).get("return_on_assets", ""), "return_on_equity": (fund or {}).get("return_on_equity", ""),
            "liabilities_to_assets": (fund or {}).get("liabilities_to_assets", ""), "cash_to_assets": (fund or {}).get("cash_to_assets", ""),
            "current_ratio": (fund or {}).get("current_ratio", ""),
            "profitability_positive_flag": (fund or {}).get("profitability_positive_flag", ""), "balance_strength_flag": (fund or {}).get("balance_strength_flag", ""),
            "fundamental_signal_summary": signal_summary(fund), "price_signal_summary": price_summary(price),
            "evidence_notes": "Prepared for future scoring; no recommendation language or ranking emitted.",
            "scoring_calculated": False, "ranking_calculated": False, "recommendation_generated": False, "phase": PHASE,
        }
        for field in ["return_1m", "return_3m", "return_6m", "return_12m", "volatility_3m", "volatility_6m", "max_drawdown_6m", "max_drawdown_12m", "price_vs_sma_50", "price_vs_sma_200", "trend_positive_flag", "near_52w_high_flag", "liquidity_available_flag"]:
            row[field] = (price or {}).get(field, "")
        rows.append(row)

    rows.sort(key=lambda r: str(r["asset_id"]))
    quality = [{f: row.get(f, "") for f in QUALITY_FIELDS} for row in rows]
    write_csv(output_dir / "europe_candidate_feature_matrix_v2_38x.csv", FIELDS, rows)
    write_csv(output_dir / "europe_candidate_feature_matrix_quality_v2_38x.csv", QUALITY_FIELDS, quality)
    write_csv(output_dir / "europe_candidate_feature_matrix_rejections_v2_38x.csv", REJECTION_FIELDS, rejections)

    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["candidate_matrix_status"])
        counts[key] = counts.get(key, 0) + 1
    joined_both = sum(1 for a in asset_ids if a in fundamentals and a in prices)
    report = {
        "phase": PHASE, "status": "COMPLETED_EUROPE_CANDIDATE_FEATURE_MATRIX_NOT_SCORING",
        "candidates_total": len(rows), "matrix_ready": counts.get("CANDIDATE_MATRIX_READY", 0),
        "partial_price": counts.get("CANDIDATE_MATRIX_PARTIAL_PRICE", 0), "partial_fundamentals": counts.get("CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS", 0),
        "insufficient_evidence": counts.get("CANDIDATE_MATRIX_INSUFFICIENT_EVIDENCE", 0), "blocked": counts.get("CANDIDATE_MATRIX_BLOCKED", 0),
        "fundamental_input_companies": len(fundamentals), "price_input_companies": len(prices), "joined_both": joined_both,
        "only_fundamentals": len(fundamentals) - joined_both, "only_price": len(prices) - joined_both, "rejected_rows": len(rejections),
        "note": "price_input_companies is 0 because v2.38O/P have not collected any real Europe price history yet -- this matrix reflects that honestly rather than inventing price signals.",
        "guardrails": {"network_calls": 0, "phase9c_authorized": False, "ranking_calculated": False, "recommendations_generated": False, "scoring_calculated": False},
    }
    write_text(output_dir / "europe_candidate_feature_matrix_aggregate_report_v2_38x.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_text(output_dir / "README.md", "# v2.38X Europe candidate feature matrix\n\nCombines local Europe fundamental features (v2.38X part 1, from the real v2.38W iXBRL extraction) with local Europe price features (v2.38P) into a traceable candidate matrix for future scoring. Real price coverage is 0 today (v2.38O/P have not collected any Europe price history) -- reflected honestly, not invented. No scoring, ranking or recommendations.\n")
    write_text(output_dir / "EUROPE_CANDIDATE_FEATURE_MATRIX_CONTRACT_v2_38x.md", "# Europe Candidate Feature Matrix Contract v2.38X\n\nJoins Europe fundamental features and local Europe price features. Output is preparation for a future scoring phase only. Not financial advice, does not predict returns.\n")
    write_text(output_dir / "PHASE9X_EUROPE_CANDIDATE_MATRIX_GATE_v2_38x.md", f"# Phase 9X Europe Candidate Matrix Gate\n\nStatus: {report['status']}\n\n- Candidates: {report['candidates_total']}\n- Ready matrix rows: {report['matrix_ready']}\n- Partial price rows: {report['partial_price']}\n- Partial fundamental rows: {report['partial_fundamentals']}\n- Rejected rows: {report['rejected_rows']}\n\nGuardrails: no network calls, no scoring, no ranking, no recommendations, no phase 9C authorization.\n")

    public = ["README.md", "EUROPE_CANDIDATE_FEATURE_MATRIX_CONTRACT_v2_38x.md", "PHASE9X_EUROPE_CANDIDATE_MATRIX_GATE_v2_38x.md", "europe_candidate_feature_matrix_v2_38x.csv", "europe_candidate_feature_matrix_quality_v2_38x.csv", "europe_candidate_feature_matrix_rejections_v2_38x.csv", "europe_candidate_feature_matrix_aggregate_report_v2_38x.json"]
    manifest = {"phase": PHASE, "outputs": {name: {"bytes": (output_dir / name).stat().st_size, "sha256": sha256(output_dir / name)} for name in public}, "guardrails": report["guardrails"]}
    write_text(output_dir / "europe_candidate_feature_matrix_manifest_v2_38x.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fundamentals-path", type=Path, default=FUNDAMENTALS)
    parser.add_argument("--prices-path", type=Path, default=PRICES)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.fundamentals_path, args.prices_path, args.output_dir)
    print(json.dumps({k: report[k] for k in ["status", "candidates_total", "matrix_ready", "partial_price", "partial_fundamentals", "rejected_rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
