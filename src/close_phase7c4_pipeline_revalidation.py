
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

OUT_DIR = ROOT / "outputs" / "scouting"

STAGE1_SUMMARY_CANDIDATES = [
    OUT_DIR / "stage1_balanced_official_closure_summary.json",
    OUT_DIR / "stage1_summary.json",
]

STAGE2_SUMMARY = OUT_DIR / "stage2_summary.json"
STAGE3_SUMMARY = OUT_DIR / "stage3_summary.json"
STAGE2_IMPLEMENTATION_SUMMARY = OUT_DIR / "stage2_yfinance_policy_implementation_summary.json"

STAGE1_FILES = {
    "passed": ROOT / "data" / "stages" / "stage1_passed.csv",
    "watchlist": ROOT / "data" / "stages" / "stage1_watchlist.csv",
    "rejected": ROOT / "data" / "stages" / "stage1_rejected.csv",
}

STAGE2_FILES = {
    "passed": ROOT / "data" / "stages" / "stage2_passed.csv",
    "watchlist": ROOT / "data" / "stages" / "stage2_watchlist.csv",
    "rejected": ROOT / "data" / "stages" / "stage2_rejected.csv",
}

STAGE3_FILES = {
    "passed": ROOT / "data" / "stages" / "stage3_passed.csv",
    "watchlist": ROOT / "data" / "stages" / "stage3_watchlist.csv",
    "rejected": ROOT / "data" / "stages" / "stage3_rejected.csv",
}

EXPORT_FILES = {
    "stage3_candidates_for_ranking": OUT_DIR / "stage3_candidates_for_ranking.csv",
    "top_20_deep_research": OUT_DIR / "top_20_deep_research.csv",
    "top_50_watchlist": OUT_DIR / "top_50_watchlist.csv",
    "top_100_candidates": OUT_DIR / "top_100_candidates.csv",
    "top_recoverable_candidates": OUT_DIR / "top_recoverable_candidates.csv",
}

SUMMARY_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_summary.json"
REPORT_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_report.md"
EVIDENCE_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_evidence.csv"
TOP_CANDIDATES_PATH = OUT_DIR / "phase7c4_pipeline_revalidation_top_candidates.csv"
POLICY_STATUS_PATH = OUT_DIR / "active_pipeline_policy_status.json"

EXPECTED = {
    "stage1": {"passed": 182, "watchlist": 84, "rejected": 234},
    "stage2": {"passed": 63, "watchlist": 81, "rejected": 38},
    "stage3": {"passed": 6, "watchlist": 28, "rejected": 29},
}

EXPECTED_FUNNEL = {
    "initial_pilot_universe": 500,
    "stage1_passed": 182,
    "stage2_passed": 63,
    "stage3_passed": 6,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
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


def file_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "rows": 0,
            "size_bytes": 0,
            "modified_at": None,
        }

    stat = path.stat()
    rows = count_csv(path) if path.suffix.lower() == ".csv" else None
    return {
        "path": str(path),
        "exists": True,
        "rows": rows,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
    }


def read_stage1_summary() -> dict[str, Any]:
    for path in STAGE1_SUMMARY_CANDIDATES:
        data = read_json(path)
        if data:
            data["_source_path"] = str(path)
            return data
    return {}


def stage_counts(files: dict[str, Path]) -> dict[str, int]:
    return {key: count_csv(path) for key, path in files.items()}


def percentages(counts: dict[str, int], denominator: int) -> dict[str, float]:
    if denominator <= 0:
        return {key + "_rate": 0.0 for key in counts}
    return {
        key + "_rate": round(100 * value / denominator, 2)
        for key, value in counts.items()
    }


def extract_top_candidates(limit: int = 20) -> pd.DataFrame:
    candidates = ROOT / "outputs" / "scouting" / "top_100_candidates.csv"
    if not candidates.exists():
        return pd.DataFrame()

    df = pd.read_csv(candidates)
    score_col = "final_stage3_score" if "final_stage3_score" in df.columns else None
    if score_col:
        df = df.sort_values(score_col, ascending=False)

    cols = [col for col in [
        "ticker",
        "name",
        "final_stage3_score",
        "stage3_category",
        "stage3_status",
        "risk_score",
        "data_quality_score",
    ] if col in df.columns]

    return df[cols].head(limit) if cols else df.head(limit)


def render_report(summary: dict[str, Any], top_candidates: pd.DataFrame) -> str:
    stage1 = summary["stage_counts"]["stage1"]
    stage2 = summary["stage_counts"]["stage2"]
    stage3 = summary["stage_counts"]["stage3"]

    top_lines = []
    if not top_candidates.empty:
        for _, row in top_candidates.head(10).iterrows():
            ticker = row.get("ticker", "")
            name = row.get("name", "")
            score = row.get("final_stage3_score", "")
            category = row.get("stage3_category", "")
            top_lines.append(f"- {ticker} | {name} | score={score} | {category}")
    else:
        top_lines.append("- No top candidates file found.")

    evidence_lines = []
    for item in summary["evidence_files"]:
        evidence_lines.append(
            f"- {item['label']}: exists={item['exists']} rows={item.get('rows')} path=`{item['path']}`"
        )

    return f"""# Scout Finance — Phase 7C.4 Pipeline revalidation closure

Generated at: `{summary["created_at"]}`

## Closure status

- Status: **{summary["status"]}**
- Ready for next phase: **{summary["ready_for_next_phase"]}**
- Recommended next phase: **{summary["recommended_next_phase"]}**

## Active policies

| Layer | Active policy |
|---|---|
| Stage 1 | {summary["active_policies"]["stage1"]} |
| Stage 2 | {summary["active_policies"]["stage2"]} |
| Stage 3 | {summary["active_policies"]["stage3"]} |

## Funnel

```text
500 initial clean pilot universe
→ {stage1["passed"]} Stage 1 PASSED
→ {stage2["passed"]} Stage 2 PASSED
→ {stage3["passed"]} Stage 3 PASSED
```

## Stage counts

| Stage | Passed | Watchlist | Rejected |
|---|---:|---:|---:|
| Stage 1 | {stage1["passed"]} | {stage1["watchlist"]} | {stage1["rejected"]} |
| Stage 2 | {stage2["passed"]} | {stage2["watchlist"]} | {stage2["rejected"]} |
| Stage 3 | {stage3["passed"]} | {stage3["watchlist"]} | {stage3["rejected"]} |

## Stage 3 category distribution

```json
{json.dumps(summary["stage3_category_distribution"], indent=2, ensure_ascii=False)}
```

## Top company

```json
{json.dumps(summary["top_company"], indent=2, ensure_ascii=False)}
```

## Top candidates

{chr(10).join(top_lines)}

## Evidence files

{chr(10).join(evidence_lines)}

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- release modified: `{summary["release_modified"]}`

## Notes

This phase only closes the revalidation evidence. It does not modify production code, dashboard code, release files, or external-data providers.
"""


def main() -> int:
    print("Scout Finance — Phase 7C.4 pipeline revalidation closure")
    print("=" * 88)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stage1_summary = read_stage1_summary()
    stage2_summary = read_json(STAGE2_SUMMARY)
    stage3_summary = read_json(STAGE3_SUMMARY)
    stage2_impl_summary = read_json(STAGE2_IMPLEMENTATION_SUMMARY)

    stage1_counts = stage_counts(STAGE1_FILES)
    stage2_counts = stage_counts(STAGE2_FILES)
    stage3_counts = stage_counts(STAGE3_FILES)

    initial_pilot = sum(stage1_counts.values())

    top_candidates = extract_top_candidates(limit=20)
    top_candidates.to_csv(TOP_CANDIDATES_PATH, index=False, encoding="utf-8-sig")

    evidence_items = []

    for label, path in [
        ("stage1_summary", Path(stage1_summary.get("_source_path", "")) if stage1_summary.get("_source_path") else Path("")),
        ("stage2_summary", STAGE2_SUMMARY),
        ("stage3_summary", STAGE3_SUMMARY),
        ("stage2_implementation_summary", STAGE2_IMPLEMENTATION_SUMMARY),
    ]:
        if str(path):
            info = file_info(path)
            info["label"] = label
            evidence_items.append(info)

    for group_name, files in [
        ("stage1", STAGE1_FILES),
        ("stage2", STAGE2_FILES),
        ("stage3", STAGE3_FILES),
        ("exports", EXPORT_FILES),
    ]:
        for label, path in files.items():
            info = file_info(path)
            info["label"] = f"{group_name}_{label}"
            evidence_items.append(info)

    evidence_df = pd.DataFrame(evidence_items)
    evidence_df.to_csv(EVIDENCE_PATH, index=False, encoding="utf-8-sig")

    counts_match = (
        stage1_counts == EXPECTED["stage1"]
        and stage2_counts == EXPECTED["stage2"]
        and stage3_counts == EXPECTED["stage3"]
        and initial_pilot == EXPECTED_FUNNEL["initial_pilot_universe"]
    )

    stage2_policy_ok = (
        stage2_impl_summary.get("status") == "OK"
        and stage2_impl_summary.get("matches_expected") is True
        and stage2_impl_summary.get("provider_limitation_reason_present") is True
    )

    stage3_ok = (
        stage3_summary.get("input_companies") == 63
        and stage3_summary.get("passed_companies") == 6
        and stage3_summary.get("watchlist_companies") == 28
        and stage3_summary.get("rejected_companies") == 29
    )

    export_ok = EXPORT_FILES["stage3_candidates_for_ranking"].exists() and count_csv(EXPORT_FILES["stage3_candidates_for_ranking"]) > 0

    status = "OK" if counts_match and stage2_policy_ok and stage3_ok and export_ok else "REVIEW"

    summary = {
        "phase": "7C.4",
        "status": status,
        "created_at": utc_now(),
        "ready_for_next_phase": status == "OK",
        "recommended_next_phase": "7D — Integrate real revalidated funnel into dashboard/app" if status == "OK" else "7C.4b — Fix missing evidence before dashboard integration",
        "active_policies": {
            "stage1": "Balanced official policy",
            "stage2": "yfinance-aligned provider-limitation policy",
            "stage3": "Existing Stage 3 opportunity scoring policy",
        },
        "stage_counts": {
            "stage1": stage1_counts,
            "stage2": stage2_counts,
            "stage3": stage3_counts,
        },
        "funnel": {
            "initial_pilot_universe": initial_pilot,
            "stage1_passed": stage1_counts["passed"],
            "stage2_passed": stage2_counts["passed"],
            "stage3_passed": stage3_counts["passed"],
            "path": f"{initial_pilot} → {stage1_counts['passed']} → {stage2_counts['passed']} → {stage3_counts['passed']}",
        },
        "rates": {
            "stage1": percentages(stage1_counts, initial_pilot),
            "stage2": percentages(stage2_counts, stage1_counts["passed"]),
            "stage3": percentages(stage3_counts, stage2_counts["passed"]),
            "overall_stage3_pass_rate_from_initial": round(100 * stage3_counts["passed"] / initial_pilot, 2) if initial_pilot else 0.0,
        },
        "checks": {
            "counts_match_expected": counts_match,
            "stage2_policy_ok": stage2_policy_ok,
            "stage3_ok": stage3_ok,
            "export_ok": export_ok,
        },
        "stage3_category_distribution": stage3_summary.get("category_distribution", {}),
        "stage3_reasons": stage3_summary.get("top_rejection_or_watchlist_reasons", {}),
        "top_company": stage3_summary.get("top_company", {}),
        "evidence_files": evidence_items,
        "output_files": {
            "summary_json": str(SUMMARY_PATH),
            "report_md": str(REPORT_PATH),
            "evidence_csv": str(EVIDENCE_PATH),
            "top_candidates_csv": str(TOP_CANDIDATES_PATH),
            "policy_status_json": str(POLICY_STATUS_PATH),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "release_modified": False,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary, top_candidates), encoding="utf-8")

    policy_status = {
        "created_at": summary["created_at"],
        "active_stage1_policy": summary["active_policies"]["stage1"],
        "active_stage2_policy": summary["active_policies"]["stage2"],
        "active_stage3_policy": summary["active_policies"]["stage3"],
        "current_revalidated_funnel": summary["funnel"],
        "ready_for_dashboard_integration": summary["ready_for_next_phase"],
        "source_phase": "7C.4",
    }
    POLICY_STATUS_PATH.write_text(json.dumps(policy_status, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("Funnel")
    print("-" * 88)
    print(summary["funnel"]["path"])

    print()
    print("Stage counts")
    print("-" * 88)
    print(f"Stage 1: {stage1_counts}")
    print(f"Stage 2: {stage2_counts}")
    print(f"Stage 3: {stage3_counts}")

    print()
    print("Checks")
    print("-" * 88)
    for key, value in summary["checks"].items():
        print(f"{key}: {value}")

    print()
    print("Status")
    print("-" * 88)
    print(status)
    print(summary["recommended_next_phase"])

    return 0 if status == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
