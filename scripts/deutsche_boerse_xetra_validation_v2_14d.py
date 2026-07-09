from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import Iterable


VERSION = "v2.14D"
PHASE = "Deutsche Boerse Xetra Validation"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

MANIFEST_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_download_manifest_v2_14c.json"

VALIDATION_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_validation_v2_14d.json"
VALIDATION_MD = OUTPUT_DIR / "deutsche_boerse_xetra_validation_v2_14d.md"
FILE_INVENTORY_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_validation_file_inventory_v2_14d.csv"
CANDIDATE_PROJECTION_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_validation_candidate_projection_v2_14d.csv"
SAMPLES_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_validation_samples_v2_14d.csv"

CURRENT_EXPANDED_ROWS = 36863
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 13137

NON_EQUITY_PATTERNS = [
    ("etf", r"\betf\b|exchange traded fund|active etf"),
    ("etn", r"\betn\b|exchange traded note"),
    ("etc", r"\betc\b|exchange traded commodit"),
    ("etp", r"\betp\b|exchange traded product"),
    ("fund", r"\bfund\b|\bfonds\b|investment fund|mutual fund"),
    ("bond", r"\bbond\b|\banleihe\b|fixed income|debt"),
    ("certificate", r"certificate|zertifikat|certificat"),
    ("warrant", r"warrant|optionsschein"),
    ("derivative", r"future|option|derivative|swap"),
    ("commodity", r"commodity|rohstoff"),
    ("crypto", r"crypto|bitcoin|ethereum"),
    ("index", r"\bindex\b|indice"),
    ("reit", r"\breit\b|real estate investment trust"),
    ("rights_or_units", r"subscription right|rights issue|\bright\b|\bunit\b"),
    ("depositary_receipt", r"depositary receipt|\badr\b|\bgdr\b"),
]

EQUITY_PATTERNS = [
    r"\bequity\b",
    r"\bshare\b",
    r"\bshares\b",
    r"\bstock\b",
    r"\bcommon\b",
    r"\bordinary\b",
    r"\bregistered shares?\b",
    r"\bbearer shares?\b",
    r"\baktie\b",
    r"\baktien\b",
    r"\bstammaktie\b",
    r"\bvorzugsaktie\b",
    r"\binhaber-?aktien\b",
    r"\bnamens-?aktien\b",
    r"\bstk\b",
]

DATA_EXTENSIONS = {".csv", ".txt", ".dat", ".tsv"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        VALIDATION_JSON,
        VALIDATION_MD,
        FILE_INVENTORY_CSV,
        CANDIDATE_PROJECTION_CSV,
        SAMPLES_CSV,
    ]
    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14D outputs:\n"
            + "\n".join(existing)
        )


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_key(value: object) -> str:
    return normalize_text(value).lower()


def decode_bytes(data: bytes) -> str:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1", "utf-16"]
    best = None
    best_score = -1

    for encoding in encodings:
        try:
            text = data.decode(encoding, errors="replace")
            score = len(text) - text.count("\ufffd") * 10
            if score > best_score:
                best = text
                best_score = score
        except Exception:
            continue

    return best or data.decode("latin-1", errors="replace")


def detect_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:25])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except Exception:
        counts = {delimiter: sample.count(delimiter) for delimiter in [",", ";", "\t", "|"]}
        return max(counts, key=counts.get)


def normalize_headers(headers: Iterable[str]) -> list[str]:
    result = []
    for header in headers:
        clean = normalize_text(header).replace("\ufeff", "")
        result.append(clean)
    return result


def parse_delimited_bytes(data: bytes) -> tuple[list[str], list[dict]]:
    text = decode_bytes(data)
    delimiter = detect_delimiter(text)
    reader = csv.DictReader(StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        return [], []

    original_headers = normalize_headers(reader.fieldnames)
    rows = []

    for raw_row in reader:
        row = {}
        for original, clean in zip(reader.fieldnames, original_headers):
            row[clean] = normalize_text(raw_row.get(original, ""))
        rows.append(row)

    return original_headers, rows


def header_contains(header: str, patterns: list[str]) -> bool:
    low = header.lower()
    return any(pattern in low for pattern in patterns)


def find_first_header(headers: list[str], patterns: list[str], exclude: list[str] | None = None) -> str:
    exclude = exclude or []
    for header in headers:
        low = header.lower()
        if any(token in low for token in exclude):
            continue
        if any(pattern in low for pattern in patterns):
            return header
    return ""


def find_headers(headers: list[str], patterns: list[str]) -> list[str]:
    return [header for header in headers if header_contains(header, patterns)]


def extract_isin(row: dict, headers: list[str]) -> str:
    col = find_first_header(headers, ["isin"])
    value = normalize_text(row.get(col, "")) if col else ""
    value = value.upper().replace(" ", "")
    return value if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", value or "") else value


def extract_ticker(row: dict, headers: list[str]) -> str:
    ticker_col = find_first_header(
        headers,
        ["mnemonic", "symbol", "ticker", "trading code", "instrument code", "instrument id", "product id"],
        exclude=["isin", "wkn"],
    )
    value = normalize_text(row.get(ticker_col, "")) if ticker_col else ""
    return value.upper().replace(" ", "")


def extract_name(row: dict, headers: list[str]) -> str:
    name_col = find_first_header(headers, ["instrument name", "security name", "name", "issuer", "short name"])
    return normalize_text(row.get(name_col, "")) if name_col else ""


def extract_type_text(row: dict, headers: list[str]) -> str:
    type_cols = find_headers(
        headers,
        [
            "instrument type",
            "security type",
            "product type",
            "product category",
            "asset class",
            "segment",
            "market segment",
            "class",
            "category",
            "type",
            "market",
        ],
    )
    values = [normalize_text(row.get(col, "")) for col in type_cols if normalize_text(row.get(col, ""))]
    return " | ".join(values)


def classify_row(row: dict, headers: list[str]) -> tuple[str, str]:
    name = extract_name(row, headers)
    type_text = extract_type_text(row, headers)
    searchable = f"{type_text} | {name}".lower()

    for reason, pattern in NON_EQUITY_PATTERNS:
        if re.search(pattern, searchable, flags=re.I):
            return "excluded_non_common_equity", reason

    for pattern in EQUITY_PATTERNS:
        if re.search(pattern, searchable, flags=re.I):
            return "equity_like_candidate", "equity_pattern"

    return "manual_review_unknown_type", "insufficient_type_signal"


def find_baseline_csv() -> Path | None:
    candidates = []
    for path in OUTPUT_DIR.rglob("*.csv"):
        parts = {part.lower() for part in path.parts}
        name = path.name.lower()

        if "raw" in parts:
            continue
        if "v2_14d" in name or "v2_14c" in name or "manifest" in name or "contract" in name:
            continue
        if "candidate" in name or "planned" in name or "links" in name or "question" in name:
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
        if "v2_13" in name:
            score += 10

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

    isin_col = find_first_header(headers, ["isin"])
    ticker_col = find_first_header(headers, ["ticker", "symbol", "mnemonic"], exclude=["isin", "wkn"])
    exchange_col = find_first_header(headers, ["exchange", "mic", "venue", "market"])

    isins = set()
    exchange_tickers = set()

    for row in rows:
        isin = normalize_text(row.get(isin_col, "")).upper().replace(" ", "") if isin_col else ""
        if isin:
            isins.add(isin)

        ticker = normalize_text(row.get(ticker_col, "")).upper().replace(" ", "") if ticker_col else ""
        exchange = normalize_text(row.get(exchange_col, "")).upper().replace(" ", "") if exchange_col else ""

        if ticker and exchange:
            exchange_tickers.add(f"{exchange}|{ticker}")

    return isins, exchange_tickers, len(rows)


def diagnostic_baseline_status(isin: str, ticker: str, baseline_isins: set[str], baseline_exchange_tickers: set[str]) -> str:
    if isin and isin in baseline_isins:
        return "already_in_baseline_by_isin"

    possible_exchange_keys = [
        f"XETR|{ticker}",
        f"XETRA|{ticker}",
        f"DEUTSCHE_BOERSE_XETRA|{ticker}",
        f"DEUTSCHE BOERSE XETRA|{ticker}",
    ]

    if ticker and any(key in baseline_exchange_tickers for key in possible_exchange_keys):
        return "already_in_baseline_by_exchange_ticker"

    if isin or ticker:
        return "diagnostic_not_found_in_baseline"

    return "missing_identifier"


def iter_dataset_payloads(raw_path: Path) -> list[tuple[str, bytes]]:
    suffix = raw_path.suffix.lower()

    if suffix == ".zip":
        payloads = []
        with zipfile.ZipFile(raw_path, "r") as zf:
            for member in zf.infolist():
                member_suffix = Path(member.filename).suffix.lower()
                if member.is_dir():
                    continue
                if member_suffix in DATA_EXTENSIONS:
                    payloads.append((member.filename, zf.read(member)))
        return payloads

    if suffix in DATA_EXTENSIONS or suffix == "":
        return [(raw_path.name, raw_path.read_bytes())]

    return []


def main() -> None:
    no_overwrite_guard()

    manifest = read_json(MANIFEST_JSON)
    dataset_rows = manifest.get("dataset_candidate_manifest", [])

    baseline_path = find_baseline_csv()
    baseline_isins, baseline_exchange_tickers, baseline_rows = load_baseline_sets(baseline_path)

    inventory_rows: list[dict] = []
    projection_rows: list[dict] = []
    sample_rows: list[dict] = []

    total_structured_rows = 0
    total_parse_successes = 0
    total_equity_like = 0
    total_unknown = 0
    total_non_equity = 0
    total_not_found_in_baseline = 0
    total_already_by_isin = 0
    total_already_by_exchange_ticker = 0

    exclusion_counter = Counter()

    for ds in dataset_rows:
        raw_path_text = ds.get("raw_path", "")
        raw_path = Path(raw_path_text)

        inventory_base = {
            "source_page_id": ds.get("source_page_id", ""),
            "candidate_index": ds.get("candidate_index", ""),
            "url": ds.get("url", ""),
            "raw_path": raw_path_text,
            "raw_exists": str(raw_path.exists()),
            "raw_bytes": raw_path.stat().st_size if raw_path.exists() else 0,
            "content_type": ds.get("content_type", ""),
            "status_code": ds.get("status_code", ""),
        }

        if not raw_path.exists():
            inventory_rows.append({**inventory_base, "member": "", "parse_status": "missing_raw_file", "headers": "", "row_count": 0})
            continue

        try:
            payloads = iter_dataset_payloads(raw_path)
        except Exception as exc:
            inventory_rows.append({**inventory_base, "member": "", "parse_status": f"payload_error:{type(exc).__name__}", "headers": "", "row_count": 0})
            continue

        if not payloads:
            inventory_rows.append({**inventory_base, "member": "", "parse_status": "no_supported_structured_member", "headers": "", "row_count": 0})
            continue

        for member_name, payload in payloads:
            try:
                headers, rows = parse_delimited_bytes(payload)
                parse_status = "parsed_for_validation"
                total_parse_successes += 1
            except Exception as exc:
                headers, rows = [], []
                parse_status = f"parse_error:{type(exc).__name__}"

            row_count = len(rows)
            total_structured_rows += row_count

            inventory_rows.append(
                {
                    **inventory_base,
                    "member": member_name,
                    "parse_status": parse_status,
                    "headers": " | ".join(headers[:80]),
                    "row_count": row_count,
                }
            )

            classification_counter = Counter()
            baseline_counter = Counter()

            for row in rows:
                isin = extract_isin(row, headers)
                ticker = extract_ticker(row, headers)
                name = extract_name(row, headers)
                type_text = extract_type_text(row, headers)
                classification, reason = classify_row(row, headers)

                baseline_status = diagnostic_baseline_status(
                    isin,
                    ticker,
                    baseline_isins,
                    baseline_exchange_tickers,
                )

                classification_counter[classification] += 1
                baseline_counter[baseline_status] += 1
                exclusion_counter[reason] += 1

                if classification == "equity_like_candidate":
                    total_equity_like += 1
                elif classification == "excluded_non_common_equity":
                    total_non_equity += 1
                else:
                    total_unknown += 1

                if baseline_status == "diagnostic_not_found_in_baseline":
                    total_not_found_in_baseline += 1
                elif baseline_status == "already_in_baseline_by_isin":
                    total_already_by_isin += 1
                elif baseline_status == "already_in_baseline_by_exchange_ticker":
                    total_already_by_exchange_ticker += 1

                if len(sample_rows) < 300 and (
                    classification == "equity_like_candidate"
                    or classification == "excluded_non_common_equity"
                    or baseline_status == "diagnostic_not_found_in_baseline"
                ):
                    sample_rows.append(
                        {
                            "raw_path": raw_path_text,
                            "member": member_name,
                            "isin": isin,
                            "ticker": ticker,
                            "company_name": name,
                            "instrument_type_text": type_text,
                            "classification": classification,
                            "reason": reason,
                            "baseline_status": baseline_status,
                        }
                    )

            projection_rows.append(
                {
                    "raw_path": raw_path_text,
                    "member": member_name,
                    "row_count": row_count,
                    "classification_equity_like_candidate": classification_counter["equity_like_candidate"],
                    "classification_excluded_non_common_equity": classification_counter["excluded_non_common_equity"],
                    "classification_manual_review_unknown_type": classification_counter["manual_review_unknown_type"],
                    "baseline_already_in_by_isin": baseline_counter["already_in_baseline_by_isin"],
                    "baseline_already_in_by_exchange_ticker": baseline_counter["already_in_baseline_by_exchange_ticker"],
                    "baseline_diagnostic_not_found": baseline_counter["diagnostic_not_found_in_baseline"],
                    "baseline_missing_identifier": baseline_counter["missing_identifier"],
                }
            )

    checks = []

    def add_check(name: str, passed: bool, severity: str, detail: str) -> None:
        checks.append(
            {
                "check": name,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("v2_14c_manifest_exists", MANIFEST_JSON.exists(), "critical", str(MANIFEST_JSON))
    add_check("dataset_candidates_downloaded", len(dataset_rows) > 0, "critical", f"dataset_candidate_manifest={len(dataset_rows)}")
    add_check("structured_payloads_parsed", total_parse_successes > 0, "critical", f"parse_successes={total_parse_successes}")
    add_check("structured_rows_found", total_structured_rows > 0, "critical", f"structured_rows={total_structured_rows}")
    add_check("baseline_detected", baseline_path is not None and baseline_rows > 0, "critical", f"baseline_path={baseline_path}; baseline_rows={baseline_rows}")
    add_check("equity_like_candidates_found", total_equity_like > 0, "critical", f"equity_like_candidates={total_equity_like}")
    add_check("full_source_still_blocked", True, "critical", "full_source_unlocked=False")
    add_check("no_rebuild_performed", True, "critical", "expanded_universe_rebuilt=False")
    add_check("non_equity_filter_needed", total_non_equity > 0 or total_unknown > 0, "warning", f"non_equity={total_non_equity}; unknown={total_unknown}")

    critical_failed = sum(1 for check in checks if check["severity"] == "critical" and not check["passed"])
    warning_failed = sum(1 for check in checks if check["severity"] == "warning" and not check["passed"])

    rebuild_allowed_by_validation = critical_failed == 0

    status = (
        "DEUTSCHE_BOERSE_XETRA_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED"
        if rebuild_allowed_by_validation
        else "DEUTSCHE_BOERSE_XETRA_VALIDATION_NEEDS_MANUAL_REVIEW_FULL_SOURCE_STILL_BLOCKED"
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
        "rebuild_allowed_by_validation": rebuild_allowed_by_validation,
        "recommended_next_phase": recommended_next_phase,
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
            "dataset_candidates_from_manifest": len(dataset_rows),
            "structured_payloads_parsed_for_validation": total_parse_successes,
            "gross_structured_rows_read": total_structured_rows,
            "equity_like_candidates": total_equity_like,
            "excluded_non_common_equity_or_non_share": total_non_equity,
            "manual_review_unknown_type": total_unknown,
            "diagnostic_not_found_in_baseline": total_not_found_in_baseline,
            "already_in_baseline_by_isin": total_already_by_isin,
            "already_in_baseline_by_exchange_ticker": total_already_by_exchange_ticker,
            "critical_failed_checks": critical_failed,
            "warning_failed_checks": warning_failed,
        },
        "exclusion_reason_counts": dict(exclusion_counter),
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed_for_validation": total_parse_successes > 0,
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

    write_json(VALIDATION_JSON, payload)

    write_csv(
        FILE_INVENTORY_CSV,
        inventory_rows,
        [
            "source_page_id",
            "candidate_index",
            "url",
            "raw_path",
            "raw_exists",
            "raw_bytes",
            "content_type",
            "status_code",
            "member",
            "parse_status",
            "headers",
            "row_count",
        ],
    )

    write_csv(
        CANDIDATE_PROJECTION_CSV,
        projection_rows,
        [
            "raw_path",
            "member",
            "row_count",
            "classification_equity_like_candidate",
            "classification_excluded_non_common_equity",
            "classification_manual_review_unknown_type",
            "baseline_already_in_by_isin",
            "baseline_already_in_by_exchange_ticker",
            "baseline_diagnostic_not_found",
            "baseline_missing_identifier",
        ],
    )

    write_csv(
        SAMPLES_CSV,
        sample_rows,
        [
            "raw_path",
            "member",
            "isin",
            "ticker",
            "company_name",
            "instrument_type_text",
            "classification",
            "reason",
            "baseline_status",
        ],
    )

    checks_lines = "\n".join(
        f"- {check['check']}: {'PASS' if check['passed'] else 'FAIL'} ({check['severity']}) — {check['detail']}"
        for check in checks
    )

    projection_lines = "\n".join(
        f"- `{row['member']}` rows={row['row_count']} equity_like={row['classification_equity_like_candidate']} "
        f"excluded={row['classification_excluded_non_common_equity']} unknown={row['classification_manual_review_unknown_type']} "
        f"diagnostic_not_found={row['baseline_diagnostic_not_found']}"
        for row in projection_rows
    )

    md = f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **validation-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `{payload["generated_at_utc"]}`

## Decision

- Rebuild allowed by validation: **{str(rebuild_allowed_by_validation).lower()}**
- Recommended next phase: **{recommended_next_phase}**
- Full source unlocked: **false**
- Full 59k: **blocked**

## Baseline

- Baseline path: `{payload["baseline"]["baseline_path"]}`
- Baseline rows: {baseline_rows}
- Baseline ISIN keys: {len(baseline_isins)}
- Baseline exchange+ticker keys: {len(baseline_exchange_tickers)}

## Counts

- Dataset candidates from manifest: {len(dataset_rows)}
- Structured payloads parsed for validation: {total_parse_successes}
- Gross structured rows read: {total_structured_rows}
- Equity-like candidates: {total_equity_like}
- Excluded non-common-equity / non-share: {total_non_equity}
- Manual review unknown type: {total_unknown}
- Diagnostic not found in baseline: {total_not_found_in_baseline}
- Already in baseline by ISIN: {total_already_by_isin}
- Already in baseline by exchange+ticker: {total_already_by_exchange_ticker}
- Critical failed checks: {critical_failed}
- Warning failed checks: {warning_failed}

## Checks

{checks_lines}

## Dataset projection

{projection_lines}

## Guards

- Network download performed in v2.14D: false
- Raw files downloaded in v2.14D: false
- Raw files modified after write: false
- Workbook/CSV parsed for validation: {str(total_parse_successes > 0).lower()}
- Normalization performed: false
- Final net-new filtering finalized: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase produces validation diagnostics only. It does not create a new expanded source universe.
"""

    if VALIDATION_MD.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {VALIDATION_MD}")
    VALIDATION_MD.write_text(md, encoding="utf-8")

    print("v2.14D Deutsche Boerse Xetra validation-only completed.")
    print(f"- validation json: {VALIDATION_JSON}")
    print(f"- validation report: {VALIDATION_MD}")
    print(f"- file inventory csv: {FILE_INVENTORY_CSV}")
    print(f"- candidate projection csv: {CANDIDATE_PROJECTION_CSV}")
    print(f"- samples csv: {SAMPLES_CSV}")
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
    print("BASELINE:")
    for key, value in payload["baseline"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
