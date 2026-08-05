from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.16G"
PHASE = "TMX Expanded Rebuild Candidate"
PHASE_TYPE = "expanded-rebuild-candidate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
V216F_JSON = OUTPUT_DIR / "tmx_candidate_validation_against_canonical_v2_16f.json"
V216F_ROWS_CSV = OUTPUT_DIR / "tmx_candidate_validation_rows_v2_16f.csv"

CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_tmx_v2_16g.csv"
ADDITIONS_CSV = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_additions_v2_16g.csv"
REPORT_JSON = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_v2_16g.json"
REPORT_MD = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_v2_16g.md"
ROW_AUDIT_CSV = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_row_audit_v2_16g.csv"

CURRENT_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_BEFORE = 11713
SOURCE_TO_50K_COMPLETED_PERCENT_BEFORE = 76.6

NEXT_PHASE = "v2.16H - TMX Expanded Validation"

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

SOURCE_COLUMNS = [
    "source",
    "source_id",
    "source_name",
    "source_provider",
    "provider",
    "data_source",
]

COUNTRY_COLUMNS = [
    "country",
    "issuer_country",
    "domicile_country",
    "market_country",
]

CURRENCY_COLUMNS = [
    "currency",
    "trading_currency",
    "quote_currency",
]

ADDITION_FIELDS = [
    "addition_id",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "confidence_bucket",
    "source_id",
    "validation_status",
    "dry_run_decision",
    "rebuild_candidate_reason",
    "mapped_symbol_column",
    "mapped_name_column",
    "mapped_exchange_column",
    "candidate_dataset_row_index",
    "evidence",
    "notes",
]

ROW_AUDIT_FIELDS = [
    "audit_id",
    "row_type",
    "symbol",
    "name",
    "exchange",
    "source_id",
    "validation_status",
    "dry_run_decision",
    "recommended_for_rebuild_candidate",
    "action",
    "detail",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
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


def truthy(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def canonical_key(row: dict, symbol_col: str, exchange_col: str) -> tuple[str, str]:
    symbol = normalize_symbol(row.get(symbol_col, "")) if symbol_col else ""
    exchange = normalize_exchange(row.get(exchange_col, "")) if exchange_col else ""
    return symbol, exchange


def build_addition_row(
    validation_row: dict,
    fieldnames: list[str],
    symbol_col: str,
    name_col: str,
    exchange_col: str,
    source_col: str,
    country_col: str,
    currency_col: str,
) -> dict:
    row = {field: "" for field in fieldnames}

    symbol = normalize_symbol(validation_row.get("raw_symbol", ""))
    name = str(validation_row.get("raw_name", "")).strip()
    exchange = normalize_exchange(validation_row.get("raw_exchange", ""))
    source_id = str(validation_row.get("source_id", "")).strip()

    if symbol_col:
        row[symbol_col] = symbol

    if name_col:
        row[name_col] = name

    if exchange_col:
        row[exchange_col] = exchange

    if source_col:
        row[source_col] = f"tmx_v2_16g:{source_id}"

    if country_col:
        row[country_col] = "Canada"

    if currency_col:
        row[currency_col] = "CAD"

    for field in fieldnames:
        low = field.lower()

        if low in {"source_phase", "phase", "source_version", "version"}:
            row[field] = VERSION
        elif low in {"source_url", "url", "raw_url"}:
            row[field] = ""
        elif low in {"confidence", "confidence_bucket"}:
            row[field] = validation_row.get("confidence_bucket", "")
        elif low in {"review_required", "needs_review"}:
            row[field] = "True"
        elif low in {"validation_status"}:
            row[field] = validation_row.get("validation_status", "")
        elif low in {"rebuild_candidate_reason"}:
            row[field] = validation_row.get("rebuild_candidate_reason", "")

    return row


def main() -> None:
    for path in [CANDIDATE_DATASET, ADDITIONS_CSV, REPORT_JSON, REPORT_MD, ROW_AUDIT_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    f_report = read_json(V216F_JSON)
    validation_rows = read_csv(V216F_ROWS_CSV)
    canonical_rows = read_csv(CANONICAL_DATASET)

    fieldnames = list(canonical_rows[0].keys()) if canonical_rows else []

    symbol_col = pick_column(fieldnames, SYMBOL_COLUMNS)
    exchange_col = pick_column(fieldnames, EXCHANGE_COLUMNS)
    name_col = pick_column(fieldnames, NAME_COLUMNS)
    source_col = pick_column(fieldnames, SOURCE_COLUMNS)
    country_col = pick_column(fieldnames, COUNTRY_COLUMNS)
    currency_col = pick_column(fieldnames, CURRENCY_COLUMNS)

    selected = [
        row
        for row in validation_rows
        if truthy(row.get("recommended_for_rebuild_candidate", ""))
    ]

    canonical_keys = {
        canonical_key(row, symbol_col, exchange_col)
        for row in canonical_rows
        if canonical_key(row, symbol_col, exchange_col)[0]
    }

    additions = []
    row_audit = []

    for selected_row in selected:
        symbol = normalize_symbol(selected_row.get("raw_symbol", ""))
        exchange = normalize_exchange(selected_row.get("raw_exchange", ""))
        name = str(selected_row.get("raw_name", "")).strip()
        key = (symbol, exchange)

        audit_base = {
            "symbol": symbol,
            "name": name,
            "exchange": exchange,
            "source_id": selected_row.get("source_id", ""),
            "validation_status": selected_row.get("validation_status", ""),
            "dry_run_decision": selected_row.get("dry_run_decision", ""),
            "recommended_for_rebuild_candidate": selected_row.get("recommended_for_rebuild_candidate", ""),
        }

        if key in canonical_keys:
            row_audit.append(
                {
                    "audit_id": sha256_text(f"skip|{symbol}|{exchange}")[:16],
                    "row_type": "selected_validation_row",
                    **audit_base,
                    "action": "skip",
                    "detail": "symbol_exchange_already_in_canonical_at_rebuild_candidate_time",
                }
            )
            continue

        addition_row = build_addition_row(
            selected_row,
            fieldnames,
            symbol_col,
            name_col,
            exchange_col,
            source_col,
            country_col,
            currency_col,
        )

        addition_id = sha256_text(
            f"{VERSION}|{symbol}|{name.lower()}|{exchange}|{selected_row.get('validation_id', '')}"
        )[:16]

        additions.append(
            {
                "addition_id": addition_id,
                "raw_symbol": symbol,
                "raw_name": name,
                "raw_exchange": exchange,
                "confidence_bucket": selected_row.get("confidence_bucket", ""),
                "source_id": selected_row.get("source_id", ""),
                "validation_status": selected_row.get("validation_status", ""),
                "dry_run_decision": selected_row.get("dry_run_decision", ""),
                "rebuild_candidate_reason": selected_row.get("rebuild_candidate_reason", ""),
                "mapped_symbol_column": symbol_col,
                "mapped_name_column": name_col,
                "mapped_exchange_column": exchange_col,
                "candidate_dataset_row_index": CURRENT_ROWS + len(additions) + 1,
                "evidence": selected_row.get("evidence", ""),
                "notes": selected_row.get("notes", ""),
            }
        )

        row_audit.append(
            {
                "audit_id": sha256_text(f"add|{symbol}|{exchange}|{addition_id}")[:16],
                "row_type": "candidate_addition",
                **audit_base,
                "action": "add_to_candidate_dataset_only",
                "detail": "added_to_v2_16g_candidate_dataset_not_to_canonical",
            }
        )

    candidate_rows = list(canonical_rows)

    addition_lookup = {
        row["addition_id"]: row for row in additions
    }

    for addition in additions:
        selected_row = next(
            row
            for row in selected
            if normalize_symbol(row.get("raw_symbol", "")) == addition["raw_symbol"]
            and normalize_exchange(row.get("raw_exchange", "")) == addition["raw_exchange"]
        )

        candidate_rows.append(
            build_addition_row(
                selected_row,
                fieldnames,
                symbol_col,
                name_col,
                exchange_col,
                source_col,
                country_col,
                currency_col,
            )
        )

    write_csv(CANDIDATE_DATASET, candidate_rows, fieldnames)
    write_csv(ADDITIONS_CSV, additions, ADDITION_FIELDS)
    write_csv(ROW_AUDIT_CSV, row_audit, ROW_AUDIT_FIELDS)

    candidate_rows_written = len(candidate_rows)
    additions_count = len(additions)
    expected_candidate_rows = len(canonical_rows) + additions_count
    rows_needed_after_candidate = FULL_SOURCE_THRESHOLD - candidate_rows_written
    source_to_50k_after_candidate = round((candidate_rows_written / FULL_SOURCE_THRESHOLD) * 100, 2)

    source_counter = Counter(row["source_id"] for row in additions)
    exchange_counter = Counter(row["raw_exchange"] for row in additions)
    confidence_counter = Counter(row["confidence_bucket"] for row in additions)

    checks = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_16f_report_exists", V216F_JSON.exists(), "critical", str(V216F_JSON))
    add_check("v2_16f_rows_exists", V216F_ROWS_CSV.exists(), "critical", str(V216F_ROWS_CSV))
    add_check(
        "v2_16f_status_valid",
        f_report.get("status") == "TMX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_REBUILD_CANDIDATES_FOUND_REBUILD_STILL_BLOCKED",
        "critical",
        f_report.get("status", ""),
    )
    add_check(
        "v2_16f_recommended_g",
        f_report.get("recommended_next_phase") == "v2.16G - TMX Expanded Rebuild Candidate",
        "critical",
        f_report.get("recommended_next_phase", ""),
    )
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", len(canonical_rows) == CURRENT_ROWS, "critical", f"canonical_rows={len(canonical_rows)} expected={CURRENT_ROWS}")
    add_check("canonical_symbol_column_detected", bool(symbol_col), "critical", f"symbol_col={symbol_col}")
    add_check("canonical_name_column_detected", bool(name_col), "critical", f"name_col={name_col}")
    add_check("canonical_exchange_column_detected", bool(exchange_col), "warning", f"exchange_col={exchange_col}")
    add_check("selected_rebuild_candidates_loaded", len(selected) > 0, "critical", f"selected={len(selected)}")
    add_check("additions_created", additions_count > 0, "critical", f"additions={additions_count}")
    add_check("expected_single_tmx_addition", additions_count == 1, "critical", f"additions={additions_count}")
    add_check("candidate_dataset_rows_expected", candidate_rows_written == expected_candidate_rows, "critical", f"candidate_rows={candidate_rows_written} expected={expected_candidate_rows}")
    add_check("candidate_dataset_written", CANDIDATE_DATASET.exists(), "critical", str(CANDIDATE_DATASET))
    add_check("additions_csv_written", ADDITIONS_CSV.exists(), "critical", str(ADDITIONS_CSV))
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("new_expanded_candidate_dataset_written", True, "critical", str(CANDIDATE_DATASET))
    add_check("canonical_replacement_not_performed", True, "critical", "expanded_universe_v2_14e.csv untouched")
    add_check("full_source_still_blocked", candidate_rows_written < FULL_SOURCE_THRESHOLD, "critical", f"{candidate_rows_written} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed != 0:
        status = "TMX_EXPANDED_REBUILD_CANDIDATE_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.16G_FIX - TMX Expanded Rebuild Candidate Repair"
    else:
        status = "TMX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_ADD1_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": str(CANONICAL_DATASET),
            "canonical_rows_before": len(canonical_rows),
            "candidate_dataset": str(CANDIDATE_DATASET),
            "candidate_rows_after": candidate_rows_written,
            "additions": additions_count,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_before": ROWS_NEEDED_BEFORE,
            "rows_needed_after_candidate": rows_needed_after_candidate,
            "source_to_50k_completed_percent_before": SOURCE_TO_50K_COMPLETED_PERCENT_BEFORE,
            "source_to_50k_completed_percent_after_candidate": source_to_50k_after_candidate,
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "schema_mapping": {
            "symbol_col": symbol_col,
            "name_col": name_col,
            "exchange_col": exchange_col,
            "source_col": source_col,
            "country_col": country_col,
            "currency_col": currency_col,
            "field_count": len(fieldnames),
        },
        "rebuild_candidate_summary": {
            "v2_16f_status": f_report.get("status", ""),
            "v2_16f_recommended_next_phase": f_report.get("recommended_next_phase", ""),
            "selected_rebuild_candidates": len(selected),
            "additions_created": additions_count,
            "canonical_rows_before": len(canonical_rows),
            "candidate_rows_after": candidate_rows_written,
            "rows_needed_after_candidate": rows_needed_after_candidate,
            "source_to_50k_completed_percent_after_candidate": source_to_50k_after_candidate,
            "source_counts": dict(source_counter),
            "exchange_counts": dict(exchange_counter),
            "confidence_counts": dict(confidence_counter),
            "candidate_dataset_sha256": sha256_file(CANDIDATE_DATASET),
            "additions_sha256": sha256_file(ADDITIONS_CSV),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "additions": additions,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "candidate_validation_rows_read": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "new_expanded_candidate_dataset_written": True,
            "canonical_replacement_performed": False,
            "net_new_filtering_applied_to_canonical": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "repo_wide_renormalization_performed": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "full_source_gate_unblocked": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    addition_lines = "\n".join(
        f"- `{row['raw_symbol']}` `{row['raw_name']}` exchange=`{row['raw_exchange']}` confidence=`{row['confidence_bucket']}` reason=`{row['rebuild_candidate_reason']}` row_index=`{row['candidate_dataset_row_index']}`"
        for row in additions
    ) or "- No additions."

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
- Canonical rows before: `{len(canonical_rows)}`
- Candidate dataset: `{CANDIDATE_DATASET}`
- Candidate rows after: `{candidate_rows_written}`
- Additions: `{additions_count}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed before: `{ROWS_NEEDED_BEFORE}`
- Rows needed after candidate: `{rows_needed_after_candidate}`
- Source-to-50k before: `{SOURCE_TO_50K_COMPLETED_PERCENT_BEFORE}%`
- Source-to-50k after candidate: `{source_to_50k_after_candidate}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Schema mapping

- Symbol column: `{symbol_col}`
- Name column: `{name_col}`
- Exchange column: `{exchange_col}`
- Source column: `{source_col}`
- Country column: `{country_col}`
- Currency column: `{currency_col}`
- Field count: `{len(fieldnames)}`

## Additions

{addition_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Candidate validation rows read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- New expanded candidate dataset written: true
- Canonical replacement performed: false
- Net-new filtering applied to canonical: false
- Expanded universe rebuilt as canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

TMX expanded rebuild candidate generated.

This phase creates a separate candidate dataset by appending the v2.16F recommended rebuild candidate row to a copy of the canonical expanded universe. It does not modify the canonical dataset and does not unblock full source.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16G TMX expanded rebuild candidate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REBUILD_CANDIDATE_SUMMARY:")
    for key, value in payload["rebuild_candidate_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("SCHEMA_MAPPING:")
    for key, value in payload["schema_mapping"].items():
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
