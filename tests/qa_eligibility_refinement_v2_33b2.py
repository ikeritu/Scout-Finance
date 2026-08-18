#!/usr/bin/env python3
"""QA gate for the v2.33B2 full-population refinement."""
from __future__ import annotations

import json
import lzma
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/v2_33b2"


def main() -> int:
    report = json.loads((OUTPUT / "eligibility_refinement_report_v2_33b2.json").read_text(encoding="utf-8"))
    with lzma.open(OUTPUT / "eligibility_census_v2_33b2.csv.xz", "rt", encoding="utf-8") as handle:
        census = pd.read_csv(handle, dtype=str, keep_default_na=False)
    assert report["phase"] == "v2.33B2" and report["status"] == "PASS"
    assert len(census) == census["row_number"].nunique() == 43_089
    assert report["prior_eligible"] == 23_888 and report["refined_rows"] == 2_723
    assert report["decision_summary"] == {
        "eligible_for_financial_enrichment": 21_165,
        "excluded_from_equity_opportunity_universe": 10_432,
        "requires_review_or_repair": 11_492,
    }
    eligible = census[census["eligibility_decision_v2_33b2"].eq("eligible_for_financial_enrichment_v2_33b2")]
    names = eligible["company_name"].str.upper()
    assert not eligible["source_provider"].eq("sgx_structured_endpoint").any()
    assert not eligible["source_provider"].eq("deutsche_boerse_xetra_all_tradable_instruments").any()
    assert not names.isin({"DUMMY", "TEST", "N/A", "UNKNOWN"}).any()
    assert not names.str.fullmatch(r"TEST[A-Z0-9._-]*", na=False).any()
    assert not names.str.contains(r"\b(?:ETFS?|ETNS?|EXCHANGE[- ]TRADED|PREFERRED)\b", regex=True).any()
    assert set(census["eligible_for_opportunity_ranking"]) == {"False"}
    assert report["operational_dataset_modified"] is False and report["operational_pointers_modified"] is False
    assert report["production_scoring_authorized"] is False and report["allow_ranking"] is False
    print("PASS: v2.33B2/43089/full-population-preflight/2723-refined/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
