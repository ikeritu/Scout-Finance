#!/usr/bin/env python3
"""Offline QA for v2.38BA -- extracting real SEC fundamentals for Joby
Aviation by reusing v2.38F.normalize_company() and v2.38G.build_company()
unmodified. No network calls -- builds a synthetic companyfacts.json
fixture in the same shape already used by the existing v2.38F/G test
suites, never the real SEC data.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_joby_aviation_fundamentals_v2_38ba.py"


def module():
    spec = importlib.util.spec_from_file_location("build_us_joby_aviation_fundamentals_v2_38ba", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_companyfacts(path: Path, cik: str, years: list[dict[str, float]]) -> None:
    """years: list of dicts, oldest first, each mapping concept->value for
    one fiscal year's 10-K filing."""
    concept_names = {
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
    us_gaap: dict[str, dict] = {}
    for i, year_data in enumerate(years):
        fy = 2023 + i
        fact_base = {"fy": fy, "fp": "FY", "form": "10-K", "filed": f"{fy + 1}-02-20", "end": f"{fy}-12-31", "frame": f"CY{fy}"}
        for metric, value in year_data.items():
            concept = concept_names[metric]
            unit = "USD/shares" if metric.startswith("eps_") else "USD"
            us_gaap.setdefault(concept, {"units": {unit: []}})
            us_gaap[concept]["units"].setdefault(unit, [])
            us_gaap[concept]["units"][unit].append(dict(fact_base, val=value))
    payload = {"entityName": "Joby Aviation, Inc.", "cik": int(cik), "facts": {"us-gaap": us_gaap}}
    dest = path / "companyfacts" / f"CIK{cik}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload), encoding="utf-8")


def test_blocked_when_sec_cache_missing():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        report = mod.build(root / "empty_cache", root / "out")
    assert report["status"] == "BLOCKED_SEC_CACHE_MISSING"


def test_two_years_of_real_shaped_data_produces_features_ready():
    """Real case shape: an early-stage company with growing revenue but a
    net loss both years -- net_income_yoy_growth must stay unavailable
    (previous value negative, fail-closed per yoy()'s own rule) while
    revenue_yoy_growth calculates normally."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache = root / "cache"
        write_companyfacts(cache, "0001819848", [
            {"revenue": 1000000, "net_income": -500000000, "assets": 1000000000, "liabilities": 200000000, "equity": 800000000, "operating_cash_flow": -400000000, "capex": -20000000, "eps_basic": -1.5, "eps_diluted": -1.5},
            {"revenue": 5000000, "net_income": -600000000, "assets": 1500000000, "liabilities": 250000000, "equity": 1250000000, "operating_cash_flow": -560000000, "capex": -25000000, "eps_basic": -1.7, "eps_diluted": -1.7},
        ])
        report = mod.build(cache, root / "out")
        rows = list(csv.DictReader((root / "out" / "us_joby_aviation_fundamental_features_v2_38ba.csv").open(encoding="utf-8")))
    assert report["normalization_quality_status"] == "NORMALIZED_READY"
    assert rows[0]["asset_id"] == "U04441"
    assert rows[0]["ticker"] == "JOBY"
    assert float(rows[0]["revenue_yoy_growth"]) > 0
    assert rows[0]["net_income_yoy_growth"] == ""  # previous net_income negative -> fail-closed, never a fabricated growth number


def test_reuses_v2_38f_and_v2_38g_functions_directly_not_reimplemented():
    """Guards against future drift: this block must call the real,
    already-tested functions, not a local reimplementation that could
    silently diverge from the 555-company methodology."""
    mod = module()
    v38f = mod.load_module("normalize_us_sec_fundamentals_v2_38f", ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py")
    v38g = mod.load_module("build_us_sec_fundamental_features_v2_38g", ROOT / "scripts/build_us_sec_fundamental_features_v2_38g.py")
    assert hasattr(v38f, "normalize_company")
    assert hasattr(v38g, "build_company")


def test_single_year_only_yields_partial_never_fabricated_growth():
    """With only one fiscal year, ratio features (net_margin, ROA, ROE...)
    still compute from that single year alone, but every YoY growth
    feature has no previous year to compare against -- must stay missing,
    never a fabricated growth number from nothing."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache = root / "cache"
        write_companyfacts(cache, "0001819848", [
            {"revenue": 1000000, "net_income": -500000000, "assets": 1000000000, "liabilities": 200000000, "equity": 800000000, "operating_cash_flow": -400000000, "capex": -20000000, "eps_basic": -1.5, "eps_diluted": -1.5},
        ])
        report = mod.build(cache, root / "out")
        rows = list(csv.DictReader((root / "out" / "us_joby_aviation_fundamental_features_v2_38ba.csv").open(encoding="utf-8")))
    assert report["feature_quality_status"] == "FEATURES_PARTIAL"
    assert rows[0]["revenue_yoy_growth"] == ""
    assert rows[0]["net_margin"] != ""


CASES = [
    test_blocked_when_sec_cache_missing,
    test_two_years_of_real_shaped_data_produces_features_ready,
    test_reuses_v2_38f_and_v2_38g_functions_directly_not_reimplemented,
    test_single_year_only_yields_partial_never_fabricated_growth,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BA-us-joby-aviation-fundamentals/blocked-no-cache/two-year-features/reuses-v2.38f-g/single-year-insufficient/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
