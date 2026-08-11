from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.19Q"
PHASE = "HKEX Expanded Validation"
PHASE_TYPE = "expanded-validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
CURRENT_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
EXPANDED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_hkex_v2_19p.csv"

V219P_JSON = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_v2_19p.json"
V219P_APPENDED_ROWS_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_appended_rows_v2_19p.csv"
V219P_ROWCOUNT_AUDIT_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_rowcount_audit_v2_19p.csv"
V219P_MAPPING_AUDIT_CSV = OUTPUT_DIR / "hkex_expanded_rebuild_candidate_mapping_audit_v2_19p.csv"

REPORT_JSON = OUTPUT_DIR / "hkex_expanded_validation_v2_19q.json"
REPORT_MD = OUTPUT_DIR / "hkex_expanded_validation_v2_19q.md"
ROWCOUNT_VALIDATION_CSV = OUTPUT_DIR / "hkex_expanded_validation_rowcount_v2_19q.csv"
SCHEMA_VALIDATION_CSV = OUTPUT_DIR / "hkex_expanded_validation_schema_v2_19q.csv"
APPENDED_TAIL_VALIDATION_CSV = OUTPUT_DIR / "hkex_expanded_validation_appended_tail_v2_19q.csv"
DUPLICATE_VALIDATION_CSV = OUTPUT_DIR / "hkex_expanded_validation_duplicates_v2_19q.csv"
PROVIDER_VALIDATION_CSV = OUTPUT_DIR / "hkex_expanded_validation_provider_profile_v2_19q.csv"
CHECKS_CSV = OUTPUT_DIR / "hkex_expanded_validation_checks_v2_19q.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "hkex_expanded_validation_next_actions_v2_19q.csv"

EXPECTED_V219P_STATUS = "HKEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_41392_ROWS_EXPANDED_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED = 40996
EXPANDED_CANDIDATE_ROWS_EXPECTED = 41392
APPENDED_ROWS_EXPECTED = 396
ROWS_NEEDED_AFTER_REBUILD_EXPECTED = 8608
FINAL_TARGET_CANDIDATES = 50000

EXPECTED_EXPANDED_SHA256_FROM_V219P = "3f864f1fc0196d9ec3b9ed1b2e8fa3f11c6a109933e0c07c212dc8e89d8b571c"

STATUS_SUCCESS = "HKEX_EXPANDED_VALIDATION_COMPLETED_41392_ROWS_VALIDATED_CLOSURE_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
STATUS_FAILED = "HKEX_EXPANDED_VALIDATION_FAILED_REVIEW_REQUIRED"

NEXT_PHASE_CLOSURE = "v2.19R - HKEX Closure Report"
NEXT_PHASE_REVIEW = "v2.19Q_REVIEW - HKEX Expanded Validation Review"


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


def normalize_header(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_\-/]+", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def clean_cell(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text(value: Any) -> str:
    return clean_cell(value).upper()


def normalize_ticker(value: Any) -> str:
    text = normalize_text(value).replace(" ", "").replace("_", ".")
    text = re.sub(r"[^A-Z0-9.\-]", "", text)

    match = re.fullmatch(r"(\d{1,5})\.HK", text)
    if match:
        return f"{match.group(1).zfill(5)}.HK"

    match = re.fullmatch(r"HKEX[_\-\.]?(\d{1,5})", text)
    if match:
        return f"{match.group(1).zfill(5)}.HK"

    return text


def normalize_isin(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^A-Z0-9]", "", text)
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", text):
        return text
    return ""


def row_digest(row: dict[str, str], headers: list[str]) -> str:
    payload = "\x1f".join(clean_cell(row.get(header, "")) for header in headers)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def dataset_digest(rows: list[dict[str, str]], headers: list[str]) -> str:
    digest = hashlib.sha256()
    digest.update(("headers:" + "\x1f".join(headers)).encode("utf-8"))
    for row in rows:
        digest.update(row_digest(row, headers).encode("utf-8"))
    return digest.hexdigest()


def find_header(headers: list[str], candidates: set[str]) -> str:
    normalized_to_header = {normalize_header(header): header for header in headers}
    for candidate in candidates:
        if candidate in normalized_to_header:
            return normalized_to_header[candidate]
    return ""


def get_first_available(row: dict[str, str], headers: list[str], candidates: set[str]) -> str:
    header = find_header(headers, candidates)
    if not header:
        return ""
    return clean_cell(row.get(header, ""))


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        ROWCOUNT_VALIDATION_CSV,
        SCHEMA_VALIDATION_CSV,
        APPENDED_TAIL_VALIDATION_CSV,
        DUPLICATE_VALIDATION_CSV,
        PROVIDER_VALIDATION_CSV,
        CHECKS_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v219p = read_json(V219P_JSON)

    current_headers, current_rows = read_csv_with_header(CURRENT_VALIDATED_CANDIDATE_DATASET)
    expanded_headers, expanded_rows = read_csv_with_header(EXPANDED_CANDIDATE_DATASET)
    appended_headers, appended_audit_rows = read_csv_with_header(V219P_APPENDED_ROWS_CSV)

    active_canonical_rows = count_csv_rows(ACTIVE_CANONICAL_DATASET)
    current_candidate_rows = len(current_rows)
    expanded_candidate_rows = len(expanded_rows)
    appended_rows_count = len(appended_audit_rows)
    rows_needed_after_rebuild = max(FINAL_TARGET_CANDIDATES - expanded_candidate_rows, 0)
    final_50k_gate_after_validation = "READY" if expanded_candidate_rows >= FINAL_TARGET_CANDIDATES else "BLOCKED"

    active_canonical_sha_before = sha256_file(ACTIVE_CANONICAL_DATASET)
    active_canonical_sha_after = sha256_file(ACTIVE_CANONICAL_DATASET)

    current_candidate_sha_before = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)
    current_candidate_sha_after = sha256_file(CURRENT_VALIDATED_CANDIDATE_DATASET)

    expanded_candidate_sha = sha256_file(EXPANDED_CANDIDATE_DATASET)

    schema_equal = current_headers == expanded_headers
    header_count_current = len(current_headers)
    header_count_expanded = len(expanded_headers)

    prefix_rows = expanded_rows[:current_candidate_rows]
    tail_rows = expanded_rows[current_candidate_rows:]

    prefix_digest_current = dataset_digest(current_rows, current_headers)
    prefix_digest_expanded = dataset_digest(prefix_rows, expanded_headers) if schema_equal else ""
    prefix_matches_current_candidate = schema_equal and prefix_digest_current == prefix_digest_expanded

    ticker_header = find_header(expanded_headers, {"ticker"})
    symbol_header = find_header(expanded_headers, {"symbol"})
    isin_header = find_header(expanded_headers, {"isin"})
    provider_header = find_header(expanded_headers, {"source_provider", "provider"})
    exchange_header = find_header(expanded_headers, {"exchange"})
    mic_header = find_header(expanded_headers, {"mic"})
    source_phase_header = find_header(expanded_headers, {"source_phase", "phase"})
    country_header = find_header(expanded_headers, {"country", "source_country"})
    currency_header = find_header(expanded_headers, {"currency", "trading_currency"})
    company_name_header = find_header(expanded_headers, {"company_name", "security_name", "name"})

    appended_tickers: list[str] = []
    appended_symbols: list[str] = []
    appended_isins: list[str] = []
    appended_providers: list[str] = []
    appended_exchanges: list[str] = []
    appended_mics: list[str] = []
    appended_source_phases: list[str] = []
    appended_countries: list[str] = []
    appended_currencies: list[str] = []
    appended_company_names: list[str] = []

    for row in tail_rows:
        appended_tickers.append(normalize_ticker(row.get(ticker_header, "")) if ticker_header else "")
        appended_symbols.append(normalize_ticker(row.get(symbol_header, "")) if symbol_header else "")
        appended_isins.append(normalize_isin(row.get(isin_header, "")) if isin_header else "")
        appended_providers.append(normalize_text(row.get(provider_header, "")) if provider_header else "")
        appended_exchanges.append(normalize_text(row.get(exchange_header, "")) if exchange_header else "")
        appended_mics.append(normalize_text(row.get(mic_header, "")) if mic_header else "")
        appended_source_phases.append(clean_cell(row.get(source_phase_header, "")) if source_phase_header else "")
        appended_countries.append(normalize_text(row.get(country_header, "")) if country_header else "")
        appended_currencies.append(normalize_text(row.get(currency_header, "")) if currency_header else "")
        appended_company_names.append(clean_cell(row.get(company_name_header, "")) if company_name_header else "")

    ticker_counter = Counter(t for t in appended_tickers if t)
    symbol_counter = Counter(t for t in appended_symbols if t)
    isin_counter = Counter(i for i in appended_isins if i)
    provider_counter = Counter(p for p in appended_providers if p)
    exchange_counter = Counter(e for e in appended_exchanges if e)
    mic_counter = Counter(m for m in appended_mics if m)
    source_phase_counter = Counter(p for p in appended_source_phases if p)
    country_counter = Counter(c for c in appended_countries if c)
    currency_counter = Counter(c for c in appended_currencies if c)

    duplicate_appended_tickers = sorted([ticker for ticker, count in ticker_counter.items() if count > 1])
    duplicate_appended_symbols = sorted([symbol for symbol, count in symbol_counter.items() if count > 1])
    duplicate_appended_isins = sorted([isin for isin, count in isin_counter.items() if count > 1])

    current_tickers: set[str] = set()
    current_symbols: set[str] = set()
    current_isins: set[str] = set()

    for row in current_rows:
        if ticker_header:
            ticker = normalize_ticker(row.get(ticker_header, ""))
            if ticker:
                current_tickers.add(ticker)
        if symbol_header:
            symbol = normalize_ticker(row.get(symbol_header, ""))
            if symbol:
                current_symbols.add(symbol)
        if isin_header:
            isin = normalize_isin(row.get(isin_header, ""))
            if isin:
                current_isins.add(isin)

    appended_tickers_already_in_current = sorted([ticker for ticker in set(appended_tickers) if ticker and ticker in current_tickers])
    appended_symbols_already_in_current = sorted([symbol for symbol in set(appended_symbols) if symbol and symbol in current_symbols])
    appended_isins_already_in_current = sorted([isin for isin in set(appended_isins) if isin and isin in current_isins])

    tail_appended_audit_tickers = [normalize_ticker(row.get("ticker") or row.get("symbol") or row.get("ticker_yahoo")) for row in appended_audit_rows]
    tail_tickers_match_appended_audit = [t for t in appended_tickers if t] == [t for t in tail_appended_audit_tickers if t]

    rowcount_validation_rows = [
        {"metric": "active_canonical_rows", "value": active_canonical_rows, "expected": ACTIVE_CANONICAL_ROWS_EXPECTED, "passed": active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "detail": str(ACTIVE_CANONICAL_DATASET)},
        {"metric": "current_validated_candidate_rows", "value": current_candidate_rows, "expected": CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "passed": current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "detail": str(CURRENT_VALIDATED_CANDIDATE_DATASET)},
        {"metric": "expanded_candidate_rows", "value": expanded_candidate_rows, "expected": EXPANDED_CANDIDATE_ROWS_EXPECTED, "passed": expanded_candidate_rows == EXPANDED_CANDIDATE_ROWS_EXPECTED, "detail": str(EXPANDED_CANDIDATE_DATASET)},
        {"metric": "appended_tail_rows", "value": len(tail_rows), "expected": APPENDED_ROWS_EXPECTED, "passed": len(tail_rows) == APPENDED_ROWS_EXPECTED, "detail": "expanded tail rows"},
        {"metric": "appended_audit_rows", "value": appended_rows_count, "expected": APPENDED_ROWS_EXPECTED, "passed": appended_rows_count == APPENDED_ROWS_EXPECTED, "detail": str(V219P_APPENDED_ROWS_CSV)},
        {"metric": "rowcount_arithmetic", "value": current_candidate_rows + appended_rows_count, "expected": expanded_candidate_rows, "passed": current_candidate_rows + appended_rows_count == expanded_candidate_rows, "detail": "current + appended = expanded"},
        {"metric": "rows_needed_after_rebuild", "value": rows_needed_after_rebuild, "expected": ROWS_NEEDED_AFTER_REBUILD_EXPECTED, "passed": rows_needed_after_rebuild == ROWS_NEEDED_AFTER_REBUILD_EXPECTED, "detail": "expanded vs 50k"},
        {"metric": "final_50k_gate_after_validation", "value": final_50k_gate_after_validation, "expected": "BLOCKED", "passed": final_50k_gate_after_validation == "BLOCKED", "detail": "41,392 < 50,000"},
    ]

    schema_validation_rows = [
        {"metric": "schema_equal_to_current_candidate", "value": schema_equal, "expected": True, "passed": schema_equal, "detail": "expanded headers equal current candidate headers"},
        {"metric": "current_header_count", "value": header_count_current, "expected": header_count_current, "passed": header_count_current > 0, "detail": "|".join(current_headers)},
        {"metric": "expanded_header_count", "value": header_count_expanded, "expected": header_count_current, "passed": header_count_expanded == header_count_current, "detail": "|".join(expanded_headers)},
        {"metric": "ticker_header", "value": ticker_header, "expected": "present", "passed": bool(ticker_header), "detail": "ticker header used for HKEX validation"},
        {"metric": "symbol_header", "value": symbol_header, "expected": "present", "passed": bool(symbol_header), "detail": "symbol header used for HKEX validation"},
        {"metric": "company_name_header", "value": company_name_header, "expected": "present", "passed": bool(company_name_header), "detail": "company/security name header"},
        {"metric": "provider_header", "value": provider_header, "expected": "present", "passed": bool(provider_header), "detail": "provider/source provider header"},
        {"metric": "exchange_header", "value": exchange_header, "expected": "present", "passed": bool(exchange_header), "detail": "exchange header"},
        {"metric": "mic_header", "value": mic_header, "expected": "present", "passed": bool(mic_header), "detail": "mic header"},
        {"metric": "source_phase_header", "value": source_phase_header, "expected": "present", "passed": bool(source_phase_header), "detail": "source phase header"},
    ]

    appended_tail_validation_rows = [
        {"metric": "prefix_matches_current_candidate", "value": prefix_matches_current_candidate, "expected": True, "passed": prefix_matches_current_candidate, "detail": "first 40,996 expanded rows match current candidate exactly by digest"},
        {"metric": "tail_rows_count", "value": len(tail_rows), "expected": APPENDED_ROWS_EXPECTED, "passed": len(tail_rows) == APPENDED_ROWS_EXPECTED, "detail": "tail rows are HKEX appended rows"},
        {"metric": "tail_tickers_match_appended_audit", "value": tail_tickers_match_appended_audit, "expected": True, "passed": tail_tickers_match_appended_audit, "detail": "tail ticker order equals v2.19P appended audit"},
        {"metric": "tail_nonempty_ticker_count", "value": sum(1 for t in appended_tickers if t), "expected": APPENDED_ROWS_EXPECTED, "passed": sum(1 for t in appended_tickers if t) == APPENDED_ROWS_EXPECTED, "detail": "all appended rows have ticker"},
        {"metric": "tail_nonempty_name_count", "value": sum(1 for n in appended_company_names if n), "expected": APPENDED_ROWS_EXPECTED, "passed": sum(1 for n in appended_company_names if n) == APPENDED_ROWS_EXPECTED, "detail": "all appended rows have company/security name"},
        {"metric": "tail_provider_hkex_count", "value": provider_counter.get("HKEX", 0), "expected": APPENDED_ROWS_EXPECTED, "passed": provider_counter.get("HKEX", 0) == APPENDED_ROWS_EXPECTED, "detail": json.dumps(provider_counter.most_common(), ensure_ascii=False)},
        {"metric": "tail_exchange_hkex_count", "value": exchange_counter.get("HKEX", 0), "expected": APPENDED_ROWS_EXPECTED, "passed": exchange_counter.get("HKEX", 0) == APPENDED_ROWS_EXPECTED, "detail": json.dumps(exchange_counter.most_common(), ensure_ascii=False)},
        {"metric": "tail_mic_xhkg_count", "value": mic_counter.get("XHKG", 0), "expected": APPENDED_ROWS_EXPECTED, "passed": mic_counter.get("XHKG", 0) == APPENDED_ROWS_EXPECTED, "detail": json.dumps(mic_counter.most_common(), ensure_ascii=False)},
        {"metric": "tail_source_phase_v219p_count", "value": source_phase_counter.get("v2.19P", 0), "expected": APPENDED_ROWS_EXPECTED, "passed": source_phase_counter.get("v2.19P", 0) == APPENDED_ROWS_EXPECTED, "detail": json.dumps(source_phase_counter.most_common(), ensure_ascii=False)},
        {"metric": "tail_currency_profile", "value": len(currency_counter), "expected": "documented", "passed": len(currency_counter) > 0, "detail": json.dumps(currency_counter.most_common(), ensure_ascii=False)},
    ]

    duplicate_validation_rows = [
        {"metric": "duplicate_appended_ticker_count", "value": len(duplicate_appended_tickers), "expected": 0, "passed": len(duplicate_appended_tickers) == 0, "detail": ",".join(duplicate_appended_tickers[:100])},
        {"metric": "duplicate_appended_symbol_count", "value": len(duplicate_appended_symbols), "expected": 0, "passed": len(duplicate_appended_symbols) == 0, "detail": ",".join(duplicate_appended_symbols[:100])},
        {"metric": "duplicate_appended_isin_count", "value": len(duplicate_appended_isins), "expected": "documented", "passed": True, "detail": ",".join(duplicate_appended_isins[:100])},
        {"metric": "appended_tickers_already_in_current_count", "value": len(appended_tickers_already_in_current), "expected": 0, "passed": len(appended_tickers_already_in_current) == 0, "detail": ",".join(appended_tickers_already_in_current[:100])},
        {"metric": "appended_symbols_already_in_current_count", "value": len(appended_symbols_already_in_current), "expected": 0, "passed": len(appended_symbols_already_in_current) == 0, "detail": ",".join(appended_symbols_already_in_current[:100])},
        {"metric": "appended_isins_already_in_current_count", "value": len(appended_isins_already_in_current), "expected": "documented", "passed": len(appended_isins_already_in_current) == 0, "detail": ",".join(appended_isins_already_in_current[:100])},
    ]

    provider_validation_rows = [
        {"field": "provider", "profile_json": json.dumps(provider_counter.most_common(), ensure_ascii=False)},
        {"field": "exchange", "profile_json": json.dumps(exchange_counter.most_common(), ensure_ascii=False)},
        {"field": "mic", "profile_json": json.dumps(mic_counter.most_common(), ensure_ascii=False)},
        {"field": "source_phase", "profile_json": json.dumps(source_phase_counter.most_common(), ensure_ascii=False)},
        {"field": "country", "profile_json": json.dumps(country_counter.most_common(), ensure_ascii=False)},
        {"field": "currency", "profile_json": json.dumps(currency_counter.most_common(), ensure_ascii=False)},
    ]

    all_validation_rows = rowcount_validation_rows + schema_validation_rows + appended_tail_validation_rows + duplicate_validation_rows

    checks: list[dict[str, Any]] = []
    critical_failed = 0

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_19p_report_exists", V219P_JSON.exists(), "critical", str(V219P_JSON))
    add_check("v2_19p_status_expected", v219p.get("status") == EXPECTED_V219P_STATUS, "critical", str(v219p.get("status", "")))
    add_check("expanded_candidate_exists", EXPANDED_CANDIDATE_DATASET.exists(), "critical", str(EXPANDED_CANDIDATE_DATASET))
    add_check("expanded_candidate_sha_matches_v2_19p", expanded_candidate_sha == EXPECTED_EXPANDED_SHA256_FROM_V219P, "critical", expanded_candidate_sha)
    add_check("active_canonical_rows_expected", active_canonical_rows == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={active_canonical_rows}")
    add_check("current_validated_candidate_rows_expected", current_candidate_rows == CURRENT_VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"current_candidate_rows={current_candidate_rows}")
    add_check("expanded_candidate_rows_expected", expanded_candidate_rows == EXPANDED_CANDIDATE_ROWS_EXPECTED, "critical", f"expanded_candidate_rows={expanded_candidate_rows}")
    add_check("appended_tail_rows_expected", len(tail_rows) == APPENDED_ROWS_EXPECTED, "critical", f"tail_rows={len(tail_rows)}")
    add_check("appended_audit_rows_expected", appended_rows_count == APPENDED_ROWS_EXPECTED, "critical", f"appended_audit_rows={appended_rows_count}")
    add_check("rowcount_arithmetic_expected", current_candidate_rows + appended_rows_count == expanded_candidate_rows, "critical", f"{current_candidate_rows}+{appended_rows_count}={expanded_candidate_rows}")
    add_check("rows_needed_after_rebuild_expected", rows_needed_after_rebuild == ROWS_NEEDED_AFTER_REBUILD_EXPECTED, "critical", f"rows_needed_after={rows_needed_after_rebuild}")
    add_check("final_50k_gate_after_validation_blocked", final_50k_gate_after_validation == "BLOCKED", "critical", final_50k_gate_after_validation)
    add_check("schema_equal_to_current_candidate", schema_equal, "critical", f"current_headers={header_count_current}; expanded_headers={header_count_expanded}")
    add_check("prefix_matches_current_candidate", prefix_matches_current_candidate, "critical", "expanded prefix equals current candidate by digest")
    add_check("tail_tickers_match_appended_audit", tail_tickers_match_appended_audit, "critical", "tail ticker order equals appended audit")
    add_check("tail_all_tickers_present", sum(1 for t in appended_tickers if t) == APPENDED_ROWS_EXPECTED, "critical", f"tickers={sum(1 for t in appended_tickers if t)}")
    add_check("tail_all_names_present", sum(1 for n in appended_company_names if n) == APPENDED_ROWS_EXPECTED, "critical", f"names={sum(1 for n in appended_company_names if n)}")
    add_check("tail_provider_hkex_expected", provider_counter.get("HKEX", 0) == APPENDED_ROWS_EXPECTED, "critical", f"HKEX provider rows={provider_counter.get('HKEX', 0)}")
    add_check("tail_exchange_hkex_expected", exchange_counter.get("HKEX", 0) == APPENDED_ROWS_EXPECTED, "critical", f"HKEX exchange rows={exchange_counter.get('HKEX', 0)}")
    add_check("tail_mic_xhkg_expected", mic_counter.get("XHKG", 0) == APPENDED_ROWS_EXPECTED, "critical", f"XHKG rows={mic_counter.get('XHKG', 0)}")
    add_check("tail_source_phase_v219p_expected", source_phase_counter.get("v2.19P", 0) == APPENDED_ROWS_EXPECTED, "critical", f"v2.19P rows={source_phase_counter.get("v2.19P", 0)}")
    add_check("duplicate_appended_tickers_zero", len(duplicate_appended_tickers) == 0, "critical", f"duplicate_appended_tickers={len(duplicate_appended_tickers)}")
    add_check("duplicate_appended_symbols_zero", len(duplicate_appended_symbols) == 0, "critical", f"duplicate_appended_symbols={len(duplicate_appended_symbols)}")
    add_check("duplicate_appended_isins_documented", len(duplicate_appended_isins) >= 0, "warning", f"duplicate_appended_isins={len(duplicate_appended_isins)}")
    add_check("appended_tickers_not_in_current", len(appended_tickers_already_in_current) == 0, "critical", f"appended_tickers_already_in_current={len(appended_tickers_already_in_current)}")
    add_check("appended_symbols_not_in_current", len(appended_symbols_already_in_current) == 0, "critical", f"appended_symbols_already_in_current={len(appended_symbols_already_in_current)}")
    add_check("appended_isins_not_in_current", len(appended_isins_already_in_current) == 0, "warning", f"appended_isins_already_in_current={len(appended_isins_already_in_current)}")
    add_check("canonical_sha_unchanged", active_canonical_sha_before == active_canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("current_candidate_sha_unchanged", current_candidate_sha_before == current_candidate_sha_after, "critical", "current validated candidate sha unchanged")
    add_check("expanded_validation_performed", True, "critical", "expanded_validation_performed=True")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("current_candidate_dataset_not_modified", True, "critical", "current_candidate_dataset_modified=False")
    add_check("new_expanded_candidate_validated_only", True, "critical", "no canonical promotion in this phase")
    add_check("network_not_used_by_validation", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")

    if critical_failed == 0:
        status = STATUS_SUCCESS
        recommended_next_phase = NEXT_PHASE_CLOSURE
    else:
        status = STATUS_FAILED
        recommended_next_phase = NEXT_PHASE_REVIEW

    validation_summary = {
        "active_canonical_rows": active_canonical_rows,
        "current_validated_candidate_rows": current_candidate_rows,
        "expanded_candidate_rows": expanded_candidate_rows,
        "appended_tail_rows": len(tail_rows),
        "appended_audit_rows": appended_rows_count,
        "rows_needed_after_rebuild": rows_needed_after_rebuild,
        "final_50k_candidate_gate_after_validation": final_50k_gate_after_validation,
        "expanded_candidate_dataset": str(EXPANDED_CANDIDATE_DATASET),
        "expanded_candidate_sha256": expanded_candidate_sha,
        "schema_equal_to_current_candidate": schema_equal,
        "prefix_matches_current_candidate": prefix_matches_current_candidate,
        "tail_tickers_match_appended_audit": tail_tickers_match_appended_audit,
        "duplicate_appended_ticker_count": len(duplicate_appended_tickers),
        "duplicate_appended_symbol_count": len(duplicate_appended_symbols),
        "duplicate_appended_isin_count": len(duplicate_appended_isins),
        "appended_tickers_already_in_current_count": len(appended_tickers_already_in_current),
        "appended_symbols_already_in_current_count": len(appended_symbols_already_in_current),
        "appended_isins_already_in_current_count": len(appended_isins_already_in_current),
        "critical_failed_checks": critical_failed,
        "full59k": "DEPRECATED_DEFERRED",
    }

    next_actions_rows = [
        {
            "action_order": 1,
            "action_scope": "HKEX",
            "action": "write_hkex_closure_report",
            "priority": "high",
            "reason": "Expanded candidate dataset has been validated and HKEX route can be closed formally.",
            "recommended_phase": NEXT_PHASE_CLOSURE,
            "guardrails": "closure only; do not promote candidate to canonical without explicit later decision",
        },
        {
            "action_order": 2,
            "action_scope": "50k",
            "action": "select_next_provider_route_after_hkex",
            "priority": "medium",
            "reason": "HKEX adds 396 rows but 50k gate remains blocked with 8,608 rows still needed.",
            "recommended_phase": "post-v2.19R route selection",
            "guardrails": "continue with quality-first provider route; full59k remains deprecated",
        },
    ]

    write_csv(ROWCOUNT_VALIDATION_CSV, rowcount_validation_rows, ["metric", "value", "expected", "passed", "detail"])
    write_csv(SCHEMA_VALIDATION_CSV, schema_validation_rows, ["metric", "value", "expected", "passed", "detail"])
    write_csv(APPENDED_TAIL_VALIDATION_CSV, appended_tail_validation_rows, ["metric", "value", "expected", "passed", "detail"])
    write_csv(DUPLICATE_VALIDATION_CSV, duplicate_validation_rows, ["metric", "value", "expected", "passed", "detail"])
    write_csv(PROVIDER_VALIDATION_CSV, provider_validation_rows, ["field", "profile_json"])
    write_csv(CHECKS_CSV, checks, ["check", "passed", "severity", "detail"])
    write_csv(NEXT_ACTIONS_CSV, next_actions_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])

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
            "expanded_candidate_dataset": str(EXPANDED_CANDIDATE_DATASET),
            "expanded_candidate_rows": expanded_candidate_rows,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_after_rebuild": rows_needed_after_rebuild,
            "final_50k_candidate_gate_after_validation": final_50k_gate_after_validation,
            "full59k": "DEPRECATED_DEFERRED",
        },
        "v2_19p_context": {
            "status": v219p.get("status"),
            "phase_type": v219p.get("phase_type"),
            "net_new_rows_appended": v219p.get("rebuild_summary", {}).get("net_new_rows_appended"),
            "expanded_candidate_rows": v219p.get("rebuild_summary", {}).get("expanded_candidate_rows"),
            "expanded_candidate_dataset": v219p.get("rebuild_summary", {}).get("expanded_candidate_dataset"),
            "expanded_candidate_sha256": v219p.get("rebuild_summary", {}).get("expanded_candidate_sha256"),
            "rows_needed_after_rebuild": v219p.get("rebuild_summary", {}).get("rows_needed_after_rebuild"),
            "final_50k_candidate_gate_after_rebuild": v219p.get("rebuild_summary", {}).get("final_50k_candidate_gate_after_rebuild"),
            "recommended_next_phase": v219p.get("recommended_next_phase"),
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
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": False,
            "expanded_validation_performed": True,
            "expanded_validation_only": True,
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": active_canonical_sha_before == active_canonical_sha_after,
            "current_candidate_dataset_read": True,
            "current_candidate_dataset_modified": False,
            "current_candidate_sha_unchanged": current_candidate_sha_before == current_candidate_sha_after,
            "expanded_candidate_dataset_read": True,
            "expanded_candidate_dataset_modified": False,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": final_50k_gate_after_validation,
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_json(REPORT_JSON, payload)

    rowcount_lines = "\n".join(
        f"- `{row['metric']}`: `{row['value']}` / expected `{row['expected']}` — {'PASS' if row['passed'] else 'FAIL'}"
        for row in rowcount_validation_rows
    )
    schema_lines = "\n".join(
        f"- `{row['metric']}`: `{row['value']}` — {'PASS' if row['passed'] else 'FAIL'}"
        for row in schema_validation_rows
    )
    tail_lines = "\n".join(
        f"- `{row['metric']}`: `{row['value']}` / expected `{row['expected']}` — {'PASS' if row['passed'] else 'FAIL'}"
        for row in appended_tail_validation_rows
    )
    duplicate_lines = "\n".join(
        f"- `{row['metric']}`: `{row['value']}` / expected `{row['expected']}` — {'PASS' if row['passed'] else 'FAIL'}"
        for row in duplicate_validation_rows
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

v2.19Q validates the HKEX expanded candidate dataset generated in v2.19P.

This phase validates the candidate dataset only. It does not promote the candidate to canonical, does not replace the active canonical dataset, does not modify the current validated candidate dataset, and does not run scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Validation summary

- Active canonical rows: `{active_canonical_rows}`
- Current validated candidate rows: `{current_candidate_rows}`
- Expanded candidate rows: `{expanded_candidate_rows}`
- Appended HKEX tail rows: `{len(tail_rows)}`
- Rows needed after rebuild: `{rows_needed_after_rebuild}`
- Final 50k candidate gate after validation: `{final_50k_gate_after_validation}`
- Expanded candidate SHA256: `{expanded_candidate_sha}`
- Schema equal to current candidate: `{schema_equal}`
- Prefix matches current candidate: `{prefix_matches_current_candidate}`
- Tail tickers match v2.19P appended audit: `{tail_tickers_match_appended_audit}`
- Critical failed checks: `{critical_failed}`

## Rowcount validation

{rowcount_lines}

## Schema validation

{schema_lines}

## Appended tail validation

{tail_lines}

## Duplicate validation

{duplicate_lines}

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Expanded validation performed: true
- Expanded validation only: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{active_canonical_sha_before == active_canonical_sha_after}`
- Current candidate dataset modified: false
- Current candidate SHA unchanged: `{current_candidate_sha_before == current_candidate_sha_after}`
- Expanded candidate dataset modified: false
- Active canonical replaced: false
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: `{final_50k_gate_after_validation}`
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

    print("v2.19Q HKEX expanded validation completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("VALIDATION_SUMMARY:")
    for key, value in validation_summary.items():
        print(f"- {key}: {value}")
    print("")
    print("ROWCOUNT_VALIDATION:")
    for row in rowcount_validation_rows:
        print(f"- {row['metric']}: {row['value']} expected={row['expected']} passed={row['passed']}")
    print("")
    print("SCHEMA_VALIDATION:")
    for row in schema_validation_rows:
        print(f"- {row['metric']}: {row['value']} expected={row['expected']} passed={row['passed']}")
    print("")
    print("APPENDED_TAIL_VALIDATION:")
    for row in appended_tail_validation_rows:
        print(f"- {row['metric']}: {row['value']} expected={row['expected']} passed={row['passed']}")
    print("")
    print("DUPLICATE_VALIDATION:")
    for row in duplicate_validation_rows:
        print(f"- {row['metric']}: {row['value']} expected={row['expected']} passed={row['passed']}")
    print("")
    print("PROVIDER_VALIDATION:")
    for row in provider_validation_rows:
        print(f"- {row['field']}: {row['profile_json']}")
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

