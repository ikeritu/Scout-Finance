#!/usr/bin/env python3
"""Local-only QA gate for the real 8-asset TWSE official STOCK_DAY
collection. Never fails CI merely because the raw data folder is absent
(prints SKIP and exits 0). Run explicitly and locally to validate the real
collection.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/twse_opendata_prices_collection_v2_33i"


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not RAW_DIR.exists():
        print("SKIP: local TWSE price data not present; not a repository defect")
        return 0

    builder = module(ROOT / "scripts/build_twse_opendata_collection_report_v2_33i.py", "build_twse_opendata_collection_report_v2_33i")
    files = sorted(RAW_DIR.glob("P*.json"))
    errors: list[str] = []
    entries: list[dict] = []
    for path in files:
        entry = builder.validate_file(path, errors)
        if entry is not None:
            entries.append(entry)

    assert not errors, f"schema errors: {errors}"
    assert len(entries) == 8, f"expected 8 valid assets, found {len(entries)}"

    report = builder.build_report(entries)
    assert report["date_coverage"]["earliest_confirmed_source_date"] == "2010-01-04"
    assert report["sessions_per_asset"]["min"] >= 1
    assert report["production_scoring_authorized"] is False
    assert report["allow_ranking"] is False

    errors2: list[str] = []
    entries2 = [e for e in (builder.validate_file(p, errors2) for p in files) if e is not None]
    report2 = builder.build_report(entries2)
    assert report == report2, "aggregate report is not reproducible across runs"

    print(json.dumps({
        "valid_assets": len(entries),
        "valid_numeric_observations": report["row_counts"]["valid_numeric_observations"],
        "min_sessions": report["sessions_per_asset"]["min"],
        "max_sessions": report["sessions_per_asset"]["max"],
        "assets_reaching_earliest_confirmed_date": report["assets_reaching_earliest_confirmed_date"],
    }, ensure_ascii=False))
    print("PASS: v2.33I-twse-opendata/8-valid/0-schema-errors/reproducible/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
