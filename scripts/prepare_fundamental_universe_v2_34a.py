#!/usr/bin/env python3
"""Build the canonical 50-asset fundamentals universe manifest (phase 5,
block A) from the real, already-validated phase-4 price collections
(J-Quants v2.33G, TWSE v2.33I). No network calls, no credentials, no
fabricated identifiers -- ISIN/LEI are recorded as empty when the
canonical census does not carry them, never guessed.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_34a_fundamental_universe_audit"

JQUANTS_RESOLUTION = ROOT / "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_symbol_resolution_v2_33g.csv"
PILOT_SYMBOLS_V2_33D = ROOT / "outputs/full_universe_source_acquisition/v2_33d_price_pilot/price_pilot_symbols_v2_33d.csv"
COVERAGE_MANIFEST = ROOT / "outputs/full_universe_source_acquisition/v2_33q_multisource_architecture/coverage_manifest_v2_33q.json"


def load_jquants_rows() -> list[dict]:
    with JQUANTS_RESOLUTION.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["status"].startswith("resolved")]
    if len(rows) != 42:
        raise SystemExit(f"expected 42 resolved J-Quants rows, found {len(rows)}")
    with PILOT_SYMBOLS_V2_33D.open(encoding="utf-8", newline="") as handle:
        names_by_pilot_id = {r["pilot_id"]: r["company_name"].strip() for r in csv.DictReader(handle) if r["exchange"] == "JPX"}
    for row in rows:
        row["_verified_company_name"] = names_by_pilot_id.get(row["pilot_id"], "")
    return rows


def load_twse_rows() -> list[dict]:
    with PILOT_SYMBOLS_V2_33D.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["exchange"] == "TWSE"]
    if len(rows) != 8:
        raise SystemExit(f"expected 8 TWSE rows, found {len(rows)}")
    return rows


def load_price_coverage() -> dict[str, dict]:
    payload = json.loads(COVERAGE_MANIFEST.read_text(encoding="utf-8"))
    return {row["asset_id"]: row for row in payload["manifest"]}


def build_manifest() -> list[dict]:
    price_coverage = load_price_coverage()
    manifest = []

    for row in load_jquants_rows():
        asset_id = row["pilot_id"]
        cov = price_coverage.get(asset_id, {})
        manifest.append({
            "asset_id": asset_id,
            "pilot_id": asset_id,
            "ticker": row["ticker"],
            "provider_symbol_jquants": row["provider_symbol"],
            "provider_symbol_twse": "",
            "company_name": row.get("_verified_company_name", ""),
            "country": "JP",
            "exchange": "JPX",
            "mic": "",
            "isin": "",
            "lei": "",
            "quoting_currency": "JPY",
            "identity_source": "jquants_master_exact_name_match_v2_33g",
            "identity_status": "identity_verified",
            "identity_notes": "Resolved v2.33G via exact CompanyNameEnglish match against the official /v2/equities/master endpoint; 0 false matches (fail-closed resolver).",
            "price_history_available": cov.get("sessions_available") is not None,
            "price_sessions_available": cov.get("sessions_available"),
            "price_date_range_start": cov.get("date_range_start"),
            "price_date_range_end": cov.get("date_range_end"),
            "fundamentals_eligible": True,
        })

    for row in load_twse_rows():
        asset_id = row["pilot_id"]
        cov = price_coverage.get(asset_id, {})
        manifest.append({
            "asset_id": asset_id,
            "pilot_id": asset_id,
            "ticker": row["ticker"],
            "provider_symbol_jquants": "",
            "provider_symbol_twse": row["provider_symbol"] or row["ticker"],
            "company_name": row.get("company_name", "").strip(),
            "country": "TW",
            "exchange": "TWSE",
            "mic": "",
            "isin": "",
            "lei": "",
            "quoting_currency": "TWD",
            "identity_source": "deterministic_ticker_suffix_v2_33d_confirmed_v2_33i",
            "identity_status": "identity_verified",
            "identity_notes": "Deterministic .TW ticker mapping (v2.33D), confirmed by 16-year real official price collection (v2.33I) under the same code.",
            "price_history_available": cov.get("sessions_available") is not None,
            "price_sessions_available": cov.get("sessions_available"),
            "price_date_range_start": cov.get("date_range_start"),
            "price_date_range_end": cov.get("date_range_end"),
            "fundamentals_eligible": True,
        })

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest()
    if len(manifest) != 50:
        raise SystemExit(f"expected 50 assets total, built {len(manifest)}")

    by_status = {}
    for row in manifest:
        by_status.setdefault(row["identity_status"], 0)
        by_status[row["identity_status"]] += 1
    by_exchange = {}
    for row in manifest:
        by_exchange.setdefault(row["exchange"], 0)
        by_exchange[row["exchange"]] += 1

    summary = {
        "phase": "v2.34A-fundamental-universe-audit",
        "expected_assets": 50,
        "built_assets": len(manifest),
        "by_exchange": by_exchange,
        "by_identity_status": by_status,
        "eligible_for_fundamentals": sum(1 for r in manifest if r["fundamentals_eligible"]),
        "production_scoring_authorized": False,
        "allow_ranking": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fields = list(manifest[0].keys())

        csv_path = OUT_DIR / "fundamental_universe_manifest_v2_34a.csv"
        tmp = csv_path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(manifest)
        tmp.replace(csv_path)

        report_path = OUT_DIR / "fundamental_universe_audit_report_v2_34a.json"
        tmp2 = report_path.with_suffix(".json.tmp")
        tmp2.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp2.replace(report_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
