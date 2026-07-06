from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.7C"
METHOD = "validate_expanded_source_with_sec_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

REBUILD_JSON = OUT_DIR / "rebuild_expanded_source_with_sec_real_v2_7b.json"

EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"
EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_7b.csv"

PROVIDER_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_sec_provider_breakdown_v2_7b.csv"
MERGE_AUDIT_CSV = OUT_DIR / "rebuild_expanded_source_with_sec_merge_audit_v2_7b.csv"
EXCLUSION_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_sec_exclusion_breakdown_v2_7b.csv"

OUT_JSON = OUT_DIR / "validate_expanded_source_with_sec_v2_7c.json"
OUT_MD = OUT_DIR / "validate_expanded_source_with_sec_v2_7c.md"
OUT_PROVIDER_VALIDATION_CSV = OUT_DIR / "validate_expanded_source_with_sec_provider_validation_v2_7c.csv"
OUT_ISSUES_CSV = OUT_DIR / "validate_expanded_source_with_sec_issues_v2_7c.csv"
OUT_DUPLICATES_CSV = OUT_DIR / "validate_expanded_source_with_sec_duplicates_v2_7c.csv"

EXPECTED_EXPANDED_ROWS = 8007
EXPECTED_EXCLUSIONS_ROWS = 10056
EXPECTED_SEC_ADDED_ROWS = 2359

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

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
    "sector",
    "industry",
    "market_cap",
    "raw_cik",
    "raw_exchange",
    "provider_precedence",
    "merge_action",
    "merge_reason",
]

EXPECTED_PROVIDER_COUNTS = {
    "nasdaq_trader_nasdaqlisted": 3244,
    "nasdaq_trader_otherlisted": 2404,
    "sec_company_tickers_exchange": 2359,
}

ALLOWED_MERGE_ACTIONS = {
    "PRESERVE_EXISTING",
    "ADD_SEC_PRIMARY_NET_NEW",
}

ALLOWED_PROVIDER_PRECEDENCE = {"1", "2"}


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm_ticker(value: str) -> str:
    return (value or "").strip().upper()


def norm_exchange(value: str) -> str:
    return (value or "").strip()


def key_exchange_ticker(row: dict[str, str]) -> tuple[str, str]:
    return (norm_exchange(row.get("exchange", "")), norm_ticker(row.get("ticker", "")))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []
    issues: list[dict[str, str]] = []
    duplicate_rows: list[dict[str, str]] = []

    rebuild = read_json(REBUILD_JSON)

    if not rebuild.get("_exists"):
        blockers.append(f"Missing v2.7B rebuild artifact: {rel(REBUILD_JSON)}")
    else:
        positives.append(f"v2.7B rebuild artifact found: {rel(REBUILD_JSON)}")

    rebuild_status = rebuild.get("rebuild_status")
    if rebuild_status == "REBUILD_EXPANDED_SOURCE_WITH_SEC_COMPLETED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.7B rebuild status accepted: {rebuild_status}")
    else:
        blockers.append(f"Unexpected v2.7B rebuild status: {rebuild_status}")

    required_files = [
        EXPANDED_CSV,
        EXCLUSIONS_CSV,
        PROVIDER_BREAKDOWN_CSV,
        MERGE_AUDIT_CSV,
        EXCLUSION_BREAKDOWN_CSV,
    ]

    for path in required_files:
        if not path.exists():
            blockers.append(f"Missing required validation input: {rel(path)}")
        else:
            positives.append(f"Required validation input available: {rel(path)}")

    expanded_rows = read_csv(EXPANDED_CSV)
    exclusions_rows = read_csv(EXCLUSIONS_CSV)
    provider_breakdown_rows = read_csv(PROVIDER_BREAKDOWN_CSV)
    merge_audit_rows = read_csv(MERGE_AUDIT_CSV)

    expanded_columns = list(expanded_rows[0].keys()) if expanded_rows else []
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in expanded_columns]

    if missing_columns:
        blockers.append(f"Missing required expanded columns: {missing_columns}")
    elif expanded_rows:
        positives.append("Expanded universe canonical schema validated.")

    final_row_count = len(expanded_rows)
    final_exclusions_count = len(exclusions_rows)

    if final_row_count != EXPECTED_EXPANDED_ROWS:
        warnings.append(f"Final expanded row count differs from expected: {final_row_count} != {EXPECTED_EXPANDED_ROWS}")
    else:
        positives.append(f"Final expanded row count matches expected: {final_row_count}")

    if final_exclusions_count != EXPECTED_EXCLUSIONS_ROWS:
        warnings.append(f"Final exclusions row count differs from expected: {final_exclusions_count} != {EXPECTED_EXCLUSIONS_ROWS}")
    else:
        positives.append(f"Final exclusions row count matches expected: {final_exclusions_count}")

    provider_counts: Counter[str] = Counter()
    exchange_counts: Counter[str] = Counter()
    merge_action_counts: Counter[str] = Counter()
    precedence_counts: Counter[str] = Counter()
    instrument_type_counts: Counter[str] = Counter()
    instrument_scope_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()

    empty_counts = {
        "ticker": 0,
        "company_name": 0,
        "exchange": 0,
        "country": 0,
        "source_provider": 0,
        "instrument_type": 0,
        "instrument_scope": 0,
        "classification_confidence": 0,
        "merge_action": 0,
        "merge_reason": 0,
    }

    key_counter: Counter[tuple[str, str]] = Counter()

    for idx, row in enumerate(expanded_rows, start=1):
        ticker = norm_ticker(row.get("ticker", ""))
        exchange = norm_exchange(row.get("exchange", ""))
        provider = (row.get("source_provider") or "").strip()
        merge_action = (row.get("merge_action") or "").strip()
        precedence = (row.get("provider_precedence") or "").strip()

        provider_counts[provider] += 1
        exchange_counts[exchange] += 1
        merge_action_counts[merge_action] += 1
        precedence_counts[precedence] += 1
        instrument_type_counts[(row.get("instrument_type") or "").strip()] += 1
        instrument_scope_counts[(row.get("instrument_scope") or "").strip()] += 1
        confidence_counts[(row.get("classification_confidence") or "").strip()] += 1

        for field in empty_counts:
            if not (row.get(field) or "").strip():
                empty_counts[field] += 1
                issues.append(
                    {
                        "row_number": str(idx),
                        "issue_type": f"EMPTY_{field.upper()}",
                        "ticker": ticker,
                        "exchange": exchange,
                        "source_provider": provider,
                        "detail": f"Required/important field {field} is empty.",
                    }
                )

        if exchange and ticker:
            key_counter[(exchange, ticker)] += 1
        else:
            issues.append(
                {
                    "row_number": str(idx),
                    "issue_type": "INVALID_EXCHANGE_TICKER_KEY",
                    "ticker": ticker,
                    "exchange": exchange,
                    "source_provider": provider,
                    "detail": "Missing exchange or ticker prevents exchange+ticker key validation.",
                }
            )

        if merge_action not in ALLOWED_MERGE_ACTIONS:
            issues.append(
                {
                    "row_number": str(idx),
                    "issue_type": "INVALID_MERGE_ACTION",
                    "ticker": ticker,
                    "exchange": exchange,
                    "source_provider": provider,
                    "detail": f"merge_action={merge_action}",
                }
            )

        if precedence not in ALLOWED_PROVIDER_PRECEDENCE:
            issues.append(
                {
                    "row_number": str(idx),
                    "issue_type": "INVALID_PROVIDER_PRECEDENCE",
                    "ticker": ticker,
                    "exchange": exchange,
                    "source_provider": provider,
                    "detail": f"provider_precedence={precedence}",
                }
            )

    duplicate_keys = {
        key: count for key, count in key_counter.items() if count > 1
    }

    for (exchange, ticker), count in duplicate_keys.items():
        duplicate_rows.append(
            {
                "exchange": exchange,
                "ticker": ticker,
                "duplicate_count": str(count),
            }
        )

    if duplicate_keys:
        blockers.append(f"Duplicate exchange+ticker keys detected: {len(duplicate_keys)}")
    else:
        positives.append("Duplicate exchange+ticker keys: 0")

    provider_validation_rows: list[dict[str, str]] = []
    for provider, expected_count in EXPECTED_PROVIDER_COUNTS.items():
        actual_count = provider_counts.get(provider, 0)
        status = "OK" if actual_count == expected_count else "MISMATCH"
        provider_validation_rows.append(
            {
                "source_provider": provider,
                "expected_rows": str(expected_count),
                "actual_rows": str(actual_count),
                "status": status,
            }
        )
        if status == "OK":
            positives.append(f"Provider count OK: {provider} = {actual_count}")
        else:
            warnings.append(f"Provider count mismatch for {provider}: {actual_count} != {expected_count}")

    unexpected_providers = sorted(set(provider_counts) - set(EXPECTED_PROVIDER_COUNTS))
    for provider in unexpected_providers:
        provider_validation_rows.append(
            {
                "source_provider": provider,
                "expected_rows": "0",
                "actual_rows": str(provider_counts.get(provider, 0)),
                "status": "UNEXPECTED_PROVIDER",
            }
        )
        warnings.append(f"Unexpected provider in expanded universe: {provider}")

    for field, count in empty_counts.items():
        if count:
            if field in {"sector", "industry", "market_cap"}:
                warnings.append(f"Optional/partially populated field empty count {field}: {count}")
            else:
                warnings.append(f"Important field empty count {field}: {count}")

    sec_added_rows = merge_action_counts.get("ADD_SEC_PRIMARY_NET_NEW", 0)
    if sec_added_rows != EXPECTED_SEC_ADDED_ROWS:
        warnings.append(f"SEC added rows mismatch: {sec_added_rows} != {EXPECTED_SEC_ADDED_ROWS}")
    else:
        positives.append(f"SEC added rows match expected: {sec_added_rows}")

    first_expansion_unlocked = final_row_count >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = final_row_count >= MIN_FULL_SOURCE_ROWS

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - final_row_count, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - final_row_count, 0)

    if not first_expansion_unlocked:
        warnings.append(f"First expansion target remains blocked: {final_row_count} < {TARGET_FIRST_EXPANSION_ROWS}")

    if not full_source_unlocked:
        warnings.append(f"Full-source threshold remains blocked: {final_row_count} < {MIN_FULL_SOURCE_ROWS}")

    write_csv(
        OUT_PROVIDER_VALIDATION_CSV,
        provider_validation_rows,
        ["source_provider", "expected_rows", "actual_rows", "status"],
    )

    write_csv(
        OUT_ISSUES_CSV,
        issues,
        ["row_number", "issue_type", "ticker", "exchange", "source_provider", "detail"],
    )

    write_csv(
        OUT_DUPLICATES_CSV,
        duplicate_rows,
        ["exchange", "ticker", "duplicate_count"],
    )

    if blockers:
        validation_status = "EXPANDED_SOURCE_WITH_SEC_VALIDATION_BLOCKED"
        readiness_score = 0
        recommended_next_phase = "Resolve blockers"
    else:
        validation_status = "EXPANDED_SOURCE_WITH_SEC_VALIDATED_USEFUL_BUT_NOT_ENOUGH"
        readiness_score = 90
        recommended_next_phase = "v2.7D ? Expanded Source With SEC Closure Report"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "rebuild_json": rel(REBUILD_JSON),
            "expanded_csv": rel(EXPANDED_CSV),
            "exclusions_csv": rel(EXCLUSIONS_CSV),
            "provider_breakdown_csv": rel(PROVIDER_BREAKDOWN_CSV),
            "merge_audit_csv": rel(MERGE_AUDIT_CSV),
            "exclusion_breakdown_csv": rel(EXCLUSION_BREAKDOWN_CSV),
        },
        "outputs": {
            "provider_validation_csv": rel(OUT_PROVIDER_VALIDATION_CSV),
            "issues_csv": rel(OUT_ISSUES_CSV),
            "duplicates_csv": rel(OUT_DUPLICATES_CSV),
        },
        "schema": {
            "required_columns": REQUIRED_COLUMNS,
            "detected_columns": expanded_columns,
            "missing_columns": missing_columns,
        },
        "summary": {
            "expanded_rows": final_row_count,
            "exclusions_rows": final_exclusions_count,
            "expected_expanded_rows": EXPECTED_EXPANDED_ROWS,
            "expected_exclusions_rows": EXPECTED_EXCLUSIONS_ROWS,
            "provider_counts": dict(provider_counts),
            "exchange_counts": dict(exchange_counts),
            "merge_action_counts": dict(merge_action_counts),
            "provider_precedence_counts": dict(precedence_counts),
            "instrument_type_counts": dict(instrument_type_counts),
            "instrument_scope_counts": dict(instrument_scope_counts),
            "classification_confidence_counts": dict(confidence_counts),
            "empty_counts": empty_counts,
            "issues_count": len(issues),
            "duplicate_exchange_ticker_keys": len(duplicate_keys),
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
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
            "expanded_universe_rebuilt": False,
            "validation_only": True,
        },
        "recommendation": (
            "Proceed to v2.7D closure. SEC rebuild is validated as useful but still not enough to unlock first expansion or full-source thresholds."
            if not blockers
            else "Resolve blockers before closure."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.7C Validate Expanded Source With SEC")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Row summary")
    md.append("")
    md.append(f"- Expanded rows: {final_row_count}")
    md.append(f"- Expected expanded rows: {EXPECTED_EXPANDED_ROWS}")
    md.append(f"- Exclusions rows: {final_exclusions_count}")
    md.append(f"- Expected exclusions rows: {EXPECTED_EXCLUSIONS_ROWS}")
    md.append(f"- Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    md.append(f"- Issues count: {len(issues)}")
    md.append("")
    md.append("## Provider counts")
    md.append("")
    for provider, count in provider_counts.most_common():
        md.append(f"- {provider}: {count}")
    md.append("")
    md.append("## Merge action counts")
    md.append("")
    for action, count in merge_action_counts.most_common():
        md.append(f"- {action}: {count}")
    md.append("")
    md.append("## Exchange counts")
    md.append("")
    for exchange, count in exchange_counts.most_common():
        md.append(f"- {exchange}: {count}")
    md.append("")
    md.append("## Threshold status")
    md.append("")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- First expansion unlocked: {first_expansion_unlocked}")
    md.append(f"- Full source unlocked: {full_source_unlocked}")
    md.append(f"- Rows needed first expansion: {rows_needed_first_expansion}")
    md.append(f"- Rows needed full source: {rows_needed_full_source}")
    md.append("")
    md.append("## Data quality")
    md.append("")
    md.append(f"- Missing columns: {missing_columns}")
    for field, count in empty_counts.items():
        md.append(f"- Empty {field}: {count}")
    md.append("")
    md.append("## Outputs")
    md.append("")
    for key, value in payload["outputs"].items():
        md.append(f"- {key}: `{value}`")
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
    md.append("Important: v2.7C is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.7C Validate Expanded Source With SEC")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Expanded rows: {final_row_count}")
    print(f"OK   Exclusions rows: {final_exclusions_count}")
    print(f"OK   Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    print(f"OK   Issues count: {len(issues)}")
    print(f"OK   First expansion unlocked: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked: {full_source_unlocked}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Provider validation CSV written: {OUT_PROVIDER_VALIDATION_CSV}")
    print(f"OK   Issues CSV written: {OUT_ISSUES_CSV}")
    print(f"OK   Duplicates CSV written: {OUT_DUPLICATES_CSV}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
