
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "scouting"

FILTER = ROOT / "src" / "filter_stage1.py"
BACKUP = ROOT / "src" / "filter_stage1_before_phase7b8_1_exact.py"

SUMMARY = OUT / "stage1_balanced_official_closure_summary.json"
REPORT = OUT / "stage1_balanced_official_closure_report.md"
EVIDENCE = OUT / "stage1_balanced_official_closure_evidence.csv"
POLICY = OUT / "active_stage1_policy_status.json"

EXPECTED = {"passed": 182, "watchlist": 84, "rejected": 234}

STAGE1 = {
    "passed": ROOT / "data" / "stages" / "stage1_passed.csv",
    "watchlist": ROOT / "data" / "stages" / "stage1_watchlist.csv",
    "rejected": ROOT / "data" / "stages" / "stage1_rejected.csv",
}

MARKERS = [
    "# PHASE 7B.8.1 EXACT BALANCED STAGE 1 POLICY APPLIED",
    '"min_market_cap_pass": 500_000_000',
    '"min_market_cap_watchlist": 150_000_000',
    '"min_price_watchlist": 1.5',
    '"min_dollar_volume_pass": 5_000_000',
    '"min_dollar_volume_watchlist": 1_000_000',
    "PRICE_STRONG_WATCHLIST_RANGE",
    "PRICE_WEAK_WATCHLIST_RANGE",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return 0


def run_stage1() -> tuple[bool, str]:
    exe = ROOT / ".venv" / "Scripts" / "python.exe"
    cmd = [str(exe) if exe.exists() else sys.executable, "-m", "src.run_stage1_filter"]
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=180)
    return result.returncode == 0, (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")


def make_report(summary: dict) -> str:
    a = summary["actual_counts"]
    return f"""# Scout Finance — Phase 7B.9 Stage 1 Balanced Official Closure

Generated at: `{summary["created_at"]}`

## Official status

- Active Stage 1 policy: **balanced**.
- Status: **{summary["status"]}**.
- Ready for v0.7 checkpoint: **{summary["ready_for_v0_7_checkpoint"]}**.
- Recommended next phase: **{summary["recommended_next_phase"]}**.

## Confirmed counts

| Bucket | Expected | Actual |
|---|---:|---:|
| Passed | 182 | {a["passed"]} |
| Watchlist | 84 | {a["watchlist"]} |
| Rejected | 234 | {a["rejected"]} |

## Active Balanced policy

```text
market_cap rejected below 150M
market_cap watchlist below 500M
price rejected below 1.5
price strong watchlist from 1.5 to below 3
price weak warning from 3 to below 5
dollar volume rejected below 1M
dollar volume watchlist below 5M
```

## Rollback

```powershell
.\\.venv\\Scripts\\python.exe scripts/rollback_phase7b8_1_exact_stage1_policy.py
```

Backup:

```text
{summary["rollback_backup_path"]}
```

## Controls

- OpenAI called: `{summary["openai_called"]}`
- API called: `{summary["api_called"]}`
- yfinance called: `{summary["yfinance_called"]}`
- app.py modified: `{summary["app_modified"]}`
- release modified: `{summary["release_modified"]}`
- filter_stage1.py modified: `{summary["filter_modified"]}`
"""


def main() -> int:
    print("Scout Finance — Phase 7B.9 Stage 1 Balanced official closure")
    print("=" * 82)

    evidence = []

    def add(check: str, status: str, detail: str) -> None:
        evidence.append({"check": check, "status": status, "detail": detail})
        print(f"{status:4} {check}: {detail}")

    add("filter_stage1_exists", "OK" if FILTER.exists() else "FAIL", str(FILTER))
    add("rollback_backup_exists", "OK" if BACKUP.exists() else "FAIL", str(BACKUP))

    try:
        py_compile.compile(str(FILTER), doraise=True)
        add("filter_stage1_compiles", "OK", "compiled")
    except Exception as exc:
        add("filter_stage1_compiles", "FAIL", str(exc))

    text = FILTER.read_text(encoding="utf-8", errors="replace") if FILTER.exists() else ""
    missing = [m for m in MARKERS if m not in text]
    add("balanced_policy_markers_present", "OK" if not missing else "FAIL", "all markers present" if not missing else str(missing))

    stage_ok, output = run_stage1()
    add("run_stage1_filter", "OK" if stage_ok else "FAIL", "executed" if stage_ok else output[-500:])

    actual = {k: read_count(v) for k, v in STAGE1.items()}
    counts_ok = actual == EXPECTED
    add("stage1_counts_match_balanced", "OK" if counts_ok else "FAIL", f"expected={EXPECTED}; actual={actual}")

    status = "OK" if all(e["status"] == "OK" for e in evidence) else "FAIL"

    summary = {
        "phase": "7B.9",
        "status": status,
        "created_at": now(),
        "active_stage1_policy": "balanced",
        "actual_counts": actual,
        "expected_counts": EXPECTED,
        "evidence": evidence,
        "rollback_backup_path": str(BACKUP),
        "stage1_output_tail": "\n".join(output.splitlines()[-20:]),
        "ready_for_v0_7_checkpoint": status == "OK",
        "recommended_next_phase": "7C — Revalidate Stage 2 / Stage 3 / candidates with Stage 1 Balanced active",
        "openai_called": False,
        "api_called": False,
        "yfinance_called": False,
        "app_modified": False,
        "release_modified": False,
        "filter_modified": True,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT.write_text(make_report(summary), encoding="utf-8")
    pd.DataFrame(evidence).to_csv(EVIDENCE, index=False, encoding="utf-8-sig")
    POLICY.write_text(json.dumps({
        "active_stage1_policy": "balanced",
        "phase_confirmed": "7B.9",
        "confirmed_at": summary["created_at"],
        "counts": actual,
        "rollback_backup_path": str(BACKUP),
        "next_phase": summary["recommended_next_phase"],
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"Status: {status}")
    print(f"Active Stage 1 policy: balanced")
    print(f"Counts: {actual}")
    print(f"Next: {summary['recommended_next_phase']}")

    return 0 if status == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
