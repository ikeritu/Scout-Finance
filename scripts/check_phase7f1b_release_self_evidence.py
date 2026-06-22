
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "releases" / "v0.7"
RELEASE_OUTPUTS = RELEASE_DIR / "outputs" / "scouting"
MANIFEST_PATH = RELEASE_DIR / "manifest_v0.7.json"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7f1b_release_self_evidence_fix_summary.json"
REPORT_PATH = OUT_DIR / "phase7f1b_release_self_evidence_fix_report.md"

REQUIRED_RELEASE_FILES = [
    RELEASE_OUTPUTS / "phase7f_release_v07_packaging_summary.json",
    RELEASE_OUTPUTS / "phase7f_release_v07_packaging_report.md",
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
    print("Scout Finance — Phase 7F.1b release self-evidence fix checker")
    print("=" * 88)

    for path in [SUMMARY_PATH, REPORT_PATH, MANIFEST_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    for path in REQUIRED_RELEASE_FILES:
        if not path.exists():
            fail(f"Missing release self-evidence file: {path}")
            return 1
        ok(f"Release self-evidence exists: {path}")

    manifest = read_json(MANIFEST_PATH)
    manifest_paths = {entry.get("path") for entry in manifest.get("files", []) if isinstance(entry, dict)}

    for rel in [
        "outputs/scouting/phase7f_release_v07_packaging_summary.json",
        "outputs/scouting/phase7f_release_v07_packaging_report.md",
    ]:
        if rel not in manifest_paths:
            fail(f"Manifest missing self-evidence entry: {rel}")
            return 1
        ok(f"Manifest contains: {rel}")

    summary = read_json(SUMMARY_PATH)

    if summary.get("phase") != "7F.1b":
        fail(f"Summary phase is not 7F.1b: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7F.1b")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("release_self_evidence_complete") is not True:
        fail("release_self_evidence_complete is not True")
        return 1
    ok("release_self_evidence_complete=True")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "app.py was not modified"),
        ("filters_modified", False, "filters were not modified"),
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
    ok("Phase 7F.1b release self-evidence fix is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
