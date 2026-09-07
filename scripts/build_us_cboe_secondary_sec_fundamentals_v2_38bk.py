#!/usr/bin/env python3
"""Block v2.38BK: extract real US GAAP fundamentals and growth features
for the 538 companies v2.38BI CIK-matched and v2.38BJ downloaded real
SEC submissions/companyfacts for -- the Cboe Europe secondary candidates
under country=US that v2.38BC first identified via GLEIF.

Zero new extraction logic: imports and reuses, unmodified,
normalize_us_sec_fundamentals_v2_38f.normalize_company()/quality_row()
and build_us_sec_fundamental_features_v2_38g.build_company()/
as_csv_value() -- the exact same pure functions already proven on the
original 555 US companies and, individually, on Joby Aviation (v2.38BA).
This script is the batch (538-company) version of what v2.38BA did for
one company: loop, don't touch the fixed-count-guarded v2.38D/F/G
pipeline for the original population.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bi_us_cboe_secondary_identity_sec/us_cboe_secondary_identity_sec_v2_38bi.csv"
CACHE_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_38bj_us_cboe_secondary_sec_enrichment/sec_raw_cache_v2_38bj"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bk_us_cboe_secondary_sec_fundamentals"
PHASE = "v2.38BK-us-cboe-secondary-sec-fundamentals"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_candidates(identity_path: Path) -> list[dict[str, str]]:
    if not identity_path.exists():
        raise SystemExit(f"BLOCKED: run scripts/resolve_us_cboe_secondary_identity_sec_v2_38bi.py first ({identity_path} not found)")
    with identity_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return sorted((r for r in rows if r.get("fetch_status") == "resolved" and r.get("cik")), key=lambda r: (r["asset_id"], r["ticker"]))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: ("" if row.get(field) is None else row.get(field)) for field in fields})
    tmp.replace(path)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def build(identity_path: Path, cache_dir: Path, output_dir: Path) -> dict[str, Any]:
    v38f = load_module("normalize_us_sec_fundamentals_v2_38f", ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py")
    v38g = load_module("build_us_sec_fundamental_features_v2_38g", ROOT / "scripts/build_us_sec_fundamental_features_v2_38g.py")

    candidates = load_candidates(identity_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_rows: list[dict[str, str]] = []
    feature_rows: list[dict[str, Any]] = []
    records_path = output_dir / "us_cboe_secondary_sec_fundamental_records_v2_38bk.jsonl"
    skipped_no_cache: list[dict[str, str]] = []

    with records_path.open("w", encoding="utf-8", newline="\n") as records_f:
        for c in candidates:
            row = {"asset_id": c["asset_id"], "ticker": c["ticker"], "cik": c["cik"], "company_name": c["company_name"], "exchange": "CBOE_EUROPE", "enrichment_status": "ENRICHED_SEC_READY"}
            if not (cache_dir / "companyfacts" / f"CIK{c['cik']}.json").exists():
                skipped_no_cache.append({"asset_id": c["asset_id"], "ticker": c["ticker"], "cik": c["cik"], "reason": "companyfacts_not_cached"})
                continue
            records, rejected, flags = v38f.normalize_company(row, cache_dir)
            quality_rows.append(v38f.quality_row(row, records, flags))
            for record in records:
                records_f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            if records:
                feature_row, feature_rejections = v38g.build_company(records)
                feature_row["company_name"] = c["company_name"]
                feature_row["sec_name"] = c.get("sec_name", "")
                feature_rows.append(feature_row)

    write_csv(output_dir / "us_cboe_secondary_sec_fundamental_quality_v2_38bk.csv", quality_rows, v38f.QUALITY_FIELDS)
    feature_fields = v38g.FEATURE_FIELDS + ["company_name", "sec_name"]
    write_csv(output_dir / "us_cboe_secondary_sec_fundamental_features_v2_38bk.csv", [{k: v38g.as_csv_value(v) for k, v in row.items()} for row in feature_rows], feature_fields)
    write_csv(output_dir / "us_cboe_secondary_sec_fundamental_skipped_v2_38bk.csv", skipped_no_cache, ["asset_id", "ticker", "cik", "reason"])

    normalization_status_counts = Counter(q["quality_status"] for q in quality_rows)
    feature_status_counts = Counter(row.get("feature_quality_status", "") for row in feature_rows)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_US_CBOE_SECONDARY_SEC_FUNDAMENTALS",
        "candidates_input": len(candidates),
        "skipped_no_cache": len(skipped_no_cache),
        "companies_normalized": len(quality_rows),
        "normalization_status_counts": dict(normalization_status_counts),
        "companies_with_features": len(feature_rows),
        "feature_status_counts": dict(feature_status_counts),
        "note": "Reuses normalize_us_sec_fundamentals_v2_38f.normalize_company()/quality_row() and build_us_sec_fundamental_features_v2_38g.build_company()/as_csv_value() unmodified -- same methodology validated on the original 555 US companies and individually on Joby Aviation (v2.38BA), applied here in a loop over the 538 Cboe-secondary US candidates CIK-matched by v2.38BI.",
        "network_used": False, "credentials_used": False,
        "guardrails": {"scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False, "phase9c_authorized": False},
    }
    write_json(output_dir / "us_cboe_secondary_sec_fundamentals_report_v2_38bk.json", report)
    return report


def main() -> int:
    report = build(IDENTITY_INPUT, CACHE_DIR, OUT)
    print(json.dumps({k: report[k] for k in ("phase", "status", "candidates_input", "companies_normalized", "normalization_status_counts", "companies_with_features", "feature_status_counts")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
