#!/usr/bin/env python3
"""Offline QA for the block-G derived-metrics calculator. No network, no
real data -- every input record is a synthetic fixture. Every derived
record produced is checked against the real schema.validate_record().
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fundamental_adapters import derived_metrics, schema  # noqa: E402


def base(metric: str, value: float | None, **overrides) -> dict:
    record = {
        "schema_version": "1.0.0", "record_id": f"fixture-{metric}", "asset_id": "P001",
        "company_id": None, "pilot_id": "P001", "ticker": "1301", "provider_symbol": "13010",
        "provider_record_id": None, "company_name": "FIXTURE CO", "exchange": "JPX", "mic": None,
        "country": "JP", "isin": None, "provider": "jquants_fins_summary",
        "source_url_or_endpoint": "/v2/fins/summary", "retrieved_at": "2026-01-01T00:00:00+00:00",
        "normalizer_version": "1.0.0", "statement_type": "income_statement", "period_type": "annual",
        "fiscal_year": "2025", "fiscal_quarter": None, "period_start": "2024-04-01", "period_end": "2025-03-31",
        "filing_date": "2025-05-01", "publication_date": "2025-05-01", "restatement_status": "original",
        "consolidation_scope": "consolidated", "accounting_standard": "JGAAP",
        "metric": metric, "raw_metric": metric, "value": value, "raw_value": value,
        "currency": "JPY" if value is not None else None, "raw_currency": "JPY" if value is not None else None,
        "unit": "currency", "scale": "units", "sign_convention": "natural", "value_status": "ok",
        "source_status": "received", "normalization_status": "normalized", "validation_status": "pending",
        "missing_reason": None if value is not None else "not_reported_by_company", "quality_flags": [],
        "transformation_notes": None,
    }
    record.update(overrides)
    return record


def all_valid(records: list[dict]) -> list[str]:
    problems = []
    for r in records:
        problems.extend(schema.validate_record(r))
    return problems


def test_margin_computed_only_when_both_components_present():
    records = [base("revenue", 1000.0), base("operating_income", 200.0), base("net_income", 100.0), base("total_assets", 5000.0)]
    derived = derived_metrics.compute_derived_records(records)
    assert not all_valid(derived)
    by_metric = {r["metric"]: r for r in derived}
    assert by_metric["operating_margin"]["value"] == 0.2
    assert by_metric["net_margin"]["value"] == 0.1
    assert by_metric["roa"]["value"] == 0.02
    assert "gross_margin" not in by_metric  # gross_profit was never reported -- must not be guessed


def test_division_by_zero_never_raises_and_is_flagged_blocked():
    records = [base("revenue", 0.0), base("net_income", 100.0)]
    derived = derived_metrics.compute_derived_records(records)
    net_margin = next(r for r in derived if r["metric"] == "net_margin")
    assert net_margin["value"] is None and net_margin["missing_reason"] == "calculation_impossible_missing_components"


def test_negative_denominator_is_flagged_not_hidden():
    records = [base("net_income", 100.0), base("total_assets", -500.0)]
    derived = derived_metrics.compute_derived_records(records)
    roa = next(r for r in derived if r["metric"] == "roa")
    assert roa["value"] == 100.0 / -500.0
    assert "negative_denominator_ratio_not_directly_comparable" in roa["quality_flags"]


def test_always_blocked_debt_and_fcf_metrics_are_explicit_not_silent():
    records = [base("revenue", 1000.0)]
    derived = derived_metrics.compute_derived_records(records)
    by_metric = {r["metric"]: r for r in derived}
    for metric in ("gross_debt", "net_debt", "free_cash_flow"):
        assert by_metric[metric]["value"] is None
        assert by_metric[metric]["missing_reason"] == "calculation_impossible_missing_components"


def test_restated_disclosure_takes_priority_over_original_for_same_period():
    # restated record listed FIRST on purpose: a naive "last one wins" from
    # input order would pick "original" here, which is exactly the bug this
    # test guards against.
    restated = base("revenue", 1200.0, restatement_status="restated", filing_date="2025-08-01")
    original = base("revenue", 1000.0, restatement_status="original", filing_date="2025-05-01")
    net_income = base("net_income", 120.0)
    derived = derived_metrics.compute_derived_records([restated, original, net_income])
    net_margin = next(r for r in derived if r["metric"] == "net_margin")
    assert net_margin["value"] == 120.0 / 1200.0  # must use the restated 1200, never the original 1000


def test_growth_yoy_computed_across_matching_periods_and_flags_negative_base():
    year1 = base("revenue", 100.0, fiscal_year="2024", fiscal_quarter=None)
    year2 = base("revenue", 150.0, fiscal_year="2025", fiscal_quarter=None)
    ni_loss_year = base("net_income", -50.0, fiscal_year="2024", fiscal_quarter=None)
    ni_recovery_year = base("net_income", 30.0, fiscal_year="2025", fiscal_quarter=None)
    derived = derived_metrics.compute_derived_records([year1, year2, ni_loss_year, ni_recovery_year])
    by_metric = {r["metric"]: r for r in derived if r["fiscal_year"] == "2025"}
    assert by_metric["revenue_growth_yoy"]["value"] == 0.5
    ni_growth = by_metric["net_income_growth_yoy"]
    assert ni_growth["value"] == (30.0 - (-50.0)) / abs(-50.0)
    assert "negative_base_period_growth_not_directly_comparable" in ni_growth["quality_flags"]


def test_no_growth_record_without_a_prior_year_match():
    records = [base("revenue", 100.0, fiscal_year="2025", fiscal_quarter=None)]
    derived = derived_metrics.compute_derived_records(records)
    assert not any(r["metric"] == "revenue_growth_yoy" for r in derived)


CASES = [
    test_margin_computed_only_when_both_components_present,
    test_division_by_zero_never_raises_and_is_flagged_blocked,
    test_negative_denominator_is_flagged_not_hidden,
    test_always_blocked_debt_and_fcf_metrics_are_explicit_not_silent,
    test_restated_disclosure_takes_priority_over_original_for_same_period,
    test_growth_yoy_computed_across_matching_periods_and_flags_negative_base,
    test_no_growth_record_without_a_prior_year_match,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.34G-fundamental-derived-metrics/no-division-by-zero/negative-flags/restated-priority/growth-yoy/no-silent-blocked-metrics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
