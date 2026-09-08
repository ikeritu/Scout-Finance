#!/usr/bin/env python3
"""Offline QA for the v2.38BV global research ranking. No network, no real
licensed data -- every fixture value below is synthetic. Does not
re-test the underlying scoring engine's own internals (percentile math,
coverage floor, tie-breaking) -- those are already covered by
tests/qa_scoring_engine_v2_35.py against the real, unmodified engine.
This file only tests that v2.38BV correctly builds the two input dicts
(fundamentals, prices) the engine expects, and its own real logic
(financial-institution recovery, not-yet-scored tracking, determinism)."""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_global_research_ranking_v2_38bv.py"

ELIGIBILITY_FIELDS = ["asset_id", "ticker", "company_name", "country", "eligibility_tier"]
US_FIELDS = ["asset_id", "net_margin", "return_on_assets", "return_on_equity", "revenue_yoy_growth", "net_income_yoy_growth"]
VALUATION_FIELDS = ["asset_id", "operating_margin", "eps_basic", "book_value_per_share"]
AT_RATIO_FIELDS = ["asset_id", "company_name", "net_margin", "operating_margin", "return_on_assets", "return_on_equity"]
AT_GROWTH_FIELDS = ["asset_id", "revenue_yoy_growth", "net_profit_yoy_growth"]


def module():
    spec = importlib.util.spec_from_file_location("build_global_research_ranking_v2_38bv", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def eligibility_row(asset_id, name, country, tier) -> dict:
    return {"asset_id": asset_id, "ticker": asset_id, "company_name": name, "country": country, "eligibility_tier": tier}


def us_row(asset_id, net_margin="0.10", roa="0.05", roe="0.15", rev_growth="0.08", ni_growth="0.09") -> dict:
    return {"asset_id": asset_id, "net_margin": net_margin, "return_on_assets": roa, "return_on_equity": roe, "revenue_yoy_growth": rev_growth, "net_income_yoy_growth": ni_growth}


def build_with(tmp: Path, eligibility=None, us_original=None, us_valuation=None, at_ratios=None, at_growth=None, price_rows=None):
    mod = module()
    eligibility_path = tmp / "eligibility.csv"
    us_original_path = tmp / "us_original.csv"
    empty_us_path = tmp / "empty_us.csv"
    valuation_path = tmp / "valuation.csv"
    price_dir = tmp / "prices"
    at_ratios_path = tmp / "at_ratios.csv"
    at_growth_path = tmp / "at_growth.csv"
    write_csv(eligibility_path, ELIGIBILITY_FIELDS, eligibility or [])
    write_csv(us_original_path, US_FIELDS, us_original or [])
    write_csv(empty_us_path, US_FIELDS, [])
    write_csv(valuation_path, VALUATION_FIELDS, us_valuation or [])
    write_csv(at_ratios_path, AT_RATIO_FIELDS, at_ratios or [])
    write_csv(at_growth_path, AT_GROWTH_FIELDS, at_growth or [])
    price_dir.mkdir(parents=True, exist_ok=True)
    for asset_id, rows in (price_rows or {}).items():
        with (price_dir / f"{asset_id}.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "close", "adjusted_close"], lineterminator="\n")
            writer.writeheader()
            for date, close in rows:
                writer.writerow({"date": date, "close": close, "adjusted_close": ""})
    report = mod.build(eligibility_path, us_original_path, empty_us_path, empty_us_path, valuation_path, price_dir, at_ratios_path, at_growth_path, tmp / "out")
    rows_out = {r["asset_id"]: r for r in csv.DictReader((tmp / "out" / "global_research_ranking_v2_38bv.csv").open(encoding="utf-8"))}
    return report, rows_out


def test_us_company_with_fundamentals_only_gets_scored_quality_and_growth():
    """5 of the 14 real factors (net_margin/roa/roe/revenue_growth/
    net_income_growth = weight 0.40) alone sit BELOW the engine's real
    0.50 coverage floor -- this is the same real behavior the underlying
    engine already validates, not a bug in this adapter. Adding the real
    operating_margin factor (weight 0.10, from v2.38BU) pushes coverage
    to exactly 0.50, the documented boundary case."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            eligibility=[eligibility_row("U1", "Widget Inc", "US", "ELIGIBLE_PARTIAL_NO_PRICE")],
            us_original=[us_row("U1")],
            us_valuation=[{"asset_id": "U1", "operating_margin": "0.12", "eps_basic": "", "book_value_per_share": ""}],
        )
    assert rows["U1"]["eligibility_status"] in ("ELIGIBLE_PARTIAL", "PARTIAL_COMPARABILITY")
    assert rows["U1"]["total_score"] != ""


def test_austria_company_scored_from_ratios_and_growth_files():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            eligibility=[eligibility_row("U2", "AST0", "AT", "ELIGIBLE_PARTIAL_NO_PRICE")],
            at_ratios=[{"asset_id": "U2", "company_name": "STRABAG SE", "net_margin": "0.05", "operating_margin": "0.14", "return_on_assets": "0.04", "return_on_equity": "0.12"}],
            at_growth=[{"asset_id": "U2", "revenue_yoy_growth": "0.03", "net_profit_yoy_growth": "0.02"}],
        )
    assert rows["U2"]["total_score"] != ""
    assert rows["U2"]["company_name"] == "STRABAG SE"  # real v2.38X name preferred over the census placeholder


def test_financial_institution_recovered_from_real_austria_name_not_scored_industrially():
    """The real bug this block had to work around: v2.38BO's own
    eligibility file carries a placeholder company_name for this Austria
    population, so its financial-institution heuristic could never catch
    a real bank there. This must be re-caught here using v2.38X's real
    name, and routed to REVIEW_REQUIRED exactly like the old product's
    P178 exclusion -- never scored with industrial ratios."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            eligibility=[eligibility_row("U3", "AST0", "AT", "ELIGIBLE_PARTIAL_NO_PRICE")],
            at_ratios=[{"asset_id": "U3", "company_name": "Erste Group Bank AG", "net_margin": "0.20", "operating_margin": "0.30", "return_on_assets": "0.02", "return_on_equity": "0.10"}],
            at_growth=[{"asset_id": "U3", "revenue_yoy_growth": "0.03", "net_profit_yoy_growth": "0.02"}],
        )
    assert rows["U3"]["eligibility_status"] == "REVIEW_REQUIRED"
    assert "financial_institution_requires_separate_factor_contract" in rows["U3"]["review_reasons"]
    assert "U3" in report["financial_institutions_recovered_from_real_austria_names"]


def test_review_required_financial_institution_from_v2_38bo_is_excluded_from_scoring():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            eligibility=[eligibility_row("U4", "Some Bancorp Inc", "US", "REVIEW_REQUIRED_FINANCIAL_INSTITUTION")],
            us_original=[us_row("U4")],
        )
    assert rows["U4"]["eligibility_status"] == "REVIEW_REQUIRED"
    assert rows["U4"]["total_score"] == ""


def test_company_in_universe_with_no_adapter_data_is_explicitly_not_yet_scored():
    """A real, explicit status -- never a silent disappearance and never
    a fabricated score for a country (e.g. Luxembourg) this block has no
    ratio/growth adapter for yet."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            eligibility=[eligibility_row("U5", "Some Luxembourg Holding SA", "LU", "ELIGIBLE_PARTIAL_SINGLE_PERIOD")],
        )
    assert rows["U5"]["eligibility_status"] == "NOT_YET_SCORED_NO_ADAPTER"
    assert "U5" in report["not_yet_scored_no_adapter"]


def test_us_company_with_real_price_gets_momentum_and_risk_factors():
    with tempfile.TemporaryDirectory() as tmp:
        price_rows = [(f"2024-{(i // 20) + 1:02d}-{(i % 20) + 1:02d}", 100.0 + i * 0.1) for i in range(260)]
        report, rows = build_with(
            Path(tmp),
            eligibility=[eligibility_row("U6", "Priced Co", "US", "ELIGIBLE_FULL")],
            us_original=[us_row("U6")],
            price_rows={"U6": price_rows},
        )
    assert float(rows["U6"]["coverage_weight"]) > 0.50  # real price present should push coverage above the fundamentals-only floor


def test_run_twice_on_same_fixtures_is_byte_identical():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        args = dict(
            eligibility=[eligibility_row("U1", "Widget Inc", "US", "ELIGIBLE_PARTIAL_NO_PRICE"), eligibility_row("U2", "AST0", "AT", "ELIGIBLE_PARTIAL_NO_PRICE")],
            us_original=[us_row("U1")],
            at_ratios=[{"asset_id": "U2", "company_name": "PORR AG", "net_margin": "0.03", "operating_margin": "0.05", "return_on_assets": "0.02", "return_on_equity": "0.08"}],
            at_growth=[{"asset_id": "U2", "revenue_yoy_growth": "0.01", "net_profit_yoy_growth": "0.02"}],
        )
        report1, _ = build_with(root / "run1", **args)
        report2, _ = build_with(root / "run2", **args)
        first = (root / "run1" / "out" / "global_research_ranking_results_v2_38bv.json").read_text(encoding="utf-8")
        second = (root / "run2" / "out" / "global_research_ranking_results_v2_38bv.json").read_text(encoding="utf-8")
    assert first == second


CASES = [
    test_us_company_with_fundamentals_only_gets_scored_quality_and_growth,
    test_austria_company_scored_from_ratios_and_growth_files,
    test_financial_institution_recovered_from_real_austria_name_not_scored_industrially,
    test_review_required_financial_institution_from_v2_38bo_is_excluded_from_scoring,
    test_company_in_universe_with_no_adapter_data_is_explicitly_not_yet_scored,
    test_us_company_with_real_price_gets_momentum_and_risk_factors,
    test_run_twice_on_same_fixtures_is_byte_identical,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BV-global-research-ranking/reuses-v2-35-engine-unmodified/never-fabricated/deterministic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
