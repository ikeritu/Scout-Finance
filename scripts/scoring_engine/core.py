from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

PILLARS = ("quality", "growth", "valuation", "momentum", "risk")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _available_on(record: dict, as_of: str) -> bool:
    available = record.get("publication_date") or record.get("filing_date")
    return not available or available <= as_of


def latest_fundamentals(records: list[dict], as_of: str) -> tuple[dict[str, dict[str, float]], dict[str, list[str]]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    flags: dict[str, list[str]] = defaultdict(list)
    for record in records:
        asset = record.get("asset_id") or record.get("pilot_id")
        if not asset or record.get("value") is None or not _available_on(record, as_of):
            continue
        # Phase-5 canonical rows deliberately remain "pending": validation is
        # stored in the separate block-H report/detail rather than rewriting
        # licensed normalized rows. Schema-rejected rows never reached this file.
        if record.get("validation_status") not in {"pending", "passed", "flagged"}:
            continue
        grouped[(asset, record["metric"])].append(record)
        flags[asset].extend(record.get("quality_flags") or [])
    values: dict[str, dict[str, float]] = defaultdict(dict)
    for (asset, metric), candidates in grouped.items():
        candidates.sort(key=lambda r: (
            r.get("publication_date") or r.get("filing_date") or "0000-00-00",
            r.get("period_end") or "0000-00-00",
            r.get("restatement_status") == "restated",
            r.get("consolidation_scope") == "consolidated",
            r.get("record_id", ""),
        ))
        values[asset][metric] = float(candidates[-1]["value"])
    return dict(values), {k: sorted(set(v)) for k, v in flags.items()}


def load_prices(raw_dirs: list[Path], as_of: str) -> tuple[dict[str, list[tuple[str, float]]], dict[str, dict]]:
    series: dict[str, list[tuple[str, float]]] = {}
    pilots: dict[str, dict] = {}
    for raw_dir in raw_dirs:
        if not raw_dir.exists():
            continue
        for path in sorted(raw_dir.glob("P*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            pilot = payload["pilot"]
            asset = pilot["pilot_id"]
            rows = []
            for row in payload["prices"]:
                d = row.get("Date")
                close = row.get("AdjC", row.get("Adjusted_close", row.get("AdjClose", row.get("Close", row.get("C")))))
                if d and d <= as_of and close is not None and float(close) > 0:
                    rows.append((d, float(close)))
            rows.sort()
            if rows:
                series[asset] = rows
                pilots[asset] = pilot
    return series, pilots


def price_factors(rows: list[tuple[str, float]]) -> dict[str, float]:
    closes = [v for _, v in rows]
    out: dict[str, float] = {}
    for name, sessions in (("return_3m", 64), ("return_6m", 127), ("return_12m", 253)):
        if len(closes) >= sessions:
            out[name] = closes[-1] / closes[-sessions] - 1.0
    if len(closes) >= 200:
        out["distance_sma200"] = closes[-1] / statistics.fmean(closes[-200:]) - 1.0
    if len(closes) >= 253:
        window = closes[-253:]
        daily = [window[i] / window[i - 1] - 1.0 for i in range(1, len(window))]
        if len(daily) > 1:
            out["volatility_12m"] = statistics.stdev(daily) * math.sqrt(252)
        peak = window[0]
        max_dd = 0.0
        for value in window:
            peak = max(peak, value)
            max_dd = min(max_dd, value / peak - 1.0)
        out["max_drawdown_12m"] = abs(max_dd)
    out["latest_close"] = closes[-1]
    return out


def build_raw_factors(fundamentals: dict[str, dict[str, float]], prices: dict[str, list[tuple[str, float]]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for asset in sorted(set(fundamentals) | set(prices)):
        factors = {k: v for k, v in fundamentals.get(asset, {}).items() if k in {
            "operating_margin", "net_margin", "roa", "roe_reported", "revenue_growth_yoy", "net_income_growth_yoy"
        }}
        if asset in prices:
            pf = price_factors(prices[asset])
            factors.update({k: v for k, v in pf.items() if k != "latest_close"})
            close = pf["latest_close"]
            eps = fundamentals.get(asset, {}).get("eps_basic")
            bps = fundamentals.get(asset, {}).get("book_value_per_share")
            if eps is not None:
                factors["earnings_yield"] = eps / close
            if bps is not None:
                factors["book_yield"] = bps / close
        result[asset] = factors
    return result


def percentile_scores(raw: dict[str, dict[str, float]], contract: dict) -> dict[str, dict[str, float]]:
    scores: dict[str, dict[str, float]] = defaultdict(dict)
    for factor in contract["factors"]:
        fid = factor["id"]
        pairs = sorted((value, asset) for asset, values in raw.items() if (value := values.get(fid)) is not None and math.isfinite(value))
        n = len(pairs)
        if not n:
            continue
        by_value: dict[float, list[str]] = defaultdict(list)
        for value, asset in pairs:
            by_value[value].append(asset)
        position = 0
        for value in sorted(by_value):
            assets = sorted(by_value[value])
            midrank = position + (len(assets) - 1) / 2
            percentile = 50.0 if n == 1 else 100.0 * midrank / (n - 1)
            if factor["direction"] == "lower":
                percentile = 100.0 - percentile
            for asset in assets:
                scores[asset][fid] = round(percentile, 8)
            position += len(assets)
    return dict(scores)


def score_assets(raw: dict[str, dict[str, float]], normalized: dict[str, dict[str, float]], contract: dict) -> list[dict]:
    factor_map = {f["id"]: f for f in contract["factors"]}
    rows = []
    for asset in sorted(raw):
        available = normalized.get(asset, {})
        effective_weight = sum(factor_map[f]["weight"] for f in available)
        anomaly = any(abs(raw[asset].get(m, 0.0)) > contract["anomaly_policy"]["absolute_margin_limit"] for m in ("operating_margin", "net_margin"))
        status = "REVIEW_REQUIRED" if anomaly else ("ELIGIBLE_PARTIAL" if effective_weight >= contract["minimum_effective_weight"] else "BLOCKED")
        contributions = {}
        total = None
        pillar_scores = {}
        if status == "ELIGIBLE_PARTIAL":
            total = 0.0
            pillar_num, pillar_den = defaultdict(float), defaultdict(float)
            for fid, score in available.items():
                factor = factor_map[fid]
                effective = factor["weight"] / effective_weight
                contributions[fid] = round(score * effective, 8)
                total += score * effective
                pillar_num[factor["pillar"]] += score * factor["weight"]
                pillar_den[factor["pillar"]] += factor["weight"]
            pillar_scores = {p: round(pillar_num[p] / pillar_den[p], 8) for p in pillar_num}
        confidence = "NOT_RANKABLE"
        if status == "ELIGIBLE_PARTIAL":
            confidence = next((label for label in ("HIGH", "MEDIUM", "LOW") if effective_weight >= contract["confidence_thresholds"][label]), "LOW")
        rows.append({
            "asset_id": asset, "eligibility_status": status, "confidence": confidence,
            "coverage_weight": round(effective_weight, 8), "total_score": None if total is None else round(total, 8),
            "raw_factors": raw[asset], "normalized_factors": available, "contributions": contributions,
            "pillar_scores": pillar_scores, "review_reasons": ["absolute_margin_outside_300pct"] if anomaly else [],
        })
    eligible = [r for r in rows if r["total_score"] is not None]
    eligible.sort(key=lambda r: (-r["total_score"], -r["coverage_weight"], -r["pillar_scores"].get("quality", -1), -r["pillar_scores"].get("risk", -1), r["asset_id"]))
    for rank, row in enumerate(eligible, 1):
        row["rank"] = rank
    return rows


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
