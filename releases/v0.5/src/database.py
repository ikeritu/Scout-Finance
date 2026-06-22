"""SQLite database utilities for the equity research MVP.

This module creates the minimum schema required by the first structural phase.
It intentionally avoids Streamlit, yfinance, OpenAI calls and financial logic.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import DEMO_DB_PATH, PROMPT_VERSION, SCORING_VERSION


def utc_now_iso() -> str:
    """Return the current UTC datetime as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Create and return a SQLite connection with foreign keys enabled."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | Path) -> None:
    """Initialize the SQLite database and create all MVP tables."""
    with get_connection(db_path) as conn:
        create_tables(conn)


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables required for the first MVP schema."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            mode TEXT NOT NULL,
            universe_size INTEGER,
            valid_companies INTEGER DEFAULT 0,
            excluded_companies INTEGER DEFAULT 0,
            scored_companies INTEGER DEFAULT 0,
            openai_analyzed_companies INTEGER DEFAULT 0,
            scoring_version TEXT,
            prompt_version TEXT,
            status TEXT DEFAULT 'created',
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,
            company_name TEXT,
            exchange TEXT,
            country TEXT,
            currency TEXT,
            sector TEXT,
            industry TEXT,
            asset_type TEXT,
            is_active INTEGER DEFAULT 1,
            source TEXT,
            last_updated TEXT
        );

        CREATE TABLE IF NOT EXISTS market_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            ticker TEXT NOT NULL,
            company_name TEXT,
            sector TEXT,
            industry TEXT,
            exchange TEXT,
            currency TEXT,
            price REAL,
            previous_close REAL,
            volume INTEGER,
            avg_volume_50d INTEGER,
            relative_volume REAL,
            change_1d REAL,
            change_5d REAL,
            change_20d REAL,
            ma20 REAL,
            ma50 REAL,
            above_ma20 INTEGER,
            above_ma50 INTEGER,
            high_52w REAL,
            low_52w REAL,
            distance_to_52w_high REAL,
            distance_to_52w_low REAL,
            market_cap REAL,
            data_source TEXT,
            data_quality_score REAL,
            data_quality_label TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(run_id)
        );

        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            ticker TEXT NOT NULL,
            price_at_signal REAL,
            score_catalyst REAL,
            score_volume REAL,
            score_momentum REAL,
            score_liquidity REAL,
            score_context REAL,
            score_fundamental REAL,
            score_asymmetry REAL,
            score_raw REAL,
            penalty_total REAL,
            score_adjusted REAL,
            score_risk REAL,
            score_confidence REAL,
            score_dilution REAL,
            score_priority REAL,
            category_final TEXT,
            opportunity_phase TEXT,
            veto_applied INTEGER DEFAULT 0,
            veto_reason TEXT,
            reason_to_pass_quant TEXT,
            missing_key_data_quant TEXT,
            scoring_version TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(run_id)
        );

        CREATE TABLE IF NOT EXISTS openai_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            run_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            ticker TEXT NOT NULL,
            model TEXT,
            prompt_version TEXT,
            schema_version TEXT,
            summary_thesis TEXT,
            opportunity_type TEXT,
            opportunity_phase TEXT,
            suggested_category TEXT,
            confidence_level TEXT,
            hype_risk TEXT,
            source_quality TEXT,
            reason_to_pass TEXT,
            missing_key_data TEXT,
            event_to_confirm TEXT,
            source_to_verify TEXT,
            verifiable_facts_json TEXT,
            reasonable_inferences_json TEXT,
            speculative_elements_json TEXT,
            contradictions_json TEXT,
            checklist_json TEXT,
            why_it_could_work TEXT,
            why_it_could_fail TEXT,
            discrepancy_with_python TEXT,
            raw_response_json TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            estimated_cost REAL,
            cache_hit INTEGER DEFAULT 0,
            FOREIGN KEY (signal_id) REFERENCES signals(id),
            FOREIGN KEY (run_id) REFERENCES runs(run_id)
        );

        CREATE TABLE IF NOT EXISTS validation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            ticker TEXT NOT NULL,
            created_at TEXT NOT NULL,
            validation_date TEXT,
            price_at_signal REAL,
            price_1d REAL,
            price_3d REAL,
            price_7d REAL,
            price_30d REAL,
            return_1d REAL,
            return_3d REAL,
            return_7d REAL,
            return_30d REAL,
            max_upside_30d REAL,
            max_drawdown_30d REAL,
            validation_status TEXT,
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        );

        CREATE TABLE IF NOT EXISTS manual_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            ticker TEXT NOT NULL,
            created_at TEXT NOT NULL,
            feedback_label TEXT,
            notes TEXT,
            reviewed_by TEXT,
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        );

        CREATE TABLE IF NOT EXISTS cost_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            signal_id INTEGER,
            ticker TEXT,
            created_at TEXT NOT NULL,
            model TEXT,
            purpose TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            estimated_cost REAL,
            cache_hit INTEGER DEFAULT 0,
            prompt_version TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(run_id),
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        );

        CREATE TABLE IF NOT EXISTS data_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            created_at TEXT NOT NULL,
            ticker TEXT,
            source TEXT,
            error_type TEXT,
            error_message TEXT,
            severity TEXT DEFAULT 'medium',
            FOREIGN KEY (run_id) REFERENCES runs(run_id)
        );
        """
    )
    conn.commit()


def create_run(
    conn: sqlite3.Connection,
    mode: str,
    universe_size: Optional[int] = None,
) -> str:
    """Create a new run record and return its generated run_id."""
    run_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO runs (
            run_id,
            created_at,
            mode,
            universe_size,
            scoring_version,
            prompt_version,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            utc_now_iso(),
            mode,
            universe_size,
            SCORING_VERSION,
            PROMPT_VERSION,
            "created",
        ),
    )
    conn.commit()
    return run_id


def insert_data_error(
    conn: sqlite3.Connection,
    run_id: str,
    ticker: str,
    source: str,
    error_type: str,
    error_message: str,
    severity: str = "medium",
) -> None:
    """Insert a data ingestion or quality error into data_errors."""
    conn.execute(
        """
        INSERT INTO data_errors (
            run_id,
            created_at,
            ticker,
            source,
            error_type,
            error_message,
            severity
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            utc_now_iso(),
            ticker,
            source,
            error_type,
            error_message,
            severity,
        ),
    )
    conn.commit()


if __name__ == "__main__":
    init_db(DEMO_DB_PATH)
    print(f"Database initialized at: {DEMO_DB_PATH}")
