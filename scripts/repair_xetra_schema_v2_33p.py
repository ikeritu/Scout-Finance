#!/usr/bin/env python3
"""Repair for the 1,424 Xetra rows held by v2.33B2 with reason
xetra_company_name_field_contains_classification_codes.

Root cause (confirmed against the full held set, not a sample): the
`company_name` column contains a market/index-segment classification
code from Deutsche Börse's own taxonomy (e.g. "DAX1" = DAX constituent,
"MDX1" = MDAX, "NAM0"/"GER0" = general domestic segments, "AST0" =
Austria, "ESP0" = Spain, etc.) instead of the issuer's name -- a column
mapping defect in the original ingestion, not missing data. All 1,424
rows carry a valid, unique ISIN (verified: 0 missing, 0 duplicates), so
the real company name is independently recoverable via ISIN lookup.

Uses OpenFIGI's free public /v3/mapping endpoint (no account, no API
key -- already approved for this kind of use in v2.33C/H) with
idType=ID_ISIN. Fail-closed: an ISIN only resolves if OpenFIGI returns
at least one record AND every returned record agrees on the same
`name` -- never guessed, never picked among disagreeing candidates.
No prices are touched here; this is identity/metadata repair only.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "outputs/full_universe_source_acquisition/v2_33b2_eligibility_refinement/eligibility_census_v2_33b2.csv.xz"
OUT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33p_sgx_xetra_metadata_repair"
HOLD_STATUS = "hold_provider_schema_xetra"
MAPPING_URL = "https://api.openfigi.com/v3/mapping"
BATCH_SIZE = 10  # no-key limit
MIN_SECONDS_BETWEEN_CALLS = 3.0  # no-key limit: 25 requests/minute
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0


def load_census() -> list[dict]:
    import lzma
    with lzma.open(CENSUS, "rt", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def map_batch(isins: list[str]) -> list[dict]:
    jobs = [{"idType": "ID_ISIN", "idValue": isin} for isin in isins]
    request = urllib.request.Request(
        MAPPING_URL,
        data=json.dumps(jobs).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                print(f"    rate-limited (429), waiting {RATE_LIMIT_BACKOFF_SECONDS:.0f}s before retry {attempt + 1}/{MAX_ATTEMPTS}", flush=True)
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            raise
    raise RuntimeError("rate limit retries exhausted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="perform the real OpenFIGI lookups (no account/key needed, but this is a real network pull)")
    parser.add_argument("--limit", type=int, default=0, help="cap on number of rows processed, 0 = all")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if not args.execute:
        print("BLOCKED: pass --execute only after explicit authorization")
        return 2

    rows = load_census()
    held = [r for r in rows if r["eligibility_decision_v2_33b2"] == HOLD_STATUS]
    if args.limit:
        held = held[: args.limit]

    repaired_rows = []
    unresolved_rows = []
    batches = [held[i : i + BATCH_SIZE] for i in range(0, len(held), BATCH_SIZE)]

    for i, batch in enumerate(batches):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        isins = [row["isin"] for row in batch]
        try:
            results = map_batch(isins)
        except Exception as exc:  # noqa: BLE001 - record and continue, never abort the whole run
            for row in batch:
                unresolved_rows.append({"row_number": row["row_number"], "isin": row["isin"], "reason": f"openfigi_call_failed_{type(exc).__name__}"})
            continue

        for row, result in zip(batch, results):
            data = result.get("data")
            if not data:
                unresolved_rows.append({"row_number": row["row_number"], "isin": row["isin"], "reason": "no_openfigi_record_for_isin"})
                continue
            names = {entry.get("name") for entry in data if entry.get("name")}
            if len(names) != 1:
                unresolved_rows.append({"row_number": row["row_number"], "isin": row["isin"], "reason": "disagreeing_names_across_openfigi_records"})
                continue
            repaired = dict(row)
            repaired["company_name"] = next(iter(names))
            repaired["missing_company_name"] = "False"
            repaired["eligibility_decision_v2_33b2"] = "repaired_v2_33p"
            repaired["eligibility_reason_v2_33b2"] = "xetra_company_name_recovered_via_openfigi_isin_exact_match"
            repaired_rows.append(repaired)

        print(f"[{i + 1}/{len(batches)}] batch done -- repaired so far: {len(repaired_rows)}, unresolved so far: {len(unresolved_rows)}", flush=True)

    report = {
        "phase": "v2.33P-xetra-metadata-repair",
        "held_rows": len(held),
        "repaired": len(repaired_rows),
        "unresolved": len(unresolved_rows),
        "unresolved_reasons": {
            reason: sum(1 for r in unresolved_rows if r["reason"] == reason)
            for reason in sorted({r["reason"] for r in unresolved_rows})
        },
        "repair_method": "openfigi_isin_exact_match_single_agreeing_name_only",
        "network_calls": len(batches),
        "credentials_used": False,
        "canonical_census_modified": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fields = list(held[0].keys())

        delta_path = OUT_DIR / "xetra_repair_delta_v2_33p.csv"
        tmp = delta_path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(repaired_rows)
        tmp.replace(delta_path)

        unresolved_path = OUT_DIR / "xetra_repair_unresolved_v2_33p.csv"
        tmp3 = unresolved_path.with_suffix(".csv.tmp")
        with tmp3.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["row_number", "isin", "reason"])
            writer.writeheader()
            writer.writerows(unresolved_rows)
        tmp3.replace(unresolved_path)

        report_path = OUT_DIR / "xetra_repair_report_v2_33p.json"
        tmp2 = report_path.with_suffix(".json.tmp")
        tmp2.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp2.replace(report_path)

    return 0 if not unresolved_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
