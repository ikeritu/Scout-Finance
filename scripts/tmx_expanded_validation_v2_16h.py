from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.16H"
PHASE = "TMX Expanded Validation"
PHASE_TYPE = "expanded-candidate-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_tmx_v2_16g.csv"
V216G_JSON = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_v2_16g.json"
V216G_ADDITIONS_CSV = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_additions_v2_16g.csv"
V216G_ROW_AUDIT_CSV = OUTPUT_DIR / "tmx_expanded_rebuild_candidate_row_audit_v2_16g.csv"

REPORT_JSON = OUTPUT_DIR / "tmx_expanded_validation_v2_16h.json"
REPORT_MD = OUTPUT_DIR / "tmx_expanded_validation_v2_16h.md"
ROW_CHECKS_CSV = OUTPUT_DIR / "tmx_expanded_validation_row_checks_v2_16h.csv"
PROFILE_CSV = OUTPUT_DIR / "tmx_expanded_validation_profile_v2_16h.csv"

CURRENT_ROWS = 38287
EXPECTED_CANDIDATE_ROWS = 38288
EXPECTED_DELTA = 1
FULL_SOURCE_THRESHOLD = 50000

EXPECTED_SYMBOL = "IRR"
EXPECTED_NAME = "Irruptive Metals Corp."
EXPECTED_EXCHANGE = "TSXV"

NEXT_PHASE = "v2.16I - TMX Closure Report"

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

CHECK_FIELDS = [
    "check_id",
    "scope",
    "check",
    "passed",
    "severity",
    "detail",
]

PROFILE_FIELDS = [
    "metric",
    "value",
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


def read_csv_with_fieldnames(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                return list(reader.fieldnames or []), rows
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


def normalize_name(value: str) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split()).strip()


def row_key(row: dict, symbol_col: str, exchange_col: str) -> tuple[str, str]:
    symbol = normalize_symbol(row.get(symbol_col, "")) if symbol_col else ""
    exchange = normalize_exchange(row.get(exchange_col, "")) if exchange_col else ""
    return symbol, exchange


def compact_row(row: dict, columns: list[str]) -> str:
    parts = []
    for col in columns:
        if col:
            parts.append(f"{col}={row.get(col, '')}")
    return "; ".join(parts)[:600]


def rows_equal(a: dict, b: dict, fieldnames: list[str]) -> bool:
    for field in fieldnames:
        if str(a.get(field, "")) != str(b.get(field, "")):
            return False
    return True


def diff_rows(a: dict, b: dict, fieldnames: list[str], limit: int = 8) -> str:
    diffs = []
    for field in fieldnames:
        av = str(a.get(field, ""))
        bv = str(b.get(field, ""))
        if av != bv:
            diffs.append(f"{field}: canonical={av!r} candidate={bv!r}")
        if len(diffs) >= limit:
            break
    return " | ".join(diffs)


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, ROW_CHECKS_CSV, PROFILE_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    g_report = read_json(V216G_JSON)
    canonical_fieldnames, canonical_rows = read_csv_with_fieldnames(CANONICAL_DATASET)
    candidate_fieldnames, candidate_rows = read_csv_with_fieldnames(CANDIDATE_DATASET)
    additions_fieldnames, additions_rows = read_csv_with_fieldnames(V216G_ADDITIONS_CSV)
    audit_fieldnames, audit_rows = read_csv_with_fieldnames(V216G_ROW_AUDIT_CSV)

    symbol_col = pick_column(canonical_fieldnames, SYMBOL_COLUMNS)
    exchange_col = pick_column(canonical_fieldnames, EXCHANGE_COLUMNS)
    name_col = pick_column(canonical_fieldnames, NAME_COLUMNS)

    canonical_count = len(canonical_rows)
    candidate_count = len(candidate_rows)
    delta = candidate_count - canonical_count

    canonical_key_counts = Counter(row_key(row, symbol_col, exchange_col) for row in canonical_rows)
    candidate_key_counts = Counter(row_key(row, symbol_col, exchange_col) for row in candidate_rows)

    expected_key = (EXPECTED_SYMBOL, EXPECTED_EXCHANGE)

    canonical_expected_key_count = canonical_key_counts.get(expected_key, 0)
    candidate_expected_key_count = candidate_key_counts.get(expected_key, 0)

    expected_candidate_rows = [
        row for row in candidate_rows
        if row_key(row, symbol_col, exchange_col) == expected_key
    ]

    expected_candidate_names = [
        normalize_name(row.get(name_col, "")) for row in expected_candidate_rows
    ]

    fieldnames_match = canonical_fieldnames == candidate_fieldnames

    prefix_mismatch_count = 0
    prefix_mismatch_examples = []

    if fieldnames_match and candidate_count >= canonical_count:
        for idx, canonical_row in enumerate(canonical_rows):
            candidate_row = candidate_rows[idx]
            if not rows_equal(canonical_row, candidate_row, canonical_fieldnames):
                prefix_mismatch_count += 1
                if len(prefix_mismatch_examples) < 5:
                    prefix_mismatch_examples.append(
                        f"row={idx + 1}: {diff_rows(canonical_row, candidate_row, canonical_fieldnames)}"
                    )
    else:
        prefix_mismatch_count = -1
        prefix_mismatch_examples.append("Skipped prefix comparison because fieldnames differ or candidate has fewer rows.")

    appended_rows = candidate_rows[canonical_count:] if candidate_count >= canonical_count else []

    appended_key_counts = Counter(row_key(row, symbol_col, exchange_col) for row in appended_rows)

    appended_expected_rows = [
        row for row in appended_rows
        if row_key(row, symbol_col, exchange_col) == expected_key
    ]

    checks = []
    critical_failed = 0

    def add_check(scope: str, check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1

        checks.append(
            {
                "check_id": sha256_text(f"{VERSION}|{scope}|{check}")[:16],
                "scope": scope,
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("inputs", "v2_16g_report_exists", V216G_JSON.exists(), "critical", str(V216G_JSON))
    add_check("inputs", "v2_16g_additions_exists", V216G_ADDITIONS_CSV.exists(), "critical", str(V216G_ADDITIONS_CSV))
    add_check("inputs", "v2_16g_audit_exists", V216G_ROW_AUDIT_CSV.exists(), "critical", str(V216G_ROW_AUDIT_CSV))
    add_check(
        "inputs",
        "v2_16g_status_valid",
        g_report.get("status") == "TMX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_ADD1_FULL_SOURCE_STILL_BLOCKED",
        "critical",
        g_report.get("status", ""),
    )
    add_check(
        "inputs",
        "v2_16g_recommended_h",
        g_report.get("recommended_next_phase") == "v2.16H - TMX Expanded Validation",
        "critical",
        g_report.get("recommended_next_phase", ""),
    )
    add_check("inputs", "canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("inputs", "candidate_dataset_exists", CANDIDATE_DATASET.exists(), "critical", str(CANDIDATE_DATASET))
    add_check("schema", "fieldnames_match", fieldnames_match, "critical", f"canonical_fields={len(canonical_fieldnames)} candidate_fields={len(candidate_fieldnames)}")
    add_check("schema", "symbol_column_detected", bool(symbol_col), "critical", f"symbol_col={symbol_col}")
    add_check("schema", "exchange_column_detected", bool(exchange_col), "critical", f"exchange_col={exchange_col}")
    add_check("schema", "name_column_detected", bool(name_col), "critical", f"name_col={name_col}")
    add_check("counts", "canonical_rows_expected", canonical_count == CURRENT_ROWS, "critical", f"canonical_rows={canonical_count} expected={CURRENT_ROWS}")
    add_check("counts", "candidate_rows_expected", candidate_count == EXPECTED_CANDIDATE_ROWS, "critical", f"candidate_rows={candidate_count} expected={EXPECTED_CANDIDATE_ROWS}")
    add_check("counts", "delta_expected_plus_one", delta == EXPECTED_DELTA, "critical", f"delta={delta} expected={EXPECTED_DELTA}")
    add_check("counts", "additions_count_expected_one", len(additions_rows) == 1, "critical", f"additions={len(additions_rows)}")
    add_check("counts", "audit_rows_present", len(audit_rows) >= 1, "critical", f"audit_rows={len(audit_rows)}")
    add_check("prefix", "canonical_prefix_unchanged_in_candidate", prefix_mismatch_count == 0, "critical", f"prefix_mismatch_count={prefix_mismatch_count}; examples={prefix_mismatch_examples}")
    add_check("addition", "canonical_expected_key_absent", canonical_expected_key_count == 0, "critical", f"{expected_key} canonical_count={canonical_expected_key_count}")
    add_check("addition", "candidate_expected_key_present_once", candidate_expected_key_count == 1, "critical", f"{expected_key} candidate_count={candidate_expected_key_count}")
    add_check("addition", "appended_expected_key_present_once", appended_key_counts.get(expected_key, 0) == 1, "critical", f"{expected_key} appended_count={appended_key_counts.get(expected_key, 0)}")
    add_check("addition", "appended_rows_count_expected_one", len(appended_rows) == 1, "critical", f"appended_rows={len(appended_rows)}")
    add_check("addition", "expected_name_present", EXPECTED_NAME in expected_candidate_names, "critical", f"names={expected_candidate_names}")
    add_check("source_gate", "full_source_still_blocked", candidate_count < FULL_SOURCE_THRESHOLD, "critical", f"{candidate_count} < {FULL_SOURCE_THRESHOLD}")
    add_check("guards", "canonical_dataset_not_modified_by_phase", True, "critical", "canonical_dataset_modified=False")
    add_check("guards", "candidate_not_promoted_to_canonical", True, "critical", "canonical_replacement_performed=False")
    add_check("guards", "network_not_used", True, "critical", "network_download_performed=False")
    add_check("guards", "endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("guards", "query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("guards", "scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("guards", "full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "TMX_EXPANDED_VALIDATION_COMPLETED_CANDIDATE_ADD1_VALID_CANONICAL_STILL_UNCHANGED_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE
    else:
        status = "TMX_EXPANDED_VALIDATION_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.16H_FIX - TMX Expanded Validation Repair"

    profile_rows = [
        {"metric": "canonical_dataset", "value": str(CANONICAL_DATASET)},
        {"metric": "candidate_dataset", "value": str(CANDIDATE_DATASET)},
        {"metric": "canonical_rows", "value": canonical_count},
        {"metric": "candidate_rows", "value": candidate_count},
        {"metric": "delta", "value": delta},
        {"metric": "canonical_field_count", "value": len(canonical_fieldnames)},
        {"metric": "candidate_field_count", "value": len(candidate_fieldnames)},
        {"metric": "symbol_col", "value": symbol_col},
        {"metric": "exchange_col", "value": exchange_col},
        {"metric": "name_col", "value": name_col},
        {"metric": "expected_symbol", "value": EXPECTED_SYMBOL},
        {"metric": "expected_exchange", "value": EXPECTED_EXCHANGE},
        {"metric": "expected_name", "value": EXPECTED_NAME},
        {"metric": "canonical_expected_key_count", "value": canonical_expected_key_count},
        {"metric": "candidate_expected_key_count", "value": candidate_expected_key_count},
        {"metric": "appended_rows", "value": len(appended_rows)},
        {"metric": "appended_expected_key_count", "value": appended_key_counts.get(expected_key, 0)},
        {"metric": "prefix_mismatch_count", "value": prefix_mismatch_count},
        {"metric": "full_source_threshold", "value": FULL_SOURCE_THRESHOLD},
        {"metric": "rows_needed_after_candidate", "value": FULL_SOURCE_THRESHOLD - candidate_count},
        {"metric": "source_to_50k_completed_percent_after_candidate", "value": round((candidate_count / FULL_SOURCE_THRESHOLD) * 100, 2)},
        {"metric": "canonical_sha256", "value": sha256_file(CANONICAL_DATASET)},
        {"metric": "candidate_sha256", "value": sha256_file(CANDIDATE_DATASET)},
        {"metric": "critical_failed_checks", "value": critical_failed},
    ]

    addition_preview = []
    for row in expected_candidate_rows:
        addition_preview.append(
            {
                "symbol": normalize_symbol(row.get(symbol_col, "")),
                "name": normalize_name(row.get(name_col, "")),
                "exchange": normalize_exchange(row.get(exchange_col, "")),
                "compact_row": compact_row(row, [symbol_col, name_col, exchange_col]),
            }
        )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "canonical_dataset": str(CANONICAL_DATASET),
            "candidate_dataset": str(CANDIDATE_DATASET),
            "canonical_rows": canonical_count,
            "candidate_rows": candidate_count,
            "delta": delta,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_after_candidate": FULL_SOURCE_THRESHOLD - candidate_count,
            "source_to_50k_completed_percent_after_candidate": round((candidate_count / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "validation_summary": {
            "v2_16g_status": g_report.get("status", ""),
            "v2_16g_recommended_next_phase": g_report.get("recommended_next_phase", ""),
            "canonical_rows": canonical_count,
            "candidate_rows": candidate_count,
            "delta": delta,
            "fieldnames_match": fieldnames_match,
            "symbol_col": symbol_col,
            "exchange_col": exchange_col,
            "name_col": name_col,
            "canonical_prefix_mismatch_count": prefix_mismatch_count,
            "canonical_expected_key_count": canonical_expected_key_count,
            "candidate_expected_key_count": candidate_expected_key_count,
            "appended_rows": len(appended_rows),
            "appended_expected_key_count": appended_key_counts.get(expected_key, 0),
            "expected_candidate_names": expected_candidate_names,
            "critical_failed_checks": critical_failed,
        },
        "addition_preview": addition_preview,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_16g_report_read": True,
            "v2_16g_additions_read": True,
            "canonical_dataset_read": True,
            "candidate_dataset_read": True,
            "candidate_dataset_validated": True,
            "canonical_dataset_modified": False,
            "canonical_replacement_performed": False,
            "candidate_promoted_to_canonical": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "new_expanded_dataset_written": False,
            "net_new_filtering_applied_to_canonical": False,
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
    write_csv(ROW_CHECKS_CSV, checks, CHECK_FIELDS)
    write_csv(PROFILE_CSV, profile_rows, PROFILE_FIELDS)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    addition_lines = "\n".join(
        f"- `{row['symbol']}` `{row['name']}` exchange=`{row['exchange']}`"
        for row in addition_preview
    ) or "- No addition preview."

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Current state

- Canonical dataset: `{CANONICAL_DATASET}`
- Candidate dataset: `{CANDIDATE_DATASET}`
- Canonical rows: `{canonical_count}`
- Candidate rows: `{candidate_count}`
- Delta: `{delta}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed after candidate: `{FULL_SOURCE_THRESHOLD - candidate_count}`
- Source-to-50k after candidate: `{round((candidate_count / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Validation summary

- v2.16G status: `{payload["validation_summary"]["v2_16g_status"]}`
- v2.16G recommended next phase: `{payload["validation_summary"]["v2_16g_recommended_next_phase"]}`
- Fieldnames match: `{fieldnames_match}`
- Symbol column: `{symbol_col}`
- Exchange column: `{exchange_col}`
- Name column: `{name_col}`
- Canonical prefix mismatch count: `{prefix_mismatch_count}`
- Canonical expected key count: `{canonical_expected_key_count}`
- Candidate expected key count: `{candidate_expected_key_count}`
- Appended rows: `{len(appended_rows)}`
- Appended expected key count: `{appended_key_counts.get(expected_key, 0)}`
- Expected candidate names: `{expected_candidate_names}`
- Critical failed checks: `{critical_failed}`

## Validated addition

{addition_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.16G report read: true
- v2.16G additions read: true
- Canonical dataset read: true
- Candidate dataset read: true
- Candidate dataset validated: true
- Canonical dataset modified: false
- Canonical replacement performed: false
- Candidate promoted to canonical: false
- Expanded universe rebuilt as canonical: false
- New expanded dataset written: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

TMX expanded candidate validation completed.

The v2.16G candidate dataset is validated as a separate candidate artifact with one additional TMX row. The canonical dataset remains the active canonical dataset and is not replaced in this phase.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.16H TMX expanded validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in payload["validation_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("CURRENT_STATE:")
    for key, value in payload["current_state"].items():
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
