#!/usr/bin/env python3
"""QA gate for v2.33B policy and row-level census."""
from __future__ import annotations

import argparse
import json
import lzma
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    policy = json.loads((args.output_dir / "eligibility_policy_v2_33b.json").read_text(encoding="utf-8"))
    with lzma.open(args.output_dir / "eligibility_census_v2_33b.csv.xz", "rt", encoding="utf-8") as handle:
        census = pd.read_csv(handle, dtype=str, keep_default_na=False)
    assert policy["phase"] == "v2.33B" and policy["status"] == "PASS"
    assert policy["rows_decided"] == len(census) == 43_089
    assert census["row_number"].nunique() == 43_089
    summary = policy["decision_summary"]
    assert summary == {
        "eligible_for_financial_enrichment": 23_888,
        "excluded_from_equity_opportunity_universe": 10_409,
        "requires_review": 8_792,
    }
    assert sum(policy["decision_counts"].values()) == 43_089
    assert not census["eligibility_decision_v2_33b"].eq("").any()
    assert set(census["eligible_for_opportunity_ranking"]) == {"False"}
    assert policy["production_scoring_authorized"] is False
    assert policy["allow_ranking"] is False
    assert policy["operational_dataset_modified"] is False
    assert policy["operational_pointers_modified"] is False
    print("PASS: v2.33B/43089/all-decided/conservative-equity-policy/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
