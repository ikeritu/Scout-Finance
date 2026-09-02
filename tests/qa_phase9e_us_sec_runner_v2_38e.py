#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_us_sec_enrichment_v2_38e.py"


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, text=True, capture_output=True, env=env)


def main() -> int:
    dry = run("--limit", "7")
    assert dry.returncode == 0
    payload = json.loads(dry.stdout)
    assert payload["status"] == "DRY_RUN"
    assert payload["selected"] <= 7
    assert payload["network_calls"] == 0
    assert payload["phase9c_authorized"] is False
    oversized = run("--limit", "251")
    assert oversized.returncode == 2
    assert json.loads(oversized.stdout)["reason"] == "batch_limit_must_be_1_to_250"
    clean_env = {k: v for k, v in os.environ.items() if k != "SCOUT_FINANCE_SEC_USER_AGENT"}
    blocked = run("--limit", "1", "--execute", env=clean_env)
    assert blocked.returncode == 2
    assert json.loads(blocked.stdout)["reason"] == "sec_user_agent_missing"
    print("PASS: v2.38E/runner/dry-run/no-network/user-agent-gate/max250/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
