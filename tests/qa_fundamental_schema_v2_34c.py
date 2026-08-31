#!/usr/bin/env python3
"""QA for the canonical FundamentalRecord schema and its two config
catalogs (block C.6). No network calls.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fundamental_adapters import schema  # noqa: E402


def base_record(**overrides) -> dict:
    record = {
        "schema_version": "1.0.0",
        "record_id": "abc123",
        "asset_id": "P143",
        "company_id": None,
        "pilot_id": "P143",
        "ticker": "1301",
        "provider_symbol": "13010",
        "provider_record_id": None,
        "company_name": "KYOKUYO CO.,LTD.",
        "exchange": "JPX",
        "mic": None,
        "country": "JP",
        "isin": None,
        "provider": "jquants_fins_summary",
        "source_url_or_endpoint": "/v2/fins/summary",
        "retrieved_at": "2026-08-31T00:00:00+00:00",
        "normalizer_version": "1.0.0",
        "statement_type": "income_statement",
        "period_type": "quarterly",
        "fiscal_year": "2026",
        "fiscal_quarter": 1,
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
        "filing_date": None,
        "publication_date": None,
        "restatement_status": "original",
        "consolidation_scope": "consolidated",
        "accounting_standard": "JGAAP",
        "metric": "revenue",
        "raw_metric": "Sales",
        "value": 1000000.0,
        "raw_value": 1000000.0,
        "currency": "JPY",
        "raw_currency": "JPY",
        "unit": "currency",
        "scale": "units",
        "sign_convention": "natural",
        "value_status": "ok",
        "source_status": "received",
        "normalization_status": "normalized",
        "validation_status": "passed",
        "missing_reason": None,
        "quality_flags": [],
        "transformation_notes": None,
    }
    record.update(overrides)
    return record


def test_valid_record_passes():
    problems = schema.validate_record(base_record())
    assert problems == [], problems


def test_valid_missing_record_with_reason_passes():
    record = base_record(value=None, raw_value=None, missing_reason="not_reported_by_company", value_status="ok")
    assert schema.validate_record(record) == []


def test_rejected_null_value_without_reason():
    record = base_record(value=None)
    problems = schema.validate_record(record)
    assert any("missing_reason" in p for p in problems)


def test_rejected_unknown_missing_reason_code():
    record = base_record(value=None, missing_reason="made_up_reason")
    problems = schema.validate_record(record)
    assert any("closed catalog" in p for p in problems)


def test_rejected_value_and_missing_reason_both_set():
    record = base_record(missing_reason="not_reported_by_company")
    problems = schema.validate_record(record)
    assert any("also set" in p for p in problems)


def test_rejected_estimated_status_forbidden():
    record = base_record(value_status="estimated")
    problems = schema.validate_record(record)
    assert any("forbidden" in p for p in problems)


def test_rejected_unknown_canonical_metric():
    record = base_record(metric="totally_made_up_metric")
    problems = schema.validate_record(record)
    assert any("unknown canonical metric" in p for p in problems)


def test_rejected_bad_enum_value():
    record = base_record(exchange="NASDAQ")  # not JPX/TWSE
    problems = schema.validate_record(record)
    assert problems, "an out-of-catalog exchange must be rejected"


def test_metrics_catalog_and_missing_reasons_load():
    metrics = schema.load_metrics_catalog()
    assert "revenue" in metrics and "net_debt" in metrics
    assert metrics["net_debt"]["kind"] == "calculated"
    reasons = schema.load_missing_reasons()
    assert "not_available_from_provider" in reasons
    assert "calculation_impossible_missing_components" in reasons


CASES = [
    test_valid_record_passes,
    test_valid_missing_record_with_reason_passes,
    test_rejected_null_value_without_reason,
    test_rejected_unknown_missing_reason_code,
    test_rejected_value_and_missing_reason_both_set,
    test_rejected_estimated_status_forbidden,
    test_rejected_unknown_canonical_metric,
    test_rejected_bad_enum_value,
    test_metrics_catalog_and_missing_reasons_load,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.34C-fundamental-schema/valid-and-rejected-examples/closed-catalogs/no-estimated-values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
