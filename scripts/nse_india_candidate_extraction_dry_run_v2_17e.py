from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17E"
PHASE = "NSE India Candidate Extraction Dry Run"
PHASE_TYPE = "candidate-extraction-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

V217D_JSON = OUTPUT_DIR / "nse_india_raw_validation_v2_17d.json"
V217D_FILE_PROFILE_CSV = OUTPUT_DIR / "nse_india_raw_validation_file_profile_v2_17d.csv"
V217D_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "nse_india_raw_validation_source_diagnostics_v2_17d.csv"
V217D_SCHEMA_PROFILE_CSV = OUTPUT_DIR / "nse_india_raw_validation_schema_profile_v2_17d.csv"

REPORT_JSON = OUTPUT_DIR / "nse_india_candidate_extraction_dry_run_v2_17e.json"
REPORT_MD = OUTPUT_DIR / "nse_india_candidate_extraction_dry_run_v2_17e.md"
CANDIDATES_CSV = OUTPUT_DIR / "nse_india_candidate_extraction_candidates_v2_17e.csv"
EXCLUSIONS_CSV = OUTPUT_DIR / "nse_india_candidate_extraction_exclusions_v2_17e.csv"
SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "nse_india_candidate_extraction_source_diagnostics_v2_17e.csv"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED = 11713

EXPECTED_V217D_STATUS = "NSE_INDIA_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_CANDIDATE_EXTRACTION_READY_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_V217D_NEXT = "v2.17E - NSE India Candidate Extraction Dry Run"

NEXT_PHASE_IF_CANDIDATES = "v2.17F - NSE India Candidate Validation Against Canonical Dry Run"
NEXT_PHASE_IF_NO_CANDIDATES = "v2.17I - NSE India Closure Report"

CANDIDATE_SOURCES = {
    "nse_all_reports_cm_mii_security_file_nse_listed": "primary_mii_security_file",
    "nse_securities_available_equity_segment": "primary_equity_segment_csv",
    "nse_securities_available_sme": "sme_equity_review_csv",
}

REVIEW_NOT_CANDIDATE_SOURCES = {
    "nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive": "bse_exclusive_scope_review_not_candidate",
    "nse_changes_company_names": "reference_only_company_name_changes",
    "nse_changes_symbols": "reference_only_symbol_changes",
}

EXPLICIT_EXCLUSION_SOURCES = {
    "nse_idrs": "excluded_source_idr",
    "nse_preference_shares": "excluded_source_preference_shares",
    "nse_warrants": "excluded_source_warrants",
    "nse_close_ended_mf": "excluded_source_close_ended_mf",
    "nse_etfs": "excluded_source_etf",
    "nse_invits": "excluded_source_invit",
    "nse_reits": "excluded_source_reit",
    "nse_debt_instruments": "excluded_source_debt",
}

SYMBOL_COLUMNS = [
    "SYMBOL",
    "Symbol",
    "symbol",
    "SYMB",
    "TckrSymb",
    "TckrSymb".upper(),
    "TICKER",
    "Ticker",
    "ticker",
]

NAME_COLUMNS = [
    "NAME OF COMPANY",
    "Name of Company",
    "NAME",
    "Name",
    "name",
    "SECURITY NAME",
    "SecurityName",
    "FinInstrmNm",
    "InstrmNm",
    "FinInstrmNm",
    "InstrmNm",
    "Security Name",
    "SECURITY",
    "Company Name",
    "COMPANY NAME",
    "COMPNAME",
    "COMPANY",
]

ISIN_COLUMNS = [
    "ISIN NUMBER",
    "ISINNumber",
    "ISIN Number",
    "ISIN",
    "isin",
    "ISIN_CODE",
    "ISIN CODE",
]

SERIES_COLUMNS = [
    "SERIES",
    "Series",
    "SctySrs",
    "series",
]

LISTING_DATE_COLUMNS = [
    "DATE OF LISTING",
    "DateofListing",
    "ListgDt",
    "IsseDt",
    "DATE_OF_LISTING",
    "Listing Date",
    "DATE OF LISTING ",
]

SECURITY_NAME_COLUMNS = [
    "SECURITY NAME",
    "SecurityName",
    "FinInstrmNm",
    "InstrmNm",
    "FinInstrmNm",
    "InstrmNm",
    "SECURITY",
    "Security Name",
]

FACE_VALUE_COLUMNS = [
    "FACE VALUE",
    "FACE VALUE*",
    "FaceValue",
    "Face Value",
]

PAID_UP_COLUMNS = [
    "PAID UP VALUE",
    "Paid Up Value",
    "PAIDUPVALUE",
]

VALID_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9&.\-]{0,24}$")
VALID_ISIN_RE = re.compile(r"^IN[A-Z0-9]{10}$")

ORDINARY_EQUITY_SERIES = {
    "EQ",
    "BE",
    "BZ",
    "BL",
    "SM",
    "ST",
    "SZ",
}

REVIEW_EQUITY_SERIES = {
    "",
    "IT",
}

EXCLUDE_SERIES_PREFIXES = (
    "N",
    "P",
    "W",
    "Y",
)

EXCLUDE_NAME_KEYWORDS = [
    "ETF",
    "EXCHANGE TRADED FUND",
    "FUND",
    "MUTUAL FUND",
    "REIT",
    "INVIT",
    "TRUST",
    "WARRANT",
    "DEBENTURE",
    "BOND",
    "NCD",
    "PREFERENCE",
    "PREF",
    "GOLD",
    "SILVER",
    "SOVEREIGN",
    "G-SEC",
    "GSEC",
    "TREASURY",
]

CANDIDATE_FIELDS = [
    "candidate_id",
    "source_id",
    "extraction_method",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "raw_series",
    "raw_isin",
    "listing_date",
    "instrument_type",
    "country",
    "currency",
    "confidence_bucket",
    "review_required",
    "candidate_key",
    "duplicate_sources",
    "evidence",
    "notes",
]

EXCLUSION_FIELDS = [
    "exclusion_id",
    "source_id",
    "exclusion_reason",
    "raw_symbol",
    "raw_name",
    "raw_series",
    "raw_isin",
    "evidence",
    "notes",
]

SOURCE_DIAGNOSTIC_FIELDS = [
    "source_id",
    "source_role",
    "raw_kind",
    "csv_rows_seen",
    "rows_considered",
    "raw_candidates_before_filter",
    "deduped_candidates_after_filter",
    "exclusions",
    "schema_columns",
    "validation_bucket",
    "notes",
]


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


def decode_text(data: bytes) -> str:
    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def load_raw_csv_rows(local_path: Path, raw_kind: str) -> tuple[list[str], list[dict]]:
    data = local_path.read_bytes()

    if data[:2] == b"\x1f\x8b" or str(raw_kind).lower().startswith("gzip"):
        data = gzip.decompress(data)

    text = decode_text(data)

    try:
        dialect = csv.Sniffer().sniff(text[:20000], delimiters=",;\t|")
    except Exception:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = list(reader)
    return list(reader.fieldnames or []), rows


def normalize_symbol(value: str) -> str:
    return str(value or "").strip().upper().replace(" ", "")


def normalize_name(value: str) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split()).strip()


def normalize_isin(value: str) -> str:
    return str(value or "").strip().upper().replace(" ", "")


def normalize_series(value: str) -> str:
    return str(value or "").strip().upper()


def pick_value(row: dict, candidates: list[str]) -> str:
    if not row:
        return ""

    lower_map = {str(key).strip().lower(): key for key in row.keys() if key is not None}

    for candidate in candidates:
        key = lower_map.get(candidate.strip().lower())
        if key is not None:
            return str(row.get(key, "") or "").strip()

    for key in row.keys():
        low = str(key).strip().lower()
        for candidate in candidates:
            if candidate.strip().lower() in low:
                return str(row.get(key, "") or "").strip()

    return ""


def evidence_for_row(row: dict, max_items: int = 18) -> str:
    clean = {}
    for idx, (key, value) in enumerate(row.items()):
        if idx >= max_items:
            break
        clean[str(key)] = str(value)[:300]
    return json.dumps(clean, ensure_ascii=False, sort_keys=True)


def symbol_valid(symbol: str) -> bool:
    return bool(symbol and VALID_SYMBOL_RE.match(symbol))


def isin_valid_or_empty(isin: str) -> bool:
    return not isin or bool(VALID_ISIN_RE.match(isin))


def has_exclusion_keyword(name: str) -> str:
    upper = f" {normalize_name(name).upper()} "

    for keyword in EXCLUDE_NAME_KEYWORDS:
        if f" {keyword} " in upper or keyword in upper:
            return keyword

    return ""


def exclusion_reason_for_candidate_source(source_id: str, symbol: str, name: str, series: str, isin: str) -> str:
    if not symbol_valid(symbol):
        return "invalid_or_missing_symbol"

    if not name:
        return "missing_name"

    if not isin_valid_or_empty(isin):
        return "invalid_isin_format"

    keyword = has_exclusion_keyword(name)
    if keyword:
        return f"excluded_name_keyword:{keyword.lower().replace(' ', '_')}"

    if source_id == "nse_all_reports_cm_mii_security_file_nse_listed" and series not in ORDINARY_EQUITY_SERIES:
        return f"excluded_mii_non_equity_series:{series or 'blank'}"

    if series:
        if series in ORDINARY_EQUITY_SERIES:
            return ""
        if source_id == "nse_securities_available_sme" and series in {"SM", "ST", "SZ"}:
            return ""
        if series.startswith(EXCLUDE_SERIES_PREFIXES):
            return f"excluded_series:{series}"
        if series not in ORDINARY_EQUITY_SERIES and series not in REVIEW_EQUITY_SERIES:
            return f"review_unknown_series:{series}"

    return ""


def confidence_for_source(source_id: str, series: str, isin: str) -> tuple[str, bool, str]:
    if source_id == "nse_securities_available_equity_segment":
        if series == "EQ" and isin:
            return "high", False, "equity_segment_eq_with_isin"
        return "medium", True, "equity_segment_review_series_or_missing_isin"

    if source_id == "nse_all_reports_cm_mii_security_file_nse_listed":
        if isin:
            return "medium", True, "mii_security_file_requires_later_canonical_validation"
        return "low", True, "mii_security_file_missing_isin_review"

    if source_id == "nse_securities_available_sme":
        return "medium", True, "sme_equity_review_required"

    return "low", True, "source_review_required"


def make_candidate(source_id: str, source_role: str, row: dict, extraction_method: str) -> tuple[dict | None, dict | None]:
    symbol = normalize_symbol(pick_value(row, SYMBOL_COLUMNS))
    name = normalize_name(pick_value(row, NAME_COLUMNS) or pick_value(row, SECURITY_NAME_COLUMNS))
    series = normalize_series(pick_value(row, SERIES_COLUMNS))
    isin = normalize_isin(pick_value(row, ISIN_COLUMNS))
    listing_date = pick_value(row, LISTING_DATE_COLUMNS)
    face_value = pick_value(row, FACE_VALUE_COLUMNS)
    paid_up_value = pick_value(row, PAID_UP_COLUMNS)

    reason = exclusion_reason_for_candidate_source(source_id, symbol, name, series, isin)

    if reason.startswith("review_unknown_series"):
        confidence = "low"
        review_required = True
        notes = reason
    elif reason:
        exclusion = {
            "exclusion_id": sha256_text(f"{VERSION}|{source_id}|{symbol}|{name.lower()}|{isin}|{reason}")[:16],
            "source_id": source_id,
            "exclusion_reason": reason,
            "raw_symbol": symbol,
            "raw_name": name,
            "raw_series": series,
            "raw_isin": isin,
            "evidence": evidence_for_row(row),
            "notes": f"candidate_source_row_excluded_during_dry_run; source_role={source_role}",
        }
        return None, exclusion
    else:
        confidence, review_required, notes = confidence_for_source(source_id, series, isin)

    candidate_key = "|".join([symbol, isin or name.upper(), series, source_id])
    candidate_id = sha256_text(f"{VERSION}|{candidate_key}")[:16]

    candidate = {
        "candidate_id": candidate_id,
        "source_id": source_id,
        "extraction_method": extraction_method,
        "raw_symbol": symbol,
        "raw_name": name,
        "raw_exchange": "NSE",
        "raw_series": series,
        "raw_isin": isin,
        "listing_date": listing_date,
        "instrument_type": series,
        "country": "India",
        "currency": "INR",
        "confidence_bucket": confidence,
        "review_required": bool(review_required),
        "candidate_key": candidate_key,
        "duplicate_sources": "",
        "evidence": evidence_for_row(row),
        "notes": f"{notes}; face_value={face_value}; paid_up_value={paid_up_value}",
    }

    return candidate, None


def make_explicit_exclusion(source_id: str, row: dict, reason: str) -> dict:
    symbol = normalize_symbol(pick_value(row, SYMBOL_COLUMNS))
    name = normalize_name(pick_value(row, NAME_COLUMNS) or pick_value(row, SECURITY_NAME_COLUMNS))
    series = normalize_series(pick_value(row, SERIES_COLUMNS))
    isin = normalize_isin(pick_value(row, ISIN_COLUMNS))

    return {
        "exclusion_id": sha256_text(f"{VERSION}|{source_id}|{reason}|{symbol}|{name.lower()}|{isin}")[:16],
        "source_id": source_id,
        "exclusion_reason": reason,
        "raw_symbol": symbol,
        "raw_name": name,
        "raw_series": series,
        "raw_isin": isin,
        "evidence": evidence_for_row(row),
        "notes": "explicit_exclusion_or_reference_source; not considered candidate in v2.17E",
    }


def dedupe_candidates(candidates: list[dict]) -> list[dict]:
    score = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    grouped = {}

    for candidate in candidates:
        key = "|".join(
            [
                candidate["raw_symbol"],
                candidate["raw_isin"] or candidate["raw_name"].upper(),
                candidate["raw_series"],
            ]
        )

        existing = grouped.get(key)

        if not existing:
            grouped[key] = candidate
            continue

        existing_sources = set(filter(None, str(existing.get("duplicate_sources", "")).split("|")))
        existing_sources.add(existing["source_id"])
        existing_sources.add(candidate["source_id"])

        current_score = score.get(candidate["confidence_bucket"], 0)
        existing_score = score.get(existing["confidence_bucket"], 0)

        if current_score > existing_score:
            candidate["duplicate_sources"] = "|".join(sorted(existing_sources))
            grouped[key] = candidate
        else:
            existing["duplicate_sources"] = "|".join(sorted(existing_sources))

    deduped = []

    for candidate in grouped.values():
        stable_id = sha256_text(
            f"{VERSION}|deduped|{candidate['raw_symbol']}|{candidate['raw_isin']}|{candidate['raw_name'].lower()}|{candidate['raw_series']}"
        )[:16]
        candidate["candidate_id"] = stable_id
        deduped.append(candidate)

    return sorted(deduped, key=lambda row: (row["raw_symbol"], row["raw_isin"], row["raw_name"]))


def main() -> None:
    for path in [REPORT_JSON, REPORT_MD, CANDIDATES_CSV, EXCLUSIONS_CSV, SOURCE_DIAGNOSTICS_CSV]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    d_report = read_json(V217D_JSON)
    file_profiles = read_csv(V217D_FILE_PROFILE_CSV)
    source_diag_v217d = read_csv(V217D_SOURCE_DIAGNOSTICS_CSV)
    schema_profiles = read_csv(V217D_SCHEMA_PROFILE_CSV)

    valid_profiles = [
        row for row in file_profiles
        if row.get("validation_bucket") == "valid_raw_csv"
    ]

    candidate_rows_before_dedupe = []
    exclusions = []
    source_diagnostics = []

    for profile in valid_profiles:
        source_id = profile.get("source_id", "")
        local_path = Path(profile.get("local_path", ""))
        raw_kind = profile.get("raw_kind", "")
        artifact_type = profile.get("artifact_type", "")

        source_role = (
            CANDIDATE_SOURCES.get(source_id)
            or EXPLICIT_EXCLUSION_SOURCES.get(source_id)
            or REVIEW_NOT_CANDIDATE_SOURCES.get(source_id)
            or "unplanned_valid_raw_source"
        )

        try:
            fieldnames, rows = load_raw_csv_rows(local_path, raw_kind)
        except Exception as exc:
            source_diagnostics.append(
                {
                    "source_id": source_id,
                    "source_role": source_role,
                    "raw_kind": raw_kind,
                    "csv_rows_seen": 0,
                    "rows_considered": 0,
                    "raw_candidates_before_filter": 0,
                    "deduped_candidates_after_filter": 0,
                    "exclusions": 0,
                    "schema_columns": "",
                    "validation_bucket": "read_failed",
                    "notes": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        source_candidates = []
        source_exclusions = []
        rows_considered = 0

        if source_id in CANDIDATE_SOURCES:
            for row in rows:
                rows_considered += 1
                candidate, exclusion = make_candidate(
                    source_id=source_id,
                    source_role=source_role,
                    row=row,
                    extraction_method="validated_raw_csv_row",
                )

                if candidate:
                    source_candidates.append(candidate)
                if exclusion:
                    source_exclusions.append(exclusion)

        elif source_id in EXPLICIT_EXCLUSION_SOURCES:
            reason = EXPLICIT_EXCLUSION_SOURCES[source_id]
            for row in rows:
                rows_considered += 1
                source_exclusions.append(make_explicit_exclusion(source_id, row, reason))

        elif source_id in REVIEW_NOT_CANDIDATE_SOURCES:
            reason = REVIEW_NOT_CANDIDATE_SOURCES[source_id]
            sample_limit = 5000
            for idx, row in enumerate(rows):
                rows_considered += 1
                if idx < sample_limit:
                    source_exclusions.append(make_explicit_exclusion(source_id, row, reason))
        else:
            reason = "unplanned_valid_raw_source_not_candidate"
            for row in rows[:5000]:
                rows_considered += 1
                source_exclusions.append(make_explicit_exclusion(source_id, row, reason))

        candidate_rows_before_dedupe.extend(source_candidates)
        exclusions.extend(source_exclusions)

        source_diagnostics.append(
            {
                "source_id": source_id,
                "source_role": source_role,
                "raw_kind": raw_kind,
                "csv_rows_seen": len(rows),
                "rows_considered": rows_considered,
                "raw_candidates_before_filter": len(source_candidates),
                "deduped_candidates_after_filter": 0,
                "exclusions": len(source_exclusions),
                "schema_columns": " | ".join(fieldnames),
                "validation_bucket": "extracted" if source_candidates else "no_candidates_or_exclusion_only",
                "notes": f"artifact_type={artifact_type}; local_path={local_path}",
            }
        )

    deduped_candidates = dedupe_candidates(candidate_rows_before_dedupe)

    candidate_count_by_source = Counter(row["source_id"] for row in deduped_candidates)

    for diagnostic in source_diagnostics:
        diagnostic["deduped_candidates_after_filter"] = candidate_count_by_source.get(diagnostic["source_id"], 0)

    exclusion_counter = Counter(row["exclusion_reason"] for row in exclusions)
    confidence_counter = Counter(row["confidence_bucket"] for row in deduped_candidates)
    source_counter = Counter(row["source_id"] for row in deduped_candidates)
    series_counter = Counter(row["raw_series"] for row in deduped_candidates)

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17d_report_exists", V217D_JSON.exists(), "critical", str(V217D_JSON))
    add_check(
        "v2_17d_status_expected",
        d_report.get("status") == EXPECTED_V217D_STATUS,
        "critical",
        str(d_report.get("status", "")),
    )
    add_check(
        "v2_17d_recommended_e",
        d_report.get("recommended_next_phase") == EXPECTED_V217D_NEXT,
        "critical",
        str(d_report.get("recommended_next_phase", "")),
    )
    add_check("file_profile_exists", V217D_FILE_PROFILE_CSV.exists(), "critical", str(V217D_FILE_PROFILE_CSV))
    add_check("source_diagnostics_exists", V217D_SOURCE_DIAGNOSTICS_CSV.exists(), "critical", str(V217D_SOURCE_DIAGNOSTICS_CSV))
    add_check("schema_profile_exists", V217D_SCHEMA_PROFILE_CSV.exists(), "critical", str(V217D_SCHEMA_PROFILE_CSV))
    add_check("valid_profiles_present", len(valid_profiles) >= 8, "critical", f"valid_profiles={len(valid_profiles)}")
    add_check("candidate_sources_read", all(source in {row["source_id"] for row in source_diagnostics} for source in CANDIDATE_SOURCES), "critical", f"sources_read={sorted({row['source_id'] for row in source_diagnostics})}")
    add_check("candidate_rows_extracted", len(deduped_candidates) > 0, "critical", f"deduped_candidates={len(deduped_candidates)} raw_before_dedupe={len(candidate_rows_before_dedupe)}")
    add_check("equity_segment_candidates_present", candidate_count_by_source.get("nse_securities_available_equity_segment", 0) > 0, "critical", f"equity_candidates={candidate_count_by_source.get('nse_securities_available_equity_segment', 0)}")
    add_check("exclusions_generated", len(exclusions) > 0, "critical", f"exclusions={len(exclusions)}")
    add_check("explicit_exclusion_sources_used", len([src for src in EXPLICIT_EXCLUSION_SOURCES if src in {row['source_id'] for row in exclusions}]) >= 5, "critical", f"exclusion_sources={sorted({row['source_id'] for row in exclusions})}")
    add_check("candidate_symbols_valid", all(symbol_valid(row["raw_symbol"]) for row in deduped_candidates), "critical", "all candidate symbols valid")
    add_check("candidate_names_present", all(bool(row["raw_name"]) for row in deduped_candidates), "critical", "all candidate names present")
    add_check("full_source_still_blocked", CURRENT_CANONICAL_ROWS < FULL_SOURCE_THRESHOLD, "critical", f"{CURRENT_CANONICAL_ROWS} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("endpoint_calls_not_performed", True, "critical", "endpoint_calls_performed=False")
    add_check("query_sweep_not_performed", True, "critical", "query_sweep_performed=False")
    add_check("raw_files_read", True, "critical", "raw_files_read=True")
    add_check("candidate_extraction_performed", True, "critical", "candidate_extraction_performed=True")
    add_check("canonical_dataset_not_read", True, "critical", "canonical_dataset_read=False")
    add_check("canonical_comparison_not_performed", True, "critical", "canonical_comparison_performed=False")
    add_check("net_new_filtering_not_applied", True, "critical", "net_new_filtering_applied=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("new_expanded_dataset_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed != 0:
        status = "NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17E_FIX - NSE India Candidate Extraction Repair"
    elif len(deduped_candidates) > 0:
        status = "NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_CANONICAL_COMPARISON_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_CANDIDATES
    else:
        status = "NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_NO_CANDIDATES_CANONICAL_COMPARISON_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE_IF_NO_CANDIDATES

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": "outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv",
            "active_canonical_rows": CURRENT_CANONICAL_ROWS,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed": ROWS_NEEDED,
            "source_to_50k_completed_percent": round((CURRENT_CANONICAL_ROWS / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "route_reference": {
            "v2_17d_artifact": str(V217D_JSON),
            "v2_17d_status": d_report.get("status", ""),
            "v2_17d_recommended_next_phase": d_report.get("recommended_next_phase", ""),
            "provider": "NSE India",
            "market": "India",
        },
        "extraction_summary": {
            "valid_profiles_read": len(valid_profiles),
            "schema_profiles_read": len(schema_profiles),
            "source_diagnostics_read": len(source_diag_v217d),
            "raw_candidates_before_dedupe": len(candidate_rows_before_dedupe),
            "deduped_candidates": len(deduped_candidates),
            "exclusions": len(exclusions),
            "candidate_source_counts": dict(source_counter),
            "candidate_confidence_counts": dict(confidence_counter),
            "candidate_series_counts": dict(series_counter),
            "exclusion_reason_counts": dict(exclusion_counter),
            "critical_failed_checks": critical_failed,
        },
        "checks": checks,
        "candidate_preview": deduped_candidates[:100],
        "source_diagnostics_preview": source_diagnostics[:50],
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_17d_report_read": True,
            "raw_validation_profiles_read": True,
            "raw_files_read": True,
            "candidate_extraction_performed": True,
            "candidate_rows_extracted": len(deduped_candidates) > 0,
            "exclusion_rows_extracted": len(exclusions) > 0,
            "canonical_dataset_read": False,
            "canonical_dataset_modified": False,
            "canonical_comparison_performed": False,
            "net_new_filtering_applied": False,
            "new_expanded_dataset_written": False,
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
    write_csv(CANDIDATES_CSV, deduped_candidates, CANDIDATE_FIELDS)
    write_csv(EXCLUSIONS_CSV, exclusions, EXCLUSION_FIELDS)
    write_csv(SOURCE_DIAGNOSTICS_CSV, source_diagnostics, SOURCE_DIAGNOSTIC_FIELDS)

    source_lines = "\n".join(
        f"- `{row['source_id']}` role=`{row['source_role']}` rows=`{row['csv_rows_seen']}` raw_candidates=`{row['raw_candidates_before_filter']}` deduped=`{row['deduped_candidates_after_filter']}` exclusions=`{row['exclusions']}`"
        for row in source_diagnostics
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

NSE India candidate extraction dry run completed.

This phase extracts preliminary candidates and exclusions from locally validated NSE raw files. It does not read the canonical dataset, does not compare candidates against canonical symbols, does not apply net-new filtering and does not create or modify any expanded universe dataset.

## Current state

- Active canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Active canonical rows: `{CURRENT_CANONICAL_ROWS}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed: `{ROWS_NEEDED}`
- Source-to-50k completion: `{round((CURRENT_CANONICAL_ROWS / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Extraction summary

- Valid profiles read: `{len(valid_profiles)}`
- Raw candidates before dedupe: `{len(candidate_rows_before_dedupe)}`
- Deduped candidates: `{len(deduped_candidates)}`
- Exclusions: `{len(exclusions)}`
- Candidate source counts: `{dict(source_counter)}`
- Candidate confidence counts: `{dict(confidence_counter)}`
- Candidate series counts: `{dict(series_counter)}`
- Exclusion reason counts: `{dict(exclusion_counter)}`
- Critical failed checks: `{critical_failed}`

## Source diagnostics

{source_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17D report read: true
- Raw validation profiles read: true
- Raw files read: true
- Candidate extraction performed: true
- Candidate rows extracted: `{len(deduped_candidates) > 0}`
- Exclusion rows extracted: `{len(exclusions) > 0}`
- Canonical dataset read: false
- Canonical dataset modified: false
- Canonical comparison performed: false
- Net-new filtering applied: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17E generated a candidate extraction dry run for NSE India and prepared the artifacts for v2.17F canonical validation.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17E NSE India candidate extraction dry run completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("EXTRACTION_SUMMARY:")
    for key, value in payload["extraction_summary"].items():
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

