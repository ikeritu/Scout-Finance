"""
OpenAI persistence module.

This module persists OpenAI analysis results into SQLite.

Current scope:
- Insert normalized OpenAI analysis payloads into openai_analysis.
- Insert cost log rows into cost_log.
- Run placeholder analysis for top enriched signals.
- Persist skipped/disabled results when ENABLE_OPENAI=false.
- Update runs.openai_analyzed_companies.

Not included in this phase:
- Real OpenAI API calls.
- News retrieval.
- Web search.
- Streamlit UI.
- Prompt optimization.
- Advanced cost accounting.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from config import get_paths
from src.database import get_connection, utc_now_iso
from src.openai_analysis import (
    analyze_company_placeholder,
    result_to_database_payload,
    summarize_analysis_results,
)
from src.openai_client import get_selected_model, validate_company_limit
from src.results import get_latest_run_id, get_top_signals_enriched


OPENAI_ANALYSIS_COLUMNS = [
    "signal_id",
    "run_id",
    "created_at",
    "ticker",
    "model",
    "prompt_version",
    "schema_version",
    "summary_thesis",
    "opportunity_type",
    "opportunity_phase",
    "suggested_category",
    "confidence_level",
    "hype_risk",
    "source_quality",
    "reason_to_pass",
    "missing_key_data",
    "event_to_confirm",
    "source_to_verify",
    "verifiable_facts_json",
    "reasonable_inferences_json",
    "speculative_elements_json",
    "contradictions_json",
    "checklist_json",
    "why_it_could_work",
    "why_it_could_fail",
    "discrepancy_with_python",
    "raw_response_json",
    "input_tokens",
    "output_tokens",
    "estimated_cost",
    "cache_hit",
]


COST_LOG_COLUMNS = [
    "run_id",
    "signal_id",
    "ticker",
    "created_at",
    "model",
    "purpose",
    "input_tokens",
    "output_tokens",
    "estimated_cost",
    "cache_hit",
    "prompt_version",
]


def _get_db_path(mode: str = "demo") -> Path:
    """
    Resolve database path for mode.
    """

    if mode not in {"demo", "real"}:
        raise ValueError("Invalid mode. Expected 'demo' or 'real'.")

    paths = get_paths(mode)
    return Path(paths["db_path"])


def _make_json_safe(value: Any) -> Any:
    """
    Convert pandas/numpy values into JSON-serializable Python values.

    This helper handles containers before pd.isna() to avoid ambiguity errors.
    """

    if value is None:
        return None

    if isinstance(value, dict):
        return {str(key): _make_json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_make_json_safe(item) for item in value]

    if hasattr(value, "item"):
        try:
            return _make_json_safe(value.item())
        except Exception:
            return str(value)

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


def _to_sql_value(value: Any) -> Any:
    """
    Convert values to SQLite-safe values.

    SQLite can store simple values, not Python lists/dicts or numpy scalar types.
    """

    safe_value = _make_json_safe(value)

    if safe_value is None:
        return None

    if isinstance(safe_value, bool):
        return int(safe_value)

    if isinstance(safe_value, (dict, list)):
        return json.dumps(safe_value, ensure_ascii=False)

    return safe_value


def insert_openai_analysis(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
) -> int:
    """
    Insert one OpenAI analysis payload into SQLite.

    Parameters
    ----------
    conn:
        SQLite connection.
    payload:
        Payload aligned with openai_analysis table.

    Returns
    -------
    int
        Created openai_analysis row id.
    """

    row_payload = dict(payload)
    row_payload["created_at"] = utc_now_iso()

    placeholders = ", ".join(["?"] * len(OPENAI_ANALYSIS_COLUMNS))
    columns_sql = ", ".join(OPENAI_ANALYSIS_COLUMNS)

    sql = f"""
        INSERT INTO openai_analysis ({columns_sql})
        VALUES ({placeholders})
    """

    values = tuple(_to_sql_value(row_payload.get(column)) for column in OPENAI_ANALYSIS_COLUMNS)

    cursor = conn.execute(sql, values)
    return int(cursor.lastrowid)


def insert_cost_log(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    purpose: str = "openai_company_analysis",
) -> int:
    """
    Insert one cost log row into SQLite.

    Parameters
    ----------
    conn:
        SQLite connection.
    payload:
        OpenAI analysis payload.
    purpose:
        Cost purpose label.

    Returns
    -------
    int
        Created cost_log row id.
    """

    row_payload = {
        "run_id": payload.get("run_id"),
        "signal_id": payload.get("signal_id"),
        "ticker": payload.get("ticker"),
        "created_at": utc_now_iso(),
        "model": payload.get("model"),
        "purpose": purpose,
        "input_tokens": payload.get("input_tokens", 0),
        "output_tokens": payload.get("output_tokens", 0),
        "estimated_cost": payload.get("estimated_cost", 0.0),
        "cache_hit": payload.get("cache_hit", 0),
        "prompt_version": payload.get("prompt_version"),
    }

    placeholders = ", ".join(["?"] * len(COST_LOG_COLUMNS))
    columns_sql = ", ".join(COST_LOG_COLUMNS)

    sql = f"""
        INSERT INTO cost_log ({columns_sql})
        VALUES ({placeholders})
    """

    values = tuple(_to_sql_value(row_payload.get(column)) for column in COST_LOG_COLUMNS)

    cursor = conn.execute(sql, values)
    return int(cursor.lastrowid)


def count_openai_analysis_for_run(
    conn: sqlite3.Connection,
    run_id: str,
) -> int:
    """
    Count OpenAI analysis rows for one run.
    """

    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM openai_analysis
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()

    return int(row["total"])


def update_run_openai_count(
    conn: sqlite3.Connection,
    run_id: str,
) -> int:
    """
    Update runs.openai_analyzed_companies using current openai_analysis rows.
    """

    total = count_openai_analysis_for_run(conn, run_id)

    conn.execute(
        """
        UPDATE runs
        SET openai_analyzed_companies = ?
        WHERE run_id = ?
        """,
        (total, run_id),
    )

    return total


def load_openai_analysis(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load OpenAI analysis rows for one run.

    If run_id is None, latest run is used.
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


def load_cost_log(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load cost log rows for one run.

    If run_id is None, latest run is used.
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


def persist_placeholder_analysis_for_top_signals(
    run_id: str | None = None,
    mode: str = "demo",
    top_n: int = 3,
    use_strong_model: bool = False,
    write_cost_log: bool = True,
) -> dict[str, Any]:
    """
    Run placeholder analysis for top enriched signals and persist results.

    This does not call OpenAI while openai_analysis.py is in placeholder mode.
    It persists skipped/disabled results so the full database circuit can be
    tested before enabling real API calls.

    Parameters
    ----------
    run_id:
        Optional run id. If None, latest run is used.
    mode:
        Either "demo" or "real".
    top_n:
        Number of top enriched signals to process.
    use_strong_model:
        Whether strong model would be requested.
    write_cost_log:
        Whether to write cost_log rows.

    Returns
    -------
    dict
        Persistence summary.
    """

    validate_company_limit(top_n)

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        raise ValueError("No runs found. Execute python -m src.pipeline first.")

    db_path = _get_db_path(mode)

    top_df = get_top_signals_enriched(
        run_id=run_id,
        mode=mode,
        top_n=top_n,
    )

    if top_df.empty:
        return {
            "run_id": run_id,
            "mode": mode,
            "selected_signals": 0,
            "analysis_rows_inserted": 0,
            "cost_rows_inserted": 0,
            "openai_analyzed_companies": 0,
            "results_summary": summarize_analysis_results([]),
        }

    inserted_analysis_ids: list[int] = []
    inserted_cost_ids: list[int] = []
    results: list[dict[str, Any]] = []

    with get_connection(db_path) as conn:
        for _, row in top_df.iterrows():
            result = analyze_company_placeholder(
                row,
                use_strong_model=use_strong_model,
            )
            results.append(result)

            payload = result_to_database_payload(
                result=result,
                signal_id=int(row["id"]),
                run_id=run_id,
            )

            analysis_id = insert_openai_analysis(conn, payload)
            inserted_analysis_ids.append(analysis_id)

            if write_cost_log:
                cost_id = insert_cost_log(conn, payload)
                inserted_cost_ids.append(cost_id)

        openai_analyzed_count = update_run_openai_count(conn, run_id)
        conn.commit()

    return {
        "run_id": run_id,
        "mode": mode,
        "model": get_selected_model(use_strong_model=use_strong_model),
        "selected_signals": int(len(top_df)),
        "analysis_rows_inserted": int(len(inserted_analysis_ids)),
        "cost_rows_inserted": int(len(inserted_cost_ids)),
        "openai_analyzed_companies": int(openai_analyzed_count),
        "inserted_analysis_ids": inserted_analysis_ids,
        "inserted_cost_ids": inserted_cost_ids,
        "results_summary": summarize_analysis_results(results),
    }


def summarize_persisted_openai_analysis(
    run_id: str | None = None,
    mode: str = "demo",
) -> dict[str, Any]:
    """
    Summarize persisted OpenAI analysis and cost rows.
    """

    analysis_df = load_openai_analysis(run_id=run_id, mode=mode)
    cost_df = load_cost_log(run_id=run_id, mode=mode)

    if analysis_df.empty:
        return {
            "analysis_rows": 0,
            "cost_rows": int(len(cost_df)),
            "tickers": [],
            "total_estimated_cost": 0.0,
            "models": [],
        }

    return {
        "analysis_rows": int(len(analysis_df)),
        "cost_rows": int(len(cost_df)),
        "tickers": analysis_df["ticker"].dropna().tolist()
        if "ticker" in analysis_df.columns
        else [],
        "total_estimated_cost": float(analysis_df["estimated_cost"].fillna(0).sum())
        if "estimated_cost" in analysis_df.columns
        else 0.0,
        "models": sorted(analysis_df["model"].dropna().unique().tolist())
        if "model" in analysis_df.columns
        else [],
    }


if __name__ == "__main__":
    mode = "demo"
    run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        raise SystemExit("No runs found. Execute python -m src.pipeline first.")

    print(f"Persisting placeholder OpenAI analysis for run: {run_id}")

    summary = persist_placeholder_analysis_for_top_signals(
        run_id=run_id,
        mode=mode,
        top_n=3,
        use_strong_model=False,
        write_cost_log=True,
    )

    print("\nPersistence summary:")
    for key, value in summary.items():
        print(f"- {key}: {value}")

    print("\nPersisted OpenAI analysis summary:")
    persisted_summary = summarize_persisted_openai_analysis(
        run_id=run_id,
        mode=mode,
    )
    for key, value in persisted_summary.items():
        print(f"- {key}: {value}")

    print("\nLatest OpenAI analysis rows:")
    analysis_df = load_openai_analysis(run_id=run_id, mode=mode)
    if analysis_df.empty:
        print("No OpenAI analysis rows found.")
    else:
        columns_to_show = [
            "id",
            "signal_id",
            "ticker",
            "model",
            "reason_to_pass",
            "input_tokens",
            "output_tokens",
            "estimated_cost",
            "cache_hit",
        ]
        available_columns = [column for column in columns_to_show if column in analysis_df.columns]
        print(analysis_df[available_columns].head(10).to_string(index=False))

    print("\nLatest cost log rows:")
    cost_df = load_cost_log(run_id=run_id, mode=mode)
    if cost_df.empty:
        print("No cost log rows found.")
    else:
        columns_to_show = [
            "id",
            "signal_id",
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
