#!/usr/bin/env python3
"""Block 9BA: extract real SEC fundamentals for Joby Aviation, Inc. (asset
U04441, ticker JOBY, NYSE, CIK 0001819848) -- the real, current, Delaware-
incorporated company hiding behind the Xetra-listed asset (8TQ, ISIN
KYG651631007, U37518) that v2.38AV classified as "Cayman Islands" purely
from its ISIN's issuance prefix. v2.38AZ confirmed live against SEC EDGAR
that the ISIN prefix reflects only the 2021 SPAC-era shell history
("Reinvent Technology Partners"); the real operating company already sits
in this project's own 43,089-company census under a separate asset_id
(U04441) with its CIK already resolved since v2.38D, but never processed
by the v2.38F/G fundamentals pipeline.

This block does NOT touch the fixed-count, contract-guarded v2.38D/F
pipeline (both raise BLOCKED if the input row count does not match an
`expected_us_rows`/`expected_cik_resolved` constant baked into
config/us_sec_foundation_contract_v1.json and
config/us_sec_fundamental_normalization_contract_v1.json) -- editing
those counts for one extra company would be a much bigger, riskier change
than the task warrants. Instead it imports and reuses, unmodified, the
exact same pure functions already proven on the 555 companies:
normalize_us_sec_fundamentals_v2_38f.normalize_company() and
build_us_sec_fundamental_features_v2_38g.build_company() -- zero new
extraction or feature logic, just applied to one more real company.

The real SEC data (submissions + companyfacts JSON for CIK 0001819848)
was already fetched into the existing v2.38E raw cache via:
    python scripts/run_us_sec_enrichment_v2_38e.py --asset-id U04441 --execute
(requires SCOUT_FINANCE_SEC_USER_AGENT, the same credential already used
for the other 555 companies -- never a new policy decision).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEC_CACHE_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_38e_us_sec_enrichment_expansion/sec_raw_cache_v2_38e"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ba_us_joby_aviation_fundamentals"
PHASE = "v2.38BA-us-joby-aviation-fundamentals"

ASSET_ROW = {
    "asset_id": "U04441",
    "ticker": "JOBY",
    "company_name": "Joby Aviation, Inc.",
    "exchange": "NYSE",
    "cik": "0001819848",
    "enrichment_status": "ENRICHED_SEC_READY",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_csv_row(path: Path, row: dict[str, Any], fields: list[str]) -> None:
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerow({field: ("" if row.get(field) is None else row.get(field)) for field in fields})
    tmp.replace(path)


def build(cache_dir: Path, output_dir: Path) -> dict[str, Any]:
    v38f = load_module("normalize_us_sec_fundamentals_v2_38f", ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py")
    v38g = load_module("build_us_sec_fundamental_features_v2_38g", ROOT / "scripts/build_us_sec_fundamental_features_v2_38g.py")

    if not (cache_dir / "companyfacts" / f"CIK{ASSET_ROW['cik']}.json").exists():
        return {"phase": PHASE, "status": "BLOCKED_SEC_CACHE_MISSING", "reason": "run scripts/run_us_sec_enrichment_v2_38e.py --asset-id U04441 --execute first", "network_used": False, "phase9c_authorized": False}

    records, rejected, flags = v38f.normalize_company(ASSET_ROW, cache_dir)
    quality = v38f.quality_row(ASSET_ROW, records, flags)

    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "us_joby_aviation_fundamental_records_v2_38ba.jsonl"
    with records_path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    write_csv_row(output_dir / "us_joby_aviation_fundamental_quality_v2_38ba.csv", quality, v38f.QUALITY_FIELDS)

    if records:
        feature_row, feature_rejections = v38g.build_company(records)
    else:
        feature_row, feature_rejections = {}, []

    if feature_row:
        write_csv_row(output_dir / "us_joby_aviation_fundamental_features_v2_38ba.csv", {k: v38g.as_csv_value(v) for k, v in feature_row.items()}, v38g.FEATURE_FIELDS)

    report = {
        "phase": PHASE, "asset_id": ASSET_ROW["asset_id"], "ticker": ASSET_ROW["ticker"], "cik": ASSET_ROW["cik"],
        "normalized_records": len(records), "normalization_rejected": len(rejected),
        "normalization_quality_status": quality["quality_status"],
        "metrics_available": quality["metrics_available"].split("|") if quality["metrics_available"] else [],
        "missing_metrics": quality["missing_metrics"].split("|") if quality["missing_metrics"] else [],
        "feature_quality_status": feature_row.get("feature_quality_status", "NO_RECORDS"),
        "features_calculated": feature_row.get("features_calculated", ""),
        "features_missing": feature_row.get("features_missing", ""),
        "feature_rejections": len(feature_rejections),
        "note": "Reuses v2.38F.normalize_company() and v2.38G.build_company() unmodified -- same methodology already validated on 555 companies, applied to one real, previously-unprocessed company discovered via v2.38AV/AZ.",
        "network_used": False, "credentials_used": False, "phase9c_authorized": False,
    }
    write_json(output_dir / "us_joby_aviation_fundamentals_summary_v2_38ba.json", report)
    return report


def main() -> int:
    report = build(SEC_CACHE_DIR, OUT)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("status") != "BLOCKED_SEC_CACHE_MISSING" else 2


if __name__ == "__main__":
    raise SystemExit(main())
