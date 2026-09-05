#!/usr/bin/env python3
"""Offline QA for the v2.38X Europe fundamental features and candidate
feature matrix builders. No network, no real licensed data -- every
fixture value below is synthetic."""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES_SCRIPT = ROOT / "scripts/build_europe_fundamental_features_v2_38x.py"
MATRIX_SCRIPT = ROOT / "scripts/build_europe_candidate_feature_matrix_v2_38x.py"


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def fixture_record(asset_id: str, ticker: str, company_name: str, company_number: str, concept: str, value: float | None, period_end: str = "2025-07-31") -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": company_name, "company_number": company_number, "concept": concept, "value": value, "period_end": period_end}


# --- features builder ---

def test_all_ratios_computed_when_all_concepts_present():
    mod = module(FEATURES_SCRIPT, "features_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:Revenue", 1000.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:ProfitLoss", 100.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:ProfitLossFromOperatingActivities", 150.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:ProfitLossBeforeTax", 120.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:Assets", 5000.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:Equity", 2000.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:Liabilities", 3000.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:CashAndCashEquivalents", 500.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:CurrentAssets", 800.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:CurrentLiabilities", 400.0),
        ])
        report, rows = mod.build(records_path, root / "out")
    assert report["companies_features_ready"] == 1
    row = rows[0]
    assert row["net_margin"] == 0.1
    assert row["operating_margin"] == 0.15
    assert row["return_on_equity"] == 0.05
    assert row["current_ratio"] == 2.0
    assert row["features_calculated"] == 9


def test_missing_concept_produces_partial_status_and_rejection_reason():
    mod = module(FEATURES_SCRIPT, "features_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:Revenue", 1000.0),
            fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:ProfitLoss", 100.0),
            # Assets missing entirely -- return_on_assets, liabilities_to_assets, equity_to_assets, cash_to_assets all become unavailable
        ])
        report, rows = mod.build(records_path, root / "out")
        rejections = list(csv.DictReader((root / "out" / "europe_fundamental_feature_rejections_v2_38x.csv").open(encoding="utf-8")))
    assert report["companies_features_partial"] == 1
    row = rows[0]
    assert row["net_margin"] == 0.1
    assert row["return_on_assets"] is None
    assert "return_on_assets" in row["features_missing"]
    by_feature = {r["feature"]: r for r in rejections}
    assert by_feature["return_on_assets"]["reason"] == "missing_or_zero_denominator"


def test_no_data_produces_insufficient_status():
    mod = module(FEATURES_SCRIPT, "features_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        records_path = root / "records.jsonl"
        write_jsonl(records_path, [fixture_record("U1", "TST", "TEST PLC", "123", "ifrs-full:Revenue", None)])
        report, rows = mod.build(records_path, root / "out")
    assert report["companies_insufficient"] == 1
    assert rows[0]["feature_quality_status"] == "INSUFFICIENT_FEATURE_EVIDENCE"


# --- candidate matrix builder ---

def write_features_csv(path: Path, rows: list[dict]) -> None:
    fields = ["asset_id", "ticker", "company_name", "company_number", "feature_quality_status", "net_margin", "operating_margin", "return_on_assets", "return_on_equity", "liabilities_to_assets", "cash_to_assets", "current_ratio", "profitability_positive_flag", "balance_strength_flag"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_prices_csv(path: Path, rows: list[dict]) -> None:
    fields = ["asset_id", "ticker", "company_name", "price_quality_status", "return_3m", "return_12m"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_matrix_classifies_ready_partial_and_missing_correctly():
    mod = module(MATRIX_SCRIPT, "matrix_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fund_path, price_path = root / "fund.csv", root / "price.csv"
        write_features_csv(fund_path, [
            {"asset_id": "U1", "ticker": "AAA", "company_name": "AAA PLC", "feature_quality_status": "FEATURES_READY", "net_margin": "0.1"},
            {"asset_id": "U2", "ticker": "BBB", "company_name": "BBB PLC", "feature_quality_status": "FEATURES_PARTIAL", "net_margin": "0.05"},
        ])
        write_prices_csv(price_path, [
            {"asset_id": "U1", "ticker": "AAA", "company_name": "AAA PLC", "price_quality_status": "PRICE_FEATURES_READY"},
            {"asset_id": "U3", "ticker": "CCC", "company_name": "CCC PLC", "price_quality_status": "PRICE_FEATURES_READY"},
        ])
        report = mod.build(fund_path, price_path, root / "out")
        rows = {r["asset_id"]: r for r in csv.DictReader((root / "out" / "europe_candidate_feature_matrix_v2_38x.csv").open(encoding="utf-8"))}
    assert rows["U1"]["candidate_matrix_status"] == "CANDIDATE_MATRIX_READY"
    assert rows["U2"]["candidate_matrix_status"] == "CANDIDATE_MATRIX_PARTIAL_PRICE"
    assert rows["U3"]["candidate_matrix_status"] == "CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS"
    assert report["matrix_ready"] == 1 and report["partial_price"] == 1 and report["partial_fundamentals"] == 1


def test_empty_price_input_never_invents_price_signal():
    mod = module(MATRIX_SCRIPT, "matrix_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fund_path, price_path = root / "fund.csv", root / "price.csv"
        write_features_csv(fund_path, [{"asset_id": "U1", "ticker": "AAA", "company_name": "AAA PLC", "feature_quality_status": "FEATURES_READY", "net_margin": "0.1"}])
        write_prices_csv(price_path, [])  # exactly today's real state: 0 price rows
        report = mod.build(fund_path, price_path, root / "out")
        row = next(iter(csv.DictReader((root / "out" / "europe_candidate_feature_matrix_v2_38x.csv").open(encoding="utf-8"))))
    assert report["price_input_companies"] == 0
    assert row["candidate_matrix_status"] == "CANDIDATE_MATRIX_PARTIAL_PRICE"
    assert row["return_3m"] == ""  # never a fabricated number
    assert "have not collected" in row["price_signal_summary"]


def test_invalid_identity_rows_are_rejected_not_silently_dropped():
    mod = module(MATRIX_SCRIPT, "matrix_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fund_path, price_path = root / "fund.csv", root / "price.csv"
        write_features_csv(fund_path, [{"asset_id": "", "ticker": "AAA", "company_name": "AAA PLC", "feature_quality_status": "FEATURES_READY"}])
        write_prices_csv(price_path, [])
        report = mod.build(fund_path, price_path, root / "out")
    assert report["rejected_rows"] == 1
    assert report["candidates_total"] == 0


CASES = [
    test_all_ratios_computed_when_all_concepts_present,
    test_missing_concept_produces_partial_status_and_rejection_reason,
    test_no_data_produces_insufficient_status,
    test_matrix_classifies_ready_partial_and_missing_correctly,
    test_empty_price_input_never_invents_price_signal,
    test_invalid_identity_rows_are_rejected_not_silently_dropped,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38X-europe-candidate-feature-matrix/ratio-computation/classification/no-invented-price-signal/no-silent-drops")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
