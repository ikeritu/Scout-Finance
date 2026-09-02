#!/usr/bin/env python3
"""Build deterministic v2.38H US price features from local histories only."""
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
CONTRACT = ROOT / "config/us_price_features_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38h_us_price_features"
FEATURE_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "price_rows", "date_start",
    "date_end", "trading_days_1y", "adjusted_prices_available",
    "price_feature_quality_status", "features_calculated", "features_missing",
    "quality_flags", "return_1m", "return_3m", "return_6m", "return_12m",
    "price_vs_sma_50", "price_vs_sma_200", "sma_50_vs_sma_200",
    "volatility_3m", "volatility_6m", "max_drawdown_6m", "max_drawdown_12m",
    "downside_volatility_6m", "avg_volume_1m", "avg_volume_3m",
    "momentum_consistency_flag", "trend_positive_flag",
    "recent_high_breakout_flag", "near_52w_high_flag",
    "recovery_from_drawdown_flag", "price_acceleration_flag",
    "liquidity_available_flag", "phase",
]
QUALITY_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "price_rows", "date_start",
    "date_end", "features_calculated", "features_missing",
    "price_feature_quality_status", "quality_flags",
]
REJECTION_FIELDS = ["asset_id", "ticker", "feature", "reason", "available_rows", "required_rows", "phase"]
FEATURES = [
    "return_1m", "return_3m", "return_6m", "return_12m", "price_vs_sma_50",
    "price_vs_sma_200", "sma_50_vs_sma_200", "volatility_3m", "volatility_6m",
    "max_drawdown_6m", "max_drawdown_12m", "downside_volatility_6m",
    "avg_volume_1m", "avg_volume_3m", "momentum_consistency_flag",
    "trend_positive_flag", "recent_high_breakout_flag", "near_52w_high_flag",
    "recovery_from_drawdown_flag", "price_acceleration_flag",
    "liquidity_available_flag",
]
WINDOWS = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_candidates(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = read_csv(path)
    candidates = []
    for row in rows:
        if row.get("asset_id") and row.get("ticker"):
            candidates.append({
                "asset_id": row.get("asset_id", ""),
                "ticker": row.get("ticker", ""),
                "company_name": row.get("company_name", ""),
                "exchange": row.get("exchange", ""),
            })
    return candidates


def price_paths(roots: list[Path], candidate: dict[str, str]) -> list[Path]:
    names = {
        candidate["asset_id"],
        candidate["ticker"],
        candidate["ticker"].replace(".", "_"),
        candidate["ticker"].replace("/", "_"),
    }
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for name in names:
            for suffix in (".csv", ".json"):
                p = root / f"{name}{suffix}"
                if p.exists() and p.is_file():
                    paths.append(p)
    return sorted(set(paths))


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


def load_price_file(path: Path) -> tuple[list[dict[str, Any]], bool]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_rows = payload if isinstance(payload, list) else payload.get("prices", [])
    else:
        raw_rows = read_csv(path)
    by_date: dict[str, dict[str, Any]] = {}
    adjusted = False
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        try:
            d = parse_date(row.get("date") or row.get("Date"))
        except (TypeError, ValueError):
            continue
        adj = parse_float(row.get("adjusted_close") or row.get("adj_close") or row.get("Adj Close"))
        close = parse_float(row.get("close") or row.get("Close"))
        selected = adj if adj is not None else close
        if selected is None or selected <= 0:
            continue
        volume = parse_float(row.get("volume") or row.get("Volume"))
        adjusted = adjusted or adj is not None
        by_date[d] = {"date": d, "close": selected, "volume": volume}
    return [by_date[d] for d in sorted(by_date)], adjusted


def calc_return(values: list[float], window: int) -> float | None:
    if len(values) <= window or values[-window - 1] <= 0:
        return None
    return round((values[-1] / values[-window - 1]) - 1, 6)


def daily_returns(values: list[float]) -> list[float]:
    return [(values[i] / values[i - 1]) - 1 for i in range(1, len(values)) if values[i - 1] > 0]


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
            worst = min(worst, (value / peak) - 1)
    return round(worst, 6)


def avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if v is not None and math.isfinite(v)]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 6)


def reject(candidate: dict[str, str], feature: str, reason: str, available: int, required: int) -> dict[str, str]:
    return {
        "asset_id": candidate["asset_id"],
        "ticker": candidate["ticker"],
        "feature": feature,
        "reason": reason,
        "available_rows": str(available),
        "required_rows": str(required),
        "phase": "v2.38H",
    }


def base_row(candidate: dict[str, str]) -> dict[str, Any]:
    row = {field: None for field in FEATURE_FIELDS}
    row.update({
        "asset_id": candidate["asset_id"],
        "ticker": candidate["ticker"],
        "company_name": candidate["company_name"],
        "exchange": candidate["exchange"],
        "price_rows": 0,
        "date_start": "",
        "date_end": "",
        "trading_days_1y": 0,
        "adjusted_prices_available": False,
        "price_feature_quality_status": "INSUFFICIENT_PRICE_EVIDENCE",
        "features_calculated": 0,
        "features_missing": "",
        "quality_flags": "",
        "momentum_consistency_flag": False,
        "trend_positive_flag": False,
        "recent_high_breakout_flag": False,
        "near_52w_high_flag": False,
        "recovery_from_drawdown_flag": False,
        "price_acceleration_flag": False,
        "liquidity_available_flag": False,
        "phase": "v2.38H",
    })
    return row


def build_company(candidate: dict[str, str], prices: list[dict[str, Any]], adjusted: bool) -> tuple[dict[str, Any], list[dict[str, str]]]:
    row = base_row(candidate)
    rejections: list[dict[str, str]] = []
    values = [float(p["close"]) for p in prices]
    volumes = [p.get("volume") for p in prices]
    count = len(values)
    row["price_rows"] = count
    row["adjusted_prices_available"] = adjusted
    row["date_start"] = prices[0]["date"] if prices else ""
    row["date_end"] = prices[-1]["date"] if prices else ""
    row["trading_days_1y"] = min(count, 252)
    if count < 22:
        row["features_missing"] = "|".join(FEATURES)
        row["quality_flags"] = "insufficient_rows"
        return row, [reject(candidate, feature, "insufficient_rows", count, 22) for feature in FEATURES]
    row["return_1m"] = calc_return(values, WINDOWS["1m"])
    row["return_3m"] = calc_return(values, WINDOWS["3m"])
    row["return_6m"] = calc_return(values, WINDOWS["6m"])
    row["return_12m"] = calc_return(values, WINDOWS["12m"])
    if count >= 50:
        sma50 = sum(values[-50:]) / 50
        row["price_vs_sma_50"] = round(values[-1] / sma50 - 1, 6)
    else:
        sma50 = None
    if count >= 200:
        sma200 = sum(values[-200:]) / 200
        row["price_vs_sma_200"] = round(values[-1] / sma200 - 1, 6)
        row["sma_50_vs_sma_200"] = round(sma50 / sma200 - 1, 6) if sma50 else None
    else:
        sma200 = None
    returns = daily_returns(values)
    row["volatility_3m"] = annualized_vol(returns[-63:]) if len(returns) >= 63 else None
    row["volatility_6m"] = annualized_vol(returns[-126:]) if len(returns) >= 126 else None
    row["max_drawdown_6m"] = max_drawdown(values[-126:]) if count >= 126 else None
    row["max_drawdown_12m"] = max_drawdown(values[-252:]) if count >= 252 else None
    negative = [r for r in returns[-126:] if r < 0]
    row["downside_volatility_6m"] = annualized_vol(negative) if len(negative) >= 2 else None
    row["avg_volume_1m"] = avg(volumes[-21:]) if count >= 21 else None
    row["avg_volume_3m"] = avg(volumes[-63:]) if count >= 63 else None
    row["liquidity_available_flag"] = bool(row["avg_volume_1m"] is not None and row["avg_volume_1m"] > 0)
    row["momentum_consistency_flag"] = bool((row["return_1m"] or 0) > 0 and (row["return_3m"] or 0) > 0 and (row["return_6m"] or 0) > 0)
    row["trend_positive_flag"] = bool(row["price_vs_sma_50"] is not None and row["price_vs_sma_50"] > 0 and row["sma_50_vs_sma_200"] is not None and row["sma_50_vs_sma_200"] > 0)
    previous_63_high = max(values[-64:-1]) if count >= 64 else None
    row["recent_high_breakout_flag"] = bool(previous_63_high is not None and values[-1] >= previous_63_high)
    high_52w = max(values[-252:]) if count >= 252 else max(values)
    row["near_52w_high_flag"] = bool(high_52w > 0 and values[-1] >= high_52w * 0.9)
    dd12 = row["max_drawdown_12m"]
    row["recovery_from_drawdown_flag"] = bool(dd12 is not None and dd12 <= -0.25 and (row["return_3m"] or 0) > 0.15)
    row["price_acceleration_flag"] = bool(row["return_1m"] is not None and row["return_3m"] is not None and row["return_1m"] > row["return_3m"] / 3 and row["return_3m"] > 0)
    missing: list[str] = []
    required = {
        "return_1m": 22, "return_3m": 64, "return_6m": 127, "return_12m": 253,
        "price_vs_sma_50": 50, "price_vs_sma_200": 200, "sma_50_vs_sma_200": 200,
        "volatility_3m": 64, "volatility_6m": 127, "max_drawdown_6m": 126,
        "max_drawdown_12m": 252, "downside_volatility_6m": 127,
        "avg_volume_1m": 21, "avg_volume_3m": 63,
    }
    for feature in FEATURES:
        if row.get(feature) in {None, ""}:
            missing.append(feature)
            rejections.append(reject(candidate, feature, "insufficient_or_missing_price_evidence", count, required.get(feature, 22)))
    calculated = [feature for feature in FEATURES if row.get(feature) not in {None, ""}]
    row["features_calculated"] = len(calculated)
    row["features_missing"] = "|".join(sorted(set(missing)))
    flags = []
    if not adjusted:
        flags.append("adjusted_prices_unavailable")
    if count < 252:
        flags.append("less_than_252_sessions")
    if not row["liquidity_available_flag"]:
        flags.append("volume_unavailable")
    row["quality_flags"] = "|".join(flags)
    if row["features_calculated"] >= 17 and count >= 252:
        row["price_feature_quality_status"] = "PRICE_FEATURES_READY"
    elif row["features_calculated"] > 0:
        row["price_feature_quality_status"] = "PRICE_FEATURES_PARTIAL"
    else:
        row["price_feature_quality_status"] = "INSUFFICIENT_PRICE_EVIDENCE"
    return row, rejections


def discover_roots(contract: dict[str, Any], override: Path | None) -> list[Path]:
    if override:
        return [override]
    return [ROOT / p for p in contract["local_price_roots"]]


def build(candidates_path: Path, output_dir: Path, price_root: Path | None = None) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    candidates = load_candidates(candidates_path)
    roots = discover_roots(contract, price_root)
    feature_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    rejection_rows: list[dict[str, str]] = []
    discovered_files: list[Path] = []
    for candidate in candidates:
        paths = price_paths(roots, candidate)
        if not paths:
            continue
        prices, adjusted = load_price_file(paths[0])
        discovered_files.append(paths[0])
        row, rejections = build_company(candidate, prices, adjusted)
        feature_rows.append(row)
        quality_rows.append({field: row.get(field) for field in QUALITY_FIELDS})
        rejection_rows.extend(rejections)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not discovered_files:
        status = "PRICE_FEATURES_BLOCKED_NO_LOCAL_US_PRICE_HISTORY"
        for candidate in candidates:
            rejection_rows.extend(reject(candidate, feature, "no_local_us_price_history", 0, 22) for feature in FEATURES)
    else:
        status = "COMPLETED_US_PRICE_FEATURES_NOT_SCORING"
    write_csv(output_dir / "us_price_features_v2_38h.csv", [{field: as_csv_value(row.get(field)) for field in FEATURE_FIELDS} for row in feature_rows], FEATURE_FIELDS)
    write_csv(output_dir / "us_price_feature_quality_v2_38h.csv", [{field: as_csv_value(row.get(field)) for field in QUALITY_FIELDS} for row in quality_rows], QUALITY_FIELDS)
    write_csv(output_dir / "us_price_feature_rejections_v2_38h.csv", rejection_rows, REJECTION_FIELDS)
    quality_counts = Counter(row.get("price_feature_quality_status", "") for row in feature_rows)
    coverage = {feature: sum(row.get(feature) not in {None, ""} for row in feature_rows) for feature in FEATURES}
    report = {
        "phase": "v2.38H-us-price-features",
        "status": status,
        "companies_candidates": len(candidates),
        "companies_input": len(feature_rows),
        "companies_price_features_ready": quality_counts["PRICE_FEATURES_READY"],
        "companies_price_features_partial": quality_counts["PRICE_FEATURES_PARTIAL"],
        "companies_insufficient_price_evidence": quality_counts["INSUFFICIENT_PRICE_EVIDENCE"],
        "price_files_discovered": len(discovered_files),
        "feature_coverage": dict(sorted(coverage.items())),
        "quality_status_counts": dict(sorted({k: v for k, v in quality_counts.items() if k}.items())),
        "rejected_rows": len(rejection_rows),
        "raw_cache_published": False,
        "guardrails": {
            "network_calls": 0,
            "phase9c_authorized": False,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
        },
    }
    (output_dir / "us_price_feature_aggregate_report_v2_38h.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "README.md").write_text("# v2.38H US price features\n\nBuilds deterministic US price features from local price histories only. If no local US price history exists, the phase closes fail-closed without invented data. No network, scoring, ranking or recommendations.\n", encoding="utf-8", newline="\n")
    (output_dir / "US_PRICE_FEATURES_CONTRACT_v2_38h.md").write_text("# US Price Features Contract v2.38H\n\nThis phase converts local US price histories into comparable price features. It does not authorize network calls, scoring, ranking, recommendations, predictions, phase 9C, broker actions or trading.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9H US Price Features Gate v2.38H

Decision: {report['status']}

- Candidate companies: {report['companies_candidates']}
- Companies with local price input: {report['companies_input']}
- Companies price features ready: {report['companies_price_features_ready']}
- Companies price features partial: {report['companies_price_features_partial']}
- Companies insufficient price evidence: {report['companies_insufficient_price_evidence']}
- Price files discovered: {report['price_files_discovered']}
- Rejected rows: {report['rejected_rows']}
- Raw cache published: false

This phase does not calculate final scores, rankings, recommendations, predictions, broker actions, trading or phase 9C signals.
"""
    (output_dir / "PHASE9H_US_PRICE_FEATURES_GATE_v2_38h.md").write_text(gate, encoding="utf-8", newline="\n")
    manifest = {
        "phase": "v2.38H-us-price-features",
        "decision": status,
        "inputs": {
            rel(candidates_path): {"bytes": candidates_path.stat().st_size if candidates_path.exists() else 0, "sha256": sha256(candidates_path) if candidates_path.exists() else ""},
        },
        "price_roots_checked": [rel(root) for root in roots],
        "outputs": {},
        "guardrails": report["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.is_file() and path.name != "us_price_features_manifest_v2_38h.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (output_dir / "us_price_features_manifest_v2_38h.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates-path", type=Path, default=ROOT / contract["input_us_feature_quality"])
    parser.add_argument("--price-root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.candidates_path, args.output_dir, args.price_root)
    print(json.dumps({
        "status": report["status"],
        "companies_input": report["companies_input"],
        "companies_price_features_ready": report["companies_price_features_ready"],
        "companies_price_features_partial": report["companies_price_features_partial"],
        "companies_insufficient_price_evidence": report["companies_insufficient_price_evidence"],
        "recommendations_generated": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
