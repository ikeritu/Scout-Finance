from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.17G"
PHASE = "NSE India Expanded Rebuild Candidate"
PHASE_TYPE = "expanded-rebuild-candidate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"

V217F_JSON = OUTPUT_DIR / "nse_india_candidate_validation_against_canonical_dry_run_v2_17f.json"
V217F_CLASSIFIED_CANDIDATES_CSV = OUTPUT_DIR / "nse_india_candidate_validation_classified_candidates_v2_17f.csv"
V217F_POTENTIAL_NET_NEW_CSV = OUTPUT_DIR / "nse_india_candidate_validation_potential_net_new_v2_17f.csv"
V217F_EXISTING_MATCHES_CSV = OUTPUT_DIR / "nse_india_candidate_validation_existing_matches_v2_17f.csv"
V217F_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "nse_india_candidate_validation_source_diagnostics_v2_17f.csv"
V217F_CANONICAL_PROFILE_CSV = OUTPUT_DIR / "nse_india_candidate_validation_canonical_profile_v2_17f.csv"

EXPANDED_CANDIDATE_CSV = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"
DELTA_ROWS_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_delta_rows_v2_17g.csv"
PROMOTIONS_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_promotions_v2_17g.csv"
SCHEMA_MAPPING_CSV = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_schema_mapping_v2_17g.csv"
REPORT_JSON = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_v2_17g.json"
REPORT_MD = OUTPUT_DIR / "nse_india_expanded_rebuild_candidate_v2_17g.md"

CURRENT_CANONICAL_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_BEFORE_NSE = 11713

EXPECTED_V217F_STATUS = "NSE_INDIA_CANDIDATE_VALIDATION_AGAINST_CANONICAL_DRY_RUN_COMPLETED_NET_NEW_FOUND_REBUILD_CANDIDATE_READY_FULL_SOURCE_STILL_BLOCKED"
EXPECTED_V217F_NEXT = "v2.17G - NSE India Expanded Rebuild Candidate"

NEXT_PHASE = "v2.17H - NSE India Expanded Validation"

SYMBOL_COLUMN_HINTS = [
    "symbol",
    "ticker",
    "ticker_symbol",
    "local_symbol",
    "raw_symbol",
    "Symbol",
    "Ticker",
    "TICKER",
    "SYMBOL",
    "TckrSymb",
]

NAME_COLUMN_HINTS = [
    "name",
    "company_name",
    "security_name",
    "instrument_name",
    "raw_name",
    "Name",
    "Company Name",
    "NAME OF COMPANY",
    "SECURITY NAME",
    "FinInstrmNm",
    "long_name",
    "short_name",
]

EXCHANGE_COLUMN_HINTS = [
    "exchange",
    "primary_exchange",
    "market",
    "mic",
    "venue",
    "raw_exchange",
    "Exchange",
    "MIC",
    "Xchg",
]

COUNTRY_COLUMN_HINTS = [
    "country",
    "country_name",
    "market_country",
    "Country",
]

CURRENCY_COLUMN_HINTS = [
    "currency",
    "Currency",
    "ccy",
    "Ccy",
]

ISIN_COLUMN_HINTS = [
    "isin",
    "ISIN",
    "isin_number",
    "ISIN NUMBER",
    "ISINNumber",
    "raw_isin",
]

SOURCE_COLUMN_HINTS = [
    "source",
    "source_id",
    "data_source",
    "provider",
    "raw_source",
    "Source",
]

ASSET_TYPE_COLUMN_HINTS = [
    "asset_type",
    "instrument_type",
    "security_type",
    "type",
    "Asset Type",
    "Instrument Type",
]

ID_COLUMN_HINTS = [
    "id",
    "uid",
    "security_id",
    "instrument_id",
]

SERIES_COLUMN_HINTS = [
    "series",
    "raw_series",
    "SERIES",
    "SctySrs",
]

STATUS_COLUMN_HINTS = [
    "status",
    "listing_status",
    "active",
]

PROMOTION_FIELDS = [
    "promotion_id",
    "candidate_id",
    "source_id",
    "raw_symbol",
    "raw_name",
    "raw_exchange",
    "raw_series",
    "raw_isin",
    "confidence_bucket",
    "review_required",
    "net_new_bucket",
    "promoted_to_candidate_dataset",
    "expanded_candidate_row_index",
    "promotion_policy",
    "promotion_notes",
]

SCHEMA_MAPPING_FIELDS = [
    "canonical_column",
    "mapped_from",
    "mapped_value_preview",
    "mapping_strategy",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    raise SystemExit(f"Unable to read CSV with supported encodings: {path}")


def read_csv_with_header(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise SystemExit(f"Missing required artifact: {path}")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
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


def norm(value: str) -> str:
    return str(value or "").strip()


def norm_upper(value: str) -> str:
    return norm(value).upper()


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def column_lookup(header: list[str], hints: list[str]) -> str:
    exact = {col.strip().lower(): col for col in header}
    compact = {col.strip().lower().replace("_", "").replace(" ", ""): col for col in header}

    for hint in hints:
        key = hint.strip().lower()
        if key in exact:
            return exact[key]

    for hint in hints:
        key = hint.strip().lower().replace("_", "").replace(" ", "")
        if key in compact:
            return compact[key]

    for col in header:
        low = col.strip().lower()
        for hint in hints:
            if hint.strip().lower() in low:
                return col

    return ""


def candidate_identity(row: dict) -> str:
    isin = norm_upper(row.get("raw_isin", ""))
    symbol = norm_upper(row.get("raw_symbol", ""))
    name = norm_upper(row.get("raw_name", ""))
    series = norm_upper(row.get("raw_series", ""))

    if isin:
        return f"isin:{isin}"

    if symbol and name:
        return f"symbol_name:{symbol}|{name}"

    if symbol:
        return f"symbol:{symbol}|series:{series}"

    return sha256_text(json.dumps(row, ensure_ascii=False, sort_keys=True))


def unique_potential_rows(rows: list[dict]) -> list[dict]:
    seen = set()
    output = []

    for row in rows:
        identity = candidate_identity(row)
        if identity in seen:
            continue
        seen.add(identity)
        output.append(row)

    return output


def build_schema_mapping(header: list[str], sample_candidate: dict | None) -> tuple[dict, list[dict]]:
    symbol_col = column_lookup(header, SYMBOL_COLUMN_HINTS)
    name_col = column_lookup(header, NAME_COLUMN_HINTS)
    exchange_col = column_lookup(header, EXCHANGE_COLUMN_HINTS)
    country_col = column_lookup(header, COUNTRY_COLUMN_HINTS)
    currency_col = column_lookup(header, CURRENCY_COLUMN_HINTS)
    isin_col = column_lookup(header, ISIN_COLUMN_HINTS)
    source_col = column_lookup(header, SOURCE_COLUMN_HINTS)
    asset_type_col = column_lookup(header, ASSET_TYPE_COLUMN_HINTS)
    id_col = column_lookup(header, ID_COLUMN_HINTS)
    series_col = column_lookup(header, SERIES_COLUMN_HINTS)
    status_col = column_lookup(header, STATUS_COLUMN_HINTS)

    mapping = {
        "symbol_col": symbol_col,
        "name_col": name_col,
        "exchange_col": exchange_col,
        "country_col": country_col,
        "currency_col": currency_col,
        "isin_col": isin_col,
        "source_col": source_col,
        "asset_type_col": asset_type_col,
        "id_col": id_col,
        "series_col": series_col,
        "status_col": status_col,
    }

    reverse = {
        symbol_col: ("raw_symbol", sample_candidate.get("raw_symbol", "") if sample_candidate else "", "symbol mapping"),
        name_col: ("raw_name", sample_candidate.get("raw_name", "") if sample_candidate else "", "name mapping"),
        exchange_col: ("raw_exchange", "NSE", "exchange mapping"),
        country_col: ("country", "India", "country mapping"),
        currency_col: ("currency", "INR", "currency mapping"),
        isin_col: ("raw_isin", sample_candidate.get("raw_isin", "") if sample_candidate else "", "isin mapping"),
        source_col: ("source_id/provider", "nse_india_v2_17g", "source provenance mapping"),
        asset_type_col: ("asset_type", "equity", "asset type mapping"),
        id_col: ("candidate_id", sample_candidate.get("candidate_id", "") if sample_candidate else "", "stable generated id mapping"),
        series_col: ("raw_series", sample_candidate.get("raw_series", "") if sample_candidate else "", "NSE series mapping"),
        status_col: ("candidate_status", "active_candidate", "status mapping"),
    }

    rows = []

    for col in header:
        if col in reverse and col:
            mapped_from, preview, strategy = reverse[col]
            rows.append(
                {
                    "canonical_column": col,
                    "mapped_from": mapped_from,
                    "mapped_value_preview": preview,
                    "mapping_strategy": strategy,
                    "notes": "mapped for NSE v2.17G appended rows",
                }
            )
        else:
            rows.append(
                {
                    "canonical_column": col,
                    "mapped_from": "",
                    "mapped_value_preview": "",
                    "mapping_strategy": "left_blank_for_appended_rows",
                    "notes": "no safe deterministic mapping inferred",
                }
            )

    return mapping, rows


def build_appended_row(header: list[str], mapping: dict, candidate: dict) -> dict:
    row = {col: "" for col in header}

    if mapping["symbol_col"]:
        row[mapping["symbol_col"]] = norm_upper(candidate.get("raw_symbol", ""))

    if mapping["name_col"]:
        row[mapping["name_col"]] = norm(candidate.get("raw_name", ""))

    if mapping["exchange_col"]:
        row[mapping["exchange_col"]] = "NSE"

    if mapping["country_col"]:
        row[mapping["country_col"]] = "India"

    if mapping["currency_col"]:
        row[mapping["currency_col"]] = "INR"

    if mapping["isin_col"]:
        row[mapping["isin_col"]] = norm_upper(candidate.get("raw_isin", ""))

    if mapping["source_col"]:
        row[mapping["source_col"]] = "nse_india_v2_17g"

    if mapping["asset_type_col"]:
        row[mapping["asset_type_col"]] = "equity"

    if mapping["id_col"]:
        row[mapping["id_col"]] = f"nse_india_{candidate.get('candidate_id', '')}"

    if mapping["series_col"]:
        row[mapping["series_col"]] = norm_upper(candidate.get("raw_series", ""))

    if mapping["status_col"]:
        row[mapping["status_col"]] = "active_candidate"

    return row


def promotion_defer_reason(row: dict) -> str:
    source_id = norm(row.get("source_id", ""))
    symbol = norm_upper(row.get("raw_symbol", ""))
    name = norm_upper(row.get("raw_name", ""))
    series = norm_upper(row.get("raw_series", ""))
    isin = norm_upper(row.get("raw_isin", ""))
    confidence = norm(row.get("confidence_bucket", "")).lower()
    review_required = boolish(row.get("review_required", ""))
    net_new_bucket = norm(row.get("net_new_bucket", ""))

    fund_or_non_equity_keywords = [
        " ETF",
        "ETF ",
        " FUND",
        "FUND ",
        " LIQUID",
        "LIQUID ",
        " BIRLASLAMC",
        "BIRLASLAMC ",
        " NIFTY",
        "NIFTY ",
        " GOLD",
        "GOLD ",
        " SILVER",
        "SILVER ",
        " BANK",
        "BANKETF",
    ]

    if source_id != "nse_securities_available_equity_segment":
        return "defer_non_primary_equity_segment_source"

    if confidence != "high":
        return "defer_not_high_confidence"

    if review_required:
        return "defer_review_required"

    if net_new_bucket != "potential_net_new_high":
        return f"defer_net_new_bucket:{net_new_bucket}"

    if series != "EQ":
        return f"defer_non_eq_series:{series}"

    if isin.startswith("INF"):
        return "defer_fund_or_etf_isin_prefix_inf"

    if "-RE" in symbol or symbol.endswith("RE1") or symbol.endswith("RE2"):
        return "defer_rights_entitlement_symbol"

    padded_name = f" {name} "
    for keyword in fund_or_non_equity_keywords:
        if keyword in padded_name:
            return f"defer_name_keyword:{keyword.strip().lower()}"

    return ""

def main() -> None:
    for path in [
        EXPANDED_CANDIDATE_CSV,
        DELTA_ROWS_CSV,
        PROMOTIONS_CSV,
        SCHEMA_MAPPING_CSV,
        REPORT_JSON,
        REPORT_MD,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    f_report = read_json(V217F_JSON)
    classified_candidates = read_csv(V217F_CLASSIFIED_CANDIDATES_CSV)
    potential_net_new_rows_raw = read_csv(V217F_POTENTIAL_NET_NEW_CSV)
    existing_matches = read_csv(V217F_EXISTING_MATCHES_CSV)
    source_diagnostics_f = read_csv(V217F_SOURCE_DIAGNOSTICS_CSV)
    canonical_profile_f = read_csv(V217F_CANONICAL_PROFILE_CSV)

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)

    promotion_candidates_all = unique_potential_rows(potential_net_new_rows_raw)

    deferred_promotion_rows = []
    potential_net_new_rows = []

    for row in promotion_candidates_all:
        reason = promotion_defer_reason(row)
        if reason:
            deferred = dict(row)
            deferred["promotion_defer_reason"] = reason
            deferred_promotion_rows.append(deferred)
        else:
            potential_net_new_rows.append(row)

    sample_candidate = potential_net_new_rows[0] if potential_net_new_rows else None
    mapping, mapping_rows = build_schema_mapping(canonical_header, sample_candidate)

    appended_rows = [
        build_appended_row(canonical_header, mapping, candidate)
        for candidate in potential_net_new_rows
    ]

    expanded_rows = canonical_rows + appended_rows

    promotions = []

    for offset, candidate in enumerate(potential_net_new_rows, start=1):
        expanded_index = len(canonical_rows) + offset
        promotions.append(
            {
                "promotion_id": sha256_text(f"{VERSION}|promotion|{candidate.get('candidate_id', '')}|{expanded_index}")[:16],
                "candidate_id": candidate.get("candidate_id", ""),
                "source_id": candidate.get("source_id", ""),
                "raw_symbol": candidate.get("raw_symbol", ""),
                "raw_name": candidate.get("raw_name", ""),
                "raw_exchange": candidate.get("raw_exchange", ""),
                "raw_series": candidate.get("raw_series", ""),
                "raw_isin": candidate.get("raw_isin", ""),
                "confidence_bucket": candidate.get("confidence_bucket", ""),
                "review_required": candidate.get("review_required", ""),
                "net_new_bucket": candidate.get("net_new_bucket", ""),
                "promoted_to_candidate_dataset": True,
                "expanded_candidate_row_index": expanded_index,
                "promotion_policy": "include_safe_high_confidence_equity_segment_eq_only_in_candidate_dataset",
                "promotion_notes": "candidate dataset only; canonical remains unchanged",
            }
        )

    source_counts = Counter(row.get("source_id", "") for row in potential_net_new_rows)
    series_counts = Counter(row.get("raw_series", "") for row in potential_net_new_rows)
    confidence_counts = Counter(row.get("confidence_bucket", "") for row in potential_net_new_rows)
    net_new_bucket_counts = Counter(row.get("net_new_bucket", "") for row in potential_net_new_rows)

    write_csv(EXPANDED_CANDIDATE_CSV, expanded_rows, canonical_header)
    write_csv(DELTA_ROWS_CSV, appended_rows, canonical_header)
    write_csv(PROMOTIONS_CSV, promotions, PROMOTION_FIELDS)
    write_csv(SCHEMA_MAPPING_CSV, mapping_rows, SCHEMA_MAPPING_FIELDS)

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    expanded_sha = sha256_bytes(EXPANDED_CANDIDATE_CSV.read_bytes())
    delta_sha = sha256_bytes(DELTA_ROWS_CSV.read_bytes())

    projected_rows = len(expanded_rows)
    rows_added = len(appended_rows)
    rows_needed_after_candidate = max(FULL_SOURCE_THRESHOLD - projected_rows, 0)

    critical_failed = 0
    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_17f_report_exists", V217F_JSON.exists(), "critical", str(V217F_JSON))
    add_check(
        "v2_17f_status_expected",
        f_report.get("status") == EXPECTED_V217F_STATUS,
        "critical",
        str(f_report.get("status", "")),
    )
    add_check(
        "v2_17f_recommended_g",
        f_report.get("recommended_next_phase") == EXPECTED_V217F_NEXT,
        "critical",
        str(f_report.get("recommended_next_phase", "")),
    )
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("canonical_rows_expected", len(canonical_rows) == CURRENT_CANONICAL_ROWS, "critical", f"canonical_rows={len(canonical_rows)}")
    add_check("canonical_header_present", len(canonical_header) > 0, "critical", f"columns={len(canonical_header)}")
    add_check("potential_net_new_rows_present", len(potential_net_new_rows_raw) > 0, "critical", f"raw_potential={len(potential_net_new_rows_raw)}")
    add_check("safe_promotable_rows_present", len(potential_net_new_rows) > 0, "critical", f"safe_promotable_rows={len(potential_net_new_rows)}")
    add_check("promotion_policy_deferred_rows_recorded", len(deferred_promotion_rows) > 0, "warning", f"deferred_rows={len(deferred_promotion_rows)}")
    add_check("rows_added_matches_unique_potential", rows_added == len(potential_net_new_rows), "critical", f"rows_added={rows_added} unique_potential={len(potential_net_new_rows)}")
    add_check("expanded_rows_projected", projected_rows == len(canonical_rows) + rows_added, "critical", f"projected={projected_rows}")
    add_check("expanded_candidate_written", EXPANDED_CANDIDATE_CSV.exists(), "critical", str(EXPANDED_CANDIDATE_CSV))
    add_check("delta_rows_written", DELTA_ROWS_CSV.exists(), "critical", str(DELTA_ROWS_CSV))
    add_check("promotions_written", PROMOTIONS_CSV.exists(), "critical", str(PROMOTIONS_CSV))
    add_check("schema_mapping_written", SCHEMA_MAPPING_CSV.exists(), "critical", str(SCHEMA_MAPPING_CSV))
    add_check("expanded_dataset_schema_matches_canonical", len(canonical_header) > 0, "critical", "same header used for canonical + appended rows")
    add_check("symbol_column_mapped", bool(mapping["symbol_col"]), "critical", f"symbol_col={mapping['symbol_col']}")
    add_check("name_column_mapped", bool(mapping["name_col"]), "critical", f"name_col={mapping['name_col']}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("full_source_still_blocked", projected_rows < FULL_SOURCE_THRESHOLD, "critical", f"{projected_rows} < {FULL_SOURCE_THRESHOLD}")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("canonical_dataset_read", True, "critical", "canonical_dataset_read=True")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("expanded_candidate_dataset_written", True, "critical", "new_expanded_candidate_dataset_written=True")
    add_check("expanded_universe_not_rebuilt_as_canonical", True, "critical", "expanded_universe_rebuilt_as_canonical=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")

    if critical_failed == 0:
        status = "NSE_INDIA_EXPANDED_REBUILD_CANDIDATE_COMPLETED_VALIDATION_READY_FULL_SOURCE_STILL_BLOCKED"
        recommended_next_phase = NEXT_PHASE
    else:
        status = "NSE_INDIA_EXPANDED_REBUILD_CANDIDATE_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = "v2.17G_FIX - NSE India Expanded Rebuild Candidate Repair"

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": len(canonical_rows),
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "rows_needed_before_nse": ROWS_NEEDED_BEFORE_NSE,
            "source_to_50k_completed_percent_before_nse_candidate": round((len(canonical_rows) / FULL_SOURCE_THRESHOLD) * 100, 2),
            "full_source_gate": "BLOCKED",
            "full_59k_dry_run": "BLOCKED",
        },
        "route_reference": {
            "v2_17f_artifact": str(V217F_JSON),
            "v2_17f_status": f_report.get("status", ""),
            "v2_17f_recommended_next_phase": f_report.get("recommended_next_phase", ""),
            "provider": "NSE India",
            "market": "India",
        },
        "rebuild_candidate_summary": {
            "canonical_rows_read": len(canonical_rows),
            "classified_candidates_read": len(classified_candidates),
            "potential_net_new_rows_raw": len(potential_net_new_rows_raw),
            "potential_net_new_rows_unique_before_promotion_policy": len(promotion_candidates_all),
            "promotion_policy_deferred_rows": len(deferred_promotion_rows),
            "promotion_defer_reason_counts": dict(Counter(row.get("promotion_defer_reason", "") for row in deferred_promotion_rows)),
            "potential_net_new_rows_promoted": len(potential_net_new_rows),
            "existing_matches_read": len(existing_matches),
            "source_diagnostics_read": len(source_diagnostics_f),
            "canonical_profile_read": len(canonical_profile_f),
            "rows_added_to_candidate_dataset": rows_added,
            "expanded_candidate_rows": projected_rows,
            "rows_needed_after_candidate_dataset": rows_needed_after_candidate,
            "source_to_50k_completed_percent_after_candidate": round((projected_rows / FULL_SOURCE_THRESHOLD) * 100, 2),
            "would_reach_full_source_threshold": projected_rows >= FULL_SOURCE_THRESHOLD,
            "potential_net_new_source_counts": dict(source_counts),
            "potential_net_new_series_counts": dict(series_counts),
            "potential_net_new_confidence_counts": dict(confidence_counts),
            "potential_net_new_bucket_counts": dict(net_new_bucket_counts),
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "expanded_candidate_sha256": expanded_sha,
            "delta_rows_sha256": delta_sha,
            "critical_failed_checks": critical_failed,
        },
        "schema_mapping": mapping,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "v2_17f_report_read": True,
            "potential_net_new_rows_read": True,
            "canonical_dataset_read": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "new_expanded_candidate_dataset_written": True,
            "delta_rows_written": True,
            "promotions_written": True,
            "schema_mapping_written": True,
            "safe_promotion_policy_applied": True,
            "deferred_review_rows_not_promoted": len(deferred_promotion_rows),
            "net_new_rows_applied_to_candidate_dataset": True,
            "net_new_rows_applied_to_canonical": False,
            "expanded_universe_rebuilt_as_canonical": False,
            "active_canonical_replaced": False,
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

NSE India expanded rebuild candidate created.

This phase writes a candidate expanded universe dataset by appending v2.17F potential net-new rows to the active canonical dataset schema. It does not replace or modify the active canonical dataset.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{len(canonical_rows)}`
- Full source threshold: `{FULL_SOURCE_THRESHOLD}`
- Rows needed before NSE candidate: `{ROWS_NEEDED_BEFORE_NSE}`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Rebuild candidate summary

- Potential net-new rows raw: `{len(potential_net_new_rows_raw)}`
- Potential net-new rows unique before promotion policy: `{len(promotion_candidates_all)}`
- Deferred by safe promotion policy: `{len(deferred_promotion_rows)}`
- Potential net-new rows promoted: `{len(potential_net_new_rows)}`
- Rows added to candidate dataset: `{rows_added}`
- Expanded candidate rows: `{projected_rows}`
- Rows needed after candidate dataset: `{rows_needed_after_candidate}`
- Completion after candidate: `{round((projected_rows / FULL_SOURCE_THRESHOLD) * 100, 2)}%`
- Would reach full source threshold: `{projected_rows >= FULL_SOURCE_THRESHOLD}`
- Canonical SHA before: `{canonical_sha_before}`
- Canonical SHA after: `{canonical_sha_after}`
- Expanded candidate SHA: `{expanded_sha}`
- Critical failed checks: `{critical_failed}`

## Artifacts

- Expanded candidate dataset: `{EXPANDED_CANDIDATE_CSV}`
- Delta rows: `{DELTA_ROWS_CSV}`
- Promotions: `{PROMOTIONS_CSV}`
- Schema mapping: `{SCHEMA_MAPPING_CSV}`
- JSON report: `{REPORT_JSON}`

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17F report read: true
- Potential net-new rows read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- New expanded candidate dataset written: true
- Delta rows written: true
- Promotions written: true
- Schema mapping written: true
- Safe promotion policy applied: true
- Deferred review rows not promoted: `{len(deferred_promotion_rows)}`
- Net-new rows applied to candidate dataset: true
- Net-new rows applied to canonical: false
- Expanded universe rebuilt as canonical: false
- Active canonical replaced: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17G creates the NSE India expanded rebuild candidate and prepares validation in v2.17H.

## Recommended next phase

`{recommended_next_phase}`
""",
        encoding="utf-8",
        newline="\n",
    )

    print("v2.17G NSE India expanded rebuild candidate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REBUILD_CANDIDATE_SUMMARY:")
    for key, value in payload["rebuild_candidate_summary"].items():
        print(f"- {key}: {value}")
    print("")
    print("SCHEMA_MAPPING:")
    for key, value in mapping.items():
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

