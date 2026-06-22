
from __future__ import annotations

import ast
import json
import py_compile
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

RELEASE_DIR = ROOT / "releases" / "v0.7"
RELEASE_SRC_DIR = RELEASE_DIR / "src"
RELEASE_SCRIPTS_DIR = RELEASE_DIR / "scripts"
RELEASE_DOCS_DIR = RELEASE_DIR / "docs" / "phase7"
RELEASE_OUTPUTS_DIR = RELEASE_DIR / "outputs" / "scouting"
RELEASE_DATA_STAGES_DIR = RELEASE_DIR / "data" / "stages"

OUT_DIR = ROOT / "outputs" / "scouting"
DATA_STAGES = ROOT / "data" / "stages"

SUMMARY_PATH = OUT_DIR / "phase7f_release_v07_packaging_summary.json"
REPORT_PATH = OUT_DIR / "phase7f_release_v07_packaging_report.md"
MANIFEST_PATH = RELEASE_DIR / "manifest_v0.7.json"

VERSION_TEXT = "0.7.0-candidate\n"

KEY_OUTPUTS = [
    "phase7e_v07_release_checkpoint_summary.json",
    "phase7e_v07_release_checkpoint_report.md",
    "phase7e_v07_release_checkpoint_evidence.csv",
    "phase7c4_pipeline_revalidation_summary.json",
    "phase7c4_pipeline_revalidation_report.md",
    "phase7c4_pipeline_revalidation_evidence.csv",
    "phase7c4_pipeline_revalidation_top_candidates.csv",
    "active_pipeline_policy_status.json",
    "stage1_balanced_official_closure_summary.json",
    "stage2_yfinance_policy_implementation_summary.json",
    "stage3_summary.json",
    "top_20_deep_research.csv",
    "top_50_watchlist.csv",
    "top_100_candidates.csv",
    "stage3_candidates_for_ranking.csv",
    "fundamentals_yfinance_enrichment_summary.json",
    "fundamentals_yfinance_enrichment_report.md",
]

KEY_STAGE_FILES = [
    "stage1_passed.csv",
    "stage1_watchlist.csv",
    "stage1_rejected.csv",
    "stage2_passed.csv",
    "stage2_watchlist.csv",
    "stage2_rejected.csv",
    "stage3_passed.csv",
    "stage3_watchlist.csv",
    "stage3_rejected.csv",
    "stage3_rejection_log.csv",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def warn(msg: str) -> None:
    print(f"WARN {msg}")


def compile_py(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def copy_file(src: Path, dst: Path, *, required: bool = True) -> dict:
    dst.parent.mkdir(parents=True, exist_ok=True)
    exists = src.exists()
    copied = False
    error = None

    if exists:
        try:
            shutil.copy2(src, dst)
            copied = True
        except Exception as exc:
            error = str(exc)
    elif required:
        error = "missing required source"

    return {
        "source": str(src),
        "target": str(dst),
        "exists": exists,
        "copied": copied,
        "required": required,
        "error": error,
        "size_bytes": dst.stat().st_size if dst.exists() else 0,
    }


def copy_tree_selected(src: Path, dst: Path, *, exclude_names: set[str] | None = None) -> list[dict]:
    exclude_names = exclude_names or set()
    copied = []

    if not src.exists():
        return copied

    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        if any(part in exclude_names for part in rel.parts):
            continue
        if "__pycache__" in rel.parts:
            continue
        if path.suffix.lower() in {".pyc", ".pyo"}:
            continue

        target = dst / rel
        copied.append(copy_file(path, target, required=False))

    return copied


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_release_docs() -> None:
    changelog = """# Changelog — Scout Finance v0.7 candidate

## Added

- Real pilot funnel release candidate.
- Validated institutional universe pipeline.
- Stage 1 Balanced official policy integrated.
- Stage 2 yfinance-aligned provider-limitation policy integrated.
- Stage 3 scoring outputs integrated.
- Dashboard now displays the validated funnel: `500 → 182 → 63 → 6`.
- Dashboard hotfixes included:
  - 7D.1 dashboard helper/render order fix.
  - 7D.2 institutional universe Count/Nº fix.
  - 7D.3b fundamental coverage exact fix.

## Changed

- Fundamental coverage dashboard now reflects 7C.1 yfinance enrichment:
  - Stage 1 passed: 182
  - Fundamentals matched: 182
  - Coverage: 83.17%
  - Runner phase: 7C.1
- Stage 2 no longer blocks clean pass solely on missing `shares_dilution_3y` when absent due to provider limitation.

## Validated funnel

```text
500 → 182 → 63 → 6
```

## Top candidate

```text
AUPH — Aurinia Pharmaceuticals Inc - Common Shares — score 70.83
```

## Notes

This is a candidate release. It packages validated code and evidence; it does not call OpenAI, yfinance, or external APIs during packaging.
"""

    release_notes = """# Release Notes — Scout Finance v0.7 candidate

## Summary

Scout Finance v0.7 candidate freezes the first real pilot institutional funnel.

The release includes:

```text
Institutional universe → Stage 1 Balanced → Stage 2 yfinance-aligned → Stage 3 scoring
```

Validated funnel:

```text
500 → 182 → 63 → 6
```

## Included evidence

- Stage 1 closure evidence.
- Stage 2 yfinance policy implementation evidence.
- Stage 3 scoring evidence.
- Dashboard integration evidence.
- 7E.1 v0.7 release checkpoint evidence.

## Important policy note

Missing `shares_dilution_3y` from yfinance is treated as a provider limitation warning, not as an automatic clean-pass blocker.

Dilution is not ignored. It remains pending for stronger sources such as SEC/companyfacts or direct filings.

## Candidate status

```text
Ready for v0.7 release packaging: True
```
"""

    (RELEASE_DIR / "VERSION").write_text(VERSION_TEXT, encoding="utf-8")
    (RELEASE_DIR / "CHANGELOG_v0.7.md").write_text(changelog, encoding="utf-8")
    (RELEASE_DIR / "RELEASE_NOTES_v0.7.md").write_text(release_notes, encoding="utf-8")


def build_manifest(summary: dict) -> dict:
    files = []
    for path in RELEASE_DIR.rglob("*"):
        if path.is_file():
            rel = path.relative_to(RELEASE_DIR).as_posix()
            files.append({
                "path": rel,
                "size_bytes": path.stat().st_size,
            })

    return {
        "release": "v0.7.0-candidate",
        "created_at": utc_now(),
        "validated_funnel": "500 → 182 → 63 → 6",
        "stage_counts": {
            "stage1_passed": 182,
            "stage2_passed": 63,
            "stage3_passed": 6,
        },
        "top_candidate": {
            "ticker": "AUPH",
            "name": "Aurinia Pharmaceuticals Inc - Common Shares",
            "score": 70.83,
        },
        "source_summary": summary,
        "files": files,
    }


def render_report(summary: dict) -> str:
    return f"""# Scout Finance — Phase 7F package release v0.7 candidate

Generated at: `{summary["created_at"]}`

## Status

- Packaging status: **{summary["status"]}**
- Release directory: `{summary["release_dir"]}`
- Ready for freeze: **{summary["ready_for_freeze"]}**

## Validated funnel

```text
500 → 182 → 63 → 6
```

## Counts

| Item | Count |
|---|---:|
| Stage 1 passed | {summary["counts"]["stage1_passed"]} |
| Stage 2 passed | {summary["counts"]["stage2_passed"]} |
| Stage 3 passed | {summary["counts"]["stage3_passed"]} |
| Stage 3 candidates for ranking | {summary["counts"]["stage3_candidates_for_ranking"]} |

## Packaged artifacts

- `VERSION`
- `CHANGELOG_v0.7.md`
- `RELEASE_NOTES_v0.7.md`
- `manifest_v0.7.json`
- `app.py`
- `src/`
- `scripts/`
- `docs/phase7/`
- `outputs/scouting/`
- `data/stages/`

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified in project root: `{summary["app_modified"]}`
- filters modified: `{summary["filters_modified"]}`
- release modified: `{summary["release_modified"]}`

## Next phase

```text
{summary["recommended_next_phase"]}
```
"""


def main() -> int:
    print("Scout Finance — Phase 7F package release v0.7 candidate")
    print("=" * 88)

    # Preflight: app compiles.
    app_path = ROOT / "app.py"
    app_ok, app_error = compile_py(app_path)
    if not app_ok:
        fail(f"app.py does not compile: {app_error}")
        return 1
    ok("app.py compiles")

    checkpoint = read_json(OUT_DIR / "phase7e_v07_release_checkpoint_summary.json")
    if checkpoint.get("ready_for_v07_release") is not True:
        fail("7E.1 checkpoint does not mark ready_for_v07_release=True")
        return 1
    ok("7E.1 checkpoint ready_for_v07_release=True")

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_SRC_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_DATA_STAGES_DIR.mkdir(parents=True, exist_ok=True)

    copied = []

    # Root app.
    copied.append(copy_file(ROOT / "app.py", RELEASE_DIR / "app.py", required=True))

    # Main project code/docs/scripts.
    copied.extend(copy_tree_selected(ROOT / "src", RELEASE_SRC_DIR))
    copied.extend(copy_tree_selected(ROOT / "scripts", RELEASE_SCRIPTS_DIR))
    copied.extend(copy_tree_selected(ROOT / "docs" / "phase7", RELEASE_DOCS_DIR))

    # Key evidence outputs only.
    for name in KEY_OUTPUTS:
        copied.append(copy_file(OUT_DIR / name, RELEASE_OUTPUTS_DIR / name, required=True))

    # Key stage files.
    for name in KEY_STAGE_FILES:
        copied.append(copy_file(DATA_STAGES / name, RELEASE_DATA_STAGES_DIR / name, required=True))

    write_release_docs()

    stage1_passed = count_csv(RELEASE_DATA_STAGES_DIR / "stage1_passed.csv")
    stage2_passed = count_csv(RELEASE_DATA_STAGES_DIR / "stage2_passed.csv")
    stage3_passed = count_csv(RELEASE_DATA_STAGES_DIR / "stage3_passed.csv")
    ranking_rows = count_csv(RELEASE_OUTPUTS_DIR / "stage3_candidates_for_ranking.csv")

    required_copy_ok = all(item["copied"] for item in copied if item["required"])
    counts_ok = stage1_passed == 182 and stage2_passed == 63 and stage3_passed == 6 and ranking_rows >= 10

    summary = {
        "phase": "7F",
        "status": "OK" if required_copy_ok and counts_ok else "REVIEW",
        "created_at": utc_now(),
        "release": "v0.7.0-candidate",
        "release_dir": str(RELEASE_DIR),
        "ready_for_freeze": bool(required_copy_ok and counts_ok),
        "counts": {
            "stage1_passed": stage1_passed,
            "stage2_passed": stage2_passed,
            "stage3_passed": stage3_passed,
            "stage3_candidates_for_ranking": ranking_rows,
        },
        "copy_results": copied,
        "checks": {
            "app_compiles": app_ok,
            "checkpoint_ready": checkpoint.get("ready_for_v07_release") is True,
            "required_copy_ok": required_copy_ok,
            "counts_ok": counts_ok,
        },
        "manifest_path": str(MANIFEST_PATH),
        "recommended_next_phase": "7F.1 — Validate release v0.7 package integrity",
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": True,
    }

    manifest = build_manifest(summary)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Release package")
    print("-" * 88)
    print(f"Status: {summary['status']}")
    print(f"Release dir: {RELEASE_DIR}")
    print(f"Ready for freeze: {summary['ready_for_freeze']}")

    print()
    print("Counts")
    print("-" * 88)
    for key, value in summary["counts"].items():
        print(f"{key}: {value}")

    print()
    print("Next")
    print("-" * 88)
    print(summary["recommended_next_phase"])

    return 0 if summary["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
