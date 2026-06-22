"""
Scoring module.

This module calculates a first quantitative priority score for companies
that passed the basic filters.

Current scope:
- Simple, explainable quantitative scoring.
- Momentum, volume, liquidity, market context and risk indicators.
- Final category for research prioritization.

Not included in this phase:
- OpenAI analysis.
- News/catalyst analysis.
- Trading recommendations.
- Buy/sell signals.
- Portfolio simulation.
- Streamlit UI.
- Database writes.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from config import SCORING_VERSION


def _is_missing(value: Any) -> bool:
    """
    Return True if a value should be considered missing.
    """

    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except TypeError:
        pass

    if isinstance(value, str) and value.strip() == "":
        return True

    return False


def _safe_float(value: Any) -> float | None:
    """
    Convert a value to float when possible.

    Returns None if the value is missing or cannot be converted.
    """

    if _is_missing(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """
    Restrict a numeric value to a fixed interval.
    """

    return max(minimum, min(maximum, value))


def score_volume(relative_volume: Any) -> float:
    """
    Score unusual volume.

    Higher relative volume means the company may deserve review.
    This is not treated as a recommendation.
    """

    rv = _safe_float(relative_volume)

    if rv is None:
        return 0.0

    if rv < 0.8:
        return 20.0

    if rv < 1.0:
        return 40.0

    if rv < 1.5:
        return 60.0

    if rv < 2.5:
        return 80.0

    return 100.0


def score_momentum(change_1d: Any, change_5d: Any, change_20d: Any) -> float:
    """
    Score recent price momentum.

    The score favors positive but not extremely explosive movement.
    Very large short-term moves are partially penalized as risk.
    """

    c1 = _safe_float(change_1d)
    c5 = _safe_float(change_5d)
    c20 = _safe_float(change_20d)

    score = 50.0

    if c1 is not None:
        score += c1 * 250

    if c5 is not None:
        score += c5 * 180

    if c20 is not None:
        score += c20 * 90

    # Very aggressive one-day moves may already be late or noisy.
    if c1 is not None and c1 > 0.15:
        score -= 15

    if c5 is not None and c5 > 0.35:
        score -= 15

    if c20 is not None and c20 < -0.25:
        score -= 15

    return round(_clamp(score), 2)


def score_liquidity(avg_volume_50d: Any, market_cap: Any) -> float:
    """
    Score liquidity and size.

    The goal is to deprioritize names that are harder to analyze reliably
    due to very low liquidity or very small size.
    """

    avg_volume = _safe_float(avg_volume_50d)
    cap = _safe_float(market_cap)

    score = 0.0

    if avg_volume is None:
        volume_score = 0.0
    elif avg_volume >= 10_000_000:
        volume_score = 100.0
    elif avg_volume >= 3_000_000:
        volume_score = 85.0
    elif avg_volume >= 1_000_000:
        volume_score = 70.0
    elif avg_volume >= 300_000:
        volume_score = 55.0
    else:
        volume_score = 20.0

    if cap is None:
        cap_score = 0.0
    elif cap >= 100_000_000_000:
        cap_score = 100.0
    elif cap >= 10_000_000_000:
        cap_score = 85.0
    elif cap >= 1_000_000_000:
        cap_score = 70.0
    elif cap >= 100_000_000:
        cap_score = 50.0
    else:
        cap_score = 20.0

    score = (volume_score * 0.55) + (cap_score * 0.45)

    return round(_clamp(score), 2)


def score_context(above_ma20: Any, above_ma50: Any, distance_to_52w_high: Any) -> float:
    """
    Score basic technical context.

    This is intentionally simple:
    - Above moving averages is treated positively.
    - Being close to 52-week high may indicate strength, but not by itself.
    """

    score = 40.0

    if bool(above_ma20):
        score += 20

    if bool(above_ma50):
        score += 20

    dist_high = _safe_float(distance_to_52w_high)

    if dist_high is not None:
        # distance_to_52w_high is expected as a negative or zero value.
        if dist_high >= -0.05:
            score += 20
        elif dist_high >= -0.15:
            score += 10
        elif dist_high < -0.40:
            score -= 10

    return round(_clamp(score), 2)


def score_risk(change_1d: Any, change_5d: Any, relative_volume: Any) -> float:
    """
    Estimate simple risk score.

    Higher value means higher risk/noise, not higher attractiveness.
    """

    c1 = _safe_float(change_1d)
    c5 = _safe_float(change_5d)
    rv = _safe_float(relative_volume)

    score = 25.0

    if c1 is not None and abs(c1) > 0.08:
        score += 20

    if c5 is not None and abs(c5) > 0.18:
        score += 20

    if rv is not None and rv > 3:
        score += 20

    if rv is not None and rv < 0.5:
        score += 10

    return round(_clamp(score), 2)


def score_confidence(data_quality_score: Any, passes_basic_filters: Any) -> float:
    """
    Estimate confidence based on data quality and filter status.
    """

    quality = _safe_float(data_quality_score)

    if quality is None:
        quality = 0.0

    score = quality

    if not bool(passes_basic_filters):
        score -= 30

    return round(_clamp(score), 2)


def calculate_priority_score(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    """
    Calculate all scoring fields for one company.

    Parameters
    ----------
    row:
        One row after data quality and basic filters.

    Returns
    -------
    dict
        Scoring fields compatible with the future signals table.
    """

    volume = score_volume(row.get("relative_volume"))
    momentum = score_momentum(
        row.get("change_1d"),
        row.get("change_5d"),
        row.get("change_20d"),
    )
    liquidity = score_liquidity(row.get("avg_volume_50d"), row.get("market_cap"))
    context = score_context(
        row.get("above_ma20"),
        row.get("above_ma50"),
        row.get("distance_to_52w_high"),
    )

    # Placeholder scores for future phases.
    catalyst = 0.0
    fundamental = 50.0
    asymmetry = 50.0
    dilution = 50.0

    risk = score_risk(
        row.get("change_1d"),
        row.get("change_5d"),
        row.get("relative_volume"),
    )
    confidence = score_confidence(
        row.get("data_quality_score"),
        row.get("passes_basic_filters"),
    )

    score_raw = (
        volume * 0.25
        + momentum * 0.25
        + liquidity * 0.20
        + context * 0.15
        + fundamental * 0.10
        + asymmetry * 0.05
    )

    penalty_total = 0.0

    if not bool(row.get("passes_basic_filters")):
        penalty_total += 35.0

    if confidence < 60:
        penalty_total += 20.0

    if risk > 70:
        penalty_total += 10.0

    score_adjusted = _clamp(score_raw - penalty_total)
    score_priority = _clamp((score_adjusted * 0.75) + (confidence * 0.25))

    category_final = categorize_priority(score_priority, confidence, risk)

    veto_applied = False
    veto_reason = ""

    if not bool(row.get("passes_basic_filters")):
        veto_applied = True
        veto_reason = "failed_basic_filters"
        category_final = "excluded"

    reason_to_pass_quant = build_reason_to_pass_quant(
        volume=volume,
        momentum=momentum,
        liquidity=liquidity,
        context=context,
        risk=risk,
        confidence=confidence,
    )
    missing_key_data_quant = build_missing_key_data_quant(row)

    return {
        "score_catalyst": catalyst,
        "score_volume": round(volume, 2),
        "score_momentum": round(momentum, 2),
        "score_liquidity": round(liquidity, 2),
        "score_context": round(context, 2),
        "score_fundamental": round(fundamental, 2),
        "score_asymmetry": round(asymmetry, 2),
        "score_raw": round(score_raw, 2),
        "penalty_total": round(penalty_total, 2),
        "score_adjusted": round(score_adjusted, 2),
        "score_risk": round(risk, 2),
        "score_confidence": round(confidence, 2),
        "score_dilution": round(dilution, 2),
        "score_priority": round(score_priority, 2),
        "category_final": category_final,
        "opportunity_phase": "quant_screening",
        "veto_applied": veto_applied,
        "veto_reason": veto_reason,
        "reason_to_pass_quant": reason_to_pass_quant,
        "missing_key_data_quant": missing_key_data_quant,
        "scoring_version": SCORING_VERSION,
    }


def categorize_priority(score_priority: float, confidence: float, risk: float) -> str:
    """
    Assign a research priority category.

    Categories are for research workflow only.
    They are not investment recommendations.
    """

    if confidence < 60:
        return "low_confidence"

    if risk >= 85:
        return "high_risk_review"

    if score_priority >= 80:
        return "high_priority_research"

    if score_priority >= 65:
        return "medium_priority_research"

    if score_priority >= 50:
        return "watchlist"

    return "low_priority"


def build_reason_to_pass_quant(
    volume: float,
    momentum: float,
    liquidity: float,
    context: float,
    risk: float,
    confidence: float,
) -> str:
    """
    Build a short explanation of the quantitative result.
    """

    reasons: list[str] = []

    if volume >= 70:
        reasons.append("strong_relative_volume")

    if momentum >= 70:
        reasons.append("positive_momentum")

    if liquidity >= 75:
        reasons.append("good_liquidity")

    if context >= 70:
        reasons.append("constructive_price_context")

    if risk >= 70:
        reasons.append("elevated_risk")

    if confidence >= 85:
        reasons.append("high_data_confidence")

    if not reasons:
        reasons.append("no_strong_quant_signal")

    return ";".join(reasons)


def build_missing_key_data_quant(row: pd.Series | dict[str, Any]) -> str:
    """
    Return a semicolon-separated list of missing fields relevant to scoring.
    """

    fields = [
        "price",
        "previous_close",
        "volume",
        "avg_volume_50d",
        "relative_volume",
        "change_1d",
        "change_5d",
        "change_20d",
        "ma20",
        "ma50",
        "market_cap",
        "data_quality_score",
    ]

    missing = [field for field in fields if _is_missing(row.get(field))]

    return ";".join(missing)


def apply_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply scoring to a dataframe.

    The function keeps all rows, including excluded companies, so the result
    remains auditable.

    Parameters
    ----------
    df:
        Dataframe after data quality and basic filters.

    Returns
    -------
    pandas.DataFrame
        Dataframe with scoring columns.
    """

    df_scored = df.copy()

    scoring_results = df_scored.apply(calculate_priority_score, axis=1)
    scoring_df = pd.DataFrame(scoring_results.tolist(), index=df_scored.index)

    for column in scoring_df.columns:
        df_scored[column] = scoring_df[column]

    return df_scored


def get_priority_companies(
    df: pd.DataFrame,
    min_score: float = 50.0,
    include_excluded: bool = False,
) -> pd.DataFrame:
    """
    Return companies sorted by priority score.

    Parameters
    ----------
    df:
        Dataframe after apply_scoring().
    min_score:
        Minimum score_priority to include.
    include_excluded:
        Whether to include companies that failed basic filters.

    Returns
    -------
    pandas.DataFrame
        Prioritized dataframe.
    """

    if "score_priority" not in df.columns:
        raise ValueError("Missing column: score_priority. Run apply_scoring() first.")

    result = df[df["score_priority"] >= min_score].copy()

    if not include_excluded and "passes_basic_filters" in result.columns:
        result = result[result["passes_basic_filters"] == True]  # noqa: E712

    return result.sort_values(
        by=["score_priority", "score_confidence"],
        ascending=[False, False],
    ).reset_index(drop=True)


def summarize_scoring(df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize scoring output.

    Parameters
    ----------
    df:
        Dataframe after apply_scoring().

    Returns
    -------
    dict
        Summary dictionary.
    """

    if df.empty:
        return {
            "total_rows": 0,
            "scored_companies": 0,
            "avg_score_priority": None,
            "max_score_priority": None,
            "high_priority_research": 0,
            "medium_priority_research": 0,
            "watchlist": 0,
            "low_priority": 0,
            "first_5_priority_tickers": [],
        }

    if "score_priority" not in df.columns:
        raise ValueError("Missing column: score_priority. Run apply_scoring() first.")

    category_counts = df["category_final"].value_counts().to_dict()
    priority_df = get_priority_companies(df, min_score=0)

    return {
        "total_rows": int(len(df)),
        "scored_companies": int(df["score_priority"].notna().sum()),
        "avg_score_priority": float(df["score_priority"].mean()),
        "max_score_priority": float(df["score_priority"].max()),
        "high_priority_research": int(category_counts.get("high_priority_research", 0)),
        "medium_priority_research": int(category_counts.get("medium_priority_research", 0)),
        "watchlist": int(category_counts.get("watchlist", 0)),
        "low_priority": int(category_counts.get("low_priority", 0)),
        "first_5_priority_tickers": priority_df["ticker"].head(5).tolist()
        if "ticker" in priority_df.columns
        else [],
    }


if __name__ == "__main__":
    from src.data_quality import apply_data_quality, summarize_data_quality
    from src.filters import apply_basic_filters, summarize_filters
    from src.market_data import build_market_snapshot, summarize_market_snapshot
    from src.universe import validate_and_load_universe

    universe_df, universe_summary = validate_and_load_universe(mode="demo")

    print("Universe loaded:")
    print(universe_summary)

    snapshot_df = build_market_snapshot(universe_df, period="1y")
    snapshot_summary = summarize_market_snapshot(snapshot_df)

    print("\nMarket snapshot summary:")
    for key, value in snapshot_summary.items():
        print(f"- {key}: {value}")

    quality_df = apply_data_quality(snapshot_df)
    quality_summary = summarize_data_quality(quality_df)

    print("\nData quality summary:")
    for key, value in quality_summary.items():
        print(f"- {key}: {value}")

    filtered_df = apply_basic_filters(quality_df)
    filter_summary = summarize_filters(filtered_df)

    print("\nFilter summary:")
    for key, value in filter_summary.items():
        print(f"- {key}: {value}")

    scored_df = apply_scoring(filtered_df)
    scoring_summary = summarize_scoring(scored_df)

    print("\nScoring summary:")
    for key, value in scoring_summary.items():
        print(f"- {key}: {value}")

    print("\nTop 10 priority companies:")
    columns_to_show = [
        "ticker",
        "company_name",
        "price",
        "relative_volume",
        "change_5d",
        "change_20d",
        "score_volume",
        "score_momentum",
        "score_liquidity",
        "score_context",
        "score_risk",
        "score_confidence",
        "score_priority",
        "category_final",
        "reason_to_pass_quant",
    ]
    priority_df = get_priority_companies(scored_df, min_score=0)
    available_columns = [column for column in columns_to_show if column in priority_df.columns]
    print(priority_df[available_columns].head(10).to_string(index=False))
