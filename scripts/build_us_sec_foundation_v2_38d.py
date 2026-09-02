#!/usr/bin/env python3
"""Build the v2.38D US SEC foundation artifacts without network calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/us_sec_foundation_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation"
OVERLAY_FIELDS = [
    "asset_id", "ticker", "exchange", "company_name", "cik", "sec_entity_name",
    "sic", "fiscal_year_end", "sec_ticker", "sec_exchange", "identity_status",
    "review_reason", "evidence_source", "evidence_hash", "phase",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_sec_cache(cache_dir: Path) -> dict[str, list[dict]]:
    source = cache_dir / "company_tickers_exchange.json"
    if not source.exists():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("data", [])
    fields = payload.get("fields", [])
    if not isinstance(rows, list) or "ticker" not in fields or "cik" not in fields:
        raise SystemExit("BLOCKED: SEC company_tickers_exchange schema changed")
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for item in rows:
        record = dict(zip(fields, item))
        ticker = str(record.get("ticker", "")).upper()
        if ticker:
            by_ticker[ticker].append(record)
    return by_ticker


def classify(row: dict[str, str], sec_by_ticker: dict[str, list[dict]]) -> dict[str, str]:
    base = {
        "asset_id": row["asset_id"],
        "ticker": row["ticker"],
        "exchange": row["exchange"],
        "company_name": row["company_name"],
        "cik": "",
        "sec_entity_name": "",
        "sic": "",
        "fiscal_year_end": "",
        "sec_ticker": "",
        "sec_exchange": "",
        "phase": "v2.38D",
    }
    if row["eligibility_status"] != "ELIGIBLE":
        status = "US_SEC_NOT_ELIGIBLE"
        reason = row["blocker_reason"] or "not eligible in v2.38C"
        source = "v2.38C US census"
    elif not sec_by_ticker:
        status = "US_SEC_SOURCE_UNAVAILABLE"
        reason = "SEC company_tickers_exchange cache unavailable; run pilot with --execute and SEC user-agent"
        source = "offline fail-closed"
    else:
        matches = sec_by_ticker.get(row["ticker"].upper(), [])
        if not matches:
            status = "US_SEC_CIK_MISSING"
            reason = "ticker not found in SEC company_tickers_exchange cache"
            source = "SEC company_tickers_exchange cache"
        elif len(matches) > 1:
            status = "US_SEC_TICKER_AMBIGUOUS"
            reason = "ticker has multiple SEC rows; manual exchange/entity review required"
            source = "SEC company_tickers_exchange cache"
        else:
            match = matches[0]
            cik = str(match.get("cik", "")).zfill(10)
            base.update({
                "cik": cik,
                "sec_entity_name": str(match.get("name", "")),
                "sec_ticker": str(match.get("ticker", "")),
                "sec_exchange": str(match.get("exchange", "")),
            })
            if not cik.isdigit() or len(cik) != 10:
                status = "US_SEC_CIK_MISSING"
                reason = "SEC CIK missing or malformed"
            elif row["exchange"] == "Cboe BZX":
                status = "US_SEC_MANUAL_REVIEW"
                reason = "Cboe BZX venue requires source confirmation before automatic SEC promotion"
            else:
                status = "US_SEC_CIK_RESOLVED"
                reason = ""
            source = "SEC company_tickers_exchange cache"
    base.update({
        "identity_status": status,
        "review_reason": reason,
        "evidence_source": source,
    })
    base["evidence_hash"] = row_hash(base["asset_id"], base["ticker"], base["exchange"], status, reason, source, base["cik"])
    return base


def select_pilot(us_rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    eligible = [r for r in us_rows if r["eligibility_status"] == "ELIGIBLE"]
    exchanges = ["NASDAQ", "NYSE", "NYSE American", "Cboe BZX", "CBOE", "NYSE Arca"]
    for exchange in exchanges:
        found = next((r for r in eligible if r["exchange"] == exchange and r not in selected), None)
        if found:
            selected.append(found)
    for row in eligible:
        if len(selected) >= limit:
            break
        if row not in selected:
            selected.append(row)
    return selected[:limit]


def build(cache_dir: Path, limit: int) -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    source = ROOT / contract["input_us_census"]
    with source.open(encoding="utf-8", newline="") as f:
        us_rows = list(csv.DictReader(f))
    if len(us_rows) != contract["expected_us_rows"]:
        raise SystemExit("BLOCKED: US census row count mismatch")
    if sum(r["eligibility_status"] == "ELIGIBLE" for r in us_rows) != contract["expected_us_eligible_rows"]:
        raise SystemExit("BLOCKED: US eligible row count mismatch")
    if not 1 <= limit <= contract["maximum_pilot_assets"]:
        raise SystemExit("BLOCKED: pilot limit must be 1..50")
    OUT.mkdir(parents=True, exist_ok=True)
    sec_by_ticker = load_sec_cache(cache_dir)
    overlay = [classify(row, sec_by_ticker) for row in us_rows]
    write_csv(OUT / "us_sec_identity_overlay_v2_38d.csv", overlay, OVERLAY_FIELDS)
    review = [r for r in overlay if r["identity_status"] != "US_SEC_CIK_RESOLVED"]
    write_csv(OUT / "us_sec_identity_review_v2_38d.csv", review, OVERLAY_FIELDS)
    pilot = select_pilot(us_rows, limit)
    write_csv(
        OUT / "us_sec_pilot_selection_v2_38d.csv",
        [{"asset_id": r["asset_id"], "ticker": r["ticker"], "exchange": r["exchange"], "company_name": r["company_name"], "selection_reason": "deterministic_exchange_balanced_not_ranked"} for r in pilot],
        ["asset_id", "ticker", "exchange", "company_name", "selection_reason"],
    )
    route_rows = [
        {"route": "identity", "source": "SEC company_tickers_exchange.json", "status": "CACHE_AVAILABLE" if sec_by_ticker else "DRY_RUN_SOURCE_UNAVAILABLE", "network_required": "true", "execute_required": "true", "output_policy": "overlay_only"},
        {"route": "filings", "source": "SEC submissions/CIK##########.json", "status": "PILOT_REQUIRED", "network_required": "true", "execute_required": "true", "output_policy": "aggregate_and_local_raw_cache"},
        {"route": "fundamentals", "source": "SEC companyfacts/CIK##########.json", "status": "PILOT_REQUIRED", "network_required": "true", "execute_required": "true", "output_policy": "aggregate_and_local_raw_cache"},
        {"route": "prices", "source": "external adjusted price provider", "status": "USER_ACTION_REQUIRED", "network_required": "true", "execute_required": "true", "output_policy": "not_collected_in_v2_38d"},
    ]
    write_csv(OUT / "us_sec_provider_route_matrix_v2_38d.csv", route_rows, ["route", "source", "status", "network_required", "execute_required", "output_policy"])
    counts = Counter(r["identity_status"] for r in overlay)
    report = {
        "phase": "v2.38D-us-sec-foundation",
        "status": "COMPLETED_US_SEC_FOUNDATION_DRY_RUN" if not sec_by_ticker else "COMPLETED_US_SEC_CACHE_FOUNDATION",
        "us_rows": len(us_rows),
        "us_eligible_rows": sum(r["eligibility_status"] == "ELIGIBLE" for r in us_rows),
        "pilot_selected_assets": len(pilot),
        "cik_resolved": counts["US_SEC_CIK_RESOLVED"],
        "submissions_available": 0,
        "companyfacts_available": 0,
        "publication_dates_available": 0,
        "identity_status_counts": dict(sorted(counts.items())),
        "failure_reasons": dict(sorted(Counter(r["review_reason"] for r in review if r["review_reason"]).items())),
        "guardrails": {
            "network_calls": 0,
            "credentials_used": False,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
        },
    }
    (OUT / "us_sec_pilot_aggregate_report_v2_38d.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    summary = {
        **report,
        "limitations": [
            "SEC cache is optional; without an executed pilot, CIKs remain fail-closed.",
            "Adjusted prices are not collected in v2.38D.",
            "No scoring, ranking or recommendation is produced.",
        ],
    }
    (OUT / "us_sec_coverage_summary_v2_38d.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (OUT / "US_SEC_FOUNDATION_CONTRACT_v2_38d.md").write_text("""# US SEC Foundation Contract v2.38D

This phase defines the US SEC identity and fundamentals foundation for Scout Finance.

Allowed SEC routes: company tickers exchange, submissions and companyfacts. Network execution is blocked by default and requires `--execute` plus `SCOUT_FINANCE_SEC_USER_AGENT`.

Forbidden outputs: scoring, ranking, recommendations, phase 9C, broker integration and trading.
""", encoding="utf-8", newline="\n")
    gate = f"""# Phase 9D US SEC Final Gate v2.38D

Decision: {report['status']}

- Global universe: 43,089
- Global eligible rows: 21,165
- US rows: {report['us_rows']}
- US eligible rows: {report['us_eligible_rows']}
- Pilot selected assets: {report['pilot_selected_assets']}
- CIK resolved: {report['cik_resolved']}
- Submissions available: {report['submissions_available']}
- Companyfacts available: {report['companyfacts_available']}
- Publication dates available: {report['publication_dates_available']}

This phase creates SEC routing infrastructure only. It does not calculate scoring, ranking, recommendations, phase 9C signals, broker actions or trading.
"""
    (OUT / "PHASE9D_US_SEC_FINAL_GATE_v2_38d.md").write_text(gate, encoding="utf-8", newline="\n")
    (OUT / "README.md").write_text("# v2.38D US SEC foundation\n\nOffline SEC identity/fundamental route foundation for US coverage.\n", encoding="utf-8", newline="\n")
    manifest = {
        "phase": "v2.38D-us-sec-foundation",
        "decision": report["status"],
        "input": {"path": contract["input_us_census"], "sha256": sha256(source), "rows": len(us_rows)},
        "outputs": {},
        "guardrails": report["guardrails"],
    }
    for path in sorted(OUT.glob("*")):
        if path.is_file() and path.name != "us_sec_manifest_v2_38d.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (OUT / "us_sec_manifest_v2_38d.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=OUT / "sec_raw_cache_v2_38d")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    report = build(args.cache_dir, args.limit)
    print(json.dumps({"status": report["status"], "us_rows": report["us_rows"], "us_eligible": report["us_eligible_rows"], "cik_resolved": report["cik_resolved"], "recommendations_generated": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
