"""Offline deterministic institutional-view module for Scout Finance."""
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


def analyze_institutional_view(row: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()
    institutional_ownership = _to_float(_first_present(row, ["institutional_ownership", "heldPercentInstitutions", "Institutional Ownership"]))
    insider_ownership = _to_float(_first_present(row, ["insider_ownership", "heldPercentInsiders", "Insider Ownership"]))
    analyst_count = _to_float(_first_present(row, ["analyst_count", "numberOfAnalystOpinions", "Analyst Count"]))
    recommendation_mean = _to_float(_first_present(row, ["recommendation_mean", "recommendationMean", "Recommendation Mean"]))

    metric_scores = {
        "institutional_ownership": None if institutional_ownership is None else (80.0 if 20 <= institutional_ownership <= 85 else 60.0 if institutional_ownership < 20 else 45.0),
        "insider_ownership": None if insider_ownership is None else (75.0 if 2 <= insider_ownership <= 35 else 55.0 if insider_ownership < 2 else 45.0),
        "analyst_count": None if analyst_count is None else (80.0 if analyst_count >= 10 else 65.0 if analyst_count >= 4 else 45.0),
        "recommendation_mean": None if recommendation_mean is None else (80.0 if recommendation_mean <= 2.0 else 60.0 if recommendation_mean <= 3.0 else 35.0),
    }
    score = _avg(metric_scores.values())
    data_gaps = [k for k, v in metric_scores.items() if v is None]
    status = "data_insufficient" if score is None or len(data_gaps) >= 3 else "ok"
    return {
        "ticker": ticker,
        "module": "institutional_view",
        "status": status,
        "score": score,
        "objective_data": {
            "institutional_ownership": institutional_ownership,
            "insider_ownership": insider_ownership,
            "analyst_count": analyst_count,
            "recommendation_mean": recommendation_mean,
        },
        "metric_scores": metric_scores,
        "interpretation": "Institutional view is a deterministic proxy from ownership and analyst-coverage fields only.",
        "data_gaps": data_gaps,
    }
