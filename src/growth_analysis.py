"""Offline deterministic growth module for Scout Finance."""
from __future__ import annotations
from typing import Any, Dict, Iterable, Optional


def _first_present(row: Dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in row and row[name] not in ("", None, "None", "nan", "NaN"):
            return row[name]
    return None


def _to_float(value: Any) -> Optional[float]:
    if value in ("", None, "None", "nan", "NaN"):
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", ".").replace("%", "").strip()
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg(values):
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def analyze_growth(row: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()
    revenue_growth = _to_float(_first_present(row, ["revenue_growth", "revenueGrowth", "sales_growth", "Revenue Growth"]))
    earnings_growth = _to_float(_first_present(row, ["earnings_growth", "earningsGrowth", "eps_growth", "EPS Growth"]))
    ebitda_growth = _to_float(_first_present(row, ["ebitda_growth", "EBITDA Growth"]))
    free_cash_flow_growth = _to_float(_first_present(row, ["free_cash_flow_growth", "fcf_growth", "FCF Growth"]))
    analyst_growth = _to_float(_first_present(row, ["analyst_growth", "earningsQuarterlyGrowth", "Analyst Growth"]))

    def s(v):
        if v is None:
            return None
        return 90.0 if v >= 30 else 75.0 if v >= 15 else 55.0 if v >= 0 else 30.0

    metric_scores = {
        "revenue_growth": s(revenue_growth),
        "earnings_growth": s(earnings_growth),
        "ebitda_growth": s(ebitda_growth),
        "free_cash_flow_growth": s(free_cash_flow_growth),
        "analyst_growth": s(analyst_growth),
    }
    score = _avg(metric_scores.values())
    data_gaps = [k for k, v in metric_scores.items() if v is None]
    status = "data_insufficient" if score is None or len(data_gaps) >= 4 else "ok"
    return {
        "ticker": ticker,
        "module": "growth_analysis",
        "status": status,
        "score": score,
        "objective_data": {
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "ebitda_growth": ebitda_growth,
            "free_cash_flow_growth": free_cash_flow_growth,
            "analyst_growth": analyst_growth,
        },
        "metric_scores": metric_scores,
        "interpretation": "Growth score is based only on available growth fields in the existing dataset.",
        "data_gaps": data_gaps,
    }
