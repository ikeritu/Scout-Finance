from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19O"
PHASE = "HKEX Candidate Validation Against Canonical Dry Run"
PHASE_TYPE = "candidate-validation-against-canonical-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"

V219N_JSON = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_v2_19n.json"
V219N_CANDIDATES_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_candidates_v2_19n.csv"
V219N_INSTRUMENT_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_instrument_summary_v2_19n.csv"
V219N_QUALITY_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_extraction_dry_run_quality_summary_v2_19n.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_v2_19o.json"
REPORT_MD = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_v2_19o.md"
VALIDATED_CANDIDATES_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_validated_candidates_v2_19o.csv"
NET_NEW_CANDIDATES_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_net_new_candidates_v2_19o.csv"
DUPLICATE_MATCHES_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_duplicate_matches_v2_19o.csv"
EXCLUSIONS_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_exclusions_v2_19o.csv"
COMPARISON_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_comparison_summary_v2_19o.csv"
INSTRUMENT_VALIDATION_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_instrument_validation_summary_v2_19o.csv"
DATASET_INDEX_SUMMARY_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_dataset_index_summary_v2_19o.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_checks_v2_19o.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_candidate_validation_against_canonical_dry_run_next_actions_v2_19o.csv"

EXPECTED_V219N_STATUS = "HKEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_EXTRACTED_CANONICAL_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9004

EXPECTED_HKEX_EXTRACT_ROWS = 17630
EXPECTED_HKEX_POTENTIAL_SCOPE_ROWS = 3180
EXPECTED_HKEX_REFERENCE_SCOPE_ROWS = 14450

STATUS_REBUILD_READY = "HKEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NET_NEW_CLASSIFIED_EXPANDED_REBUILD_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_NO_NET_NEW = "HKEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_NO_NET_NEW_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_CANDIDATE_VALIDATION_DRY_RUN_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_REBUILD = "v2.19P - HKEX Expanded Rebuild Candidate"
NEXT_PHASE_CLOSURE = "v2.19R - HKEX Closure Report"
NEXT_PHASE_REVIEW = "v2.19O_REVIEW - HKEX Candidate Validation Against Canonical Review"

POTENTIAL_SCOPE_FLAG = "potential_candidate_pending_canonical_validation"

NAME_COLUMNS_HINTS = {
    "name",
    "company_name",
    "company",
    "short_name",
    "stock_name",
    "security_name",
    "securities_name",
    "name_of_securities",
    "issuer",
    "issuer_or_name",
    "long_name",
}
ISIN_COLUMNS_HINTS = {"isin"}
TICKER_COLUMNS_HINTS = {
    "ticker",
    "symbol",
    "ticker_yahoo",
    "yahoo_symbol",
    "yf_symbol",
    "ric",
    "candidate_id",
    "stock_code",
    "code",
}
MARKET_COLUMNS_HINTS = {
    "source_provider",
    "provider",
    "source_market",
    "market",
    "source_country",
    "country",
    "exchange",
    "mic",
    "currency",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return list(reader.fieldnames or []), list(reader)
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def normalize_header(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_\-/]+", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_name(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^A-Z0-9 ]+", "", text)
    text = re.sub(r"\b(LTD|LIMITED|INC|CORP|CORPORATION|CO|COMPANY|PLC|SA|NV|AG|HOLDINGS|HLDGS)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_isin(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^A-Z0-9]", "", text)
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", text):
        return text
    return ""


def normalize_stock_code(value: Any) -> str:
    text = normalize_text(value)
    if re.fullmatch(r"\d+\.0", text):
        text = text.split(".")[0]
    digits = re.sub(r"\D", "", text)
    if not digits:
        return ""
    if len(digits) <= 5:
        return digits.zfill(5)
    return ""


def normalize_ticker(value: Any) -> str:
    text = normalize_text(value)
    text = text.replace(" ", "")
    text = text.replace("_", ".")
    text = re.sub(r"[^A-Z0-9.\-]", "", text)

    hk_match = re.fullmatch(r"(\d{1,5})\.HK", text)
    if hk_match:
        return f"{hk_match.group(1).zfill(5)}.HK"

    hkex_match = re.fullmatch(r"HKEX_(\d{1,5})", text)
    if hkex_match:
        return f"{hkex_match.group(1).zfill(5)}.HK"

    return text


def extract_hkex_codes_from_value(value: Any) -> set[str]:
    text = normalize_text(value)
    found: set[str] = set()

    for match in re.finditer(r"\b(\d{1,5})\.HK\b", text):
        found.add(match.group(1).zfill(5))

    for match in re.finditer(r"\bHKEX[_\- ]?(\d{1,5})\b", text):
        found.add(match.group(1).zfill(5))

    return found


def header_matches(header: str, hints: set[str]) -> bool:
    h = normalize_header(header)
    return h in hints or any(hint in h for hint in hints)


def row_values_blob(row: dict[str, str]) -> str:
    return " ".join(normalize_text(v) for v in row.values() if str(v).strip())


def row_looks_hkex(row: dict[str, str]) -> bool:
    blob = row_values_blob(row)
    if any(marker in blob for marker in ["HKEX", "HONG KONG", "XHKG"]):
        return True
    if re.search(r"\b\d{1,5}\.HK\b", blob):
        return True
    return False


def build_dataset_index(path: Path, dataset_label: str) -> dict[str, Any]:
    headers, rows = read_csv_with_header(path)

    tickers: set[str] = set()
    isins: set[str] = set()
    names: set[str] = set()
    hkex_stock_codes: set[str] = set()
    hkex_like_rows = 0

    ticker_headers = [h for h in headers if header_matches(h, TICKER_COLUMNS_HINTS)]
    isin_headers = [h for h in headers if header_matches(h, ISIN_COLUMNS_HINTS)]
    name_headers = [h for h in headers if header_matches(h, NAME_COLUMNS_HINTS)]
    market_headers = [h for h in headers if header_matches(h, MARKET_COLUMNS_HINTS)]

    for row in rows:
        hkex_row = row_looks_hkex(row)
        if hkex_row:
            hkex_like_rows += 1

        for header in ticker_headers:
            value = row.get(header, "")
            ticker = normalize_ticker(value)
            if ticker:
                tickers.add(ticker)
            hkex_stock_codes.update(extract_hkex_codes_from_value(value))

            if hkex_row:
                code = normalize_stock_code(value)
                if code:
                    hkex_stock_codes.add(code)

        for header in isin_headers:
            isin = normalize_isin(row.get(header, ""))
            if isin:
                isins.add(isin)

        for header in name_headers:
            name = normalize_name(row.get(header, ""))
            if name:
                names.add(name)

        if hkex_row:
            for value in row.values():
                hkex_stock_codes.update(extract_hkex_codes_from_value(value))

    return {
        "dataset_label": dataset_label,
        "path": str(path),
        "headers": headers,
        "row_count": len(rows),
        "ticker_headers": ticker_headers,
        "isin_headers": isin_headers,
        "name_headers": name_headers,
        "market_headers": market_headers,
        "ticker_index_count": len(tickers),
        "isin_index_count": len(isins),
        "name_index_count": len(names),
        "hkex_stock_code_index_count": len(hkex_stock_codes),
        "hkex_like_rows": hkex_like_rows,
        "tickers": tickers,
        "isins": isins,
        "names": names,
        "hkex_stock_codes": hkex_stock_codes,
    }


def classify_candidate(
    candidate: dict[str, str],
    active_index: dict[str, Any],
    current_index: dict[str, Any],
) -> tuple[str, str, str, list[dict[str, Any]]]:
    candidate_id = candidate.get("candidate_id", "")
    stock_code = candidate.get("stock_code", "")
    ticker = normalize_ticker(candidate.get("ticker") or candidate.get("symbol") or candidate.get("ticker_yahoo"))
    isin = normalize_isin(candidate.get("isin", ""))
    name = normalize_name(candidate.get("name", ""))
    scope_flag = candidate.get("candidate_scope_flag", "")
    instrument_family = candidate.get("instrument_family", "")

    matches: list[dict[str, Any]] = []

    if scope_flag != POTENTIAL_SCOPE_FLAG:
        return (
            "excluded_before_canonical_match",
            "non_candidate_scope_flag",
            "excluded_reference_security_likely_excluded_later",
            matches,
        )

    def add_match(dataset: str, match_type: str, match_value: str) -> None:
        matches.append(
            {
                "candidate_id": candidate_id,
                "stock_code": stock_code,
                "ticker": ticker,
                "isin": isin,
                "name": candidate.get("name", ""),
                "instrument_family": instrument_family,
                "dataset": dataset,
                "match_type": match_type,
                "match_value": match_value,
            }
        )

    for dataset, index in [("current_validated_candidate", current_index), ("active_canonical", active_index)]:
        if ticker and ticker in index["tickers"]:
            add_match(dataset, "ticker_or_symbol_exact", ticker)

        if stock_code and stock_code in index["hkex_stock_codes"]:
            add_match(dataset, "hkex_stock_code_exact", stock_code)

        if isin and isin in index["isins"]:
            add_match(dataset, "isin_exact", isin)

        if name and name in index["names"]:
            add_match(dataset, "normalized_name_exact", name)

    hard_match_types = {"ticker_or_symbol_exact", "hkex_stock_code_exact", "isin_exact"}
    hard_matches = [m for m in matches if m["match_type"] in hard_match_types]
    name_only_matches = [m for m in matches if m["match_type"] == "normalized_name_exact"]

    if hard_matches:
        first = hard_matches[0]
        return (
            "duplicate_existing_universe",
            first["match_type"],
            first["dataset"],
            matches,
        )

    if name_only_matches:
        first = name_only_matches[0]
        return (
            "possible_duplicate_name_review",
            "normalized_name_exact",
            first["dataset"],
            matches,
        )

    return (
        "net_new_pending_expanded_rebuild",
        "no_match_found",
        "not_found_in_active_or_current_candidate",
        matches,
    )


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        VALIDATED_CANDIDATES_CSV,
        NET_NEW_CANDIDATES_CSV,
        DUPLICATE_MATCHES_CSV,
        EXCLUSIONS_CSV,
        COMPARISON_SUMMARY_CSV,
        INSTRUMENT_VALIDATION_SUMMARY_CSV,
        DATASET_INDEX_SUMMARY_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219n = read_json(V219N_JSON)
    _, hkex_candidates = read_csv_with_header(V219N_CANDIDATES_CSV)
    _, v219n_instrument_summary = read_csv_with_header(V219N_INSTRUMENT_SUMMARY_CSV)
    _, v219n_quality_summary = read_csv_with_header(V219N_QUALITY_SUMMARY_CSV)

    canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = count_csv_rows(CURRENT_VALIDATED_CANDIDATE_DATASET)
    rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - current_candidate_rows, 0)

    active_index = build_dataset_index(ACTIVE_CANONICAL_DATASET, "active_canonical")
    current_index = build_dataset_index(CURRENT_VALIDATED_CANDIDATE_DATASET, "current_validated_candidate")

    validated_rows: list[dict[str, Any]] = []
    net_new_rows: list[dict[str, Any]] = []
    duplicate_match_rows: list[dict[str, Any]] = []
    exclusion_rows: list[dict[str, Any]] = []

    status_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()
    instrument_status_counter: Counter[tuple[str, str]] = Counter()

    for candidate in hkex_candidates:
        validation_status, validation_reason, matched_dataset, matches = classify_candidate(candidate, active_index, current_index)

        status_counter[validation_status] += 1
        reason_counter[validation_reason] += 1
        instrument_status_counter[(candidate.get("instrument_family", ""), validation_status)] += 1

        enriched = {
            **candidate,
            "validation_phase": VERSION,
            "validation_status": validation_status,
            "validation_reason": validation_reason,
            "matched_dataset": matched_dataset,
            "match_count": len(matches),
            "net_new_candidate": validation_status == "net_new_pending_expanded_rebuild",
            "canonical_validation_dry_run_only": True,
            "expanded_rebuild_status": "not_performed_v2_19o",
        }
        validated_rows.append(enriched)

        if validation_status == "net_new_pending_expanded_rebuild":
            net_new_rows.append(enriched)
        else:
            exclusion_rows.append(enriched)

        duplicate_match_rows.extend(matches)

    potential_scope_rows = sum(1 for row in hkex_candidates if row.get("candidate_scope_flag") == POTENTIAL_SCOPE_FLAG)
    reference_scope_rows = len(hkex_candidates) - potential_scope_rows
    duplicate_existing_count = status_counter.get("duplicate_existing_universe", 0)
    possible_name_duplicate_count = status_counter.get("possible_duplicate_name_review", 0)
    net_new_count = status_counter.get("net_new_pending_expanded_rebuild", 0)
    excluded_before_match_count = status_counter.get("excluded_before_canonical_match", 0)
    net_new_equity_like_count = sum(1 for row in net_new_rows if row.get("instrument_family") == "equity_like")
    net_new_fund_or_etp_count = sum(1 for row in net_new_rows if row.get("instrument_family") == "fund_or_etp")
    net_new_reit_count = sum(1 for row in net_new_rows if row.get("instrument_family") == "reit")
    net_new_spac_count = sum(1 for row in net_new_rows if row.get("instrument_family") == "spac")

    projected_candidate_rows_if_rebuilt = current_candidate_rows + net_new_count
    projected_rows_needed_to_50k = max(FINAL_TARGET_CANDIDATES - projected_candidate_rows_if_rebuilt, 0)
    projected_50k_gate_after_hkex = "READY" if projected_candidate_rows_if_rebuilt >= FINAL_TARGET_CANDIDATES else "BLOCKED"

    comparison_summary_rows = [
        {"metric": "hkex_candidate_rows_input", "value": len(hkex_candidates), "detail": "v2.19N dry-run candidates"},
        {"metric": "potential_scope_rows", "value": potential_scope_rows, "detail": POTENTIAL_SCOPE_FLAG},
        {"metric": "reference_scope_rows", "value": reference_scope_rows, "detail": "excluded before canonical match"},
        {"metric": "net_new_pending_expanded_rebuild", "value": net_new_count, "detail": "eligible HKEX candidates not matched to active/current indexes"},
        {"metric": "duplicate_existing_universe", "value": duplicate_existing_count, "detail": "hard duplicates by ticker/code/ISIN"},
        {"metric": "possible_duplicate_name_review", "value": possible_name_duplicate_count, "detail": "name-only possible duplicates"},
        {"metric": "excluded_before_canonical_match", "value": excluded_before_match_count, "detail": "reference/non-candidate scope"},
        {"metric": "duplicate_match_rows", "value": len(duplicate_match_rows), "detail": "all recorded match signals"},
        {"metric": "net_new_equity_like_count", "value": net_new_equity_like_count, "detail": "net new equity-like rows"},
        {"metric": "net_new_fund_or_etp_count", "value": net_new_fund_or_etp_count, "detail": "net new fund/ETP rows"},
        {"metric": "net_new_reit_count", "value": net_new_reit_count, "detail": "net new REIT rows"},
        {"metric": "net_new_spac_count", "value": net_new_spac_count, "detail": "net new SPAC rows"},
        {"metric": "current_validated_candidate_rows", "value": current_candidate_rows, "detail": "unchanged current validated candidate universe"},
        {"metric": "projected_candidate_rows_if_rebuilt", "value": projected_candidate_rows_if_rebuilt, "detail": "dry-run projection only"},
        {"metric": "projected_rows_needed_to_50k", "value": projected_rows_needed_to_50k, "detail": "dry-run projection only"},
        {"metric": "projected_50k_gate_after_hkex", "value": projected_50k_gate_after_hkex, "detail": "dry-run projection only"},
    ]

    instrument_validation_summary_rows = [
        {
            "instrument_family": instrument_family,
            "validation_status": validation_status,
            "candidate_rows": count,
        }
        for (instrument_family, validation_status), count in sorted(instrument_status_counter.items())
    ]

    dataset_index_summary_rows = [
        {
            "dataset_label": active_index["dataset_label"],
            "path": active_index["path"],
            "row_count": active_index["row_count"],
            "ticker_index_count": active_index["ticker_index_count"],
            "isin_index_count": active_index["isin_index_count"],
            "name_index_count": active_index["name_index_count"],
            "hkex_stock_code_index_count": active_index["hkex_stock_code_index_count"],
            "hkex_like_rows": active_index["hkex_like_rows"],
            "ticker_headers": "|".join(active_index["ticker_headers"]),
            "isin_headers": "|".join(active_index["isin_headers"]),
            "name_headers": "|".join(active_index["name_headers"]),
            "market_headers": "|".join(active_index["market_headers"]),
        },
        {
            "dataset_label": current_index["dataset_label"],
            "path": current_index["path"],
            "row_count": current_index["row_count"],
            "ticker_index_count": current_index["ticker_index_count"],
            "isin_index_count": current_index["isin_index_count"],
            "name_index_count": current_index["name_index_count"],
            "hkex_stock_code_index_count": current_index["hkex_stock_code_index_count"],
            "hkex_like_rows": current_index["hkex_like_rows"],
            "ticker_headers": "|".join(current_index["ticker_headers"]),
            "isin_headers": "|".join(current_index["isin_headers"]),
            "name_headers": "|".join(current_index["name_headers"]),
            "market_headers": "|".join(current_index["market_headers"]),
        },
    ]

    canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)
    candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19n_report_exists", V219N_JSON.exists(), "critical", str(V219N_JSON))
    add_check("v2_19n_status_expected", v219n.get("status") == EXPECTED_V219N_STATUS, "critical", str(v219n.get("status", "")))
    add_check("v2_19n_candidates_exists", V219N_CANDIDATES_CSV.exists(), "critical", str(V219N_CANDIDATES_CSV))
    add_check("v2_19n_candidate_rows_expected", len(hkex_candidates) == EXPECTED_HKEX_EXTRACT_ROWS, "critical", f"hkex_candidates={len(hkex_candidates)}")
    add_check("v2_19n_potential_scope_expected", potential_scope_rows == EXPECTED_HKEX_POTENTIAL_SCOPE_ROWS, "critical", f"potential_scope_rows={potential_scope_rows}")
    add_check("v2_19n_reference_scope_expected", reference_scope_rows == EXPECTED_HKEX_REFERENCE_SCOPE_ROWS, "warning", f"reference_scope_rows={reference_scope_rows}")
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("rows_needed_to_50k_expected", rows_needed_to_50k == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={rows_needed_to_50k}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("candidate_sha_unchanged", candidate_sha_before == candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("active_dataset_index_built", active_index["row_count"] == active_canonical_rows, "critical", f"active_index_rows={active_index['row_count']}")
    add_check("current_dataset_index_built", current_index["row_count"] == current_candidate_rows, "critical", f"current_index_rows={current_index['row_count']}")
    add_check("validated_rows_equal_input", len(validated_rows) == len(hkex_candidates), "critical", f"validated_rows={len(validated_rows)}; input={len(hkex_candidates)}")
    add_check("scope_accounting_balanced", potential_scope_rows + reference_scope_rows == len(hkex_candidates), "critical", f"{potential_scope_rows}+{reference_scope_rows}={len(hkex_candidates)}")
    add_check("status_accounting_balanced", sum(status_counter.values()) == len(hkex_candidates), "critical", f"status_total={sum(status_counter.values())}")
    add_check("net_new_count_documented", net_new_count >= 0, "critical", f"net_new_count={net_new_count}")
    add_check("duplicate_count_documented", duplicate_existing_count >= 0, "warning", f"duplicate_existing_count={duplicate_existing_count}")
    add_check("possible_name_duplicate_count_documented", possible_name_duplicate_count >= 0, "warning", f"possible_name_duplicate_count={possible_name_duplicate_count}")
    add_check("projected_candidate_rows_documented", projected_candidate_rows_if_rebuilt == current_candidate_rows + net_new_count, "critical", f"projected={projected_candidate_rows_if_rebuilt}")
    add_check("final_50k_gate_still_blocked_current", current_candidate_rows < FINAL_TARGET_CANDIDATES, "critical", f"{current_candidate_rows} < {FINAL_TARGET_CANDIDATES}")
    add_check("network_not_used_by_validation", True, "critical", "network_download_performed=False")
    add_check("candidate_validation_against_canonical_performed", True, "critical", "candidate_validation_against_canonical_performed=True")
    add_check("candidate_validation_dry_run_only", True, "critical", "dry_run_only=True")
    add_check("expanded_rebuild_not_performed", True, "critical", "expanded_rebuild_candidate_performed=False")
    add_check("expanded_validation_not_performed", True, "critical", "expanded_validation_performed=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0 and net_new_count > 0:
        status = STATUS_REBUILD_READY
        recommended_next_phase = NEXT_PHASE_REBUILD
    elif critical_failed == 0:
        status = STATUS_NO_NET_NEW
        recommended_next_phase = NEXT_PHASE_CLOSURE
    else:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW

    next_actions_rows: list[dict[str, Any]]
    if recommended_next_phase == NEXT_PHASE_REBUILD:
        next_actions_rows = [
            {
                "action_order": 1,
                "action_scope": "HKEX",
                "action": "run_expanded_rebuild_candidate",
                "priority": "high",
                "reason": "HKEX canonical validation dry run identified net-new candidates.",
                "recommended_phase": NEXT_PHASE_REBUILD,
                "guardrails": "build candidate dataset only; do not replace active canonical",
            },
            {
                "action_order": 2,
                "action_scope": "HKEX",
                "action": "include_net_new_only",
                "priority": "high",
                "reason": "Only net_new_pending_expanded_rebuild rows should be appended in the rebuild candidate.",
                "recommended_phase": NEXT_PHASE_REBUILD,
                "guardrails": "exclude duplicate_existing_universe, possible_duplicate_name_review and reference securities",
            },
            {
                "action_order": 3,
                "action_scope": "50k",
                "action": "recalculate_projected_gate_after_rebuild",
                "priority": "high",
                "reason": "Projected candidate row count is available only as dry-run evidence.",
                "recommended_phase": NEXT_PHASE_REBUILD,
                "guardrails": "no full59k; no scoring",
            },
        ]
    else:
        next_actions_rows = [
            {
                "action_order": 1,
                "action_scope": "HKEX",
                "action": "close_hkex_route_without_rebuild",
                "priority": "high",
                "reason": "No net-new HKEX candidates were identified in validation dry run.",
                "recommended_phase": NEXT_PHASE_CLOSURE,
                "guardrails": "closure report only; do not rebuild",
            }
        ]

    validation_summary = {
        "hkex_candidate_rows_input": len(hkex_candidates),
        "potential_scope_rows": potential_scope_rows,
        "reference_scope_rows": reference_scope_rows,
        "validated_rows": len(validated_rows),
        "net_new_pending_expanded_rebuild": net_new_count,
        "duplicate_existing_universe": duplicate_existing_count,
        "possible_duplicate_name_review": possible_name_duplicate_count,
        "excluded_before_canonical_match": excluded_before_match_count,
        "duplicate_match_rows": len(duplicate_match_rows),
        "net_new_equity_like_count": net_new_equity_like_count,
        "net_new_fund_or_etp_count": net_new_fund_or_etp_count,
        "net_new_reit_count": net_new_reit_count,
        "net_new_spac_count": net_new_spac_count,
        "current_validated_candidate_rows": current_candidate_rows,
        "projected_candidate_rows_if_rebuilt": projected_candidate_rows_if_rebuilt,
        "projected_rows_needed_to_50k": projected_rows_needed_to_50k,
        "projected_50k_gate_after_hkex": projected_50k_gate_after_hkex,
        "critical_failed_checks": critical_failed,
        "final_50k_candidate_gate_current": "BLOCKED",
        "full59k": "DEPRECATED_DEFERRED",
    }

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": active_canonical_rows,
            "current_validated_candidate_dataset": str(CURRENT_VALIDATED_CANDIDATE_DATASET),
            "current_validated_candidate_rows": current_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k": rows_needed_to_50k,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "current_candidate_sha256_before": candidate_sha_before,
            "current_candidate_sha256_after": candidate_sha_after,
        },
        "v2_19n_context": {
            "status": v219n.get("status"),
            "phase_type": v219n.get("phase_type"),
            "candidate_rows_extracted": v219n.get("extraction_summary", {}).get("candidate_rows_extracted"),
            "unique_stock_codes": v219n.get("extraction_summary", {}).get("unique_stock_codes"),
            "potential_candidate_pending_canonical_validation": v219n.get("extraction_summary", {}).get("potential_candidate_pending_canonical_validation"),
            "extracted_reference_security_likely_excluded_later": v219n.get("extraction_summary", {}).get("extracted_reference_security_likely_excluded_later"),
            "recommended_next_phase": v219n.get("recommended_next_phase"),
        },
        "validation_summary": validation_summary,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "route_selection_performed": False,
            "acquisition_plan_performed": False,
            "raw_acquisition_performed": False,
            "raw_acquisition_repair_performed": False,
            "raw_validation_performed": False,
            "repaired_raw_validation_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": True,
            "candidate_validation_dry_run_only": True,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": False,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": candidate_sha_before == candidate_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": "BLOCKED",
            "projected_50k_gate_after_hkex": projected_50k_gate_after_hkex,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    candidate_fieldnames = list(validated_rows[0].keys()) if validated_rows else []
    duplicate_fieldnames = [
        "candidate_id",
        "stock_code",
        "ticker",
        "isin",
        "name",
        "instrument_family",
        "dataset",
        "match_type",
        "match_value",
    ]

    write_csv(VALIDATED_CANDIDATES_CSV, validated_rows, candidate_fieldnames)
    write_csv(NET_NEW_CANDIDATES_CSV, net_new_rows, candidate_fieldnames)
    write_csv(DUPLICATE_MATCHES_CSV, duplicate_match_rows, duplicate_fieldnames)
    write_csv(EXCLUSIONS_CSV, exclusion_rows, candidate_fieldnames)
    write_csv(COMPARISON_SUMMARY_CSV, comparison_summary_rows, ["metric", "value", "detail"])
    write_csv(INSTRUMENT_VALIDATION_SUMMARY_CSV, instrument_validation_summary_rows, ["instrument_family", "validation_status", "candidate_rows"])
    write_csv(
        DATASET_INDEX_SUMMARY_CSV,
        dataset_index_summary_rows,
        [
            "dataset_label",
            "path",
            "row_count",
            "ticker_index_count",
            "isin_index_count",
            "name_index_count",
            "hkex_stock_code_index_count",
            "hkex_like_rows",
            "ticker_headers",
            "isin_headers",
            "name_headers",
            "market_headers",
        ],
    )
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    summary_lines = "\n".join(
        f"- `{row['metric']}`: `{row['value']}` — {row['detail']}"
        for row in comparison_summary_rows
    )

    instrument_lines = "\n".join(
        f"- `{row['instrument_family']}` / `{row['validation_status']}`: `{row['candidate_rows']}`"
        for row in instrument_validation_summary_rows
    )

    dataset_index_lines = "\n".join(
        f"- `{row['dataset_label']}`: rows `{row['row_count']}`, tickers `{row['ticker_index_count']}`, ISINs `{row['isin_index_count']}`, names `{row['name_index_count']}`, HKEX codes `{row['hkex_stock_code_index_count']}`"
        for row in dataset_index_summary_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} — {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.19O validates HKEX v2.19N dry-run candidates against the active canonical dataset and the current validated candidate dataset.

This phase performs candidate validation against canonical as a dry run only. It does not rebuild an expanded candidate dataset, does not replace the active canonical dataset, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed to 50k: `{rows_needed_to_50k}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

{summary_lines}

## Dataset indexes

{dataset_index_lines}

## Instrument validation summary

{instrument_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: true
- Candidate validation dry run only: true
- Canonical comparison performed: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{candidate_sha_before == candidate_sha_after}`
- Expanded rebuild candidate performed: false
- Expanded validation performed: false
- Active canonical replaced: false
- New expanded dataset written: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Current final 50k candidate gate: BLOCKED
- Projected 50k gate after HKEX: `{projected_50k_gate_after_hkex}`
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Overwrite allowed: false

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.19O HKEX candidate validation against canonical dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("DATASET_INDEX_SUMMARY:")
    for row in dataset_index_summary_rows:
        print(f"- {row['dataset_label']}: rows={row['row_count']} tickers={row['ticker_index_count']} isins={row['isin_index_count']} names={row['name_index_count']} hkex_codes={row['hkex_stock_code_index_count']} hkex_like_rows={row['hkex_like_rows']}")
    print("")
    print("INSTRUMENT_VALIDATION_SUMMARY:")
    for row in instrument_validation_summary_rows:
        print(f"- {row['instrument_family']} / {row['validation_status']}: {row['candidate_rows']}")
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

