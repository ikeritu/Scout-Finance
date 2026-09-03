#!/usr/bin/env python3
"""Build deterministic v2.38O Europe price-history acquisition plan."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_price_history_acquisition_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38o_europe_price_history_acquisition"
PHASE = "v2.38O-europe-price-history-acquisition"

PLAN_FIELDS = [
    "asset_id",
    "ticker",
    "company_name",
    "home_exchange",
    "home_mic",
    "home_country",
    "home_currency",
    "provider_route",
    "provider",
    "provider_symbol",
    "collection_status",
    "rows_collected",
    "first_date",
    "last_date",
    "raw_cache_path",
    "failure_reason",
    "phase",
    "scoring_calculated",
    "ranking_calculated",
    "recommendations_generated",
    "phase9c_authorized",
]
LEDGER_FIELDS = [
    "batch_id",
    "run_utc",
    "provider",
    "requested",
    "selected",
    "collected",
    "skipped_existing",
    "failed",
    "status",
    "phase9c_authorized",
    "scoring_calculated",
    "ranking_calculated",
    "recommendations_generated",
]
SUFFIX_BY_MIC = {
    "XETR": {"stooq": ".de", "twelvedata": ".DE", "yahoo_chart": ".DE", "eodhd": ".XETRA"},
    "XLON": {"stooq": ".uk", "twelvedata": ".L", "yahoo_chart": ".L", "eodhd": ".LSE"},
    "XPAR": {"stooq": ".fr", "twelvedata": ".PA", "yahoo_chart": ".PA", "eodhd": ".PA"},
    "XAMS": {"stooq": ".nl", "twelvedata": ".AS", "yahoo_chart": ".AS", "eodhd": ".AS"},
    "XBRU": {"stooq": ".be", "twelvedata": ".BR", "yahoo_chart": ".BR", "eodhd": ".BR"},
    "XLIS": {"stooq": ".pt", "twelvedata": ".LS", "yahoo_chart": ".LS", "eodhd": ".LS"},
    "XMAD": {"stooq": ".es", "twelvedata": ".MC", "yahoo_chart": ".MC", "eodhd": ".MC"},
    "MTAA": {"stooq": ".it", "twelvedata": ".MI", "yahoo_chart": ".MI", "eodhd": ".MI"},
    "XSWX": {"stooq": ".ch", "twelvedata": ".SW", "yahoo_chart": ".SW", "eodhd": ".SW"},
    "XSTO": {"stooq": ".se", "twelvedata": ".ST", "yahoo_chart": ".ST", "eodhd": ".ST"},
    "XCSE": {"stooq": ".dk", "twelvedata": ".CO", "yahoo_chart": ".CO", "eodhd": ".CO"},
    "XHEL": {"stooq": ".fi", "twelvedata": ".HE", "yahoo_chart": ".HE", "eodhd": ".HE"},
    "XOSL": {"stooq": ".no", "twelvedata": ".OL", "yahoo_chart": ".OL", "eodhd": ".OL"},
    "XDUB": {"stooq": ".ie", "twelvedata": ".IR", "yahoo_chart": ".IR", "eodhd": ".IR"},
    "XWBO": {"stooq": ".at", "twelvedata": ".VI", "yahoo_chart": ".VI", "eodhd": ".VI"},
}


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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def provider_for(row: dict[str, str], preferred: str | None = None) -> str:
    if preferred:
        return preferred
    route = row.get("provider_route", "")
    if route == "stooq_daily_prices":
        return "stooq"
    if route == "eodhd_europe_prices":
        return "eodhd"
    if route == "yahoo_chart_prices":
        return "yahoo_chart"
    return "twelvedata"


def provider_symbol(ticker: str, home_mic: str, provider: str) -> str:
    clean = ticker.strip().upper()
    if not clean or not home_mic:
        return ""
    suffix = SUFFIX_BY_MIC.get(home_mic, {}).get(provider, "")
    if provider == "stooq":
        return f"{clean}{suffix}".lower()
    return f"{clean}{suffix}"


def cache_stats(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        return "0", "", ""
    rows = read_csv(path)
    dates = sorted(r.get("date", "") for r in rows if r.get("date"))
    return str(len(rows)), (dates[0] if dates else ""), (dates[-1] if dates else "")


def build(resolution_path: Path, output_dir: Path, raw_cache: Path, preferred_provider: str | None = None) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    supported = set(contract["supported_providers"])
    if preferred_provider and preferred_provider not in supported:
        raise SystemExit("BLOCKED: provider_not_supported")
    rows = read_csv(resolution_path)
    plan_rows: list[dict[str, str]] = []
    for row in rows:
        if row.get("resolution_status") != "HOME_EXCHANGE_RESOLVED":
            continue
        if row.get("exchange") == "CBOE_EUROPE" or row.get("listing_role") == "SECONDARY_CBOE_EUROPE":
            continue
        provider = provider_for(row, preferred_provider)
        symbol = provider_symbol(row.get("ticker", ""), row.get("home_mic", ""), provider)
        local_path = raw_cache / f"{row.get('asset_id', '')}.csv"
        rows_collected, first_date, last_date = cache_stats(local_path)
        if provider not in supported:
            status, reason = "BLOCKED_PROVIDER_UNSUPPORTED", "provider_route_not_supported"
        elif not symbol:
            status, reason = "BLOCKED_PROVIDER_ERROR", "missing_ticker_or_home_mic"
        elif local_path.exists() and int(rows_collected or "0") >= int(contract["expected_min_rows"]):
            status, reason = "COLLECTED", ""
        elif local_path.exists():
            status, reason = "BLOCKED_INSUFFICIENT_HISTORY", "local_cache_below_expected_min_rows"
        else:
            status, reason = "READY_FOR_COLLECTION", ""
        plan_rows.append({
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "home_exchange": row.get("home_exchange", ""),
            "home_mic": row.get("home_mic", ""),
            "home_country": row.get("home_country", ""),
            "home_currency": row.get("home_currency", ""),
            "provider_route": row.get("provider_route", ""),
            "provider": provider,
            "provider_symbol": symbol,
            "collection_status": status,
            "rows_collected": rows_collected,
            "first_date": first_date,
            "last_date": last_date,
            "raw_cache_path": rel(local_path),
            "failure_reason": reason,
            "phase": PHASE,
            "scoring_calculated": "false",
            "ranking_calculated": "false",
            "recommendations_generated": "false",
            "phase9c_authorized": "false",
        })
    plan_rows.sort(key=lambda r: (r["collection_status"] != "READY_FOR_COLLECTION", r["home_mic"], r["ticker"], r["asset_id"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_price_history_acquisition_plan_v2_38o.csv", plan_rows, PLAN_FIELDS)
    ledger = output_dir / "europe_price_history_batch_ledger_v2_38o.csv"
    if not ledger.exists():
        write_csv(ledger, [], LEDGER_FIELDS)
    counts = Counter(r["collection_status"] for r in plan_rows)
    status = "READY_FOR_COLLECTION" if counts["READY_FOR_COLLECTION"] else "NO_PENDING_COLLECTION"
    report = {
        "phase": PHASE,
        "collection_status": status,
        "candidates_total": len(plan_rows),
        "pending_assets": counts["READY_FOR_COLLECTION"],
        "collected_assets": counts["COLLECTED"],
        "blocked_provider_unsupported": counts["BLOCKED_PROVIDER_UNSUPPORTED"],
        "blocked_cboe_secondary_source": counts["BLOCKED_CBOE_SECONDARY_SOURCE"],
        "blocked_credential_missing": counts["BLOCKED_CREDENTIAL_MISSING"],
        "blocked_network_error": counts["BLOCKED_NETWORK_ERROR"],
        "blocked_provider_error": counts["BLOCKED_PROVIDER_ERROR"],
        "blocked_insufficient_history": counts["BLOCKED_INSUFFICIENT_HISTORY"],
        "skipped_existing": counts["COLLECTED"],
        "raw_cache_published": False,
        "guardrails": {
            "network_calls": 0,
            "cboe_europe_source_forbidden": True,
            "scoring_calculated": False,
            "ranking_calculated": False,
            "recommendations_generated": False,
            "phase9c_authorized": False,
            "financial_advice": False,
            "broker_actions_allowed": False,
        },
    }
    (output_dir / "europe_price_history_collection_report_v2_38o.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "README.md").write_text(
        "# v2.38O Europe price history acquisition\n\n"
        "Builds a deterministic Europe price-history acquisition plan from v2.38N home-exchange resolved assets. "
        "Raw price history stays local and ignored. Cboe Europe is not used as a primary source. "
        "No scoring, ranking, recommendations, broker actions or Phase 9C authorization are produced.\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "EUROPE_PRICE_HISTORY_ACQUISITION_CONTRACT_v2_38o.md").write_text(
        "# Europe Price History Acquisition Contract v2.38O\n\n"
        "- Input must be v2.38N `HOME_EXCHANGE_RESOLVED` records only.\n"
        "- Cboe Europe source usage as a primary venue is forbidden.\n"
        "- Runner is dry-run by default and requires `--execute` for network calls.\n"
        "- Raw cache is local and ignored.\n"
        "- No scoring, ranking, final recommendations, financial advice, broker actions or Phase 9C.\n",
        encoding="utf-8",
        newline="\n",
    )
    gate = f"""# Phase 9O Europe Price History Gate v2.38O

Decision: {report['collection_status']}

- Candidates total: {report['candidates_total']}
- Pending assets: {report['pending_assets']}
- Collected assets: {report['collected_assets']}
- Raw cache published: false
- Cboe Europe primary source: forbidden

This phase does not calculate features, scores, rankings, recommendations, predictions, broker actions or Phase 9C signals.
"""
    (output_dir / "PHASE9O_EUROPE_PRICE_HISTORY_GATE_v2_38o.md").write_text(gate, encoding="utf-8", newline="\n")
    manifest = {
        "phase": PHASE,
        "decision": report["collection_status"],
        "inputs": {
            rel(resolution_path): {
                "bytes": resolution_path.stat().st_size if resolution_path.exists() else 0,
                "sha256": sha256(resolution_path) if resolution_path.exists() else "",
            }
        },
        "outputs": {},
        "raw_cache": rel(raw_cache),
        "guardrails": report["guardrails"],
    }
    for path in sorted(output_dir.glob("*")):
        if path.is_file() and path.name != "europe_price_history_manifest_v2_38o.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (output_dir / "europe_price_history_manifest_v2_38o.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution-path", type=Path, default=ROOT / contract["input_resolution"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--raw-cache", type=Path, default=ROOT / contract["raw_cache"])
    parser.add_argument("--provider", choices=contract["supported_providers"])
    args = parser.parse_args()
    report = build(args.resolution_path, args.output_dir, args.raw_cache, args.provider)
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
