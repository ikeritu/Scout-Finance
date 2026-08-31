#!/usr/bin/env python3
"""Offline QA for the block-E coverage report builder. Uses tiny synthetic
fixture raw collections (never the real licensed downloads) to check
counting logic and reproducibility. No network, no credentials.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_fundamentals_acquisition_report_v2_34e.py"

MANIFEST_FIELDS = ["asset_id", "pilot_id", "ticker", "provider_symbol_jquants", "provider_symbol_twse", "company_name", "exchange"]


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_manifest(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerow({"asset_id": "P001", "pilot_id": "P001", "ticker": "1301", "provider_symbol_jquants": "13010", "provider_symbol_twse": "", "company_name": "A", "exchange": "JPX"})
        writer.writerow({"asset_id": "P002", "pilot_id": "P002", "ticker": "1101", "provider_symbol_jquants": "", "provider_symbol_twse": "1101.TW", "company_name": "B", "exchange": "TWSE"})


def write_jquants_fixture(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True)
    (raw_dir / "P001.json").write_text(json.dumps({
        "asset": {"pilot_id": "P001"},
        "disclosures": [
            {"DocType": "1QFinancialStatements_Consolidated_JP", "CurPerType": "1Q", "CurFYSt": "2024-04-01", "Sales": "100", "OP": "10", "NP": "5", "EPS": "1.2", "TA": "500", "Eq": "200"},
            {"DocType": "EarnForecastRevision", "CurPerType": "FY", "CurFYSt": "2024-04-01", "Sales": "", "OP": "", "NP": "", "EPS": "", "TA": "", "Eq": ""},
        ],
    }), encoding="utf-8")
    (raw_dir / "download_report_v2_34d.json").write_text(json.dumps({"status": "COMPLETED", "collected": 1, "failed": 0}), encoding="utf-8")


def write_twse_fixture(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True)
    (raw_dir / "P002.json").write_text(json.dumps({
        "asset": {"pilot_id": "P002"},
        "snapshot_files": {
            "income_statement": [{"年度": "115", "季別": "2", "公司代號": "1101", "營業收入": "1000", "營業利益（損失）": "100", "本期淨利（淨損）": "50"}],
            "balance_sheet": [{"年度": "115", "季別": "2", "公司代號": "1101", "資產總計": "5000", "權益總計": "2000"}],
        },
    }), encoding="utf-8")
    (raw_dir / "download_report_v2_34d.json").write_text(json.dumps({"status": "COMPLETED", "extracted": 1, "failed": 0}), encoding="utf-8")


def test_report_counts_and_forecast_revision_exclusion_and_determinism():
    mod = module("build_fundamentals_report_v2_34e_1")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        mod.MANIFEST_PATH = tmp_path / "manifest.csv"
        write_manifest(mod.MANIFEST_PATH)
        mod.JQUANTS_RAW_DIR = tmp_path / "jquants_raw"
        write_jquants_fixture(mod.JQUANTS_RAW_DIR)
        mod.TWSE_RAW_DIR = tmp_path / "twse_raw"
        write_twse_fixture(mod.TWSE_RAW_DIR)

        report1 = mod.build_report()
        report2 = mod.build_report()
        assert json.dumps(report1, sort_keys=True) == json.dumps(report2, sort_keys=True)

        assert report1["expected_assets"] == {"JPX": 1, "TWSE": 1}
        jq = report1["sources"]["jquants_fins_summary"]
        assert jq["obtained_assets"] == 1 and jq["total_disclosures"] == 2
        # only the real statement (1Q) should count toward core metric presence;
        # the EarnForecastRevision disclosure has every field blank and must not
        # be silently counted as if it were reported data.
        assert jq["metric_presence_disclosure_count"]["revenue"] == 1
        assert jq["metric_presence_disclosure_count"]["net_income"] == 1

        tw = report1["sources"]["twse_mops_opendata"]
        assert tw["obtained_assets"] == 1
        assert tw["metric_presence_row_count"]["revenue"] == 1
        assert tw["metric_presence_row_count"]["total_equity"] == 1

        assert report1["gate"] == {"jpx_full_coverage": True, "twse_full_coverage": True}


def test_gate_fails_closed_when_an_asset_is_missing():
    mod = module("build_fundamentals_report_v2_34e_2")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        mod.MANIFEST_PATH = tmp_path / "manifest.csv"
        write_manifest(mod.MANIFEST_PATH)
        mod.JQUANTS_RAW_DIR = tmp_path / "jquants_raw"
        mod.JQUANTS_RAW_DIR.mkdir(parents=True)  # no P001.json -- simulates an incomplete collection
        (mod.JQUANTS_RAW_DIR / "download_report_v2_34d.json").write_text(json.dumps({"status": "COMPLETED_WITH_ERRORS", "collected": 0, "failed": 1}), encoding="utf-8")
        mod.TWSE_RAW_DIR = tmp_path / "twse_raw"
        write_twse_fixture(mod.TWSE_RAW_DIR)

        report = mod.build_report()
        assert report["gate"]["jpx_full_coverage"] is False
        assert report["gate"]["twse_full_coverage"] is True


CASES = [
    test_report_counts_and_forecast_revision_exclusion_and_determinism,
    test_gate_fails_closed_when_an_asset_is_missing,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.34E-fundamentals-acquisition-report/determinism/forecast-revision-exclusion/fail-closed-gate/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
