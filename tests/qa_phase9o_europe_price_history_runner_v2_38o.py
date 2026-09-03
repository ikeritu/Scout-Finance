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
SCRIPT = ROOT / "scripts/run_europe_price_history_acquisition_v2_38o.py"


def write_plan(path: Path) -> None:
    fields = ["asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country", "home_currency", "provider_route", "provider", "provider_symbol", "collection_status", "rows_collected", "first_date", "last_date", "raw_cache_path", "failure_reason", "phase", "scoring_calculated", "ranking_calculated", "recommendations_generated", "phase9c_authorized"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"asset_id": "U20001", "ticker": "ABC", "company_name": "Alpha AG", "home_exchange": "XETRA", "home_mic": "XETR", "home_country": "DE", "home_currency": "EUR", "provider_route": "stooq_daily_prices", "provider": "stooq", "provider_symbol": "abc.de", "collection_status": "READY_FOR_COLLECTION", "rows_collected": "0", "first_date": "", "last_date": "", "raw_cache_path": "", "failure_reason": "", "phase": "v2.38O-europe-price-history-acquisition", "scoring_calculated": "false", "ranking_calculated": "false", "recommendations_generated": "false", "phase9c_authorized": "false"})
        writer.writerow({"asset_id": "U20002", "ticker": "DEF", "company_name": "Beta Plc", "home_exchange": "LSE", "home_mic": "XLON", "home_country": "GB", "home_currency": "GBP", "provider_route": "eodhd_europe_prices", "provider": "eodhd", "provider_symbol": "DEF.LSE", "collection_status": "READY_FOR_COLLECTION", "rows_collected": "0", "first_date": "", "last_date": "", "raw_cache_path": "", "failure_reason": "", "phase": "v2.38O-europe-price-history-acquisition", "scoring_calculated": "false", "ranking_calculated": "false", "recommendations_generated": "false", "phase9c_authorized": "false"})


def write_mock(path: Path) -> None:
    values = [{"datetime": f"2025-01-{(day % 28) + 1:02d}", "open": "10", "high": "12", "low": "9", "close": "11", "adjusted_close": "11", "volume": "1000"} for day in range(130)]
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
        write_mock(mock / "abc.de.json")
        dry = run(["--limit", "1", "--provider", "stooq", "--plan-path", str(plan), "--raw-cache", str(raw)])
        assert dry.returncode == 0
        assert json.loads(dry.stdout)["status"] == "DRY_RUN"
        oversized = run(["--limit", "101", "--provider", "stooq", "--plan-path", str(plan), "--raw-cache", str(raw)])
        assert oversized.returncode == 2 and json.loads(oversized.stdout)["reason"] == "batch_limit_must_be_1_to_100"
        unsupported = run(["--limit", "1", "--provider", "unknown", "--plan-path", str(plan), "--raw-cache", str(raw)])
        assert unsupported.returncode == 2 and json.loads(unsupported.stdout)["reason"] == "provider_not_supported"
        clean_env = {k: v for k, v in os.environ.items() if k != "EODHD_API_KEY"}
        missing = run(["--limit", "1", "--provider", "eodhd", "--execute", "--plan-path", str(plan), "--raw-cache", str(raw)], env=clean_env)
        assert missing.returncode == 2 and json.loads(missing.stdout)["reason"] == "credential_missing"
        executed = run(["--limit", "1", "--provider", "stooq", "--execute", "--plan-path", str(plan), "--raw-cache", str(raw), "--mock-provider-dir", str(mock)])
        assert executed.returncode == 0, executed.stderr
        payload = json.loads(executed.stdout)
        assert payload["status"] == "COMPLETED"
        assert payload["collected"] == 1
        output = raw / "U20001.csv"
        assert output.exists()
        text = output.read_text(encoding="utf-8")
        assert "provider_symbol" in text
        assert "EODHD_API_KEY" not in text
    print("PASS: v2.38O/runner/dry-run/gates/mock-execute/no-secrets/no-network-in-qa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
