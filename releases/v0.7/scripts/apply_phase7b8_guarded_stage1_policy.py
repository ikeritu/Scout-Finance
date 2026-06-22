
from __future__ import annotations

import ast
import json
import py_compile
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "src" / "filter_stage1.py"
BACKUP = ROOT / "src" / "filter_stage1_before_phase7b8_balanced.py"
OUT = ROOT / "outputs" / "scouting"

SUMMARY = OUT / "stage1_balanced_guarded_implementation_summary.json"
REPORT = OUT / "stage1_balanced_guarded_implementation_report.md"
COMPARISON = OUT / "stage1_balanced_guarded_implementation_comparison.csv"

EXPECTED = {"passed": 182, "watchlist": 84, "rejected": 234}

STAGE1 = {
    "passed": ROOT / "data" / "stages" / "stage1_passed.csv",
    "watchlist": ROOT / "data" / "stages" / "stage1_watchlist.csv",
    "rejected": ROOT / "data" / "stages" / "stage1_rejected.csv",
}


BALANCED_CONSTANTS = {
    "MIN_MARKET_CAP": "150_000_000",
    "MIN_MARKET_CAP_USD": "150_000_000",
    "STAGE1_MIN_MARKET_CAP": "150_000_000",
    "WATCH_MARKET_CAP": "500_000_000",
    "WATCH_MARKET_CAP_USD": "500_000_000",
    "STAGE1_WATCH_MARKET_CAP": "500_000_000",
    "MIN_PRICE": "1.5",
    "MIN_SHARE_PRICE": "1.5",
    "STAGE1_MIN_PRICE": "1.5",
    "STRONG_PRICE_WATCH": "3.0",
    "PRICE_STRONG_WATCH": "3.0",
    "STAGE1_STRONG_PRICE_WATCH": "3.0",
    "WATCH_PRICE": "5.0",
    "WEAK_PRICE_WATCH": "5.0",
    "PRICE_WEAK_WATCH": "5.0",
    "STAGE1_WEAK_PRICE_WATCH": "5.0",
    "MIN_DOLLAR_VOLUME": "1_000_000",
    "MIN_DOLLAR_VOLUME_90D": "1_000_000",
    "STAGE1_MIN_DOLLAR_VOLUME": "1_000_000",
    "WATCH_DOLLAR_VOLUME": "5_000_000",
    "WATCH_DOLLAR_VOLUME_90D": "5_000_000",
    "STAGE1_WATCH_DOLLAR_VOLUME": "5_000_000",
}


def ok(msg): print(f"OK   {msg}")
def fail(msg): print(f"FAIL {msg}")
def warn(msg): print(f"WARN {msg}")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compile_file(path: Path):
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def patch_constants(text: str):
    changes = []
    for name, value in BALANCED_CONSTANTS.items():
        pattern = rf"^(\s*{re.escape(name)}\s*=\s*)([0-9_]+(?:\.[0-9]+)?)\s*$"
        text2, count = re.subn(pattern, rf"\g<1>{value}", text, count=1, flags=re.MULTILINE)
        if count:
            text = text2
            changes.append(f"{name}={value}")

    marker = "# PHASE 7B.8 BALANCED STAGE 1 POLICY APPLIED"
    if marker not in text:
        text = marker + "\n" + text
        changes.append("PHASE7B8_MARKER_ADDED")

    if not any("=" in c for c in changes if c != "PHASE7B8_MARKER_ADDED"):
        block_marker = "# PHASE 7B.8 BALANCED POLICY CONSTANTS"
        if block_marker not in text:
            text += (
                "\n\n"
                + block_marker
                + "\nPHASE7B8_MIN_MARKET_CAP = 150_000_000\n"
                + "PHASE7B8_WATCH_MARKET_CAP = 500_000_000\n"
                + "PHASE7B8_MIN_PRICE = 1.5\n"
                + "PHASE7B8_STRONG_PRICE_WATCH = 3.0\n"
                + "PHASE7B8_WEAK_PRICE_WATCH = 5.0\n"
                + "PHASE7B8_MIN_DOLLAR_VOLUME = 1_000_000\n"
                + "PHASE7B8_WATCH_DOLLAR_VOLUME = 5_000_000\n"
            )
            changes.append("PHASE7B8_POLICY_BLOCK_APPENDED")

    return text, changes


def run_stage1():
    exe = ROOT / ".venv" / "Scripts" / "python.exe"
    cmd = [str(exe) if exe.exists() else sys.executable, "-m", "src.run_stage1_filter"]
    result = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=180)
    return result.returncode == 0, (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")


def count_csv(path: Path):
    if not path.exists():
        return 0
    return len(pd.read_csv(path))


def write_report(summary: dict):
    actual = summary["actual"]
    text = f"""# Scout Finance — Phase 7B.8 Guarded Stage 1 Implementation

Generated at: `{summary['created_at']}`

## Result

- Status: **{summary['status']}**.
- Stage 1 run OK: **{summary['stage1_run_ok']}**.
- Matches dry-run: **{summary['matches_expected']}**.

## Counts

| Bucket | Expected dry-run | Actual after patch |
|---|---:|---:|
| Passed | {EXPECTED['passed']} | {actual.get('passed')} |
| Watchlist | {EXPECTED['watchlist']} | {actual.get('watchlist')} |
| Rejected | {EXPECTED['rejected']} | {actual.get('rejected')} |

## Rollback

```powershell
.\\.venv\\Scripts\\python.exe scripts/rollback_phase7b8_stage1_policy.py
```
"""
    REPORT.write_text(text, encoding="utf-8")


def main():
    print("Scout Finance — Phase 7B.8 guarded Stage 1 implementation")
    print("=" * 78)

    if not FILTER.exists():
        fail(f"Missing filter file: {FILTER}")
        return 1

    good, error = compile_file(FILTER)
    if not good:
        fail(f"filter_stage1.py does not compile before patch: {error}")
        return 1
    ok("filter_stage1.py compiles before patch")

    if not BACKUP.exists():
        shutil.copy2(FILTER, BACKUP)
        ok(f"Backup created: {BACKUP}")
        backup_created = True
    else:
        ok(f"Backup already exists: {BACKUP}")
        backup_created = False

    original = FILTER.read_text(encoding="utf-8", errors="replace")
    patched, changes = patch_constants(original)
    FILTER.write_text(patched, encoding="utf-8")

    good, error = compile_file(FILTER)
    if not good:
        fail(f"filter_stage1.py does not compile after patch: {error}")
        shutil.copy2(BACKUP, FILTER)
        warn("Rollback restored from backup")
        return 1
    ok("filter_stage1.py compiles after patch")
    ok(f"Changes applied: {changes}")

    stage1_ok, output = run_stage1()
    if not stage1_ok:
        fail("Stage 1 failed after patch")
        print(output)
        return 1
    ok("Stage 1 executed after patch")

    actual = {k: count_csv(v) for k, v in STAGE1.items()}
    rows = [{"bucket": k, "expected": EXPECTED[k], "actual": actual[k], "matches": EXPECTED[k] == actual[k]} for k in EXPECTED]
    pd.DataFrame(rows).to_csv(COMPARISON, index=False, encoding="utf-8-sig")

    matches = all(EXPECTED[k] == actual[k] for k in EXPECTED)
    summary = {
        "phase": "7B.8",
        "status": "OK" if matches else "MISMATCH",
        "created_at": utc_now(),
        "backup_path": str(BACKUP),
        "backup_created": backup_created,
        "changes": changes,
        "stage1_run_ok": stage1_ok,
        "stage1_output_tail": "\n".join(output.splitlines()[-20:]),
        "expected": EXPECTED,
        "actual": actual,
        "matches_expected": matches,
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "release_modified": False,
        "filter_modified": True,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary)

    print()
    print("Counts")
    print("-" * 78)
    print(f"Expected: {EXPECTED}")
    print(f"Actual:   {actual}")

    if matches:
        ok("Guarded implementation matches 7B.6 dry-run")
        return 0

    fail("Guarded implementation does not match 7B.6 dry-run")
    print("Run rollback if needed:")
    print(r".\.venv\Scripts\python.exe scripts/rollback_phase7b8_stage1_policy.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
