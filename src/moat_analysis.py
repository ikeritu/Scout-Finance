"""Offline deterministic moat proxy module for Scout Finance."""
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


def analyze_moat(row: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()
    gross_margin = _to_float(_first_present(row, ["gross_margin", "grossMargins", "Gross Margin"]))
    operating_margin = _to_float(_first_present(row, ["operating_margin", "operatingMargins", "Operating Margin"]))
    roe = _to_float(_first_present(row, ["roe", "return_on_equity", "returnOnEquity", "ROE"]))
    roic = _to_float(_first_present(row, ["roic", "return_on_invested_capital", "ROIC"]))
    revenue_growth = _to_float(_first_present(row, ["revenue_growth", "revenueGrowth", "Revenue Growth"]))

    metric_scores = {
        "gross_margin": None if gross_margin is None else (85.0 if gross_margin >= 65 else 70.0 if gross_margin >= 40 else 45.0 if gross_margin >= 20 else 25.0),
        "operating_margin": None if operating_margin is None else (85.0 if operating_margin >= 25 else 70.0 if operating_margin >= 12 else 45.0 if operating_margin >= 0 else 25.0),
        "roe": None if roe is None else (85.0 if roe >= 25 else 70.0 if roe >= 12 else 45.0 if roe >= 0 else 25.0),
        "roic": None if roic is None else (85.0 if roic >= 18 else 70.0 if roic >= 10 else 45.0 if roic >= 0 else 25.0),
        "revenue_growth": None if revenue_growth is None else (75.0 if revenue_growth >= 10 else 55.0 if revenue_growth >= 0 else 30.0),
    }
    score = _avg(metric_scores.values())
    data_gaps = [k for k, v in metric_scores.items() if v is None]
    status = "data_insufficient" if score is None or len(data_gaps) >= 4 else "ok"
    return {
        "ticker": ticker,
        "module": "moat_analysis",
        "status": status,
        "score": score,
        "objective_data": {
            "gross_margin": gross_margin,
            "operating_margin": operating_margin,
            "roe": roe,
            "roic": roic,
            "revenue_growth": revenue_growth,
        },
        "metric_scores": metric_scores,
        "interpretation": "Moat is only a proxy from profitability and return metrics; it is not proof of durable competitive advantage.",
        "data_gaps": data_gaps,
    }
