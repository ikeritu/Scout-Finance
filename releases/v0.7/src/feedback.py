"""
Feedback module.

This module manages manual feedback for persisted quantitative signals.

Current scope:
- List available feedback labels.
- Add manual feedback for a signal.
- Add manual feedback by ticker and run_id.
- Read feedback history.
- Join latest signals with latest manual feedback.
- Provide a simple console demo.

Not included in this phase:
- Streamlit UI.
- User authentication.
- OpenAI analysis.
- Automatic learning from feedback.
- Portfolio decisions.
- Buy/sell recommendations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import get_paths
from src.database import get_connection, utc_now_iso
from src.results import get_latest_run_id, get_top_signals, load_signals


VALID_FEEDBACK_LABELS = {
    "interesting",
    "discard",
    "review_later",
    "false_positive",
    "needs_more_research",
    "already_known",
}


def _get_db_path(mode: str = "demo") -> Path:
    """
    Resolve the SQLite database path for demo or real mode.
    """

    if mode not in {"demo", "real"}:
        raise ValueError("Invalid mode. Expected 'demo' or 'real'.")

    paths = get_paths(mode)
    return Path(paths["db_path"])


def get_valid_feedback_labels() -> list[str]:
    """
    Return the allowed manual feedback labels.
    """

    return sorted(VALID_FEEDBACK_LABELS)


def validate_feedback_label(feedback_label: str) -> None:
    """
    Validate a feedback label.

    Raises
    ------
    ValueError
        If the label is not allowed.
    """

    if feedback_label not in VALID_FEEDBACK_LABELS:
        allowed = ", ".join(get_valid_feedback_labels())
        raise ValueError(f"Invalid feedback_label '{feedback_label}'. Allowed: {allowed}")


def get_signal_by_id(
    signal_id: int,
    mode: str = "demo",
) -> dict[str, Any] | None:
    """
    Return a signal row by internal signal id.

    Parameters
    ----------
    signal_id:
        Internal id from the signals table.
    mode:
        Either "demo" or "real".

    Returns
    -------
    dict | None
        Signal row as dictionary or None if not found.
    """

    db_path = _get_db_path(mode)

    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM signals
            WHERE id = ?
            """,
            (signal_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_signal_by_ticker(
    ticker: str,
    run_id: str | None = None,
    mode: str = "demo",
) -> dict[str, Any] | None:
    """
    Return a signal row by ticker and run_id.

    If run_id is None, the latest run is used.

    Parameters
    ----------
    ticker:
        Ticker symbol.
    run_id:
        Optional run identifier.
    mode:
        Either "demo" or "real".

    Returns
    -------
    dict | None
        Signal row as dictionary or None if not found.
    """

    if run_id is None:
        run_id = get_latest_run_id(mode=mode)

    if run_id is None:
        return None

    db_path = _get_db_path(mode)

    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM signals
            WHERE run_id = ?
              AND ticker = ?
            ORDER BY score_priority DESC
            LIMIT 1
            """,
            (run_id, ticker.upper().strip()),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def add_manual_feedback(
    signal_id: int,
    feedback_label: str,
    notes: str | None = None,
    reviewed_by: str | None = None,
    mode: str = "demo",
) -> int:
    """
    Insert manual feedback for a signal.

    Parameters
    ----------
    signal_id:
        Internal id from the signals table.
    feedback_label:
        One of the allowed feedback labels.
    notes:
        Optional notes.
    reviewed_by:
        Optional reviewer name.
    mode:
        Either "demo" or "real".

    Returns
    -------
    int
        Created feedback row id.
    """

    validate_feedback_label(feedback_label)

    signal = get_signal_by_id(signal_id=signal_id, mode=mode)

    if signal is None:
        raise ValueError(f"Signal not found with id={signal_id}")

    db_path = _get_db_path(mode)
    created_at = utc_now_iso()

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO manual_feedback (
                signal_id,
                ticker,
                created_at,
                feedback_label,
                notes,
                reviewed_by
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                signal.get("ticker"),
                created_at,
                feedback_label,
                notes,
                reviewed_by,
            ),
        )
        conn.commit()

        return int(cursor.lastrowid)


def add_manual_feedback_by_ticker(
    ticker: str,
    feedback_label: str,
    notes: str | None = None,
    reviewed_by: str | None = None,
    run_id: str | None = None,
    mode: str = "demo",
) -> int:
    """
    Insert manual feedback using ticker instead of internal signal id.

    If run_id is None, the latest run is used.

    Parameters
    ----------
    ticker:
        Ticker symbol.
    feedback_label:
        One of the allowed feedback labels.
    notes:
        Optional notes.
    reviewed_by:
        Optional reviewer name.
    run_id:
        Optional run identifier.
    mode:
        Either "demo" or "real".

    Returns
    -------
    int
        Created feedback row id.
    """

    signal = get_signal_by_ticker(ticker=ticker, run_id=run_id, mode=mode)

    if signal is None:
        resolved_run_id = run_id or get_latest_run_id(mode=mode)
        raise ValueError(f"Signal not found for ticker={ticker} and run_id={resolved_run_id}")

    return add_manual_feedback(
        signal_id=int(signal["id"]),
        feedback_label=feedback_label,
        notes=notes,
        reviewed_by=reviewed_by,
        mode=mode,
    )


def load_manual_feedback(
    mode: str = "demo",
    ticker: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Load manual feedback history.

    Parameters
    ----------
    mode:
        Either "demo" or "real".
    ticker:
        Optional ticker filter.
    limit:
        Optional maximum number of rows.

    Returns
    -------
    pandas.DataFrame
        Manual feedback rows.
    """

    db_path = _get_db_path(mode)

    query = """
        SELECT
            mf.id,
            mf.signal_id,
            mf.ticker,
            mf.created_at,
            mf.feedback_label,
            mf.notes,
            mf.reviewed_by,
            s.run_id,
            s.score_priority,
            s.category_final,
            s.reason_to_pass_quant
        FROM manual_feedback mf
        LEFT JOIN signals s
            ON mf.signal_id = s.id
    """

    params: list[Any] = []

    if ticker is not None:
        query += " WHERE mf.ticker = ?"
        params.append(ticker.upper().strip())

    query += " ORDER BY mf.created_at DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_latest_feedback_per_signal(mode: str = "demo") -> pd.DataFrame:
    """
    Return the latest manual feedback row per signal.

    Parameters
    ----------
    mode:
        Either "demo" or "real".

    Returns
    -------
    pandas.DataFrame
        Latest feedback per signal.
    """

    db_path = _get_db_path(mode)

    query = """
        SELECT
            mf.*
        FROM manual_feedback mf
        INNER JOIN (
            SELECT signal_id, MAX(created_at) AS latest_created_at
            FROM manual_feedback
            GROUP BY signal_id
        ) latest
            ON mf.signal_id = latest.signal_id
           AND mf.created_at = latest.latest_created_at
        ORDER BY mf.created_at DESC
    """

    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn)


def load_signals_with_feedback(
    run_id: str | None = None,
    mode: str = "demo",
) -> pd.DataFrame:
    """
    Load signals joined with their latest manual feedback, if any.

    If run_id is None, the latest run is used.

    Parameters
    ----------
    run_id:
        Optional run identifier.
    mode:
        Either "demo" or "real".

    Returns
    -------
    pandas.DataFrame
        Signals with feedback columns.
    """

    signals_df = load_signals(run_id=run_id, mode=mode)

    if signals_df.empty:
        return signals_df

    feedback_df = get_latest_feedback_per_signal(mode=mode)

    if feedback_df.empty:
        signals_df["feedback_label"] = None
        signals_df["feedback_notes"] = None
        signals_df["reviewed_by"] = None
        signals_df["feedback_created_at"] = None
        return signals_df

    feedback_subset = feedback_df[
        [
            "signal_id",
            "feedback_label",
            "notes",
            "reviewed_by",
            "created_at",
        ]
    ].rename(
        columns={
            "signal_id": "id",
            "notes": "feedback_notes",
            "created_at": "feedback_created_at",
        }
    )

    return signals_df.merge(feedback_subset, on="id", how="left")


def summarize_feedback(mode: str = "demo") -> dict[str, Any]:
    """
    Summarize all manual feedback stored in the database.
    """

    feedback_df = load_manual_feedback(mode=mode)

    if feedback_df.empty:
        return {
            "total_feedback_rows": 0,
            "reviewed_tickers": 0,
            "labels": {},
            "latest_feedback": None,
        }

    labels = feedback_df["feedback_label"].value_counts().to_dict()

    return {
        "total_feedback_rows": int(len(feedback_df)),
        "reviewed_tickers": int(feedback_df["ticker"].nunique()),
        "labels": labels,
        "latest_feedback": str(feedback_df.iloc[0]["created_at"]),
    }


def print_feedback_labels() -> None:
    """
    Print available feedback labels.
    """

    print("Available feedback labels:")
    for label in get_valid_feedback_labels():
        print(f"- {label}")


if __name__ == "__main__":
    mode = "demo"
    latest_run_id = get_latest_run_id(mode=mode)

    if latest_run_id is None:
        raise SystemExit("No runs found. Execute python -m src.pipeline first.")

    print(f"Latest run: {latest_run_id}")
    print_feedback_labels()

    print("\nTop 5 current signals:")
    top_df = get_top_signals(run_id=latest_run_id, mode=mode, top_n=5)

    if top_df.empty:
        print("No signals found.")
    else:
        columns_to_show = [
            "id",
            "ticker",
            "score_priority",
            "category_final",
            "reason_to_pass_quant",
        ]
        available_columns = [column for column in columns_to_show if column in top_df.columns]
        print(top_df[available_columns].to_string(index=False))

        first_signal = top_df.iloc[0]
        first_ticker = str(first_signal["ticker"])

        print(f"\nConsole demo: adding sample feedback to {first_ticker}")
        feedback_id = add_manual_feedback_by_ticker(
            ticker=first_ticker,
            feedback_label="needs_more_research",
            notes="Automatic console demo feedback. Replace or delete in real use.",
            reviewed_by="system_demo",
            run_id=latest_run_id,
            mode=mode,
        )
        print(f"Created feedback id: {feedback_id}")

    print("\nFeedback summary:")
    summary = summarize_feedback(mode=mode)
    for key, value in summary.items():
        print(f"- {key}: {value}")

    print("\nLatest feedback rows:")
    feedback_history = load_manual_feedback(mode=mode, limit=10)
    if feedback_history.empty:
        print("No feedback found.")
    else:
        columns_to_show = [
            "id",
            "ticker",
            "feedback_label",
            "reviewed_by",
            "created_at",
            "notes",
        ]
        available_columns = [column for column in columns_to_show if column in feedback_history.columns]
        print(feedback_history[available_columns].to_string(index=False))
