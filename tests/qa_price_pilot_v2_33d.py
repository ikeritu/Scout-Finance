#!/usr/bin/env python3
"""Preparation and fail-closed gate for v2.33D."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    output = ROOT / "outputs/v2_33d"
    manifest = json.loads((output / "price_pilot_manifest_v2_33d.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((output / "price_pilot_sample_v2_33d.csv").open(encoding="utf-8", newline="")))
    assert manifest["status"] == "READY_FOR_AUTHORIZED_PILOT_NOT_EXECUTED"
    assert manifest["population"] == 23_888 and manifest["sample_rows"] == len(rows) == 240
    assert len({row["row_number"] for row in rows}) == 240
    assert set(manifest["provider_quotas"]) == {row["source_provider"] for row in rows}
    assert all(row["provider_symbol_status"] == "pending_provider_mapping" for row in rows)
    assert manifest["eligibility_preflight"]["review_rows"] > 0
    assert manifest["eligibility_preflight"]["v2_33b_reopen_required"] is True
    assert any(row["price_collection_status"] == "blocked_pending_eligibility_correction" for row in rows)
    assert manifest["network_collection_executed"] is False and manifest["price_rows_collected"] == 0
    env = dict(os.environ)
    env.pop("SCOUT_FINANCE_EODHD_API_TOKEN", None)
    blocked = subprocess.run(
        [sys.executable, str(ROOT / "scripts/download_eodhd_price_pilot_v2_33d.py"), str(output / "price_pilot_sample_v2_33d.csv"), str(output / "raw"), "--execute"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30
    )
    assert blocked.returncode == 2 and "BLOCKED" in blocked.stdout
    assert manifest["production_scoring_authorized"] is False and manifest["allow_ranking"] is False
    print("PASS: v2.33D-preparation/240-unique/preflight-detected-eligibility-incidents/fail-closed/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
