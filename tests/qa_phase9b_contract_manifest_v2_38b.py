#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import lzma
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38b_global_enrichment"


def main() -> int:
    contract = json.loads((ROOT / "config/global_enrichment_contract_v1.json").read_text(encoding="utf-8"))
    source = ROOT / contract["input_manifest"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == contract["input_sha256"]
    assert contract["maximum_batch_assets"] == 500 and contract["execution_default"] == "BLOCKED"
    assert contract["phase9c_authorized"] is False and contract["allow_ranking"] is False
    with lzma.open(OUT / "global_acquisition_manifest_v2_38b.csv.xz", "rt", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 43089 == len({r["asset_id"] for r in rows})
    assert sum(r["eligibility_status"] == "ELIGIBLE" for r in rows) == 21165
    assert sum(r["batch_eligible"] == "true" for r in rows) == 763
    assert Counter(r["acquisition_status"] for r in rows) == {
        "READY_FOR_CONTROLLED_BATCH": 763, "SYMBOL_RESOLUTION_REQUIRED": 3634, "USER_ACTION_REQUIRED": 5011,
        "SOURCE_RESEARCH_REQUIRED": 10486, "LICENSE_BLOCKED": 1271,
        "METADATA_REPAIR_REQUIRED": 1782, "REVIEW_REQUIRED": 9710, "NOT_ELIGIBLE": 10432,
    }
    assert all(len(r["evidence_hash"]) == 64 and r["attempt_count"] == "0" for r in rows)
    assert sum(r["exchange"] == "JPX" and bool(r["provider_symbol"]) for r in rows) == 67
    print("PASS: v2.38B/contract/43089/21165/763-ready/3634-symbol-resolution/closed-states/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
