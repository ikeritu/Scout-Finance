from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any


VERSION = "v0.8.0-candidate"


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
    releases = root / "releases"

    print("Scout Finance — v0.8.0-candidate freeze checker")
    print("=" * 92)

    zip_path = releases / "Scout_Finance_v0.8.0_candidate_FREEZE.zip"
    lock_path = releases / "RELEASE_LOCK_v0.8.json"
    report_path = releases / "FREEZE_REPORT_v0.8.md"
    manifest_path = releases / "MANIFEST_v0.8.0_candidate.json"
    v07_zip = releases / "Scout_Finance_v0.7.0_candidate_FREEZE.zip"

    for path in [zip_path, lock_path, report_path, manifest_path]:
        require_file(path)

    lock = read_json(lock_path)
    manifest = read_json(manifest_path)

    require(lock.get("version") == VERSION, "Lock version OK")
    require(lock.get("baseline_version") == "v0.7.0-candidate", "Baseline version OK")
    require(lock.get("ai_execution") == "disabled_by_default", "AI execution disabled by default")
    require(lock.get("default_top_n") == 3, "Default TOP N OK")

    for key in [
        "openai_called",
        "api_called",
        "yfinance_called",
        "pipeline_recalculated",
        "app_modified",
        "filters_modified",
        "release_modified",
    ]:
        require(lock.get(key) is False, f"Lock control OK: {key}=False")

    prereq = lock.get("prerequisites", {})
    require(prereq.get("status") == "OK", "Prerequisites OK")
    require(prereq.get("blockers") == [], "No prerequisite blockers")
    require(prereq.get("v07_zip_exists") is True or v07_zip.exists(), "v0.7 ZIP present or detected")

    require(manifest.get("version") == VERSION, "Manifest version OK")
    require(isinstance(manifest.get("files"), list), "Manifest files is list")
    require(manifest.get("file_count", 0) >= 20, "Manifest file count plausible")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())

    required_inside = [
        "releases/RELEASE_LOCK_v0.8.json",
        "releases/FREEZE_REPORT_v0.8.md",
        "releases/MANIFEST_v0.8.0_candidate.json",
        "outputs/scouting/phase8j_v08_candidate_audit_summary.json",
        "outputs/scouting/phase8j_v08_candidate_audit_report.md",
        "src/phase8j_v08_candidate_audit.py",
        "src/research_memo.py",
        "src/fundamentals.py",
        "src/valuation.py",
        "src/risk_analysis.py",
        "src/moat_analysis.py",
        "src/growth_analysis.py",
        "src/institutional_view.py",
        "src/earnings_analysis.py",
    ]

    for name in required_inside:
        require(name in names, f"ZIP contains: {name}")

    forbidden_fragments = [
        ".venv/",
        ".git/",
        "__pycache__/",
    ]
    for frag in forbidden_fragments:
        require(not any(frag in name for name in names), f"ZIP excludes {frag}")

    report = report_path.read_text(encoding="utf-8")
    for text in [
        "v0.8.0-candidate",
        "OpenAI called: False",
        "yfinance called: False",
        "Real AI execution disabled by default",
        "No inventar datos",
        "data_insufficient",
        "not financial advice",
    ]:
        require(text in report, f"Freeze report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Scout Finance v0.8.0-candidate freeze is valid")


if __name__ == "__main__":
    main()
