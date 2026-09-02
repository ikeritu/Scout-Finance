#!/usr/bin/env python3
"""Build deterministic v2.38I US price history acquisition plan."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_price_history_acquisition_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38i_us_price_history_acquisition"
PLAN_FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "priority_bucket",
    "fundamental_feature_status", "provider_symbol", "acquisition_status",
    "reason", "local_price_path", "expected_min_rows", "adjusted_prices_required",
]
LEDGER_FIELDS = [
    "batch_id", "run_utc", "provider", "requested", "selected", "collected",
    "skipped_existing", "failed", "status", "phase9c_authorized",
    "scoring_calculated", "ranking_calculated", "recommendations_generated",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def provider_symbol(ticker: str) -> str:
    return ticker.strip().upper()


def priority(status: str) -> tuple[int, str]:
    if status == "FEATURES_READY":
        return 1, "FEATURES_READY"
    if status == "FEATURES_PARTIAL":
        return 2, "FEATURES_PARTIAL"
    return 3, "SEC_READY_OTHER"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build(features_path: Path, output_dir: Path, raw_cache: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rows = read_csv(features_path)
    seen: set[str] = set()
    plan_rows: list[dict[str, str]] = []
    for row in rows:
        asset_id = row.get("asset_id", "")
        if not asset_id or asset_id in seen:
            continue
        seen.add(asset_id)
        ticker = row.get("ticker", "").strip()
        status = row.get("feature_quality_status", "")
        order, bucket = priority(status)
        symbol = provider_symbol(ticker)
        local_path = raw_cache / f"{asset_id}.csv"
        if not symbol:
            acquisition_status = "BLOCKED_MISSING_SYMBOL"
            reason = "missing_ticker"
        elif local_path.exists():
            acquisition_status = "LOCAL_PRICE_READY"
            reason = "local_price_history_exists"
        else:
            acquisition_status = "PENDING_COLLECTION"
            reason = "awaiting_local_price_history"
        plan_rows.append({
            "_order": str(order),
            "asset_id": asset_id,
            "ticker": ticker,
            "company_name": row.get("company_name", ""),
            "exchange": row.get("exchange", ""),
            "priority_bucket": bucket,
            "fundamental_feature_status": status,
            "provider_symbol": symbol,
            "acquisition_status": acquisition_status,
            "reason": reason,
            "local_price_path": rel(local_path),
            "expected_min_rows": str(contract["default_expected_min_rows"]),
            "adjusted_prices_required": "true",
        })
    plan_rows.sort(key=lambda r: (int(r["_order"]), r["ticker"], r["asset_id"]))
    public_rows = [{k: v for k, v in row.items() if k != "_order"} for row in plan_rows]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "us_price_history_acquisition_plan_v2_38i.csv", public_rows, PLAN_FIELDS)
    ledger = output_dir / "us_price_history_batch_ledger_v2_38i.csv"
    if not ledger.exists():
        write_csv(ledger, [], LEDGER_FIELDS)
    counts = Counter(row["acquisition_status"] for row in public_rows)
    buckets = Counter(row["priority_bucket"] for row in public_rows)
    collection_status = "READY_FOR_COLLECTION" if counts["PENDING_COLLECTION"] else "NO_PENDING_COLLECTION"
    report = {
        "phase": "v2.38I-us-price-history-acquisition",
        "collection_status": collection_status,
        "candidates_total": len(public_rows),
        "ready_priority": buckets["FEATURES_READY"],
        "partial_priority": buckets["FEATURES_PARTIAL"],
        "provider": "twelvedata",
        "pending_assets": counts["PENDING_COLLECTION"],
        "collected_assets": counts["LOCAL_PRICE_READY"],
        "failed_assets": counts["COLLECTION_FAILED"],
        "skipped_existing": counts["LOCAL_PRICE_READY"],
        "local_raw_cache_published": False,
        "guardrails": {
            "phase9c_authorized": False,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
        },
    }
    (output_dir / "us_price_history_collection_report_v2_38i.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "README.md").write_text("# v2.38I US price history acquisition\n\nBuilds a deterministic acquisition plan and controlled runner for US daily price histories. Raw price history stays local and ignored. No scoring, ranking or recommendations.\n", encoding="utf-8", newline="\n")
    (output_dir / "US_PRICE_HISTORY_ACQUISITION_CONTRACT_v2_38i.md").write_text("# US Price History Acquisition Contract v2.38I\n\nThis phase plans and controls acquisition of US price history for future price features. It does not authorize scoring, ranking, recommendations, predictions, phase 9C, broker actions or trading.\n", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9I US Price History Acquisition Gate v2.38I

Decision: {report['collection_status']}

- Candidates total: {report['candidates_total']}
- FEATURES_READY priority: {report['ready_priority']}
- FEATURES_PARTIAL priority: {report['partial_priority']}
- Pending assets: {report['pending_assets']}
- Local price ready: {report['collected_assets']}
- Provider: {report['provider']}
- Local raw cache published: false

This phase does not calculate scores, rankings, recommendations, predictions, broker actions, trading or phase 9C signals.
"""
    (output_dir / "PHASE9I_US_PRICE_HISTORY_GATE_v2_38i.md").write_text(gate, encoding="utf-8", newline="\n")
    manifest = {
        "phase": "v2.38I-us-price-history-acquisition",
        "decision": report["collection_status"],
        "inputs": {
            rel(features_path): {"bytes": features_path.stat().st_size if features_path.exists() else 0, "sha256": sha256(features_path) if features_path.exists() else ""}
        },
        "outputs": {},
        "raw_cache": rel(raw_cache),
        "guardrails": report["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.is_file() and path.name != "us_price_history_manifest_v2_38i.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (output_dir / "us_price_history_manifest_v2_38i.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--features-path", type=Path, default=ROOT / contract["input_sec_features"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--raw-cache", type=Path, default=ROOT / contract["raw_cache"])
    args = parser.parse_args()
    report = build(args.features_path, args.output_dir, args.raw_cache)
    print(json.dumps({
        "status": report["collection_status"],
        "candidates_total": report["candidates_total"],
        "pending_assets": report["pending_assets"],
        "collected_assets": report["collected_assets"],
        "recommendations_generated": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
