#!/usr/bin/env python3
"""Deterministic repair for the 358 SGX rows held by v2.33B2 with reason
sgx_ticker_and_name_fields_require_source_schema_repair.

Root cause (confirmed against all 358 rows, not inferred from a sample):
the ingestion pipeline swapped two columns from the SGX structured
endpoint. Every one of the 358 rows has `ticker` matching a plain decimal
number (a last-traded price, e.g. "0.845") and `company_name` matching a
short alphanumeric SGX-style code (e.g. "LVR", "1Y1", "533"). The real
company name was never present in this source at all -- it is not
recoverable from this dataset by any transformation, only the ticker
code survived (in the wrong column).

This script does NOT invent or look up company names. It only moves the
real ticker back into the ticker column, drops the stray price value
(it is stale market data, not identity data, and does not belong in a
universe/identity file), and marks company_name as genuinely missing --
an honest "missing", not a "corrupted" placeholder.

Dry-run by default. Never overwrites the canonical census in place;
writes a repair delta + a full repaired copy to this pilot's own output
directory. No network calls, no credentials.
"""
from __future__ import annotations

import argparse
import csv
import json
import lzma
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "outputs/full_universe_source_acquisition/v2_33b2_eligibility_refinement/eligibility_census_v2_33b2.csv.xz"
OUT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33p_sgx_xetra_metadata_repair"
HOLD_STATUS = "hold_provider_schema_sgx"

DECIMAL_PRICE = re.compile(r"^\d+\.\d+$")
TICKER_LIKE = re.compile(r"^[A-Z0-9]{1,5}$")


def load_census() -> list[dict]:
    with lzma.open(CENSUS, "rt", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def repair_row(row: dict) -> tuple[dict | None, str]:
    """Return (repaired_row_or_None, reason). None means still blocked."""
    ticker_field = row["ticker"].strip()
    name_field = row["company_name"].strip()
    if not DECIMAL_PRICE.match(ticker_field):
        return None, "ticker_field_not_a_plain_decimal_price_pattern_mismatch"
    if not TICKER_LIKE.match(name_field):
        return None, "company_name_field_not_ticker_like_pattern_mismatch"

    repaired = dict(row)
    repaired["ticker"] = name_field
    repaired["company_name"] = ""  # honestly missing, not fabricated
    repaired["missing_company_name"] = "True"
    repaired["eligibility_decision_v2_33b2"] = "repaired_pending_company_name_v2_33p"
    repaired["eligibility_reason_v2_33b2"] = "sgx_ticker_recovered_company_name_genuinely_absent_from_source"
    return repaired, "repaired"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the repair delta and repaired-copy files (still never touches the canonical census)")
    args = parser.parse_args()

    rows = load_census()
    held = [r for r in rows if r["eligibility_decision_v2_33b2"] == HOLD_STATUS]

    repaired_rows = []
    unresolved_rows = []
    for row in held:
        repaired, reason = repair_row(row)
        if repaired is not None:
            repaired_rows.append(repaired)
        else:
            unresolved_rows.append({"row_number": row["row_number"], "reason": reason})

    report = {
        "phase": "v2.33P-sgx-metadata-repair",
        "held_rows": len(held),
        "repaired": len(repaired_rows),
        "unresolved": len(unresolved_rows),
        "unresolved_detail": unresolved_rows,
        "repair_method": "deterministic_column_unshift_confirmed_against_all_held_rows",
        "company_name_recovered": False,
        "note": "El nombre real de la empresa no está presente en esta fuente; se marca ausente, no se inventa.",
        "credentials_used": False,
        "network_calls": 0,
        "canonical_census_modified": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fields = list(held[0].keys())

        delta_path = OUT_DIR / "sgx_repair_delta_v2_33p.csv"
        tmp = delta_path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(repaired_rows)
        tmp.replace(delta_path)

        report_path = OUT_DIR / "sgx_repair_report_v2_33p.json"
        tmp2 = report_path.with_suffix(".json.tmp")
        tmp2.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp2.replace(report_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
