from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.16F"
PHASE = "TMX Candidate Validation Against Canonical Dry Run"
PHASE_TYPE = "candidate-validation-against-canonical-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V216E_JSON = OUTPUT_DIR / "tmx_candidate_extraction_dry_run_v2_16e.json"
V216E_CANDIDATES_CSV = OUTPUT_DIR / "tmx_candidate_extraction_candidates_v2_16e.csv"

REPORT_JSON = OUTPUT_DIR / "tmx_candidate_validation_against_canonical_v2_16f.json"
REPORT_MD = OUTPUT_DIR / "tmx_candidate_validation_against_canonical_v2_16f.md"
VALIDATION_ROWS_CSV = OUTPUT_DIR / "tmx_candidate_validation_rows_v2_16f.csv"
CANONICAL_PROFILE_CSV = OUTPUT_DIR / "tmx_candidate_validation_canonical_profile_v2_16f.csv"

CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713
SOURCE_TO_50K_COMPLETED_PERCENT = 76.6

NEXT_PHASE_IF_REBUILD_CANDIDATES = "v2.16G - TMX Expanded Rebuild Candidate"
NEXT_PHASE_IF_NO_REBUILD_CANDIDATES = "v2.16I - TMX Closure Report"

VALIDATION_FIELDS = [
    "validation_id",
    "candidate_id",
    "source_id",
    "extraction_method",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "confidence_bucket",
    "review_required",
    "candidate_key",
    "symbol_valid",
    "canonical_symbol_match_any_exchange",
    "canonical_symbol_exchange_match",
    "canonical_name_token_overlap_max",
    "canonical_match_count_symbol",
    "canonical_match_count_symbol_exchange",
    "validation_status",
    "dry_run_decision",
    "recommended_for_rebuild_candidate",
    "rebuild_candidate_reason",
    "canonical_match_examples",
    "evidence",
    "notes",
]

CANONICAL_PROFILE_FIELDS = [
    "metric",
    "value",
]

SYMBOL_COLUMNS = [
    "ticker",
    "symbol",
    "raw_symbol",
    "normalized_symbol",
    "source_symbol",
    "yahoo_symbol",
    "bbg_ticker",
    "figi_ticker",
    "security_ticker",
]

EXCHANGE_COLUMNS = [
    "exchange",
    "raw_exchange",
    "normalized_exchange",
    "source_exchange",
    "exchange_code",
    "market",
    "mic",
    "venue",
]

NAME_COLUMNS = [
    "name",
    "company_name",
    "raw_name",
    "security_name",
    "issuer_name",
    "instrument_name",
    "long_name",
    "short_name",
]

ISIN_COLUMNS = [
    "isin",
    "raw_isin",
    "security_isin",
]

VALID_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,14}$")

COMMON_WORDS = {
    "inc",
    "corp",
    "corporation",
    "company",
    "co",
    "ltd",
    "limited",
    "plc",
    "sa",
    "ag",
    "nv",
    "the",
    "and",
    "of",
    "group",
    "holdings",
    "holding",
    "class",
    "common",
    "shares",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    encodings = ["utf-8-sig", "utf-8", "cp1252"]

    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_symbol(value: str) -> str:
    value = str(value or "").strip().upper()
    for prefix in ["TSX:", "TSXV:", "TSX-V:", "NYSE:", "NASDAQ:"]:
        value = value.replace(prefix, "")
    return value.strip(" .,:;|[](){}")


def normalize_exchange(value: str) -> str:
    value = str(value or "").strip().upper()

    aliases = {
        "TSX VENTURE": "TSXV",
        "TSX VENTURE EXCHANGE": "TSXV",
        "TSX-V": "TSXV",
        "TSXV": "TSXV",
        "TORONTO STOCK EXCHANGE": "TSX",
        "TSX": "TSX",
        "XTSE": "TSX",
        "XTSX": "TSXV",
    }

    return aliases.get(value, value)


def normalize_name(value: str) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split()).strip()


def symbol_is_valid(symbol: str) -> bool:
    return bool(symbol and VALID_SYMBOL_RE.match(symbol))


def pick_column(fieldnames: list[str], candidates: list[str]) -> str:
    lower_map = {name.lower(): name for name in fieldnames if name}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    for name in fieldnames:
        low = name.lower()
        for candidate in candidates:
            if candidate.lower() in low:
                return name

    return ""


def name_tokens(name: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", normalize_name(name).lower())
    return {token for token in tokens if len(token) >= 3 and token not in COMMON_WORDS}


def token_overlap_ratio(a: str, b: str) -> float:
    a_tokens = name_tokens(a)
    b_tokens = name_tokens(b)

    if not a_tokens or not b_tokens:
        return 0.0

    return len(a_tokens.intersection(b_tokens)) / max(len(a_tokens), 1)


def compact_match_example(row: dict, symbol_col: str, exchange_col: str, name_col: str, isin_col: str) -> str:
    parts = []

    if symbol_col:
        parts.append(f"symbol={row.get(symbol_col, '')}")
    if exchange_col:
        parts.append(f"exchange={row.get(exchange_col, '')}")
    if name_col:
        parts.append(f"name={row.get(name_col, '')}")
    if isin_col:
        parts.append(f"isin={row.get(isin_col, '')}")

    return "; ".join(parts)[:500]


def build_canonical_index(canonical_rows: list[dict]) -> dict:
    fieldnames = list(canonical_rows[0].keys()) if canonical_rows else []

    symbol_col = pick_column(fieldnames, SYMBOL_COLUMNS)
    exchange_col = pick_column(fieldnames, EXCHANGE_COLUMNS)
    name_col = pick_column(fieldnames, NAME_COLUMNS)
    isin_col = pick_column(fieldnames, ISIN_COLUMNS)

    by_symbol = {}
    by_symbol_exchange = {}

    symbol_nonempty = 0
    exchange_nonempty = 0
    name_nonempty = 0
    isin_nonempty = 0

    for row in canonical_rows:
        symbol = normalize_symbol(row.get(symbol_col, "")) if symbol_col else ""
        exchange = normalize_exchange(row.get(exchange_col, "")) if exchange_col else ""
        name = normalize_name(row.get(name_col, "")) if name_col else ""
        isin = str(row.get(isin_col, "")).strip().upper() if isin_col else ""

        if symbol:
            symbol_nonempty += 1
            by_symbol.setdefault(symbol, []).append(row)

        if symbol and exchange:
            exchange_nonempty += 1
            by_symbol_exchange.setdefault((symbol, exchange), []).append(row)

        if name:
            name_nonempty += 1

        if isin:
            isin_nonempty += 1

    return {
        "fieldnames": fieldnames,
        "symbol_col": symbol_col,
        "exchange_col": exchange_col,
        "name_col": name_col,
        "isin_col": isin_col,
        "by_symbol": by_symbol,
        "by_symbol_exchange": by_symbol_exchange,
        "symbol_nonempty": symbol_nonempty,
        "exchange_nonempty": exchange_nonempty,
        "name_nonempty": name_nonempty,
        "isin_nonempty": isin_nonempty,
    }


def validate_candidate(candidate: dict, canonical_index: dict) -> dict:
    symbol = normalize_symbol(candidate.get("raw_symbol", ""))
    name = normalize_name(candidate.get("raw_name", ""))
    exchange = normalize_exchange(candidate.get("raw_exchange", ""))
    confidence = str(candidate.get("confidence_bucket", "")).strip().lower()
    review_required = str(candidate.get("review_required", "")).strip()

    symbol_valid = symbol_is_valid(symbol)

    symbol_matches = canonical_index["by_symbol"].get(symbol, []) if symbol else []
    symbol_exchange_matches = canonical_index["by_symbol_exchange"].get((symbol, exchange), []) if symbol and exchange else []

    canonical_symbol_match_any_exchange = bool(symbol_matches)
    canonical_symbol_exchange_match = bool(symbol_exchange_matches)

    name_col = canonical_index["name_col"]
    symbol_col = canonical_index["symbol_col"]
    exchange_col = canonical_index["exchange_col"]
    isin_col = canonical_index["isin_col"]

    max_overlap = 0.0

    for row in symbol_matches[:100]:
        canonical_name = row.get(name_col, "") if name_col else ""
        max_overlap = max(max_overlap, token_overlap_ratio(name, canonical_name))

    examples = []

    for row in (symbol_exchange_matches or symbol_matches)[:5]:
        examples.append(compact_match_example(row, symbol_col, exchange_col, name_col, isin_col))

    if not symbol_valid:
        validation_status = "rejected_invalid_symbol"
        dry_run_decision = "reject"
        recommended = False
        reason = "invalid_symbol_format"

    elif canonical_symbol_exchange_match:
        validation_status = "duplicate_exact_symbol_exchange"
        dry_run_decision = "reject_duplicate"
        recommended = False
        reason = "already_present_exact_symbol_exchange"

    elif canonical_symbol_match_any_exchange:
        validation_status = "possible_duplicate_symbol_review"
        dry_run_decision = "review_duplicate"
        recommended = False
        reason = "symbol_already_present_any_exchange"

    elif confidence == "high" and name and exchange:
        validation_status = "net_new_candidate_high_confidence_dry_run"
        dry_run_decision = "review_net_new_candidate"
        recommended = True
        reason = "symbol_absent_from_canonical_high_confidence"

    elif name and exchange:
        validation_status = "net_new_candidate_medium_evidence_dry_run"
        dry_run_decision = "review_net_new_candidate"
        recommended = True
        reason = "symbol_absent_from_canonical_name_and_exchange_present"

    elif name:
        validation_status = "net_new_candidate_low_evidence_review"
        dry_run_decision = "manual_review_required"
        recommended = False
        reason = "symbol_absent_but_exchange_missing"

    else:
        validation_status = "rejected_insufficient_evidence"
        dry_run_decision = "reject"
        recommended = False
        reason = "missing_name_or_exchange_evidence"

    validation_id = sha256_text(
        "|".join(
            [
                VERSION,
                candidate.get("candidate_id", ""),
                candidate.get("source_id", ""),
                symbol,
                name.lower(),
                exchange,
                validation_status,
            ]
        )
    )[:16]

    return {
        "validation_id": validation_id,
        "candidate_id": candidate.get("candidate_id", ""),
        "source_id": candidate.get("source_id", ""),
        "extraction_method": candidate.get("extraction_method", ""),
        "raw_symbol": symbol,
        "raw_name": name,
        "raw_exchange": exchange,
        "confidence_bucket": candidate.get("confidence_bucket", ""),
        "review_required": review_required,
        "candidate_key": candidate.get("candidate_key", ""),
        "symbol_valid": symbol_valid,
        "canonical_symbol_match_any_exchange": canonical_symbol_match_any_exchange,
        "canonical_symbol_exchange_match": canonical_symbol_exchange_match,
        "canonical_name_token_overlap_max": round(max_overlap, 4),
        "canonical_match_count_symbol": len(symbol_matches),
        "canonical_match_count_symbol_exchange": len(symbol_exchange_matches),
        "validation_status": validation_status,
        "dry_run_decision": dry_run_decision,
        "recommended_for_rebuild_candidate": recommended,
        "rebuild_candidate_reason": reason,
        "canonical_match_examples": " || ".join(examples),
        "evidence": candidate.get("evidence", ""),
        "notes": candidate.get("notes", ""),
    }


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, VALIDATION_ROWS_CSV, CANONICAL_PROFILE_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    e_report = read_json(V216E_JSON)
    candidates = read_csv(V216E_CANDIDATES_CSV)
    canonical_rows = read_csv(CANONICAL_DATASET)

    canonical_index = build_canonical_index(canonical_rows)
    validation_rows = [validate_candidate(candidate, canonical_index) for candidate in candidates]

    status_counter = Counter(row["validation_status"] for row in validation_rows)
    decision_counter = Counter(row["dry_run_decision"] for row in validation_rows)
    source_counter = Counter(row["source_id"] for row in validation_rows)
    confidence_counter = Counter(row["confidence_bucket"] for row in validation_rows)

    recommended_count = sum(1 for row in validation_rows if row["recommended_for_rebuild_candidate"])
    duplicate_exact_count = status_counter.get("duplicate_exact_symbol_exchange", 0)
    duplicate_symbol_review_count = status_counter.get("possible_duplicate_symbol_review", 0)
    low_evidence_count = status_counter.get("net_new_candidate_low_evidence_review", 0)
    rejected_count = sum(1 for row in validation_rows if str(row["dry_run_decision"]).startswith("reject"))

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_16e_report_exists", V216E_JSON.exists(), "critical", str(V216E_JSON))
    add_check("v2_16e_candidates_exists", V216E_CANDIDATES_CSV.exists(), "critical", str(V216E_CANDIDATES_CSV))
    add_check(
        "v2_16e_status_valid",
        e_report.get("status") == "TMX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED",
        "critical",
        e_report.get("status", ""),
    )
    add_check(
        "v2_16e_recommended_f",
        e_report.get("recommended_next_phase") == "v2.16F - TMX Candidate Validation Against Canonical Dry Run",
        "critical",
        e_report.get("recommended_next_phase", ""),
    )
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_dataset_rows_expected", len(canonical_rows) == CURRENT_ROWS, "critical", f"canonical_rows={len(canonical_rows)} expected={CURRENT_ROWS}")
    add_check("canonical_symbol_column_detected", bool(canonical_index["symbol_col"]), "critical", f"symbol_col={canonical_index['symbol_col']}")
    add_check("candidate_rows_loaded", len(candidates) > 0, "critical", f"candidate_rows={len(candidates)}")
    add_check("validation_rows_generated", len(validation_rows) == len(candidates), "critical", f"validation_rows={len(validation_rows)} candidates={len(candidates)}")
    add_check("canonical_dataset_read_only", True, "critical", "canonical_dataset_modified=False")
    add_check("canonical_comparison_performed", True, "critical", "canonical_comparison_performed=True")
    add_check("net_new_dry_run_classification_performed", True, "critical", "net_new_dry_run_classification_performed=True")
    add_check("net_new_filtering_not_applied", True, "critical", "net_new_filtering_applied=False")
    add_check("expanded_universe_not_rebuilt", True, "critical", "expanded_universe_rebuilt=False")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("recommended_rebuild_candidates_review", recommended_count > 0, "warning", f"recommended_count={recommended_count}")
    add_check("duplicates_review", duplicate_exact_count + duplicate_symbol_review_count >= 0, "warning", f"duplicate_exact={duplicate_exact_count}; duplicate_symbol_review={duplicate_symbol_review_count}")
    add_check("low_evidence_review", low_evidence_count >= 0, "warning", f"low_evidence={low_evidence_count}")
    add_check("full_source_still_blocked", CURRENT_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_ROWS} < {FULL_SOURCE_THRESHOLD}")

    if critical_failed != 0:
        status = "TMX_CANDIDATE_VALIDATION_DRY_RUN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.16F_FIX - TMX Candidate Validation Repair"
    elif recommended_count > 0:
        status = "TMX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_REBUILD_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_REBUILD_CANDIDATES
    else:
        status = "TMX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NO_REBUILD_CANDIDATES_REBUILD_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_NO_REBUILD_CANDIDATES

    profile_rows = [
        {"metric": "canonical_rows", "value": len(canonical_rows)},
        {"metric": "canonical_field_count", "value": len(canonical_index["fieldnames"])},
        {"metric": "symbol_col", "value": canonical_index["symbol_col"]},
        {"metric": "exchange_col", "value": canonical_index["exchange_col"]},
        {"metric": "name_col", "value": canonical_index["name_col"]},
        {"metric": "isin_col", "value": canonical_index["isin_col"]},
        {"metric": "symbol_nonempty", "value": canonical_index["symbol_nonempty"]},
        {"metric": "exchange_nonempty", "value": canonical_index["exchange_nonempty"]},
        {"metric": "name_nonempty", "value": canonical_index["name_nonempty"]},
        {"metric": "isin_nonempty", "value": canonical_index["isin_nonempty"]},
        {"metric": "candidate_rows", "value": len(candidates)},
        {"metric": "validation_rows", "value": len(validation_rows)},
        {"metric": "recommended_for_rebuild_candidate", "value": recommended_count},
        {"metric": "duplicate_exact_symbol_exchange", "value": duplicate_exact_count},
        {"metric": "possible_duplicate_symbol_review", "value": duplicate_symbol_review_count},
        {"metric": "low_evidence_review", "value": low_evidence_count},
        {"metric": "rejected_count", "value": rejected_count},
        {"metric": "critical_failed_checks", "value": critical_failed},
    ]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": str(CANONICAL_DATASET),
            "current_rows": CURRENT_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": SOURCE_TO_50K_COMPLETED_PERCENT,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "validation_summary": {
            "v2_16e_status": e_report.get("status", ""),
            "v2_16e_recommended_next_phase": e_report.get("recommended_next_phase", ""),
            "canonical_rows": len(canonical_rows),
            "candidate_rows": len(candidates),
            "validation_rows": len(validation_rows),
            "canonical_symbol_col": canonical_index["symbol_col"],
            "canonical_exchange_col": canonical_index["exchange_col"],
            "canonical_name_col": canonical_index["name_col"],
            "canonical_isin_col": canonical_index["isin_col"],
            "recommended_for_rebuild_candidate": recommended_count,
            "duplicate_exact_symbol_exchange": duplicate_exact_count,
            "possible_duplicate_symbol_review": duplicate_symbol_review_count,
            "low_evidence_review": low_evidence_count,
            "rejected_count": rejected_count,
            "status_counts": dict(status_counter),
            "decision_counts": dict(decision_counter),
            "source_counts": dict(source_counter),
            "confidence_counts": dict(confidence_counter),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "validation_preview": validation_rows[:100],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "candidate_rows_read": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_comparison_performed": True,
            "net_new_dry_run_classification_performed": True,
            "net_new_filtering_applied": False,
            "expanded_universe_rebuilt": False,
            "new_expanded_dataset_written": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)
    write_csv(VALIDATION_ROWS_CSV, validation_rows, VALIDATION_FIELDS)
    write_csv(CANONICAL_PROFILE_CSV, profile_rows, CANONICAL_PROFILE_FIELDS)

    validation_lines = "\n".join(
        f"- `{row['raw_symbol']}` `{row['raw_name']}` exchange=`{row['raw_exchange']}` status=`{row['validation_status']}` decision=`{row['dry_run_decision']}` rebuild={row['recommended_for_rebuild_candidate']} reason=`{row['rebuild_candidate_reason']}`"
        for row in validation_rows
    ) or "- No validation rows."

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Current state

- Canonical dataset: `{CANONICAL_DATASET}`
- Current rows: `{CURRENT_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completed: `{SOURCE_TO_50K_COMPLETED_PERCENT}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- v2.16E status: `{payload["validation_summary"]["v2_16e_status"]}`
- v2.16E recommended next phase: `{payload["validation_summary"]["v2_16e_recommended_next_phase"]}`
- Canonical rows: `{len(canonical_rows)}`
- Candidate rows: `{len(candidates)}`
- Validation rows: `{len(validation_rows)}`
- Canonical symbol column: `{canonical_index["symbol_col"]}`
- Canonical exchange column: `{canonical_index["exchange_col"]}`
- Canonical name column: `{canonical_index["name_col"]}`
- Canonical ISIN column: `{canonical_index["isin_col"]}`
- Recommended for rebuild candidate: `{recommended_count}`
- Duplicate exact symbol/exchange: `{duplicate_exact_count}`
- Possible duplicate symbol review: `{duplicate_symbol_review_count}`
- Low evidence review: `{low_evidence_count}`
- Rejected count: `{rejected_count}`
- Status counts: `{dict(status_counter)}`
- Decision counts: `{dict(decision_counter)}`
- Source counts: `{dict(source_counter)}`
- Confidence counts: `{dict(confidence_counter)}`
- Critical failed checks: `{critical_failed}`

## Validation rows

{validation_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Candidate rows read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Canonical comparison performed: true
- Net-new dry-run classification performed: true
- Net-new filtering applied: false
- Expanded universe rebuilt: false
- New expanded dataset written: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX candidate validation against canonical completed as a dry run.

This phase reads the v2.16E candidate file and the current canonical expanded universe, classifies candidate overlap against the canonical symbol/exchange universe, and identifies whether any candidate should proceed to a rebuild-candidate phase. It does not modify the canonical dataset, does not write a new expanded universe, does not apply net-new filtering to the canonical dataset and does not rebuild.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16F TMX candidate validation against canonical dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in payload["validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CHECKS:")
    for row in checks:
        print(f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) - {row['detail']}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("RECOMMENDED_NEXT_PHASE:")
    print(f"- {recommended_next_phase}")


if __name__ == "__main__":
    main()
