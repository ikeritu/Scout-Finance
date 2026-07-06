from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.7B"
METHOD = "rebuild_expanded_source_with_sec_real_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"

PLAN_JSON = OUT_DIR / "rebuild_expanded_source_with_sec_plan_v2_7a.json"

CURRENT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_4b.csv"
CURRENT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_4b.csv"

SEC_REBUILD_CANDIDATES_CSV = OUT_DIR / "sec_incremental_rebuild_candidates_v2_6e.csv"
SEC_ENRICHMENT_CSV = OUT_DIR / "sec_incremental_enrichment_rows_v2_6e.csv"

OUT_EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_7b.csv"
OUT_EXCLUSIONS_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_exclusions_v2_7b.csv"

OUT_JSON = OUT_DIR / "rebuild_expanded_source_with_sec_real_v2_7b.json"
OUT_MD = OUT_DIR / "rebuild_expanded_source_with_sec_real_v2_7b.md"
OUT_PROVIDER_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_sec_provider_breakdown_v2_7b.csv"
OUT_MERGE_AUDIT_CSV = OUT_DIR / "rebuild_expanded_source_with_sec_merge_audit_v2_7b.csv"
OUT_EXCLUSION_BREAKDOWN_CSV = OUT_DIR / "rebuild_expanded_source_with_sec_exclusion_breakdown_v2_7b.csv"

TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000

CANONICAL_COLUMNS = [
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


def ensure_columns(row: dict[str, str], defaults: dict[str, str] | None = None) -> dict[str, str]:
    defaults = defaults or {}
    out: dict[str, str] = {}

    for column in CANONICAL_COLUMNS:
        out[column] = str(row.get(column, defaults.get(column, "")) or "")

    return out


def normalize_existing_row(row: dict[str, str]) -> dict[str, str]:
    out = ensure_columns(
        row,
        {
            "provider_precedence": "1",
            "merge_action": "PRESERVE_EXISTING",
            "merge_reason": "Existing validated expanded_universe_v2_4b row preserved as base source.",
        },
    )

    out["ticker"] = norm_ticker(out["ticker"])
    out["exchange"] = norm_exchange(out["exchange"])

    if not out["provider_precedence"]:
        out["provider_precedence"] = "1"
    if not out["merge_action"]:
        out["merge_action"] = "PRESERVE_EXISTING"
    if not out["merge_reason"]:
        out["merge_reason"] = "Existing validated expanded_universe_v2_4b row preserved as base source."

    return out


def normalize_sec_candidate_row(row: dict[str, str]) -> dict[str, str]:
    out = ensure_columns(
        row,
        {
            "country": "USA",
            "source_provider": "sec_company_tickers_exchange",
            "source_file": "data/raw/source_providers/sec_company_tickers_exchange/company_tickers_exchange.json",
            "instrument_type": "UNKNOWN_PENDING_CLASSIFICATION",
            "instrument_scope": "UNKNOWN_PENDING_CLASSIFICATION",
            "classification_confidence": "LOW",
            "classification_reason": "SEC company_tickers_exchange primary net-new row; instrument type requires downstream provider confirmation.",
            "provider_precedence": "2",
            "merge_action": "ADD_SEC_PRIMARY_NET_NEW",
            "merge_reason": "SEC primary exchange+ticker key not present in expanded_universe_v2_4b.",
        },
    )

    out["ticker"] = norm_ticker(out["ticker"])
    out["exchange"] = norm_exchange(out["exchange"])

    out["source_provider"] = "sec_company_tickers_exchange"
    out["provider_precedence"] = "2"
    out["merge_action"] = "ADD_SEC_PRIMARY_NET_NEW"
    out["merge_reason"] = "SEC primary exchange+ticker key not present in expanded_universe_v2_4b."

    return out


def normalize_exclusion_row(row: dict[str, str], source: str, reason: str) -> dict[str, str]:
    out = ensure_columns(
        row,
        {
            "country": "USA",
            "source_provider": row.get("source_provider", source),
            "source_file": row.get("source_file", ""),
            "instrument_type": row.get("instrument_type", ""),
            "instrument_scope": row.get("instrument_scope", ""),
            "classification_confidence": row.get("classification_confidence", ""),
            "classification_reason": row.get("classification_reason", ""),
            "provider_precedence": "3",
            "merge_action": "EXCLUDE_OR_ENRICHMENT_REFERENCE",
            "merge_reason": reason,
        },
    )

    out["ticker"] = norm_ticker(out["ticker"])
    out["exchange"] = norm_exchange(out["exchange"])

    if not out["source_provider"]:
        out["source_provider"] = source

    out["provider_precedence"] = "3"
    out["merge_action"] = "EXCLUDE_OR_ENRICHMENT_REFERENCE"
    out["merge_reason"] = reason

    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_EXPANDED_CSV.parent.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    plan = read_json(PLAN_JSON)

    if not plan.get("_exists"):
        blockers.append(f"Missing v2.7A plan artifact: {rel(PLAN_JSON)}")
    else:
        positives.append(f"v2.7A plan artifact found: {rel(PLAN_JSON)}")

    plan_status = plan.get("plan_status")
    if plan_status == "REBUILD_EXPANDED_SOURCE_WITH_SEC_PLAN_READY":
        positives.append(f"v2.7A plan status accepted: {plan_status}")
    else:
        blockers.append(f"Unexpected v2.7A plan status: {plan_status}")

    required_inputs = [
        CURRENT_EXPANDED_CSV,
        CURRENT_EXCLUSIONS_CSV,
        SEC_REBUILD_CANDIDATES_CSV,
        SEC_ENRICHMENT_CSV,
    ]

    for path in required_inputs:
        if not path.exists():
            blockers.append(f"Missing required input: {rel(path)}")
        else:
            positives.append(f"Required input available: {rel(path)}")

    current_rows = read_csv(CURRENT_EXPANDED_CSV)
    current_exclusion_rows = read_csv(CURRENT_EXCLUSIONS_CSV)
    sec_candidate_rows = read_csv(SEC_REBUILD_CANDIDATES_CSV)
    sec_enrichment_rows = read_csv(SEC_ENRICHMENT_CSV)

    if not current_rows:
        blockers.append(f"Current expanded universe is empty: {rel(CURRENT_EXPANDED_CSV)}")

    if not sec_candidate_rows:
        blockers.append(f"SEC rebuild candidates are empty: {rel(SEC_REBUILD_CANDIDATES_CSV)}")

    expanded_rows: list[dict[str, str]] = []
    exclusions_rows: list[dict[str, str]] = []
    merge_audit_rows: list[dict[str, str]] = []

    existing_keys: set[tuple[str, str]] = set()
    duplicate_existing_keys: Counter[tuple[str, str]] = Counter()

    if not blockers:
        for row in current_rows:
            normalized = normalize_existing_row(row)
            key = key_exchange_ticker(normalized)

            if not key[0] or not key[1]:
                exclusions_rows.append(
                    normalize_exclusion_row(
                        normalized,
                        source=normalized.get("source_provider", "existing_expanded_universe_v2_4b"),
                        reason="Existing row missing exchange or ticker; routed to exclusions in v2.7B.",
                    )
                )
                merge_audit_rows.append(
                    {
                        "exchange": key[0],
                        "ticker": key[1],
                        "source": "existing_expanded_universe_v2_4b",
                        "merge_action": "EXCLUDE_EXISTING_INVALID_KEY",
                        "merge_reason": "Missing exchange or ticker.",
                    }
                )
                continue

            duplicate_existing_keys[key] += 1
            if duplicate_existing_keys[key] > 1:
                exclusions_rows.append(
                    normalize_exclusion_row(
                        normalized,
                        source=normalized.get("source_provider", "existing_expanded_universe_v2_4b"),
                        reason="Duplicate existing exchange+ticker key routed to exclusions; first occurrence preserved.",
                    )
                )
                merge_audit_rows.append(
                    {
                        "exchange": key[0],
                        "ticker": key[1],
                        "source": "existing_expanded_universe_v2_4b",
                        "merge_action": "EXCLUDE_EXISTING_DUPLICATE",
                        "merge_reason": "Duplicate existing exchange+ticker key.",
                    }
                )
                continue

            existing_keys.add(key)
            expanded_rows.append(normalized)
            merge_audit_rows.append(
                {
                    "exchange": key[0],
                    "ticker": key[1],
                    "source": "existing_expanded_universe_v2_4b",
                    "merge_action": "PRESERVE_EXISTING",
                    "merge_reason": "Base row preserved.",
                }
            )

        added_sec_keys: set[tuple[str, str]] = set()
        skipped_sec_existing_overlap = 0
        skipped_sec_internal_duplicate = 0
        skipped_sec_invalid_key = 0
        added_sec_rows = 0

        for row in sec_candidate_rows:
            normalized = normalize_sec_candidate_row(row)
            key = key_exchange_ticker(normalized)

            if not key[0] or not key[1]:
                skipped_sec_invalid_key += 1
                exclusions_rows.append(
                    normalize_exclusion_row(
                        normalized,
                        source="sec_company_tickers_exchange",
                        reason="SEC candidate missing exchange or ticker; routed to exclusions.",
                    )
                )
                merge_audit_rows.append(
                    {
                        "exchange": key[0],
                        "ticker": key[1],
                        "source": "sec_company_tickers_exchange",
                        "merge_action": "EXCLUDE_SEC_INVALID_KEY",
                        "merge_reason": "Missing exchange or ticker.",
                    }
                )
                continue

            if key in existing_keys:
                skipped_sec_existing_overlap += 1
                exclusions_rows.append(
                    normalize_exclusion_row(
                        normalized,
                        source="sec_company_tickers_exchange",
                        reason="SEC candidate overlaps existing v2.4B exchange+ticker key; existing row wins.",
                    )
                )
                merge_audit_rows.append(
                    {
                        "exchange": key[0],
                        "ticker": key[1],
                        "source": "sec_company_tickers_exchange",
                        "merge_action": "EXCLUDE_SEC_OVERLAP_EXISTING",
                        "merge_reason": "Existing v2.4B key wins.",
                    }
                )
                continue

            if key in added_sec_keys:
                skipped_sec_internal_duplicate += 1
                exclusions_rows.append(
                    normalize_exclusion_row(
                        normalized,
                        source="sec_company_tickers_exchange",
                        reason="SEC internal duplicate exchange+ticker key; first occurrence added.",
                    )
                )
                merge_audit_rows.append(
                    {
                        "exchange": key[0],
                        "ticker": key[1],
                        "source": "sec_company_tickers_exchange",
                        "merge_action": "EXCLUDE_SEC_INTERNAL_DUPLICATE",
                        "merge_reason": "SEC internal duplicate key.",
                    }
                )
                continue

            added_sec_keys.add(key)
            expanded_rows.append(normalized)
            added_sec_rows += 1
            merge_audit_rows.append(
                {
                    "exchange": key[0],
                    "ticker": key[1],
                    "source": "sec_company_tickers_exchange",
                    "merge_action": "ADD_SEC_PRIMARY_NET_NEW",
                    "merge_reason": "SEC primary exchange+ticker key not present in v2.4B.",
                }
            )

        for row in current_exclusion_rows:
            exclusions_rows.append(
                normalize_exclusion_row(
                    row,
                    source=row.get("source_provider", "existing_expanded_universe_exclusions_v2_4b"),
                    reason="Existing v2.4B exclusion preserved.",
                )
            )

        for row in sec_enrichment_rows:
            exclusions_rows.append(
                normalize_exclusion_row(
                    row,
                    source="sec_company_tickers_exchange",
                    reason="SEC OTC/None row preserved as enrichment/exclusion reference; not merged into primary universe.",
                )
            )

        expanded_keys = [key_exchange_ticker(row) for row in expanded_rows]
        duplicate_final_keys = {
            f"{exchange}|{ticker}": count
            for (exchange, ticker), count in Counter(expanded_keys).items()
            if count > 1
        }

        if duplicate_final_keys:
            blockers.append(f"Final expanded universe has duplicate exchange+ticker keys: {len(duplicate_final_keys)}")

        if skipped_sec_existing_overlap:
            warnings.append(f"SEC candidates skipped due to existing overlap: {skipped_sec_existing_overlap}")

        if skipped_sec_internal_duplicate:
            warnings.append(f"SEC internal duplicates skipped: {skipped_sec_internal_duplicate}")

        if skipped_sec_invalid_key:
            warnings.append(f"SEC invalid-key candidates skipped: {skipped_sec_invalid_key}")

        if len(expanded_rows) < TARGET_FIRST_EXPANSION_ROWS:
            warnings.append(f"v2.7B output does not unlock first expansion target: {len(expanded_rows)} < {TARGET_FIRST_EXPANSION_ROWS}")

        if len(expanded_rows) < MIN_FULL_SOURCE_ROWS:
            warnings.append(f"v2.7B output does not unlock full-source threshold: {len(expanded_rows)} < {MIN_FULL_SOURCE_ROWS}")

        positives.append(f"Existing rows preserved or normalized: {len(current_rows)}")
        positives.append(f"SEC primary net-new rows added: {added_sec_rows}")
        positives.append(f"SEC enrichment/exclusion rows preserved outside primary universe: {len(sec_enrichment_rows)}")

        write_csv(OUT_EXPANDED_CSV, expanded_rows, CANONICAL_COLUMNS)
        write_csv(OUT_EXCLUSIONS_CSV, exclusions_rows, CANONICAL_COLUMNS)

        write_csv(
            OUT_MERGE_AUDIT_CSV,
            merge_audit_rows,
            ["exchange", "ticker", "source", "merge_action", "merge_reason"],
        )

        provider_counter = Counter(row.get("source_provider", "") for row in expanded_rows)
        provider_breakdown_rows = [
            {"source_provider": provider, "included_rows": count}
            for provider, count in provider_counter.most_common()
        ]

        write_csv(
            OUT_PROVIDER_BREAKDOWN_CSV,
            provider_breakdown_rows,
            ["source_provider", "included_rows"],
        )

        exclusion_counter = Counter(row.get("merge_reason", "") for row in exclusions_rows)
        exclusion_breakdown_rows = [
            {"merge_reason": reason, "row_count": count}
            for reason, count in exclusion_counter.most_common()
        ]

        write_csv(
            OUT_EXCLUSION_BREAKDOWN_CSV,
            exclusion_breakdown_rows,
            ["merge_reason", "row_count"],
        )

    else:
        added_sec_rows = 0
        skipped_sec_existing_overlap = 0
        skipped_sec_internal_duplicate = 0
        skipped_sec_invalid_key = 0
        duplicate_final_keys = {}

    final_rows = len(expanded_rows)
    final_exclusions = len(exclusions_rows)

    rows_needed_first_expansion = max(TARGET_FIRST_EXPANSION_ROWS - final_rows, 0)
    rows_needed_full_source = max(MIN_FULL_SOURCE_ROWS - final_rows, 0)

    first_expansion_unlocked = final_rows >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = final_rows >= MIN_FULL_SOURCE_ROWS

    if blockers:
        rebuild_status = "REBUILD_EXPANDED_SOURCE_WITH_SEC_BLOCKED"
        readiness_score = 0
        recommended_next_phase = "Resolve blockers"
    else:
        rebuild_status = "REBUILD_EXPANDED_SOURCE_WITH_SEC_COMPLETED_USEFUL_BUT_NOT_ENOUGH"
        readiness_score = 90
        recommended_next_phase = "v2.7C ? Validate Expanded Source With SEC"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "rebuild_status": rebuild_status,
        "readiness_score": readiness_score,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "plan_json": rel(PLAN_JSON),
            "current_expanded_csv": rel(CURRENT_EXPANDED_CSV),
            "current_exclusions_csv": rel(CURRENT_EXCLUSIONS_CSV),
            "sec_rebuild_candidates_csv": rel(SEC_REBUILD_CANDIDATES_CSV),
            "sec_enrichment_csv": rel(SEC_ENRICHMENT_CSV),
        },
        "outputs": {
            "expanded_universe_v2_7b_csv": rel(OUT_EXPANDED_CSV) if OUT_EXPANDED_CSV.exists() else None,
            "expanded_universe_exclusions_v2_7b_csv": rel(OUT_EXCLUSIONS_CSV) if OUT_EXCLUSIONS_CSV.exists() else None,
            "provider_breakdown_csv": rel(OUT_PROVIDER_BREAKDOWN_CSV) if OUT_PROVIDER_BREAKDOWN_CSV.exists() else None,
            "merge_audit_csv": rel(OUT_MERGE_AUDIT_CSV) if OUT_MERGE_AUDIT_CSV.exists() else None,
            "exclusion_breakdown_csv": rel(OUT_EXCLUSION_BREAKDOWN_CSV) if OUT_EXCLUSION_BREAKDOWN_CSV.exists() else None,
        },
        "summary": {
            "current_expanded_input_rows": len(current_rows),
            "current_exclusions_input_rows": len(current_exclusion_rows),
            "sec_candidate_input_rows": len(sec_candidate_rows),
            "sec_enrichment_input_rows": len(sec_enrichment_rows),
            "final_expanded_rows": final_rows,
            "final_exclusions_rows": final_exclusions,
            "sec_primary_rows_added": added_sec_rows,
            "sec_skipped_existing_overlap": skipped_sec_existing_overlap,
            "sec_skipped_internal_duplicate": skipped_sec_internal_duplicate,
            "sec_skipped_invalid_key": skipped_sec_invalid_key,
            "final_duplicate_exchange_ticker_keys": len(duplicate_final_keys),
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
            "expanded_universe_rebuilt": True,
            "active_mvp_outputs_overwritten": False,
            "versioned_output_only": True,
        },
        "recommendation": (
            "Proceed to v2.7C validation. SEC rebuild is useful but still does not unlock first expansion or full-source thresholds."
            if not blockers
            else "Resolve blockers before validation."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.7B Rebuild Expanded Source With SEC Real")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Rebuild status: **{rebuild_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Rebuild summary")
    md.append("")
    md.append(f"- Current expanded input rows: {len(current_rows)}")
    md.append(f"- Current exclusions input rows: {len(current_exclusion_rows)}")
    md.append(f"- SEC candidate input rows: {len(sec_candidate_rows)}")
    md.append(f"- SEC enrichment input rows: {len(sec_enrichment_rows)}")
    md.append(f"- Final expanded rows: {final_rows}")
    md.append(f"- Final exclusions rows: {final_exclusions}")
    md.append(f"- SEC primary rows added: {added_sec_rows}")
    md.append(f"- SEC skipped existing overlap: {skipped_sec_existing_overlap}")
    md.append(f"- SEC skipped internal duplicate: {skipped_sec_internal_duplicate}")
    md.append(f"- SEC skipped invalid key: {skipped_sec_invalid_key}")
    md.append(f"- Final duplicate exchange+ticker keys: {len(duplicate_final_keys)}")
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
    md.append("- Versioned output only: true")
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
    md.append("Important: v2.7B creates versioned source outputs only. It does not execute scoring, call OpenAI, call a broker, overwrite active MVP outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.7B Rebuild Expanded Source With SEC Real")
    print("=" * 92)
    print(f"OK   Rebuild status: {rebuild_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Current expanded input rows: {len(current_rows)}")
    print(f"OK   SEC candidate input rows: {len(sec_candidate_rows)}")
    print(f"OK   Final expanded rows: {final_rows}")
    print(f"OK   Final exclusions rows: {final_exclusions}")
    print(f"OK   SEC primary rows added: {added_sec_rows}")
    print(f"OK   Final duplicate exchange+ticker keys: {len(duplicate_final_keys)}")
    print(f"OK   First expansion unlocked: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked: {full_source_unlocked}")
    print(f"OK   Rows needed first expansion: {rows_needed_first_expansion}")
    print(f"OK   Rows needed full source: {rows_needed_full_source}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   Expanded CSV written: {OUT_EXPANDED_CSV if OUT_EXPANDED_CSV.exists() else None}")
    print(f"OK   Exclusions CSV written: {OUT_EXCLUSIONS_CSV if OUT_EXCLUSIONS_CSV.exists() else None}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: False")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Active MVP outputs overwritten: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
