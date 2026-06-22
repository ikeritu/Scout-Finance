"""
Scout Finance — Phase 5I global funnel demo runner.

Run from project root:

    ./.venv/Scripts/python.exe -m src.run_global_funnel_demo

Purpose:
- Execute the full demo funnel in one command.
- Does not call OpenAI.
- Does not modify app.py.
- Does not touch the existing Phase 2 pipeline.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from src.funnel_paths import SCOUTING_OUTPUTS_DIR, ensure_funnel_directories
from src.global_universe import validate_and_prepare_global_universe
from src.filter_stage1 import run_stage1_filter
from src.enrich_stage1_demo_financials import main as enrich_stage1_demo_financials
from src.filter_stage2 import run_stage2_filter
from src.enrich_stage2_demo_scoring_inputs import main as enrich_stage2_demo_scoring_inputs
from src.filter_stage3 import run_stage3_scoring
from src.scouting_candidates import export_candidates_for_existing_ranking


GLOBAL_FUNNEL_RUN_SUMMARY_PATH = SCOUTING_OUTPUTS_DIR / "global_funnel_run_summary.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _step_result(
    *,
    name: str,
    status: str,
    started_at: str,
    finished_at: str,
    elapsed_seconds: float,
    details: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "details": details or {},
        "error": error,
    }


def _run_step(name: str, func) -> dict[str, Any]:
    started_at = _utc_now_iso()
    start = time.perf_counter()

    try:
        result = func()
        elapsed = time.perf_counter() - start
        finished_at = _utc_now_iso()

        if isinstance(result, dict):
            details = result
        else:
            details = {"result": str(result)}

        return _step_result(
            name=name,
            status="OK",
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed,
            details=details,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        finished_at = _utc_now_iso()

        return _step_result(
            name=name,
            status="FAILED",
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed,
            error=str(exc),
        )


def run_global_funnel_demo() -> dict[str, Any]:
    """
    Run the full demo funnel in one command.

    It stops if a critical step fails.
    """

    ensure_funnel_directories()

    run_started_at = _utc_now_iso()
    run_start = time.perf_counter()

    steps: list[dict[str, Any]] = []

    pipeline = [
        ("Stage 0 — Validate global universe", validate_and_prepare_global_universe),
        ("Stage 1 — Investable universe filter", run_stage1_filter),
        ("Demo enrichment — Stage 1 financials", enrich_stage1_demo_financials),
        ("Stage 2 — Financial sanity check", run_stage2_filter),
        ("Demo enrichment — Stage 2 scoring inputs", enrich_stage2_demo_scoring_inputs),
        ("Stage 3 — Opportunity scoring", run_stage3_scoring),
        ("Export — Stage 3 candidates bridge", export_candidates_for_existing_ranking),
    ]

    overall_status = "OK"

    for name, func in pipeline:
        step = _run_step(name, func)
        steps.append(step)

        if step["status"] != "OK":
            overall_status = "FAILED"
            break

    run_finished_at = _utc_now_iso()
    elapsed = time.perf_counter() - run_start

    stage0_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Stage 0")), {})
    stage1_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Stage 1")), {})
    stage2_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Stage 2")), {})
    stage3_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Stage 3")), {})

    summary = {
        "phase": "5I",
        "runner": "run_global_funnel_demo",
        "status": overall_status,
        "started_at": run_started_at,
        "finished_at": run_finished_at,
        "elapsed_seconds": round(elapsed, 3),
        "openai_called": False,
        "app_modified": False,
        "steps": steps,
        "funnel_counts": {
            "stage0_input_companies": stage0_details.get("input_companies"),
            "stage1_passed": stage1_details.get("passed_companies"),
            "stage1_watchlist": stage1_details.get("watchlist_companies"),
            "stage1_rejected": stage1_details.get("rejected_companies"),
            "stage2_passed": stage2_details.get("passed_companies"),
            "stage2_watchlist": stage2_details.get("watchlist_companies"),
            "stage2_rejected": stage2_details.get("rejected_companies"),
            "stage3_passed": stage3_details.get("passed_companies"),
            "stage3_watchlist": stage3_details.get("watchlist_companies"),
            "stage3_rejected": stage3_details.get("rejected_companies"),
        },
        "output_files": {
            "summary": str(GLOBAL_FUNNEL_RUN_SUMMARY_PATH),
            "top_100_candidates": str(SCOUTING_OUTPUTS_DIR / "top_100_candidates.csv"),
            "stage3_candidates_for_ranking": str(SCOUTING_OUTPUTS_DIR / "stage3_candidates_for_ranking.csv"),
        },
    }

    GLOBAL_FUNNEL_RUN_SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return summary


def print_global_funnel_demo_summary(summary: dict[str, Any]) -> None:
    print("Scout Finance — Phase 5I global funnel demo runner")
    print("=" * 64)
    print(f"Status: {summary.get('status')}")
    print(f"Elapsed seconds: {summary.get('elapsed_seconds')}")
    print(f"OpenAI called: {summary.get('openai_called')}")
    print(f"App modified: {summary.get('app_modified')}")

    print()
    print("Steps")
    print("-" * 64)

    for step in summary.get("steps", []):
        print(f"{step.get('status'):7} {step.get('name')} ({step.get('elapsed_seconds')}s)")

        if step.get("error"):
            print(f"        Error: {step.get('error')}")

    print()
    print("Funnel counts")
    print("-" * 64)

    counts = summary.get("funnel_counts", {})

    print(f"Stage 0 input:      {counts.get('stage0_input_companies')}")
    print(
        "Stage 1:            "
        f"passed={counts.get('stage1_passed')} | "
        f"watchlist={counts.get('stage1_watchlist')} | "
        f"rejected={counts.get('stage1_rejected')}"
    )
    print(
        "Stage 2:            "
        f"passed={counts.get('stage2_passed')} | "
        f"watchlist={counts.get('stage2_watchlist')} | "
        f"rejected={counts.get('stage2_rejected')}"
    )
    print(
        "Stage 3:            "
        f"passed={counts.get('stage3_passed')} | "
        f"watchlist={counts.get('stage3_watchlist')} | "
        f"rejected={counts.get('stage3_rejected')}"
    )

    print()
    print("Output files")
    print("-" * 64)

    for label, path in summary.get("output_files", {}).items():
        print(f"- {label}: {path}")


def main() -> int:
    summary = run_global_funnel_demo()
    print_global_funnel_demo_summary(summary)

    return 0 if summary.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
