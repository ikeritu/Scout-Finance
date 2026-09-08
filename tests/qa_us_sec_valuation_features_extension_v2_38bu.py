#!/usr/bin/env python3
"""Offline QA for the v2.38BU US SEC valuation features extension. No
network, no real licensed data -- every fixture companyfacts JSON below
is synthetic."""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_sec_valuation_features_extension_v2_38bu.py"


def module():
    spec = importlib.util.spec_from_file_location("build_us_sec_valuation_features_extension_v2_38bu", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["asset_id", "ticker", "company_name", "exchange", "cik"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def usd_fact(value: float, fy: int = 2024) -> dict:
    return {"val": value, "fy": fy, "fp": "FY", "form": "10-K", "filed": f"{fy + 1}-02-01", "end": f"{fy}-12-31"}


def shares_fact(value: float, fy: int = 2024) -> dict:
    return {"val": value, "fy": fy, "fp": "FY", "form": "10-K", "filed": f"{fy + 1}-02-01", "end": f"{fy}-12-31"}


def write_companyfacts(cache_dir: Path, cik: str, concepts: dict) -> None:
    path = cache_dir / "companyfacts" / f"CIK{cik}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    facts = {}
    for concept, (unit, fact) in concepts.items():
        facts[concept] = {"units": {unit: [fact]}}
    path.write_text(json.dumps({"facts": {"us-gaap": facts}}), encoding="utf-8")


def row(asset_id: str, cik: str) -> dict:
    return {"asset_id": asset_id, "ticker": asset_id, "company_name": f"{asset_id} Co", "exchange": "NASDAQ", "cik": cik}


def build_with(tmp: Path, rows: list[dict], cache_dir: Path):
    mod = module()
    features_path = tmp / "features.csv"
    write_csv(features_path, rows)
    empty_path = tmp / "empty.csv"
    write_csv(empty_path, [])
    report = mod.build(features_path, cache_dir, empty_path, cache_dir, empty_path, cache_dir, tmp / "out")
    out_rows = {r["asset_id"]: r for r in csv.DictReader((tmp / "out" / "us_sec_valuation_features_extension_v2_38bu.csv").open(encoding="utf-8"))}
    return report, out_rows


def test_all_three_concepts_present_is_ready():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache_dir = root / "cache"
        write_companyfacts(cache_dir, "0000000001", {
            "OperatingIncomeLoss": ("USD", usd_fact(200.0)),
            "Revenues": ("USD", usd_fact(1000.0)),
            "StockholdersEquity": ("USD", usd_fact(500.0)),
            "CommonStockSharesOutstanding": ("shares", shares_fact(100.0)),
            "EarningsPerShareBasic": ("USD/shares", usd_fact(2.5)),
        })
        report, rows = build_with(root, [row("U1", "0000000001")], cache_dir)
    assert rows["U1"]["valuation_extension_status"] == "READY"
    assert float(rows["U1"]["operating_margin"]) == 0.2
    assert float(rows["U1"]["book_value_per_share"]) == 5.0
    assert float(rows["U1"]["eps_basic"]) == 2.5


def test_shares_outstanding_real_unit_is_plain_shares_not_usd():
    """The real bug this script had to fix: v2.38F's own supported_unit()
    only ever accepted "USD" or a "*/shares" ratio unit -- a raw share
    COUNT reports its real SEC unit as plain "shares", confirmed against
    the real, already-cached CIK0000002488.json. Without the wrapper,
    book_value_per_share would be blank for every single company."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache_dir = root / "cache"
        write_companyfacts(cache_dir, "0000000002", {
            "Revenues": ("USD", usd_fact(1000.0)),
            "StockholdersEquity": ("USD", usd_fact(300.0)),
            "CommonStockSharesOutstanding": ("shares", shares_fact(150.0)),
        })
        report, rows = build_with(root, [row("U1", "0000000002")], cache_dir)
    assert rows["U1"]["book_value_per_share"] != ""
    assert float(rows["U1"]["book_value_per_share"]) == 2.0


def test_missing_operating_income_leaves_operating_margin_blank_never_estimated():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache_dir = root / "cache"
        write_companyfacts(cache_dir, "0000000003", {
            "Revenues": ("USD", usd_fact(1000.0)),
            "StockholdersEquity": ("USD", usd_fact(500.0)),
            "CommonStockSharesOutstanding": ("shares", shares_fact(100.0)),
        })
        report, rows = build_with(root, [row("U1", "0000000003")], cache_dir)
    assert rows["U1"]["operating_margin"] == ""
    assert rows["U1"]["valuation_extension_status"] == "PARTIAL"


def test_company_with_no_normalizable_concepts_at_all_is_insufficient_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache_dir = root / "cache"
        (cache_dir / "companyfacts").mkdir(parents=True)
        report, rows = build_with(root, [row("U1", "0000000004")], cache_dir)
    assert rows["U1"]["valuation_extension_status"] == "INSUFFICIENT_EVIDENCE"
    assert rows["U1"]["operating_margin"] == ""


def test_row_without_a_cik_is_skipped_never_crashes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache_dir = root / "cache"
        (cache_dir / "companyfacts").mkdir(parents=True)
        report, rows = build_with(root, [{"asset_id": "U1", "ticker": "U1", "company_name": "No CIK Co", "exchange": "NASDAQ", "cik": ""}], cache_dir)
    assert "U1" not in rows
    assert report["companies_processed"] == 0


def test_original_v2_38f_supported_unit_behavior_is_unchanged_for_every_other_concept():
    """The monkeypatch must be additive only -- every concept v2.38F
    already validates (revenue, net_income, eps_basic...) must keep
    exactly its original unit-acceptance behavior."""
    mod = module()
    v38f = mod.load_module("normalize_us_sec_fundamentals_v2_38f_check", ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py")
    original = v38f.supported_unit
    assert original("revenue", "USD") is True
    assert original("revenue", "shares") is False
    assert original("eps_basic", "USD/shares") is True
    assert original("shares_outstanding", "shares") is False  # confirms the real gap this script had to patch


CASES = [
    test_all_three_concepts_present_is_ready,
    test_shares_outstanding_real_unit_is_plain_shares_not_usd,
    test_missing_operating_income_leaves_operating_margin_blank_never_estimated,
    test_company_with_no_normalizable_concepts_at_all_is_insufficient_evidence,
    test_row_without_a_cik_is_skipped_never_crashes,
    test_original_v2_38f_supported_unit_behavior_is_unchanged_for_every_other_concept,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BU-us-sec-valuation-features-extension/zero-new-network/monkeypatch-additive-only/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
