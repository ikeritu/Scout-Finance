# v1.6E5 fundamentals granular tie-breaker packaged
# v1.6C8 data source detection refactor compatible
# v1.6C6 dashboard combined warning final fix compatible
# v1.6C5 dashboard combined source card compatible
# v1.6C4 combined UI final polish compatible
# v1.6C3 active combined ranking normalizer compatible
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCOUTING = ROOT / "outputs" / "scouting"
SCORING = ROOT / "outputs" / "scoring"
FUNDAMENTALS = ROOT / "outputs" / "fundamentals"

ACTIVE = SCOUTING / "active_real_universe_top_candidates.csv"
LOCAL_CANDIDATES = SCOUTING / "local_score_v0_candidates.csv"
FUNDAMENTALS_VALID = FUNDAMENTALS / "manual_fundamentals_valid_rows.csv"

COMBINED_CANDIDATES = SCOUTING / "combined_score_v1_candidates.csv"
BREAKDOWN = SCORING / "combined_score_v1_breakdown.csv"
SUMMARY = SCORING / "combined_score_v1_summary.json"
REPORT = SCORING / "combined_score_v1_report.md"

METHOD = "combined_score_v1"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def norm(value: Any) -> str:
    return str(value or "").strip()


def ticker(value: Any) -> str:
    return norm(value).upper().replace("$", "")


def as_float(value: Any, default: float | None = None) -> float | None:
    try:
        raw = norm(value)
        if not raw or raw.lower() in {"nan", "none", "null", "—"}:
            return default
        number = float(raw)
        if math.isnan(number):
            return default
        return number
    except Exception:
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row.keys():
                if key not in fields:
                    fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_candidates() -> list[dict[str, Any]]:
    if ACTIVE.exists():
        rows = read_csv(ACTIVE)
        if rows:
            return rows
    return read_csv(LOCAL_CANDIDATES)


def load_fundamentals_map() -> dict[str, dict[str, Any]]:
    rows = read_csv(FUNDAMENTALS_VALID)
    return {ticker(row.get("ticker")): row for row in rows if ticker(row.get("ticker"))}


def base_local_score(row: dict[str, Any]) -> float:
    for key in ["local_score_v0", "score", "Score", "combined_score_v1"]:
        value = as_float(row.get(key))
        if value is not None:
            return clamp(value)
    return 50.0


def metadata_score(row: dict[str, Any]) -> float:
    score = base_local_score(row)
    has_sector = bool(norm(row.get("sector") or row.get("Sector")))
    has_industry = bool(norm(row.get("industry") or row.get("Industria")))
    has_exchange = bool(norm(row.get("exchange") or row.get("Exchange")))
    quality = 60.0
    quality += 12.0 if has_sector else -6.0
    quality += 12.0 if has_industry else -6.0
    quality += 8.0 if has_exchange else -4.0
    # Blend with previous local score so the ranking remains stable.
    return round(clamp((quality * 0.45) + (score * 0.55)), 2)


def market_data_score(row: dict[str, Any]) -> float:
    score = base_local_score(row)

    price = as_float(row.get("price") or row.get("Precio"))
    market_cap = as_float(row.get("market_cap") or row.get("market_cap_usd") or row.get("Market Cap"))
    volume = as_float(row.get("volume") or row.get("Volumen"))
    rel_volume = as_float(row.get("relative_volume") or row.get("volume_relative") or row.get("Vol. relativo"))

    one_day = as_float(row.get("change_1d") or row.get("return_1d") or row.get("1D"))
    five_day = as_float(row.get("change_5d") or row.get("return_5d") or row.get("5D"))
    twenty_day = as_float(row.get("change_20d") or row.get("return_20d") or row.get("20D"))

    md = 50.0
    md += 8.0 if price is not None and price > 0 else -12.0
    md += 12.0 if market_cap is not None and market_cap > 1_000_000_000 else (-8.0 if market_cap is None else -4.0)
    md += 10.0 if volume is not None and volume > 500_000 else (-6.0 if volume is None else -2.0)
    md += 5.0 if rel_volume is not None and 0.3 <= rel_volume <= 3.0 else 0.0

    momentum_values = [v for v in [one_day, five_day, twenty_day] if v is not None]
    if momentum_values:
        avg_mom = sum(momentum_values) / len(momentum_values)
        if -5.0 <= avg_mom <= 15.0:
            md += 8.0
        elif avg_mom < -10.0 or avg_mom > 30.0:
            md -= 8.0
        else:
            md += 2.0
    else:
        md -= 4.0

    return round(clamp((md * 0.65) + (score * 0.35)), 2)


def fundamentals_score(f: dict[str, Any] | None) -> tuple[float, list[str], list[str]]:
    if not f:
        return 35.0, [], ["sin fundamentales validados"]

    positives: list[str] = []
    negatives: list[str] = []

    revenue = as_float(f.get("revenue"))
    growth = as_float(f.get("revenue_growth_yoy"))
    gross_margin = as_float(f.get("gross_margin"))
    operating_margin = as_float(f.get("operating_margin"))
    net_margin = as_float(f.get("net_margin"))
    fcf = as_float(f.get("free_cash_flow"))
    cash = as_float(f.get("total_cash"))
    debt = as_float(f.get("total_debt"))

    score = 50.0

    if revenue is not None:
        if revenue >= 50_000_000_000:
            score += 10
            positives.append("escala de ingresos alta")
        elif revenue >= 5_000_000_000:
            score += 6
            positives.append("escala de ingresos razonable")
        elif revenue > 0:
            score += 2
        else:
            score -= 10
            negatives.append("ingresos no positivos")
    else:
        score -= 12
        negatives.append("revenue ausente")

    if growth is not None:
        if growth >= 10:
            score += 10
            positives.append("crecimiento de ingresos fuerte")
        elif growth >= 3:
            score += 6
            positives.append("crecimiento de ingresos positivo")
        elif growth >= 0:
            score += 2
        else:
            score -= 8
            negatives.append("crecimiento negativo")
    else:
        score -= 6
        negatives.append("crecimiento YoY ausente")

    if gross_margin is not None:
        if gross_margin >= 60:
            score += 10
            positives.append("gross margin excelente")
        elif gross_margin >= 40:
            score += 7
            positives.append("gross margin sólido")
        elif gross_margin >= 20:
            score += 2
        else:
            score -= 6
            negatives.append("gross margin bajo")
    else:
        score -= 5
        negatives.append("gross margin ausente")

    if operating_margin is not None:
        if operating_margin >= 30:
            score += 10
            positives.append("operating margin excelente")
        elif operating_margin >= 15:
            score += 6
            positives.append("operating margin positivo")
        elif operating_margin >= 0:
            score += 1
        else:
            score -= 10
            negatives.append("operating margin negativo")
    else:
        score -= 5
        negatives.append("operating margin ausente")

    if net_margin is not None:
        if net_margin >= 20:
            score += 7
            positives.append("net margin fuerte")
        elif net_margin >= 8:
            score += 4
        elif net_margin < 0:
            score -= 8
            negatives.append("net margin negativo")
    else:
        score -= 3

    if fcf is not None:
        if fcf > 0:
            score += 10
            positives.append("free cash flow positivo")
        else:
            score -= 10
            negatives.append("free cash flow negativo")
    else:
        score -= 7
        negatives.append("free cash flow ausente")

    if cash is not None and debt is not None:
        if debt <= 0 and cash > 0:
            score += 6
            positives.append("sin deuda neta aparente")
        elif cash >= debt:
            score += 6
            positives.append("cash cubre deuda")
        elif debt > cash * 3:
            score -= 8
            negatives.append("deuda elevada frente a caja")
        else:
            score += 1
    else:
        score -= 3
        negatives.append("cash/debt incompleto")

    return round(clamp(score), 2), positives, negatives


# >>> v1.6E5 FUNDAMENTALS GRANULAR TIE-BREAKER HELPERS
def revenue_scale_detail_score(revenue: float) -> float:
    if revenue >= 100_000_000_000:
        return 100.0
    if revenue >= 50_000_000_000:
        return 90.0
    if revenue >= 25_000_000_000:
        return 80.0
    if revenue >= 10_000_000_000:
        return 70.0
    if revenue >= 5_000_000_000:
        return 60.0
    return 45.0


def growth_detail_score(growth: float) -> float:
    return clamp(50 + growth * 4, 0, 100)


def margin_detail_score(margin: float, excellent: float) -> float:
    if excellent <= 0:
        return 0.0
    return clamp((margin / excellent) * 100, 0, 100)


def fcf_scale_detail_score(fcf: float) -> float:
    if fcf >= 50_000_000_000:
        return 100.0
    if fcf >= 20_000_000_000:
        return 90.0
    if fcf >= 10_000_000_000:
        return 80.0
    if fcf >= 5_000_000_000:
        return 70.0
    if fcf > 0:
        return 55.0
    return 30.0


def balance_sheet_detail_score(cash: float, debt: float) -> float:
    if debt <= 0:
        return 100.0
    cash_to_debt = cash / debt
    if cash_to_debt >= 1.5:
        return 100.0
    if cash_to_debt >= 1.0:
        return 90.0
    if cash_to_debt >= 0.75:
        return 80.0
    if cash_to_debt >= 0.5:
        return 70.0
    return 55.0


def fundamentals_granular_score_v1_6e(fundamentals: dict[str, object] | None) -> float:
    """Non-production granular fundamentals score used only for exact tie-breaking."""
    if not fundamentals:
        return 0.0

    revenue = as_float(fundamentals.get("revenue"), 0) or 0.0
    growth = as_float(fundamentals.get("revenue_growth_yoy"), 0) or 0.0
    gross = as_float(fundamentals.get("gross_margin"), 0) or 0.0
    operating = as_float(fundamentals.get("operating_margin"), 0) or 0.0
    net = as_float(fundamentals.get("net_margin"), 0) or 0.0
    fcf = as_float(fundamentals.get("free_cash_flow"), 0) or 0.0
    cash = as_float(fundamentals.get("total_cash"), 0) or 0.0
    debt = as_float(fundamentals.get("total_debt"), 0) or 0.0

    score = (
        revenue_scale_detail_score(revenue) * 0.15
        + growth_detail_score(growth) * 0.20
        + margin_detail_score(gross, 65.0) * 0.15
        + margin_detail_score(operating, 40.0) * 0.15
        + margin_detail_score(net, 35.0) * 0.10
        + fcf_scale_detail_score(fcf) * 0.15
        + balance_sheet_detail_score(cash, debt) * 0.10
    )

    return round(clamp(score, 0, 100), 2)


def exact_component_tie_key(row: dict[str, object]) -> tuple[float, float, float, float]:
    return (
        round(as_float(row.get("combined_score_v1"), 0) or 0.0, 4),
        round(as_float(row.get("metadata_score_component"), 0) or 0.0, 4),
        round(as_float(row.get("market_data_score_component"), 0) or 0.0, 4),
        round(as_float(row.get("fundamentals_score_component"), 0) or 0.0, 4),
    )


def annotate_exact_component_ties(rows: list[dict[str, object]]) -> None:
    counts: dict[tuple[float, float, float, float], int] = {}

    for row in rows:
        key = exact_component_tie_key(row)
        counts[key] = counts.get(key, 0) + 1

    for row in rows:
        key = exact_component_tie_key(row)
        is_tie = counts.get(key, 0) > 1
        row["tie_status"] = "EXACT_COMPONENT_TIE" if is_tie else "NO_TIE"
        row["calibration_warning"] = (
            "Empate exacto de componentes; orden secundario por granularidad fundamental."
            if is_tie
            else ""
        )
# <<< v1.6E5 FUNDAMENTALS GRANULAR TIE-BREAKER HELPERS


def category(score: float) -> str:
    if score >= 85:
        return "combined_score_high"
    if score >= 70:
        return "combined_score_medium"
    if score >= 55:
        return "combined_score_watch"
    return "combined_score_low"


def human_category(value: str) -> str:
    return {
        "combined_score_high": "Alta prioridad combinada",
        "combined_score_medium": "Prioridad media combinada",
        "combined_score_watch": "Vigilar con fundamentales",
        "combined_score_low": "Prioridad baja combinada",
    }.get(value, value)


def run() -> dict[str, Any]:
    candidates = load_candidates()
    fundamentals = load_fundamentals_map()

    output_rows: list[dict[str, Any]] = []
    breakdown_rows: list[dict[str, Any]] = []

    for row in candidates:
        t = ticker(row.get("ticker") or row.get("Ticker"))
        f = fundamentals.get(t)

        m_score = metadata_score(row)
        md_score = market_data_score(row)
        f_score, f_pos, f_neg = fundamentals_score(f)
        fundamentals_granular = fundamentals_granular_score_v1_6e(f)

        combined = round(clamp((m_score * 0.20) + (md_score * 0.35) + (f_score * 0.45)), 2)
        cat = category(combined)

        previous_score = base_local_score(row)
        delta = round(combined - previous_score, 2)

        positives = []
        negatives = []

        if m_score >= 75:
            positives.append("metadatos suficientes")
        if md_score >= 75:
            positives.append("market data sólido")
        if f_score >= 75:
            positives.append("fundamentales sólidos")
        positives.extend(f_pos[:4])

        if f_score < 55:
            negatives.append("fundamentales débiles o incompletos")
        if md_score < 55:
            negatives.append("market data débil o incompleto")
        negatives.extend(f_neg[:4])

        summary = (
            f"COMBINED_SCORE_V1 {combined}: metadata {m_score}, market data {md_score}, "
            f"fundamentales {f_score}. "
            f"{'Sube por ' + ', '.join(positives[:4]) if positives else 'Sin factores positivos fuertes'}; "
            f"{'vigilar ' + ', '.join(negatives[:4]) if negatives else 'sin alertas fuertes'}. "
            "No es recomendación financiera."
        )

        out = dict(row)
        out["ticker"] = t
        # v1.6C1 preserves combined score as active score
        if "local_score_v0" not in out:
            out["local_score_v0"] = previous_score
        out["score_previous"] = previous_score
        out["score"] = combined
        out["combined_score_v1"] = combined
        # v1.6C2 legacy UI compatibility bridge
        # Some UI routes still read legacy score/category/status fields.
        # Keep previous values in *_previous, then make legacy fields point to the combined score.
        out["local_score_v0_previous"] = previous_score
        out["score_previous"] = previous_score
        out["score"] = combined
        out["local_score_v0"] = combined
        out["score_final"] = combined
        out["display_score"] = combined
        out["combined_score_delta"] = delta
        out["metadata_score_component"] = m_score
        out["market_data_score_component"] = md_score
        out["fundamentals_score_component"] = f_score
        out["fundamentals_granular_score_v1_6e"] = fundamentals_granular
        out["category_final"] = cat
        out["category"] = cat
        out["category_label"] = human_category(cat)
        out["stage3_status"] = "COMBINED_SCORE_V1"
        out["status"] = "COMBINED_SCORE_V1"
        out["estado"] = "COMBINED_SCORE_V1"
        out["scoring_method"] = METHOD
        out["fundamentals_status"] = "OK" if f else "MISSING"
        out["local_score_v0_reason_previous"] = out.get("score_reason", "")
        out["score_reason"] = summary
        out["reason_to_pass_quant"] = summary
        out["local_score_reason"] = summary
        out["explainability_summary"] = summary
        out["positive_factors"] = " | ".join(positives[:8])
        out["negative_factors"] = " | ".join(negatives[:8])
        out["review_flags"] = " | ".join(negatives[:4]) if negatives else "standard_review"
        out["explainability_badges"] = "combined score v1 | fundamentals included | no external API"
        output_rows.append(out)

        breakdown_rows.append({
            "ticker": t,
            "score_previous": previous_score,
            "metadata_score_component": m_score,
            "market_data_score_component": md_score,
            "fundamentals_score_component": f_score,
            "fundamentals_granular_score_v1_6e": fundamentals_granular,
            "combined_score_v1": combined,
            "combined_score_delta": delta,
            "category_final": cat,
            "category_label": human_category(cat),
            "fundamentals_status": "OK" if f else "MISSING",
            "positive_factors": " | ".join(positives[:8]),
            "negative_factors": " | ".join(negatives[:8]),
            "method": METHOD,
        })

    annotate_exact_component_ties(output_rows)
    annotate_exact_component_ties(breakdown_rows)

    output_rows.sort(
        key=lambda r: (
            as_float(r.get("combined_score_v1"), 0) or 0,
            as_float(r.get("fundamentals_granular_score_v1_6e"), 0) or 0,
            str(r.get("ticker", "")),
        ),
        reverse=True,
    )
    breakdown_rows.sort(
        key=lambda r: (
            as_float(r.get("combined_score_v1"), 0) or 0,
            as_float(r.get("fundamentals_granular_score_v1_6e"), 0) or 0,
            str(r.get("ticker", "")),
        ),
        reverse=True,
    )

    write_csv(COMBINED_CANDIDATES, output_rows)
    write_csv(BREAKDOWN, breakdown_rows)

    # Make the app use the new combined ranking as the active ranking.
    if output_rows:
        write_csv(ACTIVE, output_rows)

    matched = sum(1 for r in output_rows if r.get("fundamentals_status") == "OK")
    top = output_rows[0] if output_rows else {}

    summary = {
        "phase": "v1.6C",
        "title": "Combined Scoring v1",
        "status": "OK" if output_rows else "ERROR",
        "created_at": now(),
        "rows_input": len(candidates),
        "rows_scored": len(output_rows),
        "fundamentals_matched": matched,
        "fundamentals_coverage_ratio": round(matched / len(output_rows), 4) if output_rows else 0.0,
        "top_ticker": top.get("ticker", ""),
        "top_score": top.get("combined_score_v1", ""),
        "method": METHOD,
        "weights": {
            "metadata_score_component": 0.20,
            "market_data_score_component": 0.35,
            "fundamentals_score_component": 0.45,
        },
        "openai_called": False,
        "broker_called": False,
        "pipeline_recalculated": False,
        "yfinance_called": False,
        "fundamentals_api_called": False,
        "active_ranking_updated": bool(output_rows),
        "outputs": [
            str(COMBINED_CANDIDATES.relative_to(ROOT)),
            str(BREAKDOWN.relative_to(ROOT)),
            str(SUMMARY.relative_to(ROOT)),
            str(REPORT.relative_to(ROOT)),
            str(ACTIVE.relative_to(ROOT)),
        ],
    }

    write_json(SUMMARY, summary)

    lines = [
        "# Scout Finance — v1.6C Combined Scoring v1 Report",
        "",
        f"Status: **{summary['status']}**",
        "",
        "## Summary",
        "",
        f"- Rows input: {summary['rows_input']}",
        f"- Rows scored: {summary['rows_scored']}",
        f"- Fundamentals matched: {summary['fundamentals_matched']}",
        f"- Fundamentals coverage: {summary['fundamentals_coverage_ratio']}",
        f"- Top ticker: {summary['top_ticker']}",
        f"- Top score: {summary['top_score']}",
        f"- Active ranking updated: {summary['active_ranking_updated']}",
        "",
        "## Weights",
        "",
        "- Metadata: 20%",
        "- Market data: 35%",
        "- Fundamentals: 45%",
        "",
        "## Controls",
        "",
        "- OpenAI called: False",
        "- Broker called: False",
        "- yfinance called: False",
        "- Fundamentals API called: False",
        "",
        "## Outputs",
        "",
    ]
    lines.extend([f"- `{path}`" for path in summary["outputs"]])
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run combined scoring v1.")
    parser.add_argument("--score", action="store_true", help="Generate combined score v1 outputs and update active ranking.")
    args = parser.parse_args()

    if not args.score:
        parser.print_help()
        return

    summary = run()
    print("Scout Finance — v1.6C Combined Scoring v1")
    print("=" * 92)
    print(f"Status: {summary['status']}")
    print(f"Rows input: {summary['rows_input']}")
    print(f"Rows scored: {summary['rows_scored']}")
    print(f"Fundamentals matched: {summary['fundamentals_matched']}")
    print(f"Fundamentals coverage: {summary['fundamentals_coverage_ratio']}")
    print(f"Top ticker: {summary['top_ticker']}")
    print(f"Top score: {summary['top_score']}")
    print("Weights: metadata 20%, market data 35%, fundamentals 45%")
    print("OpenAI called: False")
    print("Broker called: False")
    print("Pipeline recalculated: False")
    print("yfinance called: False")
    print("Fundamentals API called: False")
    print("Report: outputs/scoring/combined_score_v1_report.md")


if __name__ == "__main__":
    main()
