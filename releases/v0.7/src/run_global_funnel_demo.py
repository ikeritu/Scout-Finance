
"""
Scout Finance — Phase 6E clean global funnel demo runner.

Run from project root:

    ./.venv/Scripts/python.exe -m src.run_global_funnel_demo

Purpose:
- Execute the full demo funnel in one command.
- Use the clean enriched Stage 2 flow.
- Do not overwrite data/stages/stage1_passed.csv.
- Do not call OpenAI.
- Do not call external APIs.
- Do not modify app.py.

Clean flow:
1. Stage 0 — validate global universe
2. Stage 1 — investable universe filter
3. Phase 6C — enrich Stage 1 into stage1_passed_enriched.csv
4. Phase 6D — Stage 2 from stage1_passed_enriched.csv
5. Demo enrichment — Stage 2 scoring inputs
6. Stage 3 — opportunity scoring
7. Export Stage 3 candidates bridge
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from src.funnel_paths import SCOUTING_OUTPUTS_DIR, STAGES_DIR, ensure_funnel_directories
from src.global_universe import validate_and_prepare_global_universe
from src.filter_stage1 import run_stage1_filter
from src.prepare_fundamentals_csv import enrich_stage1_passed_with_fundamentals
from src.run_stage2_filter_enriched import STAGE1_PASSED_ENRICHED_PATH
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


def _run_fundamentals_enrichment_clean() -> dict[str, Any]:
    """
    Create stage1_passed_enriched.csv without overwriting stage1_passed.csv.
    """

    return enrich_stage1_passed_with_fundamentals(
        overwrite_stage1_passed=False,
        data_source="sample_fundamentals",
    )


def _run_stage2_from_enriched() -> dict[str, Any]:
    """
    Run Stage 2 directly from stage1_passed_enriched.csv.
    """

    return run_stage2_filter(input_path=STAGE1_PASSED_ENRICHED_PATH)


def run_global_funnel_demo() -> dict[str, Any]:
    """
    Run full demo funnel using the clean enriched Stage 2 flow.
    """

    ensure_funnel_directories()

    run_started_at = _utc_now_iso()
    run_start = time.perf_counter()

    steps: list[dict[str, Any]] = []

    pipeline = [
        ("Stage 0 — Validate global universe", validate_and_prepare_global_universe),
        ("Stage 1 — Investable universe filter", run_stage1_filter),
        ("Phase 6C — Enrich Stage 1 fundamentals cleanly", _run_fundamentals_enrichment_clean),
        ("Phase 6D — Stage 2 from enriched Stage 1", _run_stage2_from_enriched),
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
    stage2_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Phase 6D")), {})
    stage3_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Stage 3")), {})
    enrichment_details = next((s.get("details", {}) for s in steps if s["name"].startswith("Phase 6C")), {})

    summary = {
        "phase": "6E",
        "runner": "run_global_funnel_demo",
        "status": overall_status,
        "started_at": run_started_at,
        "finished_at": run_finished_at,
        "elapsed_seconds": round(elapsed, 3),
        "clean_enriched_flow": True,
        "stage1_passed_overwritten": False,
        "stage2_input": str(STAGE1_PASSED_ENRICHED_PATH),
        "openai_called": False,
        "api_called": False,
        "app_modified": False,
        "steps": steps,
        "funnel_counts": {
            "stage0_input_companies": stage0_details.get("input_companies"),
            "stage1_passed": stage1_details.get("passed_companies"),
            "stage1_watchlist": stage1_details.get("watchlist_companies"),
            "stage1_rejected": stage1_details.get("rejected_companies"),
            "fundamentals_matched_companies": enrichment_details.get("matched_companies_with_revenue"),
            "stage2_passed": stage2_details.get("passed_companies"),
            "stage2_watchlist": stage2_details.get("watchlist_companies"),
            "stage2_rejected": stage2_details.get("rejected_companies"),
            "stage3_passed": stage3_details.get("passed_companies"),
            "stage3_watchlist": stage3_details.get("watchlist_companies"),
            "stage3_rejected": stage3_details.get("rejected_companies"),
        },
        "output_files": {
            "summary": str(GLOBAL_FUNNEL_RUN_SUMMARY_PATH),
            "stage1_passed": str(STAGES_DIR / "stage1_passed.csv"),
            "stage1_passed_enriched": str(STAGES_DIR / "stage1_passed_enriched.csv"),
            "stage2_passed": str(STAGES_DIR / "stage2_passed.csv"),
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
    print("Scout Finance — Phase 6E clean global funnel demo runner")
    print("=" * 68)
    print(f"Status: {summary.get('status')}")
    print(f"Elapsed seconds: {summary.get('elapsed_seconds')}")
    print(f"Clean enriched flow: {summary.get('clean_enriched_flow')}")
    print(f"Stage1 passed overwritten: {summary.get('stage1_passed_overwritten')}")
    print(f"Stage 2 input: {summary.get('stage2_input')}")
    print(f"OpenAI called: {summary.get('openai_called')}")
    print(f"API called: {summary.get('api_called')}")
    print(f"App modified: {summary.get('app_modified')}")

    print()
    print("Steps")
    print("-" * 68)

    for step in summary.get("steps", []):
        print(f"{step.get('status'):7} {step.get('name')} ({step.get('elapsed_seconds')}s)")

        if step.get("error"):
            print(f"        Error: {step.get('error')}")

    print()
    print("Funnel counts")
    print("-" * 68)

    counts = summary.get("funnel_counts", {})

    print(f"Stage 0 input:               {counts.get('stage0_input_companies')}")
    print(
        "Stage 1:                     "
        f"passed={counts.get('stage1_passed')} | "
        f"watchlist={counts.get('stage1_watchlist')} | "
        f"rejected={counts.get('stage1_rejected')}"
    )
    print(f"Fundamentals matched:         {counts.get('fundamentals_matched_companies')}")
    print(
        "Stage 2 enriched:            "
        f"passed={counts.get('stage2_passed')} | "
        f"watchlist={counts.get('stage2_watchlist')} | "
        f"rejected={counts.get('stage2_rejected')}"
    )
    print(
        "Stage 3:                     "
        f"passed={counts.get('stage3_passed')} | "
        f"watchlist={counts.get('stage3_watchlist')} | "
        f"rejected={counts.get('stage3_rejected')}"
    )

    print()
    print("Output files")
    print("-" * 68)

    for label, path in summary.get("output_files", {}).items():
        print(f"- {label}: {path}")


def main() -> int:
    summary = run_global_funnel_demo()
    print_global_funnel_demo_summary(summary)
    return 0 if summary.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
