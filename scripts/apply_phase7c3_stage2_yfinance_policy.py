
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

FILTER_PATH = ROOT / "src" / "filter_stage2.py"
BACKUP_PATH = ROOT / "src" / "filter_stage2_before_phase7c3_yfinance_policy.py"

OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "stage2_yfinance_policy_implementation_summary.json"
REPORT_PATH = OUT_DIR / "stage2_yfinance_policy_implementation_report.md"
COMPARISON_PATH = OUT_DIR / "stage2_yfinance_policy_implementation_comparison.csv"

EXPECTED = {
    "passed": 63,
    "watchlist": 81,
    "rejected": 38,
}

STAGE2_PATHS = {
    "passed": ROOT / "data" / "stages" / "stage2_passed.csv",
    "watchlist": ROOT / "data" / "stages" / "stage2_watchlist.csv",
    "rejected": ROOT / "data" / "stages" / "stage2_rejected.csv",
}

PATCH_MARKER = "# PHASE 7C.3 YFINANCE STAGE 2 POLICY APPLIED"

OLD_BLOCK = """    # Dilution
    if shares_dilution_3y is None:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="MISSING_SHARES_DILUTION",
            reason_text="Shares dilution 3Y missing.",
            metric_name="shares_dilution_3y",
            metric_value=shares_dilution_3y,
            threshold="required for clean pass",
            severity="medium",
            recoverable=True,
        )
    elif shares_dilution_3y > cfg["max_shares_dilution_3y_watchlist"]:
"""

NEW_BLOCK = """    # Dilution
    if shares_dilution_3y is None:
        _add_reason(
            reasons,
            reason_code="MISSING_SHARES_DILUTION_PROVIDER_LIMITATION",
            reason_text="Shares dilution 3Y unavailable from the current free fundamentals provider; tracked as provider limitation, not as a clean-pass blocker.",
            metric_name="shares_dilution_3y",
            metric_value=shares_dilution_3y,
            threshold="provider limitation",
            severity="low",
            recoverable=True,
        )
    elif shares_dilution_3y > cfg["max_shares_dilution_3y_watchlist"]:
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def compile_file(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def patch_filter_stage2(text: str) -> tuple[str, list[str]]:
    if PATCH_MARKER in text:
        return text, ["ALREADY_APPLIED"]

    if OLD_BLOCK in text:
        patched = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    else:
        pattern = (
            r'    # Dilution\n'
            r'    if shares_dilution_3y is None:\n'
            r'        watchlist = True\n'
            r'        _add_reason\(\n'
            r'            reasons,\n'
            r'            reason_code="MISSING_SHARES_DILUTION",\n'
            r'            reason_text="Shares dilution 3Y missing\.",\n'
            r'            metric_name="shares_dilution_3y",\n'
            r'            metric_value=shares_dilution_3y,\n'
            r'            threshold="required for clean pass",\n'
            r'            severity="medium",\n'
            r'            recoverable=True,\n'
            r'        \)\n'
            r'    elif shares_dilution_3y > cfg\["max_shares_dilution_3y_watchlist"\]:\n'
        )
        patched, count = re.subn(pattern, NEW_BLOCK, text, count=1)
        if count != 1:
            raise RuntimeError("Could not find the exact MISSING_SHARES_DILUTION block in src/filter_stage2.py")

    patched = PATCH_MARKER + "\n" + patched
    return patched, [
        "PHASE7C3_MARKER_ADDED",
        "MISSING_SHARES_DILUTION_NO_LONGER_BLOCKS_CLEAN_PASS",
        "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION_ADDED",
    ]


def run_stage2() -> tuple[bool, str]:
    exe = ROOT / ".venv" / "Scripts" / "python.exe"
    cmd = [str(exe) if exe.exists() else sys.executable, "-m", "src.run_stage2_filter_enriched"]
    try:
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=180)
        output = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
        return result.returncode == 0, output
    except Exception as exc:
        return False, str(exc)


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def read_stage2_reasons() -> set[str]:
    path = ROOT / "data" / "stages" / "stage2_rejection_log.csv"
    if not path.exists():
        return set()
    try:
        df = pd.read_csv(path)
        if "reason_code" not in df.columns:
            return set()
        return set(df["reason_code"].dropna().astype(str))
    except Exception:
        return set()


def render_report(summary: dict) -> str:
    actual = summary["actual"]
    expected = summary["expected"]
    changes = "\n".join("- " + str(change) for change in summary["changes"])

    return f"""# Scout Finance — Phase 7C.3 Stage 2 yfinance policy implementation

Generated at: `{summary["created_at"]}`

## Result

- Status: **{summary["status"]}**
- Stage 2 run OK: **{summary["stage2_run_ok"]}**
- Matches 7C.2 dry-run: **{summary["matches_expected"]}**

## Counts

| Bucket | Expected dry-run | Actual after implementation |
|---|---:|---:|
| Passed | {expected["passed"]} | {actual["passed"]} |
| Watchlist | {expected["watchlist"]} | {actual["watchlist"]} |
| Rejected | {expected["rejected"]} | {actual["rejected"]} |

## Applied policy

```text
MISSING_SHARES_DILUTION
→ MISSING_SHARES_DILUTION_PROVIDER_LIMITATION
```

Missing 3Y dilution from yfinance is tracked as a provider limitation and does not block clean pass by itself.

## Applied changes

{changes}

## Rollback

```powershell
.\\.venv\\Scripts\\python.exe scripts/rollback_phase7c3_stage2_yfinance_policy.py
```

Backup file:

```text
{summary["backup_path"]}
```

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- filter_stage2.py modified: `{summary["filter_stage2_modified"]}`
- release modified: `{summary["release_modified"]}`
"""


def main() -> int:
    print("Scout Finance — Phase 7C.3 guarded Stage 2 yfinance policy implementation")
    print("=" * 92)

    if not FILTER_PATH.exists():
        fail(f"Missing filter file: {FILTER_PATH}")
        return 1

    good, error = compile_file(FILTER_PATH)
    if not good:
        fail(f"filter_stage2.py does not compile before patch: {error}")
        return 1
    ok("filter_stage2.py compiles before patch")

    if not BACKUP_PATH.exists():
        shutil.copy2(FILTER_PATH, BACKUP_PATH)
        backup_created = True
        ok(f"Backup created: {BACKUP_PATH}")
    else:
        backup_created = False
        ok(f"Backup already exists: {BACKUP_PATH}")

    original = FILTER_PATH.read_text(encoding="utf-8", errors="replace")

    try:
        patched, changes = patch_filter_stage2(original)
    except Exception as exc:
        fail(str(exc))
        return 1

    FILTER_PATH.write_text(patched, encoding="utf-8")

    good, error = compile_file(FILTER_PATH)
    if not good:
        fail(f"filter_stage2.py does not compile after patch: {error}")
        shutil.copy2(BACKUP_PATH, FILTER_PATH)
        warn("Rollback restored from backup")
        return 1
    ok("filter_stage2.py compiles after patch")

    stage2_ok, stage2_output = run_stage2()
    if not stage2_ok:
        fail("Stage 2 failed after patch")
        print(stage2_output)
        return 1
    ok("Stage 2 executed after patch")

    actual = {key: count_csv(path) for key, path in STAGE2_PATHS.items()}
    matches = actual == EXPECTED

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([
        {"bucket": key, "expected_7c2_dryrun": EXPECTED[key], "actual_after_7c3": actual[key], "matches": EXPECTED[key] == actual[key]}
        for key in ["passed", "watchlist", "rejected"]
    ]).to_csv(COMPARISON_PATH, index=False, encoding="utf-8-sig")

    reason_codes = read_stage2_reasons()
    old_reason_present = "MISSING_SHARES_DILUTION" in reason_codes
    new_reason_present = "MISSING_SHARES_DILUTION_PROVIDER_LIMITATION" in reason_codes

    summary = {
        "phase": "7C.3",
        "status": "OK" if matches and not old_reason_present and new_reason_present else "MISMATCH",
        "created_at": utc_now(),
        "backup_path": str(BACKUP_PATH),
        "backup_created": backup_created,
        "changes": changes,
        "stage2_run_ok": stage2_ok,
        "stage2_output_tail": "\n".join(stage2_output.splitlines()[-25:]),
        "expected": EXPECTED,
        "actual": actual,
        "matches_expected": matches,
        "old_missing_shares_dilution_present": old_reason_present,
        "provider_limitation_reason_present": new_reason_present,
        "output_files": {
            "summary_json": str(SUMMARY_PATH),
            "report_md": str(REPORT_PATH),
            "comparison_csv": str(COMPARISON_PATH),
        },
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "filter_stage2_modified": True,
        "release_modified": False,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")

    print()
    print("Counts")
    print("-" * 92)
    print(f"Expected: {EXPECTED}")
    print(f"Actual:   {actual}")
    print()
    print("Reason controls")
    print("-" * 92)
    print(f"Old MISSING_SHARES_DILUTION present: {old_reason_present}")
    print(f"New provider limitation present: {new_reason_present}")

    if summary["status"] == "OK":
        ok("Phase 7C.3 implementation matches 7C.2 dry-run")
        return 0

    fail("Phase 7C.3 implementation did not match required controls")
    print("Run rollback if needed:")
    print(r".\.venv\Scripts\python.exe scripts/rollback_phase7c3_stage2_yfinance_policy.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
