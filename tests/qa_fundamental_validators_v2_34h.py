#!/usr/bin/env python3
"""Offline QA for the block-H validators (accounting equations, temporal
consistency, economic sanity, quality score). No network, no real data --
every fixture value is synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fundamental_adapters import validators  # noqa: E402


def rec(metric: str, value: float | None, **overrides) -> dict:
    record = {
        "asset_id": "P001", "record_id": f"fixture-{metric}-{overrides.get('fiscal_year', '2025')}",
        "metric": metric, "value": value, "period_type": "annual", "fiscal_year": "2025",
        "fiscal_quarter": None, "consolidation_scope": "consolidated",
        "period_start": None, "period_end": "2025-03-31", "provider": "twse_mops_opendata",
        "normalization_status": "normalized", "quality_flags": [],
    }
    record.update(overrides)
    return record


# --- accounting equations ---

def test_balance_sheet_equation_passes_within_tolerance_not_exact():
    records = [rec("total_assets", 1000.0), rec("total_liabilities", 600.0), rec("total_equity", 401.0)]  # off by 1, within 2% tolerance
    results = validators.check_accounting_equations(records)
    eq = next(r for r in results if r["equation"] == "balance_sheet_equation")
    assert eq["status"] == "passed"


def test_balance_sheet_equation_fails_outside_tolerance():
    records = [rec("total_assets", 1000.0), rec("total_liabilities", 600.0), rec("total_equity", 300.0)]  # off by 100, way outside 2%
    results = validators.check_accounting_equations(records)
    eq = next(r for r in results if r["equation"] == "balance_sheet_equation")
    assert eq["status"] == "failed"


def test_balance_sheet_equation_not_applicable_without_independent_liabilities():
    # JPX-like case: only total_assets and total_equity reported, no total_liabilities
    records = [rec("total_assets", 1000.0), rec("total_equity", 400.0)]
    results = validators.check_accounting_equations(records)
    eq = next(r for r in results if r["equation"] == "balance_sheet_equation")
    assert eq["status"] == "not_applicable"


def test_gross_profit_equation_checked_only_when_all_three_present():
    records = [rec("revenue", 1000.0), rec("cost_of_sales", 600.0), rec("gross_profit", 400.0)]
    results = validators.check_accounting_equations(records)
    eq = next(r for r in results if r["equation"] == "gross_profit_equation")
    assert eq["status"] == "passed"

    records2 = [rec("revenue", 1000.0), rec("gross_profit", 400.0)]  # cost_of_sales missing
    results2 = validators.check_accounting_equations(records2)
    eq2 = next(r for r in results2 if r["equation"] == "gross_profit_equation")
    assert eq2["status"] == "not_applicable"


# --- temporal ---

def test_temporal_flags_period_start_after_period_end():
    records = [rec("revenue", 100.0, period_start="2025-06-01", period_end="2025-01-01")]
    problems = validators.check_temporal_consistency(records)
    assert any(p["issue"] == "period_start_after_period_end" for p in problems)


def test_temporal_flags_out_of_range_quarter():
    records = [rec("revenue", 100.0, fiscal_quarter=5)]
    problems = validators.check_temporal_consistency(records)
    assert any(p["issue"] == "fiscal_quarter_out_of_range" for p in problems)


def test_temporal_clean_data_produces_no_flags():
    records = [rec("revenue", 100.0, period_start="2025-01-01", period_end="2025-03-31", fiscal_quarter=1)]
    assert validators.check_temporal_consistency(records) == []


# --- economic sanity ---

def test_negative_total_assets_flagged():
    records = [rec("total_assets", -100.0)]
    flags = validators.check_economic_sanity(records)
    assert any(f["issue"] == "negative_total_assets_implausible" for f in flags)


def test_implausible_margin_flagged_plausible_margin_not_flagged():
    implausible = rec("net_margin", 5.0)  # 500% margin
    plausible = rec("net_margin", 0.15, record_id="fixture-plausible")
    flags = validators.check_economic_sanity([implausible, plausible])
    flagged_ids = {f["record_id"] for f in flags}
    assert implausible["record_id"] in flagged_ids
    assert plausible["record_id"] not in flagged_ids


# --- quality score ---

def test_quality_score_dimensions_and_promotion_tiers():
    normalized = [
        rec("revenue", 1000.0, provider="twse_mops_opendata"),
        rec("operating_income", 200.0, provider="twse_mops_opendata"),
        rec("net_income", 100.0, provider="twse_mops_opendata"),
        rec("total_assets", 5000.0, provider="twse_mops_opendata"),
        rec("total_equity", 2000.0, provider="twse_mops_opendata"),
        rec("total_liabilities", 3000.0, provider="twse_mops_opendata"),
    ]
    equations = validators.check_accounting_equations(normalized)
    sanity = validators.check_economic_sanity(normalized)
    q = validators.compute_quality_scores("P001", "twse_mops_opendata", normalized, equations, sanity)
    assert q["dimensions"]["identity"] == 1.0
    assert q["dimensions"]["completeness"] == 1.0  # all 5 core metrics present
    assert q["dimensions"]["coherence"] == 1.0  # balance sheet equation passed
    assert 0.0 < q["composite_quality_score"] <= 1.0
    assert q["accounting_equations_attempted"] >= 1


def test_coherence_is_null_not_zero_when_no_equations_attempted():
    # JPX-like: no independent total_liabilities, no cost_of_sales -- nothing to check
    normalized = [rec("revenue", 1000.0, provider="jquants_fins_summary"), rec("total_assets", 5000.0, provider="jquants_fins_summary")]
    equations = validators.check_accounting_equations(normalized)
    sanity = validators.check_economic_sanity(normalized)
    q = validators.compute_quality_scores("P001", "jquants_fins_summary", normalized, equations, sanity)
    assert q["dimensions"]["coherence"] is None  # never silently scored as 0 or 1 when untestable
    # composite must exclude the null dimension from the average, not treat it as 0
    scored = [v for v in q["dimensions"].values() if v is not None]
    assert abs(q["composite_quality_score"] - sum(scored) / len(scored)) < 1e-9


CASES = [
    test_balance_sheet_equation_passes_within_tolerance_not_exact,
    test_balance_sheet_equation_fails_outside_tolerance,
    test_balance_sheet_equation_not_applicable_without_independent_liabilities,
    test_gross_profit_equation_checked_only_when_all_three_present,
    test_temporal_flags_period_start_after_period_end,
    test_temporal_flags_out_of_range_quarter,
    test_temporal_clean_data_produces_no_flags,
    test_negative_total_assets_flagged,
    test_implausible_margin_flagged_plausible_margin_not_flagged,
    test_quality_score_dimensions_and_promotion_tiers,
    test_coherence_is_null_not_zero_when_no_equations_attempted,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.34H-fundamental-validators/tolerance-not-exact-equality/not-applicable-vs-failed/sanity-flags/quality-score/null-dimension-handling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
