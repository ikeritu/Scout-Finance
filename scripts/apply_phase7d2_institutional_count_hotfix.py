
from __future__ import annotations

import ast
import json
import py_compile
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = ROOT / "app.py"
BACKUP_PATH = ROOT / "app_before_phase7d2_institutional_count_hotfix.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "phase7d2_institutional_count_hotfix_summary.json"
REPORT_PATH = OUT_DIR / "phase7d2_institutional_count_hotfix_report.md"

PATCH_MARKER = "# PHASE 7D.2 INSTITUTIONAL COUNT HOTFIX APPLIED"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")


def warn(msg: str) -> None:
    print(f"WARN {msg}")


def compile_file(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def patch_app(text: str) -> tuple[str, list[str]]:
    if PATCH_MARKER in text:
        return text, ["ALREADY_APPLIED"]

    target_function = "def _render_institutional_universe_dashboard"
    start = text.find(target_function)
    if start == -1:
        raise RuntimeError("Could not find _render_institutional_universe_dashboard in app.py")

    next_def = text.find("\ndef ", start + len(target_function))
    if next_def == -1:
        next_def = len(text)

    before = text[:start]
    block = text[start:next_def]
    after = text[next_def:]

    old = '.sort_values("Count", ascending=False)'
    new = '.sort_values("Nº", ascending=False)'

    count = block.count(old)
    if count < 1:
        # fallback for single quotes
        old_alt = ".sort_values('Count', ascending=False)"
        new_alt = ".sort_values('Nº', ascending=False)"
        count_alt = block.count(old_alt)
        if count_alt < 1:
            raise RuntimeError("Could not find sort_values('Count') inside _render_institutional_universe_dashboard")
        block = block.replace(old_alt, new_alt)
        changes = [f"REPLACED_SORT_COUNT_WITH_N_IN_INSTITUTIONAL_DASHBOARD_{count_alt}"]
    else:
        block = block.replace(old, new)
        changes = [f"REPLACED_SORT_COUNT_WITH_N_IN_INSTITUTIONAL_DASHBOARD_{count}"]

    patched = before + PATCH_MARKER + "\n" + block + after
    changes.append("PHASE7D2_MARKER_ADDED")
    return patched, changes


def render_report(summary: dict) -> str:
    changes = "\n".join("- " + str(change) for change in summary["changes"])
    return f"""# Scout Finance — Phase 7D.2 institutional Count/Nº hotfix

Generated at: `{summary["created_at"]}`

## Result

- Status: **{summary["status"]}**
- app.py modified: **{summary["app_modified"]}**
- Backup: `{summary["backup_path"]}`

## Problem fixed

The institutional universe dashboard displayed a table using the Spanish count column:

```text
Nº
```

but attempted to sort by:

```text
Count
```

This caused:

```text
KeyError: 'Count'
```

## Applied changes

{changes}

## Rollback

```powershell
.\\.venv\\Scripts\\python.exe scripts/rollback_phase7d2_institutional_count_hotfix.py
```

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- filters modified: `{summary["filters_modified"]}`
- release modified: `{summary["release_modified"]}`
"""


def main() -> int:
    print("Scout Finance — Phase 7D.2 institutional Count/Nº hotfix")
    print("=" * 84)

    if not APP_PATH.exists():
        fail(f"Missing app.py: {APP_PATH}")
        return 1

    good, error = compile_file(APP_PATH)
    if not good:
        fail(f"app.py does not compile before hotfix: {error}")
        return 1
    ok("app.py compiles before hotfix")

    if not BACKUP_PATH.exists():
        shutil.copy2(APP_PATH, BACKUP_PATH)
        backup_created = True
        ok(f"Backup created: {BACKUP_PATH}")
    else:
        backup_created = False
        ok(f"Backup already exists: {BACKUP_PATH}")

    original = APP_PATH.read_text(encoding="utf-8", errors="replace")

    try:
        patched, changes = patch_app(original)
    except Exception as exc:
        fail(str(exc))
        return 1

    APP_PATH.write_text(patched, encoding="utf-8")

    good, error = compile_file(APP_PATH)
    if not good:
        fail(f"app.py does not compile after hotfix: {error}")
        shutil.copy2(BACKUP_PATH, APP_PATH)
        warn("Rollback restored app.py from backup")
        return 1
    ok("app.py compiles after hotfix")

    summary = {
        "phase": "7D.2",
        "status": "OK",
        "created_at": utc_now(),
        "backup_path": str(BACKUP_PATH),
        "backup_created": backup_created,
        "changes": changes,
        "fixed_error": "KeyError: 'Count'",
        "app_modified": True,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "filters_modified": False,
        "release_modified": False,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Hotfix")
    print("-" * 84)
    print(f"Changes: {changes}")
    ok("Phase 7D.2 institutional Count/Nº hotfix applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
