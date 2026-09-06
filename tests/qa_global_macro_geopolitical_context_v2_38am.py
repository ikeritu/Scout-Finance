#!/usr/bin/env python3
"""Offline QA for the v2.38AM global macro/geopolitical context builder.
No network, no live news, no real licensed data -- every fixture value
below is synthetic."""
from __future__ import annotations

import csv
import importlib.util
import lzma
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_global_macro_geopolitical_context_v2_38am.py"

COVERAGE_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "country", "sector",
    "census_eligibility_status", "census_route_status", "identity_status", "identity_source",
    "fundamentals_status", "fundamentals_source", "growth_status", "growth_source",
    "price_status", "price_source", "overall_coverage_status", "phase",
]
US_SIGNAL_FIELDS = ["asset_id", "ticker", "company_name", "fundamental_signal_summary", "price_signal_summary", "risk_signal_summary"]
GB_SIC_FIELDS = ["asset_id", "ticker", "company_name", "sic_codes", "sic_descriptions"]
FRANCE_SECTOR_FIELDS = ["asset_id", "ticker", "company_name", "naf_code", "naf_description_en"]
NETHERLANDS_SECTOR_FIELDS = ["asset_id", "ticker", "company_name", "industries", "non_official_source_caveat"]
GENERALIZED_WIKIDATA_SECTOR_FIELDS = ["asset_id", "ticker", "company_name", "country", "industries", "non_official_source_caveat"]
AUSTRIA_ONACE_FIELDS = ["asset_id", "ticker", "company_name", "fetch_status", "onace_code", "onace_description_en", "purpose_de"]


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


def write_coverage_xz(path: Path, rows: list[dict]) -> None:
    with lzma.open(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COVERAGE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def coverage_row(asset_id: str, ticker: str, name: str, country: str, identity_status: str = "RESOLVED", overall: str = "IDENTITY_ONLY_NO_FUNDAMENTALS_YET") -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": name, "exchange": "", "country": country, "sector": "",
            "census_eligibility_status": "ELIGIBLE", "census_route_status": "", "identity_status": identity_status, "identity_source": "",
            "fundamentals_status": "NOT_ATTEMPTED", "fundamentals_source": "", "growth_status": "NOT_ATTEMPTED", "growth_source": "",
            "price_status": "NOT_ATTEMPTED", "price_source": "", "overall_coverage_status": overall, "phase": ""}


def build_with(tmp: Path, coverage_rows: list[dict], us_signal_rows=None, gb_sic_rows=None, france_sector_rows=None, netherlands_sector_rows=None, generalized_wikidata_sector_rows=None, austria_onace_rows=None):
    mod = module(SCRIPT, f"geo_{id(coverage_rows)}")
    coverage_path = tmp / "coverage.csv.xz"
    write_coverage_xz(coverage_path, coverage_rows)
    us_signal_path = tmp / "us_signal.csv"
    if us_signal_rows:
        write_csv(us_signal_path, us_signal_rows, US_SIGNAL_FIELDS)
    gb_sic_path = tmp / "gb_sic.csv"
    if gb_sic_rows:
        write_csv(gb_sic_path, gb_sic_rows, GB_SIC_FIELDS)
    france_sector_path = tmp / "france_sector.csv"
    if france_sector_rows:
        write_csv(france_sector_path, france_sector_rows, FRANCE_SECTOR_FIELDS)
    netherlands_sector_path = tmp / "netherlands_sector.csv"
    if netherlands_sector_rows:
        write_csv(netherlands_sector_path, netherlands_sector_rows, NETHERLANDS_SECTOR_FIELDS)
    generalized_wikidata_sector_path = tmp / "generalized_wikidata_sector.csv"
    if generalized_wikidata_sector_rows:
        write_csv(generalized_wikidata_sector_path, generalized_wikidata_sector_rows, GENERALIZED_WIKIDATA_SECTOR_FIELDS)
    austria_onace_path = tmp / "austria_onace.csv"
    if austria_onace_rows:
        write_csv(austria_onace_path, austria_onace_rows, AUSTRIA_ONACE_FIELDS)
    report = mod.build(coverage_path, us_signal_path, gb_sic_path, france_sector_path, netherlands_sector_path, generalized_wikidata_sector_path, austria_onace_path, tmp / "out")
    rows = {r["asset_id"]: r for r in csv.DictReader((tmp / "out" / "global_macro_geopolitical_context_v2_38am.csv").open(encoding="utf-8"))}
    return report, rows


def test_only_identity_resolved_companies_get_context():
    """The vast majority of the 43,089-company census has no resolved
    identity yet -- this module must never guess macro context for a
    company we haven't even confirmed the identity of."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [
            coverage_row("U1", "AAA", "AAA CO", "USA", identity_status="NOT_ATTEMPTED"),
            coverage_row("U2", "BBB", "BBB AG", "DE", identity_status="RESOLVED"),
        ])
    assert report["identity_resolved_companies_input"] == 1
    assert "U1" not in rows and "U2" in rows


def test_us_company_with_signal_text_matches_sector_theme():
    """A real US company with the v2.38J narrative signal text mentioning
    a sector keyword (semiconductor) must reach MACRO_CONTEXT_READY and
    include the AI_SEMICONDUCTORS theme."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "NVDA", "SEMICONDUCTOR CO", "USA")],
            us_signal_rows=[{"asset_id": "U1", "ticker": "NVDA", "company_name": "SEMICONDUCTOR CO", "fundamental_signal_summary": "revenue growth positive; semiconductor demand strong", "price_signal_summary": "", "risk_signal_summary": ""}],
        )
    row = rows["U1"]
    assert row["macro_context_status"] == "MACRO_CONTEXT_READY"
    assert "AI_SEMICONDUCTORS" in row["applicable_themes"].split("|")


def test_europe_company_with_no_text_gets_partial_status_and_honest_limitation():
    """A real case: a European company (e.g. from v2.38AB identity
    resolution) with no narrative text at all and a company name with no
    sector keyword. Must be MACRO_CONTEXT_PARTIAL with a limitation
    message that specifically names the missing-narrative-text gap, not
    the generic one used when text exists but nothing matched."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "XYZ", "XYZ HOLDING SE", "DE")])
    row = rows["U1"]
    assert row["macro_context_status"] == "MACRO_CONTEXT_PARTIAL"
    assert "No narrative signal text is available" in row["macro_limitations"]
    assert row["sector_text_source"] == ""


def test_gb_company_with_real_sic_description_reaches_ready_status():
    """Real case: v2.38AN fetched real UK SIC codes (e.g. Barclays ->
    64191 'Banks') that v2.38Y's search-endpoint approach never captured.
    Feeding that real description into the same matcher must reach
    MACRO_CONTEXT_READY via BANK_CREDIT_CYCLE, attacking the 0/689 Europe
    sector-match finding from this module's first run."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "BCY", "BARCLAYS PLC", "GB")],
            gb_sic_rows=[{"asset_id": "U1", "ticker": "BCY", "company_name": "BARCLAYS PLC", "sic_codes": "64191", "sic_descriptions": "Banks"}],
        )
    row = rows["U1"]
    assert row["macro_context_status"] == "MACRO_CONTEXT_READY"
    assert "BANK_CREDIT_CYCLE" in row["applicable_themes"].split("|")
    assert row["sector_text_source"] == "v2.38AN"


def test_france_company_with_real_naf_description_reaches_ready_status():
    """Real case: v2.38AO fetched Soitec's real NAF code (26.11Z ->
    'Manufacture of electronic components'). Confirms the France sector
    source feeds the same matcher and is correctly attributed."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "SOH1", "SOITEC S.A.", "FR")],
            france_sector_rows=[{"asset_id": "U1", "ticker": "SOH1", "company_name": "SOITEC S.A.", "naf_code": "72.11Z", "naf_description_en": "Research and development in biotechnology"}],
        )
    row = rows["U1"]
    assert row["macro_context_status"] == "MACRO_CONTEXT_READY"
    assert "HEALTHCARE_REGULATION" in row["applicable_themes"].split("|")
    assert row["sector_text_source"] == "v2.38AO"


def test_netherlands_wikidata_source_matches_and_carries_non_official_caveat():
    """Real case: ASML Holding's Wikidata industry ('semiconductor
    industry') must reach MACRO_CONTEXT_READY via v2.38AQ, and its
    limitation text must carry the non-official-source caveat -- unlike
    GB/France, which are official government sources and get no such
    caveat appended."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "ASME", "ASML HOLDING", "NL")],
            netherlands_sector_rows=[{"asset_id": "U1", "ticker": "ASME", "company_name": "ASML HOLDING", "industries": "semiconductor industry", "non_official_source_caveat": "Sourced from Wikidata -- NOT an official government registry."}],
        )
    row = rows["U1"]
    assert row["macro_context_status"] == "MACRO_CONTEXT_READY"
    assert "AI_SEMICONDUCTORS" in row["applicable_themes"].split("|")
    assert row["sector_text_source"] == "v2.38AQ"
    assert "NOT an official government registry" in row["macro_limitations"]


def test_switzerland_generalized_wikidata_source_matches_and_carries_caveat():
    """Real case: v2.38AR generalized v2.38AQ's approach to Switzerland
    after live-testing confirmed the Swiss UID register's public tier
    never exposes NOGACode. Novartis's real Wikidata industry
    ('pharmaceutical industry') must reach MACRO_CONTEXT_READY via
    v2.38AR, distinct from v2.38AQ's own Netherlands-specific source."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "NOT", "NOVARTIS", "CH")],
            generalized_wikidata_sector_rows=[{"asset_id": "U1", "ticker": "NOT", "company_name": "NOVARTIS", "country": "CH", "industries": "pharmaceutical industry", "non_official_source_caveat": "Sourced from Wikidata -- NOT an official government registry."}],
        )
    row = rows["U1"]
    assert row["macro_context_status"] == "MACRO_CONTEXT_READY"
    assert "HEALTHCARE_REGULATION" in row["applicable_themes"].split("|")
    assert row["sector_text_source"] == "v2.38AR"
    assert "NOT an official government registry" in row["macro_limitations"]


def test_austria_onace_source_matches_bank_via_german_purpose_substring():
    """Real case (Erste Group Bank AG): v2.38AS provides both the
    English-translated ÖNACE description ('Other monetary intermediation'
    -- doesn't literally contain 'bank') and the raw German purpose text
    ('Bankgeschäfte') -- which DOES match the BANK_CREDIT_CYCLE keyword
    'bank' as a substring, a real free win from including the untranslated
    official filing text rather than only the translated description."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "EBO", "ERSTE GROUP BANK AG", "AT")],
            austria_onace_rows=[{"asset_id": "U1", "ticker": "EBO", "company_name": "ERSTE GROUP BANK AG", "fetch_status": "resolved", "onace_code": "64190", "onace_description_en": "Other monetary intermediation", "purpose_de": "Bankgeschäfte"}],
        )
    row = rows["U1"]
    assert row["macro_context_status"] == "MACRO_CONTEXT_READY"
    assert "BANK_CREDIT_CYCLE" in row["applicable_themes"].split("|")
    assert row["sector_text_source"] == "v2.38AS"


def test_austria_onace_not_yet_resolved_never_used_as_source():
    """A company still pending (fetch_status='error', a real state given
    firmenakte.at's confirmed intermittent connectivity) must never be
    treated as if it had real sector data."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [coverage_row("U1", "OMV", "OMV AKTIENGESELLSCHAFT", "AT")],
            austria_onace_rows=[{"asset_id": "U1", "ticker": "OMV", "company_name": "OMV AKTIENGESELLSCHAFT", "fetch_status": "error", "onace_code": "", "onace_description_en": "", "purpose_de": ""}],
        )
    row = rows["U1"]
    assert row["sector_text_source"] == ""
    assert row["macro_context_status"] == "MACRO_CONTEXT_PARTIAL"


def test_eurozone_country_gets_both_eu_and_eurozone_themes_not_uk_or_chf():
    """Real case: Austria (AT) is both an EU member and a Eurozone member
    -- must get EU_SINGLE_MARKET_REGULATION AND EUROZONE_ECB_MONETARY_
    POLICY, but never the UK or Swiss-specific themes."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "OMV", "OMV AG", "AT")])
    themes = rows["U1"]["applicable_themes"].split("|")
    assert "EU_SINGLE_MARKET_REGULATION" in themes
    assert "EUROZONE_ECB_MONETARY_POLICY" in themes
    assert "UK_POST_BREXIT_TRADE_FRICTION" not in themes
    assert "CHF_SAFE_HAVEN_DYNAMICS" not in themes


def test_gb_gets_brexit_theme_not_eu_or_eurozone():
    """Real case: the UK left the EU -- must get UK_POST_BREXIT_TRADE_
    FRICTION only, never the EU/Eurozone themes despite being a real,
    long-standing European market covered by this pipeline (v2.38Y)."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "KGF", "KINGFISHER PLC", "GB")])
    themes = rows["U1"]["applicable_themes"].split("|")
    assert "UK_POST_BREXIT_TRADE_FRICTION" in themes
    assert "EU_SINGLE_MARKET_REGULATION" not in themes
    assert "EUROZONE_ECB_MONETARY_POLICY" not in themes


def test_switzerland_gets_chf_theme_not_eu_or_eurozone():
    """Real case: Switzerland is in neither the EU nor the Eurozone --
    must get only the CHF safe-haven theme among the country-specific
    ones."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "NESN", "SWISS HOLDING AG", "CH")])
    themes = rows["U1"]["applicable_themes"].split("|")
    assert "CHF_SAFE_HAVEN_DYNAMICS" in themes
    assert "EU_SINGLE_MARKET_REGULATION" not in themes
    assert "UK_POST_BREXIT_TRADE_FRICTION" not in themes


def test_missing_or_duplicate_identity_is_rejected_not_silently_dropped():
    with tempfile.TemporaryDirectory() as tmp:
        rows_in = [
            coverage_row("U1", "AAA", "AAA CO", "USA"), coverage_row("U1", "AAA", "DUPLICATE OF U1", "USA"),  # second is a real duplicate asset_id
            coverage_row("U2", "BBB", "", "USA"),  # missing company_name
        ]
        report, rows = build_with(Path(tmp), rows_in)
    assert report["rejected_rows"] == 2  # the duplicate U1 row, and the blank-name U2 row
    assert report["companies_context_built"] == 1
    assert "U1" in rows and "U2" not in rows


def test_missing_us_signal_file_is_skipped_not_an_error():
    """Before v2.38J ever ran, or in a test environment without it, this
    must degrade gracefully to company_name-only matching, never crash."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "AAA", "GENERIC HOLDING CO", "USA")])
    assert report["companies_context_built"] == 1
    assert rows["U1"]["macro_context_status"] == "MACRO_CONTEXT_PARTIAL"


CASES = [
    test_only_identity_resolved_companies_get_context,
    test_us_company_with_signal_text_matches_sector_theme,
    test_europe_company_with_no_text_gets_partial_status_and_honest_limitation,
    test_gb_company_with_real_sic_description_reaches_ready_status,
    test_france_company_with_real_naf_description_reaches_ready_status,
    test_netherlands_wikidata_source_matches_and_carries_non_official_caveat,
    test_switzerland_generalized_wikidata_source_matches_and_carries_caveat,
    test_austria_onace_source_matches_bank_via_german_purpose_substring,
    test_austria_onace_not_yet_resolved_never_used_as_source,
    test_eurozone_country_gets_both_eu_and_eurozone_themes_not_uk_or_chf,
    test_gb_gets_brexit_theme_not_eu_or_eurozone,
    test_switzerland_gets_chf_theme_not_eu_or_eurozone,
    test_missing_or_duplicate_identity_is_rejected_not_silently_dropped,
    test_missing_us_signal_file_is_skipped_not_an_error,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AM-global-macro-geopolitical-context/country-themes/no-guessed-identity/honest-limitations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
