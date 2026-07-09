from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path


VERSION = "v2.14D4"
PHASE = "Deutsche Boerse Xetra Taxonomy-Corrected Validation"
PHASE_TYPE = "validation-only-taxonomy-corrected"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
D2_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_header_diagnostic_v2_14d2.csv"

JSON_OUT = OUTPUT_DIR / "deutsche_boerse_xetra_taxonomy_validation_v2_14d4.json"
MD_OUT = OUTPUT_DIR / "deutsche_boerse_xetra_taxonomy_validation_v2_14d4.md"
PROJECTION_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_taxonomy_candidate_projection_v2_14d4.csv"
TYPE_COUNTS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_taxonomy_type_counts_v2_14d4.csv"
SAMPLES_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_taxonomy_samples_v2_14d4.csv"

CURRENT_EXPANDED_ROWS = 36863
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 13137

# Conservative Xetra taxonomy discovered from v2.14D3 samples:
# CS is treated as common-stock / share-like candidate.
# ETF/ETN/etc remain excluded.
EQUITY_LIKE_INSTRUMENT_TYPES = {
    "CS",
}

EXCLUDED_INSTRUMENT_TYPES = {
    "ETF",
    "ETN",
    "ETC",
    "ETP",
    "FUND",
    "MF",
    "BOND",
    "WAR",
    "WARRANT",
    "CERT",
    "CERTIFICATE",
    "RIGHT",
    "RIGHTS",
    "FUT",
    "OPT",
    "OPTION",
}

EXCLUDED_GROUP_PREFIXES = {
    "ETF",
    "ETN",
    "ETC",
    "FON",
    "FUND",
    "BON",
    "CRT",
    "WAR",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [JSON_OUT, MD_OUT, PROJECTION_CSV, TYPE_COUNTS_CSV, SAMPLES_CSV]
    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14D4 outputs:\n"
            + "\n".join(existing)
        )


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def compact(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def decode_bytes(data: bytes) -> str:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1", "utf-16"]
    best_text = ""
    best_score = -10**9

    for enc in encodings:
        try:
            text = data.decode(enc, errors="replace")
            score = len(text) - text.count("\ufffd") * 100
            if score > best_score:
                best_text = text
                best_score = score
        except Exception:
            pass

    return best_text


def delimiter_from_repr(value: str) -> str:
    value = str(value or "").strip()
    if value in {"'\\t'", '"\\t"', "\\t"}:
        return "\t"
    if len(value) >= 3 and value[0] in {"'", '"'} and value[-1] == value[0]:
        return value[1:-1]
    return value or ";"


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def find_col(headers: list[str], names: list[str]) -> str:
    for header in headers:
        h_low = header.lower()
        h_cmp = compact(header)
        for name in names:
            if name.lower() in h_low or compact(name) == h_cmp:
                return header
    return ""


def parse_main_all_tradable() -> tuple[dict, list[dict]]:
    if not D2_CSV.exists():
        raise SystemExit(f"Missing D2 diagnostic CSV: {D2_CSV}")

    diagnostic_rows = read_csv_rows(D2_CSV)

    main_rows = [
        row for row in diagnostic_rows
        if "alltradable" in compact(row.get("member", ""))
        or "alltradable" in compact(row.get("source_file", ""))
    ]

    if not main_rows:
        raise SystemExit("No all-tradable diagnostic row found in D2 output.")

    diag = main_rows[0]

    raw_path = Path(diag["source_file"])
    if not raw_path.exists():
        raise SystemExit(f"Main raw file not found: {raw_path}")

    header_line_number = int(diag["header_line_number_one_based"])
    delimiter = delimiter_from_repr(diag["delimiter"])

    text = decode_bytes(raw_path.read_bytes())
    lines = text.splitlines()
    data_text = "\n".join(lines[header_line_number - 1:])

    reader = csv.DictReader(StringIO(data_text), delimiter=delimiter)

    if not reader.fieldnames:
        raise SystemExit("No headers found after corrected header line.")

    headers = [normalize_text(header).replace("\ufeff", "") for header in reader.fieldnames]
    rows = []

    for raw in reader:
        row = {}
        for original, clean in zip(reader.fieldnames, headers):
            row[clean] = normalize_text(raw.get(original, ""))
        rows.append(row)

    return (
        {
            "raw_path": str(raw_path),
            "member": diag["member"],
            "header_line_number_one_based": header_line_number,
            "delimiter": delimiter,
            "headers": headers,
            "row_count": len(rows),
        },
        rows,
    )


def parse_delimited_bytes(data: bytes) -> tuple[list[str], list[dict]]:
    text = decode_bytes(data)
    sample = "\n".join(text.splitlines()[:30])

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ";"

    reader = csv.DictReader(StringIO(text), delimiter=delimiter)

    if not reader.fieldnames:
        return [], []

    headers = [normalize_text(h).replace("\ufeff", "") for h in reader.fieldnames]
    rows = []

    for raw in reader:
        row = {}
        for original, clean in zip(reader.fieldnames, headers):
            row[clean] = normalize_text(raw.get(original, ""))
        rows.append(row)

    return headers, rows


def find_baseline_csv() -> Path | None:
    candidates = []

    for path in OUTPUT_DIR.rglob("*.csv"):
        parts = {part.lower() for part in path.parts}
        name = path.name.lower()

        if "raw" in parts:
            continue
        if "v2_14" in name:
            continue
        if "manifest" in name or "contract" in name or "question" in name:
            continue

        score = 0
        if "v2_13e" in name:
            score += 100
        if "expanded" in name:
            score += 60
        if "universe" in name:
            score += 60
        if "source" in name:
            score += 20

        if score >= 80:
            candidates.append((score, path.stat().st_mtime, path))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][2]


def load_baseline_sets(path: Path | None) -> tuple[set[str], set[str], int]:
    if path is None or not path.exists():
        return set(), set(), 0

    try:
        headers, rows = parse_delimited_bytes(path.read_bytes())
    except Exception:
        return set(), set(), 0

    isin_col = find_col(headers, ["isin"])
    ticker_col = find_col(headers, ["ticker", "symbol", "mnemonic"])
    exchange_col = find_col(headers, ["exchange", "mic", "venue", "market"])

    isins = set()
    exchange_tickers = set()

    for row in rows:
        isin = normalize_text(row.get(isin_col, "")).upper().replace(" ", "") if isin_col else ""
        ticker = normalize_text(row.get(ticker_col, "")).upper().replace(" ", "") if ticker_col else ""
        exchange = normalize_text(row.get(exchange_col, "")).upper().replace(" ", "") if exchange_col else ""

        if isin:
            isins.add(isin)
        if ticker and exchange:
            exchange_tickers.add(f"{exchange}|{ticker}")

    return isins, exchange_tickers, len(rows)


def classify(instrument_type: str, group: str) -> tuple[str, str]:
    typ = normalize_text(instrument_type).upper()
    grp = normalize_text(group).upper()

    if typ in EQUITY_LIKE_INSTRUMENT_TYPES:
        return "equity_like_candidate", "instrument_type_cs"

    if typ in EXCLUDED_INSTRUMENT_TYPES:
        return "excluded_non_common_equity", f"instrument_type_{typ.lower()}"

    for prefix in EXCLUDED_GROUP_PREFIXES:
        if grp.startswith(prefix):
            return "excluded_non_common_equity", f"group_prefix_{prefix.lower()}"

    return "manual_review_unknown_type", "unmapped_taxonomy"


def baseline_status(isin: str, mnemonic: str, baseline_isins: set[str], baseline_exchange_tickers: set[str]) -> str:
    isin = normalize_text(isin).upper().replace(" ", "")
    mnemonic = normalize_text(mnemonic).upper().replace(" ", "")

    if isin and isin in baseline_isins:
        return "already_in_baseline_by_isin"

    possible_keys = [
        f"XETR|{mnemonic}",
        f"XETRA|{mnemonic}",
        f"DEUTSCHE_BOERSE_XETRA|{mnemonic}",
        f"DEUTSCHE BOERSE XETRA|{mnemonic}",
    ]

    if mnemonic and any(key in baseline_exchange_tickers for key in possible_keys):
        return "already_in_baseline_by_exchange_ticker"

    if isin or mnemonic:
        return "diagnostic_not_found_in_baseline"

    return "missing_identifier"


def main() -> None:
    no_overwrite_guard()

    parser_info, rows = parse_main_all_tradable()
    headers = parser_info["headers"]

    isin_col = find_col(headers, ["ISIN"])
    mnemonic_col = find_col(headers, ["Mnemonic"])
    instrument_id_col = find_col(headers, ["Instrument ID", "InstrumentId"])
    group_col = find_col(headers, ["Product Assignment Group Description", "Product Assignment Group"])
    type_col = find_col(headers, ["Instrument Type", "Security Type"])

    baseline_path = find_baseline_csv()
    baseline_isins, baseline_exchange_tickers, baseline_rows = load_baseline_sets(baseline_path)

    classification_counter = Counter()
    reason_counter = Counter()
    baseline_counter = Counter()
    type_counter = Counter()
    group_counter = Counter()

    sample_rows = []

    equity_like_not_found = 0
    equity_like_already_isin = 0
    equity_like_already_exchange_ticker = 0
    equity_like_missing_identifier = 0

    excluded_not_found = 0
    unknown_not_found = 0

    for row in rows:
        isin = normalize_text(row.get(isin_col, "")).upper().replace(" ", "") if isin_col else ""
        mnemonic = normalize_text(row.get(mnemonic_col, "")).upper().replace(" ", "") if mnemonic_col else ""
        instrument_id = normalize_text(row.get(instrument_id_col, "")) if instrument_id_col else ""
        group = normalize_text(row.get(group_col, "")) if group_col else ""
        typ = normalize_text(row.get(type_col, "")) if type_col else ""

        row_class, reason = classify(typ, group)
        b_status = baseline_status(isin, mnemonic, baseline_isins, baseline_exchange_tickers)

        classification_counter[row_class] += 1
        reason_counter[reason] += 1
        baseline_counter[b_status] += 1
        type_counter[typ or "(blank)"] += 1
        group_counter[group or "(blank)"] += 1

        if row_class == "equity_like_candidate":
            if b_status == "diagnostic_not_found_in_baseline":
                equity_like_not_found += 1
            elif b_status == "already_in_baseline_by_isin":
                equity_like_already_isin += 1
            elif b_status == "already_in_baseline_by_exchange_ticker":
                equity_like_already_exchange_ticker += 1
            elif b_status == "missing_identifier":
                equity_like_missing_identifier += 1
        elif row_class == "excluded_non_common_equity" and b_status == "diagnostic_not_found_in_baseline":
            excluded_not_found += 1
        elif row_class == "manual_review_unknown_type" and b_status == "diagnostic_not_found_in_baseline":
            unknown_not_found += 1

        if len(sample_rows) < 500:
            sample_rows.append(
                {
                    "isin": isin,
                    "mnemonic": mnemonic,
                    "instrument_id": instrument_id,
                    "product_assignment_group_description": group,
                    "instrument_type": typ,
                    "classification": row_class,
                    "reason": reason,
                    "baseline_status": b_status,
                }
            )

    gross_rows = len(rows)
    rows_with_isin = sum(1 for row in rows if normalize_text(row.get(isin_col, ""))) if isin_col else 0
    rows_with_mnemonic = sum(1 for row in rows if normalize_text(row.get(mnemonic_col, ""))) if mnemonic_col else 0
    rows_with_instrument_id = sum(1 for row in rows if normalize_text(row.get(instrument_id_col, ""))) if instrument_id_col else 0

    equity_like = classification_counter["equity_like_candidate"]
    excluded = classification_counter["excluded_non_common_equity"]
    unknown = classification_counter["manual_review_unknown_type"]

    projected_rows_after_rebuild = CURRENT_EXPANDED_ROWS + equity_like_not_found
    rows_needed_after_projected_rebuild = max(0, FULL_SOURCE_THRESHOLD - projected_rows_after_rebuild)
    source_to_50k_after_projected_rebuild = round((projected_rows_after_rebuild / FULL_SOURCE_THRESHOLD) * 100, 1)

    projection_rows = [
        {
            "member": parser_info["member"],
            "raw_path": parser_info["raw_path"],
            "header_line_number_one_based": parser_info["header_line_number_one_based"],
            "delimiter": parser_info["delimiter"],
            "gross_rows": gross_rows,
            "rows_with_isin": rows_with_isin,
            "rows_with_mnemonic": rows_with_mnemonic,
            "rows_with_instrument_id": rows_with_instrument_id,
            "equity_like_candidates": equity_like,
            "excluded_non_common_equity": excluded,
            "manual_review_unknown_type": unknown,
            "all_rows_already_in_baseline_by_isin": baseline_counter["already_in_baseline_by_isin"],
            "all_rows_already_in_baseline_by_exchange_ticker": baseline_counter["already_in_baseline_by_exchange_ticker"],
            "all_rows_diagnostic_not_found_in_baseline": baseline_counter["diagnostic_not_found_in_baseline"],
            "all_rows_missing_identifier": baseline_counter["missing_identifier"],
            "equity_like_diagnostic_not_found_in_baseline": equity_like_not_found,
            "equity_like_already_in_baseline_by_isin": equity_like_already_isin,
            "equity_like_already_in_baseline_by_exchange_ticker": equity_like_already_exchange_ticker,
            "equity_like_missing_identifier": equity_like_missing_identifier,
            "excluded_diagnostic_not_found_in_baseline": excluded_not_found,
            "unknown_diagnostic_not_found_in_baseline": unknown_not_found,
            "projected_rows_after_rebuild_if_approved": projected_rows_after_rebuild,
            "rows_needed_after_projected_rebuild": rows_needed_after_projected_rebuild,
            "source_to_50k_after_projected_rebuild_percent": source_to_50k_after_projected_rebuild,
        }
    ]

    type_count_rows = []
    for value, count in type_counter.most_common():
        type_count_rows.append({"field": "Instrument Type", "value": value, "count": count})

    for value, count in group_counter.most_common():
        type_count_rows.append({"field": "Product Assignment Group Description", "value": value, "count": count})

    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("d2_header_diagnostic_exists", D2_CSV.exists(), "critical", str(D2_CSV))
    add_check("corrected_header_used", parser_info["header_line_number_one_based"] > 1, "critical", f"header_line={parser_info['header_line_number_one_based']}")
    add_check("gross_rows_found", gross_rows > 0, "critical", f"gross_rows={gross_rows}")
    add_check("isin_detected", rows_with_isin > 0, "critical", f"rows_with_isin={rows_with_isin}")
    add_check("mnemonic_detected", rows_with_mnemonic > 0, "critical", f"rows_with_mnemonic={rows_with_mnemonic}")
    add_check("instrument_type_detected", bool(type_col), "critical", f"type_col={type_col}")
    add_check("baseline_detected", baseline_path is not None and baseline_rows > 0, "critical", f"baseline_path={baseline_path}; baseline_rows={baseline_rows}")
    add_check("cs_taxonomy_detected", type_counter["CS"] > 0, "critical", f"CS_count={type_counter['CS']}")
    add_check("equity_like_candidates_found", equity_like > 0, "critical", f"equity_like_candidates={equity_like}")
    add_check("equity_like_net_new_found", equity_like_not_found > 0, "critical", f"equity_like_diagnostic_not_found_in_baseline={equity_like_not_found}")
    add_check("non_common_equity_excluded", excluded > 0, "critical", f"excluded_non_common_equity={excluded}")
    add_check("full_source_still_blocked", True, "critical", "full_source_unlocked=False")
    add_check("no_rebuild_performed", True, "critical", "expanded_universe_rebuilt=False")
    add_check("unknown_rows_zero_or_reviewable", unknown >= 0, "warning", f"unknown={unknown}")

    critical_failed = sum(1 for check in checks if check["severity"] == "critical" and not check["passed"])
    warning_failed = sum(1 for check in checks if check["severity"] == "warning" and not check["passed"])

    rebuild_allowed_by_validation = critical_failed == 0

    status = (
        "DEUTSCHE_BOERSE_XETRA_TAXONOMY_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED"
        if rebuild_allowed_by_validation
        else "DEUTSCHE_BOERSE_XETRA_TAXONOMY_VALIDATION_NEEDS_MANUAL_REVIEW_FULL_SOURCE_STILL_BLOCKED"
    )

    recommended_next_phase = (
        "v2.14E - Deutsche Boerse Xetra Expanded Source Rebuild"
        if rebuild_allowed_by_validation
        else "v2.14D-review - Manual Review Before Rebuild"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "selected_provider": "deutsche_boerse_xetra_all_tradable_instruments",
        "taxonomy_decision": {
            "accepted_equity_like_instrument_types": sorted(EQUITY_LIKE_INSTRUMENT_TYPES),
            "excluded_instrument_types": sorted(EXCLUDED_INSTRUMENT_TYPES),
            "excluded_group_prefixes": sorted(EXCLUDED_GROUP_PREFIXES),
            "main_rule": "Only Instrument Type CS is accepted as equity-like candidate in v2.14D4.",
        },
        "rebuild_allowed_by_validation": rebuild_allowed_by_validation,
        "recommended_next_phase": recommended_next_phase,
        "parser": {
            "raw_path": parser_info["raw_path"],
            "member": parser_info["member"],
            "header_line_number_one_based": parser_info["header_line_number_one_based"],
            "delimiter": parser_info["delimiter"],
            "isin_col": isin_col,
            "mnemonic_col": mnemonic_col,
            "instrument_id_col": instrument_id_col,
            "group_col": group_col,
            "type_col": type_col,
        },
        "current_state": {
            "current_expanded_rows": CURRENT_EXPANDED_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
            "full_source_unlocked": False,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "previous_phase_commit": "ac7f238",
        },
        "baseline": {
            "baseline_path": str(baseline_path) if baseline_path else "",
            "baseline_rows": baseline_rows,
            "baseline_isins": len(baseline_isins),
            "baseline_exchange_ticker_keys": len(baseline_exchange_tickers),
        },
        "counts": {
            "gross_rows_read": gross_rows,
            "rows_with_isin": rows_with_isin,
            "rows_with_mnemonic": rows_with_mnemonic,
            "rows_with_instrument_id": rows_with_instrument_id,
            "equity_like_candidates": equity_like,
            "excluded_non_common_equity": excluded,
            "manual_review_unknown_type": unknown,
            "all_rows_already_in_baseline_by_isin": baseline_counter["already_in_baseline_by_isin"],
            "all_rows_already_in_baseline_by_exchange_ticker": baseline_counter["already_in_baseline_by_exchange_ticker"],
            "all_rows_diagnostic_not_found_in_baseline": baseline_counter["diagnostic_not_found_in_baseline"],
            "all_rows_missing_identifier": baseline_counter["missing_identifier"],
            "equity_like_diagnostic_not_found_in_baseline": equity_like_not_found,
            "equity_like_already_in_baseline_by_isin": equity_like_already_isin,
            "equity_like_already_in_baseline_by_exchange_ticker": equity_like_already_exchange_ticker,
            "equity_like_missing_identifier": equity_like_missing_identifier,
            "excluded_diagnostic_not_found_in_baseline": excluded_not_found,
            "unknown_diagnostic_not_found_in_baseline": unknown_not_found,
            "projected_rows_after_rebuild_if_approved": projected_rows_after_rebuild,
            "rows_needed_after_projected_rebuild": rows_needed_after_projected_rebuild,
            "source_to_50k_after_projected_rebuild_percent": source_to_50k_after_projected_rebuild,
            "critical_failed_checks": critical_failed,
            "warning_failed_checks": warning_failed,
        },
        "classification_reason_counts": dict(reason_counter),
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed_for_validation": True,
            "normalization_performed": False,
            "net_new_filtering_finalized": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
    }

    write_json(JSON_OUT, payload)

    write_csv(
        PROJECTION_CSV,
        projection_rows,
        [
            "member",
            "raw_path",
            "header_line_number_one_based",
            "delimiter",
            "gross_rows",
            "rows_with_isin",
            "rows_with_mnemonic",
            "rows_with_instrument_id",
            "equity_like_candidates",
            "excluded_non_common_equity",
            "manual_review_unknown_type",
            "all_rows_already_in_baseline_by_isin",
            "all_rows_already_in_baseline_by_exchange_ticker",
            "all_rows_diagnostic_not_found_in_baseline",
            "all_rows_missing_identifier",
            "equity_like_diagnostic_not_found_in_baseline",
            "equity_like_already_in_baseline_by_isin",
            "equity_like_already_in_baseline_by_exchange_ticker",
            "equity_like_missing_identifier",
            "excluded_diagnostic_not_found_in_baseline",
            "unknown_diagnostic_not_found_in_baseline",
            "projected_rows_after_rebuild_if_approved",
            "rows_needed_after_projected_rebuild",
            "source_to_50k_after_projected_rebuild_percent",
        ],
    )

    write_csv(TYPE_COUNTS_CSV, type_count_rows, ["field", "value", "count"])

    write_csv(
        SAMPLES_CSV,
        sample_rows,
        [
            "isin",
            "mnemonic",
            "instrument_id",
            "product_assignment_group_description",
            "instrument_type",
            "classification",
            "reason",
            "baseline_status",
        ],
    )

    check_lines = "\n".join(
        f"- {check['check']}: {'PASS' if check['passed'] else 'FAIL'} ({check['severity']}) — {check['detail']}"
        for check in checks
    )

    top_types = "\n".join(
        f"- {value}: {count}"
        for value, count in type_counter.most_common(20)
    )

    top_groups = "\n".join(
        f"- {value}: {count}"
        for value, count in group_counter.most_common(20)
    )

    MD_OUT.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **validation-only-taxonomy-corrected**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `{payload["generated_at_utc"]}`

## Decision

- Rebuild allowed by validation: **{str(rebuild_allowed_by_validation).lower()}**
- Recommended next phase: **{recommended_next_phase}**
- Full source unlocked: **false**
- Full 59k: **blocked**

## Taxonomy decision

Only `Instrument Type = CS` is accepted as equity-like candidate in v2.14D4.

ETF, ETN, ETC, ETP, funds, bonds, warrants, certificates, rights, futures and options remain excluded.

## Counts

- Gross rows read: {gross_rows}
- Rows with ISIN: {rows_with_isin}
- Rows with mnemonic: {rows_with_mnemonic}
- Rows with instrument ID: {rows_with_instrument_id}
- Equity-like candidates: {equity_like}
- Excluded non-common-equity: {excluded}
- Manual review unknown type: {unknown}
- Equity-like diagnostic not found in baseline: {equity_like_not_found}
- Equity-like already in baseline by ISIN: {equity_like_already_isin}
- Projected rows after rebuild if approved: {projected_rows_after_rebuild}
- Rows needed after projected rebuild: {rows_needed_after_projected_rebuild}
- Source-to-50k after projected rebuild: {source_to_50k_after_projected_rebuild}%
- Critical failed checks: {critical_failed}
- Warning failed checks: {warning_failed}

## Top Instrument Type values

{top_types}

## Top Product Assignment Group Description values

{top_groups}

## Baseline

- Baseline path: `{payload["baseline"]["baseline_path"]}`
- Baseline rows: {baseline_rows}
- Baseline ISIN keys: {len(baseline_isins)}
- Baseline exchange+ticker keys: {len(baseline_exchange_tickers)}

## Checks

{check_lines}

## Guards

- Network download performed in v2.14D4: false
- Raw files downloaded in v2.14D4: false
- Raw files modified after write: false
- Workbook/CSV parsed for validation: true
- Normalization performed: false
- Final net-new filtering finalized: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase validates taxonomy and projection only. It does not create a new expanded source universe.
""",
        encoding="utf-8",
    )

    print("v2.14D4 taxonomy-corrected validation completed.")
    print(f"- json: {JSON_OUT}")
    print(f"- report: {MD_OUT}")
    print(f"- projection: {PROJECTION_CSV}")
    print(f"- type counts: {TYPE_COUNTS_CSV}")
    print(f"- samples: {SAMPLES_CSV}")
    print("")
    print("DECISION:")
    print(f"- status: {status}")
    print(f"- rebuild_allowed_by_validation: {rebuild_allowed_by_validation}")
    print(f"- recommended_next_phase: {recommended_next_phase}")
    print("")
    print("COUNTS:")
    for key, value in payload["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
