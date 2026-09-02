#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_us_price_history_acquisition_v2_38i.py"


def write_plan(path: Path) -> None:
    fields = ["asset_id", "ticker", "company_name", "exchange", "priority_bucket", "fundamental_feature_status", "provider_symbol", "acquisition_status", "reason", "local_price_path", "expected_min_rows", "adjusted_prices_required"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Inc.", "exchange": "NASDAQ", "priority_bucket": "FEATURES_READY", "fundamental_feature_status": "FEATURES_READY", "provider_symbol": "AAA", "acquisition_status": "PENDING_COLLECTION", "reason": "", "local_price_path": "", "expected_min_rows": "252", "adjusted_prices_required": "true"})


def write_mock(path: Path) -> None:
    values = [{"datetime": f"2026-01-{day:02d}", "close": str(10 + day), "adjusted_close": str(10 + day), "volume": str(1000 + day)} for day in range(1, 6)]
    path.write_text(json.dumps({"values": values}), encoding="utf-8")


def run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True, env=env)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        plan = base / "plan.csv"
        raw = base / "raw"
        mock = base / "mock"
        mock.mkdir()
        write_plan(plan)
        write_mock(mock / "AAA.json")
        dry = run(["--limit", "1", "--plan-path", str(plan), "--raw-cache", str(raw)])
        assert dry.returncode == 0
        assert json.loads(dry.stdout)["status"] == "DRY_RUN"
        oversized = run(["--limit", "251", "--plan-path", str(plan), "--raw-cache", str(raw)])
        assert oversized.returncode == 2 and json.loads(oversized.stdout)["reason"] == "batch_limit_must_be_1_to_250"
        unsupported = run(["--limit", "1", "--provider", "unknown", "--plan-path", str(plan), "--raw-cache", str(raw)])
        assert unsupported.returncode == 2 and json.loads(unsupported.stdout)["reason"] == "provider_not_supported"
        clean_env = {k: v for k, v in os.environ.items() if k != "TWELVE_DATA_API_KEY"}
        missing = run(["--limit", "1", "--execute", "--plan-path", str(plan), "--raw-cache", str(raw)], env=clean_env)
        assert missing.returncode == 2 and json.loads(missing.stdout)["reason"] == "credential_missing"
        env = dict(clean_env, TWELVE_DATA_API_KEY="test-not-secret")
        executed = run(["--limit", "1", "--execute", "--plan-path", str(plan), "--raw-cache", str(raw), "--mock-provider-dir", str(mock)], env=env)
        assert executed.returncode == 0, executed.stderr
        payload = json.loads(executed.stdout)
        assert payload["status"] == "COMPLETED" and payload["collected"] == 1
        assert "test-not-secret" not in executed.stdout
        output = raw / "U00001.csv"
        assert output.exists()
        text = output.read_text(encoding="utf-8")
        assert "test-not-secret" not in text and "provider_symbol" in text
    print("PASS: v2.38I/runner/dry-run/gates/mock-execute/no-secrets/no-network-in-qa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
