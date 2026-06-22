
"""
Scout Finance — Phase 7A real universe pilot runner.

Run from project root:
    ./.venv/Scripts/python.exe -m src.run_real_universe_pilot --input data/raw/universe_source_real.csv --limit 500 --source real_csv_pilot
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.funnel_paths import SCOUTING_OUTPUTS_DIR, ensure_funnel_directories
from src.prepare_real_universe_csv import normalize_real_universe_csv
from src.global_universe import validate_and_prepare_global_universe
from src.filter_stage1 import run_stage1_filter
from src.fundamental_coverage_report import build_fundamental_coverage_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REAL_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_real.csv"
PILOT_INPUT = PROJECT_ROOT / "data" / "raw" / "universe_source_pilot.csv"
PILOT_SUMMARY = SCOUTING_OUTPUTS_DIR / "real_universe_pilot_summary.json"
PILOT_SAMPLE_EXPORT = SCOUTING_OUTPUTS_DIR / "real_universe_pilot_input_sample.csv"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_limited_input(input_path: Path, limit: int | None) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {input_path}. "
            "Place a real CSV in data/raw/universe_source_real.csv or pass --input."
        )

    df = pd.read_csv(input_path)

    if df.empty:
        raise ValueError(f"Input CSV is empty: {input_path}")

    if limit is not None and limit > 0:
        df = df.head(limit).copy()

    return df


def _safe_step(name: str, func) -> dict[str, Any]:
    started_at = _utc_now_iso()
    start = time.perf_counter()

    try:
        result = func()
        elapsed = time.perf_counter() - start
        return {
            "name": name,
            "status": "OK",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "elapsed_seconds": round(elapsed, 3),
            "details": result if isinstance(result, dict) else {"result": str(result)},
            "error": None,
        }
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return {
            "name": name,
            "status": "FAILED",
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "elapsed_seconds": round(elapsed, 3),
            "details": {},
            "error": str(exc),
        }


def run_real_universe_pilot(
    input_path: Path = DEFAULT_REAL_INPUT,
    limit: int | None = 500,
    source: str = "real_csv_pilot",
    country: str = "USA",
    currency: str = "USD",
) -> dict[str, Any]:
    ensure_funnel_directories()

    started_at = _utc_now_iso()
    start = time.perf_counter()

    raw_df = _load_limited_input(input_path, limit)
    PILOT_INPUT.parent.mkdir(parents=True, exist_ok=True)
    raw_df.to_csv(PILOT_INPUT, index=False, encoding="utf-8-sig")
    raw_df.head(50).to_csv(PILOT_SAMPLE_EXPORT, index=False, encoding="utf-8-sig")

    steps: list[dict[str, Any]] = []

    steps.append(
        _safe_step(
            "Phase 6A — Normalize pilot CSV",
            lambda: {
                "rows_written": int(len(normalize_real_universe_csv(
                    input_path=PILOT_INPUT,
                    data_source=source,
                    default_country=country,
                    default_currency=currency,
                ))),
                "input_path": str(PILOT_INPUT),
            },
        )
    )

    if steps[-1]["status"] == "OK":
        steps.append(_safe_step("Stage 0 — Validate normalized global universe", validate_and_prepare_global_universe))

    if steps[-1]["status"] == "OK":
        steps.append(_safe_step("Stage 1 — Investable universe filter", run_stage1_filter))

    if steps[-1]["status"] == "OK":
        steps.append(_safe_step("Phase 6B — Fundamental coverage report", build_fundamental_coverage_report))

    status = "OK" if all(step["status"] == "OK" for step in steps) else "FAILED"

    stage0_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Stage 0")), {})
    stage1_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Stage 1")), {})
    coverage_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Phase 6B")), {})

    summary = {
        "phase": "7A",
        "runner": "run_real_universe_pilot",
        "status": status,
        "started_at": started_at,
        "finished_at": _utc_now_iso(),
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "source": source,
        "input_path": str(input_path),
        "pilot_input_path": str(PILOT_INPUT),
        "limit": limit,
        "raw_rows_loaded": int(len(raw_df)),
        "stage2_executed": False,
        "openai_called": False,
        "api_called": False,
        "app_modified": False,
        "release_v0_6_modified": False,
        "steps": steps,
        "counts": {
            "stage0_input_companies": stage0_details.get("input_companies"),
            "stage1_passed": stage1_details.get("passed_companies"),
            "stage1_watchlist": stage1_details.get("watchlist_companies"),
            "stage1_rejected": stage1_details.get("rejected_companies"),
            "fundamental_coverage_input_companies": coverage_details.get("input_companies"),
            "companies_ready_for_stage2": coverage_details.get("companies_ready_for_stage2"),
            "companies_not_ready_for_stage2": coverage_details.get("companies_not_ready_for_stage2"),
            "average_core_stage2_coverage_percent": coverage_details.get("average_core_stage2_coverage_percent"),
        },
        "output_files": {
            "pilot_summary": str(PILOT_SUMMARY),
            "pilot_input": str(PILOT_INPUT),
            "pilot_sample_export": str(PILOT_SAMPLE_EXPORT),
            "global_universe": str(PROJECT_ROOT / "data" / "universe" / "global_universe.csv"),
            "stage1_passed": str(PROJECT_ROOT / "data" / "stages" / "stage1_passed.csv"),
            "stage1_rejection_log": str(PROJECT_ROOT / "data" / "stages" / "stage1_rejection_log.csv"),
            "fundamental_coverage_report": str(SCOUTING_OUTPUTS_DIR / "fundamental_coverage_report.json"),
        },
    }

    PILOT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 7A real universe pilot")
    print("=" * 68)
    print(f"Status: {summary.get('status')}")
    print(f"Input: {summary.get('input_path')}")
    print(f"Pilot rows loaded: {summary.get('raw_rows_loaded')}")
    print(f"Limit: {summary.get('limit')}")
    print(f"OpenAI called: {summary.get('openai_called')}")
    print(f"API called: {summary.get('api_called')}")
    print(f"App modified: {summary.get('app_modified')}")
    print(f"Release v0.6 modified: {summary.get('release_v0_6_modified')}")

    print()
    print("Steps")
    print("-" * 68)
    for step in summary.get("steps", []):
        print(f"{step.get('status'):7} {step.get('name')} ({step.get('elapsed_seconds')}s)")
        if step.get("error"):
            print(f"        Error: {step.get('error')}")

    counts = summary.get("counts", {})
    print()
    print("Counts")
    print("-" * 68)
    print(f"Stage 0 input companies: {counts.get('stage0_input_companies')}")
    print("Stage 1 passed/watchlist/rejected: "
          f"{counts.get('stage1_passed')} / {counts.get('stage1_watchlist')} / {counts.get('stage1_rejected')}")
    print(f"Companies ready for Stage 2: {counts.get('companies_ready_for_stage2')}")
    print(f"Companies not ready for Stage 2: {counts.get('companies_not_ready_for_stage2')}")
    print(f"Average core Stage 2 coverage: {counts.get('average_core_stage2_coverage_percent')}%")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_REAL_INPUT))
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--no-limit", action="store_true")
    parser.add_argument("--source", default="real_csv_pilot")
    parser.add_argument("--country", default="USA")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()

    limit = None if args.no_limit else args.limit
    summary = run_real_universe_pilot(
        input_path=Path(args.input),
        limit=limit,
        source=args.source,
        country=args.country,
        currency=args.currency,
    )
    print_summary(summary)
    return 0 if summary.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
