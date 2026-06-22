
from __future__ import annotations

import ast
import json
import py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = PROJECT_ROOT / "releases" / "v0.6"
MANIFEST_PATH = RELEASE_DIR / "RELEASE_MANIFEST_v0_6.json"

REQUIRED_RELEASE_FILES = [
    "app.py", "app_v0_6_stable.py", "README.md", "CHANGELOG.md", "VERSION.md",
    "requirements.txt", "VERSION_RELEASE_v0_6.md", "RELEASE_MANIFEST_v0_6.json",
]

REQUIRED_RELEASE_DIRS = ["src", "scripts"]

REQUIRED_APP_MARKERS = [
    "🧭 Candidatos Stage 3",
    "🧭 Embudo global de scouting",
    "🧬 Cobertura de fundamentales",
    "_render_stage3_candidates_tab",
    "_render_global_funnel_summary_dashboard",
    "_render_fundamental_enrichment_dashboard",
]

REQUIRED_PHASE6_FILES = [
    "src/prepare_real_universe_csv.py",
    "src/fundamental_coverage_report.py",
    "src/prepare_fundamentals_csv.py",
    "src/run_stage2_filter_enriched.py",
    "src/run_global_funnel_demo.py",
    "scripts/check_phase6a_real_universe.py",
    "scripts/check_phase6b_fundamental_coverage.py",
    "scripts/check_phase6c_fundamentals_enrichment.py",
    "scripts/check_phase6d_stage2_enriched.py",
    "scripts/check_phase6e_clean_global_runner.py",
    "scripts/check_phase6f_dashboard.py",
]


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def main() -> int:
    print("Scout Finance — Phase 6G release v0.6 checker")
    print("=" * 62)

    if not RELEASE_DIR.exists():
        fail(f"Release directory missing: {RELEASE_DIR}")
        return 1
    ok(f"Release directory exists: {RELEASE_DIR}")

    for relative_path in REQUIRED_RELEASE_FILES:
        if not (RELEASE_DIR / relative_path).exists():
            fail(f"Missing release file: {relative_path}")
            return 1
        ok(f"Release file exists: {relative_path}")

    for relative_path in REQUIRED_RELEASE_DIRS:
        path = RELEASE_DIR / relative_path
        if not path.exists() or not path.is_dir():
            fail(f"Missing release directory: {relative_path}")
            return 1
        ok(f"Release directory exists: {relative_path}")

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Cannot read manifest: {exc}")
        return 1

    if manifest.get("release") != "v0.6":
        fail("Manifest release is not v0.6")
        return 1
    ok("Manifest release is v0.6")

    if manifest.get("openai_called") is False:
        ok("Manifest confirms OpenAI was not called")
    else:
        fail("Manifest indicates OpenAI was called")
        return 1

    if manifest.get("api_called") is False:
        ok("Manifest confirms external API was not called")
    else:
        fail("Manifest indicates external API was called")
        return 1

    app_path = RELEASE_DIR / "app.py"
    try:
        py_compile.compile(str(app_path), doraise=True)
        ok("Release app.py compiles")
    except Exception as exc:
        fail(f"Release app.py does not compile: {exc}")
        return 1

    content = app_path.read_text(encoding="utf-8", errors="replace")
    ast.parse(content)

    missing_markers = [marker for marker in REQUIRED_APP_MARKERS if marker not in content]
    if missing_markers:
        fail("Missing app markers in release:")
        for marker in missing_markers:
            print(f"   - {marker}")
        return 1
    ok("Release app contains Phase 5/6 Dashboard markers")

    for relative_path in REQUIRED_PHASE6_FILES:
        if not (RELEASE_DIR / relative_path).exists():
            fail(f"Missing required Phase 6 file in release: {relative_path}")
            return 1
        ok(f"Required Phase 6 file exists: {relative_path}")

    print("\nResult")
    print("-" * 62)
    ok("Release v0.6 is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
