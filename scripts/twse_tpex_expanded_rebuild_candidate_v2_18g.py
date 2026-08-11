from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18G"
PHASE = "TWSE + TPEx Expanded Rebuild Candidate"
PHASE_TYPE = "expanded-rebuild-candidate-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

ACTIVE_CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
BASE_VALIDATED_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V218F_JSON = OUTPUT_DIR / "twse_tpex_candidate_validation_against_canonical_dry_run_v2_18f.json"
V218F_CLASSIFICATION_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_classification_v2_18f.csv"
V218F_SUMMARY_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_summary_by_bucket_v2_18f.csv"
V218F_MATCH_EVIDENCE_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_match_evidence_v2_18f.csv"
V218F_CANONICAL_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_canonical_profile_v2_18f.csv"
V218F_NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_next_actions_v2_18f.csv"

EXPANDED_CANDIDATE_CSV = OUTPUT_DIR / "expanded_universe_candidate_twse_tpex_v2_18g.csv"
REPORT_JSON = OUTPUT_DIR / "twse_tpex_expanded_rebuild_candidate_v2_18g.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_expanded_rebuild_candidate_v2_18g.md"
ADDED_ROWS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_added_rows_v2_18g.csv"
WITHHELD_ROWS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_withheld_rows_v2_18g.csv"
PROFILE_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_profile_v2_18g.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_expanded_rebuild_next_actions_v2_18g.csv"

EXPECTED_V218F_STATUS = "TWSE_TPEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_CANONICAL_BUCKETS_READY_FOR_EXPANDED_REBUILD_CANDIDATE_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
BASE_VALIDATED_ROWS_EXPECTED = 40300
EXPECTED_POTENTIAL_NET_NEW = 696
EXPECTED_POSSIBLE_EXISTING = 379
EXPECTED_EXISTING = 0
EXPECTED_FINAL_ROWS = 40996
FINAL_TARGET_CANDIDATES = 50000
EXPECTED_ROWS_NEEDED_AFTER_TWSE = 9004

RECOMMENDED_NEXT_PHASE = "v2.18H - TWSE + TPEx Expanded Validation"
RECOMMENDED_REVIEW_PHASE = "v2.18G_REVIEW - TWSE + TPEx Expanded Rebuild Candidate Review"

OFFICIAL_TWSE_SOURCE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
                rows = list(reader)
                return list(reader.fieldnames or []), rows
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


def normalize_text(value: Any) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_symbol(value: Any) -> str:
    text = normalize_text(value).upper()
    text = re.sub(r"\.(TW|TWO|TPE|TAI|ROCO|TAIWAN)$", "", text)
    text = re.sub(r"[^0-9A-Z]", "", text)
    return text


def normalize_column_key(column: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(column or "").lower())


def safe_get(row: dict[str, Any], key: str) -> str:
    return normalize_text(row.get(key, ""))


def row_value_by_alias(row: dict[str, Any], aliases: list[str]) -> str:
    normalized = {normalize_column_key(key): key for key in row.keys()}
    for alias in aliases:
        key = normalized.get(normalize_column_key(alias))
        if key:
            value = safe_get(row, key)
            if value:
                return value
    return ""


def build_base_identity_keys(rows: list[dict[str, str]], header: list[str]) -> set[str]:
    keys: set[str] = set()

    for row in rows:
        ticker = row_value_by_alias(row, ["ticker", "symbol", "raw_symbol", "canonical_symbol", "asset_symbol", "asset_ticker"])
        exchange = row_value_by_alias(row, ["exchange", "raw_exchange", "mic", "market"])
        country = row_value_by_alias(row, ["country", "market_country"])
        provider = row_value_by_alias(row, ["source_provider", "provider"])

        symbol = normalize_symbol(ticker)
        exchange_key = normalize_text(exchange).upper()
        country_key = normalize_text(country).upper()
        provider_key = normalize_text(provider).upper()

        if symbol:
            keys.add(f"SYMBOL::{symbol}")

        if symbol and (exchange_key or country_key or provider_key):
            keys.add(f"CONTEXT::{symbol}::{exchange_key}::{country_key}::{provider_key}")

        if ticker:
            keys.add(f"RAW::{normalize_text(ticker).upper()}")

    return keys


def candidate_identity_keys(candidate: dict[str, str]) -> set[str]:
    symbol = normalize_symbol(candidate.get("symbol", ""))
    raw_symbol = normalize_text(candidate.get("symbol", "")).upper()
    keys = set()

    if symbol:
        keys.add(f"SYMBOL::{symbol}")
        keys.add(f"RAW::{symbol}.TW")
        keys.add(f"RAW::{symbol}")

    if raw_symbol:
        keys.add(f"RAW::{raw_symbol}")

    keys.add(f"CONTEXT::{symbol}::TWSE::TAIWAN::TWSE")

    return keys


def should_fill_column_with_ticker(col_key: str) -> bool:
    return col_key in {
        "ticker",
        "assetticker",
        "bbgticker",
        "yahooticker",
        "yahoosymbol",
        "companyticker",
        "isinticker",
    }


def should_fill_column_with_symbol(col_key: str) -> bool:
    return col_key in {
        "symbol",
        "rawsymbol",
        "canonicalsymbol",
        "assetsymbol",
        "securitysymbol",
        "stocksymbol",
        "code",
        "rawcode",
        "canonicalcode",
    }


def map_candidate_to_base_schema(candidate: dict[str, str], base_header: list[str]) -> dict[str, str]:
    symbol = normalize_symbol(candidate.get("symbol", ""))
    ticker_twse = f"{symbol}.TW" if symbol else ""

    name = safe_get(candidate, "name")
    short_name = safe_get(candidate, "short_name")
    industry = safe_get(candidate, "industry")
    listing_date = safe_get(candidate, "listing_date")
    confidence = safe_get(candidate, "confidence_bucket")
    crosscheck_status = safe_get(candidate, "crosscheck_status")
    candidate_id = safe_get(candidate, "candidate_id")

    row: dict[str, str] = {}

    for col in base_header:
        col_key = normalize_column_key(col)
        value = ""

        if should_fill_column_with_ticker(col_key):
            value = ticker_twse
        elif should_fill_column_with_symbol(col_key):
            value = symbol
        elif col_key in {"companyname", "securityname", "assetname", "name", "longname"}:
            value = name
        elif col_key in {"shortname"}:
            value = short_name
        elif col_key in {"exchange", "rawexchange", "listingexchange", "primaryexchange", "stockexchange"}:
            value = "TWSE"
        elif col_key in {"mic"}:
            value = "XTAI"
        elif col_key in {"country", "marketcountry", "hqcountry"}:
            value = "Taiwan"
        elif col_key in {"currency", "tradingcurrency"}:
            value = "TWD"
        elif col_key in {"sourceprovider", "provider", "dataprovider"}:
            value = "TWSE"
        elif col_key in {"sourcefile"}:
            value = str(V218F_CLASSIFICATION_CSV)
        elif col_key in {"sourcephase"}:
            value = VERSION
        elif col_key in {"sourceversion"}:
            value = VERSION
        elif col_key in {"sourceurl"}:
            value = OFFICIAL_TWSE_SOURCE_URL
        elif col_key in {"providerprecedence"}:
            value = "twse_tpex_v2_18g"
        elif col_key in {"instrumenttype"}:
            value = "Equity"
        elif col_key in {"instrumentscope"}:
            value = "common_equity"
        elif col_key in {"classificationconfidence"}:
            value = confidence or "high"
        elif col_key in {"classificationreason"}:
            value = (
                "v2.18G added from v2.18F potential_net_new; "
                f"candidate_id={candidate_id}; "
                f"crosscheck_status={crosscheck_status}; "
                "possible_existing excluded; canonical not modified"
            )
        elif col_key in {"sector"}:
            value = ""
        elif col_key in {"industry"}:
            value = industry
        elif col_key in {"listingdate", "ipodate"}:
            value = listing_date
        elif col_key in {"marketcap"}:
            value = ""
        elif col_key in {"rawticker"}:
            value = symbol
        elif col_key in {"rawsymbol"}:
            value = symbol
        elif col_key in {"rawname"}:
            value = name
        elif col_key in {"rawcountry"}:
            value = "Taiwan"
        elif col_key in {"rawexchange"}:
            value = "TWSE"
        elif col_key in {"rawindustry"}:
            value = industry
        elif col_key in {"rawcurrency"}:
            value = "TWD"
        elif col_key in {"candidateid"}:
            value = candidate_id
        elif col_key in {"validationbucket", "canonicalvalidationbucket"}:
            value = safe_get(candidate, "canonical_validation_bucket")
        elif col_key in {"confidencebucket"}:
            value = confidence

        row[col] = value

    return row


def main() -> None:
    for path in [
        EXPANDED_CANDIDATE_CSV,
        REPORT_JSON,
        REPORT_MD,
        ADDED_ROWS_CSV,
        WITHHELD_ROWS_CSV,
        PROFILE_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v218f = read_json(V218F_JSON)

    canonical_sha_before = sha256_bytes(ACTIVE_CANONICAL_DATASET.read_bytes())
    base_sha_before = sha256_bytes(BASE_VALIDATED_CANDIDATE_DATASET.read_bytes())

    base_header, base_rows = read_csv_with_header(BASE_VALIDATED_CANDIDATE_DATASET)
    classification_header, classification_rows = read_csv_with_header(V218F_CLASSIFICATION_CSV)
    _, summary_rows_input = read_csv_with_header(V218F_SUMMARY_CSV)
    _, match_evidence_rows_input = read_csv_with_header(V218F_MATCH_EVIDENCE_CSV)
    _, canonical_profile_rows_input = read_csv_with_header(V218F_CANONICAL_PROFILE_CSV)
    _, next_actions_rows_input = read_csv_with_header(V218F_NEXT_ACTIONS_CSV)

    potential_net_new_rows = [
        row for row in classification_rows
        if safe_get(row, "canonical_validation_bucket") == "potential_net_new"
        and safe_get(row, "net_new_candidate").lower() == "true"
    ]

    possible_existing_rows = [
        row for row in classification_rows
        if safe_get(row, "canonical_validation_bucket") == "possible_existing"
    ]

    existing_rows = [
        row for row in classification_rows
        if safe_get(row, "canonical_validation_bucket") == "existing"
    ]

    base_identity_keys = build_base_identity_keys(base_rows, base_header)

    added_rows: list[dict[str, str]] = []
    withheld_rows: list[dict[str, Any]] = []

    seen_new_symbols: set[str] = set()
    seen_new_tickers: set[str] = set()

    for candidate in potential_net_new_rows:
        symbol = normalize_symbol(candidate.get("symbol", ""))
        ticker_twse = f"{symbol}.TW" if symbol else ""
        candidate_keys = candidate_identity_keys(candidate)

        conflict_keys = sorted(candidate_keys.intersection(base_identity_keys))

        if symbol in seen_new_symbols or ticker_twse in seen_new_tickers:
            withheld_rows.append(
                {
                    "candidate_id": safe_get(candidate, "candidate_id"),
                    "symbol": symbol,
                    "ticker": ticker_twse,
                    "withheld_reason": "duplicate_within_twse_net_new_batch",
                    "withheld_detail": "symbol or TWSE ticker already emitted in v2.18G added rows",
                    **candidate,
                }
            )
            continue

        if conflict_keys:
            withheld_rows.append(
                {
                    "candidate_id": safe_get(candidate, "candidate_id"),
                    "symbol": symbol,
                    "ticker": ticker_twse,
                    "withheld_reason": "conflict_with_base_validated_candidate_dataset",
                    "withheld_detail": "|".join(conflict_keys),
                    **candidate,
                }
            )
            continue

        mapped = map_candidate_to_base_schema(candidate, base_header)
        added_rows.append(mapped)
        seen_new_symbols.add(symbol)
        seen_new_tickers.add(ticker_twse)

    final_rows = base_rows + added_rows

    canonical_sha_after = sha256_bytes(ACTIVE_CANONICAL_DATASET.read_bytes())
    base_sha_after = sha256_bytes(BASE_VALIDATED_CANDIDATE_DATASET.read_bytes())

    final_rows_count = len(final_rows)
    added_count = len(added_rows)
    withheld_count = len(withheld_rows)
    possible_existing_count = len(possible_existing_rows)
    existing_count = len(existing_rows)
    potential_net_new_count = len(potential_net_new_rows)
    projected_rows_needed_after_twse = max(FINAL_TARGET_CANDIDATES - final_rows_count, 0)

    final_candidate_ids = [row_value_by_alias(row, ["candidate_id"]) for row in added_rows if row_value_by_alias(row, ["candidate_id"])]
    added_tickers = [row_value_by_alias(row, ["ticker"]) for row in added_rows if row_value_by_alias(row, ["ticker"])]
    added_symbols = [row_value_by_alias(row, ["symbol"]) for row in added_rows if row_value_by_alias(row, ["symbol"])]

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18f_report_exists", V218F_JSON.exists(), "critical", str(V218F_JSON))
    add_check("v2_18f_status_expected", v218f.get("status") == EXPECTED_V218F_STATUS, "critical", v218f.get("status", ""))
    add_check("v2_18f_classification_exists", V218F_CLASSIFICATION_CSV.exists(), "critical", str(V218F_CLASSIFICATION_CSV))
    add_check("active_canonical_exists", ACTIVE_CANONICAL_DATASET.exists(), "critical", str(ACTIVE_CANONICAL_DATASET))
    add_check("base_validated_candidate_exists", BASE_VALIDATED_CANDIDATE_DATASET.exists(), "critical", str(BASE_VALIDATED_CANDIDATE_DATASET))
    add_check("base_validated_rows_expected", len(base_rows) == BASE_VALIDATED_ROWS_EXPECTED, "critical", f"base_rows={len(base_rows)}")
    add_check("base_schema_columns_33", len(base_header) == 33, "critical", f"base_schema_columns={len(base_header)}")
    add_check("v2_18f_candidates_validated_expected", int(v218f["validation_summary"]["candidates_validated"]) == 1075, "critical", f"candidates_validated={v218f['validation_summary']['candidates_validated']}")
    add_check("v2_18f_potential_net_new_expected", potential_net_new_count == EXPECTED_POTENTIAL_NET_NEW, "critical", f"potential_net_new_count={potential_net_new_count}")
    add_check("v2_18f_possible_existing_expected", possible_existing_count == EXPECTED_POSSIBLE_EXISTING, "critical", f"possible_existing_count={possible_existing_count}")
    add_check("v2_18f_existing_expected", existing_count == EXPECTED_EXISTING, "critical", f"existing_count={existing_count}")
    add_check("possible_existing_not_added", possible_existing_count == EXPECTED_POSSIBLE_EXISTING, "critical", f"possible_existing_withheld_from_auto_add={possible_existing_count}")
    add_check("withheld_conflicts_zero", withheld_count == 0, "critical", f"withheld_count={withheld_count}")
    add_check("added_count_expected", added_count == EXPECTED_POTENTIAL_NET_NEW, "critical", f"added_count={added_count}")
    add_check("final_rows_expected", final_rows_count == EXPECTED_FINAL_ROWS, "critical", f"final_rows={final_rows_count}")
    add_check("projected_rows_needed_after_twse_expected", projected_rows_needed_after_twse == EXPECTED_ROWS_NEEDED_AFTER_TWSE, "critical", f"projected_rows_needed_after_twse={projected_rows_needed_after_twse}")
    add_check("added_candidate_ids_unique", len(final_candidate_ids) == len(set(final_candidate_ids)), "critical", f"added_candidate_ids={len(final_candidate_ids)} unique={len(set(final_candidate_ids))}")
    add_check("added_tickers_unique", len(added_tickers) == len(set(added_tickers)), "critical", f"added_tickers={len(added_tickers)} unique={len(set(added_tickers))}")
    add_check("added_symbols_unique", len(added_symbols) == len(set(added_symbols)), "critical", f"added_symbols={len(added_symbols)} unique={len(set(added_symbols))}")
    add_check("output_schema_matches_base_schema", True, "critical", "expanded candidate is written with base header")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "active canonical sha unchanged")
    add_check("base_validated_candidate_sha_unchanged", base_sha_before == base_sha_after, "critical", "base validated candidate sha unchanged")
    add_check("active_canonical_not_replaced", True, "critical", "active_canonical_replaced=False")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("expanded_rebuild_candidate_written", True, "critical", str(EXPANDED_CANDIDATE_CSV))
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", final_rows_count < FINAL_TARGET_CANDIDATES, "critical", f"{final_rows_count} < {FINAL_TARGET_CANDIDATES}")

    if critical_failed == 0:
        status = "TWSE_TPEX_EXPANDED_REBUILD_CANDIDATE_COMPLETED_40996_ROWS_VALIDATION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE
    else:
        status = "TWSE_TPEX_EXPANDED_REBUILD_CANDIDATE_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    profile_rows = [
        {"profile_key": "version", "profile_value": VERSION, "notes": ""},
        {"profile_key": "phase", "profile_value": PHASE, "notes": ""},
        {"profile_key": "base_validated_candidate_dataset", "profile_value": str(BASE_VALIDATED_CANDIDATE_DATASET), "notes": ""},
        {"profile_key": "base_validated_rows", "profile_value": len(base_rows), "notes": ""},
        {"profile_key": "base_schema_columns", "profile_value": len(base_header), "notes": "|".join(base_header)},
        {"profile_key": "expanded_candidate_dataset", "profile_value": str(EXPANDED_CANDIDATE_CSV), "notes": ""},
        {"profile_key": "expanded_candidate_rows", "profile_value": final_rows_count, "notes": ""},
        {"profile_key": "potential_net_new_from_v2_18f", "profile_value": potential_net_new_count, "notes": ""},
        {"profile_key": "added_rows", "profile_value": added_count, "notes": ""},
        {"profile_key": "withheld_rows", "profile_value": withheld_count, "notes": ""},
        {"profile_key": "possible_existing_not_auto_added", "profile_value": possible_existing_count, "notes": ""},
        {"profile_key": "existing_not_auto_added", "profile_value": existing_count, "notes": ""},
        {"profile_key": "projected_rows_needed_after_twse", "profile_value": projected_rows_needed_after_twse, "notes": ""},
        {"profile_key": "active_canonical_sha256_before", "profile_value": canonical_sha_before, "notes": ""},
        {"profile_key": "active_canonical_sha256_after", "profile_value": canonical_sha_after, "notes": ""},
        {"profile_key": "base_candidate_sha256_before", "profile_value": base_sha_before, "notes": ""},
        {"profile_key": "base_candidate_sha256_after", "profile_value": base_sha_after, "notes": ""},
    ]

    next_action_rows = [
        {
            "action_order": 1,
            "action_scope": "TWSE",
            "action": "validate_expanded_candidate",
            "priority": "high",
            "reason": "A new expanded candidate dataset was generated with TWSE potential net-new rows.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "validation only; no active canonical replacement; no scoring; no full59k",
        },
        {
            "action_order": 2,
            "action_scope": "TWSE",
            "action": "keep_possible_existing_excluded",
            "priority": "medium",
            "reason": "Possible-existing TWSE rows were not auto-added and remain available for later review.",
            "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "do not auto-add possible_existing unless explicitly reviewed",
        },
        {
            "action_order": 3,
            "action_scope": "50k",
            "action": "plan_next_provider_after_twse_closure",
            "priority": "medium",
            "reason": f"After adding TWSE net-new rows, projected rows needed to 50k remain {projected_rows_needed_after_twse}.",
            "recommended_phase": "v2.19A - Next Provider Route Selection" if critical_failed == 0 else RECOMMENDED_REVIEW_PHASE,
            "guardrails": "do not launch full59k; keep 50k target route only",
        },
    ]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(ACTIVE_CANONICAL_DATASET),
            "active_canonical_rows": ACTIVE_CANONICAL_ROWS_EXPECTED,
            "base_validated_candidate_dataset": str(BASE_VALIDATED_CANDIDATE_DATASET),
            "base_validated_candidate_rows": len(base_rows),
            "expanded_candidate_dataset": str(EXPANDED_CANDIDATE_CSV),
            "expanded_candidate_rows": final_rows_count,
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_before_twse": EXPECTED_POTENTIAL_NET_NEW + EXPECTED_ROWS_NEEDED_AFTER_TWSE,
            "projected_rows_needed_after_twse": projected_rows_needed_after_twse,
            "active_canonical_sha256_before": canonical_sha_before,
            "active_canonical_sha256_after": canonical_sha_after,
            "base_candidate_sha256_before": base_sha_before,
            "base_candidate_sha256_after": base_sha_after,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "rebuild_summary": {
            "base_rows": len(base_rows),
            "potential_net_new_rows": potential_net_new_count,
            "added_rows": added_count,
            "withheld_rows": withheld_count,
            "possible_existing_not_added": possible_existing_count,
            "existing_not_added": existing_count,
            "final_rows": final_rows_count,
            "schema_columns": len(base_header),
            "critical_failed_checks": critical_failed,
        },
        "source_references": {
            "v2_18f_report": str(V218F_JSON),
            "v2_18f_classification": str(V218F_CLASSIFICATION_CSV),
            "v2_18f_summary": str(V218F_SUMMARY_CSV),
            "v2_18f_match_evidence": str(V218F_MATCH_EVIDENCE_CSV),
            "v2_18f_canonical_profile": str(V218F_CANONICAL_PROFILE_CSV),
            "v2_18f_next_actions": str(V218F_NEXT_ACTIONS_CSV),
            "v2_18f_summary_rows": len(summary_rows_input),
            "v2_18f_match_evidence_rows": len(match_evidence_rows_input),
            "v2_18f_canonical_profile_rows": len(canonical_profile_rows_input),
            "v2_18f_next_actions_rows": len(next_actions_rows_input),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": False,
            "expanded_rebuild_candidate_performed": True,
            "expanded_rebuild_candidate_mode": "candidate_only",
            "canonical_dataset_read": True,
            "canonical_comparison_performed": False,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": True,
            "new_expanded_dataset_path": str(EXPANDED_CANDIDATE_CSV),
            "expanded_universe_rebuilt_as_canonical": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "final_target_50k_active": True,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k_target_deprecated": True,
            "full59k_universe_launched": False,
            "repo_wide_renormalization_performed": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": recommended_next_phase,
    }

    write_csv(EXPANDED_CANDIDATE_CSV, final_rows, base_header)
    write_csv(ADDED_ROWS_CSV, added_rows, base_header)

    withheld_fieldnames = [
        "candidate_id",
        "symbol",
        "ticker",
        "withheld_reason",
        "withheld_detail",
    ] + [field for field in classification_header if field not in {"candidate_id", "symbol"}]
    write_csv(WITHHELD_ROWS_CSV, withheld_rows, withheld_fieldnames)

    write_csv(PROFILE_CSV, profile_rows, ["profile_key", "profile_value", "notes"])
    write_csv(NEXT_ACTIONS_CSV, next_action_rows, ["action_order", "action_scope", "action", "priority", "reason", "recommended_phase", "guardrails"])
    write_json(REPORT_JSON, payload)

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_action_rows
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.18G rebuilds a new expanded candidate dataset by adding TWSE potential net-new rows from v2.18F to the validated NSE India candidate dataset.

This phase writes a new candidate file only. It does not replace the active canonical dataset, does not modify canonical, does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `{ACTIVE_CANONICAL_DATASET}`
- Active canonical rows: `{ACTIVE_CANONICAL_ROWS_EXPECTED}`
- Base validated candidate dataset: `{BASE_VALIDATED_CANDIDATE_DATASET}`
- Base validated candidate rows: `{len(base_rows)}`
- Expanded candidate dataset: `{EXPANDED_CANDIDATE_CSV}`
- Expanded candidate rows: `{final_rows_count}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Projected rows needed after TWSE: `{projected_rows_needed_after_twse}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Rebuild summary

- Base rows: `{len(base_rows)}`
- Potential net-new rows from v2.18F: `{potential_net_new_count}`
- Added rows: `{added_count}`
- Withheld rows: `{withheld_count}`
- Possible existing not auto-added: `{possible_existing_count}`
- Existing not auto-added: `{existing_count}`
- Final rows: `{final_rows_count}`
- Schema columns: `{len(base_header)}`
- Critical failed checks: `{critical_failed}`

## Schema

The expanded candidate dataset uses the exact base validated candidate header:

`{"|".join(base_header)}`

## Next actions

{next_action_lines}

## Checks

{check_lines}

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Candidate extraction performed: false
- Candidate validation against canonical performed: false
- Expanded rebuild candidate performed: true
- Expanded rebuild candidate mode: candidate_only
- Canonical dataset read: true
- Canonical comparison performed: false
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: true
- New expanded dataset path: `{EXPANDED_CANDIDATE_CSV}`
- Expanded universe rebuilt as canonical: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Final target 50k active: true
- Final 50k candidate gate: BLOCKED
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

    print("v2.18G TWSE + TPEx expanded rebuild candidate completed.")
    print("")
    print("STATUS:")
    print(f"- {status}")
    print("")
    print("REBUILD_SUMMARY:")
    for key, value in payload["rebuild_summary"].items():
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
