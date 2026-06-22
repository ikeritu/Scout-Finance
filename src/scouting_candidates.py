"""
Scout Finance — Phase 5F scouting candidates loader.

Purpose:
- Load Stage 3 scouting candidates from outputs/scouting/top_100_candidates.csv
- Provide helper functions for Streamlit/app integration
- Keep the existing demo/pipeline untouched

This module does not call OpenAI.
It does not modify app.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.funnel_paths import SCOUTING_OUTPUTS_DIR


TOP_20_DEEP_RESEARCH_PATH = SCOUTING_OUTPUTS_DIR / "top_20_deep_research.csv"
TOP_50_WATCHLIST_PATH = SCOUTING_OUTPUTS_DIR / "top_50_watchlist.csv"
TOP_100_CANDIDATES_PATH = SCOUTING_OUTPUTS_DIR / "top_100_candidates.csv"
TOP_RECOVERABLE_CANDIDATES_PATH = SCOUTING_OUTPUTS_DIR / "top_recoverable_candidates.csv"

SCOUTING_CANDIDATE_FILES = {
    "Top 20 — Deep research": TOP_20_DEEP_RESEARCH_PATH,
    "Top 50 — Watchlist": TOP_50_WATCHLIST_PATH,
    "Top 100 — Candidates": TOP_100_CANDIDATES_PATH,
    "Recoverable candidates": TOP_RECOVERABLE_CANDIDATES_PATH,
}


def _safe_read_csv(path: Path) -> pd.DataFrame:
    """
    Read a CSV safely. Return empty dataframe if missing or unreadable.
    """

    try:
        if not path.exists():
            return pd.DataFrame()

        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def scouting_candidates_available() -> bool:
    """
    Return True if the main Top 100 candidates file exists and has rows.
    """

    df = _safe_read_csv(TOP_100_CANDIDATES_PATH)
    return not df.empty


def load_scouting_candidates(
    path: Path = TOP_100_CANDIDATES_PATH,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Load Stage 3 scouting candidates.

    Default source:
        outputs/scouting/top_100_candidates.csv
    """

    df = _safe_read_csv(path)

    if df.empty:
        return df

    if "final_stage3_score" in df.columns:
        df["final_stage3_score"] = pd.to_numeric(df["final_stage3_score"], errors="coerce")
        df = df.sort_values("final_stage3_score", ascending=False)

    if limit is not None:
        df = df.head(limit)

    return df.reset_index(drop=True)


def load_all_scouting_candidate_sets() -> dict[str, pd.DataFrame]:
    """
    Load all generated candidate CSVs.
    """

    return {
        label: load_scouting_candidates(path=path)
        for label, path in SCOUTING_CANDIDATE_FILES.items()
    }


def build_scouting_candidates_summary() -> dict[str, Any]:
    """
    Build summary metrics for Stage 3 candidate files.
    """

    summary: dict[str, Any] = {
        "available": scouting_candidates_available(),
        "files": {},
        "top_company": None,
        "category_distribution": {},
    }

    for label, path in SCOUTING_CANDIDATE_FILES.items():
        df = load_scouting_candidates(path=path)
        summary["files"][label] = {
            "path": str(path),
            "exists": path.exists(),
            "rows": int(len(df)),
        }

    top100 = load_scouting_candidates(TOP_100_CANDIDATES_PATH)

    if not top100.empty:
        display_columns = [
            column
            for column in ["ticker", "name", "final_stage3_score", "stage3_category"]
            if column in top100.columns
        ]

        if display_columns:
            summary["top_company"] = top100.iloc[0][display_columns].to_dict()

        if "stage3_category" in top100.columns:
            summary["category_distribution"] = (
                top100["stage3_category"]
                .fillna("Sin categoría")
                .astype(str)
                .value_counts()
                .to_dict()
            )

    return summary


def prepare_candidates_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a user-friendly dataframe for Streamlit display.
    """

    if df.empty:
        return df

    display = df.copy()

    rename_map = {
        "ticker": "Ticker",
        "name": "Empresa",
        "sector": "Sector",
        "industry": "Industria",
        "country": "País",
        "market_cap": "Market cap",
        "final_stage3_score": "Score final",
        "stage3_category": "Categoría Stage 3",
        "business_quality_score": "Calidad negocio",
        "financial_health_score": "Salud financiera",
        "growth_score": "Crecimiento",
        "valuation_score": "Valoración",
        "risk_score": "Riesgo",
        "moat_proxy_score": "Moat proxy",
        "momentum_score": "Momentum",
        "liquidity_score": "Liquidez",
        "data_quality_score": "Calidad datos",
    }

    for old, new in rename_map.items():
        if old in display.columns and new not in display.columns:
            display[new] = display[old]

    preferred = [
        "Ticker",
        "Empresa",
        "Score final",
        "Categoría Stage 3",
        "Sector",
        "Industria",
        "País",
        "Market cap",
        "Calidad negocio",
        "Salud financiera",
        "Crecimiento",
        "Valoración",
        "Riesgo",
        "Moat proxy",
        "Momentum",
        "Liquidez",
        "Calidad datos",
    ]

    available = [column for column in preferred if column in display.columns]
    result = display[available].copy() if available else display

    numeric_columns = [
        "Score final",
        "Market cap",
        "Calidad negocio",
        "Salud financiera",
        "Crecimiento",
        "Valoración",
        "Riesgo",
        "Moat proxy",
        "Momentum",
        "Liquidez",
        "Calidad datos",
    ]

    for column in numeric_columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce").round(2)

    return result


def export_candidates_for_existing_ranking(
    input_path: Path = TOP_100_CANDIDATES_PATH,
    output_path: Path = SCOUTING_OUTPUTS_DIR / "stage3_candidates_for_ranking.csv",
) -> Path:
    """
    Export a simplified candidate file for future integration with the existing ranking.

    This does not replace the current pipeline.
    It only creates a bridge CSV with common fields.
    """

    df = load_scouting_candidates(input_path)

    if df.empty:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame().to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    bridge = pd.DataFrame()

    bridge["ticker"] = df.get("ticker", pd.Series(dtype=str))
    bridge["company_name"] = df.get("name", pd.Series(dtype=str))
    bridge["sector"] = df.get("sector", pd.Series(dtype=str))
    bridge["industry"] = df.get("industry", pd.Series(dtype=str))
    bridge["country"] = df.get("country", pd.Series(dtype=str))
    bridge["market_cap"] = df.get("market_cap", pd.Series(dtype=float))
    bridge["score"] = df.get("final_stage3_score", pd.Series(dtype=float))
    bridge["category"] = df.get("stage3_category", pd.Series(dtype=str))
    bridge["source"] = "stage3_opportunity_scoring"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    bridge.to_csv(output_path, index=False, encoding="utf-8-sig")

    return output_path
