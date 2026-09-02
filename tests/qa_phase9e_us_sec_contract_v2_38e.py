#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_sec_enrichment_expansion_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38e_us_sec_enrichment_expansion"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38E-us-sec-enrichment-expansion"
    assert contract["expected_us_rows"] == 9200
    assert contract["expected_us_eligible_rows"] == 5011
    assert contract["baseline_cik_resolved_minimum"] >= 4896
    assert contract["maximum_batch_assets"] == 250
    forbidden = set(contract["forbidden_actions"])
    assert {"scoring", "ranking", "recommendations", "phase9c", "broker", "trading", "raw_sec_json_in_git"} <= forbidden
    subprocess.run(["git", "check-ignore", "-q", str(OUT / "sec_raw_cache_v2_38e/example.json")], cwd=ROOT, check=True)
    print("PASS: v2.38E/contract/US-SEC-expansion/max250/raw-cache-ignored/no-scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
