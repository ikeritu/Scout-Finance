"""
Pipeline module.

This module connects the existing MVP blocks and persists their output in SQLite.

Current scope:
- Load universe.
- Build market snapshot.
- Apply data quality checks.
- Apply basic filters.
- Apply quantitative scoring.
- Save companies, market snapshots, signals and data errors into SQLite.
- Update run status and counters.

Not included in this phase:
- Streamlit UI.
- OpenAI analysis.
- Exporting files.
- Validation after signal date.
- Advanced cache.
- Trading recommendations.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from config import get_paths
from src.data_quality import (
    apply_data_quality,
    build_data_error_rows,
    summarize_data_quality,
)
from src.database import (
    create_run,
    get_connection,
    init_db,
    insert_data_error,
    utc_now_iso,
)
from src.filters import apply_basic_filters, summarize_filters
from src.market_data import build_market_snapshot, summarize_market_snapshot
from src.scoring import apply_scoring, summarize_scoring
from src.universe import validate_and_load_universe


COMPANY_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "country",
    "currency",
    "sector",
    "industry",
    "asset_type",
    "is_active",
    "source",
    "last_updated",
]


MARKET_SNAPSHOT_COLUMNS = [
    "run_id",
    "created_at",
    "ticker",
    "company_name",
    "sector",
    "industry",
    "exchange",
    "currency",
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
    "above_ma20",
    "above_ma50",
    "high_52w",
    "low_52w",
    "distance_to_52w_high",
    "distance_to_52w_low",
    "market_cap",
    "data_source",
    "data_quality_score",
    "data_quality_label",
]


SIGNAL_COLUMNS = [
    "run_id",
    "created_at",
    "ticker",
    "price_at_signal",
    "score_catalyst",
    "score_volume",
    "score_momentum",
    "score_liquidity",
    "score_context",
    "score_fundamental",
    "score_asymmetry",
    "score_raw",
    "penalty_total",
    "score_adjusted",
    "score_risk",
    "score_confidence",
    "score_dilution",
    "score_priority",
    "category_final",
    "opportunity_phase",
    "veto_applied",
    "veto_reason",
    "reason_to_pass_quant",
    "missing_key_data_quant",
    "scoring_version",
]


def _to_sql_value(value: Any) -> Any:
    """
    Convert pandas/numpy values to SQLite-safe values.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    if isinstance(value, bool):
        return int(value)

    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            return value

    return value


def _row_value(row: pd.Series, column: str, default: Any = None) -> Any:
    """
    Safely get a SQLite-compatible value from a dataframe row.
    """

    if column not in row.index:
        return default

    return _to_sql_value(row[column])


def upsert_companies(conn: sqlite3.Connection, universe_df: pd.DataFrame) -> int:
    """
    Insert or update companies from the clean universe dataframe.

    Parameters
    ----------
    conn:
        SQLite connection.
    universe_df:
        Clean universe dataframe.

    Returns
    -------
    int
        Number of processed company rows.
    """

    sql = """
        INSERT INTO companies (
            ticker,
            company_name,
            exchange,
            country,
            currency,
            sector,
            industry,
            asset_type,
            is_active,
            source,
            last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            company_name = excluded.company_name,
            exchange = excluded.exchange,
            country = excluded.country,
            currency = excluded.currency,
            sector = excluded.sector,
            industry = excluded.industry,
            asset_type = excluded.asset_type,
            is_active = excluded.is_active,
            source = excluded.source,
            last_updated = excluded.last_updated
    """

    rows = []

    for _, row in universe_df.iterrows():
        rows.append(
            tuple(
                int(_row_value(row, column)) if column == "is_active" else _row_value(row, column)
                for column in COMPANY_COLUMNS
            )
        )

    conn.executemany(sql, rows)
    return len(rows)


def insert_market_snapshots(
    conn: sqlite3.Connection,
    run_id: str,
    snapshot_df: pd.DataFrame,
) -> int:
    """
    Insert market snapshot rows into SQLite.

    Parameters
    ----------
    conn:
        SQLite connection.
    run_id:
        Current run identifier.
    snapshot_df:
        Dataframe after market data and data quality.

    Returns
    -------
    int
        Number of inserted snapshot rows.
    """

    created_at = utc_now_iso()

    placeholders = ", ".join(["?"] * len(MARKET_SNAPSHOT_COLUMNS))
    columns_sql = ", ".join(MARKET_SNAPSHOT_COLUMNS)

    sql = f"""
        INSERT INTO market_snapshots ({columns_sql})
        VALUES ({placeholders})
    """

    rows = []

    for _, row in snapshot_df.iterrows():
        rows.append(
            tuple(
                _snapshot_column_value(
                    row=row,
                    column=column,
                    run_id=run_id,
                    created_at=created_at,
                )
                for column in MARKET_SNAPSHOT_COLUMNS
            )
        )

    conn.executemany(sql, rows)
    return len(rows)


def _snapshot_column_value(
    row: pd.Series,
    column: str,
    run_id: str,
    created_at: str,
) -> Any:
    """
    Map dataframe columns to market_snapshots table columns.
    """

    if column == "run_id":
        return run_id

    if column == "created_at":
        return created_at

    if column == "above_ma20":
        return int(bool(_row_value(row, column, False)))

    if column == "above_ma50":
        return int(bool(_row_value(row, column, False)))

    if column == "data_source":
        return _row_value(row, column, "yfinance")

    return _row_value(row, column)


def insert_signals(
    conn: sqlite3.Connection,
    run_id: str,
    scored_df: pd.DataFrame,
    only_passed: bool = True,
) -> int:
    """
    Insert quantitative scoring rows into the signals table.

    Parameters
    ----------
    conn:
        SQLite connection.
    run_id:
        Current run identifier.
    scored_df:
        Dataframe after apply_scoring().
    only_passed:
        If True, only companies that passed basic filters are inserted.

    Returns
    -------
    int
        Number of inserted signal rows.
    """

    if only_passed and "passes_basic_filters" in scored_df.columns:
        source_df = scored_df[scored_df["passes_basic_filters"] == True].copy()  # noqa: E712
    else:
        source_df = scored_df.copy()

    created_at = utc_now_iso()

    placeholders = ", ".join(["?"] * len(SIGNAL_COLUMNS))
    columns_sql = ", ".join(SIGNAL_COLUMNS)

    sql = f"""
        INSERT INTO signals ({columns_sql})
        VALUES ({placeholders})
    """

    rows = []

    for _, row in source_df.iterrows():
        rows.append(
            tuple(
                _signal_column_value(
                    row=row,
                    column=column,
                    run_id=run_id,
                    created_at=created_at,
                )
                for column in SIGNAL_COLUMNS
            )
        )

    conn.executemany(sql, rows)
    return len(rows)


def _signal_column_value(
    row: pd.Series,
    column: str,
    run_id: str,
    created_at: str,
) -> Any:
    """
    Map dataframe columns to signals table columns.
    """

    if column == "run_id":
        return run_id

    if column == "created_at":
        return created_at

    if column == "price_at_signal":
        return _row_value(row, "price")

    if column == "veto_applied":
        return int(bool(_row_value(row, column, False)))

    return _row_value(row, column)


def insert_quality_errors(
    conn: sqlite3.Connection,
    run_id: str,
    quality_df: pd.DataFrame,
) -> int:
    """
    Insert detected data quality issues into the data_errors table.

    Parameters
    ----------
    conn:
        SQLite connection.
    run_id:
        Current run identifier.
    quality_df:
        Dataframe after apply_data_quality().

    Returns
    -------
    int
        Number of inserted error rows.
    """

    error_rows = build_data_error_rows(
        quality_df,
        run_id=run_id,
        source="data_quality",
    )

    for error in error_rows:
        insert_data_error(
            conn=conn,
            run_id=run_id,
            ticker=error.get("ticker"),
            source=error.get("source", "data_quality"),
            error_type=error.get("error_type"),
            error_message=error.get("error_message"),
            severity=error.get("severity", "medium"),
        )

    return len(error_rows)


def update_run_summary(
    conn: sqlite3.Connection,
    run_id: str,
    universe_size: int,
    valid_companies: int,
    excluded_companies: int,
    scored_companies: int,
    status: str = "completed",
    notes: str | None = None,
) -> None:
    """
    Update the runs table with final counters and status.
    """

    conn.execute(
        """
        UPDATE runs
        SET
            universe_size = ?,
            valid_companies = ?,
            excluded_companies = ?,
            scored_companies = ?,
            status = ?,
            notes = ?
        WHERE run_id = ?
        """,
        (
            universe_size,
            valid_companies,
            excluded_companies,
            scored_companies,
            status,
            notes,
            run_id,
        ),
    )


def summarize_persisted_run(
    conn: sqlite3.Connection,
    run_id: str,
) -> dict[str, Any]:
    """
    Return row counts persisted for one run.
    """

    def count_rows(table: str) -> int:
        result = conn.execute(
            f"SELECT COUNT(*) AS total FROM {table} WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        return int(result["total"])

    run = conn.execute(
        "SELECT * FROM runs WHERE run_id = ?",
        (run_id,),
    ).fetchone()

    return {
        "run_id": run_id,
        "status": run["status"] if run else None,
        "market_snapshots": count_rows("market_snapshots"),
        "signals": count_rows("signals"),
        "data_errors": count_rows("data_errors"),
    }


def run_quant_pipeline(
    mode: str = "demo",
    period: str = "1y",
    only_passed_signals: bool = True,
) -> dict[str, Any]:
    """
    Execute the current quantitative pipeline and persist results into SQLite.

    Parameters
    ----------
    mode:
        Either "demo" or "real".
    period:
        yfinance history period used by market_data.py.
    only_passed_signals:
        If True, only companies passing basic filters are inserted into signals.

    Returns
    -------
    dict
        Summary of the run and persisted rows.
    """

    paths = get_paths(mode)
    db_path = Path(paths["db_path"])

    init_db(db_path)

    with get_connection(db_path) as conn:
        run_id = create_run(conn, mode=mode, universe_size=None)

        try:
            universe_df, universe_summary = validate_and_load_universe(mode=mode)

            snapshot_df = build_market_snapshot(universe_df, period=period)
            market_summary = summarize_market_snapshot(snapshot_df)

            quality_df = apply_data_quality(snapshot_df)
            quality_summary = summarize_data_quality(quality_df)

            filtered_df = apply_basic_filters(quality_df)
            filter_summary = summarize_filters(filtered_df)

            scored_df = apply_scoring(filtered_df)
            scoring_summary = summarize_scoring(scored_df)

            companies_count = upsert_companies(conn, universe_df)
            snapshots_count = insert_market_snapshots(conn, run_id, quality_df)
            signals_count = insert_signals(
                conn,
                run_id,
                scored_df,
                only_passed=only_passed_signals,
            )
            data_errors_count = insert_quality_errors(conn, run_id, quality_df)

            update_run_summary(
                conn=conn,
                run_id=run_id,
                universe_size=int(universe_summary["total_companies"]),
                valid_companies=int(filter_summary["passed_companies"]),
                excluded_companies=int(filter_summary["excluded_companies"]),
                scored_companies=int(signals_count),
                status="completed",
                notes="Quantitative demo pipeline completed without OpenAI.",
            )

            conn.commit()

            persisted_summary = summarize_persisted_run(conn, run_id)

            return {
                "run_id": run_id,
                "db_path": str(db_path),
                "universe_summary": universe_summary,
                "market_summary": market_summary,
                "quality_summary": quality_summary,
                "filter_summary": filter_summary,
                "scoring_summary": scoring_summary,
                "persisted_summary": persisted_summary,
                "companies_upserted": companies_count,
                "market_snapshots_inserted": snapshots_count,
                "signals_inserted": signals_count,
                "data_errors_inserted": data_errors_count,
            }

        except Exception as exc:
            update_run_summary(
                conn=conn,
                run_id=run_id,
                universe_size=0,
                valid_companies=0,
                excluded_companies=0,
                scored_companies=0,
                status="failed",
                notes=str(exc),
            )
            conn.commit()
            raise


if __name__ == "__main__":
    summary = run_quant_pipeline(mode="demo", period="1y")

    print("Pipeline completed.")
    print(f"Run ID: {summary['run_id']}")
    print(f"Database: {summary['db_path']}")

    print("\nUniverse summary:")
    for key, value in summary["universe_summary"].items():
        print(f"- {key}: {value}")

    print("\nMarket summary:")
    for key, value in summary["market_summary"].items():
        print(f"- {key}: {value}")

    print("\nQuality summary:")
    for key, value in summary["quality_summary"].items():
        print(f"- {key}: {value}")

    print("\nFilter summary:")
    for key, value in summary["filter_summary"].items():
        print(f"- {key}: {value}")

    print("\nScoring summary:")
    for key, value in summary["scoring_summary"].items():
        print(f"- {key}: {value}")

    print("\nPersisted summary:")
    for key, value in summary["persisted_summary"].items():
        print(f"- {key}: {value}")
