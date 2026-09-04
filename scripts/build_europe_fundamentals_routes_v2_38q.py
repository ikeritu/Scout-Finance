#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/europe_fundamentals_route_contract_v1.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38q_europe_fundamentals_routes"
PHASE = "v2.38Q-europe-fundamentals-route-foundation"

ROUTES = {
    "XLON": ("GB", "official_filing_registry", "uk_companies_house_filings", "provider_api_required", "FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW", "COMPANY_REGISTRY_ID", "MEDIUM"),
    "XMAD": ("ES", "official_filing_registry", "cnmv_issuer_filings", "provider_api_required", "FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW", "ISIN", "MEDIUM"),
    "XDUB": ("IE", "manual_review", "issuer_filings_manual_review", "provider_api_required", "FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED", "UNKNOWN_REVIEW", "LOW"),
}
PROVIDER_MICS = {
    "XETR": ("DE", "F"), "XPAR": ("FR", "PA"), "XAMS": ("NL", "AS"), "XBRU": ("BE", "BR"),
    "XLIS": ("PT", "LS"), "MTAA": ("IT", "MI"), "XSWX": ("CH", "SW"), "XSTO": ("SE", "ST"),
    "XCSE": ("DK", "CO"), "XHEL": ("FI", "HE"), "XOSL": ("NO", "OL"), "XWBO": ("AT", "VI"),
}
for mic, (country, suffix) in PROVIDER_MICS.items():
    ROUTES[mic] = (country, "provider_api", "eodhd_fundamentals", "issuer_filings_review", "FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT", "PROVIDER_SYMBOL", "HIGH")

ASSET_FIELDS = [
    "asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country", "home_currency",
    "source_type", "primary_fundamental_route", "secondary_fundamental_route", "fundamental_route_status",
    "expected_identifier", "provider_symbol_candidate", "filing_registry_candidate", "route_confidence",
    "blocker_reason", "phase", "network_calls", "fundamentals_downloaded", "fundamentals_normalized",
    "scoring_calculated", "ranking_calculated", "recommendations_generated", "phase9c_authorized",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def provider_symbol(ticker: str, mic: str) -> str:
    suffix = PROVIDER_MICS.get(mic, ("", ""))[1]
    clean = ticker.strip().upper().replace(" ", "").replace("/", "-")
    return f"{clean}.{suffix}" if clean and suffix else ""


def build(input_resolution: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rows = read_csv(input_resolution)
    assets: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    for row in rows:
        status = row.get("resolution_status", "")
        mic = row.get("home_mic", "").strip().upper()
        if row.get("exchange") == "CBOE_EUROPE" or row.get("home_exchange") == "CBOE_EUROPE" or mic.startswith("CBOE"):
            review.append({"asset_id": row.get("asset_id", ""), "ticker": row.get("ticker", ""), "company_name": row.get("company_name", ""), "home_exchange": row.get("home_exchange", ""), "home_mic": mic, "home_country": row.get("home_country", ""), "home_currency": row.get("home_currency", ""), "source_type": "blocked", "fundamental_route_status": "FUNDAMENTALS_ROUTE_REJECTED_CBOE_SOURCE", "blocker_reason": "cboe_europe_source_forbidden", "phase": PHASE, "network_calls": "0", "fundamentals_downloaded": "false", "fundamentals_normalized": "false", "scoring_calculated": "false", "ranking_calculated": "false", "recommendations_generated": "false", "phase9c_authorized": "false"})
            continue
        if status != "HOME_EXCHANGE_RESOLVED":
            review.append({"asset_id": row.get("asset_id", ""), "ticker": row.get("ticker", ""), "company_name": row.get("company_name", ""), "home_exchange": row.get("home_exchange", ""), "home_mic": mic, "home_country": row.get("home_country", ""), "home_currency": row.get("home_currency", ""), "source_type": "blocked", "fundamental_route_status": "FUNDAMENTALS_ROUTE_BLOCKED_HOME_EXCHANGE_REQUIRED", "blocker_reason": "home_exchange_resolution_required_before_fundamentals_route", "phase": PHASE, "network_calls": "0", "fundamentals_downloaded": "false", "fundamentals_normalized": "false", "scoring_calculated": "false", "ranking_calculated": "false", "recommendations_generated": "false", "phase9c_authorized": "false"})
            continue
        country, source_type, primary, secondary, route_status, expected_id, confidence = ROUTES.get(mic, ("", "blocked", "provider_or_official_registry_required", "manual_route_definition_required", "FUNDAMENTALS_ROUTE_BLOCKED_PROVIDER_REQUIRED", "UNKNOWN_REVIEW", "NONE"))
        out = {field: "" for field in ASSET_FIELDS}
        out.update({
            "asset_id": row.get("asset_id", ""), "ticker": row.get("ticker", ""), "company_name": row.get("company_name", ""),
            "home_exchange": row.get("home_exchange", ""), "home_mic": mic, "home_country": row.get("home_country", "") or country,
            "home_currency": row.get("home_currency", ""), "source_type": source_type, "primary_fundamental_route": primary,
            "secondary_fundamental_route": secondary, "fundamental_route_status": route_status, "expected_identifier": expected_id,
            "provider_symbol_candidate": provider_symbol(row.get("ticker", ""), mic) if source_type == "provider_api" else "",
            "filing_registry_candidate": f"{primary}:{row.get('ticker', '').strip().upper()}" if source_type == "official_filing_registry" else "",
            "route_confidence": confidence, "blocker_reason": "" if source_type != "blocked" else "no_reliable_fundamentals_route_defined_for_home_mic",
            "phase": PHASE, "network_calls": "0", "fundamentals_downloaded": "false", "fundamentals_normalized": "false",
            "scoring_calculated": "false", "ranking_calculated": "false", "recommendations_generated": "false", "phase9c_authorized": "false",
        })
        assets.append(out)

    country_summary = []
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in assets:
        groups[(row["home_country"], row["home_mic"], row["fundamental_route_status"])].append(row)
    for (country, mic, status), grouped in sorted(groups.items()):
        country_summary.append({"home_country": country, "home_mic": mic, "fundamental_route_status": status, "assets": str(len(grouped))})
    batch_plan = [{"batch_id": f"EUFUND38Q-{idx:03d}", "fundamental_route_status": status, "home_mic": mic, "assets": str(len(grouped)), "network_allowed": "false", "phase9c_authorized": "false"} for idx, ((_, mic, status), grouped) in enumerate(sorted(groups.items()), start=1)]
    counts = Counter(row["fundamental_route_status"] for row in assets)
    report = {
        "phase": PHASE, "status": contract["final_status"], "input_assets": len(rows), "routed_assets": len(assets),
        "route_ready_provider_pilot": counts["FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT"],
        "route_ready_official_filings_review": counts["FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW"],
        "route_manual_review_required": counts["FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED"],
        "raw_cache_published": False, "guardrails": contract["guardrails"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_fundamentals_asset_routes_v2_38q.csv", assets, ASSET_FIELDS)
    write_csv(output_dir / "europe_fundamentals_route_review_v2_38q.csv", review, list(review[0].keys()) if review else ["asset_id"])
    write_csv(output_dir / "europe_fundamentals_country_summary_v2_38q.csv", country_summary, ["home_country", "home_mic", "fundamental_route_status", "assets"])
    write_csv(output_dir / "europe_fundamentals_batch_plan_v2_38q.csv", batch_plan, ["batch_id", "fundamental_route_status", "home_mic", "assets", "network_allowed", "phase9c_authorized"])
    write_csv(output_dir / "europe_fundamentals_route_matrix_v2_38q.csv", [{"home_mic": mic, "home_country": data[0], "source_type": data[1], "primary_fundamental_route": data[2], "fundamental_route_status": data[4]} for mic, data in sorted(ROUTES.items())], ["home_mic", "home_country", "source_type", "primary_fundamental_route", "fundamental_route_status"])
    (output_dir / "europe_fundamentals_aggregate_report_v2_38q.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text("# v2.38Q Europe fundamentals route foundation\n\nRoutes only; no network, fundamentals, scoring, ranking or recommendations.\n", encoding="utf-8")
    (output_dir / "EUROPE_FUNDAMENTALS_ROUTE_CONTRACT_v2_38q.md").write_text("# Europe Fundamentals Route Contract v2.38Q\n\nOffline route foundation only.\n", encoding="utf-8")
    (output_dir / "PHASE9Q_EUROPE_FUNDAMENTALS_GATE_v2_38q.md").write_text(f"# Phase 9Q Europe Fundamentals Gate\n\nDecision: {contract['final_status']}\n\nProvider pilot: {report['route_ready_provider_pilot']}\nOfficial review: {report['route_ready_official_filings_review']}\nManual review: {report['route_manual_review_required']}\n", encoding="utf-8")
    manifest = {"phase": PHASE, "inputs": {str(input_resolution): {"sha256": sha(input_resolution)}}, "outputs": {}, "guardrails": contract["guardrails"]}
    for path in sorted(output_dir.glob("*")):
        if path.name != "europe_fundamentals_manifest_v2_38q.json":
            manifest["outputs"][path.name] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    (output_dir / "europe_fundamentals_manifest_v2_38q.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-resolution", type=Path, default=ROOT / contract["input_resolution"])
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.input_resolution, args.output_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
