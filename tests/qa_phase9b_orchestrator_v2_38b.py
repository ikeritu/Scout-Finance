#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_global_acquisition_v2_38b.py"


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True, env=env)


def main() -> int:
    dry = run("--market", "JPX", "--limit", "25")
    assert dry.returncode == 0
    payload = json.loads(dry.stdout)
    assert payload["status"] == "DRY_RUN" and payload["selected"] == 25 and len(payload["asset_ids"]) == 25
    oversized = run("--market", "JPX", "--limit", "501")
    assert oversized.returncode == 2 and json.loads(oversized.stdout)["reason"] == "batch_limit_must_be_1_to_500"
    clean_env = {k: v for k, v in os.environ.items() if k not in {"JQUANTS_API_KEY", "SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN", "TWELVE_DATA_API_KEY"}}
    execute = run("--market", "JPX", "--limit", "5", "--execute", env=clean_env)
    assert execute.returncode == 2 and json.loads(execute.stdout)["reason"] == "credential_missing"
    twse = run("--market", "TWSE", "--limit", "5", "--execute", env=clean_env)
    assert twse.returncode == 2 and json.loads(twse.stdout)["reason"] == "market_adapter_not_authorized_for_v2_38b_real_collection"
    print("PASS: v2.38B/orchestrator/dry-run/max500/credential-gate/adapter-gate/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
