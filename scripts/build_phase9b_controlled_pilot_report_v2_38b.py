#!/usr/bin/env python3
"""Validate local v2.38B pilot evidence and publish aggregate-only results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/full_universe_source_acquisition/v2_38b_global_enrichment"
JPX_REQUIRED = {"Date", "Code", "O", "H", "L", "C", "Vo"}
TWSE_REQUIRED = {"Date", "Open", "High", "Low", "Close", "Volume_shares"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_prices(folder: Path, expected_ids: set[str], required: set[str]) -> dict[str, object]:
    files = sorted(folder.glob("U*.json"))
    if {path.stem for path in files} != expected_ids:
        raise ValueError(f"{folder.name}: asset identity set does not match the controlled pilot")
    counts: list[int] = []
    starts: list[str] = []
    ends: list[str] = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("pilot", {}).get("pilot_id") != path.stem:
            raise ValueError(f"{path.name}: embedded identity mismatch")
        prices = payload.get("prices") or []
        if not prices or not required.issubset(prices[0]):
            raise ValueError(f"{path.name}: empty data or schema mismatch")
        dates = sorted(row["Date"] for row in prices if row.get("Date"))
        if len(dates) != len(prices) or len(dates) != len(set(dates)):
            raise ValueError(f"{path.name}: missing or duplicate dates")
        counts.append(len(prices)); starts.append(dates[0]); ends.append(dates[-1])
    return {
        "assets": len(files),
        "price_rows": sum(counts),
        "rows_min": min(counts),
        "rows_max": max(counts),
        "date_start": min(starts),
        "date_end": max(ends),
        "invalid_assets": 0,
    }


def build_report(base: Path) -> dict[str, object]:
    overlay_path = base / "jpx_symbol_resolution_overlay_25_v2_38b.csv"
    twse_batch_path = base / "twse_collection_pilot_25_v2_38b.csv"
    overlay = read_csv(overlay_path)
    twse_batch = read_csv(twse_batch_path)
    if len(overlay) != 25 or any(row["resolution_status"] != "EXACT_COMPANY_NAME_MATCH" for row in overlay):
        raise ValueError("JPX overlay must contain 25 exact-match resolutions")
    jpx_ids = {row["asset_id"] for row in overlay}
    twse_ids = {row["pilot_id"] for row in twse_batch}
    if len(jpx_ids) != 25 or len(twse_ids) != 25:
        raise ValueError("Controlled pilot identities must be unique")
    jpx = validate_prices(base / "jpx_price_pilot_25_results_v2_38b", jpx_ids, JPX_REQUIRED)
    twse = validate_prices(base / "twse_collection_pilot_25_results_v2_38b", twse_ids, TWSE_REQUIRED)
    return {
        "phase": "v2.38B-controlled-global-enrichment-pilot",
        "status": "CONTROLLED_PILOT_VALIDATED_NOT_GLOBAL_PROMOTION",
        "markets": {"JPX": {**jpx, "adjusted_prices": True}, "TWSE": {**twse, "adjusted_prices": False}},
        "totals": {"assets": jpx["assets"] + twse["assets"], "price_rows": jpx["price_rows"] + twse["price_rows"], "invalid_assets": 0},
        "evidence": {"jpx_symbol_overlay_sha256": sha256(overlay_path), "raw_price_files_published": False},
        "limitations": [
            "This validates a controlled 50-asset pilot, not enrichment of the 21,165 eligible assets.",
            "TWSE prices are unadjusted and must not be compared as adjusted-return series.",
            "JPX history remains limited by the active J-Quants subscription window.",
        ],
        "guardrails": {"scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False, "phase9c_authorized": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.base / "controlled_pilot_aggregate_report_v2_38b.json"
    try:
        report = build_report(args.base)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": type(exc).__name__, "detail": str(exc)}, ensure_ascii=False))
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(output)
    print(json.dumps({"status": "PASS", **report["totals"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
