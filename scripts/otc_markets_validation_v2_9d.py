from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.9D"
METHOD = "otc_markets_validation_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

ACQUISITION_JSON = OUT_DIR / "otc_markets_acquisition_real_v2_9c.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

PROVIDER_ID = "otc_markets_stock_screener"
RAW_CSV = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID / "otc_markets_stock_screener_raw.csv"

OUT_JSON = OUT_DIR / "otc_markets_validation_v2_9d.json"
OUT_MD = OUT_DIR / "otc_markets_validation_v2_9d.md"
NORMALIZED_CANDIDATE_CSV = OUT_DIR / "otc_markets_normalized_candidate_v2_9d.csv"
NET_NEW_CANDIDATE_CSV = OUT_DIR / "otc_markets_net_new_candidates_v2_9d.csv"
DUPLICATES_CSV = OUT_DIR / "otc_markets_duplicates_v2_9d.csv"
ISSUES_CSV = OUT_DIR / "otc_markets_issues_v2_9d.csv"

CURRENT_EXPANDED_ROWS = 9200
CURRENT_EXCLUSIONS_ROWS = 10056
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000
ROWS_NEEDED_FIRST_EXPANSION = 5800
ROWS_NEEDED_FULL_SOURCE = 40800

EXPECTED_FIELDS = [
    "Symbol",
    "Security Name",
    "Tier",
    "Price",
    "Change %",
    "Vol",
    "Sec Type",
    "Country",
    "State",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fieldnames(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def first_existing_field(fields: list[str], candidates: list[str]) -> str:
    lowered = {f.lower().strip(): f for f in fields}
    for candidate in candidates:
        hit = lowered.get(candidate.lower().strip())
        if hit:
            return hit
    return ""


def clean(value: Any) -> str:
    return str(value or "").strip()


def normalize_symbol(value: str) -> str:
    return clean(value).upper()


def normalize_exchange(value: str) -> str:
    value = clean(value).upper()
    return value or "OTC"


def detect_expanded_fields(fields: list[str]) -> dict[str, str]:
    return {
        "ticker": first_existing_field(fields, ["ticker", "symbol", "Symbol", "Ticker"]),
        "exchange": first_existing_field(fields, ["exchange", "Exchange", "market", "Market"]),
        "company_name": first_existing_field(fields, ["company_name", "companyName", "name", "Name", "Security Name", "security_name"]),
        "source_provider": first_existing_field(fields, ["source_provider", "sourceProvider", "provider"]),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []
    issues: list[dict[str, str]] = []

    acquisition = read_json(ACQUISITION_JSON)

    if not acquisition.get("_exists"):
        blockers.append(f"Missing v2.9C acquisition artifact: {rel(ACQUISITION_JSON)}")
    else:
        positives.append(f"v2.9C acquisition artifact found: {rel(ACQUISITION_JSON)}")

    acquisition_status = acquisition.get("acquisition_status")
    acquisition_decision = acquisition.get("acquisition_decision")

    if acquisition_status == "OTC_MARKETS_ACQUISITION_COMPLETED":
        positives.append(f"v2.9C acquisition status accepted: {acquisition_status}")
    else:
        blockers.append(f"Unexpected v2.9C acquisition status: {acquisition_status}")

    if acquisition_decision == "OTC_MARKETS_RAW_SOURCE_READY_FOR_VALIDATION":
        positives.append(f"v2.9C acquisition decision accepted: {acquisition_decision}")
    else:
        blockers.append(f"Unexpected v2.9C acquisition decision: {acquisition_decision}")

    for path in [RAW_CSV, CURRENT_EXPANDED_CSV, CURRENT_EXCLUSIONS_CSV]:
        if path.exists():
            positives.append(f"Validation input available: {rel(path)}")
        else:
            blockers.append(f"Missing validation input: {rel(path)}")

    raw_fields = fieldnames(RAW_CSV)
    raw_rows = read_csv_dicts(RAW_CSV)

    missing_expected_fields = [field for field in EXPECTED_FIELDS if field not in raw_fields]
    if missing_expected_fields:
        blockers.append(f"Missing expected OTC fields: {missing_expected_fields}")
    else:
        positives.append("Expected OTC schema fields detected.")

    symbol_field = first_existing_field(raw_fields, ["Symbol", "symbol", "Ticker", "ticker"])
    name_field = first_existing_field(raw_fields, ["Security Name", "security name", "Company Name", "company name", "Name", "name"])
    tier_field = first_existing_field(raw_fields, ["Tier", "tier", "Market Tier", "market tier"])
    sec_type_field = first_existing_field(raw_fields, ["Sec Type", "Security Type", "Type", "Instrument Type"])
    country_field = first_existing_field(raw_fields, ["Country", "country"])
    state_field = first_existing_field(raw_fields, ["State", "state"])

    if not symbol_field:
        blockers.append("No usable OTC symbol field detected.")
    else:
        positives.append(f"OTC symbol field detected: {symbol_field}")

    if not name_field:
        warnings.append("No OTC security/company name field detected.")
    else:
        positives.append(f"OTC security name field detected: {name_field}")

    if not tier_field:
        warnings.append("No OTC tier field detected.")
    else:
        positives.append(f"OTC tier field detected: {tier_field}")

    if not sec_type_field:
        warnings.append("No OTC security type field detected.")
    else:
        positives.append(f"OTC security type field detected: {sec_type_field}")

    expanded_fields = fieldnames(CURRENT_EXPANDED_CSV)
    expanded_detection = detect_expanded_fields(expanded_fields)

    if not expanded_detection["ticker"]:
        blockers.append("Could not detect ticker field in current expanded universe.")
    if not expanded_detection["exchange"]:
        blockers.append("Could not detect exchange field in current expanded universe.")

    expanded_rows = read_csv_dicts(CURRENT_EXPANDED_CSV)

    existing_keys: set[tuple[str, str]] = set()
    for row in expanded_rows:
        exchange = normalize_exchange(row.get(expanded_detection["exchange"], ""))
        ticker = normalize_symbol(row.get(expanded_detection["ticker"], ""))
        if exchange and ticker:
            existing_keys.add((exchange, ticker))

    normalized_rows: list[dict[str, str]] = []

    for idx, row in enumerate(raw_rows, start=1):
        ticker = normalize_symbol(row.get(symbol_field, ""))
        company_name = clean(row.get(name_field, ""))
        tier = clean(row.get(tier_field, ""))
        sec_type = clean(row.get(sec_type_field, ""))
        country = clean(row.get(country_field, ""))
        state = clean(row.get(state_field, ""))

        if not ticker:
            issues.append({
                "severity": "ERROR",
                "issue_type": "EMPTY_SYMBOL",
                "detail": f"Raw row {idx} has empty Symbol.",
            })
            continue

        classification_reason = (
            f"OTC Markets candidate row from stock screener. "
            f"Tier={tier or 'UNKNOWN'}; Sec Type={sec_type or 'UNKNOWN'}; "
            f"Country={country or 'UNKNOWN'}; State={state or 'UNKNOWN'}."
        )

        normalized_rows.append({
            "exchange": "OTC",
            "ticker": ticker,
            "company_name": company_name,
            "country": country,
            "instrument_type": sec_type or "UNKNOWN_OTC_SECURITY_TYPE",
            "instrument_scope": "OTC_MARKETS_CANDIDATE_PROVIDER_ROW_PENDING_POST_REBUILD_VALIDATION",
            "source_provider": PROVIDER_ID,
            "source_phase": PHASE,
            "source_tier": tier,
            "source_state": state,
            "classification_confidence": "LOW",
            "classification_reason": classification_reason,
        })

    key_counts = Counter((row["exchange"], row["ticker"]) for row in normalized_rows)
    duplicate_keys = {key: count for key, count in key_counts.items() if count > 1}

    net_new_rows = [
        row for row in normalized_rows
        if (row["exchange"], row["ticker"]) not in existing_keys
    ]

    overlap_rows = len(normalized_rows) - len(net_new_rows)

    tier_counts = Counter(row.get("source_tier", "") or "UNKNOWN" for row in normalized_rows)
    sec_type_counts = Counter(row.get("instrument_type", "") or "UNKNOWN" for row in normalized_rows)
    country_counts = Counter(row.get("country", "") or "UNKNOWN" for row in normalized_rows)

    if duplicate_keys:
        warnings.append(f"Duplicate OTC exchange+ticker keys detected: {len(duplicate_keys)}")

    if len(raw_rows) < ROWS_NEEDED_FIRST_EXPANSION:
        warnings.append(f"OTC route is insufficient for first expansion: {len(raw_rows)} raw rows < {ROWS_NEEDED_FIRST_EXPANSION} rows needed.")

    if len(net_new_rows) < ROWS_NEEDED_FIRST_EXPANSION:
        warnings.append(f"OTC net-new rows are insufficient for first expansion: {len(net_new_rows)} < {ROWS_NEEDED_FIRST_EXPANSION} rows needed.")

    if len(net_new_rows) == 0:
        warnings.append("OTC produced zero net-new rows against current expanded universe.")

    if issues:
        warnings.append(f"Validation issues detected: {len(issues)}")

    normalized_fields = [
        "exchange",
        "ticker",
        "company_name",
        "country",
        "instrument_type",
        "instrument_scope",
        "source_provider",
        "source_phase",
        "source_tier",
        "source_state",
        "classification_confidence",
        "classification_reason",
    ]

    with NORMALIZED_CANDIDATE_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=normalized_fields)
        writer.writeheader()
        writer.writerows(normalized_rows)

    with NET_NEW_CANDIDATE_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=normalized_fields)
        writer.writeheader()
        writer.writerows(net_new_rows)

    with DUPLICATES_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["exchange", "ticker", "duplicate_count"])
        writer.writeheader()
        for (exchange, ticker), count in sorted(duplicate_keys.items()):
            writer.writerow({
                "exchange": exchange,
                "ticker": ticker,
                "duplicate_count": count,
            })

    with ISSUES_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["severity", "issue_type", "detail"])
        writer.writeheader()
        writer.writerows(issues)

    projected_rows_if_rebuilt = CURRENT_EXPANDED_ROWS + len(net_new_rows)
    first_expansion_unlocked_if_rebuilt = projected_rows_if_rebuilt >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked_if_rebuilt = projected_rows_if_rebuilt >= MIN_FULL_SOURCE_ROWS

    if blockers:
        validation_status = "OTC_MARKETS_VALIDATION_BLOCKED"
        readiness_score = 0
        validation_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    elif len(net_new_rows) >= ROWS_NEEDED_FIRST_EXPANSION:
        validation_status = "OTC_MARKETS_VALIDATED_FOR_REBUILD"
        readiness_score = 88
        validation_decision = "OTC_MARKETS_USABLE_FOR_ISOLATED_REBUILD"
        recommended_next_phase = "v2.9E ? Rebuild Expanded Source With OTC Markets"
    else:
        validation_status = "OTC_MARKETS_VALIDATED_INSUFFICIENT_FOR_EXPANSION"
        readiness_score = 82
        validation_decision = "OTC_MARKETS_VALID_BUT_NOT_ENOUGH_REFERENCE_OR_ENRICHMENT_ONLY"
        recommended_next_phase = "v2.9G ? OTC Markets Closure Report OR v2.10A next provider route"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "validation_decision": validation_decision,
        "recommended_next_phase": recommended_next_phase,
        "provider": {
            "provider_id": PROVIDER_ID,
            "raw_csv": rel(RAW_CSV),
        },
        "schema": {
            "raw_fields": raw_fields,
            "expected_fields": EXPECTED_FIELDS,
            "missing_expected_fields": missing_expected_fields,
            "detected_fields": {
                "symbol_field": symbol_field,
                "name_field": name_field,
                "tier_field": tier_field,
                "sec_type_field": sec_type_field,
                "country_field": country_field,
                "state_field": state_field,
            },
            "expanded_detection": expanded_detection,
        },
        "row_summary": {
            "raw_rows": len(raw_rows),
            "normalized_candidate_rows": len(normalized_rows),
            "net_new_candidate_rows": len(net_new_rows),
            "overlap_rows": overlap_rows,
            "duplicate_exchange_ticker_keys": len(duplicate_keys),
            "issues_count": len(issues),
        },
        "distribution": {
            "tier_counts": dict(tier_counts),
            "sec_type_counts": dict(sec_type_counts),
            "country_counts": dict(country_counts),
        },
        "threshold_status": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "projected_rows_if_rebuilt": projected_rows_if_rebuilt,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion_before_otc": ROWS_NEEDED_FIRST_EXPANSION,
            "rows_needed_full_source_before_otc": ROWS_NEEDED_FULL_SOURCE,
            "first_expansion_unlocked_if_rebuilt": first_expansion_unlocked_if_rebuilt,
            "full_source_unlocked_if_rebuilt": full_source_unlocked_if_rebuilt,
            "rows_still_needed_first_expansion_after_otc": max(0, TARGET_FIRST_EXPANSION_ROWS - projected_rows_if_rebuilt),
            "rows_still_needed_full_source_after_otc": max(0, MIN_FULL_SOURCE_ROWS - projected_rows_if_rebuilt),
        },
        "outputs": {
            "normalized_candidate_csv": rel(NORMALIZED_CANDIDATE_CSV),
            "net_new_candidate_csv": rel(NET_NEW_CANDIDATE_CSV),
            "duplicates_csv": rel(DUPLICATES_CSV),
            "issues_csv": rel(ISSUES_CSV),
            "validation_json": rel(OUT_JSON),
            "validation_md": rel(OUT_MD),
        },
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "network_download_performed": False,
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "active_outputs_overwritten": False,
            "expanded_universe_rebuilt": False,
            "validation_only": True,
        },
        "recommendation": (
            "Do not rebuild. Close OTC route as valid schema/reference/enrichment but insufficient for expansion; proceed to next provider route."
            if not blockers and len(net_new_rows) < ROWS_NEEDED_FIRST_EXPANSION
            else "Proceed according to validation decision."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.9D OTC Markets Validation")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Validation decision: **{validation_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Provider")
    md.append("")
    md.append(f"- Provider ID: `{PROVIDER_ID}`")
    md.append(f"- Raw CSV: `{rel(RAW_CSV)}`")
    md.append("")
    md.append("## Schema")
    md.append("")
    md.append(f"- Raw fields: {', '.join(raw_fields)}")
    md.append(f"- Missing expected fields: {missing_expected_fields}")
    md.append(f"- Symbol field: `{symbol_field}`")
    md.append(f"- Name field: `{name_field}`")
    md.append(f"- Tier field: `{tier_field}`")
    md.append(f"- Security type field: `{sec_type_field}`")
    md.append(f"- Country field: `{country_field}`")
    md.append(f"- State field: `{state_field}`")
    md.append("")
    md.append("## Row summary")
    md.append("")
    md.append(f"- Raw rows: {len(raw_rows)}")
    md.append(f"- Normalized candidate rows: {len(normalized_rows)}")
    md.append(f"- Net-new candidate rows: {len(net_new_rows)}")
    md.append(f"- Overlap rows: {overlap_rows}")
    md.append(f"- Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    md.append(f"- Issues count: {len(issues)}")
    md.append("")
    md.append("## Distribution")
    md.append("")
    md.append(f"- Tier counts: {dict(tier_counts)}")
    md.append(f"- Security type counts: {dict(sec_type_counts)}")
    md.append(f"- Country counts: {dict(country_counts)}")
    md.append("")
    md.append("## Threshold status")
    md.append("")
    md.append(f"- Current expanded rows: {CURRENT_EXPANDED_ROWS}")
    md.append(f"- Projected rows if rebuilt: {projected_rows_if_rebuilt}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- First expansion unlocked if rebuilt: {first_expansion_unlocked_if_rebuilt}")
    md.append(f"- Full source unlocked if rebuilt: {full_source_unlocked_if_rebuilt}")
    md.append(f"- Rows still needed first expansion after OTC: {max(0, TARGET_FIRST_EXPANSION_ROWS - projected_rows_if_rebuilt)}")
    md.append(f"- Rows still needed full source after OTC: {max(0, MIN_FULL_SOURCE_ROWS - projected_rows_if_rebuilt)}")
    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Normalized candidate CSV: `{rel(NORMALIZED_CANDIDATE_CSV)}`")
    md.append(f"- Net-new candidate CSV: `{rel(NET_NEW_CANDIDATE_CSV)}`")
    md.append(f"- Duplicates CSV: `{rel(DUPLICATES_CSV)}`")
    md.append(f"- Issues CSV: `{rel(ISSUES_CSV)}`")
    md.append(f"- Validation JSON: `{rel(OUT_JSON)}`")
    md.append(f"- Validation report: `{rel(OUT_MD)}`")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- Network download performed: false")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded universe rebuilt: false")
    md.append("- Validation only: true")
    md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
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
    md.append("Important: v2.9D is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.9D OTC Markets Validation")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Validation decision: {validation_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Raw rows: {len(raw_rows)}")
    print(f"OK   Normalized candidate rows: {len(normalized_rows)}")
    print(f"OK   Net-new candidate rows: {len(net_new_rows)}")
    print(f"OK   Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    print(f"OK   Issues count: {len(issues)}")
    print(f"OK   Projected rows if rebuilt: {projected_rows_if_rebuilt}")
    print(f"OK   First expansion unlocked if rebuilt: {first_expansion_unlocked_if_rebuilt}")
    print(f"OK   Full source unlocked if rebuilt: {full_source_unlocked_if_rebuilt}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Normalized CSV written: {NORMALIZED_CANDIDATE_CSV}")
    print(f"OK   Net-new CSV written: {NET_NEW_CANDIDATE_CSV}")
    print(f"OK   Duplicates CSV written: {DUPLICATES_CSV}")
    print(f"OK   Issues CSV written: {ISSUES_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
