"""
Results module.

This module reads persisted MVP results from SQLite.

Current scope:
- List recent runs.
- Read one run summary.
- Read market snapshots for a run.
- Read signals for a run.
- Return top prioritized companies.
- Return enriched signals joined with market snapshots.
- Return final research view:
    signals + market_snapshots + latest OpenAI analysis + latest manual feedback.
- Provide a simple console check.

Not included in this phase:
- Streamlit UI.
- Export files.
- Manual feedback writes.
- OpenAI analysis writes.
- Validation after signal date.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import get_paths
from src.database import get_connection


DEFAULT_TOP_N = 10


def _get_db_path(mode: str = "demo") -> Path:
    """
    Resolve the SQLite database path for demo or real mode.
    """

    if mode not in {"demo", "real"}:
        raise ValueError("Invalid mode. Expected 'demo' or 'real'.")

    paths = get_paths(mode)
    return Path(paths["db_path"])


def list_runs(mode: str = "demo", limit: int = 10) -> pd.DataFrame:
    """
    Return recent pipeline runs.
    """

    db_path = _get_db_path(mode)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    query = """
        SELECT
            run_id,
            created_at,
            mode,
            universe_size,
            valid_companies,
            excluded_companies,
            scored_companies,
            openai_analyzed_companies,
            scoring_version,
            prompt_version,
            status,
            notes
        FROM runs
        ORDER BY created_at DESC
        LIMIT ?
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(limit,))


def get_latest_run_id(mode: str = "demo") -> str | None:
    """
    Return the latest run_id for a mode.
    """

    runs_df = list_runs(mode=mode, limit=1)

    if runs_df.empty:
        return None

    return str(runs_df.iloc[0]["run_id"])


def get_run_summary(run_id: str | None = None, mode: str = "demo") -> dict[str, Any]:
    """
    Return summary information for one run.

    If run_id is None, the latest run is used.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return {
            "run_id": None,
            "status": None,
            "message": "No runs found.",
        }

    with get_connection(db_path) as conn:
        run_row = conn.execute(
            """
            SELECT *
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        if run_row is None:
            raise ValueError(f"Run not found: {run_id}")

        market_snapshots = conn.execute(
            "SELECT COUNT(*) AS total FROM market_snapshots WHERE run_id = ?",
            (run_id,),
        ).fetchone()["total"]

        signals = conn.execute(
            "SELECT COUNT(*) AS total FROM signals WHERE run_id = ?",
            (run_id,),
        ).fetchone()["total"]

        data_errors = conn.execute(
            "SELECT COUNT(*) AS total FROM data_errors WHERE run_id = ?",
            (run_id,),
        ).fetchone()["total"]

        openai_analysis = conn.execute(
            "SELECT COUNT(*) AS total FROM openai_analysis WHERE run_id = ?",
            (run_id,),
        ).fetchone()["total"]

        cost_log = conn.execute(
            "SELECT COUNT(*) AS total FROM cost_log WHERE run_id = ?",
            (run_id,),
        ).fetchone()["total"]

    return {
        "run_id": run_row["run_id"],
        "created_at": run_row["created_at"],
        "mode": run_row["mode"],
        "status": run_row["status"],
        "universe_size": run_row["universe_size"],
        "valid_companies": run_row["valid_companies"],
        "excluded_companies": run_row["excluded_companies"],
        "scored_companies": run_row["scored_companies"],
        "openai_analyzed_companies": run_row["openai_analyzed_companies"],
        "scoring_version": run_row["scoring_version"],
        "prompt_version": run_row["prompt_version"],
        "notes": run_row["notes"],
        "market_snapshots_rows": int(market_snapshots),
        "signals_rows": int(signals),
        "data_errors_rows": int(data_errors),
        "openai_analysis_rows": int(openai_analysis),
        "cost_log_rows": int(cost_log),
    }


def load_market_snapshots(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load market snapshots for one run.

    If run_id is None, the latest run is used.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT *
        FROM market_snapshots
        WHERE run_id = ?
        ORDER BY ticker ASC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id,))


def load_signals(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load quantitative signals for one run.

    If run_id is None, the latest run is used.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT *
        FROM signals
        WHERE run_id = ?
        ORDER BY score_priority DESC, score_confidence DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id,))


def load_enriched_signals(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load signals enriched with market snapshot context.

    This joins:
    - signals
    - market_snapshots

    Join key:
    - run_id
    - ticker
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT
            s.id,
            s.run_id,
            s.created_at AS signal_created_at,
            s.ticker,

            ms.created_at AS snapshot_created_at,
            ms.company_name,
            ms.sector,
            ms.industry,
            ms.exchange,
            ms.currency,
            ms.price,
            ms.previous_close,
            ms.volume,
            ms.avg_volume_50d,
            ms.relative_volume,
            ms.change_1d,
            ms.change_5d,
            ms.change_20d,
            ms.ma20,
            ms.ma50,
            ms.above_ma20,
            ms.above_ma50,
            ms.high_52w,
            ms.low_52w,
            ms.distance_to_52w_high,
            ms.distance_to_52w_low,
            ms.market_cap,
            ms.data_source,
            ms.data_quality_score,
            ms.data_quality_label,

            s.price_at_signal,
            s.score_catalyst,
            s.score_volume,
            s.score_momentum,
            s.score_liquidity,
            s.score_context,
            s.score_fundamental,
            s.score_asymmetry,
            s.score_raw,
            s.penalty_total,
            s.score_adjusted,
            s.score_risk,
            s.score_confidence,
            s.score_dilution,
            s.score_priority,
            s.category_final,
            s.opportunity_phase,
            s.veto_applied,
            s.veto_reason,
            s.reason_to_pass_quant,
            s.missing_key_data_quant,
            s.scoring_version
        FROM signals s
        LEFT JOIN market_snapshots ms
            ON s.run_id = ms.run_id
           AND s.ticker = ms.ticker
        WHERE s.run_id = ?
        ORDER BY s.score_priority DESC, s.score_confidence DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id,))


def get_top_signals(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = DEFAULT_TOP_N,
    min_score: float | None = None,
    include_excluded: bool = False,
) -> pd.DataFrame:
    """
    Return top signals for one run.
    """

    signals_df = load_signals(run_id=run_id, mode=mode)

    if signals_df.empty:
        return signals_df

    result = signals_df.copy()

    if min_score is not None:
        result = result[result["score_priority"] >= min_score]

    if not include_excluded and "category_final" in result.columns:
        result = result[result["category_final"] != "excluded"]

    return result.sort_values(
        by=["score_priority", "score_confidence"],
        ascending=[False, False],
    ).head(top_n).reset_index(drop=True)


def get_top_signals_enriched(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = DEFAULT_TOP_N,
    min_score: float | None = None,
    include_excluded: bool = False,
) -> pd.DataFrame:
    """
    Return top signals enriched with market snapshot context.
    """

    enriched_df = load_enriched_signals(run_id=run_id, mode=mode)

    if enriched_df.empty:
        return enriched_df

    result = enriched_df.copy()

    if min_score is not None:
        result = result[result["score_priority"] >= min_score]

    if not include_excluded and "category_final" in result.columns:
        result = result[result["category_final"] != "excluded"]

    return result.sort_values(
        by=["score_priority", "score_confidence"],
        ascending=[False, False],
    ).head(top_n).reset_index(drop=True)


def load_openai_analysis(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load OpenAI analysis rows for one run.

    If run_id is None, the latest run is used.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT *
        FROM openai_analysis
        WHERE run_id = ?
        ORDER BY created_at DESC, id DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id,))


def load_latest_openai_analysis_per_signal(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load the latest OpenAI analysis row per signal for one run.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT oa.*
        FROM openai_analysis oa
        INNER JOIN (
            SELECT signal_id, MAX(id) AS latest_id
            FROM openai_analysis
            WHERE run_id = ?
            GROUP BY signal_id
        ) latest
            ON oa.id = latest.latest_id
        WHERE oa.run_id = ?
        ORDER BY oa.created_at DESC, oa.id DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id, run_id))


def load_cost_log(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load cost log rows for one run.

    If run_id is None, the latest run is used.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT *
        FROM cost_log
        WHERE run_id = ?
        ORDER BY created_at DESC, id DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id,))


def load_manual_feedback(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load manual feedback rows joined with signals for one run.

    If run_id is None, the latest run is used.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT
            mf.id,
            mf.signal_id,
            mf.ticker,
            mf.created_at,
            mf.feedback_label,
            mf.notes,
            mf.reviewed_by,
            s.run_id
        FROM manual_feedback mf
        LEFT JOIN signals s
            ON mf.signal_id = s.id
        WHERE s.run_id = ?
        ORDER BY mf.created_at DESC, mf.id DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id,))


def load_latest_manual_feedback_per_signal(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load the latest manual feedback row per signal for one run.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT
            mf.id,
            mf.signal_id,
            mf.ticker,
            mf.created_at,
            mf.feedback_label,
            mf.notes,
            mf.reviewed_by,
            s.run_id
        FROM manual_feedback mf
        LEFT JOIN signals s
            ON mf.signal_id = s.id
        INNER JOIN (
            SELECT mf2.signal_id, MAX(mf2.id) AS latest_id
            FROM manual_feedback mf2
            LEFT JOIN signals s2
                ON mf2.signal_id = s2.id
            WHERE s2.run_id = ?
            GROUP BY mf2.signal_id
        ) latest
            ON mf.id = latest.latest_id
        WHERE s.run_id = ?
        ORDER BY mf.created_at DESC, mf.id DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id, run_id))


def load_final_research_view(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load the final consolidated research view for one run.

    This combines:
    - enriched signals: signals + market_snapshots
    - latest OpenAI analysis per signal
    - latest manual feedback per signal

    It is the best current read model for a future Streamlit table.
    """

    enriched_df = load_enriched_signals(run_id=run_id, mode=mode)

    if enriched_df.empty:
        return enriched_df

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    openai_df = load_latest_openai_analysis_per_signal(run_id=run_id, mode=mode)
    feedback_df = load_latest_manual_feedback_per_signal(run_id=run_id, mode=mode)

    result = enriched_df.copy()

    if not openai_df.empty:
        openai_subset = openai_df[
            [
                "signal_id",
                "id",
                "created_at",
                "model",
                "summary_thesis",
                "suggested_category",
                "confidence_level",
                "hype_risk",
                "source_quality",
                "reason_to_pass",
                "missing_key_data",
                "why_it_could_work",
                "why_it_could_fail",
                "estimated_cost",
                "cache_hit",
            ]
        ].rename(
            columns={
                "signal_id": "id",
                "id": "openai_analysis_id",
                "created_at": "openai_created_at",
                "model": "openai_model",
                "reason_to_pass": "openai_reason_to_pass",
                "estimated_cost": "openai_estimated_cost",
                "cache_hit": "openai_cache_hit",
            }
        )

        result = result.merge(openai_subset, on="id", how="left")
    else:
        result["openai_analysis_id"] = None
        result["openai_created_at"] = None
        result["openai_model"] = None
        result["summary_thesis"] = None
        result["suggested_category"] = None
        result["confidence_level"] = None
        result["hype_risk"] = None
        result["source_quality"] = None
        result["openai_reason_to_pass"] = None
        result["missing_key_data"] = None
        result["why_it_could_work"] = None
        result["why_it_could_fail"] = None
        result["openai_estimated_cost"] = None
        result["openai_cache_hit"] = None

    if not feedback_df.empty:
        feedback_subset = feedback_df[
            [
                "signal_id",
                "id",
                "created_at",
                "feedback_label",
                "notes",
                "reviewed_by",
            ]
        ].rename(
            columns={
                "signal_id": "id",
                "id": "feedback_id",
                "created_at": "feedback_created_at",
                "notes": "feedback_notes",
            }
        )

        result = result.merge(feedback_subset, on="id", how="left")
    else:
        result["feedback_id"] = None
        result["feedback_created_at"] = None
        result["feedback_label"] = None
        result["feedback_notes"] = None
        result["reviewed_by"] = None

    return result.sort_values(
        by=["score_priority", "score_confidence"],
        ascending=[False, False],
    ).reset_index(drop=True)


def get_top_final_research_view(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = DEFAULT_TOP_N,
    min_score: float | None = None,
    include_excluded: bool = False,
) -> pd.DataFrame:
    """
    Return top rows from the final consolidated research view.
    """

    view_df = load_final_research_view(run_id=run_id, mode=mode)

    if view_df.empty:
        return view_df

    result = view_df.copy()

    if min_score is not None:
        result = result[result["score_priority"] >= min_score]

    if not include_excluded and "category_final" in result.columns:
        result = result[result["category_final"] != "excluded"]

    return result.head(top_n).reset_index(drop=True)


def summarize_signals(signals_df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize a signals dataframe.
    """

    if signals_df.empty:
        return {
            "total_signals": 0,
            "avg_score_priority": None,
            "max_score_priority": None,
            "categories": {},
            "first_5_tickers": [],
        }

    categories = (
        signals_df["category_final"].value_counts().to_dict()
        if "category_final" in signals_df.columns
        else {}
    )

    return {
        "total_signals": int(len(signals_df)),
        "avg_score_priority": float(signals_df["score_priority"].mean())
        if "score_priority" in signals_df.columns
        else None,
        "max_score_priority": float(signals_df["score_priority"].max())
        if "score_priority" in signals_df.columns
        else None,
        "categories": categories,
        "first_5_tickers": signals_df["ticker"].head(5).tolist()
        if "ticker" in signals_df.columns
        else [],
    }


def summarize_enriched_signals(enriched_df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize enriched signal context completeness.
    """

    if enriched_df.empty:
        return {
            "total_rows": 0,
            "rows_with_company_name": 0,
            "rows_with_sector": 0,
            "rows_with_market_cap": 0,
            "rows_with_relative_volume": 0,
            "rows_with_change_5d": 0,
            "first_5_tickers": [],
        }

    return {
        "total_rows": int(len(enriched_df)),
        "rows_with_company_name": int(enriched_df["company_name"].notna().sum())
        if "company_name" in enriched_df.columns
        else 0,
        "rows_with_sector": int(enriched_df["sector"].notna().sum())
        if "sector" in enriched_df.columns
        else 0,
        "rows_with_market_cap": int(enriched_df["market_cap"].notna().sum())
        if "market_cap" in enriched_df.columns
        else 0,
        "rows_with_relative_volume": int(enriched_df["relative_volume"].notna().sum())
        if "relative_volume" in enriched_df.columns
        else 0,
        "rows_with_change_5d": int(enriched_df["change_5d"].notna().sum())
        if "change_5d" in enriched_df.columns
        else 0,
        "first_5_tickers": enriched_df["ticker"].head(5).tolist()
        if "ticker" in enriched_df.columns
        else [],
    }


def summarize_final_research_view(view_df: pd.DataFrame) -> dict[str, Any]:
    """
    Summarize final consolidated research view.
    """

    if view_df.empty:
        return {
            "total_rows": 0,
            "rows_with_openai_analysis": 0,
            "rows_with_manual_feedback": 0,
            "total_openai_estimated_cost": 0.0,
            "feedback_labels": {},
            "first_5_tickers": [],
        }

    feedback_labels = (
        view_df["feedback_label"].dropna().value_counts().to_dict()
        if "feedback_label" in view_df.columns
        else {}
    )

    return {
        "total_rows": int(len(view_df)),
        "rows_with_openai_analysis": int(view_df["openai_analysis_id"].notna().sum())
        if "openai_analysis_id" in view_df.columns
        else 0,
        "rows_with_manual_feedback": int(view_df["feedback_id"].notna().sum())
        if "feedback_id" in view_df.columns
        else 0,
        "total_openai_estimated_cost": float(
            view_df["openai_estimated_cost"].fillna(0).sum()
        )
        if "openai_estimated_cost" in view_df.columns
        else 0.0,
        "feedback_labels": feedback_labels,
        "first_5_tickers": view_df["ticker"].head(5).tolist()
        if "ticker" in view_df.columns
        else [],
    }


def load_data_errors(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load data errors for one run.

    If run_id is None, the latest run is used.
    """

    db_path = _get_db_path(mode)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return pd.DataFrame()

    query = """
        SELECT *
        FROM data_errors
        WHERE run_id = ?
        ORDER BY created_at DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=(run_id,))


if __name__ == "__main__":
    mode = "demo"

    print("Recent runs:")
    runs_df = list_runs(mode=mode, limit=5)
    if runs_df.empty:
        print("No runs found.")
    else:
        columns_to_show = [
            "run_id",
            "created_at",
            "mode",
            "valid_companies",
            "excluded_companies",
            "scored_companies",
            "openai_analyzed_companies",
            "status",
        ]
        print(runs_df[columns_to_show].to_string(index=False))

    latest_run_id = get_latest_run_id(mode=mode)

    print("\nLatest run summary:")
    summary = get_run_summary(run_id=latest_run_id, mode=mode)
    for key, value in summary.items():
        print(f"- {key}: {value}")

    print("\nTop signals:")
    top_df = get_top_signals(run_id=latest_run_id, mode=mode, top_n=10)

    if top_df.empty:
        print("No signals found.")
    else:
        columns_to_show = [
            "ticker",
            "price_at_signal",
            "score_priority",
            "score_confidence",
            "score_risk",
            "category_final",
            "reason_to_pass_quant",
        ]
        available_columns = [column for column in columns_to_show if column in top_df.columns]
        print(top_df[available_columns].to_string(index=False))

    print("\nTop enriched signals:")
    enriched_top_df = get_top_signals_enriched(
        run_id=latest_run_id,
        mode=mode,
        top_n=10,
    )

    if enriched_top_df.empty:
        print("No enriched signals found.")
    else:
        enriched_columns_to_show = [
            "ticker",
            "company_name",
            "sector",
            "industry",
            "market_cap",
            "relative_volume",
            "change_5d",
            "change_20d",
            "score_priority",
            "category_final",
        ]
        available_columns = [
            column for column in enriched_columns_to_show
            if column in enriched_top_df.columns
        ]
        print(enriched_top_df[available_columns].to_string(index=False))

    print("\nEnriched signal summary:")
    enriched_summary = summarize_enriched_signals(enriched_top_df)
    for key, value in enriched_summary.items():
        print(f"- {key}: {value}")

    print("\nFinal research view:")
    final_view_df = get_top_final_research_view(
        run_id=latest_run_id,
        mode=mode,
        top_n=10,
    )

    if final_view_df.empty:
        print("No final research view rows found.")
    else:
        final_columns_to_show = [
            "ticker",
            "company_name",
            "score_priority",
            "category_final",
            "openai_model",
            "openai_reason_to_pass",
            "openai_estimated_cost",
            "feedback_label",
            "reviewed_by",
        ]
        available_columns = [
            column for column in final_columns_to_show
            if column in final_view_df.columns
        ]
        print(final_view_df[available_columns].to_string(index=False))

    print("\nFinal research view summary:")
    final_summary = summarize_final_research_view(final_view_df)
    for key, value in final_summary.items():
        print(f"- {key}: {value}")

    print("\nCost log:")
    cost_df = load_cost_log(run_id=latest_run_id, mode=mode)
    if cost_df.empty:
        print("No cost log rows found.")
    else:
        columns_to_show = [
            "ticker",
            "model",
            "purpose",
            "input_tokens",
            "output_tokens",
            "estimated_cost",
            "cache_hit",
        ]
        available_columns = [column for column in columns_to_show if column in cost_df.columns]
        print(cost_df[available_columns].head(10).to_string(index=False))

    print("\nData errors:")
    errors_df = load_data_errors(run_id=latest_run_id, mode=mode)
    if errors_df.empty:
        print("No data errors found.")
    else:
        columns_to_show = [
            "ticker",
            "source",
            "error_type",
            "severity",
            "error_message",
        ]
        available_columns = [column for column in columns_to_show if column in errors_df.columns]
        print(errors_df[available_columns].to_string(index=False))
