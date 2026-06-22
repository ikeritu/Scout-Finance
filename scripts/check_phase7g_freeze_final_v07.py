
from __future__ import annotations

import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RELEASE_DIR = ROOT / "releases" / "v0.7"
ZIP_PATH = ROOT / "releases" / "Scout_Finance_v0.7.0_candidate_FREEZE.zip"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7g_freeze_final_v07_summary.json"
REPORT_PATH = OUT_DIR / "phase7g_freeze_final_v07_report.md"

LOCK_PATH = RELEASE_DIR / "RELEASE_LOCK_v0.7.json"
FREEZE_REPORT_RELEASE_PATH = RELEASE_DIR / "FREEZE_REPORT_v0.7.md"

REQUIRED_IN_ZIP = [
    "Scout_Finance_v0.7/VERSION",
    "Scout_Finance_v0.7/CHANGELOG_v0.7.md",
    "Scout_Finance_v0.7/RELEASE_NOTES_v0.7.md",
    "Scout_Finance_v0.7/RELEASE_LOCK_v0.7.json",
    "Scout_Finance_v0.7/FREEZE_REPORT_v0.7.md",
    "Scout_Finance_v0.7/manifest_v0.7.json",
    "Scout_Finance_v0.7/app.py",
    "Scout_Finance_v0.7/outputs/scouting/phase7f1_release_v07_integrity_summary.json",
    "Scout_Finance_v0.7/data/stages/stage1_passed.csv",
    "Scout_Finance_v0.7/data/stages/stage2_passed.csv",
    "Scout_Finance_v0.7/data/stages/stage3_passed.csv",
]


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    print("Scout Finance — Phase 7G freeze final v0.7 checker")
    print("=" * 88)

    for path in [SUMMARY_PATH, REPORT_PATH, LOCK_PATH, FREEZE_REPORT_RELEASE_PATH, ZIP_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    summary = read_json(SUMMARY_PATH)

    if summary.get("phase") != "7G":
        fail(f"Summary phase is not 7G: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7G")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("freeze_status") != "FROZEN":
        fail(f"Freeze status is not FROZEN: {summary.get('freeze_status')}")
        return 1
    ok("Freeze status FROZEN")

    if summary.get("validated_funnel") != "500 → 182 → 63 → 6":
        fail(f"Unexpected funnel: {summary.get('validated_funnel')}")
        return 1
    ok("Funnel OK: 500 → 182 → 63 → 6")

    counts = summary.get("counts", {})
    for key, expected in {
        "stage1_passed": 182,
        "stage2_passed": 63,
        "stage3_passed": 6,
        "stage3_candidates_for_ranking": 34,
    }.items():
        if counts.get(key) != expected:
            fail(f"{key} mismatch: {counts.get(key)} != {expected}")
            return 1
        ok(f"{key} OK: {expected}")

    lock = read_json(LOCK_PATH)
    if lock.get("status") != "FROZEN":
        fail(f"Lock status is not FROZEN: {lock.get('status')}")
        return 1
    ok("Lock status FROZEN")

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        names = set(z.namelist())

    for required in REQUIRED_IN_ZIP:
        if required not in names:
            fail(f"ZIP missing: {required}")
            return 1
        ok(f"ZIP contains: {required}")

    if summary.get("zip_required_files_present") is not True:
        fail("zip_required_files_present is not True")
        return 1
    ok("ZIP required files present")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "root app.py was not modified"),
        ("filters_modified", False, "filters were not modified"),
        ("pipeline_recalculated", False, "pipeline was not recalculated"),
        ("release_modified", True, "release was modified"),
    ]:
        if summary.get(flag) is expected:
            ok(label)
        else:
            fail(f"Invalid flag {flag}: {summary.get(flag)}")
            return 1

    print()
    print("Result")
    print("-" * 88)
    ok("Scout Finance v0.7.0-candidate final freeze is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
