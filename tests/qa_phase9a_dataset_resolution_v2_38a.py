#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/global_universe_audit_contract_v1.json"
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = ROOT / contract["canonical_dataset"]
    metadata = ROOT / contract["metadata_dataset"]
    assert digest(source) == contract["canonical_sha256"]
    assert digest(metadata) == contract["metadata_sha256"]
    with lzma.open(source, "rt", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == contract["expected_rows"] == 43089
    assert sum(r["eligibility_decision_v2_33b2"] == contract["eligible_status"] for r in rows) == 21165
    candidates = list(csv.DictReader((OUTPUT / "canonical_dataset_candidates_v2_38a.csv").open(encoding="utf-8", newline="")))
    assert sum(r["selected"] == "true" for r in candidates) == 1
    assert next(r for r in candidates if r["selected"] == "true")["sha256"] == contract["canonical_sha256"]
    print("PASS: v2.38A/canonical-resolution/43089/sha-locked/21165-eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
