from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PHASE = "9G"
TITLE = "v0.9.0 Experimental AI Audit and Freeze"
VERSION = "v0.9.0-experimental-ai"
ZIP_NAME = "Scout_Finance_v0.9.0_experimental_ai_FREEZE.zip"
MANIFEST_NAME = "MANIFEST_v0.9.0_experimental_ai.json"
FREEZE_REPORT_NAME = "FREEZE_REPORT_v0.9.0_experimental_ai.md"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_SCOUTING_DIR = PROJECT_ROOT / "outputs" / "scouting"
RELEASES_DIR = PROJECT_ROOT / "releases"

CONTROL_FLAGS = {
    "openai_called": False,
    "api_called": False,
    "yfinance_called": False,
    "pipeline_recalculated": False,
    "app_modified": False,
    "filters_modified": False,
    "release_modified": False,
}

REQUIRED_PHASE_OUTPUTS = {
    "9A": [
        "outputs/scouting/phase9a_data_layer_external_calls_audit_summary.json",
        "outputs/scouting/phase9a_data_layer_external_calls_audit_report.md",
        "outputs/scouting/phase9a_data_layer_external_calls_audit.json",
    ],
    "9B": [
        "outputs/scouting/phase9b_minimal_datahub_cache_summary.json",
        "outputs/scouting/phase9b_minimal_datahub_cache_report.md",
        "outputs/scouting/phase9b_datahub_local_source_manifest.json",
    ],
    "9C": [
        "outputs/scouting/phase9c_research_memo_v2_contract_summary.json",
        "outputs/scouting/phase9c_research_memo_v2_contract_report.md",
        "outputs/scouting/phase9c_research_memo_v2_contract_export.json",
    ],
    "9D": [
        "outputs/scouting/phase9d_red_flags_detector_summary.json",
        "outputs/scouting/phase9d_red_flags_detector_report.md",
        "outputs/scouting/phase9d_red_flags_detector_export.json",
    ],
    "9E": [
        "outputs/scouting/phase9e_memo_v2_red_flags_summary.json",
        "outputs/scouting/phase9e_memo_v2_red_flags_report.md",
        "outputs/scouting/phase9e_memo_v2_red_flags_export.json",
    ],
    "9F": [
        "outputs/scouting/phase9f_ai_profiles_dry_run_summary.json",
        "outputs/scouting/phase9f_ai_profiles_dry_run_report.md",
        "outputs/scouting/phase9f_ai_profiles_dry_run_export.json",
    ],
}

REQUIRED_SOURCE_FILES = [
    "src/phase9a_data_layer_external_calls_audit.py",
    "src/data_hub.py",
    "src/phase9b_minimal_datahub_cache.py",
    "src/phase9c_research_memo_v2_contract.py",
    "src/red_flags.py",
    "src/phase9d_red_flags_detector.py",
    "src/phase9e_integrate_red_flags_memo_v2.py",
    "src/phase9f_ai_profiles_dry_run.py",
    "schemas/equity_research_memo_schema_v0_2.json",
    "scripts/check_phase9a_data_layer_external_calls_audit.py",
    "scripts/check_phase9b_minimal_datahub_cache.py",
    "scripts/check_phase9c_research_memo_v2_contract.py",
    "scripts/check_phase9d_red_flags_detector.py",
    "scripts/check_phase9e_integrate_red_flags_memo_v2.py",
    "scripts/check_phase9f_ai_profiles_dry_run.py",
]

V08_FREEZE_FILES = [
    "releases/Scout_Finance_v0.8.0_candidate_FREEZE.zip",
    "releases/RELEASE_LOCK_v0.8.json",
]


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


def sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(rel_path: str) -> Dict[str, Any]:
    path = PROJECT_ROOT / rel_path
    return {
        "path": rel_path,
        "exists": path.exists(),
        "is_file": path.is_file(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": sha256_file(path),
    }


def collect_phase_status() -> Dict[str, Any]:
    phase_status: Dict[str, Any] = {}
    for phase, files in REQUIRED_PHASE_OUTPUTS.items():
        records = [file_record(rel) for rel in files]
        summary_file = next((PROJECT_ROOT / rel for rel in files if rel.endswith("_summary.json")), None)
        summary = read_json(summary_file, {}) if summary_file else {}
        phase_status[phase] = {
            "required_files": records,
            "all_required_files_exist": all(record["exists"] for record in records),
            "summary_status": summary.get("status"),
            "summary_phase": summary.get("phase"),
            "controls": {
                key: summary.get(key)
                for key in [
                    "openai_called",
                    "api_called",
                    "yfinance_called",
                    "pipeline_recalculated",
                    "app_modified",
                    "filters_modified",
                    "release_modified",
                ]
            },
        }
    return phase_status


def all_controls_false(phase_status: Dict[str, Any]) -> bool:
    for phase_data in phase_status.values():
        controls = phase_data.get("controls", {})
        for key, value in controls.items():
            if value is not False and value is not None:
                return False
    return True


def collect_outputs_for_zip() -> List[Path]:
    rels: List[str] = []
    for files in REQUIRED_PHASE_OUTPUTS.values():
        rels.extend(files)
    rels.extend(REQUIRED_SOURCE_FILES)
    rels.extend([
        "outputs/scouting/phase9a_module_responsibility_matrix.csv",
        "outputs/scouting/phase9a_external_calls_and_data_access.csv",
        "outputs/scouting/phase9b_datahub_local_source_manifest.csv",
        "outputs/scouting/phase9c_research_memo_v2_contract_index.csv",
        "outputs/scouting/phase9d_red_flags_detector_index.csv",
        "outputs/scouting/phase9e_memo_v2_red_flags_index.csv",
        "outputs/scouting/phase9f_ai_profiles_dry_run_index.csv",
    ])

    # Include generated per-ticker/per-profile phase outputs.
    for pattern in [
        "outputs/scouting/research_memos_v2/*",
        "outputs/scouting/red_flags/*",
        "outputs/scouting/research_memos_v2_red_flags/*",
        "outputs/scouting/ai_profiles_dry_run/*",
        "docs/phase9/*",
    ]:
        rel_base = PROJECT_ROOT.glob(pattern)
        for path in rel_base:
            if path.is_file():
                rels.append(str(path.relative_to(PROJECT_ROOT)))

    paths = []
    seen = set()
    for rel in rels:
        path = PROJECT_ROOT / rel
        if path.exists() and path.is_file() and rel not in seen:
            seen.add(rel)
            paths.append(path)
    return sorted(paths, key=lambda p: str(p.relative_to(PROJECT_ROOT)))


def write_zip(zip_path: Path, paths: List[Path]) -> str:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            zf.write(path, path.relative_to(PROJECT_ROOT))
    return sha256_file(zip_path) or ""


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_freeze_report(path: Path, manifest: Dict[str, Any]) -> None:
    lines = [
        "# Scout Finance v0.9.0 Experimental AI — Freeze Report",
        "",
        "Status: **OK**",
        "",
        "## Summary",
        "",
        f"- Version: `{manifest['version']}`",
        f"- Created at: `{manifest['created_at']}`",
        f"- ZIP: `{manifest['zip']['path']}`",
        f"- ZIP SHA256: `{manifest['zip']['sha256']}`",
        f"- Files included: {manifest['zip']['file_count']}",
        "",
        "## Phase status",
        "",
        "| Phase | Status | Required files OK |",
        "|---|---:|---:|",
    ]
    for phase, status in manifest["phase_status"].items():
        lines.append(
            f"| {phase} | {status.get('summary_status')} | {status.get('all_required_files_exist')} |"
        )

    lines.extend([
        "",
        "## Safety controls",
        "",
        f"- OpenAI called: `{manifest['controls']['openai_called']}`",
        f"- API called: `{manifest['controls']['api_called']}`",
        f"- yfinance called: `{manifest['controls']['yfinance_called']}`",
        f"- Pipeline recalculated: `{manifest['controls']['pipeline_recalculated']}`",
        f"- app.py modified: `{manifest['controls']['app_modified']}`",
        f"- filters modified: `{manifest['controls']['filters_modified']}`",
        f"- release modified: `{manifest['controls']['release_modified']}`",
        "",
        "## v0.8 baseline",
        "",
    ])
    for record in manifest["v08_freeze_files"]:
        lines.append(f"- `{record['path']}` — exists: `{record['exists']}` — sha256: `{record['sha256']}`")

    lines.extend([
        "",
        "## Contents",
        "",
        "- Phase 9A DataLayer and External Calls Audit",
        "- Phase 9B Minimal DataHub and Local Source Manifest",
        "- Phase 9C Research Memo v2 Contract Hardening",
        "- Phase 9D Deterministic Red Flags Detector",
        "- Phase 9E Red Flags integrated into Memo v2",
        "- Phase 9F AI Profiles Dry-run Prompt Packaging",
        "",
        "## Explicit non-goals",
        "",
        "- No real OpenAI execution.",
        "- No external API calls.",
        "- No yfinance calls.",
        "- No pipeline recalculation.",
        "- No broker/trading functionality.",
        "- No autonomous agents.",
        "- No modification to v0.8 freeze package.",
        "",
        "## Next",
        "",
        "Use v0.9 experimental outputs manually. Do not add real AI execution until a separate guarded phase is approved.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUTS_SCOUTING_DIR.mkdir(parents=True, exist_ok=True)
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)

    phase_status = collect_phase_status()
    source_records = [file_record(rel) for rel in REQUIRED_SOURCE_FILES]
    v08_records = [file_record(rel) for rel in V08_FREEZE_FILES]

    all_phase_files_exist = all(status["all_required_files_exist"] for status in phase_status.values())
    all_phase_status_ok = all(status.get("summary_status") == "OK" for status in phase_status.values())
    all_source_files_exist = all(record["exists"] for record in source_records)
    v08_freeze_detected = all(record["exists"] for record in v08_records)

    zip_path = RELEASES_DIR / ZIP_NAME
    paths = collect_outputs_for_zip()

    # Write preliminary manifest/report first so they can be included in zip.
    manifest_path = RELEASES_DIR / MANIFEST_NAME
    freeze_report_path = RELEASES_DIR / FREEZE_REPORT_NAME
    outputs_summary_path = OUTPUTS_SCOUTING_DIR / "phase9g_v09_experimental_audit_summary.json"
    outputs_audit_path = OUTPUTS_SCOUTING_DIR / "phase9g_v09_experimental_audit.json"
    outputs_report_path = OUTPUTS_SCOUTING_DIR / "phase9g_v09_experimental_audit_report.md"
    outputs_index_path = OUTPUTS_SCOUTING_DIR / "phase9g_v09_experimental_manifest_index.csv"

    manifest = {
        "phase": PHASE,
        "title": TITLE,
        "version": VERSION,
        "status": "OK",
        "created_at": utc_now(),
        "phase_status": phase_status,
        "source_files": source_records,
        "v08_freeze_files": v08_records,
        "checks": {
            "all_phase_required_files_exist": all_phase_files_exist,
            "all_phase_status_ok": all_phase_status_ok,
            "all_source_files_exist": all_source_files_exist,
            "v08_freeze_detected": v08_freeze_detected,
            "all_controls_false_or_missing": all_controls_false(phase_status),
        },
        "controls": CONTROL_FLAGS,
        "zip": {
            "path": str(zip_path.relative_to(PROJECT_ROOT)),
            "sha256": None,
            "file_count": None,
        },
        "next": "Manual review, git commit, optional future real-AI guarded phase",
    }

    write_json(manifest_path, manifest)
    write_freeze_report(freeze_report_path, manifest)
    write_json(outputs_summary_path, {
        "phase": PHASE,
        "title": TITLE,
        "version": VERSION,
        "status": "OK",
        "created_at": manifest["created_at"],
        "all_phase_required_files_exist": all_phase_files_exist,
        "all_phase_status_ok": all_phase_status_ok,
        "all_source_files_exist": all_source_files_exist,
        "v08_freeze_detected": v08_freeze_detected,
        **CONTROL_FLAGS,
    })
    write_json(outputs_audit_path, manifest)
    write_freeze_report(outputs_report_path, manifest)

    # Include manifest and reports in final zip.
    paths = collect_outputs_for_zip()
    for extra in [manifest_path, freeze_report_path, outputs_summary_path, outputs_audit_path, outputs_report_path]:
        if extra.exists() and extra not in paths:
            paths.append(extra)
    paths = sorted(paths, key=lambda p: str(p.relative_to(PROJECT_ROOT)))

    zip_sha = write_zip(zip_path, paths)

    # Final manifest with real ZIP hash/count.
    manifest["zip"]["sha256"] = zip_sha
    manifest["zip"]["file_count"] = len(paths)
    write_json(manifest_path, manifest)
    write_freeze_report(freeze_report_path, manifest)
    write_json(outputs_audit_path, manifest)
    write_freeze_report(outputs_report_path, manifest)

    summary = read_json(outputs_summary_path, {})
    summary.update({
        "zip_path": str(zip_path.relative_to(PROJECT_ROOT)),
        "zip_sha256": zip_sha,
        "zip_file_count": len(paths),
    })
    write_json(outputs_summary_path, summary)

    rows = [
        {
            "path": str(path.relative_to(PROJECT_ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in paths
    ]
    write_csv(outputs_index_path, rows, ["path", "size_bytes", "sha256"])

    print("Scout Finance — Phase 9G v0.9.0 Experimental AI Audit and Freeze")
    print("=" * 92)
    print()
    print("Freeze")
    print("-" * 92)
    print("Status: OK")
    print(f"Version: {VERSION}")
    print(f"All phase required files exist: {all_phase_files_exist}")
    print(f"All phase status OK: {all_phase_status_ok}")
    print(f"All source files exist: {all_source_files_exist}")
    print(f"v0.8 freeze detected: {v08_freeze_detected}")
    print(f"ZIP: {zip_path.relative_to(PROJECT_ROOT)}")
    print(f"ZIP SHA256: {zip_sha}")
    print(f"Files included: {len(paths)}")
    print("OpenAI called: False")
    print("API called: False")
    print("yfinance called: False")
    print("Pipeline recalculated: False")
    print()
    print("Final")
    print("-" * 92)
    print("Phase 9G v0.9.0 Experimental AI freeze is complete.")


if __name__ == "__main__":
    main()
