#!/usr/bin/env python3
"""Offline QA for the v2.38AL global coverage matrix builder. No network,
no real licensed data -- every fixture value below is synthetic."""
from __future__ import annotations

import csv
import importlib.util
import lzma
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_global_coverage_matrix_v2_38al.py"


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_census_xz(path: Path, rows: list[dict]) -> None:
    fields = ["asset_id", "ticker", "company_name", "exchange", "country", "sector", "eligibility_status", "route_status"]
    with lzma.open(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def census_row(asset_id: str, ticker: str, name: str, exchange: str, country: str, eligibility: str = "ELIGIBLE", route: str = "SOURCE_RESEARCH_REQUIRED") -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": name, "exchange": exchange, "country": country, "sector": "", "eligibility_status": eligibility, "route_status": route}


def build_with(tmp: Path, census_rows: list[dict], us_fund_rows=None, us_price_rows=None, eu_identity_rows=None, eu_fund_rows=None, eu_growth_rows=None):
    mod_name = f"coverage_{id(census_rows)}"
    mod = module(SCRIPT, mod_name)
    census_path = tmp / "census.csv.xz"
    write_census_xz(census_path, census_rows)

    us_fund_path = tmp / "us_fund.csv"
    if us_fund_rows:
        fields = ["asset_id", "ticker", "company_name", "feature_quality_status"] + mod.US_GROWTH_FIELDS + mod.US_FUNDAMENTAL_RATIO_FIELDS
        write_csv(us_fund_path, us_fund_rows, fields)

    us_price_path = tmp / "us_price.csv"
    if us_price_rows:
        write_csv(us_price_path, us_price_rows, ["asset_id", "price_feature_quality_status"])

    eu_identity_path = tmp / "eu_identity.csv"
    if eu_identity_rows:
        write_csv(eu_identity_path, eu_identity_rows, ["asset_id", "resolution_status"])

    eu_fund_path = tmp / "eu_fund.csv"
    if eu_fund_rows:
        write_csv(eu_fund_path, eu_fund_rows, ["asset_id", "feature_quality_status"])

    eu_growth_path = tmp / "eu_growth.csv"
    if eu_growth_rows:
        write_csv(eu_growth_path, eu_growth_rows, ["asset_id", "feature_quality_status"])

    report = mod.build(census_path, us_fund_path, us_price_path, eu_identity_path, eu_fund_path, eu_growth_path, tmp / "out")
    with lzma.open(tmp / "out" / "global_coverage_matrix_v2_38al.csv.xz", "rt", encoding="utf-8", newline="") as f:
        rows = {r["asset_id"]: r for r in csv.DictReader(f)}
    return report, rows


def test_untouched_census_company_is_no_data_yet():
    """The overwhelming majority of the 43,089-company census: never
    identity-resolved by any phase yet. Must show up plainly, not be
    dropped, and never be guessed at."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [census_row("U1", "ZZZ", "UNTOUCHED CO", "ASX", "Australia")])
    assert report["companies_total"] == 1
    row = rows["U1"]
    assert row["identity_status"] == "NOT_ATTEMPTED"
    assert row["fundamentals_status"] == "NOT_ATTEMPTED"
    assert row["growth_status"] == "NOT_ATTEMPTED"
    assert row["price_status"] == "NOT_ATTEMPTED"
    assert row["overall_coverage_status"] == "NO_DATA_YET"


def test_europe_identity_only_reports_confirmed_price_gap_not_unattempted():
    """A real Europe asset (identity resolved via v2.38AB) with no
    fundamentals yet -- e.g. most of the 689 in-scope Europe assets
    outside GB/Austria today. price_status must report the CONFIRMED
    negative finding (v2.38AJ), not a generic 'not attempted'."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U2", "SIE", "SIEMENS AG", "Xetra", "DE")],
            eu_identity_rows=[{"asset_id": "U2", "resolution_status": "resolved"}],
        )
    row = rows["U2"]
    assert row["identity_status"] == "RESOLVED" and row["identity_source"] == "v2.38AB"
    assert row["fundamentals_status"] == "NOT_ATTEMPTED"
    assert row["price_status"] == "NOT_COLLECTED_NO_FREE_SOURCE_FOUND"
    assert row["overall_coverage_status"] == "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"


def test_europe_growth_ready_reaches_top_of_ladder_despite_no_price():
    """Real Austrian pattern: fundamentals AND growth both FEATURES_READY.
    Must reach GROWTH_READY even though price_status stays a confirmed
    gap -- price is deliberately never folded into this ladder."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U3", "OMV", "OMV AG", "Wien", "AT")],
            eu_identity_rows=[{"asset_id": "U3", "resolution_status": "resolved"}],
            eu_fund_rows=[{"asset_id": "U3", "feature_quality_status": "FEATURES_READY"}],
            eu_growth_rows=[{"asset_id": "U3", "feature_quality_status": "FEATURES_READY"}],
        )
    row = rows["U3"]
    assert row["fundamentals_status"] == "FEATURES_READY" and row["fundamentals_source"] == "v2.38X"
    assert row["growth_status"] == "FEATURES_READY" and row["growth_source"] == "v2.38AK"
    assert row["overall_coverage_status"] == "GROWTH_READY"
    assert row["price_status"] == "NOT_COLLECTED_NO_FREE_SOURCE_FOUND"


def test_us_company_splits_single_row_into_fundamentals_and_growth_ladder():
    """v2.38G packs ratios and growth into one row per US company -- this
    builder must split that back into the same two-stage ladder Europe
    uses, by presence of the exact growth vs ratio field names."""
    with tempfile.TemporaryDirectory() as tmp:
        us_row = {"asset_id": "U4", "ticker": "AAPL", "company_name": "APPLE INC", "feature_quality_status": "FEATURES_READY"}
        us_row.update({f: "0.1" for f in module(SCRIPT, "tmp_fields").US_GROWTH_FIELDS})
        us_row.update({f: "0.2" for f in module(SCRIPT, "tmp_fields2").US_FUNDAMENTAL_RATIO_FIELDS})
        report, rows = build_with(
            Path(tmp),
            [census_row("U4", "AAPL", "APPLE INC", "NASDAQ", "USA")],
            us_fund_rows=[us_row],
            us_price_rows=[{"asset_id": "U4", "price_feature_quality_status": "PRICE_FEATURES_READY"}],
        )
    row = rows["U4"]
    assert row["identity_status"] == "RESOLVED" and row["identity_source"] == "v2.38D-F"
    assert row["fundamentals_status"] == "FEATURES_READY" and row["fundamentals_source"] == "v2.38G"
    assert row["growth_status"] == "FEATURES_READY" and row["growth_source"] == "v2.38G"
    assert row["price_status"] == "PRICE_FEATURES_READY" and row["price_source"] == "v2.38H"
    assert row["overall_coverage_status"] == "GROWTH_READY"


def test_us_company_present_but_insufficient_ratios_stays_identity_only():
    """A US company with a resolved CIK (present in v2.38G) but zero
    computable ratios -- e.g. one of the 15 real INSUFFICIENT_FEATURE_
    EVIDENCE rows from v2.38G. Identity is still real and resolved; it
    must not be confused with a company nobody has looked at yet."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U5", "SHEL", "SHELL CO NO DATA", "NYSE", "USA")],
            us_fund_rows=[{"asset_id": "U5", "ticker": "SHEL", "company_name": "SHELL CO NO DATA", "feature_quality_status": "INSUFFICIENT_FEATURE_EVIDENCE"}],
        )
    row = rows["U5"]
    assert row["identity_status"] == "RESOLVED"
    assert row["fundamentals_status"] == "INSUFFICIENT_FEATURE_EVIDENCE"
    assert row["overall_coverage_status"] == "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"


def test_every_census_row_appears_exactly_once_never_dropped():
    """The defining property of this builder, unlike every other one in
    this pipeline: nothing is ever excluded or rejected -- all rows from
    the census must appear in the output, mixed coverage or none."""
    with tempfile.TemporaryDirectory() as tmp:
        rows_in = [
            census_row("U1", "AAA", "AAA CO", "NASDAQ", "USA"),
            census_row("U2", "BBB", "BBB AG", "Xetra", "DE"),
            census_row("U3", "CCC", "CCC LTD", "ASX", "Australia"),
        ]
        report, rows = build_with(Path(tmp), rows_in, eu_identity_rows=[{"asset_id": "U2", "resolution_status": "resolved"}])
    assert report["companies_total"] == 3
    assert set(rows) == {"U1", "U2", "U3"}


def test_missing_input_files_are_skipped_not_errors():
    """A future phase's file that doesn't exist yet (e.g. before v2.38AK
    ever ran) must never crash this builder -- it's treated as 0
    companies covered by that phase, same convention as v2.38X."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        mod = module(SCRIPT, "coverage_missing")
        census_path = tmp_path / "census.csv.xz"
        write_census_xz(census_path, [census_row("U1", "AAA", "AAA CO", "NASDAQ", "USA")])
        report = mod.build(
            census_path,
            tmp_path / "does_not_exist_fund.csv", tmp_path / "does_not_exist_price.csv",
            tmp_path / "does_not_exist_identity.csv", tmp_path / "does_not_exist_eu_fund.csv", tmp_path / "does_not_exist_eu_growth.csv",
            tmp_path / "out",
        )
    assert report["companies_total"] == 1
    assert report["overall_coverage_status_counts"] == {"NO_DATA_YET": 1}


CASES = [
    test_untouched_census_company_is_no_data_yet,
    test_europe_identity_only_reports_confirmed_price_gap_not_unattempted,
    test_europe_growth_ready_reaches_top_of_ladder_despite_no_price,
    test_us_company_splits_single_row_into_fundamentals_and_growth_ladder,
    test_us_company_present_but_insufficient_ratios_stays_identity_only,
    test_every_census_row_appears_exactly_once_never_dropped,
    test_missing_input_files_are_skipped_not_errors,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AL-global-coverage-matrix/full-census-shown/depth-ladder/no-drops/no-fabricated-status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
