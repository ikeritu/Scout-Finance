"""Scout Finance — deterministic research memo assembler.

This is not the OpenAI memo generator. It is the offline, auditable base layer
used by Phase 8C and later by v0.8.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from src.fundamentals import analyze_fundamentals
from src.valuation import analyze_valuation
from src.risk_analysis import analyze_risk
from src.moat_analysis import analyze_moat
from src.growth_analysis import analyze_growth
from src.institutional_view import analyze_institutional_view
from src.earnings_analysis import analyze_earnings


SCHEMA_VERSION = "equity_research_memo_schema_v0_1"
PROMPT_VERSION = "deterministic_no_prompt_v0_1"


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


def _avg(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def build_deterministic_research_memo(row: Dict[str, Any], ranking_position: int | None = None) -> Dict[str, Any]:
    """Build one deterministic memo using only the given row."""
    ticker = str(_first_present(row, ["ticker", "symbol", "Ticker", "Symbol"]) or "").upper()
    company_name = str(_first_present(row, ["company_name", "shortName", "longName", "name", "Company Name"]) or ticker)
    quant_score = _to_float(_first_present(row, ["score", "quant_score", "final_score", "Score"]))

    fundamentals = analyze_fundamentals(row)
    valuation = analyze_valuation(row)
    risk = analyze_risk(row)
    moat = analyze_moat(row)
    growth = analyze_growth(row)
    institutional = analyze_institutional_view(row)
    earnings = analyze_earnings(row)

    module_results = {
        "financial_health": fundamentals,
        "valuation_analysis": valuation,
        "risk_analysis": risk,
        "moat_analysis": moat,
        "growth_analysis": growth,
        "institutional_view": institutional,
        "earnings_analysis": earnings,
    }

    scores = {
        "financial_health_score": fundamentals.get("score"),
        "valuation_score": valuation.get("score"),
        "risk_score": risk.get("score"),
        "moat_score": moat.get("score"),
        "growth_score": growth.get("score"),
        "institutional_score": institutional.get("score"),
    }
    deterministic_score = _avg(scores.values())

    data_gaps: List[str] = []
    for section_name, section in module_results.items():
        for gap in section.get("data_gaps", []):
            data_gaps.append(f"{section_name}.{gap}")
    data_gaps = sorted(set(data_gaps))

    memo_status = "data_insufficient" if deterministic_score is None or len(data_gaps) >= 18 else "deterministic_complete"

    confidence = "low"
    if deterministic_score is not None:
        confidence = "medium" if len(data_gaps) <= 10 else "low"
        if len(data_gaps) <= 5:
            confidence = "high"

    final_verdict = "watchlist_only"
    if deterministic_score is not None:
        if deterministic_score >= 70 and (risk.get("risk_level") in ("low", "moderate", None)):
            final_verdict = "research_candidate"
        elif deterministic_score < 45 or risk.get("risk_level") == "high":
            final_verdict = "high_risk_or_weak_data"

    return {
        "ticker": ticker,
        "company_name": company_name,
        "ranking_position": ranking_position,
        "quant_score": quant_score,
        "memo_status": memo_status,
        "business_model": {
            "status": "data_insufficient",
            "objective_data": {},
            "interpretation": "Business model is not inferred in deterministic mode without a verified source field.",
        },
        "financial_health": fundamentals,
        "moat_analysis": moat,
        "valuation_analysis": valuation,
        "growth_analysis": growth,
        "risk_analysis": risk,
        "institutional_view": institutional,
        "earnings_analysis": earnings,
        "bull_case": {
            "status": "deterministic_placeholder",
            "points": ["Bull case requires later AI or verified qualitative inputs; not invented in 8C."],
        },
        "base_case": {
            "status": "deterministic_placeholder",
            "points": ["Base case limited to deterministic scores and available objective data."],
        },
        "bear_case": {
            "status": "deterministic_placeholder",
            "points": ["Bear case prioritizes risk score and data gaps until qualitative research is enabled."],
        },
        "final_verdict": final_verdict,
        "confidence": confidence,
        "deterministic_score": deterministic_score,
        "scores": scores,
        "data_gaps": data_gaps,
        "sources": ["existing_scout_finance_outputs_only"],
        "model_used": None,
        "estimated_cost": 0.0,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "objective_data_json": {
            "input_row_keys": sorted(row.keys()),
            "module_results": module_results,
        },
        "ai_interpretation_json": None,
    }


def build_deterministic_research_memos(rows: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    limited = rows[:top_n]
    return [build_deterministic_research_memo(row, idx + 1) for idx, row in enumerate(limited)]
