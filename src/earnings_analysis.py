"""Offline deterministic earnings module for Scout Finance."""
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


def analyze_earnings(row: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()
    eps_growth = _to_float(_first_present(row, ["eps_growth", "earnings_growth", "earningsGrowth", "EPS Growth"]))
    revenue_growth = _to_float(_first_present(row, ["revenue_growth", "revenueGrowth", "Revenue Growth"]))
    earnings_surprise = _to_float(_first_present(row, ["earnings_surprise", "earningsSurprise", "Earnings Surprise"]))
    next_earnings_date = _first_present(row, ["next_earnings_date", "earningsDate", "Next Earnings Date"])

    metric_scores = {
        "eps_growth": None if eps_growth is None else (85.0 if eps_growth >= 20 else 70.0 if eps_growth >= 5 else 45.0 if eps_growth >= 0 else 25.0),
        "revenue_growth": None if revenue_growth is None else (80.0 if revenue_growth >= 15 else 65.0 if revenue_growth >= 5 else 45.0 if revenue_growth >= 0 else 25.0),
        "earnings_surprise": None if earnings_surprise is None else (80.0 if earnings_surprise >= 5 else 60.0 if earnings_surprise >= 0 else 35.0),
    }
    score = _avg(metric_scores.values())
    data_gaps = [k for k, v in metric_scores.items() if v is None]
    if next_earnings_date is None:
        data_gaps.append("next_earnings_date")
    status = "data_insufficient" if score is None or len(data_gaps) >= 3 else "ok"
    return {
        "ticker": ticker,
        "module": "earnings_analysis",
        "status": status,
        "score": score,
        "objective_data": {
            "eps_growth": eps_growth,
            "revenue_growth": revenue_growth,
            "earnings_surprise": earnings_surprise,
            "next_earnings_date": next_earnings_date,
        },
        "metric_scores": metric_scores,
        "interpretation": "Earnings analysis is deterministic and incomplete when earnings fields are absent.",
        "data_gaps": data_gaps,
    }
