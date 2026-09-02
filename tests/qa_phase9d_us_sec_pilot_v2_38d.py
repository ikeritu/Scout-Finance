#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation"
RUNNER = ROOT / "scripts/run_us_sec_pilot_v2_38d.py"


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, env=env)


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_us_sec_foundation_v2_38d.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    with (OUT / "us_sec_pilot_selection_v2_38d.csv").open(encoding="utf-8", newline="") as f:
        selection = list(csv.DictReader(f))
    assert 1 <= len(selection) <= 50
    assert len(selection) == len({r["asset_id"] for r in selection})
    dry = run("--limit", "12")
    assert dry.returncode == 0
    payload = json.loads(dry.stdout)
    assert payload["status"] == "DRY_RUN" and payload["selected"] == 12 and payload["network_calls"] == 0
    clean_env = {k: v for k, v in os.environ.items() if k != "SCOUT_FINANCE_SEC_USER_AGENT"}
    blocked = run("--limit", "2", "--execute", env=clean_env)
    assert blocked.returncode == 2 and json.loads(blocked.stdout)["reason"] == "sec_user_agent_missing"
    ignored = subprocess.run(["git", "check-ignore", "-q", "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation/sec_raw_cache_v2_38d/example.json"], cwd=ROOT)
    assert ignored.returncode == 0
    print("PASS: v2.38D/US-SEC-pilot/dry-run/max50/user-agent-gate/raw-cache-ignored/no-network-in-qa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
