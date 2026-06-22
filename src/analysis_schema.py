"""Scout Finance Phase 2 schema constants."""
from __future__ import annotations
from typing import Any

SCHEMA_VERSION = "scout_finance_company_report_v0.3"

ALLOWED_FINAL_CATEGORIES = {
    "🟢 Alta calidad / seguir de cerca",
    "🔵 Interesante pero cara",
    "🟡 Apta solo con margen de seguridad",
    "🟠 Riesgo elevado",
    "🔴 Descartar por ahora",
    "⚫ Datos insuficientes",
}
ALLOWED_CONFIDENCE_LEVELS = {"alto", "medio", "bajo", "insuficiente"}
SCORE_FIELDS = [
    "business_quality_score", "financial_health_score", "growth_score",
    "valuation_score", "risk_score", "moat_score",
    "evidence_quality_score", "data_freshness_score", "confidence_score",
]
MOAT_FIELDS = [
    "brand_strength", "switching_costs", "network_effects", "cost_advantage",
    "technology_edge", "scale_advantage",
]
REQUIRED_TOP_LEVEL_FIELDS = [
    "ticker", "company_name", "sector", "industry", "analysis_date", "currency",
    "business_summary", "business_model", "revenue_streams", "scores",
    "moat_breakdown", "valuation_summary", "risk_analysis", "scenarios",
    "dividend_analysis", "final_result", "sources",
]
REQUIRED_FINAL_RESULT_FIELDS = ["final_category", "confidence_level", "final_reasoning", "watchlist_decision"]
REQUIRED_SOURCE_FIELDS = ["main_sources", "source_warnings", "data_limitations"]
REQUIRED_SCENARIO_KEYS = ["bull_case", "base_case", "bear_case"]
REQUIRED_SCENARIO_FIELDS = ["summary", "key_assumptions", "probability"]

def empty_analysis_schema() -> dict[str, Any]:
    return {
        "ticker": "", "company_name": "", "sector": "", "industry": "",
        "analysis_date": "", "currency": "", "business_summary": "",
        "business_model": "", "revenue_streams": [],
        "scores": {field: None for field in SCORE_FIELDS},
        "moat_breakdown": {
            "brand_strength": None, "switching_costs": None, "network_effects": None,
            "cost_advantage": None, "technology_edge": None, "scale_advantage": None,
            "moat_comment": "",
        },
        "valuation_summary": {
            "relative_valuation": "", "valuation_status": "",
            "valuation_confidence": None, "main_valuation_risk": "",
        },
        "risk_analysis": {
            "main_risks": [{"risk": "", "probability": "", "impact": "", "severity": "", "comment": ""}],
            "risk_level": "", "risk_comment": "",
        },
        "scenarios": {
            "bull_case": {"summary": "", "key_assumptions": [], "probability": None},
            "base_case": {"summary": "", "key_assumptions": [], "probability": None},
            "bear_case": {"summary": "", "key_assumptions": [], "probability": None},
        },
        "dividend_analysis": {
            "is_dividend_payer": None, "dividend_yield": None,
            "payout_ratio_earnings": None, "payout_ratio_fcf": None,
            "dividend_growth_5y": None, "yield_trap_warning": None,
            "dividend_verdict": "",
        },
        "final_result": {"final_category": "", "confidence_level": "", "final_reasoning": "", "watchlist_decision": ""},
        "sources": {"main_sources": [], "source_warnings": [], "data_limitations": []},
    }
