#!/usr/bin/env python3
"""QA gate for deterministic-only price symbol resolution."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_33d_price_pilot"


def main() -> int:
    report = json.loads((OUTPUT / "symbol_resolution_report_v2_33d.json").read_text(encoding="utf-8"))
    with (OUTPUT / "price_pilot_symbols_v2_33d.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 240 and report["input_rows"] == 240
    assert report["resolved_deterministic"] == 77
    assert report["excluded_non_company"] == 1
    assert report["unresolved"] == 162
    by_id = {row["pilot_id"]: row for row in rows}
    assert by_id["P014"]["provider_symbol_status"] == "excluded_non_company_index"
    assert by_id["P014"]["price_collection_status"] == "excluded_non_company"
    assert by_id["P230"]["provider_symbol"] == "MOG-B.US"
    assert all(row["provider_symbol"].endswith(".US") for row in rows if row["exchange"] in {"NASDAQ", "NYSE", "NYSE American", "NYSE Arca", "Cboe BZX"})
    assert all(row["provider_symbol"].endswith(".AU") for row in rows if row["exchange"] == "ASX" and row["provider_symbol_status"].startswith("resolved"))
    assert all(row["provider_symbol"].endswith(".TW") for row in rows if row["exchange"] == "TWSE")
    assert all(not row["provider_symbol"] for row in rows if row["exchange"] in {"CBOE_EUROPE", "JPX", "BVC"})
    assert report["network_calls"] == 0 and report["credentials_used"] is False
    assert report["production_scoring_authorized"] is False and report["allow_ranking"] is False
    print("PASS: v2.33D-symbols/77-resolved/1-index-excluded/162-ambiguous-blocked/no-network/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
