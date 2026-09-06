#!/usr/bin/env python3
"""Offline QA for the v2.38AK Europe growth features builder. No network,
no real licensed data -- every fixture value below is synthetic."""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_growth_features_v2_38ak.py"


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def fixture_record(asset_id: str, ticker: str, company_name: str, company_number: str, concept: str, value: float | None, period_end: str) -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": company_name, "company_number": company_number, "concept": concept, "value": value, "period_end": period_end}


def test_single_period_company_is_insufficient_not_guessed():
    """GB/Ireland's iXBRL extraction only ever captures one period per
    company -- there is no prior year to compare against, so this must
    report INSUFFICIENT_FEATURE_EVIDENCE, never a fabricated growth rate."""
    mod = module(SCRIPT, "growth_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [
            fixture_record("U1", "SCT", "SOFTCAT PLC", "111", "ifrs-full:Revenue", 1000.0, "2025-07-31"),
            fixture_record("U1", "SCT", "SOFTCAT PLC", "111", "ifrs-full:ProfitLoss", 100.0, "2025-07-31"),
        ])
        report, rows = mod.build(records_path, root / "out")
        rejections = list(csv.DictReader((root / "out" / "europe_growth_feature_rejections_v2_38ak.csv").open(encoding="utf-8")))
    assert report["companies_insufficient"] == 1
    row = rows[0]
    assert row["feature_quality_status"] == "INSUFFICIENT_FEATURE_EVIDENCE"
    assert row["revenue_yoy_growth"] is None
    assert row["quality_flags"] == "fewer_than_two_periods_on_file"
    assert len(rejections) == len(mod.FEATURES)


def test_two_periods_computes_yoy_growth_and_margin_expansion():
    """Real Austrian pattern: two consecutive fiscal years, German Bilanz/
    GuV vocabulary. Revenue and net profit both grew, and the margin
    improved -- margin_expansion_flag must be True. growth_acceleration_flag
    needs a third year and must stay False here, not guessed."""
    mod = module(SCRIPT, "growth_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "umsatzerloese", 1000.0, "2023-12-31"),
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "jahresueberschuss", 50.0, "2023-12-31"),
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "bilanzSumme", 5000.0, "2023-12-31"),
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "eigenkapital", 2000.0, "2023-12-31"),
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "umsatzerloese", 1200.0, "2024-12-31"),
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "jahresueberschuss", 84.0, "2024-12-31"),
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "bilanzSumme", 5500.0, "2024-12-31"),
            fixture_record("U1", "GEPH", "GEPH AG", "555f", "eigenkapital", 2300.0, "2024-12-31"),
        ])
        report, rows = mod.build(records_path, root / "out")
    row = rows[0]
    assert report["companies_features_ready"] == 1
    assert row["current_period_end"] == "2024-12-31" and row["previous_period_end"] == "2023-12-31"
    assert row["revenue_yoy_growth"] == 0.2
    assert row["net_profit_yoy_growth"] == 0.68
    assert row["assets_yoy_growth"] == 0.1
    assert row["equity_yoy_growth"] == 0.15
    assert row["margin_expansion_flag"] is True  # 84/1200=0.07 > 50/1000=0.05
    assert row["growth_acceleration_flag"] is False  # only 2 periods on file


def test_growth_acceleration_flag_needs_three_periods_and_compares_correctly():
    """Real Austrian pattern (e.g. OMV/PORR): 3+ fiscal years on file.
    Revenue growth accelerated from FY22->FY23 (5%) to FY23->FY24 (20%),
    so growth_acceleration_flag must be True."""
    mod = module(SCRIPT, "growth_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [
            fixture_record("U1", "OMV", "OMV AG", "93363z", "umsatzerloese", 1000.0, "2022-12-31"),
            fixture_record("U1", "OMV", "OMV AG", "93363z", "umsatzerloese", 1050.0, "2023-12-31"),
            fixture_record("U1", "OMV", "OMV AG", "93363z", "umsatzerloese", 1260.0, "2024-12-31"),
        ])
        report, rows = mod.build(records_path, root / "out")
    row = rows[0]
    assert row["periods_available"] == 3
    assert row["revenue_yoy_growth"] == 0.2  # (1260-1050)/1050
    assert row["growth_acceleration_flag"] is True  # 0.2 > (1050-1000)/1000=0.05


def test_nonconsecutive_gap_uses_the_two_most_recent_periods_chronologically():
    """Real case confirmed in v2.38AI: at least one company (0B2) has a
    filing gap (e.g. 2015, then 2021-2024 with no gap). The two most
    recent periods on file are still exactly what should be compared,
    regardless of any earlier gap in the history."""
    mod = module(SCRIPT, "growth_4")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [
            fixture_record("U1", "0B2", "GAP AG", "999f", "umsatzerloese", 1.0, "2015-12-31"),
            fixture_record("U1", "0B2", "GAP AG", "999f", "umsatzerloese", 800.0, "2023-12-31"),
            fixture_record("U1", "0B2", "GAP AG", "999f", "umsatzerloese", 1000.0, "2024-12-31"),
        ])
        report, rows = mod.build(records_path, root / "out")
    row = rows[0]
    assert row["current_period_end"] == "2024-12-31" and row["previous_period_end"] == "2023-12-31"
    assert row["revenue_yoy_growth"] == 0.25  # (1000-800)/800, the 2015 figure never enters this ratio


def test_nonpositive_previous_value_produces_missing_growth_not_a_fabricated_ratio():
    mod = module(SCRIPT, "growth_5")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [
            fixture_record("U1", "TST", "TEST AG", "1f", "jahresueberschuss", -50.0, "2023-12-31"),
            fixture_record("U1", "TST", "TEST AG", "1f", "jahresueberschuss", 30.0, "2024-12-31"),
        ])
        report, rows = mod.build(records_path, root / "out")
        rejections = list(csv.DictReader((root / "out" / "europe_growth_feature_rejections_v2_38ak.csv").open(encoding="utf-8")))
    row = rows[0]
    assert row["net_profit_yoy_growth"] is None
    by_feature = {r["feature"]: r for r in rejections}
    assert by_feature["net_profit_yoy_growth"]["reason"] == "nonpositive_previous_period_value"


def test_multiple_companies_and_missing_input_file_handled_correctly():
    mod = module(SCRIPT, "growth_6")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path_a = root / "records_a.jsonl"
        path_missing = root / "records_does_not_exist.jsonl"
        write_jsonl(path_a, [
            fixture_record("U1", "AAA", "AAA AG", "1f", "umsatzerloese", 100.0, "2023-12-31"),
            fixture_record("U1", "AAA", "AAA AG", "1f", "umsatzerloese", 110.0, "2024-12-31"),
            fixture_record("U2", "BBB", "BBB AG", "2f", "umsatzerloese", 100.0, "2024-12-31"),  # only 1 period
        ])
        report, rows = mod.build([path_a, path_missing], root / "out")
    assert report["companies_input"] == 2
    assert len(report["records_sources_used"]) == 1  # the missing path is skipped, never an error
    by_asset = {r["asset_id"]: r for r in rows}
    assert by_asset["U1"]["feature_quality_status"] == "FEATURES_PARTIAL"  # only revenue growth available
    assert by_asset["U2"]["feature_quality_status"] == "INSUFFICIENT_FEATURE_EVIDENCE"


CASES = [
    test_single_period_company_is_insufficient_not_guessed,
    test_two_periods_computes_yoy_growth_and_margin_expansion,
    test_growth_acceleration_flag_needs_three_periods_and_compares_correctly,
    test_nonconsecutive_gap_uses_the_two_most_recent_periods_chronologically,
    test_nonpositive_previous_value_produces_missing_growth_not_a_fabricated_ratio,
    test_multiple_companies_and_missing_input_file_handled_correctly,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AK-europe-growth-features/yoy-computation/flags/gap-handling/no-fabricated-ratios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
