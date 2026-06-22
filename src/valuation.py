"""Offline deterministic valuation module for Scout Finance."""
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


def _score_multiple(value: Optional[float], cheap: float, fair: float, expensive: float) -> Optional[float]:
    if value is None or value <= 0:
        return None
    if value <= cheap:
        return 85.0
    if value <= fair:
        return 70.0
    if value <= expensive:
        return 45.0
    return 25.0


def _avg(values):
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def analyze_valuation(row: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()
    pe = _to_float(_first_present(row, ["pe", "trailingPE", "forwardPE", "P/E", "pe_ratio"]))
    ps = _to_float(_first_present(row, ["price_to_sales", "priceToSalesTrailing12Months", "P/S", "ps_ratio"]))
    pb = _to_float(_first_present(row, ["price_to_book", "priceToBook", "P/B", "pb_ratio"]))
    ev_ebitda = _to_float(_first_present(row, ["ev_to_ebitda", "enterpriseToEbitda", "EV/EBITDA"]))
    fcf_yield = _to_float(_first_present(row, ["fcf_yield", "free_cash_flow_yield", "FCF Yield"]))
    quant_score = _to_float(_first_present(row, ["score", "quant_score", "final_score", "Score"]))

    metric_scores = {
        "pe": _score_multiple(pe, 12.0, 25.0, 45.0),
        "price_to_sales": _score_multiple(ps, 3.0, 8.0, 15.0),
        "price_to_book": _score_multiple(pb, 2.0, 5.0, 10.0),
        "ev_to_ebitda": _score_multiple(ev_ebitda, 8.0, 16.0, 30.0),
        "fcf_yield": None if fcf_yield is None else (85.0 if fcf_yield >= 8 else 70.0 if fcf_yield >= 4 else 45.0 if fcf_yield >= 0 else 25.0),
    }
    score = _avg(metric_scores.values())
    data_gaps = [k for k, v in metric_scores.items() if v is None]
    status = "data_insufficient" if score is None or len(data_gaps) >= 4 else "ok"

    return {
        "ticker": ticker,
        "module": "valuation",
        "status": status,
        "score": score,
        "objective_data": {
            "pe": pe,
            "price_to_sales": ps,
            "price_to_book": pb,
            "ev_to_ebitda": ev_ebitda,
            "fcf_yield": fcf_yield,
            "quant_score": quant_score,
        },
        "metric_scores": metric_scores,
        "interpretation": "Valuation estimated only from available multiples; absent multiples remain data gaps.",
        "data_gaps": data_gaps,
    }
