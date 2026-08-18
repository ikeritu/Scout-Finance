#!/usr/bin/env python3
"""QA gate for the v2.33A audit artifacts."""
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
    summary = json.loads((args.output_dir / "audit_summary_v2_33a.json").read_text(encoding="utf-8"))
    with lzma.open(args.output_dir / "universe_row_audit_v2_33a.csv.xz", "rt", encoding="utf-8") as handle:
        audit = pd.read_csv(handle, dtype=str, keep_default_na=False)
    assert summary["phase"] == "v2.33A" and summary["status"] == "PASS"
    assert summary["input"]["rows"] == summary["rows_audited"] == len(audit) == 43_089
    assert sum(summary["type_buckets"].values()) == 43_089
    assert summary["identity"]["duplicate_exchange_ticker_rows"] == 0
    assert summary["financial_coverage"]["fundamental_scoring_possible_from_current_catalog_alone"] is False
    assert summary["production_scoring_authorized"] is False
    assert summary["allow_ranking"] is False
    assert summary["input_modified"] is False
    assert audit["row_number"].nunique() == 43_089
    assert set(audit["v2_33a_status"]) == {"audited_pending_eligibility_policy_v2_33b"}
    print("PASS: v2.33A/43089/one-audit-row-per-input/no-identity-collision/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
