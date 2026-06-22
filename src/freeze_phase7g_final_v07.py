
from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RELEASE_DIR = ROOT / "releases" / "v0.7"
OUT_DIR = ROOT / "outputs" / "scouting"

LOCK_PATH = RELEASE_DIR / "RELEASE_LOCK_v0.7.json"
FREEZE_REPORT_RELEASE_PATH = RELEASE_DIR / "FREEZE_REPORT_v0.7.md"

ZIP_PATH = ROOT / "releases" / "Scout_Finance_v0.7.0_candidate_FREEZE.zip"

SUMMARY_PATH = OUT_DIR / "phase7g_freeze_final_v07_summary.json"
REPORT_PATH = OUT_DIR / "phase7g_freeze_final_v07_report.md"

INTEGRITY_SUMMARY_PATH = OUT_DIR / "phase7f1_release_v07_integrity_summary.json"
MANIFEST_PATH = RELEASE_DIR / "manifest_v0.7.json"

REQUIRED_IN_ZIP = [
    "VERSION",
    "CHANGELOG_v0.7.md",
    "RELEASE_NOTES_v0.7.md",
    "RELEASE_LOCK_v0.7.json",
    "FREEZE_REPORT_v0.7.md",
    "manifest_v0.7.json",
    "app.py",
    "outputs/scouting/phase7f1_release_v07_integrity_summary.json",
    "outputs/scouting/phase7c4_pipeline_revalidation_summary.json",
    "outputs/scouting/stage3_candidates_for_ranking.csv",
    "data/stages/stage1_passed.csv",
    "data/stages/stage2_passed.csv",
    "data/stages/stage3_passed.csv",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_release_files() -> list[dict]:
    rows = []
    for path in RELEASE_DIR.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(RELEASE_DIR).as_posix()
        rows.append({
            "path": rel,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return sorted(rows, key=lambda item: item["path"])


def write_freeze_report(lock: dict) -> str:
    return f"""# Scout Finance — v0.7.0-candidate FREEZE

Freeze created at: `{lock["freeze_created_at"]}`

## Status

```text
{lock["status"]}
```

## Release

```text
{lock["release"]}
```

## Release directory

```text
{lock["release_dir"]}
```

## Final validated funnel

```text
{lock["validated_funnel"]}
```

## Core counts

| Item | Count |
|---|---:|
| Stage 1 passed | {lock["counts"]["stage1_passed"]} |
| Stage 2 passed | {lock["counts"]["stage2_passed"]} |
| Stage 3 passed | {lock["counts"]["stage3_passed"]} |
| Stage 3 candidates for ranking | {lock["counts"]["stage3_candidates_for_ranking"]} |

## Top candidate

```text
{lock["top_candidate"]["ticker"]} — {lock["top_candidate"]["name"]} — score {lock["top_candidate"]["score"]}
```

## Integrity

```text
release_freeze_approved: {lock["integrity"]["release_freeze_approved"]}
integrity_status: {lock["integrity"]["status"]}
files_audit_rows: {lock["integrity"].get("files_audit_rows", "N/A")}
```

## Controls

- OpenAI called: `False`
- API called: `False`
- yfinance called: `False`
- app.py root modified: `False`
- filters modified: `False`
- pipeline recalculated: `False`

## Final declaration

```text
Scout Finance v0.7.0-candidate is frozen.
This release packages the validated real pilot funnel 500 → 182 → 63 → 6.
```
"""


def make_zip() -> tuple[bool, str, int]:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for path in RELEASE_DIR.rglob("*"):
            if path.is_file():
                z.write(path, arcname=f"Scout_Finance_v0.7/{path.relative_to(RELEASE_DIR).as_posix()}")
                count += 1

    return ZIP_PATH.exists(), sha256_file(ZIP_PATH) or "", count


def validate_zip() -> tuple[bool, list[str]]:
    if not ZIP_PATH.exists():
        return False, REQUIRED_IN_ZIP

    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        names = set(z.namelist())

    missing = []
    for rel in REQUIRED_IN_ZIP:
        zip_rel = f"Scout_Finance_v0.7/{rel}"
        if zip_rel not in names:
            missing.append(rel)

    return len(missing) == 0, missing


def main() -> int:
    print("Scout Finance — Phase 7G freeze final v0.7")
    print("=" * 88)

    if not RELEASE_DIR.exists():
        fail(f"Missing release directory: {RELEASE_DIR}")
        return 1
    ok(f"Release directory exists: {RELEASE_DIR}")

    integrity = read_json(INTEGRITY_SUMMARY_PATH)
    if integrity.get("release_freeze_approved") is not True:
        fail("7F.1 integrity summary does not approve release freeze")
        return 1
    ok("7F.1 integrity summary approves release freeze")

    manifest = read_json(MANIFEST_PATH)
    if manifest.get("validated_funnel") != "500 → 182 → 63 → 6":
        fail("Manifest funnel is not the validated funnel")
        return 1
    ok("Manifest funnel OK")

    release_files_before_lock = collect_release_files()

    lock = {
        "phase": "7G",
        "release": "v0.7.0-candidate",
        "status": "FROZEN",
        "freeze_created_at": utc_now(),
        "release_dir": str(RELEASE_DIR),
        "validated_funnel": "500 → 182 → 63 → 6",
        "counts": {
            "stage1_passed": 182,
            "stage2_passed": 63,
            "stage3_passed": 6,
            "stage3_candidates_for_ranking": 34,
        },
        "top_candidate": {
            "ticker": "AUPH",
            "name": "Aurinia Pharmaceuticals Inc - Common Shares",
            "score": 70.83,
        },
        "integrity": {
            "summary_path": str(INTEGRITY_SUMMARY_PATH),
            "status": integrity.get("status"),
            "release_freeze_approved": integrity.get("release_freeze_approved"),
            "files_audit_rows": len(release_files_before_lock),
        },
        "controls": {
            "openai_called": False,
            "api_called": False,
            "yfinance_called": False,
            "app_modified": False,
            "filters_modified": False,
            "pipeline_recalculated": False,
        },
    }

    LOCK_PATH.write_text(json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8")
    FREEZE_REPORT_RELEASE_PATH.write_text(write_freeze_report(lock), encoding="utf-8")
    ok("Release lock and freeze report written")

    zip_ok, zip_hash, zip_file_count = make_zip()
    if not zip_ok:
        fail("Freeze ZIP was not created")
        return 1
    ok(f"Freeze ZIP created: {ZIP_PATH}")

    zip_valid, missing = validate_zip()
    if not zip_valid:
        fail(f"Freeze ZIP missing required files: {missing}")
        return 1
    ok("Freeze ZIP contains required files")

    release_files_after_lock = collect_release_files()

    summary = {
        "phase": "7G",
        "status": "OK",
        "release": "v0.7.0-candidate",
        "freeze_status": "FROZEN",
        "created_at": utc_now(),
        "release_dir": str(RELEASE_DIR),
        "zip_path": str(ZIP_PATH),
        "zip_sha256": zip_hash,
        "zip_file_count": zip_file_count,
        "release_file_count": len(release_files_after_lock),
        "validated_funnel": "500 → 182 → 63 → 6",
        "counts": lock["counts"],
        "top_candidate": lock["top_candidate"],
        "lock_path": str(LOCK_PATH),
        "freeze_report_release_path": str(FREEZE_REPORT_RELEASE_PATH),
        "zip_required_files_present": True,
        "zip_missing_required_files": [],
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "pipeline_recalculated": False,
        "release_modified": True,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(write_freeze_report(lock), encoding="utf-8")

    print()
    print("Freeze")
    print("-" * 88)
    print(f"Status: {summary['status']}")
    print(f"Freeze status: {summary['freeze_status']}")
    print(f"Release dir: {RELEASE_DIR}")
    print(f"ZIP: {ZIP_PATH}")
    print(f"ZIP sha256: {zip_hash}")
    print(f"ZIP files: {zip_file_count}")

    print()
    print("Final")
    print("-" * 88)
    print("Scout Finance v0.7.0-candidate is frozen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
