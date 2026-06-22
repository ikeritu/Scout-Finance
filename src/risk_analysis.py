"""Offline deterministic risk module for Scout Finance."""
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


def analyze_risk(row: Dict[str, Any]) -> Dict[str, Any]:
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()

    beta = _to_float(_first_present(row, ["beta", "Beta"]))
    volatility = _to_float(_first_present(row, ["volatility", "annualized_volatility", "Volatility"]))
    max_drawdown = _to_float(_first_present(row, ["max_drawdown", "drawdown", "Max Drawdown"]))
    debt_to_equity = _to_float(_first_present(row, ["debt_to_equity", "debtToEquity", "Debt To Equity"]))
    short_ratio = _to_float(_first_present(row, ["short_ratio", "shortRatio", "Short Ratio"]))
    current_ratio = _to_float(_first_present(row, ["current_ratio", "currentRatio", "Current Ratio"]))
    market_cap = _to_float(_first_present(row, ["market_cap", "marketCap", "Market Cap"]))

    metric_scores = {
        "beta": None if beta is None else (85.0 if beta <= 0.9 else 65.0 if beta <= 1.3 else 45.0 if beta <= 1.8 else 25.0),
        "volatility": None if volatility is None else (85.0 if volatility <= 25 else 65.0 if volatility <= 45 else 40.0 if volatility <= 70 else 20.0),
        "max_drawdown": None if max_drawdown is None else (85.0 if max_drawdown >= -20 else 65.0 if max_drawdown >= -40 else 40.0 if max_drawdown >= -60 else 20.0),
        "debt_to_equity": None if debt_to_equity is None else (85.0 if debt_to_equity <= 50 else 65.0 if debt_to_equity <= 120 else 40.0 if debt_to_equity <= 250 else 20.0),
        "short_ratio": None if short_ratio is None else (80.0 if short_ratio <= 3 else 60.0 if short_ratio <= 7 else 35.0),
        "current_ratio": None if current_ratio is None else (80.0 if current_ratio >= 1.5 else 60.0 if current_ratio >= 1.0 else 30.0),
        "market_cap": None if market_cap is None else (75.0 if market_cap >= 2_000_000_000 else 55.0 if market_cap >= 300_000_000 else 35.0),
    }

    score = _avg(metric_scores.values())
    data_gaps = [k for k, v in metric_scores.items() if v is None]
    status = "data_insufficient" if score is None or len(data_gaps) >= 5 else "ok"
    risk_level = None
    if score is not None:
        risk_level = "low" if score >= 75 else "moderate" if score >= 55 else "high"

    return {
        "ticker": ticker,
        "module": "risk_analysis",
        "status": status,
        "score": score,
        "risk_level": risk_level,
        "objective_data": {
            "beta": beta,
            "volatility": volatility,
            "max_drawdown": max_drawdown,
            "debt_to_equity": debt_to_equity,
            "short_ratio": short_ratio,
            "current_ratio": current_ratio,
            "market_cap": market_cap,
        },
        "metric_scores": metric_scores,
        "interpretation": "Risk score is deterministic and based only on available balance-sheet, liquidity, volatility and size proxies.",
        "data_gaps": data_gaps,
    }
