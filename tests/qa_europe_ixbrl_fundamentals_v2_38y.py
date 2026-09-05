#!/usr/bin/env python3
"""Offline QA for the v2.38Y iXBRL normalizer (same extraction logic as
v2.38W, run again for the full 40-company expansion). Uses a small
synthetic iXBRL fixture (never a real, licensed filing) that reproduces
the exact structural shapes confirmed in v2.38W's real document: a target
concept with a plain (non-dimensional) context, a sibling dimensional
breakdown context sharing the SAME date, and numeric text with spaces
interspersed plus a thousands-comma. No network calls.
"""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/normalize_europe_ixbrl_fundamentals_v2_38y.py"

FIXTURE_XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
      xmlns:ifrs-full="http://xbrl.ifrs.org/taxonomy/2021-03-24/ifrs-full">
<head><ix:header>
  <ix:resources>
    <xbrli:context id="c-current"><xbrli:entity><xbrli:identifier scheme="x">E1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-12-31</xbrli:instant></xbrli:period></xbrli:context>
    <xbrli:context id="c-prior"><xbrli:entity><xbrli:identifier scheme="x">E1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2024-12-31</xbrli:instant></xbrli:period></xbrli:context>
    <xbrli:context id="c-current-dim"><xbrli:entity><xbrli:identifier scheme="x">E1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:instant>2025-12-31</xbrli:instant></xbrli:period><xbrli:scenario><xbrldi:explicitMember dimension="ifrs-full:ComponentsOfEquityAxis">ifrs-full:IssuedCapitalMember</xbrldi:explicitMember></xbrli:scenario></xbrli:context>
    <xbrli:context id="d-current"><xbrli:entity><xbrli:identifier scheme="x">E1</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate></xbrli:period></xbrli:context>
    <xbrli:unit id="u-gbp"><xbrli:measure>iso4217:GBP</xbrli:measure></xbrli:unit>
  </ix:resources>
</ix:header></head>
<body>
  <span><ix:nonFraction name="ifrs-full:Revenue" contextRef="d-current" unitRef="u-gbp" scale="3" decimals="-3" format="ixt4:num-dot-decimal">2 ,10 0,0 0 0</ix:nonFraction></span>
  <span><ix:nonFraction name="ifrs-full:Equity" contextRef="c-current-dim" unitRef="u-gbp" scale="3" decimals="-3" format="ixt4:num-dot-decimal">50</ix:nonFraction></span>
  <span><ix:nonFraction name="ifrs-full:Equity" contextRef="c-current" unitRef="u-gbp" scale="3" decimals="-3" format="ixt4:num-dot-decimal">410,500</ix:nonFraction></span>
  <span><ix:nonFraction name="ifrs-full:Equity" contextRef="c-prior" unitRef="u-gbp" scale="3" decimals="-3" format="ixt4:num-dot-decimal">380,200</ix:nonFraction></span>
  <span><ix:nonFraction name="ifrs-full:Liabilities" contextRef="c-current" unitRef="u-gbp" sign="-" scale="3" decimals="-3" format="ixt4:num-dot-decimal">920,300</ix:nonFraction></span>
</body>
</html>
"""


def module():
    spec = importlib.util.spec_from_file_location("normalize_europe_ixbrl_fundamentals_v2_38y", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_fixture(dir_path: Path) -> Path:
    path = dir_path / "fixture.xhtml"
    path.write_text(FIXTURE_XHTML, encoding="utf-8")
    return path


def test_number_cleaning_handles_interspersed_spaces_and_thousands_comma():
    mod = module()
    assert mod.clean_number_text("2 ,10 0,0 0 0") == 2100000.0
    assert mod.clean_number_text("410,500") == 410500.0
    assert mod.clean_number_text("-") is None
    assert mod.clean_number_text("") is None


def test_dimensional_context_never_wins_over_plain_context_for_same_date():
    """Regression test for the same real bug fixed in v2.38W: a single
    global 'latest context id' pick would let a dimensional equity
    breakdown context silently outrank the plain, undimensioned context
    for the SAME date, wrongly marking Assets/Liabilities as not-tagged."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        fixture = write_fixture(Path(tmp))
        contract = {
            "target_ifrs_concepts": ["ifrs-full:Revenue", "ifrs-full:Equity", "ifrs-full:Liabilities"],
            "flow_concepts": ["ifrs-full:Revenue"],
            "stock_concepts": ["ifrs-full:Equity", "ifrs-full:Liabilities"],
        }
        row = {"asset_id": "U1", "ticker": "TST", "company_number": "123", "resolved_company_name": "TEST CO PLC"}
        records = mod.extract_company(fixture, row, contract)

    by_concept = {r["concept"]: r for r in records}
    assert by_concept["ifrs-full:Equity"]["value"] == 410500.0 * 1000  # the plain c-current fact, NOT the dimensional c-current-dim fact (50 * 1000)
    assert by_concept["ifrs-full:Equity"]["period_end"] == "2025-12-31"
    assert by_concept["ifrs-full:Revenue"]["value"] == 2100000.0 * 1000
    assert by_concept["ifrs-full:Liabilities"]["value"] == -920300.0 * 1000  # sign="-" applied
    assert all(r["normalized_fundamentals_present"] for r in records)


def test_missing_concept_recorded_as_not_tagged_never_guessed():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        fixture = write_fixture(Path(tmp))
        contract = {
            "target_ifrs_concepts": ["ifrs-full:Revenue", "ifrs-full:Assets"],  # Assets is not in the fixture at all
            "flow_concepts": ["ifrs-full:Revenue"],
            "stock_concepts": ["ifrs-full:Assets"],
        }
        row = {"asset_id": "U1", "ticker": "TST", "company_number": "123", "resolved_company_name": "TEST CO PLC"}
        records = mod.extract_company(fixture, row, contract)

    by_concept = {r["concept"]: r for r in records}
    assert by_concept["ifrs-full:Assets"]["value"] is None
    assert by_concept["ifrs-full:Assets"]["normalized_fundamentals_present"] is False
    assert by_concept["ifrs-full:Assets"]["extraction_method"] == "not_tagged_in_document"


def test_only_latest_period_is_extracted_not_prior_year_comparative():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        fixture = write_fixture(Path(tmp))
        contract = {"target_ifrs_concepts": ["ifrs-full:Equity"], "flow_concepts": [], "stock_concepts": ["ifrs-full:Equity"]}
        row = {"asset_id": "U1", "ticker": "TST", "company_number": "123", "resolved_company_name": "TEST CO PLC"}
        records = mod.extract_company(fixture, row, contract)
    assert len(records) == 1
    assert records[0]["period_end"] == "2025-12-31"
    assert records[0]["value"] == 410500.0 * 1000  # not the prior-year 380,200 figure


CASES = [
    test_number_cleaning_handles_interspersed_spaces_and_thousands_comma,
    test_dimensional_context_never_wins_over_plain_context_for_same_date,
    test_missing_concept_recorded_as_not_tagged_never_guessed,
    test_only_latest_period_is_extracted_not_prior_year_comparative,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38Y-ixbrl-normalizer/dimensional-context-regression/number-cleaning/latest-period-only/no-guessing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
