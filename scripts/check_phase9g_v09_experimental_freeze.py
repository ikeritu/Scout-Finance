from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any


PHASE = "9G"
VERSION = "v0.9.0-experimental-ai"
ZIP_NAME = "Scout_Finance_v0.9.0_experimental_ai_FREEZE.zip"
MANIFEST_NAME = "MANIFEST_v0.9.0_experimental_ai.json"
FREEZE_REPORT_NAME = "FREEZE_REPORT_v0.9.0_experimental_ai.md"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if condition:
        ok(message)
    else:
        fail(message)


def require_file(path: Path) -> None:
    require(path.exists(), f"File exists: {path}")


def main() -> None:
    root = project_root()
    out = root / "outputs" / "scouting"
    releases = root / "releases"

    print("Scout Finance — Phase 9G v0.9.0 Experimental AI freeze checker")
    print("=" * 92)

    required = [
        root / "src" / "phase9g_v09_experimental_freeze.py",
        root / "scripts" / "check_phase9g_v09_experimental_freeze.py",
        out / "phase9g_v09_experimental_audit_summary.json",
        out / "phase9g_v09_experimental_audit_report.md",
        out / "phase9g_v09_experimental_audit.json",
        out / "phase9g_v09_experimental_manifest_index.csv",
        releases / MANIFEST_NAME,
        releases / FREEZE_REPORT_NAME,
        releases / ZIP_NAME,
        releases / "Scout_Finance_v0.8.0_candidate_FREEZE.zip",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "phase9g_v09_experimental_audit_summary.json")
    manifest = read_json(releases / MANIFEST_NAME)
    audit = read_json(out / "phase9g_v09_experimental_audit.json")

    require(summary.get("phase") == PHASE, "Summary phase is 9G")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("version") == VERSION, "Summary version OK")
    require(summary.get("all_phase_required_files_exist") is True, "All phase required files exist")
    require(summary.get("all_phase_status_ok") is True, "All phase statuses OK")
    require(summary.get("all_source_files_exist") is True, "All source files exist")
    require(summary.get("v08_freeze_detected") is True, "v0.8 freeze detected")
    require(summary.get("zip_sha256"), "ZIP SHA present")
    require(summary.get("zip_file_count", 0) > 0, "ZIP file count > 0")

    for key in [
        "openai_called",
        "api_called",
        "yfinance_called",
        "pipeline_recalculated",
        "app_modified",
        "filters_modified",
        "release_modified",
    ]:
        require(summary.get(key) is False, f"Summary control OK: {key}=False")
        require(manifest.get("controls", {}).get(key) is False, f"Manifest control OK: {key}=False")

    require(manifest.get("phase") == PHASE, "Manifest phase OK")
    require(manifest.get("version") == VERSION, "Manifest version OK")
    require(manifest.get("status") == "OK", "Manifest status OK")
    require(manifest.get("zip", {}).get("sha256") == summary.get("zip_sha256"), "ZIP SHA matches summary")
    require(manifest.get("zip", {}).get("file_count") == summary.get("zip_file_count"), "ZIP file count matches summary")
    require(audit.get("version") == VERSION, "Audit version OK")

    phase_status = manifest.get("phase_status", {})
    for phase in ["9A", "9B", "9C", "9D", "9E", "9F"]:
        require(phase in phase_status, f"Phase {phase} present in manifest")
        require(phase_status[phase].get("summary_status") == "OK", f"Phase {phase} status OK")
        require(phase_status[phase].get("all_required_files_exist") is True, f"Phase {phase} files OK")

    zip_path = releases / ZIP_NAME
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
    for expected in [
        "src/data_hub.py",
        "src/red_flags.py",
        "src/phase9f_ai_profiles_dry_run.py",
        "outputs/scouting/phase9f_ai_profiles_dry_run_summary.json",
        f"releases/{MANIFEST_NAME}",
        f"releases/{FREEZE_REPORT_NAME}",
    ]:
        require(expected in names, f"ZIP contains: {expected}")

    report = (releases / FREEZE_REPORT_NAME).read_text(encoding="utf-8")
    for text in [
        "Scout Finance v0.9.0 Experimental AI",
        "Phase 9A",
        "Phase 9F",
        "OpenAI called",
        "No real OpenAI execution",
        "No pipeline recalculation",
    ]:
        require(text in report, f"Freeze report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Scout Finance v0.9.0 experimental AI freeze is valid")


if __name__ == "__main__":
    main()
