from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_SCOUT = ROOT / "outputs" / "scouting"
OUT_SCORE = ROOT / "outputs" / "scoring"

INPUT = OUT_SCOUT / "active_real_universe_top_candidates.csv"
OUT_CANDIDATES = OUT_SCOUT / "ranking_explainability_candidates.csv"
OUT_ACTIVE = OUT_SCOUT / "active_real_universe_top_candidates.csv"
OUT_FACTORS = OUT_SCORE / "ranking_explainability_factors.csv"
OUT_SUMMARY = OUT_SCORE / "ranking_explainability_summary.json"
OUT_REPORT = OUT_SCORE / "ranking_explainability_report.md"

METHOD = "ranking_explainability_v0"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def norm(v: Any) -> str:
    return str(v or "").strip()


def fl(v: Any) -> float | None:
    try:
        if norm(v) == "":
            return None
        return float(v)
    except Exception:
        return None


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
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def join(items: list[str]) -> str:
    return " | ".join(dict.fromkeys([x for x in items if x]))


def explain_row(row: dict[str, Any]) -> dict[str, Any]:
    positives: list[str] = []
    negatives: list[str] = []
    missing: list[str] = []
    review: list[str] = []
    badges: list[str] = []

    score = fl(row.get("local_score_v0") or row.get("final_stage3_score")) or 0
    market = fl(row.get("market_data_component_score")) or 0
    liquidity = fl(row.get("liquidity_component_score")) or 0
    momentum = fl(row.get("momentum_component_score")) or 0
    quality = fl(row.get("data_quality_component_score")) or 0
    penalty = fl(row.get("penalty_score")) or 0

    price = fl(row.get("price_at_signal") or row.get("regular_market_price"))
    market_cap = fl(row.get("market_cap"))
    volume = fl(row.get("volume"))
    rel_volume = fl(row.get("relative_volume"))

    status = norm(row.get("stage3_status"))
    provider = norm(row.get("market_data_provider"))
    error = norm(row.get("error"))

    if score >= 85:
        badges.append("alta prioridad local")
    elif score >= 70:
        badges.append("prioridad media local")
    else:
        badges.append("revisión baja")

    if market >= 85:
        positives.append("datos de mercado completos")
        badges.append("datos completos")
    elif market < 60:
        negatives.append("datos de mercado incompletos")

    if liquidity >= 80:
        positives.append("liquidez/tamaño razonables")
        badges.append("liquidez OK")
    elif liquidity < 55:
        negatives.append("liquidez o tamaño débiles")
        review.append("revisar liquidez/market cap")

    if momentum >= 75:
        positives.append("momentum sin extremos")
        badges.append("momentum estable")
    elif momentum < 50:
        negatives.append("momentum extremo o débil")
        review.append("revisar movimientos recientes")

    if quality >= 85:
        positives.append("buena calidad/fuente de datos")
    elif quality < 60:
        negatives.append("calidad de datos limitada")

    if penalty >= 20:
        negatives.append("penalizaciones relevantes")
        review.append("revisar penalizaciones del score")

    if price is None:
        missing.append("precio")
    if market_cap is None:
        missing.append("market cap")
    if volume is None:
        missing.append("volumen")
    if rel_volume is None:
        missing.append("volumen relativo")
    for col, label in [("change_1d", "1D"), ("change_5d", "5D"), ("change_20d", "20D")]:
        if fl(row.get(col)) is None:
            missing.append(label)

    if status == "METADATA_SCORE_FALLBACK":
        negatives.append("sin datos de mercado usable")
        review.append("añadir market data manual")
        badges.append("fallback")
    if provider == "manual_market_data.csv":
        badges.append("manual data")
        review.append("verificar fecha/fuente manual")
    if error:
        negatives.append("error de proveedor")
        review.append("revisar error proveedor")

    if not positives:
        positives.append("sin fortalezas destacadas")
    if not negatives:
        negatives.append("sin alertas fuertes")
    if not review:
        review.append("revisión estándar")

    summary = f"Score {score:.2f}: sube por {', '.join(positives[:3])}; vigilar {', '.join(negatives[:3])}."

    out = dict(row)
    out["explainability_summary"] = summary
    out["positive_factors"] = join(positives)
    out["negative_factors"] = join(negatives)
    out["missing_data_flags"] = join(missing)
    out["review_flags"] = join(review)
    out["explainability_badges"] = join(badges)
    out["explainability_method"] = METHOD
    out["reason_to_pass_quant"] = summary
    return out


def run_explain() -> dict[str, Any]:
    OUT_SCORE.mkdir(parents=True, exist_ok=True)
    OUT_SCOUT.mkdir(parents=True, exist_ok=True)

    input_rows = read_csv(INPUT)
    explained = [explain_row(row) for row in input_rows if norm(row.get("ticker"))]
    explained.sort(key=lambda r: fl(r.get("local_score_v0") or r.get("final_stage3_score")) or 0, reverse=True)

    factors = []
    for row in explained:
        factors.append({
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "local_score_v0": row.get("local_score_v0", row.get("final_stage3_score", "")),
            "explainability_summary": row.get("explainability_summary", ""),
            "positive_factors": row.get("positive_factors", ""),
            "negative_factors": row.get("negative_factors", ""),
            "missing_data_flags": row.get("missing_data_flags", ""),
            "review_flags": row.get("review_flags", ""),
            "explainability_badges": row.get("explainability_badges", ""),
        })

    summary = {
        "phase": "v1.5B",
        "title": "Ranking Explainability",
        "status": "OK" if explained else "EMPTY",
        "created_at": now(),
        "rows_input": len(input_rows),
        "rows_explained": len(explained),
        "top_tickers": ", ".join(row.get("ticker", "") for row in explained[:10]),
        "explainability_method": METHOD,
        "openai_called": False,
        "broker_called": False,
        "pipeline_recalculated": False,
        "yfinance_called": False,
    }

    write_csv(OUT_CANDIDATES, explained)
    write_csv(OUT_ACTIVE, explained)
    write_csv(OUT_FACTORS, factors)
    write_json(OUT_SUMMARY, summary)

    lines = [
        "# Scout Finance — v1.5B Ranking Explainability Report",
        "",
        f"Status: **{summary['status']}**",
        "",
        "## Summary",
        "",
        f"- Rows input: {summary['rows_input']}",
        f"- Rows explained: {summary['rows_explained']}",
        f"- Top tickers: {summary['top_tickers']}",
        f"- Method: `{METHOD}`",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- Broker called: False",
        "- Pipeline recalculated: False",
        "- yfinance called: False",
        "",
        "## Rows",
        "",
    ]
    for row in explained:
        lines.append(f"- `{row.get('ticker')}` — {row.get('explainability_summary')}")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local explainability factors for the current ranking.")
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()

    if not args.explain:
        parser.print_help()
        return

    summary = run_explain()

    print("Scout Finance — v1.5B Ranking Explainability")
    print("=" * 92)
    print(f"Status: {summary['status']}")
    print(f"Rows input: {summary['rows_input']}")
    print(f"Rows explained: {summary['rows_explained']}")
    print(f"Top tickers: {summary['top_tickers']}")
    print(f"Method: {summary['explainability_method']}")
    print("OpenAI called: False")
    print("Broker called: False")
    print("Pipeline recalculated: False")
    print("yfinance called: False")
    print("Report: outputs/scoring/ranking_explainability_report.md")


if __name__ == "__main__":
    main()
