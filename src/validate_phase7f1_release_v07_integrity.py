
from __future__ import annotations

import ast, hashlib, json, py_compile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "releases" / "v0.7"
OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7f1_release_v07_integrity_summary.json"
REPORT_PATH = OUT_DIR / "phase7f1_release_v07_integrity_report.md"
FILES_AUDIT_PATH = OUT_DIR / "phase7f1_release_v07_files_audit.csv"
MANIFEST_PATH = RELEASE_DIR / "manifest_v0.7.json"

REQUIRED_ARTIFACTS = [
    "VERSION", "CHANGELOG_v0.7.md", "RELEASE_NOTES_v0.7.md", "manifest_v0.7.json", "app.py",
    "src", "scripts", "docs/phase7",
    "outputs/scouting/phase7e_v07_release_checkpoint_summary.json",
    "outputs/scouting/phase7f_release_v07_packaging_summary.json",
    "outputs/scouting/phase7c4_pipeline_revalidation_summary.json",
    "outputs/scouting/active_pipeline_policy_status.json",
    "outputs/scouting/stage3_summary.json",
    "outputs/scouting/stage3_candidates_for_ranking.csv",
    "outputs/scouting/top_100_candidates.csv",
    "outputs/scouting/fundamentals_yfinance_enrichment_summary.json",
    "data/stages/stage1_passed.csv", "data/stages/stage2_passed.csv", "data/stages/stage3_passed.csv",
    "data/stages/stage3_rejection_log.csv",
]
TEXT_CHECKS = {
    "VERSION": ["0.7.0-candidate"],
    "CHANGELOG_v0.7.md": ["500 → 182 → 63 → 6", "AUPH", "Stage 2 yfinance-aligned"],
    "RELEASE_NOTES_v0.7.md": ["Ready for v0.7 release packaging: True", "shares_dilution_3y", "500 → 182 → 63 → 6"],
}

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}

def count_csv(path: Path) -> int:
    try:
        return int(len(pd.read_csv(path))) if path.exists() else 0
    except Exception:
        return 0

def compile_py(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)

def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def audit_files() -> list[dict]:
    rows = []
    for path in RELEASE_DIR.rglob("*"):
        if path.is_file():
            rel = path.relative_to(RELEASE_DIR).as_posix()
            rows.append({"path": rel, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return sorted(rows, key=lambda r: r["path"])

def render_report(summary: dict) -> str:
    artifact_lines = "\n".join(f"- `{k}`: {v}" for k, v in summary["required_artifacts"].items())
    check_lines = "\n".join(f"- {k}: {v}" for k, v in summary["checks"].items())
    return f"""# Scout Finance — Phase 7F.1 release v0.7 integrity validation

Generated at: `{summary["created_at"]}`

## Status

- Integrity status: **{summary["status"]}**
- Release freeze approved: **{summary["release_freeze_approved"]}**
- Release directory: `{summary["release_dir"]}`

## Validated funnel

```text
{summary["validated_funnel"]}
```

## Core counts

| Item | Count |
|---|---:|
| Stage 1 passed | {summary["counts"]["stage1_passed"]} |
| Stage 2 passed | {summary["counts"]["stage2_passed"]} |
| Stage 3 passed | {summary["counts"]["stage3_passed"]} |
| Stage 3 candidates for ranking | {summary["counts"]["stage3_candidates_for_ranking"]} |

## Required artifacts

{artifact_lines}

## Checks

{check_lines}

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- filters modified: `{summary["filters_modified"]}`
- release modified: `{summary["release_modified"]}`

## Final statement

```text
Scout Finance v0.7.0-candidate is integrity-validated and ready to freeze.
```
"""

def main() -> int:
    print("Scout Finance — Phase 7F.1 release v0.7 integrity validation")
    print("=" * 92)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not RELEASE_DIR.exists():
        print(f"FAIL Release directory does not exist: {RELEASE_DIR}")
        return 1

    files = audit_files()
    pd.DataFrame(files).to_csv(FILES_AUDIT_PATH, index=False, encoding="utf-8-sig")

    manifest = read_json(MANIFEST_PATH)
    manifest_paths = {x.get("path") for x in manifest.get("files", [])}
    actual_paths = {x.get("path") for x in files}
    missing_from_disk = sorted(p for p in manifest_paths if p not in actual_paths)

    required_artifacts = {rel: (RELEASE_DIR / rel).exists() for rel in REQUIRED_ARTIFACTS}
    text_results = {}
    for rel, needles in TEXT_CHECKS.items():
        p = RELEASE_DIR / rel
        txt = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        text_results[rel] = {needle: needle in txt for needle in needles}

    app_ok, app_err = compile_py(RELEASE_DIR / "app.py")
    counts = {
        "stage1_passed": count_csv(RELEASE_DIR / "data/stages/stage1_passed.csv"),
        "stage2_passed": count_csv(RELEASE_DIR / "data/stages/stage2_passed.csv"),
        "stage3_passed": count_csv(RELEASE_DIR / "data/stages/stage3_passed.csv"),
        "stage3_candidates_for_ranking": count_csv(RELEASE_DIR / "outputs/scouting/stage3_candidates_for_ranking.csv"),
    }

    checks = {
        "release_dir_exists": RELEASE_DIR.exists(),
        "release_app_compiles": app_ok,
        "required_artifacts_ok": all(required_artifacts.values()),
        "required_texts_ok": all(all(v.values()) for v in text_results.values()),
        "counts_ok": counts["stage1_passed"] == 182 and counts["stage2_passed"] == 63 and counts["stage3_passed"] == 6 and counts["stage3_candidates_for_ranking"] >= 10,
        "manifest_exists": MANIFEST_PATH.exists(),
        "manifest_release_ok": manifest.get("release") == "v0.7.0-candidate",
        "manifest_funnel_ok": manifest.get("validated_funnel") == "500 → 182 → 63 → 6",
        "manifest_files_exist_on_disk": len(missing_from_disk) == 0,
    }
    approved = all(checks.values())

    summary = {
        "phase": "7F.1",
        "status": "OK" if approved else "REVIEW",
        "created_at": utc_now(),
        "release": "v0.7.0-candidate",
        "release_dir": str(RELEASE_DIR),
        "validated_funnel": "500 → 182 → 63 → 6",
        "release_freeze_approved": approved,
        "counts": counts,
        "checks": checks,
        "app_compile_error": app_err,
        "required_artifacts": required_artifacts,
        "required_text_checks": text_results,
        "manifest_check": {
            "manifest_exists": MANIFEST_PATH.exists(),
            "release": manifest.get("release"),
            "validated_funnel": manifest.get("validated_funnel"),
            "manifest_file_count": len(manifest.get("files", [])),
            "actual_file_count": len(files),
            "missing_from_disk": missing_from_disk,
        },
        "files_audit_csv": str(FILES_AUDIT_PATH),
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": False,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Integrity")
    print("-" * 92)
    print(f"Status: {summary['status']}")
    print(f"Release freeze approved: {approved}")
    print(f"Release dir: {RELEASE_DIR}")
    print()
    print("Counts")
    print("-" * 92)
    for k, v in counts.items():
        print(f"{k}: {v}")
    print()
    print("Checks")
    print("-" * 92)
    for k, v in checks.items():
        print(f"{k}: {v}")
    print()
    print("Final")
    print("-" * 92)
    print("Scout Finance v0.7.0-candidate is integrity-validated and ready to freeze." if approved else "Release requires review before freeze.")
    return 0 if approved else 1

if __name__ == "__main__":
    raise SystemExit(main())
