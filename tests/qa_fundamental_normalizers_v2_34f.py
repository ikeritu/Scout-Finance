#!/usr/bin/env python3
"""Offline QA for the block-F normalizers (J-Quants, TWSE MOPS). No network,
no real licensed data -- every fixture value below is synthetic. Every
record produced is checked against the real schema.validate_record() (the
same function block D/E/H will all use), not a hand-rolled shape check.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fundamental_adapters import jquants_normalizer, schema, twse_normalizer  # noqa: E402

JQUANTS_ASSET = {"pilot_id": "P001", "ticker": "1301", "provider_symbol_jquants": "13010", "company_name": "FIXTURE CO", "isin": ""}
TWSE_ASSET = {"pilot_id": "P016", "ticker": "1101.TW", "provider_symbol_twse": "1101.TW", "company_name": "夾具公司", "isin": ""}


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def all_valid(records: list[dict]) -> list[str]:
    problems = []
    for r in records:
        problems.extend(schema.validate_record(r))
    return problems


# --- J-Quants normalizer ---

def test_jquants_reported_value_and_blank_field_are_distinguished():
    disclosure = {
        "DocType": "1QFinancialStatements_Consolidated_JP", "CurPerType": "1Q",
        "CurFYSt": "2024-04-01", "CurPerSt": "2024-04-01", "CurPerEn": "2024-06-30",
        "DiscDate": "2024-08-05", "DiscNo": "X1",
        "Sales": "1000", "OP": "100", "NP": "50", "TA": "5000", "Eq": "2000",
        "CFO": "", "BPS": "",  # legitimately blank on a 1Q disclosure
        "ChgByASRev": "false", "ChgNoASRev": "false", "ChgAcEst": "false", "RetroRst": "false",
    }
    records = jquants_normalizer.normalize_disclosure(JQUANTS_ASSET, disclosure, "2026-01-01T00:00:00+00:00")
    assert not all_valid(records)

    by_metric = {(r["metric"], r["consolidation_scope"]): r for r in records}
    revenue = by_metric[("revenue", "consolidated")]
    assert revenue["value"] == 1000.0 and revenue["missing_reason"] is None and revenue["restatement_status"] == "original"

    cfo = by_metric[("operating_cash_flow", "consolidated")]
    assert cfo["value"] is None and cfo["missing_reason"] == "not_reported_by_company"
    assert cfo["currency"] is None  # a null value must not keep a currency label


def test_jquants_forecast_revision_disclosures_are_skipped_entirely():
    disclosure = {"DocType": "EarnForecastRevision", "CurPerType": "FY", "CurFYSt": "2024-04-01",
                  "Sales": "", "OP": "", "NP": ""}
    records = jquants_normalizer.normalize_disclosure(JQUANTS_ASSET, disclosure, "2026-01-01T00:00:00+00:00")
    assert records == []


def test_jquants_restated_flag_detection_and_non_consolidated_split():
    disclosure = {
        "DocType": "FYFinancialStatements_Consolidated_JP", "CurPerType": "FY",
        "CurFYSt": "2024-04-01", "CurPerSt": "2024-04-01", "CurPerEn": "2025-03-31",
        "DiscDate": "2025-05-01", "DiscNo": "X2",
        "Sales": "9000", "NCSales": "8000",
        "ChgByASRev": "true", "ChgNoASRev": "false", "ChgAcEst": "false", "RetroRst": "false",
    }
    records = jquants_normalizer.normalize_disclosure(JQUANTS_ASSET, disclosure, "2026-01-01T00:00:00+00:00")
    by_metric = {(r["metric"], r["consolidation_scope"]): r for r in records}
    assert by_metric[("revenue", "consolidated")]["value"] == 9000.0
    assert by_metric[("revenue", "consolidated")]["restatement_status"] == "restated"
    assert by_metric[("revenue", "non_consolidated")]["value"] == 8000.0


def test_jquants_unparseable_value_is_flagged_not_dropped():
    disclosure = {"DocType": "1QFinancialStatements_Consolidated_JP", "CurPerType": "1Q", "CurFYSt": "2024-04-01",
                  "Sales": "not_a_number"}
    records = jquants_normalizer.normalize_disclosure(JQUANTS_ASSET, disclosure, "2026-01-01T00:00:00+00:00")
    revenue = next(r for r in records if r["metric"] == "revenue" and r["consolidation_scope"] == "consolidated")
    assert revenue["value"] is None and revenue["missing_reason"] == "incomplete_response"
    assert revenue["normalization_status"] == "normalization_error"


def test_jquants_file_roundtrip_atomic_and_deterministic():
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir = Path(tmp)
        write_json(raw_dir / "P001.json", {
            "asset": JQUANTS_ASSET,
            "disclosures": [{
                "DocType": "1QFinancialStatements_Consolidated_JP", "CurPerType": "1Q", "CurFYSt": "2024-04-01",
                "CurPerSt": "2024-04-01", "CurPerEn": "2024-06-30", "DiscDate": "2024-08-05", "DiscNo": "X1",
                "Sales": "1000",
            }],
        })
        records_a = jquants_normalizer.normalize_collection(raw_dir)
        records_b = jquants_normalizer.normalize_collection(raw_dir)
        assert json.dumps(records_a, sort_keys=True) == json.dumps(records_b, sort_keys=True)
        assert not all_valid(records_a)


# --- TWSE normalizer ---

def test_twse_scale_conversion_and_period_end_derivation():
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir = Path(tmp)
        write_json(raw_dir / "P016.json", {
            "asset": TWSE_ASSET,
            "snapshot_files": {
                "income_statement": [{"年度": "115", "季別": "2", "公司代號": "1101", "營業收入": "71289957.00", "營業成本": "58298233.00"}],
                "balance_sheet": [{"年度": "115", "季別": "2", "公司代號": "1101", "資產總計": "596016531.00"}],
            },
        })
        records = twse_normalizer.normalize_collection(raw_dir)
        assert not all_valid(records)

        revenue = next(r for r in records if r["metric"] == "revenue")
        assert revenue["raw_value"] == 71289957.0
        assert revenue["value"] == 71289957000.0  # thousands -> whole TWD
        assert revenue["fiscal_year"] == "2026"  # ROC 115 -> western 2026
        assert revenue["period_end"] == "2026-06-30"  # Q2 -> calendar June 30
        assert "period_cumulative_vs_discrete_unconfirmed" in revenue["quality_flags"]


def test_twse_blank_field_gets_missing_reason_not_zero():
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir = Path(tmp)
        write_json(raw_dir / "P016.json", {
            "asset": TWSE_ASSET,
            "snapshot_files": {
                "income_statement": [{"年度": "115", "季別": "2", "公司代號": "1101", "營業收入": "", "營業成本": "100.00"}],
                "balance_sheet": [],
            },
        })
        records = twse_normalizer.normalize_collection(raw_dir)
        revenue = next(r for r in records if r["metric"] == "revenue")
        assert revenue["value"] is None and revenue["missing_reason"] == "not_reported_by_company"
        assert revenue["value"] != 0  # never silently zero-filled


CASES = [
    test_jquants_reported_value_and_blank_field_are_distinguished,
    test_jquants_forecast_revision_disclosures_are_skipped_entirely,
    test_jquants_restated_flag_detection_and_non_consolidated_split,
    test_jquants_unparseable_value_is_flagged_not_dropped,
    test_jquants_file_roundtrip_atomic_and_deterministic,
    test_twse_scale_conversion_and_period_end_derivation,
    test_twse_blank_field_gets_missing_reason_not_zero,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.34F-fundamental-normalizers/schema-valid/no-synthetic-values/forecast-revision-exclusion/scale-conversion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
