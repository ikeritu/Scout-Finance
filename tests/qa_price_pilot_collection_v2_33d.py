#!/usr/bin/env python3
"""Local-only QA gate for the real 77-asset EODHD price pilot collection.

This validates the licensed, gitignored raw JSON files under
outputs/full_universe_source_acquisition/v2_33d_price_pilot/eodhd_prices_collection_77_v2_33d/.
It must never fail CI merely because that folder is absent (no license to
redistribute the raw data): it prints SKIP and exits 0 in that case. Run it
explicitly and locally to validate the real collection.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33d_price_pilot/eodhd_prices_collection_77_v2_33d"


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not RAW_DIR.exists():
        print("SKIP: local licensed EODHD price data not present; not a repository defect")
        return 0

    builder = module(ROOT / "scripts/build_price_pilot_collection_report_v2_33d.py", "build_price_pilot_collection_report_v2_33d")
    files = sorted(RAW_DIR.glob("P*.json"))
    errors: list[str] = []
    entries: list[dict] = []
    for path in files:
        entry = builder.validate_file(path, errors)
        if entry is not None:
            entries.append(entry)

    assert not errors, f"schema errors: {errors}"
    assert len(entries) == 77, f"expected 77 valid assets, found {len(entries)}"
    assert all(e["pilot_id"] != "P014" for e in entries), "P014 must be excluded from the collection"
    p230 = next((e for e in entries if e["pilot_id"] == "P230"), None)
    assert p230 is not None and p230["provider_symbol"] == "MOG-B.US", "P230 must resolve to MOG-B.US"

    report = builder.build_report(entries)
    assert report["row_counts"]["raw_rows_including_provider_notice_rows"] == 18791
    assert report["row_counts"]["valid_numeric_observations"] == 18714
    assert report["row_counts"]["provider_notice_rows"] == 77
    assert report["sessions_per_asset"]["min"] >= 1
    assert report["assets_reaching_2021_or_earlier"] == 0
    assert report["production_scoring_authorized"] is False
    assert report["allow_ranking"] is False

    # Reproducibility: re-running the same validator over the same local files
    # must yield identical aggregate counts.
    errors2: list[str] = []
    entries2 = [e for e in (builder.validate_file(p, errors2) for p in files) if e is not None]
    report2 = builder.build_report(entries2)
    assert report == report2, "aggregate report is not reproducible across runs"

    print(json.dumps({
        "valid_assets": len(entries),
        "raw_rows": report["row_counts"]["raw_rows_including_provider_notice_rows"],
        "valid_numeric_observations": report["row_counts"]["valid_numeric_observations"],
        "min_sessions": report["sessions_per_asset"]["min"],
        "max_sessions": report["sessions_per_asset"]["max"],
        "median_coverage_pct": report["date_coverage"]["median_sessions_coverage_pct_of_requested"],
    }, ensure_ascii=False))
    print("PASS: v2.33D1-collection/77-valid/0-schema-errors/P014-excluded/P230-MOG-B.US/reproducible/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
