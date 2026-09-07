#!/usr/bin/env python3
"""Offline QA for the v2.38BI US Cboe-secondary SEC CIK resolver.
No network, no real licensed data -- every fixture value below is
synthetic (even the CIKs)."""
from __future__ import annotations

import csv
import importlib.util
import json
import lzma
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_us_cboe_secondary_identity_sec_v2_38bi.py"

COVERAGE_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "country", "sector",
    "census_eligibility_status", "census_route_status", "identity_status", "identity_source",
    "fundamentals_status", "fundamentals_source", "growth_status", "growth_source",
    "price_status", "price_source", "overall_coverage_status", "phase",
]


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def coverage_row(asset_id: str, ticker: str, name: str, identity_source: str = "v2.38BC") -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": name, "exchange": "CBOE_EUROPE", "country": "US", "sector": "",
            "census_eligibility_status": "ELIGIBLE", "census_route_status": "", "identity_status": "RESOLVED", "identity_source": identity_source,
            "fundamentals_status": "NOT_ATTEMPTED", "fundamentals_source": "", "growth_status": "NOT_ATTEMPTED", "growth_source": "",
            "price_status": "NOT_ATTEMPTED", "price_source": "", "overall_coverage_status": "IDENTITY_ONLY_NO_FUNDAMENTALS_YET", "phase": ""}


def write_coverage_xz(path: Path, rows: list[dict]) -> None:
    with lzma.open(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COVERAGE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sec_tickers(path: Path, rows: list[list]) -> None:
    path.write_text(json.dumps({"fields": ["cik", "name", "ticker", "exchange"], "data": rows}), encoding="utf-8")


def build_with(tmp: Path, coverage_rows: list[dict], sec_rows: list[list]):
    mod = module(SCRIPT, f"us_bi_{id(coverage_rows)}")
    coverage_path = tmp / "coverage.csv.xz"
    write_coverage_xz(coverage_path, coverage_rows)
    sec_path = tmp / "sec_tickers.json"
    write_sec_tickers(sec_path, sec_rows)
    report = mod.build(coverage_path, sec_path, tmp / "out")
    rows = {r["asset_id"]: r for r in csv.DictReader((tmp / "out" / "us_cboe_secondary_identity_sec_v2_38bi.csv").open(encoding="utf-8"))}
    return report, rows


def test_exact_normalized_name_match_resolves():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1TST", "Test Widget Co")],
            [[9000001, "TEST WIDGET CO", "TWCO", "Nasdaq"]],
        )
    row = rows["U1"]
    assert row["fetch_status"] == "resolved"
    assert row["cik"] == "0009000001"
    assert row["match_tier"] == "exact_normalized_name"


def test_state_of_incorporation_suffix_variants_are_stripped():
    """Real case: SEC appends a state-of-incorporation suffix in three
    different literal shapes across its own file -- /DE, / DE (with a
    space before the slash), and /DE/ (trailing slash too, seen on
    Northrop Grumman's real SEC record). All three must normalize the
    same as the plain name."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1AAA", "Acme Defense Corp"), coverage_row("U2", "1BBB", "Beta Energy Corp"), coverage_row("U3", "1CCC", "Gamma Foods Corp")],
            [[9000002, "ACME DEFENSE CORP /DE", "ACDF", "NYSE"], [9000003, "BETA ENERGY CORP / DE", "BETE", "NYSE"], [9000004, "GAMMA FOODS CORP /DE/", "GAFD", "NYSE"]],
        )
    assert rows["U1"]["fetch_status"] == "resolved" and rows["U1"]["cik"] == "0009000002"
    assert rows["U2"]["fetch_status"] == "resolved" and rows["U2"]["cik"] == "0009000003"
    assert rows["U3"]["fetch_status"] == "resolved" and rows["U3"]["cik"] == "0009000004"


def test_squashed_fallback_resolves_inconsistent_apostrophe_handling():
    """Real case: SEC deletes the apostrophe in some names with no space
    (MCDONALDS CORP) but replaces it with a space in others (O REILLY
    AUTOMOTIVE INC) -- a genuine SEC-side inconsistency, not a bug on
    either side. The squashed (whitespace-removed) key must still match."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1ORLY", "O'Reilly Automotive Inc")],
            [[9000005, "O REILLY AUTOMOTIVE INC", "ORLY", "Nasdaq"]],
        )
    row = rows["U1"]
    assert row["fetch_status"] == "resolved"
    assert row["cik"] == "0009000005"
    assert row["match_tier"] == "squashed_normalized_name"


def test_sorted_token_set_resolves_sec_inverted_surname_order():
    """Real case: a real, confirmed SEC quirk -- some registrants are
    filed under an inverted, surname-first legacy catalog order ("PRICE
    T ROWE GROUP INC" for T. Rowe Price, "SMITH A O CORP" for A.O.
    Smith). Comparing the sorted word set (not literal order) resolves
    these without a manual alias table."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1TRP", "T Rowe Price Group Inc")],
            [[9000006, "PRICE T ROWE GROUP INC", "TROW", "Nasdaq"]],
        )
    row = rows["U1"]
    assert row["fetch_status"] == "resolved"
    assert row["cik"] == "0009000006"
    assert row["match_tier"] == "sorted_token_set"


def test_multiple_tickers_same_cik_is_not_ambiguous():
    """Real case: many SEC registrants have several rows in
    company_tickers_exchange.json (common + preferred share classes, or
    a dual OTC listing) that all share the same CIK -- e.g. Comcast Corp
    (CMCSA on Nasdaq, CCZ on NYSE). This must resolve, never be treated
    as ambiguous, since it is the exact same real company either way."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1CCST", "Comcast Corp")],
            [[9000007, "COMCAST CORP", "CMCSA", "Nasdaq"], [9000007, "COMCAST CORP", "CCZ", "NYSE"]],
        )
    row = rows["U1"]
    assert row["fetch_status"] == "resolved"
    assert row["cik"] == "0009000007"


def test_two_distinct_companies_same_normalized_name_stays_ambiguous():
    """Fail-closed: if two DIFFERENT real CIKs collapse to the same
    normalized key, this must never guess -- stays ambiguous, same
    discipline as GLEIF/Firmenbuch/TOL resolution elsewhere in this
    project."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1DUP", "Duplicate Name Inc")],
            [[9000008, "DUPLICATE NAME INC", "DUPA", "Nasdaq"], [9000009, "DUPLICATE NAME INC", "DUPB", "NYSE"]],
        )
    row = rows["U1"]
    assert row["fetch_status"] == "ambiguous"
    assert row["fetch_reason"] == "ambiguous_multiple_distinct_companies_matched"
    assert row["cik"] == ""


def test_no_match_stays_unresolved_never_guessed():
    """Real case: companies genuinely absent from SEC's ticker file
    (delisted, acquired, or a real gap in that specific file) must stay
    unresolved, never fuzzy-matched to something plausible-looking."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1NOPE", "Totally Unmatched Holdings Inc")],
            [[9000010, "SOME OTHER COMPANY", "SOME", "Nasdaq"]],
        )
    row = rows["U1"]
    assert row["fetch_status"] == "unresolved"
    assert row["fetch_reason"] == "no_exact_normalized_name_match"


def test_only_v2_38bc_sourced_us_candidates_are_considered():
    """This module's job is narrowly the 628 US-country candidates that
    v2.38BC resolved via GLEIF -- not the original 555 US companies
    (already SEC CIK resolved since v2.38D) and not any other
    identity_source. A row with a different identity_source must be
    skipped entirely, never re-processed or double-counted."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "1IN", "In Scope Co", identity_source="v2.38BC"), coverage_row("U2", "1OUT", "Out Of Scope Co", identity_source="v2.38D")],
            [[9000011, "IN SCOPE CO", "INSC", "Nasdaq"], [9000012, "OUT OF SCOPE CO", "OUTS", "Nasdaq"]],
        )
    assert report["candidates_input"] == 1
    assert "U1" in rows and "U2" not in rows


def test_missing_sec_cache_blocks_cleanly_not_a_crash():
    with tempfile.TemporaryDirectory() as tmp:
        mod = module(SCRIPT, "us_bi_missing_cache")
        coverage_path = Path(tmp) / "coverage.csv.xz"
        write_coverage_xz(coverage_path, [coverage_row("U1", "1AAA", "Any Co")])
        report = mod.build(coverage_path, Path(tmp) / "does_not_exist.json", Path(tmp) / "out")
    assert report["status"] == "BLOCKED_SEC_CACHE_UNAVAILABLE"
    assert report["resolved"] == 0


CASES = [
    test_exact_normalized_name_match_resolves,
    test_state_of_incorporation_suffix_variants_are_stripped,
    test_squashed_fallback_resolves_inconsistent_apostrophe_handling,
    test_sorted_token_set_resolves_sec_inverted_surname_order,
    test_multiple_tickers_same_cik_is_not_ambiguous,
    test_two_distinct_companies_same_normalized_name_stays_ambiguous,
    test_no_match_stays_unresolved_never_guessed,
    test_only_v2_38bc_sourced_us_candidates_are_considered,
    test_missing_sec_cache_blocks_cleanly_not_a_crash,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BI-us-cboe-secondary-identity-sec/fail-closed/no-guessed-identity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
