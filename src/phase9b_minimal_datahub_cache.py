from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.data_hub import (
    PROJECT_ROOT,
    OUTPUTS_SCOUTING_DIR,
    discover_local_sources,
    ensure_no_external_fetch,
    get_data_mode,
    records_to_dicts,
    write_source_manifest,
    write_source_manifest_csv,
)


PHASE = "9B"
TITLE = "Minimal DataHub and Local Source Manifest"
DEFAULT_TOP_N = 3
MAX_TOP_N = 3

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(path: Path, summary: Dict[str, Any], recommendations: List[Dict[str, str]]) -> None:
    lines = [
        "# Phase 9B — Minimal DataHub and Local Source Manifest",
        "",
        "Status: **OK**",
        "",
        "## Purpose",
        "",
        "Create the smallest possible DataHub layer: local-only, auditable and without external fetches.",
        "",
        "## Summary",
        "",
        f"- Data mode: `{summary['data_mode']}`",
        f"- Local source records: {summary['local_source_records']}",
        f"- outputs/scouting records: {summary['outputs_scouting_records']}",
        f"- data/stages records: {summary['data_stages_records']}",
        f"- External fetch allowed: {summary['external_fetch_allowed']}",
        "",
        "## Safety controls",
        "",
        "- OpenAI called: False",
        "- API called: False",
        "- yfinance called: False",
        "- Pipeline recalculated: False",
        "- app.py modified: False",
        "- filters modified: False",
        "- release modified: False",
        "",
        "## Recommendations",
        "",
        "| Priority | Recommendation |",
        "|---|---|",
    ]
    for rec in recommendations:
        lines.append(f"| {rec['priority']} | {rec['recommendation']} |")

    lines.extend([
        "",
        "## Next",
        "",
        "Proceed to Phase 9C only after reviewing whether this local DataHub is enough or whether a SQLite-backed cache is justified.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    out = OUTPUTS_SCOUTING_DIR
    out.mkdir(parents=True, exist_ok=True)

    phase9a_summary = read_json(out / "phase9a_data_layer_external_calls_audit_summary.json", {})
    guard = ensure_no_external_fetch()
    records = discover_local_sources(dataset_version="phase9b_minimal_datahub_v0_1")
    record_dicts = records_to_dicts(records)

    outputs_count = sum(1 for r in record_dicts if r["source"] == "outputs/scouting")
    stages_count = sum(1 for r in record_dicts if r["source"] == "data/stages")

    manifest_json = out / "phase9b_datahub_local_source_manifest.json"
    manifest_csv = out / "phase9b_datahub_local_source_manifest.csv"
    write_source_manifest(manifest_json, records)
    write_source_manifest_csv(manifest_csv, records)

    expected_paths = {
        "src/data_hub.py": (PROJECT_ROOT / "src" / "data_hub.py").exists(),
        "src/data_cache.py": (PROJECT_ROOT / "src" / "data_cache.py").exists(),
        "src/red_flags.py": (PROJECT_ROOT / "src" / "red_flags.py").exists(),
        "releases/Scout_Finance_v0.8.0_candidate_FREEZE.zip": (PROJECT_ROOT / "releases" / "Scout_Finance_v0.8.0_candidate_FREEZE.zip").exists(),
    }

    recommendations = [
        {
            "priority": "Alta",
            "recommendation": "Use src/data_hub.py as the only new data access entry point for future v0.9 modules.",
        },
        {
            "priority": "Alta",
            "recommendation": "Do not add external fetches yet. Keep local_only until a source-specific connector is justified.",
        },
        {
            "priority": "Media",
            "recommendation": "Review whether SQLite cache is needed after seeing real usage of this manifest.",
        },
        {
            "priority": "Alta",
            "recommendation": "Proceed next with Research Memo v2 contract hardening or Red Flags detector, not real AI calls.",
        },
    ]

    summary = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": utc_now(),
        "default_top_n": DEFAULT_TOP_N,
        "max_top_n": MAX_TOP_N,
        "data_mode": get_data_mode(),
        "external_fetch_allowed": guard["external_fetch_allowed"],
        "local_source_records": len(record_dicts),
        "outputs_scouting_records": outputs_count,
        "data_stages_records": stages_count,
        "phase9a_status": phase9a_summary.get("status"),
        "phase9a_external_findings_count": phase9a_summary.get("external_findings_count"),
        "expected_paths": expected_paths,
        "manifest_json": str(manifest_json),
        "manifest_csv": str(manifest_csv),
        **CONTROL_FLAGS,
        "next": "Phase 9C — Research Memo v2 Contract Hardening or Phase 9D — Red Flags Detector",
    }

    audit = {
        "phase": PHASE,
        "title": TITLE,
        "status": "OK",
        "created_at": summary["created_at"],
        "summary": summary,
        "guard": guard,
        "records_sample": record_dicts[:50],
        "record_count": len(record_dicts),
        "recommendations": recommendations,
    }

    write_json(out / "phase9b_minimal_datahub_cache_summary.json", summary)
    write_json(out / "phase9b_minimal_datahub_cache_audit.json", audit)
    write_report(out / "phase9b_minimal_datahub_cache_report.md", summary, recommendations)

    print("Scout Finance — Phase 9B Minimal DataHub and Local Source Manifest")
    print("=" * 92)
    print()
    print("DataHub")
    print("-" * 92)
    print("Status: OK")
    print(f"Data mode: {summary['data_mode']}")
    print(f"External fetch allowed: {summary['external_fetch_allowed']}")
    print(f"Local source records: {summary['local_source_records']}")
    print(f"outputs/scouting records: {summary['outputs_scouting_records']}")
    print(f"data/stages records: {summary['data_stages_records']}")
    print(f"OpenAI called: False")
    print(f"API called: False")
    print(f"yfinance called: False")
    print(f"Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 9B Minimal DataHub and Local Source Manifest is complete.")


if __name__ == "__main__":
    main()
