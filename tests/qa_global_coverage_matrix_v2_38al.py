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


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(__import__("json").dumps(record) + "\n")


def build_with(
    tmp: Path, census_rows: list[dict], us_fund_rows=None, us_price_rows=None, eu_identity_rows=None, eu_fund_rows=None,
    eu_growth_rows=None, joby_features_rows=None, av_mismatch_rows=None, lux_aw_rcs_rows=None, lux_ax_fund_records=None,
    lux_be_rcs_rows=None, lux_be_fund_records=None, lux_be_fund_compartment_records=None, at_bg_rows=None, fi_bh_rows=None,
    cboe_bulk_rows=None,
):
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

    joby_features_path = tmp / "joby_features.csv"
    if joby_features_rows:
        fields = ["asset_id"] + mod.US_GROWTH_FIELDS + mod.US_FUNDAMENTAL_RATIO_FIELDS
        write_csv(joby_features_path, joby_features_rows, fields)

    av_mismatch_path = tmp / "av_mismatch.csv"
    if av_mismatch_rows:
        write_csv(av_mismatch_path, av_mismatch_rows, ["asset_id", "real_home_country_guess", "resolution_status"])

    lux_aw_rcs_path = tmp / "lux_aw_rcs.csv"
    if lux_aw_rcs_rows:
        write_csv(lux_aw_rcs_path, lux_aw_rcs_rows, ["asset_id", "rcs_number"])

    lux_ax_fund_path = tmp / "lux_ax_fund.jsonl"
    if lux_ax_fund_records:
        write_jsonl(lux_ax_fund_path, lux_ax_fund_records)

    lux_be_rcs_path = tmp / "lux_be_rcs.csv"
    if lux_be_rcs_rows:
        write_csv(lux_be_rcs_path, lux_be_rcs_rows, ["asset_id", "gleif_lookup_status", "rcs_number"])

    lux_be_fund_path = tmp / "lux_be_fund.jsonl"
    if lux_be_fund_records:
        write_jsonl(lux_be_fund_path, lux_be_fund_records)

    lux_be_fund_compartments_path = tmp / "lux_be_fund_compartments.jsonl"
    if lux_be_fund_compartment_records:
        write_jsonl(lux_be_fund_compartments_path, lux_be_fund_compartment_records)

    at_bg_path = tmp / "at_bg.csv"
    if at_bg_rows:
        write_csv(at_bg_path, at_bg_rows, ["asset_id", "gleif_lookup_status"])

    fi_bh_path = tmp / "fi_bh.csv"
    if fi_bh_rows:
        write_csv(fi_bh_path, fi_bh_rows, ["asset_id", "fetch_status", "tol_description_en"])

    cboe_bulk_path = tmp / "cboe_bulk.csv"
    if cboe_bulk_rows:
        write_csv(cboe_bulk_path, cboe_bulk_rows, ["asset_id", "status", "country"])

    report = mod.build(
        census_path, us_fund_path, us_price_path, eu_identity_path, eu_fund_path, eu_growth_path,
        joby_features_path, av_mismatch_path, lux_aw_rcs_path, lux_ax_fund_path, lux_be_rcs_path,
        lux_be_fund_path, lux_be_fund_compartments_path, at_bg_path, fi_bh_path, cboe_bulk_path, tmp / "out",
    )
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
        missing = tmp_path / "does_not_exist"
        report = mod.build(
            census_path,
            tmp_path / "does_not_exist_fund.csv", tmp_path / "does_not_exist_price.csv",
            tmp_path / "does_not_exist_identity.csv", tmp_path / "does_not_exist_eu_fund.csv", tmp_path / "does_not_exist_eu_growth.csv",
            missing / "joby.csv", missing / "av.csv", missing / "aw.csv", missing / "ax.jsonl", missing / "be_rcs.csv",
            missing / "be_fund.jsonl", missing / "be_fund_compartments.jsonl", missing / "at.csv", missing / "fi.csv", missing / "cboe.csv",
            tmp_path / "out",
        )
    assert report["companies_total"] == 1
    assert report["overall_coverage_status_counts"] == {"NO_DATA_YET": 1}


def test_luxembourg_real_company_with_fundamentals_reaches_fundamentals_ready():
    """Real case: a v2.38AV-identified Luxembourg company with v2.38AX
    concepts for all 4 tracked fundamentals -- country gets overridden to
    LU (the census row itself carries no country for these Cboe/Xetra
    placeholder rows), and the ladder reaches FUNDAMENTALS_READY_NO_GROWTH_YET
    since Luxembourg has no multi-year growth computed yet."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U10", "RRTL", "RTL GROUP", "XETR", "")],
            av_mismatch_rows=[{"asset_id": "U10", "real_home_country_guess": "Luxembourg", "resolution_status": "resolved"}],
            lux_ax_fund_records=[{"asset_id": "U10", "fetch_status": "resolved", "concepts": {"revenue": {"value": "1"}, "net_profit": {"value": "1"}, "total_assets": {"value": "1"}, "equity": {"value": "1"}}}],
        )
    row = rows["U10"]
    assert row["country"] == "LU"
    assert row["identity_status"] == "RESOLVED"
    assert row["fundamentals_status"] == "FEATURES_READY"
    assert row["overall_coverage_status"] == "FUNDAMENTALS_READY_NO_GROWTH_YET"


def test_luxembourg_fund_compartment_is_never_treated_as_a_company():
    """Real case from v2.38BE: a GLEIF-resolved Luxembourg entity whose
    RCS-equivalent identifier does not start with "B" is an investment
    fund sub-compartment, not an operating company -- must reach the
    dedicated IDENTITY_ONLY_NOT_AN_OPERATING_COMPANY status, never a
    fabricated fundamentals figure."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U11", "ENYm", "ENERGY", "XETR", "")],
            lux_be_rcs_rows=[{"asset_id": "U11", "gleif_lookup_status": "resolved", "rcs_number": "O00000010_00000025"}],
        )
    row = rows["U11"]
    assert row["fundamentals_status"] == "NOT_APPLICABLE_INVESTMENT_FUND_NOT_AN_OPERATING_COMPANY"
    assert row["overall_coverage_status"] == "IDENTITY_ONLY_NOT_AN_OPERATING_COMPANY"


def test_austria_confirmed_quota_blocker_is_distinct_from_not_attempted():
    """Real case from v2.38BG: identity resolved via GLEIF, but
    fundamentals confirmed blocked by an exhausted firmenakte.at quota
    (live HTTP 429) -- must read as a confirmed real blocker, never
    identical to a company nobody has looked at yet."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U12", "ADKOv", "Addiko Bank AG", "XETR", "")],
            at_bg_rows=[{"asset_id": "U12", "gleif_lookup_status": "resolved"}],
        )
    row = rows["U12"]
    assert row["country"] == "AT"
    assert row["fundamentals_status"] == "BLOCKED_PROVIDER_QUOTA_EXHAUSTED"
    assert row["overall_coverage_status"] == "IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED"


def test_finland_carries_real_sector_but_confirmed_no_fundamentals_source():
    """Real case from v2.38BH: PRH gives a real English sector
    description (unlike every other country, no translation needed), but
    the confirmed live finding is that its XBRL API has zero coverage for
    large caps -- fundamentals must show that confirmed reason, not
    NOT_ATTEMPTED, while sector still gets populated with real data."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U13", "ACG1Vh", "Aspocomp Group Oyj", "XETR", "")],
            fi_bh_rows=[{"asset_id": "U13", "fetch_status": "resolved", "tol_description_en": "Manufacture of electronic components"}],
        )
    row = rows["U13"]
    assert row["country"] == "FI"
    assert row["sector"] == "Manufacture of electronic components"
    assert row["fundamentals_status"] == "NOT_COLLECTED_NO_FREE_SOURCE_FOUND_FOR_LARGE_CAPS"
    assert row["overall_coverage_status"] == "IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED"


def test_joby_aviation_country_corrected_from_cayman_isin_prefix_to_real_us():
    """Real case from v2.38AZ/BA: the Xetra listing's ISIN prefix implies
    Cayman Islands, but the real, current company is Joby Aviation, Inc.,
    a Delaware/SEC-reporting company -- the coverage matrix must show the
    corrected real country and cross-reference the real company's own SEC
    fundamentals, never inventing a second, separate figure."""
    with tempfile.TemporaryDirectory() as tmp:
        mod = module(SCRIPT, "tmp_joby")
        joby_asset_id = mod.JOBY_CAYMAN_ASSET_ID
        us_growth = {f: "0.1" for f in mod.US_GROWTH_FIELDS}
        us_ratios = {f: "0.2" for f in mod.US_FUNDAMENTAL_RATIO_FIELDS}
        report, rows = build_with(
            Path(tmp),
            [census_row(joby_asset_id, "8TQ", "Joby Aviation", "XETR", "")],
            joby_features_rows=[{"asset_id": joby_asset_id, **us_growth, **us_ratios}],
        )
    row = rows[joby_asset_id]
    assert row["country"] == "US"
    assert row["fundamentals_status"] == "FEATURES_READY"
    assert "v2.38BA" in row["fundamentals_source"]


def test_av_other_country_gets_real_country_code_from_isin_prefix():
    """Real case from v2.38AV: Bulgaria/Liechtenstein/Malta, identity
    only, real ISO country code populated from the readable country
    name."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U14", "SLYG", "SHELLY GROUP PLC", "XETR", "")],
            av_mismatch_rows=[{"asset_id": "U14", "real_home_country_guess": "Bulgaria", "resolution_status": "resolved"}],
        )
    row = rows["U14"]
    assert row["country"] == "BG"
    assert row["identity_status"] == "RESOLVED"
    assert row["overall_coverage_status"] == "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"


def test_cboe_bulk_fallback_covers_everything_without_a_richer_source():
    """Real case from v2.38BC: the 3,766-row bulk identity resolution
    fills in real country + identity for any asset not already covered by
    a more specific pipeline (US, original Europe, Luxembourg, Austria,
    Finland, or the other v2.38AV countries)."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U15", "1VOW3m", "Volkswagen AG", "CBOE_EUROPE", "")],
            cboe_bulk_rows=[{"asset_id": "U15", "status": "resolved", "country": "DE"}],
        )
    row = rows["U15"]
    assert row["country"] == "DE"
    assert row["identity_status"] == "RESOLVED" and row["identity_source"] == "v2.38BC"
    assert row["overall_coverage_status"] == "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"


def test_original_689_europe_identity_takes_priority_over_new_sources():
    """A company already covered by the original, richer v2.38AB/X/AK
    pipeline must never be downgraded or reclassified by the newer, less
    detailed bulk sources, even if it happens to also appear there."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [census_row("U16", "OMV", "OMV AG", "Wien", "AT")],
            eu_identity_rows=[{"asset_id": "U16", "resolution_status": "resolved"}],
            eu_fund_rows=[{"asset_id": "U16", "feature_quality_status": "FEATURES_READY"}],
            at_bg_rows=[{"asset_id": "U16", "gleif_lookup_status": "resolved"}],
        )
    row = rows["U16"]
    assert row["identity_source"] == "v2.38AB"
    assert row["fundamentals_status"] == "FEATURES_READY"


CASES = [
    test_untouched_census_company_is_no_data_yet,
    test_europe_identity_only_reports_confirmed_price_gap_not_unattempted,
    test_europe_growth_ready_reaches_top_of_ladder_despite_no_price,
    test_us_company_splits_single_row_into_fundamentals_and_growth_ladder,
    test_us_company_present_but_insufficient_ratios_stays_identity_only,
    test_every_census_row_appears_exactly_once_never_dropped,
    test_missing_input_files_are_skipped_not_errors,
    test_luxembourg_real_company_with_fundamentals_reaches_fundamentals_ready,
    test_luxembourg_fund_compartment_is_never_treated_as_a_company,
    test_austria_confirmed_quota_blocker_is_distinct_from_not_attempted,
    test_finland_carries_real_sector_but_confirmed_no_fundamentals_source,
    test_joby_aviation_country_corrected_from_cayman_isin_prefix_to_real_us,
    test_av_other_country_gets_real_country_code_from_isin_prefix,
    test_cboe_bulk_fallback_covers_everything_without_a_richer_source,
    test_original_689_europe_identity_takes_priority_over_new_sources,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AL-global-coverage-matrix/full-census-shown/depth-ladder/no-drops/no-fabricated-status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
