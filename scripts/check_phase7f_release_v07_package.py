
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "releases" / "v0.7"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7f_release_v07_packaging_summary.json"
REPORT_PATH = OUT_DIR / "phase7f_release_v07_packaging_report.md"
MANIFEST_PATH = RELEASE_DIR / "manifest_v0.7.json"

REQUIRED_RELEASE_FILES = [
    RELEASE_DIR / "VERSION",
    RELEASE_DIR / "CHANGELOG_v0.7.md",
    RELEASE_DIR / "RELEASE_NOTES_v0.7.md",
    RELEASE_DIR / "manifest_v0.7.json",
    RELEASE_DIR / "app.py",
    RELEASE_DIR / "src",
    RELEASE_DIR / "scripts",
    RELEASE_DIR / "docs" / "phase7",
    RELEASE_DIR / "outputs" / "scouting" / "phase7e_v07_release_checkpoint_summary.json",
    RELEASE_DIR / "outputs" / "scouting" / "phase7c4_pipeline_revalidation_summary.json",
    RELEASE_DIR / "outputs" / "scouting" / "stage3_candidates_for_ranking.csv",
    RELEASE_DIR / "data" / "stages" / "stage1_passed.csv",
    RELEASE_DIR / "data" / "stages" / "stage2_passed.csv",
    RELEASE_DIR / "data" / "stages" / "stage3_passed.csv",
]


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def compile_py(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def main() -> int:
    print("Scout Finance — Phase 7F release v0.7 package checker")
    print("=" * 88)

    for path in [SUMMARY_PATH, REPORT_PATH, MANIFEST_PATH]:
        if not path.exists():
            fail(f"Missing file: {path}")
            return 1
        ok(f"File exists: {path}")

    if not RELEASE_DIR.exists():
        fail(f"Release dir missing: {RELEASE_DIR}")
        return 1
    ok(f"Release dir exists: {RELEASE_DIR}")

    for path in REQUIRED_RELEASE_FILES:
        if not path.exists():
            fail(f"Missing release artifact: {path}")
            return 1
        ok(f"Release artifact exists: {path}")

    app_ok, app_error = compile_py(RELEASE_DIR / "app.py")
    if not app_ok:
        fail(f"Release app.py does not compile: {app_error}")
        return 1
    ok("Release app.py compiles")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    if summary.get("phase") != "7F":
        fail(f"Summary phase is not 7F: {summary.get('phase')}")
        return 1
    ok("Summary phase is 7F")

    if summary.get("status") != "OK":
        fail(f"Summary status is not OK: {summary.get('status')}")
        return 1
    ok("Summary status OK")

    if summary.get("ready_for_freeze") is not True:
        fail("ready_for_freeze is not True")
        return 1
    ok("ready_for_freeze=True")

    counts = summary.get("counts", {})
    for key, expected in {
        "stage1_passed": 182,
        "stage2_passed": 63,
        "stage3_passed": 6,
    }.items():
        if counts.get(key) != expected:
            fail(f"{key} mismatch: {counts.get(key)} != {expected}")
            return 1
        ok(f"{key} OK: {expected}")

    stage1 = count_csv(RELEASE_DIR / "data" / "stages" / "stage1_passed.csv")
    stage2 = count_csv(RELEASE_DIR / "data" / "stages" / "stage2_passed.csv")
    stage3 = count_csv(RELEASE_DIR / "data" / "stages" / "stage3_passed.csv")
    ranking = count_csv(RELEASE_DIR / "outputs" / "scouting" / "stage3_candidates_for_ranking.csv")

    if (stage1, stage2, stage3) != (182, 63, 6):
        fail(f"Release CSV counts mismatch: {(stage1, stage2, stage3)}")
        return 1
    ok("Release CSV counts OK: 182 / 63 / 6")

    if ranking < 10:
        fail(f"Ranking rows too low: {ranking}")
        return 1
    ok(f"Ranking rows OK: {ranking}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("release") != "v0.7.0-candidate":
        fail(f"Unexpected manifest release: {manifest.get('release')}")
        return 1
    ok("Manifest release OK")

    if manifest.get("validated_funnel") != "500 → 182 → 63 → 6":
        fail(f"Unexpected manifest funnel: {manifest.get('validated_funnel')}")
        return 1
    ok("Manifest funnel OK")

    for flag, expected, label in [
        ("openai_called", False, "OpenAI was not called"),
        ("api_called", False, "External API was not called"),
        ("yfinance_called", False, "yfinance was not called"),
        ("app_modified", False, "root app.py was not modified"),
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
    ok("Phase 7F release v0.7 package is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
