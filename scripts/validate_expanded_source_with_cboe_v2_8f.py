from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.8F"
METHOD = "validate_expanded_source_with_cboe_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

REBUILD_JSON = OUT_DIR / "rebuild_expanded_source_with_cboe_real_v2_8e.json"

EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

PROVIDER_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_cboe_provider_breakdown_v2_8e.csv"
MERGE_AUDIT_CSV = OUT_DIR / "rebuild_expanded_source_with_cboe_merge_audit_v2_8e.csv"
EXCLUSION_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_cboe_exclusion_breakdown_v2_8e.csv"

OUT_JSON = OUT_DIR / "validate_expanded_source_with_cboe_v2_8f.json"
OUT_MD = OUT_DIR / "validate_expanded_source_with_cboe_v2_8f.md"
OUT_PROVIDER_VALIDATION_CSV = OUT_DIR / "validate_expanded_source_with_cboe_provider_validation_v2_8f.csv"
OUT_ISSUES_CSV = OUT_DIR / "validate_expanded_source_with_cboe_issues_v2_8f.csv"
OUT_DUPLICATES_CSV = OUT_DIR / "validate_expanded_source_with_cboe_duplicates_v2_8f.csv"

EXPECTED_EXPANDED_ROWS = 9200
EXPECTED_EXCLUSIONS_ROWS = 10056
EXPECTED_CBOE_ROWS = 1193

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
]

EXPECTED_PROVIDER_COUNTS = {
    "nasdaq_trader_nasdaqlisted": 3244,
    "nasdaq_trader_otherlisted": 2404,
    "sec_company_tickers_exchange": 2359,
    "cboe_listed_symbols": 1193,
}


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
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def key(row: dict[str, str]) -> tuple[str, str]:
    return (
        (row.get("exchange") or "").strip().upper(),
        (row.get("ticker") or "").strip().upper(),
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []
    issues: list[dict[str, Any]] = []

    rebuild = read_json(REBUILD_JSON)

    if not rebuild.get("_exists"):
        blockers.append(f"Missing v2.8E rebuild artifact: {rel(REBUILD_JSON)}")
    else:
        positives.append(f"v2.8E rebuild artifact found: {rel(REBUILD_JSON)}")

    rebuild_status = rebuild.get("rebuild_status")
    if rebuild_status == "REBUILD_EXPANDED_SOURCE_WITH_CBOE_COMPLETED_USEFUL_BUT_NOT_ENOUGH":
        positives.append(f"v2.8E rebuild status accepted: {rebuild_status}")
    else:
        blockers.append(f"Unexpected v2.8E rebuild status: {rebuild_status}")

    required_inputs = [
        EXPANDED_CSV,
        EXCLUSIONS_CSV,
        PROVIDER_BREAKDOWN_CSV,
        MERGE_AUDIT_CSV,
        EXCLUSION_BREAKDOWN_CSV,
    ]

    for path in required_inputs:
        if path.exists():
            positives.append(f"Required validation input available: {rel(path)}")
        else:
            blockers.append(f"Missing validation input: {rel(path)}")

    expanded_rows = read_csv(EXPANDED_CSV)
    exclusions_rows = read_csv(EXCLUSIONS_CSV)
    merge_audit_rows = read_csv(MERGE_AUDIT_CSV)

    fieldnames = list(expanded_rows[0].keys()) if expanded_rows else []

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
    if missing_columns:
        blockers.append(f"Missing required columns: {missing_columns}")
        issues.append({
            "severity": "BLOCKER",
            "issue_type": "MISSING_REQUIRED_COLUMNS",
            "detail": "|".join(missing_columns),
        })
    else:
        positives.append("Required canonical columns available.")

    if len(expanded_rows) != EXPECTED_EXPANDED_ROWS:
        blockers.append(f"Expanded rows mismatch: {len(expanded_rows)} != {EXPECTED_EXPANDED_ROWS}")
        issues.append({
            "severity": "BLOCKER",
            "issue_type": "EXPANDED_ROW_COUNT_MISMATCH",
            "detail": f"{len(expanded_rows)} != {EXPECTED_EXPANDED_ROWS}",
        })
    else:
        positives.append(f"Expanded row count OK: {len(expanded_rows)}")

    if len(exclusions_rows) != EXPECTED_EXCLUSIONS_ROWS:
        warnings.append(f"Exclusions rows mismatch: {len(exclusions_rows)} != {EXPECTED_EXCLUSIONS_ROWS}")
        issues.append({
            "severity": "WARNING",
            "issue_type": "EXCLUSIONS_ROW_COUNT_MISMATCH",
            "detail": f"{len(exclusions_rows)} != {EXPECTED_EXCLUSIONS_ROWS}",
        })
    else:
        positives.append(f"Exclusions row count OK: {len(exclusions_rows)}")

    duplicate_counter = Counter(key(row) for row in expanded_rows if key(row) != ("", ""))
    duplicate_rows: list[dict[str, Any]] = []

    for candidate_key, count in duplicate_counter.items():
        if count > 1:
            exchange, ticker = candidate_key
            duplicate_rows.append({
                "exchange": exchange,
                "ticker": ticker,
                "count": count,
            })

    if duplicate_rows:
        blockers.append(f"Duplicate exchange+ticker keys found: {len(duplicate_rows)}")
        issues.append({
            "severity": "BLOCKER",
            "issue_type": "DUPLICATE_EXCHANGE_TICKER_KEYS",
            "detail": str(len(duplicate_rows)),
        })
    else:
        positives.append("Duplicate exchange+ticker keys: 0")

    empty_checks = {
        "empty_ticker": sum(1 for row in expanded_rows if not (row.get("ticker") or "").strip()),
        "empty_company_name": sum(1 for row in expanded_rows if not (row.get("company_name") or "").strip()),
        "empty_exchange": sum(1 for row in expanded_rows if not (row.get("exchange") or "").strip()),
        "empty_country": sum(1 for row in expanded_rows if not (row.get("country") or "").strip()),
        "empty_source_provider": sum(1 for row in expanded_rows if not (row.get("source_provider") or "").strip()),
        "empty_instrument_type": sum(1 for row in expanded_rows if not (row.get("instrument_type") or "").strip()),
        "empty_instrument_scope": sum(1 for row in expanded_rows if not (row.get("instrument_scope") or "").strip()),
        "empty_classification_confidence": sum(1 for row in expanded_rows if not (row.get("classification_confidence") or "").strip()),
        "empty_classification_reason": sum(1 for row in expanded_rows if not (row.get("classification_reason") or "").strip()),
    }

    for check_name, count in empty_checks.items():
        if count:
            warnings.append(f"{check_name}: {count}")
            issues.append({
                "severity": "WARNING",
                "issue_type": check_name.upper(),
                "detail": str(count),
            })

    provider_counts = Counter((row.get("source_provider") or "").strip() for row in expanded_rows)

    provider_validation_rows: list[dict[str, Any]] = []
    for provider, expected_count in EXPECTED_PROVIDER_COUNTS.items():
        actual_count = provider_counts.get(provider, 0)
        status = "OK" if actual_count == expected_count else "MISMATCH"
        provider_validation_rows.append({
            "source_provider": provider,
            "expected_rows": expected_count,
            "actual_rows": actual_count,
            "status": status,
        })

        if status == "OK":
            positives.append(f"Provider count OK: {provider} = {actual_count}")
        else:
            blockers.append(f"Provider count mismatch: {provider} expected {expected_count}, actual {actual_count}")
            issues.append({
                "severity": "BLOCKER",
                "issue_type": "PROVIDER_COUNT_MISMATCH",
                "detail": f"{provider}: {actual_count} != {expected_count}",
            })

    cboe_rows = [row for row in expanded_rows if (row.get("source_provider") or "").strip() == "cboe_listed_symbols"]

    if len(cboe_rows) != EXPECTED_CBOE_ROWS:
        blockers.append(f"Cboe row count mismatch: {len(cboe_rows)} != {EXPECTED_CBOE_ROWS}")
    else:
        positives.append(f"Cboe row count OK: {len(cboe_rows)}")

    cboe_confidence_counts = Counter((row.get("classification_confidence") or "").strip() for row in cboe_rows)
    cboe_scope_counts = Counter((row.get("instrument_scope") or "").strip() for row in cboe_rows)

    if cboe_confidence_counts.get("LOW", 0) != EXPECTED_CBOE_ROWS:
        warnings.append(f"Cboe rows are not all LOW confidence: {dict(cboe_confidence_counts)}")
    else:
        positives.append("Cboe candidate rows keep LOW confidence.")

    expected_cboe_scope = "CANDIDATE_PROVIDER_ROW_PENDING_POST_REBUILD_VALIDATION"
    if cboe_scope_counts.get(expected_cboe_scope, 0) != EXPECTED_CBOE_ROWS:
        warnings.append(f"Cboe rows do not all use expected candidate scope: {dict(cboe_scope_counts)}")
    else:
        positives.append("Cboe candidate rows use expected pending-validation scope.")

    merge_action_counts = Counter((row.get("action") or "").strip() for row in merge_audit_rows)
    expected_merge_action_count = merge_action_counts.get("ADD_CBOE_CANDIDATE_NET_NEW", 0)

    if expected_merge_action_count != EXPECTED_CBOE_ROWS:
        warnings.append(f"Merge audit ADD_CBOE_CANDIDATE_NET_NEW count mismatch: {expected_merge_action_count} != {EXPECTED_CBOE_ROWS}")
    else:
        positives.append(f"Merge audit Cboe added rows OK: {expected_merge_action_count}")

    first_expansion_unlocked = len(expanded_rows) >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = len(expanded_rows) >= MIN_FULL_SOURCE_ROWS

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - len(expanded_rows), 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - len(expanded_rows), 0)

    if not first_expansion_unlocked:
        warnings.append(f"First expansion target remains blocked: {len(expanded_rows)} < {TARGET_FIRST_EXPANSION_ROWS}")

    if not full_source_unlocked:
        warnings.append(f"Full-source threshold remains blocked: {len(expanded_rows)} < {MIN_FULL_SOURCE_ROWS}")

    warnings.append("Cboe provider is useful but not enough to close source expansion.")
    warnings.append("Full 59k dry-run remains blocked.")

    write_csv(
        OUT_PROVIDER_VALIDATION_CSV,
        provider_validation_rows,
        ["source_provider", "expected_rows", "actual_rows", "status"],
    )
    write_csv(
        OUT_ISSUES_CSV,
        issues,
        ["severity", "issue_type", "detail"],
    )
    write_csv(
        OUT_DUPLICATES_CSV,
        duplicate_rows,
        ["exchange", "ticker", "count"],
    )

    if blockers:
        validation_status = "EXPANDED_SOURCE_WITH_CBOE_VALIDATION_BLOCKED"
        readiness_score = 0
        validation_decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        validation_status = "EXPANDED_SOURCE_WITH_CBOE_VALIDATED_USEFUL_BUT_NOT_ENOUGH"
        readiness_score = 90
        validation_decision = "CBOE_REBUILD_VALIDATED_USEFUL_BUT_NOT_ENOUGH"
        recommended_next_phase = "v2.8G ? Expanded Source With Cboe Closure Report OR v2.9A next provider route"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "validation_decision": validation_decision,
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
        "summary": {
            "expanded_rows": len(expanded_rows),
            "expected_expanded_rows": EXPECTED_EXPANDED_ROWS,
            "exclusions_rows": len(exclusions_rows),
            "expected_exclusions_rows": EXPECTED_EXCLUSIONS_ROWS,
            "duplicate_exchange_ticker_keys": len(duplicate_rows),
            "issues_count": len(issues),
            "cboe_rows": len(cboe_rows),
            "expected_cboe_rows": EXPECTED_CBOE_ROWS,
            "merge_action_counts": dict(merge_action_counts),
            "provider_counts": dict(provider_counts),
            "cboe_confidence_counts": dict(cboe_confidence_counts),
            "cboe_scope_counts": dict(cboe_scope_counts),
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
        },
        "empty_checks": empty_checks,
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
            "Close Cboe rebuild as useful but not enough, then decide between closure report and next provider route."
            if not blockers
            else "Resolve blockers before closing Cboe validation."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.8F Validate Expanded Source With Cboe")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Validation decision: **{validation_decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Row summary")
    md.append("")
    md.append(f"- Expanded rows: {len(expanded_rows)}")
    md.append(f"- Expected expanded rows: {EXPECTED_EXPANDED_ROWS}")
    md.append(f"- Exclusions rows: {len(exclusions_rows)}")
    md.append(f"- Expected exclusions rows: {EXPECTED_EXCLUSIONS_ROWS}")
    md.append(f"- Duplicate exchange+ticker keys: {len(duplicate_rows)}")
    md.append(f"- Issues count: {len(issues)}")
    md.append(f"- Cboe rows: {len(cboe_rows)}")
    md.append("")
    md.append("## Provider validation")
    md.append("")
    for row in provider_validation_rows:
        md.append(f"- {row['source_provider']}: expected {row['expected_rows']}, actual {row['actual_rows']}, status {row['status']}")
    md.append("")
    md.append("## Cboe candidate validation")
    md.append("")
    md.append(f"- Cboe confidence counts: `{dict(cboe_confidence_counts)}`")
    md.append(f"- Cboe scope counts: `{dict(cboe_scope_counts)}`")
    md.append(f"- Merge action counts: `{dict(merge_action_counts)}`")
    md.append("")
    md.append("## Threshold status")
    md.append("")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Expected full rows: {EXPECTED_FULL_ROWS}")
    md.append(f"- First expansion unlocked: {first_expansion_unlocked}")
    md.append(f"- Full source unlocked: {full_source_unlocked}")
    md.append(f"- Rows needed first expansion: {rows_needed_first_expansion}")
    md.append(f"- Rows needed full source: {rows_needed_full_source}")
    md.append("")
    md.append("## Data quality")
    md.append("")
    md.append(f"- Missing columns: {missing_columns}")
    for check_name, count in empty_checks.items():
        md.append(f"- {check_name}: {count}")
    md.append("")
    md.append("## Outputs")
    md.append("")
    for k, v in payload["outputs"].items():
        md.append(f"- {k}: `{v}`")
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
    md.append("Important: v2.8F is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.8F Validate Expanded Source With Cboe")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Validation decision: {validation_decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Expanded rows: {len(expanded_rows)}")
    print(f"OK   Exclusions rows: {len(exclusions_rows)}")
    print(f"OK   Cboe rows: {len(cboe_rows)}")
    print(f"OK   Duplicate exchange+ticker keys: {len(duplicate_rows)}")
    print(f"OK   Issues count: {len(issues)}")
    print(f"OK   First expansion unlocked: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked: {full_source_unlocked}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Provider validation written: {OUT_PROVIDER_VALIDATION_CSV}")
    print(f"OK   Issues written: {OUT_ISSUES_CSV}")
    print(f"OK   Duplicates written: {OUT_DUPLICATES_CSV}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Expanded universe rebuilt: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
