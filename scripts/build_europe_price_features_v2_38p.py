#!/usr/bin/env python3
"""Build deterministic v2.38P Europe price features from local raw cache only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_price_features_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38p_europe_price_features"
PHASE = "v2.38P-europe-price-features"
FEATURE_FIELDS = [
    "asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country",
    "home_currency", "provider", "provider_symbol", "price_first_date", "price_last_date",
    "price_rows", "return_1m", "return_3m", "return_6m", "return_12m",
    "volatility_3m", "volatility_6m", "downside_volatility_6m", "max_drawdown_6m",
    "max_drawdown_12m", "price_vs_sma_50", "price_vs_sma_200", "sma_50_vs_sma_200",
    "avg_volume_1m", "avg_volume_3m", "liquidity_available_flag", "trend_positive_flag",
    "momentum_consistency_flag", "near_52w_high_flag", "recent_high_breakout_flag",
    "recovery_from_drawdown_flag", "price_acceleration_flag", "price_quality_status",
    "phase", "scoring_calculated", "ranking_calculated", "recommendations_generated",
    "phase9c_authorized",
]
QUALITY_FIELDS = [
    "asset_id", "ticker", "price_rows", "price_quality_status", "missing_feature_count",
    "rejection_reason", "phase",
]
REJECTION_FIELDS = [
    "asset_id", "ticker", "company_name", "provider_symbol", "rejection_status",
    "rejection_reason", "phase", "scoring_calculated", "ranking_calculated",
    "recommendations_generated", "phase9c_authorized",
]
NUMERIC_FEATURES = [
    "return_1m", "return_3m", "return_6m", "return_12m", "volatility_3m",
    "volatility_6m", "downside_volatility_6m", "max_drawdown_6m", "max_drawdown_12m",
    "price_vs_sma_50", "price_vs_sma_200", "sma_50_vs_sma_200", "avg_volume_1m",
    "avg_volume_3m",
]
FLAG_FEATURES = [
    "liquidity_available_flag", "trend_positive_flag", "momentum_consistency_flag",
    "near_52w_high_flag", "recent_high_breakout_flag", "recovery_from_drawdown_flag",
    "price_acceleration_flag",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def parse_date(value: Any) -> str:
    text = str(value or "").strip()[:10]
    date.fromisoformat(text)
    return text


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return str(round(value, 6))
    return str(value)


def load_prices(path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = read_csv(path)
    required_any = {"date", "Date"}
    if not raw:
        return [], "empty_price_history"
    by_date: dict[str, dict[str, Any]] = {}
    for row in raw:
        if not required_any.intersection(row):
            return [], "missing_date_column"
        try:
            d = parse_date(row.get("date") or row.get("Date"))
        except (TypeError, ValueError):
            return [], "invalid_date"
        close = parse_float(row.get("adjusted_close") or row.get("adj_close") or row.get("Adj Close") or row.get("close") or row.get("Close"))
        if close is None or close <= 0:
            return [], "invalid_close"
        volume = parse_float(row.get("volume") or row.get("Volume"))
        by_date[d] = {"date": d, "close": close, "volume": volume}
    return [by_date[d] for d in sorted(by_date)], ""


def daily_returns(values: list[float]) -> list[float]:
    return [(values[i] / values[i - 1]) - 1 for i in range(1, len(values)) if values[i - 1] > 0]


def calc_return(values: list[float], window: int) -> float | None:
    if len(values) <= window or values[-window - 1] <= 0:
        return None
    return round(values[-1] / values[-window - 1] - 1, 6)


def annualized_vol(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    return round(statistics.stdev(returns) * math.sqrt(252), 6)


def max_drawdown(values: list[float]) -> float | None:
    if not values:
        return None
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1)
    return round(worst, 6)


def avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if v is not None and math.isfinite(v)]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 6)


def present_number(value: Any) -> float | None:
    return value if isinstance(value, (int, float)) and math.isfinite(value) else None


def rejection(candidate: dict[str, str], status: str, reason: str) -> dict[str, str]:
    return {
        "asset_id": candidate.get("asset_id", ""),
        "ticker": candidate.get("ticker", ""),
        "company_name": candidate.get("company_name", ""),
        "provider_symbol": candidate.get("provider_symbol", ""),
        "rejection_status": status,
        "rejection_reason": reason,
        "phase": PHASE,
        "scoring_calculated": "false",
        "ranking_calculated": "false",
        "recommendations_generated": "false",
        "phase9c_authorized": "false",
    }


def base_feature_row(candidate: dict[str, str], rows_count: int, first: str, last: str, status: str) -> dict[str, Any]:
    row = {field: "" for field in FEATURE_FIELDS}
    for field in ["asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country", "home_currency", "provider", "provider_symbol"]:
        row[field] = candidate.get(field, "")
    row.update({
        "price_first_date": first,
        "price_last_date": last,
        "price_rows": str(rows_count),
        "price_quality_status": status,
        "phase": PHASE,
        "scoring_calculated": "false",
        "ranking_calculated": "false",
        "recommendations_generated": "false",
        "phase9c_authorized": "false",
    })
    for flag in FLAG_FEATURES:
        row[flag] = "false"
    return row


def build_one(candidate: dict[str, str], prices: list[dict[str, Any]], min_ready: int, min_partial: int) -> tuple[dict[str, Any], dict[str, str], list[dict[str, str]]]:
    values = [float(p["close"]) for p in prices]
    volumes = [p.get("volume") for p in prices]
    count = len(values)
    first = prices[0]["date"] if prices else ""
    last = prices[-1]["date"] if prices else ""
    status = "EUROPE_PRICE_FEATURES_READY" if count >= min_ready else "EUROPE_PRICE_FEATURES_PARTIAL" if count >= min_partial else "EUROPE_PRICE_FEATURES_INSUFFICIENT"
    row = base_feature_row(candidate, count, first, last, status)
    rejections: list[dict[str, str]] = []
    if count < min_partial:
        quality = {
            "asset_id": candidate["asset_id"], "ticker": candidate["ticker"], "price_rows": str(count),
            "price_quality_status": status, "missing_feature_count": str(len(NUMERIC_FEATURES)),
            "rejection_reason": "insufficient_price_history", "phase": PHASE,
        }
        rejections.append(rejection(candidate, status, "insufficient_price_history"))
        return row, quality, rejections
    returns = daily_returns(values)
    row["return_1m"] = calc_return(values, 21)
    row["return_3m"] = calc_return(values, 63)
    row["return_6m"] = calc_return(values, 126)
    row["return_12m"] = calc_return(values, 252)
    if count >= 50:
        sma50 = sum(values[-50:]) / 50
        row["price_vs_sma_50"] = round(values[-1] / sma50 - 1, 6)
    else:
        sma50 = None
    if count >= 200:
        sma200 = sum(values[-200:]) / 200
        row["price_vs_sma_200"] = round(values[-1] / sma200 - 1, 6)
        row["sma_50_vs_sma_200"] = round(sma50 / sma200 - 1, 6) if sma50 else None
    row["volatility_3m"] = annualized_vol(returns[-63:]) if len(returns) >= 63 else None
    row["volatility_6m"] = annualized_vol(returns[-126:]) if len(returns) >= 126 else None
    row["downside_volatility_6m"] = annualized_vol([r for r in returns[-126:] if r < 0])
    row["max_drawdown_6m"] = max_drawdown(values[-126:]) if count >= 126 else None
    row["max_drawdown_12m"] = max_drawdown(values[-252:]) if count >= 252 else None
    row["avg_volume_1m"] = avg(volumes[-21:]) if count >= 21 else None
    row["avg_volume_3m"] = avg(volumes[-63:]) if count >= 63 else None
    avg_volume_1m = present_number(row["avg_volume_1m"])
    price_vs_sma_50 = present_number(row["price_vs_sma_50"])
    sma_50_vs_sma_200 = present_number(row["sma_50_vs_sma_200"])
    return_1m = present_number(row["return_1m"])
    return_3m = present_number(row["return_3m"])
    return_6m = present_number(row["return_6m"])
    row["liquidity_available_flag"] = avg_volume_1m is not None and avg_volume_1m > 0
    row["trend_positive_flag"] = price_vs_sma_50 is not None and price_vs_sma_50 > 0 and sma_50_vs_sma_200 is not None and sma_50_vs_sma_200 > 0
    row["momentum_consistency_flag"] = all(value is not None and value > 0 for value in [return_1m, return_3m, return_6m])
    high_52w = max(values[-252:]) if count >= 252 else max(values)
    row["near_52w_high_flag"] = high_52w > 0 and values[-1] >= high_52w * 0.9
    previous_63_high = max(values[-64:-1]) if count >= 64 else None
    row["recent_high_breakout_flag"] = previous_63_high is not None and values[-1] >= previous_63_high
    max_drawdown_6m = present_number(row["max_drawdown_6m"])
    row["recovery_from_drawdown_flag"] = return_3m is not None and return_3m > 0 and max_drawdown_6m is not None and max_drawdown_6m < -0.15
    row["price_acceleration_flag"] = return_1m is not None and return_3m is not None and return_1m > return_3m / 3
    missing = [feature for feature in NUMERIC_FEATURES if row.get(feature) in {"", None}]
    if count < min_ready and status == "EUROPE_PRICE_FEATURES_PARTIAL":
        rejections.append(rejection(candidate, status, "partial_price_feature_history"))
    quality = {
        "asset_id": candidate["asset_id"],
        "ticker": candidate["ticker"],
        "price_rows": str(count),
        "price_quality_status": status,
        "missing_feature_count": str(len(missing)),
        "rejection_reason": "partial_price_feature_history" if missing else "",
        "phase": PHASE,
    }
    return {k: as_text(v) for k, v in row.items()}, quality, rejections


def write_docs(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "README.md").write_text(
        "# v2.38P Europe price features\n\n"
        "Builds deterministic Europe price features from local v2.38O raw cache only. "
        "If local price evidence is unavailable, the phase closes fail-closed. "
        "No network calls, scoring, ranking, recommendations, broker actions or Phase 9C authorization are produced.\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "EUROPE_PRICE_FEATURES_CONTRACT_v2_38p.md").write_text(
        "# Europe Price Features Contract v2.38P\n\n"
        "- Input is the v2.38O acquisition plan and local raw cache.\n"
        "- Cboe Europe is rejected as a primary source.\n"
        "- READY requires at least 252 local price rows.\n"
        "- PARTIAL requires at least 120 local price rows.\n"
        "- No network, scoring, ranking, final recommendations, financial advice or broker actions.\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "PHASE9P_EUROPE_PRICE_FEATURES_GATE_v2_38p.md").write_text(
        f"""# Phase 9P Europe Price Features Gate v2.38P

Decision: {report['status']}

- Companies candidates: {report['companies_candidates']}
- Companies input: {report['companies_input']}
- Price features ready: {report['companies_price_features_ready']}
- Price features partial: {report['companies_price_features_partial']}
- Insufficient price evidence: {report['companies_insufficient_price_evidence']}
- Raw cache published: false

This phase does not calculate scores, rankings, recommendations, predictions, broker actions or Phase 9C signals.
""",
        encoding="utf-8",
        newline="\n",
    )


def build(plan_path: Path, price_root: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    plan = read_csv(plan_path)
    features: list[dict[str, Any]] = []
    quality: list[dict[str, str]] = []
    rejections: list[dict[str, str]] = []
    discovered = 0
    for candidate in plan:
        if candidate.get("home_exchange") == "CBOE_EUROPE" or candidate.get("home_mic", "").upper().startswith("CBOE"):
            rejections.append(rejection(candidate, "EUROPE_PRICE_FEATURES_REJECTED_CBOE_SOURCE", "cboe_europe_primary_source_forbidden"))
            quality.append({
                "asset_id": candidate.get("asset_id", ""), "ticker": candidate.get("ticker", ""), "price_rows": "0",
                "price_quality_status": "EUROPE_PRICE_FEATURES_REJECTED_CBOE_SOURCE",
                "missing_feature_count": str(len(NUMERIC_FEATURES)),
                "rejection_reason": "cboe_europe_primary_source_forbidden", "phase": PHASE,
            })
            continue
        path = price_root / f"{candidate.get('asset_id', '')}.csv"
        if not path.exists():
            continue
        discovered += 1
        prices, error = load_prices(path)
        if error:
            status = "EUROPE_PRICE_FEATURES_REJECTED_BAD_SCHEMA"
            features.append(base_feature_row(candidate, 0, "", "", status))
            quality.append({
                "asset_id": candidate.get("asset_id", ""), "ticker": candidate.get("ticker", ""), "price_rows": "0",
                "price_quality_status": status, "missing_feature_count": str(len(NUMERIC_FEATURES)),
                "rejection_reason": error, "phase": PHASE,
            })
            rejections.append(rejection(candidate, status, error))
            continue
        row, qrow, rejects = build_one(candidate, prices, int(contract["min_rows_ready"]), int(contract["min_rows_partial"]))
        features.append(row)
        quality.append(qrow)
        rejections.extend(rejects)
    status_counts = Counter(r["price_quality_status"] for r in features)
    if not features:
        status = "PRICE_FEATURES_BLOCKED_NO_LOCAL_EUROPE_PRICE_HISTORY"
    else:
        status = "COMPLETED_EUROPE_PRICE_FEATURES_NOT_SCORING"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_price_features_v2_38p.csv", features, FEATURE_FIELDS)
    write_csv(output_dir / "europe_price_feature_quality_v2_38p.csv", quality, QUALITY_FIELDS)
    write_csv(output_dir / "europe_price_feature_rejections_v2_38p.csv", rejections, REJECTION_FIELDS)
    coverage = {feature: sum(1 for row in features if row.get(feature) not in {"", None}) for feature in NUMERIC_FEATURES + FLAG_FEATURES}
    report = {
        "phase": PHASE,
        "status": status,
        "companies_candidates": len(plan),
        "companies_input": len(features),
        "price_files_discovered": discovered,
        "companies_price_features_ready": status_counts["EUROPE_PRICE_FEATURES_READY"],
        "companies_price_features_partial": status_counts["EUROPE_PRICE_FEATURES_PARTIAL"],
        "companies_insufficient_price_evidence": status_counts["EUROPE_PRICE_FEATURES_INSUFFICIENT"],
        "rejected_rows": len(rejections),
        "quality_status_counts": dict(sorted(status_counts.items())),
        "feature_coverage": coverage,
        "raw_cache_published": False,
        "guardrails": {
            "network_calls": 0,
            "cboe_europe_source_forbidden": True,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
        },
    }
    (output_dir / "europe_price_feature_aggregate_report_v2_38p.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    write_docs(report, output_dir)
    manifest = {
        "phase": PHASE,
        "decision": status,
        "inputs": {
            rel(plan_path): {"bytes": plan_path.stat().st_size if plan_path.exists() else 0, "sha256": sha256(plan_path) if plan_path.exists() else ""}
        },
        "outputs": {},
        "raw_cache": rel(price_root),
        "guardrails": report["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.is_file() and path.name != "europe_price_features_manifest_v2_38p.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (output_dir / "europe_price_features_manifest_v2_38p.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-path", type=Path, default=ROOT / contract["input_plan"])
    parser.add_argument("--price-root", type=Path, default=ROOT / contract["raw_cache"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.plan_path, args.price_root, args.output_dir)
    print(json.dumps({
        "status": report["status"],
        "companies_input": report["companies_input"],
        "companies_price_features_ready": report["companies_price_features_ready"],
        "companies_price_features_partial": report["companies_price_features_partial"],
        "companies_insufficient_price_evidence": report["companies_insufficient_price_evidence"],
        "recommendations_generated": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
