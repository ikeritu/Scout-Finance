from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.6E"
METHOD = "sec_incremental_coverage_analysis_v1"

PROVIDER_ID = "sec_company_tickers_exchange"

SEC_CSV = ROOT / "data" / "raw" / "source_providers" / PROVIDER_ID / "sec_company_tickers_exchange.csv"
EXPANDED_CSV = ROOT / "data" / "raw" / "expanded_universe" / "expanded_universe_v2_4b.csv"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
VALIDATION_JSON = OUT_DIR / "sec_company_tickers_exchange_validation_v2_6d.json"

OUT_JSON = OUT_DIR / "sec_incremental_coverage_analysis_v2_6e.json"
OUT_MD = OUT_DIR / "sec_incremental_coverage_analysis_v2_6e.md"

OUT_PRIMARY_NEW_CSV = OUT_DIR / "sec_incremental_primary_new_rows_v2_6e.csv"
OUT_PRIMARY_OVERLAP_CSV = OUT_DIR / "sec_incremental_primary_overlap_rows_v2_6e.csv"
OUT_ENRICHMENT_CSV = OUT_DIR / "sec_incremental_enrichment_rows_v2_6e.csv"
OUT_REBUILD_CANDIDATES_CSV = OUT_DIR / "sec_incremental_rebuild_candidates_v2_6e.csv"
OUT_DECISION_BREAKDOWN_CSV = OUT_DIR / "sec_incremental_decision_breakdown_v2_6e.csv"

PRIMARY_EXCHANGES = {"NASDAQ", "NYSE", "CBOE"}
ENRICHMENT_EXCHANGES = {"OTC", "None", ""}

CURRENT_INCLUDED_ROWS = 5648
TARGET_FIRST_EXPANSION_ROWS = 15000
MIN_FULL_SOURCE_ROWS = 50000
EXPECTED_FULL_ROWS = 59000


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


def key_ticker(row: dict[str, str]) -> str:
    return norm_ticker(row.get("ticker", ""))


def classify_sec_row(row: dict[str, str]) -> str:
    exchange = norm_exchange(row.get("exchange", ""))

    if exchange in PRIMARY_EXCHANGES:
        return "PRIMARY_EXCHANGE_CANDIDATE"

    if exchange in ENRICHMENT_EXCHANGES:
        return "ENRICHMENT_OR_EXCLUSION_CANDIDATE"

    return "UNKNOWN_EXCHANGE_REVIEW_REQUIRED"


def make_sec_output_row(row: dict[str, str], coverage_status: str) -> dict[str, str]:
    return {
        "ticker": norm_ticker(row.get("ticker", "")),
        "company_name": row.get("company_name", ""),
        "exchange": norm_exchange(row.get("exchange", "")),
        "raw_cik": row.get("raw_cik", ""),
        "source_provider": row.get("source_provider", ""),
        "sec_classification": classify_sec_row(row),
        "coverage_status": coverage_status,
        "instrument_type": row.get("instrument_type", ""),
        "instrument_scope": row.get("instrument_scope", ""),
        "classification_confidence": row.get("classification_confidence", ""),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    validation = read_json(VALIDATION_JSON)

    if not validation.get("_exists"):
        blockers.append(f"Missing v2.6D validation artifact: {rel(VALIDATION_JSON)}")
    else:
        positives.append(f"v2.6D validation artifact found: {rel(VALIDATION_JSON)}")

    validation_status = validation.get("validation_status")
    sec_route_decision = validation.get("sec_route_decision")

    if validation_status == "SEC_COMPANY_TICKERS_EXCHANGE_VALIDATED_WITH_PRIMARY_CANDIDATES":
        positives.append(f"v2.6D validation status accepted: {validation_status}")
    else:
        blockers.append(f"Unexpected v2.6D validation status: {validation_status}")

    if sec_route_decision == "USABLE_AS_PARTIAL_PROVIDER_AND_IDENTIFIER_ENRICHMENT":
        positives.append(f"v2.6D SEC route decision accepted: {sec_route_decision}")
    else:
        warnings.append(f"Unexpected v2.6D SEC route decision: {sec_route_decision}")

    sec_rows = read_csv(SEC_CSV)
    expanded_rows = read_csv(EXPANDED_CSV)

    if not sec_rows:
        blockers.append(f"SEC CSV missing or empty: {rel(SEC_CSV)}")
    else:
        positives.append(f"SEC CSV found: {rel(SEC_CSV)}")

    if not expanded_rows:
        blockers.append(f"Expanded universe CSV missing or empty: {rel(EXPANDED_CSV)}")
    else:
        positives.append(f"Expanded universe CSV found: {rel(EXPANDED_CSV)}")

    expanded_keys = {
        key_exchange_ticker(row)
        for row in expanded_rows
        if key_exchange_ticker(row)[0] and key_exchange_ticker(row)[1]
    }

    expanded_tickers = {
        key_ticker(row)
        for row in expanded_rows
        if key_ticker(row)
    }

    primary_new_rows: list[dict[str, str]] = []
    primary_overlap_rows: list[dict[str, str]] = []
    enrichment_rows: list[dict[str, str]] = []
    unknown_rows: list[dict[str, str]] = []
    rebuild_candidates: list[dict[str, str]] = []

    sec_exchange_counts: Counter[str] = Counter()
    sec_classification_counts: Counter[str] = Counter()
    primary_new_exchange_counts: Counter[str] = Counter()
    primary_overlap_exchange_counts: Counter[str] = Counter()

    sec_keys = set()
    primary_keys = set()
    primary_new_keys = set()
    primary_overlap_keys = set()
    enrichment_keys = set()

    for row in sec_rows:
        exchange = norm_exchange(row.get("exchange", ""))
        ticker = norm_ticker(row.get("ticker", ""))
        key = (exchange, ticker)
        classification = classify_sec_row(row)

        if exchange and ticker:
            sec_keys.add(key)

        sec_exchange_counts[exchange] += 1
        sec_classification_counts[classification] += 1

        if classification == "PRIMARY_EXCHANGE_CANDIDATE":
            primary_keys.add(key)

            if key in expanded_keys:
                primary_overlap_keys.add(key)
                primary_overlap_exchange_counts[exchange] += 1
                primary_overlap_rows.append(make_sec_output_row(row, "PRIMARY_OVERLAP_EXISTING"))
            else:
                primary_new_keys.add(key)
                primary_new_exchange_counts[exchange] += 1
                out_row = make_sec_output_row(row, "PRIMARY_NET_NEW")
                primary_new_rows.append(out_row)
                rebuild_candidates.append(out_row)

        elif classification == "ENRICHMENT_OR_EXCLUSION_CANDIDATE":
            if exchange and ticker:
                enrichment_keys.add(key)
            enrichment_rows.append(make_sec_output_row(row, "ENRICHMENT_OR_EXCLUSION"))

        else:
            unknown_rows.append(make_sec_output_row(row, "UNKNOWN_EXCHANGE_REVIEW_REQUIRED"))

    max_possible_rows_after_sec_rebuild = len(expanded_rows) + len(primary_new_keys)
    rows_needed_first_expansion_after_sec = max(TARGET_FIRST_EXPANSION_ROWS - max_possible_rows_after_sec_rebuild, 0)
    rows_needed_full_source_after_sec = max(MIN_FULL_SOURCE_ROWS - max_possible_rows_after_sec_rebuild, 0)

    first_expansion_unlocked = max_possible_rows_after_sec_rebuild >= TARGET_FIRST_EXPANSION_ROWS
    full_source_unlocked = max_possible_rows_after_sec_rebuild >= MIN_FULL_SOURCE_ROWS

    sec_incremental_gain_rows = len(primary_new_keys)
    sec_incremental_gain_pct_vs_current = (
        round((sec_incremental_gain_rows / len(expanded_rows)) * 100, 2)
        if expanded_rows
        else 0.0
    )

    coverage_after_sec_pct_of_first_expansion = round(
        (max_possible_rows_after_sec_rebuild / TARGET_FIRST_EXPANSION_ROWS) * 100,
        2,
    )

    coverage_after_sec_pct_of_full_source = round(
        (max_possible_rows_after_sec_rebuild / MIN_FULL_SOURCE_ROWS) * 100,
        2,
    )

    write_csv(
        OUT_PRIMARY_NEW_CSV,
        primary_new_rows,
        [
            "ticker",
            "company_name",
            "exchange",
            "raw_cik",
            "source_provider",
            "sec_classification",
            "coverage_status",
            "instrument_type",
            "instrument_scope",
            "classification_confidence",
        ],
    )

    write_csv(
        OUT_PRIMARY_OVERLAP_CSV,
        primary_overlap_rows,
        [
            "ticker",
            "company_name",
            "exchange",
            "raw_cik",
            "source_provider",
            "sec_classification",
            "coverage_status",
            "instrument_type",
            "instrument_scope",
            "classification_confidence",
        ],
    )

    write_csv(
        OUT_ENRICHMENT_CSV,
        enrichment_rows,
        [
            "ticker",
            "company_name",
            "exchange",
            "raw_cik",
            "source_provider",
            "sec_classification",
            "coverage_status",
            "instrument_type",
            "instrument_scope",
            "classification_confidence",
        ],
    )

    write_csv(
        OUT_REBUILD_CANDIDATES_CSV,
        rebuild_candidates,
        [
            "ticker",
            "company_name",
            "exchange",
            "raw_cik",
            "source_provider",
            "sec_classification",
            "coverage_status",
            "instrument_type",
            "instrument_scope",
            "classification_confidence",
        ],
    )

    decision_breakdown_rows = [
        {
            "metric": "current_expanded_rows",
            "value": len(expanded_rows),
            "interpretation": "Current validated expanded universe rows before SEC rebuild.",
        },
        {
            "metric": "sec_total_rows",
            "value": len(sec_rows),
            "interpretation": "Total normalized SEC rows.",
        },
        {
            "metric": "sec_primary_candidate_rows",
            "value": len(primary_keys),
            "interpretation": "SEC rows on primary exchanges considered possible provider rows.",
        },
        {
            "metric": "sec_primary_overlap_rows",
            "value": len(primary_overlap_keys),
            "interpretation": "SEC primary rows already present in expanded universe.",
        },
        {
            "metric": "sec_primary_net_new_rows",
            "value": len(primary_new_keys),
            "interpretation": "Net new primary exchange+ticker keys SEC could add.",
        },
        {
            "metric": "sec_enrichment_or_exclusion_rows",
            "value": len(enrichment_rows),
            "interpretation": "OTC/None rows to keep out of primary universe but useful for enrichment/exclusion analysis.",
        },
        {
            "metric": "max_possible_rows_after_sec_rebuild",
            "value": max_possible_rows_after_sec_rebuild,
            "interpretation": "Estimated row count if primary SEC new keys are merged.",
        },
        {
            "metric": "first_expansion_unlocked_15000",
            "value": str(first_expansion_unlocked),
            "interpretation": "Whether SEC alone reaches 15k target.",
        },
        {
            "metric": "full_source_unlocked_50000",
            "value": str(full_source_unlocked),
            "interpretation": "Whether SEC alone reaches 50k minimum full-source threshold.",
        },
    ]

    write_csv(
        OUT_DECISION_BREAKDOWN_CSV,
        decision_breakdown_rows,
        ["metric", "value", "interpretation"],
    )

    if unknown_rows:
        warnings.append(f"Unknown SEC exchange rows found: {len(unknown_rows)}")

    if enrichment_rows:
        warnings.append(f"SEC enrichment/exclusion rows should not be merged into primary universe: {len(enrichment_rows)}")

    if not first_expansion_unlocked:
        warnings.append(
            f"SEC does not unlock first expansion target: {max_possible_rows_after_sec_rebuild} < {TARGET_FIRST_EXPANSION_ROWS}"
        )

    if not full_source_unlocked:
        warnings.append(
            f"SEC does not unlock full-source threshold: {max_possible_rows_after_sec_rebuild} < {MIN_FULL_SOURCE_ROWS}"
        )

    if sec_incremental_gain_rows > 0:
        positives.append(f"SEC adds net new primary exchange+ticker keys: {sec_incremental_gain_rows}")

    if max_possible_rows_after_sec_rebuild > len(expanded_rows):
        positives.append(
            f"SEC can increase expanded universe from {len(expanded_rows)} to {max_possible_rows_after_sec_rebuild} rows before further providers."
        )

    if blockers:
        analysis_status = "SEC_INCREMENTAL_COVERAGE_ANALYSIS_BLOCKED"
        readiness_score = 0
        decision = "BLOCKED"
        recommended_next_phase = "Resolve blockers"
    else:
        if sec_incremental_gain_rows > 0 and not first_expansion_unlocked:
            analysis_status = "SEC_INCREMENTAL_COVERAGE_USEFUL_BUT_NOT_ENOUGH"
            readiness_score = 90
            decision = "REBUILD_WITH_SEC_USEFUL_BUT_NOT_ENOUGH"
            recommended_next_phase = "v2.7A ? Rebuild Expanded Source With SEC Plan"
        elif sec_incremental_gain_rows > 0 and first_expansion_unlocked and not full_source_unlocked:
            analysis_status = "SEC_INCREMENTAL_COVERAGE_UNLOCKS_FIRST_EXPANSION"
            readiness_score = 95
            decision = "REBUILD_WITH_SEC_JUSTIFIED_FIRST_EXPANSION"
            recommended_next_phase = "v2.7A ? Rebuild Expanded Source With SEC Plan"
        elif sec_incremental_gain_rows > 0 and full_source_unlocked:
            analysis_status = "SEC_INCREMENTAL_COVERAGE_UNLOCKS_FULL_SOURCE"
            readiness_score = 100
            decision = "REBUILD_WITH_SEC_JUSTIFIED_FULL_SOURCE"
            recommended_next_phase = "v2.7A ? Rebuild Expanded Source With SEC Plan"
        else:
            analysis_status = "SEC_INCREMENTAL_COVERAGE_ENRICHMENT_ONLY"
            readiness_score = 70
            decision = "SEC_ENRICHMENT_ONLY"
            recommended_next_phase = "v2.8A ? Cboe Listed Symbols Route Plan"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "analysis_status": analysis_status,
        "readiness_score": readiness_score,
        "decision": decision,
        "recommended_next_phase": recommended_next_phase,
        "inputs": {
            "sec_csv": rel(SEC_CSV),
            "expanded_universe_csv": rel(EXPANDED_CSV),
            "validation_json": rel(VALIDATION_JSON),
        },
        "summary": {
            "current_expanded_rows": len(expanded_rows),
            "sec_total_rows": len(sec_rows),
            "sec_total_unique_exchange_ticker_keys": len(sec_keys),
            "sec_primary_candidate_keys": len(primary_keys),
            "sec_primary_overlap_keys": len(primary_overlap_keys),
            "sec_primary_net_new_keys": len(primary_new_keys),
            "sec_enrichment_or_exclusion_rows": len(enrichment_rows),
            "sec_unknown_rows": len(unknown_rows),
            "sec_incremental_gain_rows": sec_incremental_gain_rows,
            "sec_incremental_gain_pct_vs_current": sec_incremental_gain_pct_vs_current,
            "max_possible_rows_after_sec_rebuild": max_possible_rows_after_sec_rebuild,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "rows_needed_first_expansion_after_sec": rows_needed_first_expansion_after_sec,
            "rows_needed_full_source_after_sec": rows_needed_full_source_after_sec,
            "coverage_after_sec_pct_of_first_expansion": coverage_after_sec_pct_of_first_expansion,
            "coverage_after_sec_pct_of_full_source": coverage_after_sec_pct_of_full_source,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
            "sec_exchange_counts": dict(sec_exchange_counts),
            "sec_classification_counts": dict(sec_classification_counts),
            "primary_new_exchange_counts": dict(primary_new_exchange_counts),
            "primary_overlap_exchange_counts": dict(primary_overlap_exchange_counts),
        },
        "outputs": {
            "primary_new_csv": rel(OUT_PRIMARY_NEW_CSV),
            "primary_overlap_csv": rel(OUT_PRIMARY_OVERLAP_CSV),
            "enrichment_csv": rel(OUT_ENRICHMENT_CSV),
            "rebuild_candidates_csv": rel(OUT_REBUILD_CANDIDATES_CSV),
            "decision_breakdown_csv": rel(OUT_DECISION_BREAKDOWN_CSV),
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
        },
        "recommendation": (
            "Proceed to v2.7A with a plan-only rebuild using SEC as partial provider and identifier enrichment. Do not run rebuild yet."
            if not blockers and decision.startswith("REBUILD_WITH_SEC")
            else "Proceed to next provider route before rebuild."
            if not blockers
            else "Resolve blockers before deciding rebuild."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.6E SEC Incremental Coverage Analysis")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Analysis status: **{analysis_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Decision: **{decision}**")
    md.append(f"- Recommended next phase: **{recommended_next_phase}**")
    md.append("")
    md.append("## Coverage summary")
    md.append("")
    md.append(f"- Current expanded rows: {len(expanded_rows)}")
    md.append(f"- SEC total rows: {len(sec_rows)}")
    md.append(f"- SEC primary candidate keys: {len(primary_keys)}")
    md.append(f"- SEC primary overlap keys: {len(primary_overlap_keys)}")
    md.append(f"- SEC primary net new keys: {len(primary_new_keys)}")
    md.append(f"- SEC enrichment/exclusion rows: {len(enrichment_rows)}")
    md.append(f"- SEC unknown rows: {len(unknown_rows)}")
    md.append(f"- SEC incremental gain vs current: {sec_incremental_gain_rows} rows ({sec_incremental_gain_pct_vs_current}%)")
    md.append("")
    md.append("## Rebuild impact estimate")
    md.append("")
    md.append(f"- Max possible rows after SEC rebuild: {max_possible_rows_after_sec_rebuild}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full-source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append(f"- Coverage after SEC vs first expansion target: {coverage_after_sec_pct_of_first_expansion}%")
    md.append(f"- Coverage after SEC vs full-source threshold: {coverage_after_sec_pct_of_full_source}%")
    md.append(f"- Rows still needed for first expansion after SEC: {rows_needed_first_expansion_after_sec}")
    md.append(f"- Rows still needed for full source after SEC: {rows_needed_full_source_after_sec}")
    md.append(f"- First expansion unlocked: {first_expansion_unlocked}")
    md.append(f"- Full source unlocked: {full_source_unlocked}")
    md.append("")
    md.append("## SEC exchange counts")
    md.append("")
    for exchange, count in sec_exchange_counts.most_common():
        md.append(f"- {exchange}: {count}")
    md.append("")
    md.append("## Primary new exchange counts")
    md.append("")
    if primary_new_exchange_counts:
        for exchange, count in primary_new_exchange_counts.most_common():
            md.append(f"- {exchange}: {count}")
    else:
        md.append("- No primary new exchange counts.")
    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append(f"- Primary new rows CSV: `{rel(OUT_PRIMARY_NEW_CSV)}`")
    md.append(f"- Primary overlap rows CSV: `{rel(OUT_PRIMARY_OVERLAP_CSV)}`")
    md.append(f"- Enrichment rows CSV: `{rel(OUT_ENRICHMENT_CSV)}`")
    md.append(f"- Rebuild candidates CSV: `{rel(OUT_REBUILD_CANDIDATES_CSV)}`")
    md.append(f"- Decision breakdown CSV: `{rel(OUT_DECISION_BREAKDOWN_CSV)}`")
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
    md.append("Important: v2.6E is an analysis-only step. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.6E SEC Incremental Coverage Analysis")
    print("=" * 92)
    print(f"OK   Analysis status: {analysis_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Decision: {decision}")
    print(f"OK   Recommended next phase: {recommended_next_phase}")
    print(f"OK   Current expanded rows: {len(expanded_rows)}")
    print(f"OK   SEC total rows: {len(sec_rows)}")
    print(f"OK   SEC primary candidate keys: {len(primary_keys)}")
    print(f"OK   SEC primary overlap keys: {len(primary_overlap_keys)}")
    print(f"OK   SEC primary net new keys: {len(primary_new_keys)}")
    print(f"OK   SEC enrichment/exclusion rows: {len(enrichment_rows)}")
    print(f"OK   Max possible rows after SEC rebuild: {max_possible_rows_after_sec_rebuild}")
    print(f"OK   First expansion unlocked: {first_expansion_unlocked}")
    print(f"OK   Full source unlocked: {full_source_unlocked}")
    print(f"OK   Rows still needed first expansion: {rows_needed_first_expansion_after_sec}")
    print(f"OK   Rows still needed full source: {rows_needed_full_source_after_sec}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
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
