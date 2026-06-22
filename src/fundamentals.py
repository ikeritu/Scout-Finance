"""
Scout Finance — deterministic fundamentals module.

This module is intentionally offline-only:
- no OpenAI calls
- no yfinance calls
- no network/API calls
- no dependency on app.py or filters.py

It works with whatever objective fields are already present in the ranking/export rows.
Missing fields are reported as data gaps instead of being invented.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional


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
            value = value.replace("%", "").replace(",", ".").strip()
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_positive(value: Optional[float], weak: float, good: float, excellent: float) -> Optional[float]:
    if value is None:
        return None
    if value >= excellent:
        return 90.0
    if value >= good:
        return 75.0
    if value >= weak:
        return 55.0
    return 35.0


def _score_negative(value: Optional[float], good: float, acceptable: float, weak: float) -> Optional[float]:
    if value is None:
        return None
    if value <= good:
        return 85.0
    if value <= acceptable:
        return 65.0
    if value <= weak:
        return 45.0
    return 25.0


def _avg(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def analyze_fundamentals(row: Dict[str, Any]) -> Dict[str, Any]:
    """Return deterministic financial-health analysis for one company row."""
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()

    revenue_growth = _to_float(_first_present(row, ["revenue_growth", "revenueGrowth", "sales_growth", "Revenue Growth"]))
    gross_margin = _to_float(_first_present(row, ["gross_margin", "grossMargins", "Gross Margin"]))
    operating_margin = _to_float(_first_present(row, ["operating_margin", "operatingMargins", "Operating Margin"]))
    net_margin = _to_float(_first_present(row, ["net_margin", "profitMargins", "Net Margin"]))
    roe = _to_float(_first_present(row, ["roe", "return_on_equity", "returnOnEquity", "ROE"]))
    roa = _to_float(_first_present(row, ["roa", "return_on_assets", "returnOnAssets", "ROA"]))
    debt_to_equity = _to_float(_first_present(row, ["debt_to_equity", "debtToEquity", "Debt To Equity"]))
    current_ratio = _to_float(_first_present(row, ["current_ratio", "currentRatio", "Current Ratio"]))
    free_cash_flow = _to_float(_first_present(row, ["free_cash_flow", "freeCashflow", "FCF", "Free Cash Flow"]))

    metric_scores = {
        "revenue_growth": _score_positive(revenue_growth, 0.0, 10.0, 25.0),
        "gross_margin": _score_positive(gross_margin, 20.0, 40.0, 65.0),
        "operating_margin": _score_positive(operating_margin, 0.0, 10.0, 25.0),
        "net_margin": _score_positive(net_margin, 0.0, 8.0, 20.0),
        "roe": _score_positive(roe, 0.0, 10.0, 25.0),
        "roa": _score_positive(roa, 0.0, 5.0, 12.0),
        "debt_to_equity": _score_negative(debt_to_equity, 50.0, 120.0, 250.0),
        "current_ratio": _score_positive(current_ratio, 1.0, 1.5, 2.5),
        "free_cash_flow": _score_positive(free_cash_flow, 0.0, 1.0, 10.0),
    }

    data_gaps = [name for name, score in metric_scores.items() if score is None]
    score = _avg(metric_scores.values())

    status = "data_insufficient" if score is None or len(data_gaps) >= 6 else "ok"
    interpretation = (
        "Deterministic financial-health score computed from available objective metrics."
        if status == "ok"
        else "Insufficient objective fundamentals available; no synthetic fundamentals were created."
    )

    return {
        "ticker": ticker,
        "module": "fundamentals",
        "status": status,
        "score": score,
        "objective_data": {
            "revenue_growth": revenue_growth,
            "gross_margin": gross_margin,
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            "roe": roe,
            "roa": roa,
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            "free_cash_flow": free_cash_flow,
        },
        "metric_scores": metric_scores,
        "interpretation": interpretation,
        "data_gaps": data_gaps,
    }
