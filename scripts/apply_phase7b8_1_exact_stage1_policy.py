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
FILTER_PATH = ROOT / "src" / "filter_stage1.py"
BACKUP_PATH = ROOT / "src" / "filter_stage1_before_phase7b8_1_exact.py"
OUT_DIR = ROOT / "outputs" / "scouting"
SUMMARY_PATH = OUT_DIR / "stage1_balanced_exact_implementation_summary.json"
REPORT_PATH = OUT_DIR / "stage1_balanced_exact_implementation_report.md"
COMPARISON_PATH = OUT_DIR / "stage1_balanced_exact_implementation_comparison.csv"

STAGE1_PATHS = {
    "passed": ROOT / "data" / "stages" / "stage1_passed.csv",
    "watchlist": ROOT / "data" / "stages" / "stage1_watchlist.csv",
    "rejected": ROOT / "data" / "stages" / "stage1_rejected.csv",
}
EXPECTED = {"passed": 182, "watchlist": 84, "rejected": 234}
CONFIG_REPLACEMENTS = {
    "min_market_cap_pass": "500_000_000",
    "min_market_cap_watchlist": "150_000_000",
    "min_price_pass": "3.0",
    "min_price_watchlist": "1.5",
    "min_dollar_volume_pass": "5_000_000",
    "min_dollar_volume_watchlist": "1_000_000",
}

PRICE_BLOCK = '''    # Price
    if price is None:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="MISSING_PRICE",
            reason_text="Price missing.",
            metric_name="price",
            metric_value=price,
            threshold="required",
            severity="high",
            recoverable=True,
        )
    elif price < cfg["min_price_watchlist"]:
        hard_reject = True
        _add_reason(
            reasons,
            reason_code="PRICE_BELOW_MINIMUM",
            reason_text="Price below Stage 1 minimum.",
            metric_name="price",
            metric_value=price,
            threshold=cfg["min_price_watchlist"],
            severity="high",
            recoverable=False,
        )
    elif price < cfg["min_price_pass"]:
        watchlist = True
        _add_reason(
            reasons,
            reason_code="PRICE_STRONG_WATCHLIST_RANGE",
            reason_text="Price is below pass threshold but above rejection threshold.",
            metric_name="price",
            metric_value=price,
            threshold=cfg["min_price_pass"],
            severity="medium",
            recoverable=True,
        )
    elif price < 5.0:
        _add_reason(
            reasons,
            reason_code="PRICE_WEAK_WATCHLIST_RANGE",
            reason_text="Price is below weak warning threshold but does not trigger watchlist by itself.",
            metric_name="price",
            metric_value=price,
            threshold=5.0,
            severity="low",
            recoverable=True,
        )
'''

def ok(message: str) -> None:
    print(f"OK   {message}")

def fail(message: str) -> None:
    print(f"FAIL {message}")

def warn(message: str) -> None:
    print(f"WARN {message}")

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def compile_python(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)

def patch_config(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    for key, value in CONFIG_REPLACEMENTS.items():
        pattern = rf'(^\s*"{re.escape(key)}"\s*:\s*)([0-9_]+(?:\.[0-9]+)?)(\s*,\s*$)'
        replacement = rf'\g<1>{value}\g<3>'
        text2, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError(f"Could not replace DEFAULT_STAGE1_CONFIG key: {key}")
        text = text2
        changes.append(f'{key}={value}')
    return text, changes

def patch_price_block(text: str) -> tuple[str, list[str]]:
    pattern = r'    # Price\n    if price is None:.*?\n\n    # Dollar volume'
    replacement = PRICE_BLOCK + '\n    # Dollar volume'
    text2, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("Could not replace the real # Price block in src/filter_stage1.py")
    return text2, ["PRICE_BLOCK_REPLACED_WITH_STRONG_AND_WEAK_PRICE_RULES"]

def run_stage1() -> tuple[bool, str]:
    exe = ROOT / ".venv" / "Scripts" / "python.exe"
    cmd = [str(exe) if exe.exists() else sys.executable, "-m", "src.run_stage1_filter"]
    try:
        result = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=180)
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

def build_report(summary: dict) -> str:
    actual = summary["actual"]
    expected = summary["expected"]
    changes = "\n".join("- " + str(change) for change in summary["changes"])
    return f"""# Scout Finance — Phase 7B.8.1 Exact Stage 1 Implementation

Generated at: `{summary['created_at']}`

## Result

- Status: **{summary['status']}**.
- Stage 1 run OK: **{summary['stage1_run_ok']}**.
- Matches dry-run: **{summary['matches_expected']}**.

## Counts

| Bucket | Expected dry-run | Actual after exact patch |
|---|---:|---:|
| Passed | {expected['passed']} | {actual['passed']} |
| Watchlist | {expected['watchlist']} | {actual['watchlist']} |
| Rejected | {expected['rejected']} | {actual['rejected']} |

## Applied changes

{changes}

## Rollback

```powershell
.\\.venv\\Scripts\\python.exe scripts/rollback_phase7b8_1_exact_stage1_policy.py
```

## Controls

- OpenAI called: `{summary['openai_called']}`
- API called: `{summary['api_called']}`
- yfinance called: `{summary['yfinance_called']}`
- app.py modified: `{summary['app_modified']}`
- release modified: `{summary['release_modified']}`
- filter_stage1.py modified: `{summary['filter_modified']}`
"""

def main() -> int:
    print("Scout Finance — Phase 7B.8.1 exact guarded Stage 1 implementation")
    print("=" * 82)
    if not FILTER_PATH.exists():
        fail(f"Missing filter file: {FILTER_PATH}")
        return 1
    good, error = compile_python(FILTER_PATH)
    if not good:
        fail(f"filter_stage1.py does not compile before patch: {error}")
        return 1
    ok("filter_stage1.py compiles before patch")
    if not BACKUP_PATH.exists():
        shutil.copy2(FILTER_PATH, BACKUP_PATH)
        ok(f"Backup created: {BACKUP_PATH}")
        backup_created = True
    else:
        ok(f"Backup already exists: {BACKUP_PATH}")
        backup_created = False
    original = FILTER_PATH.read_text(encoding="utf-8", errors="replace")
    if "# PHASE 7B.8.1 EXACT BALANCED STAGE 1 POLICY APPLIED" in original:
        warn("Phase 7B.8.1 marker already present. Reapplying will be skipped.")
        patched = original
        changes = ["ALREADY_APPLIED"]
    else:
        patched, config_changes = patch_config(original)
        patched, price_changes = patch_price_block(patched)
        marker = "# PHASE 7B.8.1 EXACT BALANCED STAGE 1 POLICY APPLIED"
        patched = marker + "\n" + patched
        changes = ["PHASE7B8_1_MARKER_ADDED"] + config_changes + price_changes
    FILTER_PATH.write_text(patched, encoding="utf-8")
    good, error = compile_python(FILTER_PATH)
    if not good:
        fail(f"filter_stage1.py does not compile after patch: {error}")
        shutil.copy2(BACKUP_PATH, FILTER_PATH)
        warn("Rollback restored from backup")
        return 1
    ok("filter_stage1.py compiles after patch")
    stage1_ok, stage1_output = run_stage1()
    if not stage1_ok:
        fail("Stage 1 failed after exact patch")
        print(stage1_output)
        return 1
    ok("Stage 1 executed after exact patch")
    actual = {key: count_csv(path) for key, path in STAGE1_PATHS.items()}
    comparison_rows = [
        {"bucket": key, "expected_dry_run": EXPECTED[key], "actual_after_exact_patch": actual[key], "matches": EXPECTED[key] == actual[key]}
        for key in ["passed", "watchlist", "rejected"]
    ]
    pd.DataFrame(comparison_rows).to_csv(COMPARISON_PATH, index=False, encoding="utf-8-sig")
    matches = all(EXPECTED[key] == actual[key] for key in EXPECTED)
    summary = {
        "phase": "7B.8.1",
        "status": "OK" if matches else "MISMATCH",
        "created_at": utc_now(),
        "backup_path": str(BACKUP_PATH),
        "backup_created": backup_created,
        "changes": changes,
        "stage1_run_ok": stage1_ok,
        "stage1_output_tail": "\n".join(stage1_output.splitlines()[-20:]),
        "expected": EXPECTED,
        "actual": actual,
        "matches_expected": matches,
        "summary_path": str(SUMMARY_PATH),
        "report_path": str(REPORT_PATH),
        "comparison_path": str(COMPARISON_PATH),
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "release_modified": False,
        "filter_modified": True,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(build_report(summary), encoding="utf-8")
    print()
    print("Counts")
    print("-" * 82)
    print(f"Expected: {EXPECTED}")
    print(f"Actual:   {actual}")
    if matches:
        ok("Exact implementation matches 7B.6 dry-run")
        return 0
    fail("Exact implementation does not match 7B.6 dry-run")
    print("Run rollback if needed:")
    print(r".\.venv\Scripts\python.exe scripts/rollback_phase7b8_1_exact_stage1_policy.py")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
