
from __future__ import annotations

import ast
import json
import py_compile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
OUT_DIR = ROOT / "outputs" / "scouting"

SUMMARY_PATH = OUT_DIR / "phase7e_v07_release_checkpoint_summary.json"
REPORT_PATH = OUT_DIR / "phase7e_v07_release_checkpoint_report.md"
EVIDENCE_PATH = OUT_DIR / "phase7e_v07_release_checkpoint_evidence.csv"

REQUIRED_FILES = {
    "stage1_balanced_closure": OUT_DIR / "stage1_balanced_official_closure_summary.json",
    "stage2_yfinance_policy": OUT_DIR / "stage2_yfinance_policy_implementation_summary.json",
    "phase7c4_pipeline_closure": OUT_DIR / "phase7c4_pipeline_revalidation_summary.json",
    "phase7d_dashboard": OUT_DIR / "phase7d_dashboard_revalidated_funnel_summary.json",
    "phase7d1_hotfix": OUT_DIR / "phase7d1_dashboard_hotfix_summary.json",
    "phase7d2_count_hotfix": OUT_DIR / "phase7d2_institutional_count_hotfix_summary.json",
    "phase7d3b_fundamental_exact_fix": OUT_DIR / "phase7d3b_fundamental_coverage_exact_fix_summary.json",
    "active_pipeline_policy_status": OUT_DIR / "active_pipeline_policy_status.json",
    "stage3_summary": OUT_DIR / "stage3_summary.json",
    "stage1_passed": ROOT / "data" / "stages" / "stage1_passed.csv",
    "stage2_passed": ROOT / "data" / "stages" / "stage2_passed.csv",
    "stage3_passed": ROOT / "data" / "stages" / "stage3_passed.csv",
    "top_100_candidates": OUT_DIR / "top_100_candidates.csv",
    "stage3_candidates_for_ranking": OUT_DIR / "stage3_candidates_for_ranking.csv",
    "phase7c4_top_candidates": OUT_DIR / "phase7c4_pipeline_revalidation_top_candidates.csv",
}

APP_REQUIRED_TEXT = [
    "# PHASE 7D REVALIDATED FUNNEL DASHBOARD APPLIED",
    "# PHASE 7D.1 DASHBOARD HOTFIX APPLIED",
    "# PHASE 7D.2 INSTITUTIONAL COUNT HOTFIX APPLIED",
    "# PHASE 7D.3B FUNDAMENTAL COVERAGE EXACT FIX APPLIED",
    "Funnel real revalidado",
    "500 → 182 → 63 → 6",
    "fundamentals_yfinance_enrichment_summary.json",
    'summary["runner_phase"] = "7C.1"',
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def file_info(label: str, path: Path) -> dict:
    exists = path.exists()
    rows = count_csv(path) if exists and path.suffix.lower() == ".csv" else None
    return {
        "label": label,
        "path": str(path),
        "exists": bool(exists),
        "rows": rows,
        "size_bytes": path.stat().st_size if exists else 0,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat() if exists else None,
    }


def compile_app() -> tuple[bool, str]:
    try:
        py_compile.compile(str(APP_PATH), doraise=True)
        ast.parse(APP_PATH.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def render_report(summary: dict) -> str:
    evidence_lines = "\n".join(
        f"- {row['label']}: exists={row['exists']} rows={row.get('rows')} path=`{row['path']}`"
        for row in summary["evidence_files"]
    )
    marker_lines = "\n".join(
        f"- `{marker}`: {present}"
        for marker, present in summary["app_marker_checks"].items()
    )
    return f"""# Scout Finance — Phase 7E v0.7 release checkpoint

Generated at: `{summary["created_at"]}`

## Status

- Checkpoint status: **{summary["status"]}**
- Ready for v0.7 release packaging: **{summary["ready_for_v07_release"]}**
- Recommended next phase: **{summary["recommended_next_phase"]}**

## Current validated funnel

```text
{summary["validated_funnel"]}
```

## Counts

| Item | Count |
|---|---:|
| Stage 1 passed | {summary["counts"]["stage1_passed_rows"]} |
| Stage 2 passed | {summary["counts"]["stage2_passed_rows"]} |
| Stage 3 passed | {summary["counts"]["stage3_passed_rows"]} |
| Top 100 candidates rows | {summary["counts"]["top_100_candidates_rows"]} |
| Candidates for ranking rows | {summary["counts"]["stage3_candidates_for_ranking_rows"]} |

## Dashboard marker checks

{marker_lines}

## Evidence files

{evidence_lines}

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- filters modified: `{summary["filters_modified"]}`
- release modified: `{summary["release_modified"]}`

## Release note draft

```text
v0.7 candidate: real pilot funnel validated and dashboard-integrated.
Pipeline: institutional universe → Stage 1 Balanced → Stage 2 yfinance-aligned → Stage 3 scoring.
Validated funnel: {summary["validated_funnel"]}.
Top candidate: {summary["top_company"].get("ticker", "N/A")} — {summary["top_company"].get("name", "N/A")} — score {summary["top_company"].get("final_stage3_score", "N/A")}.
```
"""


def main() -> int:
    print("Scout Finance — Phase 7E v0.7 release checkpoint")
    print("=" * 88)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    evidence_files = [file_info(label, path) for label, path in REQUIRED_FILES.items()]
    pd.DataFrame(evidence_files).to_csv(EVIDENCE_PATH, index=False, encoding="utf-8-sig")

    app_ok, app_error = compile_app()
    app_text = APP_PATH.read_text(encoding="utf-8", errors="replace") if APP_PATH.exists() else ""
    app_marker_checks = {marker: marker in app_text for marker in APP_REQUIRED_TEXT}

    stage1_rows = count_csv(REQUIRED_FILES["stage1_passed"])
    stage2_rows = count_csv(REQUIRED_FILES["stage2_passed"])
    stage3_rows = count_csv(REQUIRED_FILES["stage3_passed"])
    top100_rows = count_csv(REQUIRED_FILES["top_100_candidates"])
    ranking_rows = count_csv(REQUIRED_FILES["stage3_candidates_for_ranking"])

    phase7c4 = read_json(REQUIRED_FILES["phase7c4_pipeline_closure"])
    stage3_summary = read_json(REQUIRED_FILES["stage3_summary"])
    stage2_impl = read_json(REQUIRED_FILES["stage2_yfinance_policy"])
    d2 = read_json(REQUIRED_FILES["phase7d2_count_hotfix"])
    d3b = read_json(REQUIRED_FILES["phase7d3b_fundamental_exact_fix"])

    validated_funnel = phase7c4.get("funnel", {}).get("path") or "500 → 182 → 63 → 6"

    checks = {
        "app_compiles": app_ok,
        "counts_ok": stage1_rows == 182 and stage2_rows == 63 and stage3_rows == 6 and top100_rows >= 10 and ranking_rows >= 10,
        "markers_ok": all(app_marker_checks.values()),
        "required_files_ok": all(item["exists"] for item in evidence_files),
        "stage2_policy_ok": stage2_impl.get("status") == "OK",
        "dashboard_hotfixes_ok": d2.get("status") == "OK" and d3b.get("status") == "OK",
        "phase7c4_ok": phase7c4.get("status") == "OK",
    }

    ready = all(checks.values())

    summary = {
        "phase": "7E",
        "status": "OK" if ready else "REVIEW",
        "created_at": utc_now(),
        "ready_for_v07_release": ready,
        "recommended_next_phase": "7F — Package release v0.7 candidate" if ready else "7E.1 — Fix checkpoint evidence before release packaging",
        "validated_funnel": validated_funnel,
        "counts": {
            "stage1_passed_rows": stage1_rows,
            "stage2_passed_rows": stage2_rows,
            "stage3_passed_rows": stage3_rows,
            "top_100_candidates_rows": top100_rows,
            "stage3_candidates_for_ranking_rows": ranking_rows,
        },
        "checks": checks,
        "app_compile_error": app_error,
        "app_marker_checks": app_marker_checks,
        "evidence_files": evidence_files,
        "top_company": stage3_summary.get("top_company", {}),
        "output_files": {
            "summary_json": str(SUMMARY_PATH),
            "report_md": str(REPORT_PATH),
            "evidence_csv": str(EVIDENCE_PATH),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Checkpoint")
    print("-" * 88)
    print(f"Status: {summary['status']}")
    print(f"Ready for v0.7 release: {ready}")
    print(f"Funnel: {validated_funnel}")

    print()
    print("Counts")
    print("-" * 88)
    for key, value in summary["counts"].items():
        print(f"{key}: {value}")

    print()
    print("Checks")
    print("-" * 88)
    for key, value in summary["checks"].items():
        print(f"{key}: {value}")

    print()
    print("Next")
    print("-" * 88)
    print(summary["recommended_next_phase"])

    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
