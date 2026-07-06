from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.8E"
METHOD = "rebuild_expanded_source_with_cboe_real_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

PLAN_JSON = OUT_DIR / "rebuild_expanded_source_with_cboe_plan_v2_8d.json"

BASE_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"
BASE_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_7b.csv"
CBOE_NET_NEW_CSV = OUT_DIR / "cboe_listed_symbols_net_new_candidates_v2_8c.csv"

OUT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_8e.csv"
OUT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_8e.csv"

OUT_JSON = OUT_DIR / "rebuild_expanded_source_with_cboe_real_v2_8e.json"
OUT_MD = OUT_DIR / "rebuild_expanded_source_with_cboe_real_v2_8e.md"
OUT_PROVIDER_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_cboe_provider_breakdown_v2_8e.csv"
OUT_MERGE_AUDIT_CSV = OUT_DIR / "rebuild_expanded_source_with_cboe_merge_audit_v2_8e.csv"
OUT_EXCLUSION_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_cboe_exclusion_breakdown_v2_8e.csv"

EXPECTED_BASE_EXPANDED_ROWS = 8007
EXPECTED_BASE_EXCLUSIONS_ROWS = 10056
EXPECTED_CBOE_NET_NEW_ROWS = 1193
EXPECTED_FINAL_EXPANDED_ROWS = 9200

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


def canonical_key(row: dict[str, str]) -> tuple[str, str]:
    exchange = (row.get("exchange") or "").strip().upper()
    ticker = (row.get("ticker") or "").strip().upper()
    return exchange, ticker


def normalize_candidate_row(row: dict[str, str], base_fieldnames: list[str]) -> dict[str, str]:
    normalized = {field: (row.get(field, "") or "").strip() for field in base_fieldnames}

    normalized["ticker"] = (row.get("ticker") or "").strip().upper()
    normalized["company_name"] = (row.get("company_name") or "").strip()
    normalized["exchange"] = (row.get("exchange") or "CBOE").strip()
    normalized["country"] = (row.get("country") or "USA").strip()
    normalized["source_provider"] = "cboe_listed_symbols"
    normalized["source_file"] = (row.get("source_file") or rel(CBOE_NET_NEW_CSV)).strip()
    normalized["instrument_type"] = (row.get("instrument_type") or "UNKNOWN_PENDING_CLASSIFICATION").strip()
    normalized["instrument_scope"] = "CANDIDATE_PROVIDER_ROW_PENDING_POST_REBUILD_VALIDATION"
    normalized["classification_confidence"] = "LOW"
    normalized["classification_reason"] = (
        "Cboe candidate row added from v2.8C net-new candidate set; "
        "source semantics require v2.8F post-rebuild validation."
    )

    return normalized


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_EXPANDED_CSV.parent.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan = read_json(PLAN_JSON)

    if not plan.get("_exists"):
        blockers.append(f"Missing v2.8D plan artifact: {rel(PLAN_JSON)}")
    else:
        positives.append(f"v2.8D plan artifact found: {rel(PLAN_JSON)}")

    plan_status = plan.get("plan_status")
    plan_decision = plan.get("plan_decision")

    if plan_status == "REBUILD_EXPANDED_SOURCE_WITH_CBOE_PLAN_READY_WITH_CONDITIONS":
        positives.append(f"v2.8D plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.8D plan status: {plan_status}")

    if plan_decision == "CBOE_REBUILD_PLAN_APPROVED_WITH_CONDITIONS":
        positives.append(f"v2.8D plan decision accepted: {plan_decision}")
    else:
        blockers.append(f"Unexpected v2.8D plan decision: {plan_decision}")

    for path in [BASE_EXPANDED_CSV, BASE_EXCLUSIONS_CSV, CBOE_NET_NEW_CSV]:
        if path.exists():
            positives.append(f"Required rebuild input available: {rel(path)}")
        else:
            blockers.append(f"Missing rebuild input: {rel(path)}")

    base_rows = read_csv(BASE_EXPANDED_CSV)
    base_exclusion_rows = read_csv(BASE_EXCLUSIONS_CSV)
    cboe_rows = read_csv(CBOE_NET_NEW_CSV)

    if len(base_rows) != EXPECTED_BASE_EXPANDED_ROWS:
        blockers.append(f"Base expanded rows mismatch: {len(base_rows)} != {EXPECTED_BASE_EXPANDED_ROWS}")
    else:
        positives.append(f"Base expanded rows OK: {len(base_rows)}")

    if len(base_exclusion_rows) != EXPECTED_BASE_EXCLUSIONS_ROWS:
        warnings.append(f"Base exclusions rows mismatch: {len(base_exclusion_rows)} != {EXPECTED_BASE_EXCLUSIONS_ROWS}")
    else:
        positives.append(f"Base exclusions rows OK: {len(base_exclusion_rows)}")

    if len(cboe_rows) != EXPECTED_CBOE_NET_NEW_ROWS:
        warnings.append(f"Cboe net-new candidate rows differ from expected: {len(cboe_rows)} != {EXPECTED_CBOE_NET_NEW_ROWS}")
    else:
        positives.append(f"Cboe net-new candidate rows OK: {len(cboe_rows)}")

    if not base_rows:
        blockers.append("Base expanded universe is empty.")

    base_fieldnames = list(base_rows[0].keys()) if base_rows else REQUIRED_COLUMNS[:]

    missing_required_columns = [col for col in REQUIRED_COLUMNS if col not in base_fieldnames]
    if missing_required_columns:
        blockers.append(f"Base expanded universe missing required columns: {missing_required_columns}")
    else:
        positives.append("Base expanded universe canonical columns available.")

    base_keys = {canonical_key(row) for row in base_rows if all(canonical_key(row))}
    final_rows: list[dict[str, str]] = list(base_rows)
    merge_audit_rows: list[dict[str, Any]] = []

    skipped_overlap = 0
    skipped_invalid = 0
    added_cboe = 0

    if not blockers:
        for row in cboe_rows:
            key = canonical_key(row)
            exchange, ticker = key

            if not exchange or not ticker:
                skipped_invalid += 1
                merge_audit_rows.append({
                    "action": "SKIP_INVALID_KEY",
                    "exchange": exchange,
                    "ticker": ticker,
                    "source_provider": row.get("source_provider", ""),
                    "reason": "Missing exchange or ticker.",
                })
                continue

            if key in base_keys:
                skipped_overlap += 1
                merge_audit_rows.append({
                    "action": "SKIP_EXISTING_KEY",
                    "exchange": exchange,
                    "ticker": ticker,
                    "source_provider": row.get("source_provider", ""),
                    "reason": "exchange+ticker already exists in expanded_universe_v2_7b.",
                })
                continue

            new_row = normalize_candidate_row(row, base_fieldnames)
            final_rows.append(new_row)
            base_keys.add(key)
            added_cboe += 1
            merge_audit_rows.append({
                "action": "ADD_CBOE_CANDIDATE_NET_NEW",
                "exchange": exchange,
                "ticker": ticker,
                "source_provider": "cboe_listed_symbols",
                "reason": "Net-new exchange+ticker candidate from v2.8C.",
            })

    duplicate_keys = [
        key for key, count in Counter(canonical_key(row) for row in final_rows).items()
        if key != ("", "") and count > 1
    ]

    final_expanded_rows = len(final_rows)
    final_exclusions_rows = len(base_exclusion_rows)

    provider_counts = Counter((row.get("source_provider") or "").strip() for row in final_rows)
    exclusion_provider_counts = Counter((row.get("source_provider") or "").strip() for row in base_exclusion_rows)

    if duplicate_keys:
        blockers.append(f"Duplicate exchange+ticker keys found after rebuild: {len(duplicate_keys)}")
    else:
        positives.append("Duplicate exchange+ticker keys after rebuild: 0")

    if final_expanded_rows != EXPECTED_FINAL_EXPANDED_ROWS:
        warnings.append(f"Final expanded rows differ from expected: {final_expanded_rows} != {EXPECTED_FINAL_EXPANDED_ROWS}")
    else:
        positives.append(f"Final expanded rows OK: {final_expanded_rows}")

    first_expansion_unlocked = final_expanded_rows >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = final_expanded_rows >= MIN_FULL_SOURCE_ROWS

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - final_expanded_rows, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - final_expanded_rows, 0)

    warnings.append("Cboe rows are candidate-provider rows and require v2.8F validation before downstream use.")
    warnings.append(f"First expansion remains blocked: {final_expanded_rows} < {TARGET_FIRST_EXPANSION_ROWS}")
    warnings.append(f"Full-source threshold remains blocked: {final_expanded_rows} < {MIN_FULL_SOURCE_ROWS}")
    warnings.append("Full 59k dry-run remains blocked.")

    if blockers:
        rebuild_status = "REBUILD_EXPANDED_SOURCE_WITH_CBOE_BLOCKED"
        readiness_score = 0
        recommended_next_phase = "Resolve blockers"
    else:
        rebuild_status = "REBUILD_EXPANDED_SOURCE_WITH_CBOE_COMPLETED_USEFUL_BUT_NOT_ENOUGH"
        readiness_score = 88
        recommended_next_phase = "v2.8F ? Validate Expanded Source With Cboe"

        write_csv(OUT_EXPANDED_CSV, final_rows, base_fieldnames)
        write_csv(OUT_EXCLUSIONS_CSV, base_exclusion_rows, list(base_exclusion_rows[0].keys()) if base_exclusion_rows else base_fieldnames)

    provider_breakdown_rows = [
        {"source_provider": provider, "rows": count}
        for provider, count in provider_counts.most_common()
    ]

    exclusion_breakdown_rows = [
        {"source_provider": provider, "rows": count}
        for provider, count in exclusion_provider_counts.most_common()
    ]

    write_csv(OUT_PROVIDER_BREAKDOWN_CSV, provider_breakdown_rows, ["source_provider", "rows"])
    write_csv(OUT_MERGE_AUDIT_CSV, merge_audit_rows, ["action", "exchange", "ticker", "source_provider", "reason"])
    write_csv(OUT_EXCLUSION_BREAKDOWN_CSV, exclusion_breakdown_rows, ["source_provider", "rows"])

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "rebuild_status": rebuild_status,
        "readiness_score": readiness_score,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "plan_json": rel(PLAN_JSON),
            "base_expanded_csv": rel(BASE_EXPANDED_CSV),
            "base_exclusions_csv": rel(BASE_EXCLUSIONS_CSV),
            "cboe_net_new_candidates_csv": rel(CBOE_NET_NEW_CSV),
        },
        "outputs": {
            "expanded_universe_with_cboe_csv": rel(OUT_EXPANDED_CSV) if OUT_EXPANDED_CSV.exists() else None,
            "expanded_universe_exclusions_with_cboe_csv": rel(OUT_EXCLUSIONS_CSV) if OUT_EXCLUSIONS_CSV.exists() else None,
            "provider_breakdown_csv": rel(OUT_PROVIDER_BREAKDOWN_CSV),
            "merge_audit_csv": rel(OUT_MERGE_AUDIT_CSV),
            "exclusion_breakdown_csv": rel(OUT_EXCLUSION_BREAKDOWN_CSV),
        },
        "summary": {
            "base_expanded_rows": len(base_rows),
            "base_exclusions_rows": len(base_exclusion_rows),
            "cboe_candidate_rows_input": len(cboe_rows),
            "cboe_rows_added": added_cboe,
            "cboe_rows_skipped_overlap": skipped_overlap,
            "cboe_rows_skipped_invalid": skipped_invalid,
            "final_expanded_rows": final_expanded_rows,
            "final_exclusions_rows": final_exclusions_rows,
            "duplicate_exchange_ticker_keys": len(duplicate_keys),
            "projected_rows_after_cboe": final_expanded_rows,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_first_expansion": rows_needed_first_expansion,
            "rows_needed_full_source": rows_needed_full_source,
        },
        "provider_counts": dict(provider_counts),
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
            "expanded_universe_rebuilt": True,
            "active_mvp_outputs_overwritten": False,
            "isolated_rebuild_only": True,
        },
        "recommendation": (
            "Proceed to v2.8F validation before using Cboe-expanded universe downstream."
            if not blockers
            else "Resolve blockers before validation."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.8E Rebuild Expanded Source With Cboe Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Rebuild status: **{rebuild_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append(f"- Base expanded rows: {len(base_rows)}")
    md.append(f"- Base exclusions rows: {len(base_exclusion_rows)}")
    md.append(f"- Cboe candidate rows input: {len(cboe_rows)}")
    md.append(f"- Cboe rows added: {added_cboe}")
    md.append(f"- Cboe rows skipped overlap: {skipped_overlap}")
    md.append(f"- Cboe rows skipped invalid: {skipped_invalid}")
    md.append(f"- Final expanded rows: {final_expanded_rows}")
    md.append(f"- Final exclusions rows: {final_exclusions_rows}")
    md.append(f"- Duplicate exchange+ticker keys: {len(duplicate_keys)}")
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
    md.append("## Provider counts")
    md.append("")
    for provider, count in provider_counts.most_common():
        md.append(f"- {provider}: {count}")
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
    md.append("- Expanded universe rebuilt: true")
    md.append("- Active MVP outputs overwritten: false")
    md.append("- Isolated rebuild only: true")
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
    md.append("Important: v2.8E performs an isolated rebuild only. It does not execute scoring, call OpenAI, call a broker, overwrite active MVP outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.8E Rebuild Expanded Source With Cboe Real")
    print("=" * 92)
    print(f"OK   Rebuild status: {rebuild_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Base expanded rows: {len(base_rows)}")
    print(f"OK   Cboe candidate rows input: {len(cboe_rows)}")
    print(f"OK   Cboe rows added: {added_cboe}")
    print(f"OK   Final expanded rows: {final_expanded_rows}")
    print(f"OK   Final exclusions rows: {final_exclusions_rows}")
    print(f"OK   Duplicate exchange+ticker keys: {len(duplicate_keys)}")
    print(f"OK   First expansion unlocked: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked: {full_source_unlocked}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Expanded CSV written: {OUT_EXPANDED_CSV if OUT_EXPANDED_CSV.exists() else None}")
    print(f"OK   Exclusions CSV written: {OUT_EXCLUSIONS_CSV if OUT_EXCLUSIONS_CSV.exists() else None}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Active MVP outputs overwritten: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
