from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_SCOUT = ROOT / "outputs" / "scouting"
OUT_SCORE = ROOT / "outputs" / "scoring"

INPUT = OUT_SCOUT / "active_real_universe_top_candidates.csv"
OUT_CANDIDATES = OUT_SCOUT / "local_score_v0_candidates.csv"
OUT_ACTIVE = OUT_SCOUT / "active_real_universe_top_candidates.csv"
OUT_BREAKDOWN = OUT_SCORE / "local_score_v0_breakdown.csv"
OUT_SUMMARY = OUT_SCORE / "local_score_v0_summary.json"
OUT_REPORT = OUT_SCORE / "local_score_v0_report.md"

SCORE_METHOD = "local_score_v0"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def norm(v: Any) -> str:
    return str(v or "").strip()


def up(v: Any) -> str:
    return norm(v).upper().replace("$", "")


def fl(v: Any) -> float | None:
    try:
        if norm(v) == "":
            return None
        x = float(v)
        if math.isnan(x):
            return None
        return x
    except Exception:
        return None


def clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def metadata_component(row: dict[str, Any]) -> float:
    fields = ["ticker", "company_name", "exchange", "country", "sector", "industry"]
    filled = sum(1 for f in fields if norm(row.get(f)))
    return round(100.0 * filled / len(fields), 2)


def market_data_component(row: dict[str, Any]) -> float:
    score = 0.0
    if fl(row.get("regular_market_price")) or fl(row.get("price_at_signal")):
        score += 25
    if fl(row.get("market_cap")):
        score += 25
    if fl(row.get("volume")):
        score += 20
    if fl(row.get("relative_volume")):
        score += 10
    if fl(row.get("change_1d")) is not None:
        score += 5
    if fl(row.get("change_5d")) is not None:
        score += 7.5
    if fl(row.get("change_20d")) is not None:
        score += 7.5
    return round(clamp(score), 2)


def liquidity_component(row: dict[str, Any]) -> float:
    volume = fl(row.get("volume"))
    mcap = fl(row.get("market_cap"))
    score = 50.0

    if volume is None:
        score -= 25
    elif volume >= 1_000_000:
        score += 25
    elif volume >= 100_000:
        score += 15
    else:
        score -= 10

    if mcap is None:
        score -= 15
    elif mcap >= 10_000_000_000:
        score += 25
    elif mcap >= 1_000_000_000:
        score += 15
    else:
        score += 0

    return round(clamp(score), 2)


def momentum_component(row: dict[str, Any]) -> float:
    c1 = fl(row.get("change_1d"))
    c5 = fl(row.get("change_5d"))
    c20 = fl(row.get("change_20d"))

    values = [v for v in [c1, c5, c20] if v is not None]
    if not values:
        return 50.0

    # Values are ratios. Convert to percentage points for human rules.
    pct_values = [v * 100.0 for v in values]
    avg = sum(pct_values) / len(pct_values)

    score = 60.0
    if -10 <= avg <= 15:
        score += 20
    elif -25 <= avg <= 35:
        score += 5
    else:
        score -= 20

    if any(abs(v) > 50 for v in pct_values):
        score -= 25

    return round(clamp(score), 2)


def data_quality_component(row: dict[str, Any]) -> float:
    status = norm(row.get("stage3_status"))
    provider = norm(row.get("market_data_provider"))
    errors = norm(row.get("error"))

    score = 70.0

    if status == "MARKET_DATA_SCORE_MANUAL":
        score += 20
    elif status == "MARKET_DATA_SCORE_YFINANCE":
        score += 15
    elif status == "METADATA_SCORE_FALLBACK":
        score -= 25
    elif status.startswith("MARKET_DATA"):
        score += 5

    if provider == "manual_market_data.csv":
        score += 5

    if errors:
        score -= 20

    return round(clamp(score), 2)


def penalty_component(row: dict[str, Any]) -> float:
    penalty = 0.0

    if not (fl(row.get("regular_market_price")) or fl(row.get("price_at_signal"))):
        penalty += 12
    if fl(row.get("market_cap")) is None:
        penalty += 8
    if fl(row.get("volume")) is None:
        penalty += 8

    for col in ["change_1d", "change_5d", "change_20d"]:
        value = fl(row.get(col))
        if value is not None and abs(value * 100.0) > 50:
            penalty += 8

    if norm(row.get("stage3_status")) == "METADATA_SCORE_FALLBACK":
        penalty += 15

    if norm(row.get("error")):
        penalty += 10

    return round(clamp(penalty, 0, 60), 2)


def category(score: float) -> str:
    if score >= 85:
        return "local_score_high"
    if score >= 70:
        return "local_score_medium"
    if score >= 55:
        return "local_score_watch"
    return "local_score_low"


def reason(row: dict[str, Any], comps: dict[str, float], total: float) -> str:
    positives: list[str] = []
    negatives: list[str] = []

    if comps["market_data_component_score"] >= 80:
        positives.append("datos de mercado completos")
    if comps["liquidity_component_score"] >= 80:
        positives.append("liquidez/tamaño razonables")
    if comps["momentum_component_score"] >= 75:
        positives.append("momentum sin extremos")
    if comps["data_quality_component_score"] >= 85:
        positives.append("buena calidad/fuente de datos")

    if comps["penalty_score"] >= 20:
        negatives.append("penalizaciones por datos faltantes o extremos")
    if norm(row.get("stage3_status")) == "METADATA_SCORE_FALLBACK":
        negatives.append("sin market data usable")
    if norm(row.get("error")):
        negatives.append("errores de proveedor")

    pos = ", ".join(positives) if positives else "sin fortalezas destacadas"
    neg = ", ".join(negatives) if negatives else "sin alertas fuertes"

    return f"LOCAL_SCORE_V0 {total:.2f}: sube por {pos}; revisar por {neg}. No es recomendación financiera."


def score_row(row: dict[str, Any]) -> dict[str, Any]:
    comps = {
        "metadata_component_score": metadata_component(row),
        "market_data_component_score": market_data_component(row),
        "liquidity_component_score": liquidity_component(row),
        "momentum_component_score": momentum_component(row),
        "data_quality_component_score": data_quality_component(row),
        "penalty_score": penalty_component(row),
    }

    total = (
        comps["metadata_component_score"] * 0.15
        + comps["market_data_component_score"] * 0.25
        + comps["liquidity_component_score"] * 0.20
        + comps["momentum_component_score"] * 0.15
        + comps["data_quality_component_score"] * 0.25
        - comps["penalty_score"] * 0.25
    )

    total = round(clamp(total), 2)

    out = dict(row)
    out.update(comps)
    out["local_score_v0"] = total
    out["final_stage3_score"] = total
    out["score_priority"] = total
    out["local_score_category"] = category(total)
    out["stage3_category"] = category(total)
    out["category_final"] = category(total)
    out["local_score_status"] = "LOCAL_SCORE_V0"
    out["stage3_status"] = "LOCAL_SCORE_V0"
    out["local_score_method"] = SCORE_METHOD
    out["score_method"] = SCORE_METHOD
    out["local_score_reason"] = reason(row, comps, total)
    out["reason_to_pass_quant"] = out["local_score_reason"]
    out["data_quality_label"] = norm(row.get("data_quality_label")) or norm(row.get("stage3_status"))
    return out


def run_score() -> dict[str, Any]:
    OUT_SCORE.mkdir(parents=True, exist_ok=True)
    OUT_SCOUT.mkdir(parents=True, exist_ok=True)

    input_rows = read_csv(INPUT)
    scored = [score_row(row) for row in input_rows if norm(row.get("ticker"))]
    scored.sort(key=lambda r: fl(r.get("local_score_v0")) or 0, reverse=True)

    breakdown = []
    for r in scored:
        breakdown.append({
            "ticker": r.get("ticker", ""),
            "company_name": r.get("company_name", ""),
            "local_score_v0": r.get("local_score_v0", ""),
            "local_score_category": r.get("local_score_category", ""),
            "metadata_component_score": r.get("metadata_component_score", ""),
            "market_data_component_score": r.get("market_data_component_score", ""),
            "liquidity_component_score": r.get("liquidity_component_score", ""),
            "momentum_component_score": r.get("momentum_component_score", ""),
            "data_quality_component_score": r.get("data_quality_component_score", ""),
            "penalty_score": r.get("penalty_score", ""),
            "stage3_status": r.get("stage3_status", ""),
            "market_data_provider": r.get("market_data_provider", ""),
            "local_score_reason": r.get("local_score_reason", ""),
        })

    status = "OK" if scored else "EMPTY"
    summary = {
        "phase": "v1.5A",
        "title": "Local Scoring v0",
        "status": status,
        "created_at": now(),
        "rows_input": len(input_rows),
        "rows_scored": len(scored),
        "top_tickers": ", ".join(r.get("ticker", "") for r in scored[:10]),
        "score_method": SCORE_METHOD,
        "openai_called": False,
        "broker_called": False,
        "pipeline_recalculated": False,
        "yfinance_called": False,
        "financial_statement_scoring_recalculated": False,
    }

    write_csv(OUT_CANDIDATES, scored)
    write_csv(OUT_ACTIVE, scored)
    write_csv(OUT_BREAKDOWN, breakdown)
    write_json(OUT_SUMMARY, summary)

    lines = [
        "# Scout Finance — v1.5A Local Scoring v0 Report",
        "",
        f"Status: **{status}**",
        "",
        "## Summary",
        "",
        f"- Rows input: {len(input_rows)}",
        f"- Rows scored: {len(scored)}",
        f"- Top tickers: {summary['top_tickers']}",
        f"- Score method: `{SCORE_METHOD}`",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- Broker called: False",
        "- Pipeline recalculated: False",
        "- yfinance called: False",
        "- Financial statement scoring recalculated: False",
        "",
        "## Score formula",
        "",
        "- metadata 15%",
        "- market data completeness 25%",
        "- liquidity 20%",
        "- momentum 15%",
        "- data quality 25%",
        "- penalty subtraction 25%",
        "",
        "## Candidates",
        "",
    ]

    for r in scored:
        lines.append(f"- `{r.get('ticker')}` — `{r.get('local_score_v0')}` — `{r.get('local_score_category')}` — {r.get('local_score_reason')}")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic local score v0 from active real-universe candidates.")
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args()

    if not args.score:
        parser.print_help()
        return

    summary = run_score()

    print("Scout Finance — v1.5A Local Scoring v0")
    print("=" * 92)
    print(f"Status: {summary['status']}")
    print(f"Rows input: {summary['rows_input']}")
    print(f"Rows scored: {summary['rows_scored']}")
    print(f"Top tickers: {summary['top_tickers']}")
    print(f"Score method: {summary['score_method']}")
    print("OpenAI called: False")
    print("Broker called: False")
    print("Pipeline recalculated: False")
    print("yfinance called: False")
    print("Financial statement scoring recalculated: False")
    print("Report: outputs/scoring/local_score_v0_report.md")


if __name__ == "__main__":
    main()
