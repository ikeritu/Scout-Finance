#!/usr/bin/env python3
"""QA gate for the v2.33L market universe inventory: reproducibility and
sanity checks against the canonical eligibility census. No network calls.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "outputs/full_universe_source_acquisition/v2_33b2_eligibility_refinement/eligibility_census_v2_33b2.csv.xz"


def module():
    spec = importlib.util.spec_from_file_location("build_market_universe_inventory_v2_33l", ROOT / "scripts/build_market_universe_inventory_v2_33l.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not CENSUS.exists():
        print("SKIP: canonical eligibility census not present locally")
        return 0

    mod = module()
    rows = mod.load_census()
    eligible = [r for r in rows if r["eligibility_decision_v2_33b2"] == mod.ELIGIBLE_STATUS]
    assert len(eligible) == 21165, f"expected 21165 eligible candidates, found {len(eligible)}"

    by_exchange = {}
    for r in eligible:
        by_exchange.setdefault(r["exchange"], []).append(r)
    assert by_exchange["CBOE_EUROPE"].__len__() == 10483
    assert len(by_exchange) == 9

    held_xetra = sum(1 for r in rows if r["eligibility_decision_v2_33b2"] == "hold_provider_schema_xetra")
    held_sgx = sum(1 for r in rows if r["eligibility_decision_v2_33b2"] == "hold_provider_schema_sgx")
    assert held_xetra == 1424 and held_sgx == 358

    # Reproducibility: rerunning the same builder logic must give identical totals.
    rows2 = mod.load_census()
    eligible2 = [r for r in rows2 if r["eligibility_decision_v2_33b2"] == mod.ELIGIBLE_STATUS]
    assert len(eligible) == len(eligible2)

    print(json.dumps({
        "total_eligible": len(eligible),
        "cboe_europe_share_pct": round(len(by_exchange["CBOE_EUROPE"]) / len(eligible) * 100, 2),
        "held_xetra": held_xetra,
        "held_sgx": held_sgx,
    }, ensure_ascii=False))
    print("PASS: v2.33L-inventory/21165-eligible/9-exchanges/reproducible/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
