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


def build_with(tmp: Path, coverage_rows: list[dict], us_signal_rows=None):
    mod = module(SCRIPT, f"geo_{id(coverage_rows)}")
    coverage_path = tmp / "coverage.csv.xz"
    write_coverage_xz(coverage_path, coverage_rows)
    us_signal_path = tmp / "us_signal.csv"
    if us_signal_rows:
        write_csv(us_signal_path, us_signal_rows, US_SIGNAL_FIELDS)
    report = mod.build(coverage_path, us_signal_path, tmp / "out")
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
