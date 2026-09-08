#!/usr/bin/env python3
"""Offline QA for the v2.38BO global scoring eligibility definition. No
network, no real licensed data -- every fixture value below is
synthetic."""
from __future__ import annotations

import csv
import importlib.util
import lzma
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_global_scoring_eligibility_v2_38bo.py"

COVERAGE_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "country",
    "identity_status", "identity_source", "fundamentals_status", "fundamentals_source",
    "growth_status", "growth_source", "price_status", "price_source",
    "overall_coverage_status", "phase",
]


def module():
    spec = importlib.util.spec_from_file_location("build_global_scoring_eligibility_v2_38bo", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_coverage_xz(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COVERAGE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def coverage_row(asset_id: str, name: str, country: str, overall_status: str, price_status: str = "NOT_ATTEMPTED") -> dict:
    return {
        "asset_id": asset_id, "ticker": asset_id, "company_name": name, "exchange": "TEST", "country": country,
        "identity_status": "NOT_ATTEMPTED" if overall_status == "NO_DATA_YET" else "RESOLVED", "identity_source": "",
        "fundamentals_status": "", "fundamentals_source": "", "growth_status": "", "growth_source": "",
        "price_status": price_status, "price_source": "", "overall_coverage_status": overall_status, "phase": "",
    }


def build_with(tmp: Path, rows: list[dict]):
    mod = module()
    coverage_path = tmp / "coverage.csv.xz"
    write_coverage_xz(coverage_path, rows)
    report = mod.build(coverage_path, tmp / "out")
    out_rows = {r["asset_id"]: r for r in csv.DictReader((tmp / "out" / "global_scoring_eligibility_v2_38bo.csv").open(encoding="utf-8"))}
    return report, out_rows


def test_growth_ready_with_real_price_is_eligible_full():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "Widget Manufacturing Inc", "USA", "GROWTH_READY", "PRICE_FEATURES_READY")])
    assert rows["U1"]["eligibility_tier"] == "ELIGIBLE_FULL"
    assert rows["U1"]["is_financial_institution_heuristic"] == "False"


def test_growth_partial_with_partial_price_still_counts_as_real_price():
    """A partial price history is still a real signal, distinct from
    never having attempted price at all -- must reach ELIGIBLE_FULL, not
    the no-price tier."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "Widget Manufacturing Inc", "USA", "GROWTH_PARTIAL", "PRICE_FEATURES_PARTIAL")])
    assert rows["U1"]["eligibility_tier"] == "ELIGIBLE_FULL"


def test_growth_ready_without_real_price_is_eligible_partial_no_price():
    """Real case: the 538 new US Cboe-secondary companies and Austria's
    17 growth-ready companies have real growth data but no real price
    signal (never attempted, or a confirmed no-free-source finding) --
    must never be penalized to the point of exclusion, matching v2.38AL's
    own design principle of tracking price separately from the ladder."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [
            coverage_row("U1", "Moderna Inc", "US", "GROWTH_PARTIAL", "NOT_ATTEMPTED"),
            coverage_row("U2", "OMV AG", "AT", "GROWTH_READY", "NOT_COLLECTED_NO_FREE_SOURCE_FOUND"),
        ])
    assert rows["U1"]["eligibility_tier"] == "ELIGIBLE_PARTIAL_NO_PRICE"
    assert rows["U2"]["eligibility_tier"] == "ELIGIBLE_PARTIAL_NO_PRICE"


def test_fundamentals_only_no_growth_is_lowest_eligible_tier():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [coverage_row("U1", "Some Luxembourg Holding SA", "LU", "FUNDAMENTALS_PARTIAL_NO_GROWTH_YET")])
    assert rows["U1"]["eligibility_tier"] == "ELIGIBLE_PARTIAL_SINGLE_PERIOD"
    assert rows["U1"]["eligibility_reason"] == "real_fundamentals_present_but_no_year_over_year_growth_evidence_yet"


def test_financial_institution_name_routes_to_review_not_excluded_or_scored():
    """Same precedent as the old 50-asset product's P178 exception
    (a bank explicitly requiring a separate factor contract) -- real
    banks/insurers must never land in the same tier as an industrial
    company, in either direction (not excluded, not silently eligible)."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [
            coverage_row("U1", "Sierra Bancorp", "USA", "GROWTH_PARTIAL", "PRICE_FEATURES_READY"),
            coverage_row("U2", "American Coastal Insurance Corporation", "USA", "GROWTH_READY", "PRICE_FEATURES_READY"),
            coverage_row("U3", "Auburn National Bancorporation, Inc.", "USA", "FUNDAMENTALS_READY_NO_GROWTH_YET"),
        ])
    for asset_id in ("U1", "U2", "U3"):
        assert rows[asset_id]["eligibility_tier"] == "REVIEW_REQUIRED_FINANCIAL_INSTITUTION"
        assert rows[asset_id]["is_financial_institution_heuristic"] == "True"


def test_name_heuristic_does_not_false_positive_on_substrings():
    """Real regex risk this must guard against: a naive substring match
    would wrongly flag "Databank Inc" (contains "bank") or "Something
    Savingsware LLC" (contains "savings") as financial institutions.
    Whole-word matching must prevent both."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [
            coverage_row("U1", "Databank Inc", "USA", "GROWTH_READY", "PRICE_FEATURES_READY"),
            coverage_row("U2", "Something Savingsware LLC", "USA", "GROWTH_READY", "PRICE_FEATURES_READY"),
        ])
    assert rows["U1"]["eligibility_tier"] == "ELIGIBLE_FULL"
    assert rows["U2"]["eligibility_tier"] == "ELIGIBLE_FULL"


def test_not_eligible_preserves_the_real_underlying_reason():
    """Never a generic rejection -- the real v2.38AL status must survive
    into the reason field, lowercased, for every excluded row."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), [
            coverage_row("U1", "Untouched Co", "USA", "NO_DATA_YET"),
            coverage_row("U2", "Identity Only Co", "DE", "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"),
            coverage_row("U3", "Some Fund Compartment", "LU", "IDENTITY_ONLY_NOT_AN_OPERATING_COMPANY"),
            coverage_row("U4", "Cayman Co", "KY", "IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED"),
            coverage_row("U5", "Austrian Bank Delayed", "AT", "IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED"),
        ])
    for asset_id, expected_status in (
        ("U1", "NO_DATA_YET"), ("U2", "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"), ("U3", "IDENTITY_ONLY_NOT_AN_OPERATING_COMPANY"),
        ("U4", "IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED"), ("U5", "IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED"),
    ):
        assert rows[asset_id]["eligibility_tier"] == "NOT_ELIGIBLE"
        assert rows[asset_id]["eligibility_reason"] == expected_status.lower()


def test_every_census_row_gets_a_tier_none_dropped():
    with tempfile.TemporaryDirectory() as tmp:
        rows_in = [coverage_row(f"U{i}", f"Co {i}", "USA", "NO_DATA_YET") for i in range(5)]
        report, rows = build_with(Path(tmp), rows_in)
    assert report["companies_total"] == 5
    assert set(rows) == {f"U{i}" for i in range(5)}


def test_missing_coverage_input_raises_blocked_not_a_silent_empty_run():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        raised = False
        try:
            mod.build(root / "does_not_exist.csv.xz", root / "out")
        except SystemExit:
            raised = True
    assert raised


CASES = [
    test_growth_ready_with_real_price_is_eligible_full,
    test_growth_partial_with_partial_price_still_counts_as_real_price,
    test_growth_ready_without_real_price_is_eligible_partial_no_price,
    test_fundamentals_only_no_growth_is_lowest_eligible_tier,
    test_financial_institution_name_routes_to_review_not_excluded_or_scored,
    test_name_heuristic_does_not_false_positive_on_substrings,
    test_not_eligible_preserves_the_real_underlying_reason,
    test_every_census_row_gets_a_tier_none_dropped,
    test_missing_coverage_input_raises_blocked_not_a_silent_empty_run,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BO-global-scoring-eligibility/tiered-not-binary/financial-review-not-excluded/no-scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
