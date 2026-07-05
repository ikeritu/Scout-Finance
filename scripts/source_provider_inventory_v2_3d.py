from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.3D"
METHOD = "source_provider_inventory_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "source_provider_inventory_v2_3d.json"
OUT_MD = OUT_DIR / "source_provider_inventory_v2_3d.md"
OUT_CSV = OUT_DIR / "source_provider_inventory_v2_3d.csv"

PLAN_V2_3C = OUT_DIR / "source_expansion_plan_v2_3c.json"

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
TARGET_FIRST_EXPANSION_ROWS = 15000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}

    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plan = read_json(PLAN_V2_3C)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    if not plan.get("_exists"):
        blockers.append(f"Missing required v2.3C plan artifact: {rel(PLAN_V2_3C)}")
        plan_status = None
    else:
        plan_status = plan.get("plan_status")
        positives.append(f"v2.3C plan found and readable: {rel(PLAN_V2_3C)}")

    if plan_status == "SOURCE_EXPANSION_PLAN_READY":
        positives.append("v2.3C confirms source expansion plan is ready.")
    else:
        blockers.append(f"v2.3C plan is not ready: {plan_status}")

    providers = [
        {
            "provider_id": "nasdaq_trader_nasdaqlisted",
            "provider_name": "NASDAQ Trader ? nasdaqlisted",
            "exchange": "NASDAQ",
            "country": "USA",
            "region": "North America",
            "priority": 1,
            "route": "PRIMARY_ROUTE",
            "source_type": "official_exchange_symbol_list",
            "acquisition_method": "manual_or_scripted_download_later",
            "network_download_now": False,
            "expected_columns": ["Symbol", "Security Name", "Market Category", "ETF", "Test Issue", "Financial Status", "Round Lot Size"],
            "canonical_mapping": {
                "Symbol": "ticker",
                "Security Name": "company_name",
                "NASDAQ": "exchange",
                "USA": "country",
            },
            "expected_contribution": "core_us_listings",
            "first_expansion_candidate": True,
            "risk": "LOW_MEDIUM",
            "notes": "Already aligned with current project source style; good first provider for reproducible expansion.",
        },
        {
            "provider_id": "nasdaq_trader_otherlisted",
            "provider_name": "NASDAQ Trader ? otherlisted",
            "exchange": "NYSE_AMEX_ARCA_CBOE_OTHER_US",
            "country": "USA",
            "region": "North America",
            "priority": 1,
            "route": "PRIMARY_ROUTE",
            "source_type": "official_exchange_symbol_list",
            "acquisition_method": "manual_or_scripted_download_later",
            "network_download_now": False,
            "expected_columns": ["ACT Symbol", "Security Name", "Exchange", "CQS Symbol", "ETF", "Round Lot Size", "Test Issue", "NASDAQ Symbol"],
            "canonical_mapping": {
                "ACT Symbol": "ticker",
                "Security Name": "company_name",
                "Exchange": "exchange",
                "USA": "country",
            },
            "expected_contribution": "expanded_us_listings",
            "first_expansion_candidate": True,
            "risk": "LOW_MEDIUM",
            "notes": "Likely best second source to expand beyond NASDAQ while keeping official US exchange provenance.",
        },
        {
            "provider_id": "nyse_listed_directory",
            "provider_name": "NYSE Listed Company Directory",
            "exchange": "NYSE",
            "country": "USA",
            "region": "North America",
            "priority": 2,
            "route": "SECONDARY_ROUTE",
            "source_type": "official_exchange_directory",
            "acquisition_method": "manual_download_or_export_later",
            "network_download_now": False,
            "expected_columns": ["ticker", "company_name", "exchange"],
            "canonical_mapping": {
                "ticker": "ticker",
                "company_name": "company_name",
                "NYSE": "exchange",
                "USA": "country",
            },
            "expected_contribution": "nyse_crosscheck",
            "first_expansion_candidate": True,
            "risk": "MEDIUM",
            "notes": "Useful for cross-checking and improving metadata; schema may require manual inspection.",
        },
        {
            "provider_id": "euronext_instruments",
            "provider_name": "Euronext Listed Instruments",
            "exchange": "Euronext",
            "country": "Multi-country Europe",
            "region": "Europe",
            "priority": 3,
            "route": "LATER_ROUTE",
            "source_type": "official_exchange_instrument_list",
            "acquisition_method": "manual_download_or_export_later",
            "network_download_now": False,
            "expected_columns": ["symbol", "name", "market", "isin", "currency"],
            "canonical_mapping": {
                "symbol": "ticker",
                "name": "company_name",
                "market": "exchange",
            },
            "expected_contribution": "european_expansion",
            "first_expansion_candidate": False,
            "risk": "HIGH",
            "notes": "Useful later; ticker collisions and ISIN handling should be planned first.",
        },
        {
            "provider_id": "lse_instruments",
            "provider_name": "London Stock Exchange Instruments",
            "exchange": "London Stock Exchange",
            "country": "United Kingdom",
            "region": "Europe",
            "priority": 3,
            "route": "LATER_ROUTE",
            "source_type": "official_exchange_instrument_list",
            "acquisition_method": "manual_download_or_export_later",
            "network_download_now": False,
            "expected_columns": ["ticker", "name", "market", "segment", "isin"],
            "canonical_mapping": {
                "ticker": "ticker",
                "name": "company_name",
                "market": "exchange",
                "United Kingdom": "country",
            },
            "expected_contribution": "uk_expansion",
            "first_expansion_candidate": False,
            "risk": "HIGH",
            "notes": "Add after US route is reproducible.",
        },
        {
            "provider_id": "xetra_frankfurt_instruments",
            "provider_name": "Deutsche B?rse / Xetra instruments",
            "exchange": "Xetra / Frankfurt",
            "country": "Germany",
            "region": "Europe",
            "priority": 3,
            "route": "LATER_ROUTE",
            "source_type": "official_exchange_instrument_list",
            "acquisition_method": "manual_download_or_export_later",
            "network_download_now": False,
            "expected_columns": ["ticker", "name", "isin", "market"],
            "canonical_mapping": {
                "ticker": "ticker",
                "name": "company_name",
                "market": "exchange",
                "Germany": "country",
            },
            "expected_contribution": "germany_expansion",
            "first_expansion_candidate": False,
            "risk": "HIGH",
            "notes": "Requires ISIN-aware deduplication.",
        },
        {
            "provider_id": "bme_instruments",
            "provider_name": "BME / Bolsa de Madrid instruments",
            "exchange": "BME",
            "country": "Spain",
            "region": "Europe",
            "priority": 3,
            "route": "LATER_ROUTE",
            "source_type": "official_exchange_instrument_list",
            "acquisition_method": "manual_download_or_export_later",
            "network_download_now": False,
            "expected_columns": ["ticker", "name", "market", "isin"],
            "canonical_mapping": {
                "ticker": "ticker",
                "name": "company_name",
                "market": "exchange",
                "Spain": "country",
            },
            "expected_contribution": "spain_expansion",
            "first_expansion_candidate": False,
            "risk": "HIGH",
            "notes": "Useful for later European coverage, not first expansion.",
        },
        {
            "provider_id": "jp_x_tse_instruments",
            "provider_name": "Japan Exchange Group / Tokyo Stock Exchange",
            "exchange": "Tokyo Stock Exchange",
            "country": "Japan",
            "region": "Asia-Pacific",
            "priority": 4,
            "route": "LATER_ROUTE",
            "source_type": "official_exchange_instrument_list",
            "acquisition_method": "manual_download_or_export_later",
            "network_download_now": False,
            "expected_columns": ["code", "name", "market", "sector"],
            "canonical_mapping": {
                "code": "ticker",
                "name": "company_name",
                "market": "exchange",
                "Japan": "country",
            },
            "expected_contribution": "asia_pacific_expansion",
            "first_expansion_candidate": False,
            "risk": "HIGH",
            "notes": "Later route; numeric tickers need canonical formatting rules.",
        },
    ]

    first_expansion_providers = [p for p in providers if p["first_expansion_candidate"]]
    primary_route_providers = [p for p in providers if p["route"] == "PRIMARY_ROUTE"]

    if len(primary_route_providers) >= 2:
        positives.append(f"Primary route providers defined: {len(primary_route_providers)}")
    else:
        blockers.append("Not enough primary route providers defined.")

    if len(first_expansion_providers) >= 2:
        positives.append(f"First expansion providers defined: {len(first_expansion_providers)}")
    else:
        warnings.append("First expansion provider list is small.")

    if blockers:
        inventory_status = "SOURCE_PROVIDER_INVENTORY_BLOCKED"
        readiness_score = 0
    elif warnings:
        inventory_status = "SOURCE_PROVIDER_INVENTORY_READY_WITH_WARNINGS"
        readiness_score = 85
    else:
        inventory_status = "SOURCE_PROVIDER_INVENTORY_READY"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "inventory_status": inventory_status,
        "readiness_score": readiness_score,
        "strategy": {
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
        },
        "plan_input": {
            "path": rel(PLAN_V2_3C),
            "exists": plan.get("_exists"),
            "plan_status": plan_status,
        },
        "provider_count": len(providers),
        "primary_route_provider_count": len(primary_route_providers),
        "first_expansion_provider_count": len(first_expansion_providers),
        "providers": providers,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "network_download_performed": False,
        },
        "recommendation": (
            "Proceed to v2.3E Expanded Source Builder Skeleton. Do not download data yet."
            if not blockers
            else "Resolve blockers before building source expansion skeleton."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_fields = [
        "provider_id",
        "provider_name",
        "exchange",
        "country",
        "region",
        "priority",
        "route",
        "source_type",
        "acquisition_method",
        "network_download_now",
        "expected_contribution",
        "first_expansion_candidate",
        "risk",
        "notes",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(providers)

    md: list[str] = []
    md.append("# Scout Finance ? v2.3D Source Provider Inventory")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Inventory status: **{inventory_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Provider count: {len(providers)}")
    md.append(f"- Primary route providers: {len(primary_route_providers)}")
    md.append(f"- First expansion providers: {len(first_expansion_providers)}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: false")
    md.append("")
    md.append("## Plan input")
    md.append("")
    md.append(f"- Path: `{rel(PLAN_V2_3C)}`")
    md.append(f"- Exists: {plan.get('_exists')}")
    md.append(f"- Plan status: {plan_status}")
    md.append("")
    md.append("## Providers")
    md.append("")
    for provider in providers:
        marker = " ? FIRST EXPANSION" if provider["first_expansion_candidate"] else ""
        md.append(f"### {provider['provider_id']}{marker}")
        md.append("")
        md.append(f"- Name: {provider['provider_name']}")
        md.append(f"- Exchange: {provider['exchange']}")
        md.append(f"- Country: {provider['country']}")
        md.append(f"- Region: {provider['region']}")
        md.append(f"- Priority: {provider['priority']}")
        md.append(f"- Route: {provider['route']}")
        md.append(f"- Source type: {provider['source_type']}")
        md.append(f"- Acquisition method: {provider['acquisition_method']}")
        md.append(f"- Network download now: {provider['network_download_now']}")
        md.append(f"- Risk: {provider['risk']}")
        md.append(f"- Notes: {provider['notes']}")
        md.append("")
    md.append("## Positives")
    md.append("")
    for item in positives:
        md.append(f"- {item}")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.3D is an inventory only. It does not download data, execute scoring, call OpenAI, call a broker, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.3D Source Provider Inventory")
    print("=" * 92)
    print(f"OK   Inventory status: {inventory_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Provider count: {len(providers)}")
    print(f"OK   Primary route providers: {len(primary_route_providers)}")
    print(f"OK   First expansion providers: {len(first_expansion_providers)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   CSV written: {OUT_CSV}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Network download performed: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
