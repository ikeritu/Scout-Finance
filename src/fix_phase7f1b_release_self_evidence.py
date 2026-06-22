
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RELEASE_DIR = ROOT / "releases" / "v0.7"
RELEASE_OUTPUTS = RELEASE_DIR / "outputs" / "scouting"
MANIFEST_PATH = RELEASE_DIR / "manifest_v0.7.json"

ROOT_OUTPUTS = ROOT / "outputs" / "scouting"

SUMMARY_SRC = ROOT_OUTPUTS / "phase7f_release_v07_packaging_summary.json"
REPORT_SRC = ROOT_OUTPUTS / "phase7f_release_v07_packaging_report.md"

SUMMARY_DST = RELEASE_OUTPUTS / "phase7f_release_v07_packaging_summary.json"
REPORT_DST = RELEASE_OUTPUTS / "phase7f_release_v07_packaging_report.md"

FIX_SUMMARY_PATH = ROOT_OUTPUTS / "phase7f1b_release_self_evidence_fix_summary.json"
FIX_REPORT_PATH = ROOT_OUTPUTS / "phase7f1b_release_self_evidence_fix_report.md"

FILES_TO_ADD = [
    (SUMMARY_SRC, SUMMARY_DST, "outputs/scouting/phase7f_release_v07_packaging_summary.json"),
    (REPORT_SRC, REPORT_DST, "outputs/scouting/phase7f_release_v07_packaging_report.md"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def update_manifest(manifest: dict) -> tuple[dict, list[str]]:
    changes = []
    files = manifest.setdefault("files", [])

    existing = {entry.get("path"): entry for entry in files if isinstance(entry, dict)}

    for _, dst, rel in FILES_TO_ADD:
        entry = {
            "path": rel,
            "size_bytes": dst.stat().st_size if dst.exists() else 0,
            "sha256": sha256_file(dst),
        }

        if rel in existing:
            existing[rel].update(entry)
            changes.append(f"UPDATED_MANIFEST_ENTRY:{rel}")
        else:
            files.append(entry)
            changes.append(f"ADDED_MANIFEST_ENTRY:{rel}")

    manifest["updated_at"] = utc_now()
    manifest["self_evidence_fix"] = "7F.1b"
    return manifest, changes


def render_report(summary: dict) -> str:
    changes = "\n".join("- " + item for item in summary["changes"])
    copied = "\n".join(
        f"- `{item['relative_path']}`: copied={item['copied']} exists={item['exists_after']}"
        for item in summary["copied_files"]
    )

    return f"""# Scout Finance — Phase 7F.1b release self-evidence fix

Generated at: `{summary["created_at"]}`

## Status

- Status: **{summary["status"]}**
- Release directory: `{summary["release_dir"]}`

## Problem fixed

The v0.7 release package was valid, but the 7F packaging summary/report were generated after the release evidence copy step and were not included inside:

```text
releases/v0.7/outputs/scouting/
```

## Copied files

{copied}

## Manifest changes

{changes}

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- filters modified: `{summary["filters_modified"]}`
- release modified: `{summary["release_modified"]}`

## Next

```text
Re-run 7F.1 integrity validator.
```
"""


def main() -> int:
    print("Scout Finance — Phase 7F.1b release self-evidence fix")
    print("=" * 88)

    if not RELEASE_DIR.exists():
        fail(f"Release directory missing: {RELEASE_DIR}")
        return 1
    ok(f"Release directory exists: {RELEASE_DIR}")

    if not MANIFEST_PATH.exists():
        fail(f"Manifest missing: {MANIFEST_PATH}")
        return 1
    ok(f"Manifest exists: {MANIFEST_PATH}")

    RELEASE_OUTPUTS.mkdir(parents=True, exist_ok=True)

    copied_files = []
    for src, dst, rel in FILES_TO_ADD:
        if not src.exists():
            fail(f"Missing source evidence: {src}")
            return 1

        shutil.copy2(src, dst)
        copied_files.append({
            "source": str(src),
            "target": str(dst),
            "relative_path": rel,
            "copied": True,
            "exists_after": dst.exists(),
            "size_bytes": dst.stat().st_size if dst.exists() else 0,
            "sha256": sha256_file(dst),
        })
        ok(f"Copied {rel}")

    manifest = read_json(MANIFEST_PATH)
    manifest, manifest_changes = update_manifest(manifest)
    write_json(MANIFEST_PATH, manifest)
    ok("Manifest updated")

    all_copied = all(item["exists_after"] for item in copied_files)

    summary = {
        "phase": "7F.1b",
        "status": "OK" if all_copied else "REVIEW",
        "created_at": utc_now(),
        "release_dir": str(RELEASE_DIR),
        "copied_files": copied_files,
        "changes": manifest_changes,
        "release_self_evidence_complete": all_copied,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filters_modified": False,
        "release_modified": True,
    }

    FIX_SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    FIX_REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Self-evidence fix")
    print("-" * 88)
    print(f"Status: {summary['status']}")
    print(f"Copied files: {len(copied_files)}")
    print("Next: re-run 7F.1 integrity validator")

    return 0 if summary["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
