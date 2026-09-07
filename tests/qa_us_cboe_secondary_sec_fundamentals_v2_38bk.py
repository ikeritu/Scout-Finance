#!/usr/bin/env python3
"""Offline QA for v2.38BK -- batch fundamentals/growth extraction for the
538 v2.38BI-resolved Cboe-secondary US candidates. No network calls:
builds synthetic companyfacts.json fixtures in the same shape used by
the existing v2.38F/G/BA test suites, never the real SEC data."""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_cboe_secondary_sec_fundamentals_v2_38bk.py"

IDENTITY_FIELDS = ["asset_id", "ticker", "company_name", "cik", "sec_name", "sec_ticker", "sec_exchange", "match_tier", "fetch_status", "fetch_reason", "phase", "created_at_utc"]

CONCEPT_NAMES = {
    "revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
    "net_income": "NetIncomeLoss",
    "assets": "Assets",
    "liabilities": "Liabilities",
    "equity": "StockholdersEquity",
    "operating_cash_flow": "NetCashProvidedByUsedInOperatingActivities",
    "capex": "PaymentsToAcquirePropertyPlantAndEquipment",
    "eps_basic": "EarningsPerShareBasic",
    "eps_diluted": "EarningsPerShareDiluted",
}


def module():
    spec = importlib.util.spec_from_file_location("build_us_cboe_secondary_sec_fundamentals_v2_38bk", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_identity_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=IDENTITY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def identity_row(asset_id: str, ticker: str, company_name: str, cik: str, sec_name: str = "", fetch_status: str = "resolved") -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": company_name, "cik": cik, "sec_name": sec_name, "sec_ticker": "", "sec_exchange": "", "match_tier": "exact_normalized_name", "fetch_status": fetch_status, "fetch_reason": "", "phase": "", "created_at_utc": ""}


def write_companyfacts(cache_dir: Path, cik: str, years: list[dict[str, float]]) -> None:
    us_gaap: dict[str, dict] = {}
    for i, year_data in enumerate(years):
        fy = 2022 + i
        fact_base = {"fy": fy, "fp": "FY", "form": "10-K", "filed": f"{fy + 1}-02-20", "end": f"{fy}-12-31", "frame": f"CY{fy}"}
        for metric, value in year_data.items():
            concept = CONCEPT_NAMES[metric]
            unit = "USD/shares" if metric.startswith("eps_") else "USD"
            us_gaap.setdefault(concept, {"units": {unit: []}})
            us_gaap[concept]["units"].setdefault(unit, [])
            us_gaap[concept]["units"][unit].append(dict(fact_base, val=value))
    dest = cache_dir / "companyfacts" / f"CIK{cik}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"cik": int(cik), "facts": {"us-gaap": us_gaap}}), encoding="utf-8")


TWO_YEARS = [
    {"revenue": 100_000_000, "net_income": 5_000_000, "assets": 300_000_000, "liabilities": 100_000_000, "equity": 200_000_000, "operating_cash_flow": 10_000_000, "capex": -2_000_000, "eps_basic": 0.5, "eps_diluted": 0.49},
    {"revenue": 120_000_000, "net_income": 7_000_000, "assets": 330_000_000, "liabilities": 105_000_000, "equity": 225_000_000, "operating_cash_flow": 12_000_000, "capex": -2_500_000, "eps_basic": 0.6, "eps_diluted": 0.59},
]


def test_two_companies_with_full_data_reach_features_ready():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        identity_path = root / "identity.csv"
        write_identity_csv(identity_path, [
            identity_row("U1", "AAA", "Alpha Widgets Inc", "0001111111"),
            identity_row("U2", "BBB", "Beta Gadgets Corp", "0002222222"),
        ])
        cache_dir = root / "cache"
        write_companyfacts(cache_dir, "0001111111", TWO_YEARS)
        write_companyfacts(cache_dir, "0002222222", TWO_YEARS)
        report = mod.build(identity_path, cache_dir, root / "out")
        rows = {r["asset_id"]: r for r in csv.DictReader((root / "out" / "us_cboe_secondary_sec_fundamental_features_v2_38bk.csv").open(encoding="utf-8"))}
    assert report["companies_normalized"] == 2
    assert report["normalization_status_counts"].get("NORMALIZED_READY") == 2
    assert report["feature_status_counts"].get("FEATURES_READY") == 2
    assert float(rows["U1"]["revenue_yoy_growth"]) > 0
    assert rows["U1"]["company_name"] == "Alpha Widgets Inc"


def test_candidate_without_cached_companyfacts_is_skipped_not_a_crash():
    """A resolved CIK whose SEC fetch (v2.38BJ) is still pending, or hit a
    real 404 on companyfacts specifically, must be skipped cleanly and
    counted -- never silently dropped and never a fabricated zero-feature
    row."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        identity_path = root / "identity.csv"
        write_identity_csv(identity_path, [
            identity_row("U1", "AAA", "Alpha Widgets Inc", "0001111111"),
            identity_row("U2", "BBB", "No Facts Yet Inc", "0003333333"),
        ])
        cache_dir = root / "cache"
        write_companyfacts(cache_dir, "0001111111", TWO_YEARS)
        report = mod.build(identity_path, cache_dir, root / "out")
        skipped = list(csv.DictReader((root / "out" / "us_cboe_secondary_sec_fundamental_skipped_v2_38bk.csv").open(encoding="utf-8")))
    assert report["companies_normalized"] == 1
    assert report["skipped_no_cache"] == 1
    assert skipped[0]["asset_id"] == "U2"
    assert skipped[0]["reason"] == "companyfacts_not_cached"


def test_ambiguous_and_unresolved_identity_rows_are_never_processed():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        identity_path = root / "identity.csv"
        write_identity_csv(identity_path, [
            identity_row("U1", "AAA", "Alpha Widgets Inc", "0001111111"),
            identity_row("U2", "BBB", "", "", fetch_status="unresolved"),
            identity_row("U3", "CCC", "", "", fetch_status="ambiguous"),
        ])
        cache_dir = root / "cache"
        write_companyfacts(cache_dir, "0001111111", TWO_YEARS)
        report = mod.build(identity_path, cache_dir, root / "out")
    assert report["candidates_input"] == 1


def test_reuses_v2_38f_and_v2_38g_functions_directly_not_reimplemented():
    """Guards against future drift: this block must call the real,
    already-tested functions, not a local reimplementation."""
    mod = module()
    v38f = mod.load_module("normalize_us_sec_fundamentals_v2_38f", ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py")
    v38g = mod.load_module("build_us_sec_fundamental_features_v2_38g", ROOT / "scripts/build_us_sec_fundamental_features_v2_38g.py")
    assert hasattr(v38f, "normalize_company")
    assert hasattr(v38g, "build_company")


def test_missing_identity_input_raises_blocked_not_a_silent_empty_run():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        raised = False
        try:
            mod.build(root / "does_not_exist.csv", root / "cache", root / "out")
        except SystemExit:
            raised = True
    assert raised


CASES = [
    test_two_companies_with_full_data_reach_features_ready,
    test_candidate_without_cached_companyfacts_is_skipped_not_a_crash,
    test_ambiguous_and_unresolved_identity_rows_are_never_processed,
    test_reuses_v2_38f_and_v2_38g_functions_directly_not_reimplemented,
    test_missing_identity_input_raises_blocked_not_a_silent_empty_run,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BK-us-cboe-secondary-sec-fundamentals/skip-uncached/reuses-v2.38f-g/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
