from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.4B"
METHOD = "expanded_source_builder_real_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "expanded_source_builder_real_v2_4b.json"
OUT_MD = OUT_DIR / "expanded_source_builder_real_v2_4b.md"
OUT_BREAKDOWN_CSV = OUT_DIR / "expanded_source_builder_real_breakdown_v2_4b.csv"

EXPANDED_SOURCE_DIR = ROOT / "data" / "raw" / "expanded_universe"
OUT_EXPANDED_CSV = EXPANDED_SOURCE_DIR / "expanded_universe_v2_4b.csv"
OUT_EXCLUSION_CSV = EXPANDED_SOURCE_DIR / "expanded_universe_exclusions_v2_4b.csv"

ACQUISITION_JSON = OUT_DIR / "provider_source_acquisition_v2_4a.json"

PROVIDERS = [
    {
        "provider_id": "nasdaq_trader_nasdaqlisted",
        "source_file": ROOT / "data" / "raw" / "source_providers" / "nasdaq_trader_nasdaqlisted" / "nasdaq_trader_nasdaqlisted.csv",
        "provider_name": "NASDAQ Trader ? nasdaqlisted",
        "default_exchange": "NASDAQ",
        "country": "USA",
        "ticker_column": "Symbol",
        "name_column": "Security Name",
        "exchange_column": None,
        "etf_column": "ETF",
        "test_issue_column": "Test Issue",
    },
    {
        "provider_id": "nasdaq_trader_otherlisted",
        "source_file": ROOT / "data" / "raw" / "source_providers" / "nasdaq_trader_otherlisted" / "nasdaq_trader_otherlisted.csv",
        "provider_name": "NASDAQ Trader ? otherlisted",
        "default_exchange": "",
        "country": "USA",
        "ticker_column": "ACT Symbol",
        "name_column": "Security Name",
        "exchange_column": "Exchange",
        "etf_column": "ETF",
        "test_issue_column": "Test Issue",
    },
]

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
TARGET_FIRST_EXPANSION_ROWS = 15000

EXCHANGE_MAP = {
    "A": "NYSE American",
    "N": "NYSE",
    "P": "NYSE Arca",
    "Z": "Cboe BZX",
    "V": "IEX",
}

CANONICAL_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "country",
    "sector",
    "industry",
    "market_cap",
    "source_provider",
    "source_file",
    "instrument_type",
    "instrument_scope",
    "classification_confidence",
    "classification_reason",
    "raw_exchange_code",
    "raw_etf_flag",
    "raw_test_issue_flag",
]


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


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_ticker(value: str) -> str:
    return (value or "").strip().upper()


def normalize_exchange(provider: dict, row: dict[str, str]) -> tuple[str, str]:
    exchange_column = provider.get("exchange_column")
    raw_code = ""

    if exchange_column:
        raw_code = (row.get(exchange_column) or "").strip()
        return EXCHANGE_MAP.get(raw_code, raw_code or "UNKNOWN"), raw_code

    return provider["default_exchange"], provider["default_exchange"]


def classify_instrument(name: str, etf_flag: str, test_issue_flag: str) -> tuple[str, str, str, str]:
    upper_name = (name or "").upper()
    etf = (etf_flag or "").strip().upper()
    test_issue = (test_issue_flag or "").strip().upper()

    if test_issue == "Y":
        return "TEST_ISSUE", "OUT_OF_SCOPE", "HIGH", "Test issue flag is Y."

    if etf == "Y":
        return "ETF", "OUT_OF_SCOPE", "HIGH", "ETF flag is Y."

    exclusion_keywords = [
        ("WARRANT", "WARRANT"),
        ("RIGHT", "RIGHT"),
        (" UNIT", "UNIT"),
        ("UNITS", "UNIT"),
        ("PREFERRED", "PREFERRED"),
        (" PFD", "PREFERRED"),
        ("DEPOSITARY SHARES", "PREFERRED_OR_ADR_REVIEW"),
        ("NOTE DUE", "DEBT"),
        ("NOTES DUE", "DEBT"),
        ("BOND", "DEBT"),
    ]

    for keyword, instrument_type in exclusion_keywords:
        if keyword in upper_name:
            if instrument_type == "PREFERRED_OR_ADR_REVIEW":
                return "ADR_OR_PREFERRED_REVIEW", "OUT_OF_SCOPE", "MEDIUM", f"Security name contains review keyword: {keyword.strip()}."
            return instrument_type, "OUT_OF_SCOPE", "HIGH", f"Security name contains exclusion keyword: {keyword.strip()}."

    adr_keywords = [
        "AMERICAN DEPOSITARY",
        "AMERICAN DEPOSITORY",
        "ADS",
        "ADR",
    ]

    for keyword in adr_keywords:
        if keyword in upper_name:
            return "ADR", "IN_SCOPE_ADR", "MEDIUM", f"Security name indicates ADR/ADS: {keyword}."

    common_keywords = [
        "COMMON STOCK",
        "ORDINARY SHARES",
        "CLASS A",
        "CLASS B",
        "CLASS C",
    ]

    for keyword in common_keywords:
        if keyword in upper_name:
            return "COMMON_STOCK", "IN_SCOPE", "HIGH", f"Security name indicates common equity: {keyword}."

    return "COMMON_STOCK", "IN_SCOPE", "MEDIUM", "No exclusion keyword detected; treated as common equity candidate."


def build_provider_rows(provider: dict) -> tuple[list[dict[str, object]], list[dict[str, object]], dict]:
    source_file = provider["source_file"]

    summary = {
        "provider_id": provider["provider_id"],
        "source_file": rel(source_file),
        "exists": source_file.exists(),
        "readable": False,
        "raw_rows": 0,
        "included_rows": 0,
        "excluded_rows": 0,
        "duplicate_rows_removed": 0,
        "blockers": [],
        "warnings": [],
        "positives": [],
    }

    included: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []

    if not source_file.exists():
        summary["blockers"].append("Provider source file does not exist.")
        return included, excluded, summary

    try:
        columns, rows = read_csv_rows(source_file)
        summary["readable"] = True
        summary["raw_rows"] = len(rows)
        summary["positives"].append("Provider source file readable.")
    except Exception as exc:
        summary["blockers"].append(f"Could not read provider source file: {exc}")
        return included, excluded, summary

    required_columns = [provider["ticker_column"], provider["name_column"]]

    for required in required_columns:
        if required not in columns:
            summary["blockers"].append(f"Missing required column: {required}")

    if summary["blockers"]:
        return included, excluded, summary

    seen_keys: set[tuple[str, str]] = set()

    for index, row in enumerate(rows, start=1):
        ticker = normalize_ticker(row.get(provider["ticker_column"], ""))
        company_name = (row.get(provider["name_column"]) or "").strip()
        exchange, raw_exchange_code = normalize_exchange(provider, row)
        etf_flag = (row.get(provider["etf_column"]) or "").strip()
        test_issue_flag = (row.get(provider["test_issue_column"]) or "").strip()

        instrument_type, instrument_scope, confidence, reason = classify_instrument(company_name, etf_flag, test_issue_flag)

        base = {
            "ticker": ticker,
            "company_name": company_name,
            "exchange": exchange,
            "country": provider["country"],
            "sector": "",
            "industry": "",
            "market_cap": "",
            "source_provider": provider["provider_id"],
            "source_file": rel(source_file),
            "instrument_type": instrument_type,
            "instrument_scope": instrument_scope,
            "classification_confidence": confidence,
            "classification_reason": reason,
            "raw_exchange_code": raw_exchange_code,
            "raw_etf_flag": etf_flag,
            "raw_test_issue_flag": test_issue_flag,
        }

        if not ticker:
            base["instrument_type"] = "MALFORMED"
            base["instrument_scope"] = "OUT_OF_SCOPE"
            base["classification_confidence"] = "HIGH"
            base["classification_reason"] = "Missing ticker."
            excluded.append(base)
            continue

        dedupe_key = (exchange, ticker)

        if dedupe_key in seen_keys:
            summary["duplicate_rows_removed"] += 1
            base["instrument_type"] = "DUPLICATE"
            base["instrument_scope"] = "OUT_OF_SCOPE"
            base["classification_confidence"] = "HIGH"
            base["classification_reason"] = "Duplicate exchange+ticker within provider build."
            excluded.append(base)
            continue

        seen_keys.add(dedupe_key)

        if instrument_scope.startswith("IN_SCOPE"):
            included.append(base)
        else:
            excluded.append(base)

    summary["included_rows"] = len(included)
    summary["excluded_rows"] = len(excluded)

    return included, excluded, summary


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EXPANDED_SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    acquisition = read_json(ACQUISITION_JSON)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    if not acquisition.get("_exists"):
        blockers.append(f"Missing v2.4A acquisition artifact: {rel(ACQUISITION_JSON)}")
        acquisition_status = None
    else:
        acquisition_status = acquisition.get("acquisition_status")
        positives.append(f"v2.4A acquisition artifact found: {rel(ACQUISITION_JSON)}")

    if acquisition_status in {"PROVIDER_SOURCE_ACQUISITION_COMPLETED", "PROVIDER_SOURCE_ACQUISITION_COMPLETED_WITH_WARNINGS"}:
        positives.append(f"v2.4A acquisition status usable: {acquisition_status}")
    else:
        blockers.append(f"v2.4A acquisition status is not usable: {acquisition_status}")

    all_included: list[dict[str, object]] = []
    all_excluded: list[dict[str, object]] = []
    provider_summaries: list[dict] = []

    for provider in PROVIDERS:
        included, excluded, summary = build_provider_rows(provider)
        all_included.extend(included)
        all_excluded.extend(excluded)
        provider_summaries.append(summary)

        for item in summary["blockers"]:
            blockers.append(f"{summary['provider_id']}: {item}")
        for item in summary["warnings"]:
            warnings.append(f"{summary['provider_id']}: {item}")
        for item in summary["positives"]:
            positives.append(f"{summary['provider_id']}: {item}")

    global_seen: set[tuple[str, str]] = set()
    deduped_included: list[dict[str, object]] = []
    global_duplicate_exclusions: list[dict[str, object]] = []

    for row in all_included:
        key = (str(row["exchange"]), str(row["ticker"]))

        if key in global_seen:
            duplicate = dict(row)
            duplicate["instrument_type"] = "GLOBAL_DUPLICATE"
            duplicate["instrument_scope"] = "OUT_OF_SCOPE"
            duplicate["classification_confidence"] = "HIGH"
            duplicate["classification_reason"] = "Duplicate exchange+ticker across provider build."
            global_duplicate_exclusions.append(duplicate)
            continue

        global_seen.add(key)
        deduped_included.append(row)

    all_excluded.extend(global_duplicate_exclusions)

    exchange_counts = Counter(str(row["exchange"]) for row in deduped_included)
    scope_counts = Counter(str(row["instrument_scope"]) for row in deduped_included)
    type_counts = Counter(str(row["instrument_type"]) for row in deduped_included)

    included_rows = len(deduped_included)
    excluded_rows = len(all_excluded)

    if included_rows >= TARGET_FIRST_EXPANSION_ROWS:
        positives.append(f"Expanded universe meets first expansion target: {included_rows} >= {TARGET_FIRST_EXPANSION_ROWS}")
    else:
        warnings.append(f"Expanded universe below first expansion target: {included_rows} < {TARGET_FIRST_EXPANSION_ROWS}")

    if included_rows >= MIN_FULL_SOURCE_ROWS:
        positives.append(f"Expanded universe meets full-source threshold: {included_rows} >= {MIN_FULL_SOURCE_ROWS}")
    else:
        warnings.append(f"Expanded universe below full-source threshold: {included_rows} < {MIN_FULL_SOURCE_ROWS}")

    if not blockers:
        write_csv(OUT_EXPANDED_CSV, deduped_included, CANONICAL_COLUMNS)
        write_csv(OUT_EXCLUSION_CSV, all_excluded, CANONICAL_COLUMNS)

    if blockers:
        builder_status = "EXPANDED_SOURCE_BUILD_BLOCKED"
        readiness_score = 0
    elif included_rows >= MIN_FULL_SOURCE_ROWS and not warnings:
        builder_status = "EXPANDED_SOURCE_BUILD_FULL_READY"
        readiness_score = 100
    elif included_rows >= TARGET_FIRST_EXPANSION_ROWS:
        builder_status = "EXPANDED_SOURCE_BUILD_PARTIAL_READY"
        readiness_score = 85
    else:
        builder_status = "EXPANDED_SOURCE_BUILD_PARTIAL_BELOW_TARGET_WITH_WARNINGS"
        readiness_score = 70

    breakdown_rows = []

    for summary in provider_summaries:
        breakdown_rows.append(
            {
                "provider_id": summary["provider_id"],
                "source_file": summary["source_file"],
                "exists": summary["exists"],
                "readable": summary["readable"],
                "raw_rows": summary["raw_rows"],
                "included_rows": summary["included_rows"],
                "excluded_rows": summary["excluded_rows"],
                "duplicate_rows_removed": summary["duplicate_rows_removed"],
                "blockers": " | ".join(summary["blockers"]),
                "warnings": " | ".join(summary["warnings"]),
            }
        )

    write_csv(
        OUT_BREAKDOWN_CSV,
        breakdown_rows,
        [
            "provider_id",
            "source_file",
            "exists",
            "readable",
            "raw_rows",
            "included_rows",
            "excluded_rows",
            "duplicate_rows_removed",
            "blockers",
            "warnings",
        ],
    )

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "builder_status": builder_status,
        "readiness_score": readiness_score,
        "acquisition_input": {
            "path": rel(ACQUISITION_JSON),
            "exists": acquisition.get("_exists"),
            "acquisition_status": acquisition_status,
        },
        "targets": {
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
        },
        "outputs": {
            "expanded_source_csv": rel(OUT_EXPANDED_CSV),
            "exclusion_csv": rel(OUT_EXCLUSION_CSV),
            "breakdown_csv": rel(OUT_BREAKDOWN_CSV),
        },
        "summary": {
            "provider_count": len(PROVIDERS),
            "raw_rows": sum(int(s["raw_rows"]) for s in provider_summaries),
            "included_rows": included_rows,
            "excluded_rows": excluded_rows,
            "global_duplicate_exclusions": len(global_duplicate_exclusions),
            "exchange_counts": dict(exchange_counts),
            "instrument_scope_counts": dict(scope_counts),
            "instrument_type_counts": dict(type_counts),
        },
        "provider_summaries": provider_summaries,
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
            "expanded_source_written": bool(not blockers),
            "active_outputs_overwritten": False,
        },
        "recommendation": (
            "Proceed to v2.4C expanded source validation real. Do not run scoring or full 59k."
            if not blockers
            else "Resolve blockers before validating expanded source."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.4B Expanded Source Builder Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Builder status: **{builder_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Raw rows: {payload['summary']['raw_rows']}")
    md.append(f"- Included rows: {included_rows}")
    md.append(f"- Excluded rows: {excluded_rows}")
    md.append(f"- Global duplicate exclusions: {len(global_duplicate_exclusions)}")
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
    md.append("- Expanded source written: true" if not blockers else "- Expanded source written: false")
    md.append("- Active outputs overwritten: false")
    md.append("")
    md.append("## Outputs")
    md.append("")
    for key, value in payload["outputs"].items():
        md.append(f"- {key}: `{value}`")
    md.append("")
    md.append("## Provider summaries")
    md.append("")
    for summary in provider_summaries:
        md.append(f"### {summary['provider_id']}")
        md.append("")
        md.append(f"- Raw rows: {summary['raw_rows']}")
        md.append(f"- Included rows: {summary['included_rows']}")
        md.append(f"- Excluded rows: {summary['excluded_rows']}")
        md.append(f"- Duplicate rows removed: {summary['duplicate_rows_removed']}")
        md.append("")
    md.append("## Exchange counts")
    md.append("")
    for exchange, count in exchange_counts.most_common():
        md.append(f"- {exchange}: {count}")
    md.append("")
    md.append("## Instrument scope counts")
    md.append("")
    for scope, count in scope_counts.most_common():
        md.append(f"- {scope}: {count}")
    md.append("")
    md.append("## Instrument type counts")
    md.append("")
    for instrument_type, count in type_counts.most_common():
        md.append(f"- {instrument_type}: {count}")
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
    md.append("Important: v2.4B builds an isolated expanded source only. It does not execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.4B Expanded Source Builder Real")
    print("=" * 92)
    print(f"OK   Builder status: {builder_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Raw rows: {payload['summary']['raw_rows']}")
    print(f"OK   Included rows: {included_rows}")
    print(f"OK   Excluded rows: {excluded_rows}")
    print(f"OK   Global duplicate exclusions: {len(global_duplicate_exclusions)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Expanded CSV written: {OUT_EXPANDED_CSV}")
    print(f"OK   Exclusion CSV written: {OUT_EXCLUSION_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Network download performed: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
