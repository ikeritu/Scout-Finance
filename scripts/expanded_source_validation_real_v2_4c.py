from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.4C"
METHOD = "expanded_source_validation_real_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "expanded_source_validation_real_v2_4c.json"
OUT_MD = OUT_DIR / "expanded_source_validation_real_v2_4c.md"
OUT_DUPLICATES_CSV = OUT_DIR / "expanded_source_validation_duplicates_v2_4c.csv"
OUT_ISSUES_CSV = OUT_DIR / "expanded_source_validation_issues_v2_4c.csv"

BUILDER_JSON = OUT_DIR / "expanded_source_builder_real_v2_4b.json"
EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_4b.csv"
EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_4b.csv"

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
TARGET_FIRST_EXPANSION_ROWS = 15000

REQUIRED_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "country",
    "source_provider",
    "source_file",
    "instrument_type",
    "instrument_scope",
    "classification_confidence",
    "classification_reason",
]

OPTIONAL_COLUMNS = [
    "sector",
    "industry",
    "market_cap",
    "raw_exchange_code",
    "raw_etf_flag",
    "raw_test_issue_flag",
]

ALLOWED_SCOPES = {
    "IN_SCOPE",
    "IN_SCOPE_ADR",
}

ALLOWED_INSTRUMENT_TYPES = {
    "COMMON_STOCK",
    "ADR",
}

ALLOWED_CONFIDENCE = {
    "HIGH",
    "MEDIUM",
    "LOW",
}


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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    builder = read_json(BUILDER_JSON)

    if not builder.get("_exists"):
        blockers.append(f"Missing v2.4B builder artifact: {rel(BUILDER_JSON)}")
        builder_status = None
    else:
        builder_status = builder.get("builder_status")
        positives.append(f"v2.4B builder artifact found: {rel(BUILDER_JSON)}")

    if builder_status in {
        "EXPANDED_SOURCE_BUILD_FULL_READY",
        "EXPANDED_SOURCE_BUILD_PARTIAL_READY",
        "EXPANDED_SOURCE_BUILD_PARTIAL_BELOW_TARGET_WITH_WARNINGS",
    }:
        positives.append(f"v2.4B builder status usable: {builder_status}")
    else:
        blockers.append(f"v2.4B builder status is not usable: {builder_status}")

    if not EXPANDED_CSV.exists():
        blockers.append(f"Missing expanded source CSV: {rel(EXPANDED_CSV)}")
        columns = []
        rows = []
    else:
        try:
            columns, rows = read_csv_rows(EXPANDED_CSV)
            positives.append(f"Expanded source CSV readable: {rel(EXPANDED_CSV)}")
        except Exception as exc:
            blockers.append(f"Could not read expanded source CSV: {exc}")
            columns = []
            rows = []

    exclusions_rows = []
    if EXCLUSIONS_CSV.exists():
        try:
            _, exclusions_rows = read_csv_rows(EXCLUSIONS_CSV)
            positives.append(f"Exclusions CSV readable: {rel(EXCLUSIONS_CSV)}")
        except Exception as exc:
            warnings.append(f"Could not read exclusions CSV: {exc}")
    else:
        warnings.append(f"Exclusions CSV not found: {rel(EXCLUSIONS_CSV)}")

    missing_required_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    missing_optional_columns = [column for column in OPTIONAL_COLUMNS if column not in columns]

    if missing_required_columns:
        blockers.append(f"Missing required columns: {', '.join(missing_required_columns)}")
    else:
        positives.append("All required canonical columns are present.")

    if missing_optional_columns:
        warnings.append(f"Missing optional columns: {', '.join(missing_optional_columns)}")
    else:
        positives.append("All optional canonical columns are present.")

    issues: list[dict[str, object]] = []
    duplicate_rows: list[dict[str, object]] = []

    ticker_empty = 0
    company_empty = 0
    exchange_empty = 0
    country_empty = 0
    invalid_scope = 0
    invalid_instrument_type = 0
    invalid_confidence = 0

    key_counter: Counter[tuple[str, str]] = Counter()

    for index, row in enumerate(rows, start=1):
        ticker = (row.get("ticker") or "").strip().upper()
        exchange = (row.get("exchange") or "").strip()
        company_name = (row.get("company_name") or "").strip()
        country = (row.get("country") or "").strip()
        instrument_scope = (row.get("instrument_scope") or "").strip()
        instrument_type = (row.get("instrument_type") or "").strip()
        confidence = (row.get("classification_confidence") or "").strip()

        if not ticker:
            ticker_empty += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_TICKER", "ticker": ticker, "exchange": exchange})
        if not company_name:
            company_empty += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_COMPANY_NAME", "ticker": ticker, "exchange": exchange})
        if not exchange:
            exchange_empty += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_EXCHANGE", "ticker": ticker, "exchange": exchange})
        if not country:
            country_empty += 1
            issues.append({"row_number": index, "issue_type": "EMPTY_COUNTRY", "ticker": ticker, "exchange": exchange})
        if instrument_scope not in ALLOWED_SCOPES:
            invalid_scope += 1
            issues.append({"row_number": index, "issue_type": "INVALID_SCOPE", "ticker": ticker, "exchange": exchange})
        if instrument_type not in ALLOWED_INSTRUMENT_TYPES:
            invalid_instrument_type += 1
            issues.append({"row_number": index, "issue_type": "INVALID_INSTRUMENT_TYPE", "ticker": ticker, "exchange": exchange})
        if confidence not in ALLOWED_CONFIDENCE:
            invalid_confidence += 1
            issues.append({"row_number": index, "issue_type": "INVALID_CONFIDENCE", "ticker": ticker, "exchange": exchange})

        if ticker and exchange:
            key_counter[(exchange, ticker)] += 1

    duplicate_keys = {key: count for key, count in key_counter.items() if count > 1}

    if duplicate_keys:
        for (exchange, ticker), count in duplicate_keys.items():
            duplicate_rows.append(
                {
                    "exchange": exchange,
                    "ticker": ticker,
                    "duplicate_count": count,
                }
            )

    if ticker_empty:
        blockers.append(f"Empty ticker values detected: {ticker_empty}")
    else:
        positives.append("No empty ticker values detected.")

    if exchange_empty:
        blockers.append(f"Empty exchange values detected: {exchange_empty}")
    else:
        positives.append("No empty exchange values detected.")

    if country_empty:
        blockers.append(f"Empty country values detected: {country_empty}")
    else:
        positives.append("No empty country values detected.")

    if company_empty:
        warnings.append(f"Empty company names detected: {company_empty}")
    else:
        positives.append("No empty company names detected.")

    if duplicate_keys:
        blockers.append(f"Duplicate exchange+ticker keys detected: {len(duplicate_keys)}")
    else:
        positives.append("No duplicate exchange+ticker keys detected.")

    if invalid_scope:
        blockers.append(f"Invalid instrument_scope values detected: {invalid_scope}")
    else:
        positives.append("All instrument_scope values are valid.")

    if invalid_instrument_type:
        blockers.append(f"Invalid instrument_type values detected: {invalid_instrument_type}")
    else:
        positives.append("All instrument_type values are valid.")

    if invalid_confidence:
        warnings.append(f"Invalid classification_confidence values detected: {invalid_confidence}")
    else:
        positives.append("All classification_confidence values are valid.")

    row_count = len(rows)
    exclusions_count = len(exclusions_rows)

    exchange_counts = Counter((row.get("exchange") or "").strip() for row in rows)
    provider_counts = Counter((row.get("source_provider") or "").strip() for row in rows)
    scope_counts = Counter((row.get("instrument_scope") or "").strip() for row in rows)
    type_counts = Counter((row.get("instrument_type") or "").strip() for row in rows)

    if row_count >= MIN_FULL_SOURCE_ROWS:
        positives.append(f"Expanded source meets full-source threshold: {row_count} >= {MIN_FULL_SOURCE_ROWS}")
        full_source_gate = "FULL_SOURCE_ROW_THRESHOLD_MET"
    elif row_count >= TARGET_FIRST_EXPANSION_ROWS:
        warnings.append(
            f"Expanded source meets first expansion target but not full-source threshold: "
            f"{row_count} >= {TARGET_FIRST_EXPANSION_ROWS}, < {MIN_FULL_SOURCE_ROWS}"
        )
        full_source_gate = "FIRST_EXPANSION_TARGET_MET_FULL_SOURCE_BLOCKED"
    else:
        warnings.append(f"Expanded source below first expansion target: {row_count} < {TARGET_FIRST_EXPANSION_ROWS}")
        warnings.append(f"Expanded source below full-source threshold: {row_count} < {MIN_FULL_SOURCE_ROWS}")
        full_source_gate = "FULL_SOURCE_BLOCKED_BELOW_FIRST_EXPANSION_TARGET"

    if blockers:
        validation_status = "EXPANDED_SOURCE_REAL_VALIDATION_BLOCKED"
        readiness_score = 0
    elif row_count >= MIN_FULL_SOURCE_ROWS and not warnings:
        validation_status = "EXPANDED_SOURCE_REAL_VALIDATION_FULL_READY"
        readiness_score = 100
    elif row_count >= TARGET_FIRST_EXPANSION_ROWS:
        validation_status = "EXPANDED_SOURCE_REAL_VALIDATION_PARTIAL_READY_WITH_WARNINGS"
        readiness_score = 85
    else:
        validation_status = "EXPANDED_SOURCE_REAL_VALIDATION_PARTIAL_BELOW_TARGET_WITH_WARNINGS"
        readiness_score = 70

    write_csv(
        OUT_DUPLICATES_CSV,
        duplicate_rows,
        ["exchange", "ticker", "duplicate_count"],
    )

    write_csv(
        OUT_ISSUES_CSV,
        issues,
        ["row_number", "issue_type", "ticker", "exchange"],
    )

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "full_source_gate": full_source_gate,
        "builder_input": {
            "path": rel(BUILDER_JSON),
            "exists": builder.get("_exists"),
            "builder_status": builder_status,
        },
        "inputs": {
            "expanded_source_csv": rel(EXPANDED_CSV),
            "exclusions_csv": rel(EXCLUSIONS_CSV),
        },
        "outputs": {
            "duplicates_csv": rel(OUT_DUPLICATES_CSV),
            "issues_csv": rel(OUT_ISSUES_CSV),
        },
        "targets": {
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
        },
        "summary": {
            "row_count": row_count,
            "exclusions_count": exclusions_count,
            "column_count": len(columns),
            "missing_required_columns": missing_required_columns,
            "missing_optional_columns": missing_optional_columns,
            "empty_tickers": ticker_empty,
            "empty_company_names": company_empty,
            "empty_exchanges": exchange_empty,
            "empty_countries": country_empty,
            "duplicate_exchange_ticker_keys": len(duplicate_keys),
            "invalid_scope_values": invalid_scope,
            "invalid_instrument_type_values": invalid_instrument_type,
            "invalid_confidence_values": invalid_confidence,
            "exchange_counts": dict(exchange_counts),
            "provider_counts": dict(provider_counts),
            "scope_counts": dict(scope_counts),
            "type_counts": dict(type_counts),
        },
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
            "active_outputs_overwritten": False,
        },
        "recommendation": (
            "Expanded source is structurally valid but does not unlock full 59k. Repeat v2.2C/v2.2E only as partial expanded-source validation."
            if not blockers
            else "Resolve blockers before using expanded source in downstream validation."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.4C Expanded Source Validation Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Full source gate: **{full_source_gate}**")
    md.append(f"- Row count: {row_count}")
    md.append(f"- Exclusions count: {exclusions_count}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full source rows: {MIN_FULL_SOURCE_ROWS}")
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
    md.append("- Active outputs overwritten: false")
    md.append("")
    md.append("## Schema validation")
    md.append("")
    md.append(f"- Missing required columns: {missing_required_columns}")
    md.append(f"- Missing optional columns: {missing_optional_columns}")
    md.append(f"- Empty tickers: {ticker_empty}")
    md.append(f"- Empty company names: {company_empty}")
    md.append(f"- Empty exchanges: {exchange_empty}")
    md.append(f"- Empty countries: {country_empty}")
    md.append(f"- Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    md.append(f"- Invalid scope values: {invalid_scope}")
    md.append(f"- Invalid instrument type values: {invalid_instrument_type}")
    md.append(f"- Invalid confidence values: {invalid_confidence}")
    md.append("")
    md.append("## Exchange counts")
    md.append("")
    for exchange, count in exchange_counts.most_common():
        md.append(f"- {exchange}: {count}")
    md.append("")
    md.append("## Provider counts")
    md.append("")
    for provider, count in provider_counts.most_common():
        md.append(f"- {provider}: {count}")
    md.append("")
    md.append("## Scope counts")
    md.append("")
    for scope, count in scope_counts.most_common():
        md.append(f"- {scope}: {count}")
    md.append("")
    md.append("## Type counts")
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
    md.append("Important: v2.4C validates the isolated expanded source only. It does not execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.4C Expanded Source Validation Real")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Full source gate: {full_source_gate}")
    print(f"OK   Row count: {row_count}")
    print(f"OK   Exclusions count: {exclusions_count}")
    print(f"OK   Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    print(f"OK   Missing required columns: {len(missing_required_columns)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Duplicates CSV written: {OUT_DUPLICATES_CSV}")
    print(f"OK   Issues CSV written: {OUT_ISSUES_CSV}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Network download performed: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
