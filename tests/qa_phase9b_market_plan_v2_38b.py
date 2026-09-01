#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38b_global_enrichment"


def main() -> int:
    rows = list(csv.DictReader((OUT / "market_acquisition_plan_v2_38b.csv").open(encoding="utf-8", newline="")))
    by_market = {r["exchange"]: r for r in rows}
    assert len(rows) == 15 and sum(int(r["rows"]) for r in rows) == 43089
    assert int(by_market["JPX"]["batch_eligible_rows"]) == 42
    assert by_market["JPX"]["primary_status"] == "SYMBOL_RESOLUTION_REQUIRED"
    assert int(by_market["TWSE"]["batch_eligible_rows"]) == 696
    assert sum(int(by_market[x]["eligible_rows"]) for x in ("NASDAQ", "NYSE", "NYSE American", "Cboe BZX")) == 5011
    assert all(by_market[x]["primary_status"] == "USER_ACTION_REQUIRED" for x in ("NASDAQ", "NYSE", "NYSE American", "Cboe BZX"))
    assert by_market["CBOE_EUROPE"]["primary_status"] == "SOURCE_RESEARCH_REQUIRED"
    assert by_market["ASX"]["primary_status"] == "LICENSE_BLOCKED"
    assert all(r["real_collection_authorized"] == "false" and r["blocker"] for r in rows)
    summary = json.loads((OUT / "global_enrichment_summary_v2_38b.json").read_text(encoding="utf-8"))
    assert summary["network_calls"] == 0 and summary["prices_downloaded"] == summary["fundamentals_downloaded"] == 0
    jpx = list(csv.DictReader((OUT / "jpx_verified_symbols_42_v2_38b.csv").open(encoding="utf-8", newline="")))
    jpx_pilot = list(csv.DictReader((OUT / "jpx_symbol_resolution_pilot_25_v2_38b.csv").open(encoding="utf-8", newline="")))
    twse_pilot = list(csv.DictReader((OUT / "twse_collection_pilot_25_v2_38b.csv").open(encoding="utf-8", newline="")))
    assert len(jpx) == 42 and all(r["provider_symbol"] for r in jpx)
    assert len(jpx_pilot) == len(twse_pilot) == 25
    assert not ({r["ticker"] for r in jpx} & {r["ticker"] for r in jpx_pilot})
    print("PASS: v2.38B/15-markets/JPX-TWSE-ready/US-user-action/Europe-ASX-blocked/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
