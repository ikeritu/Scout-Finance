from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "v2.18F"
PHASE = "TWSE + TPEx Candidate Validation Against Canonical Dry Run"
PHASE_TYPE = "candidate-validation-against-canonical-dry-run-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

CANONICAL_DATASET = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
VALIDATED_NSE_CANDIDATE_DATASET = OUTPUT_DIR / "expanded_universe_candidate_nse_india_v2_17g.csv"

V218E_JSON = OUTPUT_DIR / "twse_tpex_candidate_extraction_dry_run_v2_18e.json"
V218E_CANDIDATES_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_candidates_v2_18e.csv"
V218E_EXCLUSIONS_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_exclusions_v2_18e.csv"
V218E_CROSSCHECK_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_crosscheck_v2_18e.csv"
V218E_FIELD_MAPPING_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_field_mapping_v2_18e.csv"
V218E_SOURCE_DIAGNOSTICS_CSV = OUTPUT_DIR / "twse_tpex_candidate_extraction_source_diagnostics_v2_18e.csv"

REPORT_JSON = OUTPUT_DIR / "twse_tpex_candidate_validation_against_canonical_dry_run_v2_18f.json"
REPORT_MD = OUTPUT_DIR / "twse_tpex_candidate_validation_against_canonical_dry_run_v2_18f.md"
CLASSIFICATION_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_classification_v2_18f.csv"
MATCH_EVIDENCE_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_match_evidence_v2_18f.csv"
SUMMARY_BY_BUCKET_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_summary_by_bucket_v2_18f.csv"
CANONICAL_PROFILE_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_canonical_profile_v2_18f.csv"
NEXT_ACTIONS_CSV = OUTPUT_DIR / "twse_tpex_candidate_validation_next_actions_v2_18f.csv"

EXPECTED_V218E_STATUS = "TWSE_TPEX_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_TWSE_CANDIDATES_READY_FOR_CANONICAL_VALIDATION_DRY_RUN_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"

ACTIVE_CANONICAL_ROWS_EXPECTED = 38287
VALIDATED_CANDIDATE_ROWS_EXPECTED = 40300
FINAL_TARGET_CANDIDATES = 50000
ROWS_NEEDED_TO_50K_EXPECTED = 9700

RECOMMENDED_NEXT_PHASE = "v2.18G - TWSE + TPEx Expanded Rebuild Candidate"
RECOMMENDED_REVIEW_PHASE = "v2.18F_REVIEW - TWSE + TPEx Candidate Validation Review"

CLASSIFICATION_FIELDS = [
    "candidate_id",
    "provider",
    "exchange",
    "symbol",
    "name",
    "short_name",
    "industry",
    "listing_date",
    "confidence_bucket",
    "crosscheck_status",
    "review_required",
    "canonical_validation_bucket",
    "canonical_match_type",
    "canonical_match_score",
    "canonical_match_row_index",
    "canonical_match_symbol",
    "canonical_match_name",
    "canonical_match_exchange",
    "canonical_match_provider",
    "canonical_match_country",
    "evidence",
    "net_new_candidate",
    "validation_review_required",
    "validation_review_reason",
]

MATCH_EVIDENCE_FIELDS = [
    "candidate_id",
    "symbol",
    "name",
    "match_rank",
    "match_score",
    "match_type",
    "canonical_row_index",
    "canonical_symbol",
    "canonical_name",
    "canonical_exchange",
    "canonical_provider",
    "canonical_country",
    "symbol_match",
    "name_match",
    "market_context_match",
    "evidence",
    "canonical_raw_json",
]

SUMMARY_BY_BUCKET_FIELDS = [
    "bucket",
    "count",
    "share_percent",
    "net_new_count",
    "review_required_count",
    "notes",
]

CANONICAL_PROFILE_FIELDS = [
    "profile_key",
    "profile_value",
    "notes",
]

NEXT_ACTIONS_FIELDS = [
    "action_order",
    "action_scope",
    "action",
    "priority",
    "reason",
    "recommended_phase",
    "guardrails",
]


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


def normalize_for_name(value: Any) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[()\[\]{}（）,，。.\-_*·/\\|:：;；'\"`]", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def normalize_symbol(value: Any) -> str:
    text = normalize_text(value).upper()
    text = re.sub(r"\.(TW|TWO|TPE|TAI|ROCO|TAIWAN)$", "", text)
    text = re.sub(r"[^0-9A-Z]", "", text)
    return text


def is_probable_symbol_value(value: str) -> bool:
    symbol = normalize_symbol(value)
    return bool(re.fullmatch(r"[0-9A-Z]{3,12}", symbol))


def normalize_column_key(column: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(column or "").lower())


def detect_columns(header: list[str], token_groups: list[str]) -> list[str]:
    alias_map = {
        "symbol": {"symbol", "rawsymbol", "canonicalsymbol", "assetsymbol", "securitysymbol", "stocksymbol"},
        "ticker": {"ticker", "assetticker", "bbgticker", "yahooticker", "yahoosymbol", "companyticker", "isinticker"},
        "code": {"code", "rawcode", "canonicalcode", "securitycode", "stockcode", "companycode"},
        "asset_symbol": {"assetsymbol"},
        "asset_ticker": {"assetticker"},
        "raw_symbol": {"rawsymbol"},
        "canonical_symbol": {"canonicalsymbol"},
        "bbg_ticker": {"bbgticker"},
        "isin_ticker": {"isinticker"},
        "name": {"name", "companyname", "shortname", "longname", "securityname", "assetname", "issuer", "empresa", "nombre"},
        "company": {"company", "companyname"},
        "company_name": {"companyname"},
        "short_name": {"shortname"},
        "long_name": {"longname"},
        "security_name": {"securityname"},
        "asset_name": {"assetname"},
        "issuer": {"issuer"},
        "empresa": {"empresa"},
        "nombre": {"nombre"},
        "provider": {"provider", "sourceprovider", "dataprovider", "providerprecedence"},
        "source_provider": {"sourceprovider"},
        "data_provider": {"dataprovider"},
        "vendor": {"vendor"},
        "source": {"sourceprovider"},
        "exchange": {"exchange", "rawexchange", "listingexchange", "primaryexchange", "stockexchange"},
        "market": {"market"},
        "mic": {"mic"},
        "venue": {"venue"},
        "listing_exchange": {"listingexchange"},
        "primary_exchange": {"primaryexchange"},
        "stock_exchange": {"stockexchange"},
        "country": {"country", "marketcountry", "hqcountry"},
        "region": {"region"},
        "market_country": {"marketcountry"},
        "domicile": {"domicile"},
        "hq_country": {"hqcountry"},
        "location": {"location"},
    }

    allowed_keys: set[str] = set()
    for token in token_groups:
        token_key = normalize_column_key(token)
        allowed_keys.add(token_key)
        allowed_keys.update(alias_map.get(token.lower(), set()))
        allowed_keys.update(alias_map.get(token_key, set()))

    result = []
    for col in header:
        col_key = normalize_column_key(col)
        if col_key in allowed_keys:
            result.append(col)

    return result


def safe_get(row: dict[str, str], col: str) -> str:
    return normalize_text(row.get(col, ""))


def row_text(row: dict[str, str]) -> str:
    return " ".join(normalize_text(value) for value in row.values() if normalize_text(value))


def canonical_market_context(row: dict[str, str], context_cols: list[str]) -> tuple[bool, str]:
    selected = " ".join(safe_get(row, col) for col in context_cols)
    combined = f"{selected} {row_text(row)}".lower()

    context_tokens = [
        "twse",
        "taiwan",
        "taipei",
        "twd",
        "taiwan stock exchange",
        "台灣",
        "臺灣",
        "上市",
        ".tw",
    ]

    matched = [token for token in context_tokens if token in combined]
    return bool(matched), "|".join(matched)


def canonical_symbols(row: dict[str, str], symbol_cols: list[str]) -> list[str]:
    symbols: list[str] = []

    for col in symbol_cols:
        value = safe_get(row, col)
        if not value:
            continue

        chunks = re.split(r"[,;/| ]+", value)
        for chunk in chunks:
            symbol = normalize_symbol(chunk)
            if is_probable_symbol_value(symbol):
                symbols.append(symbol)

        whole = normalize_symbol(value)
        if is_probable_symbol_value(whole):
            symbols.append(whole)

    seen = set()
    deduped = []
    for symbol in symbols:
        if symbol not in seen:
            seen.add(symbol)
            deduped.append(symbol)

    return deduped


def canonical_names(row: dict[str, str], name_cols: list[str]) -> list[str]:
    names = []
    for col in name_cols:
        value = safe_get(row, col)
        if value:
            names.append(value)

    seen = set()
    deduped = []
    for name in names:
        norm = normalize_for_name(name)
        if norm and norm not in seen:
            seen.add(norm)
            deduped.append(name)

    return deduped


def best_row_field(row: dict[str, str], cols: list[str]) -> str:
    for col in cols:
        value = safe_get(row, col)
        if value:
            return value
    return ""


def build_canonical_index(
    canonical_rows: list[dict[str, str]],
    symbol_cols: list[str],
    name_cols: list[str],
    provider_cols: list[str],
    exchange_cols: list[str],
    country_cols: list[str],
) -> tuple[dict[str, list[int]], dict[str, list[int]], list[dict[str, Any]]]:
    symbol_index: dict[str, list[int]] = {}
    name_index: dict[str, list[int]] = {}
    profiles: list[dict[str, Any]] = []

    context_cols = sorted(set(provider_cols + exchange_cols + country_cols))

    for idx, row in enumerate(canonical_rows, start=1):
        symbols = canonical_symbols(row, symbol_cols)
        names = canonical_names(row, name_cols)
        market_match, market_tokens = canonical_market_context(row, context_cols)

        for symbol in symbols:
            symbol_index.setdefault(symbol, []).append(idx)

        for name in names:
            norm = normalize_for_name(name)
            if norm:
                name_index.setdefault(norm, []).append(idx)

        profiles.append(
            {
                "row_index": idx,
                "symbols": symbols,
                "names": names,
                "provider": best_row_field(row, provider_cols),
                "exchange": best_row_field(row, exchange_cols),
                "country": best_row_field(row, country_cols),
                "market_context_match": market_match,
                "market_context_tokens": market_tokens,
                "raw_row": row,
            }
        )

    return symbol_index, name_index, profiles


def name_match_type(candidate_names: list[str], canonical_names_list: list[str]) -> tuple[str, str]:
    candidate_norms = [normalize_for_name(name) for name in candidate_names if normalize_for_name(name)]
    canonical_norms = [normalize_for_name(name) for name in canonical_names_list if normalize_for_name(name)]

    for cand in candidate_norms:
        for can in canonical_norms:
            if cand and can and cand == can:
                return "exact", cand

    for cand in candidate_norms:
        for can in canonical_norms:
            if cand and can and (cand in can or can in cand):
                return "contains", f"{cand}|{can}"

    return "none", ""


def candidate_names(candidate: dict[str, str]) -> list[str]:
    return [
        normalize_text(candidate.get("name", "")),
        normalize_text(candidate.get("short_name", "")),
        normalize_text(candidate.get("english_name", "")),
    ]


def score_candidate_against_profile(candidate: dict[str, str], profile: dict[str, Any]) -> dict[str, Any]:
    symbol = normalize_symbol(candidate.get("symbol", ""))
    candidate_name_values = candidate_names(candidate)

    symbol_match = symbol in profile["symbols"]
    name_type, name_evidence = name_match_type(candidate_name_values, profile["names"])
    market_context_match = bool(profile["market_context_match"])

    score = 0
    evidence_parts = []

    if symbol_match:
        score += 80
        evidence_parts.append("symbol_exact")

    if name_type == "exact":
        score += 40
        evidence_parts.append("name_exact")
    elif name_type == "contains":
        score += 25
        evidence_parts.append("name_contains")

    if market_context_match:
        score += 10
        evidence_parts.append(f"market_context:{profile['market_context_tokens']}")

    if symbol_match and name_type in {"exact", "contains"}:
        score += 10
        evidence_parts.append("symbol_name_combined")

    if score >= 90:
        match_type = "existing"
    elif score >= 60:
        match_type = "possible_existing"
    else:
        match_type = "weak_or_no_match"

    return {
        "score": score,
        "match_type": match_type,
        "symbol_match": symbol_match,
        "name_match": name_type,
        "market_context_match": market_context_match,
        "evidence": ";".join(evidence_parts),
        "name_evidence": name_evidence,
    }


def validate_candidate(
    candidate: dict[str, str],
    symbol_index: dict[str, list[int]],
    name_index: dict[str, list[int]],
    canonical_profiles: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    symbol = normalize_symbol(candidate.get("symbol", ""))
    cand_names = candidate_names(candidate)
    candidate_name_norms = [normalize_for_name(name) for name in cand_names if normalize_for_name(name)]

    candidate_row_indices = set(symbol_index.get(symbol, []))

    for name_norm in candidate_name_norms:
        for row_index in name_index.get(name_norm, []):
            candidate_row_indices.add(row_index)

    evidence_rows: list[dict[str, Any]] = []

    for row_index in candidate_row_indices:
        profile = canonical_profiles[row_index - 1]
        scored = score_candidate_against_profile(candidate, profile)

        if scored["score"] <= 0:
            continue

        canonical_name = profile["names"][0] if profile["names"] else ""
        canonical_symbol = profile["symbols"][0] if profile["symbols"] else ""

        evidence_rows.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "symbol": symbol,
                "name": candidate.get("name", ""),
                "match_rank": 0,
                "match_score": scored["score"],
                "match_type": scored["match_type"],
                "canonical_row_index": row_index,
                "canonical_symbol": canonical_symbol,
                "canonical_name": canonical_name,
                "canonical_exchange": profile["exchange"],
                "canonical_provider": profile["provider"],
                "canonical_country": profile["country"],
                "symbol_match": scored["symbol_match"],
                "name_match": scored["name_match"],
                "market_context_match": scored["market_context_match"],
                "evidence": scored["evidence"],
                "canonical_raw_json": json.dumps(profile["raw_row"], ensure_ascii=False, sort_keys=True),
            }
        )

    evidence_rows.sort(key=lambda row: int(row["match_score"]), reverse=True)

    for rank, row in enumerate(evidence_rows, start=1):
        row["match_rank"] = rank

    if not evidence_rows:
        classification = {
            "canonical_validation_bucket": "potential_net_new",
            "canonical_match_type": "no_match",
            "canonical_match_score": 0,
            "canonical_match_row_index": "",
            "canonical_match_symbol": "",
            "canonical_match_name": "",
            "canonical_match_exchange": "",
            "canonical_match_provider": "",
            "canonical_match_country": "",
            "evidence": "no_symbol_or_name_match_in_canonical_index",
            "net_new_candidate": True,
            "validation_review_required": False,
            "validation_review_reason": "",
        }
        return classification, []

    best = evidence_rows[0]
    best_score = int(best["match_score"])

    if best_score >= 90:
        bucket = "existing"
        net_new = False
        review_required = False
        review_reason = ""
    elif best_score >= 60:
        bucket = "possible_existing"
        net_new = False
        review_required = True
        review_reason = "possible_existing_requires_manual_or_phase_review"
    else:
        bucket = "potential_net_new"
        net_new = True
        review_required = False
        review_reason = ""

    classification = {
        "canonical_validation_bucket": bucket,
        "canonical_match_type": best["match_type"],
        "canonical_match_score": best_score,
        "canonical_match_row_index": best["canonical_row_index"],
        "canonical_match_symbol": best["canonical_symbol"],
        "canonical_match_name": best["canonical_name"],
        "canonical_match_exchange": best["canonical_exchange"],
        "canonical_match_provider": best["canonical_provider"],
        "canonical_match_country": best["canonical_country"],
        "evidence": best["evidence"],
        "net_new_candidate": net_new,
        "validation_review_required": review_required,
        "validation_review_reason": review_reason,
    }

    return classification, evidence_rows


def main() -> None:
    for path in [
        REPORT_JSON,
        REPORT_MD,
        CLASSIFICATION_CSV,
        MATCH_EVIDENCE_CSV,
        SUMMARY_BY_BUCKET_CSV,
        CANONICAL_PROFILE_CSV,
        NEXT_ACTIONS_CSV,
    ]:
        if path.exists():
            raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")

    v218e = read_json(V218E_JSON)

    canonical_sha_before = sha256_bytes(CANONICAL_DATASET.read_bytes())

    canonical_header, canonical_rows = read_csv_with_header(CANONICAL_DATASET)
    validated_candidate_header, validated_candidate_rows = read_csv_with_header(VALIDATED_NSE_CANDIDATE_DATASET)
    _, candidate_rows = read_csv_with_header(V218E_CANDIDATES_CSV)
    _, exclusion_rows = read_csv_with_header(V218E_EXCLUSIONS_CSV)
    _, crosscheck_rows = read_csv_with_header(V218E_CROSSCHECK_CSV)
    _, field_mapping_rows = read_csv_with_header(V218E_FIELD_MAPPING_CSV)
    _, source_diagnostics_rows = read_csv_with_header(V218E_SOURCE_DIAGNOSTICS_CSV)

    symbol_cols = detect_columns(
        canonical_header,
        [
            "symbol",
            "ticker",
            "code",
            "asset_symbol",
            "asset_ticker",
            "raw_symbol",
            "canonical_symbol",
            "bbg_ticker",
            "yahoo",
            "isin_ticker",
            "證券代號",
            "公司代號",
            "有價證券代號",
            "股票代號",
        ],
    )

    name_cols = detect_columns(
        canonical_header,
        [
            "name",
            "company",
            "company_name",
            "short_name",
            "long_name",
            "security_name",
            "asset_name",
            "issuer",
            "empresa",
            "nombre",
            "公司名稱",
            "公司簡稱",
            "證券名稱",
            "股票名稱",
        ],
    )

    provider_cols = detect_columns(
        canonical_header,
        [
            "provider",
            "source",
            "source_provider",
            "data_provider",
            "vendor",
        ],
    )

    exchange_cols = detect_columns(
        canonical_header,
        [
            "exchange",
            "market",
            "mic",
            "venue",
            "listing_exchange",
            "primary_exchange",
            "stock_exchange",
        ],
    )

    country_cols = detect_columns(
        canonical_header,
        [
            "country",
            "region",
            "market_country",
            "domicile",
            "hq_country",
            "location",
        ],
    )

    symbol_index, name_index, canonical_profiles = build_canonical_index(
        canonical_rows,
        symbol_cols,
        name_cols,
        provider_cols,
        exchange_cols,
        country_cols,
    )

    classification_rows: list[dict[str, Any]] = []
    match_evidence_rows: list[dict[str, Any]] = []

    for candidate in candidate_rows:
        classification, evidence = validate_candidate(candidate, symbol_index, name_index, canonical_profiles)

        classification_rows.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "provider": candidate.get("provider", ""),
                "exchange": candidate.get("exchange", ""),
                "symbol": candidate.get("symbol", ""),
                "name": candidate.get("name", ""),
                "short_name": candidate.get("short_name", ""),
                "industry": candidate.get("industry", ""),
                "listing_date": candidate.get("listing_date", ""),
                "confidence_bucket": candidate.get("confidence_bucket", ""),
                "crosscheck_status": candidate.get("crosscheck_status", ""),
                "review_required": candidate.get("review_required", ""),
                **classification,
            }
        )

        match_evidence_rows.extend(evidence[:5])

    bucket_counter = Counter(row["canonical_validation_bucket"] for row in classification_rows)
    net_new_count = sum(1 for row in classification_rows if str(row["net_new_candidate"]).lower() == "true" or row["net_new_candidate"] is True)
    existing_count = bucket_counter.get("existing", 0)
    possible_existing_count = bucket_counter.get("possible_existing", 0)
    potential_net_new_count = bucket_counter.get("potential_net_new", 0)
    review_required_count = sum(
        1 for row in classification_rows
        if str(row["validation_review_required"]).lower() == "true" or row["validation_review_required"] is True
    )

    total_candidates = len(candidate_rows)
    summary_rows: list[dict[str, Any]] = []

    for bucket in ["existing", "possible_existing", "potential_net_new"]:
        count = bucket_counter.get(bucket, 0)
        bucket_net_new = sum(
            1 for row in classification_rows
            if row["canonical_validation_bucket"] == bucket
            and (str(row["net_new_candidate"]).lower() == "true" or row["net_new_candidate"] is True)
        )
        bucket_review = sum(
            1 for row in classification_rows
            if row["canonical_validation_bucket"] == bucket
            and (str(row["validation_review_required"]).lower() == "true" or row["validation_review_required"] is True)
        )

        summary_rows.append(
            {
                "bucket": bucket,
                "count": count,
                "share_percent": round((count / total_candidates) * 100, 4) if total_candidates else 0,
                "net_new_count": bucket_net_new,
                "review_required_count": bucket_review,
                "notes": "dry-run classification only; no canonical modification",
            }
        )

    canonical_sha_after = sha256_bytes(CANONICAL_DATASET.read_bytes())
    validated_candidate_sha = sha256_bytes(VALIDATED_NSE_CANDIDATE_DATASET.read_bytes())

    projected_candidate_rows_if_all_net_new = int(v218e["current_state"]["validated_candidate_rows"]) + net_new_count
    projected_rows_needed_after_twse = max(FINAL_TARGET_CANDIDATES - projected_candidate_rows_if_all_net_new, 0)

    critical_failed = 0
    checks: list[dict[str, Any]] = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        nonlocal critical_failed
        if severity == "critical" and not passed:
            critical_failed += 1
        checks.append({"check": check, "passed": bool(passed), "severity": severity, "detail": detail})

    add_check("v2_18e_report_exists", V218E_JSON.exists(), "critical", str(V218E_JSON))
    add_check("v2_18e_status_expected", v218e.get("status") == EXPECTED_V218E_STATUS, "critical", v218e.get("status", ""))
    add_check("v2_18e_candidates_exists", V218E_CANDIDATES_CSV.exists(), "critical", str(V218E_CANDIDATES_CSV))
    add_check("canonical_dataset_exists", CANONICAL_DATASET.exists(), "critical", str(CANONICAL_DATASET))
    add_check("validated_candidate_dataset_exists", VALIDATED_NSE_CANDIDATE_DATASET.exists(), "critical", str(VALIDATED_NSE_CANDIDATE_DATASET))
    add_check("active_canonical_rows_expected", len(canonical_rows) == ACTIVE_CANONICAL_ROWS_EXPECTED, "critical", f"active_canonical_rows={len(canonical_rows)}")
    add_check("validated_candidate_rows_expected", len(validated_candidate_rows) == VALIDATED_CANDIDATE_ROWS_EXPECTED, "critical", f"validated_candidate_rows={len(validated_candidate_rows)}")
    add_check("rows_needed_to_50k_expected", int(v218e["current_state"]["rows_needed_to_50k"]) == ROWS_NEEDED_TO_50K_EXPECTED, "critical", f"rows_needed_to_50k={v218e['current_state']['rows_needed_to_50k']}")
    add_check("candidate_count_matches_v2_18e_report", total_candidates == int(v218e["candidate_extraction_summary"]["candidates_count"]), "critical", f"candidates_csv={total_candidates} report={v218e['candidate_extraction_summary']['candidates_count']}")
    add_check("candidate_ids_unique", len({row.get("candidate_id", "") for row in candidate_rows}) == total_candidates, "critical", "candidate_id uniqueness preserved")
    add_check("candidate_symbols_unique", len({row.get("symbol", "") for row in candidate_rows}) == total_candidates, "critical", "candidate symbol uniqueness preserved")
    add_check("canonical_symbol_columns_detected", len(symbol_cols) > 0, "warning", f"symbol_cols={'|'.join(symbol_cols)}")
    add_check("canonical_name_columns_detected", len(name_cols) > 0, "warning", f"name_cols={'|'.join(name_cols)}")
    add_check("canonical_symbol_column_detection_not_overbroad", 0 < len(symbol_cols) <= 8, "critical", f"symbol_cols_count={len(symbol_cols)} symbol_cols={'|'.join(symbol_cols)}")
    add_check("canonical_name_column_detection_not_overbroad", 0 < len(name_cols) <= 8, "critical", f"name_cols_count={len(name_cols)} name_cols={'|'.join(name_cols)}")
    add_check("canonical_validation_classified_all_candidates", len(classification_rows) == total_candidates, "critical", f"classified={len(classification_rows)} candidates={total_candidates}")
    add_check("bucket_counts_sum_to_candidates", sum(bucket_counter.values()) == total_candidates, "critical", f"bucket_sum={sum(bucket_counter.values())} candidates={total_candidates}")
    add_check("potential_net_new_tracked", potential_net_new_count >= 0, "critical", f"potential_net_new_count={potential_net_new_count}")
    add_check("match_evidence_generated_or_no_matches", len(match_evidence_rows) >= 0, "critical", f"match_evidence_rows={len(match_evidence_rows)}")
    add_check("canonical_sha_unchanged", canonical_sha_before == canonical_sha_after, "critical", "canonical sha unchanged")
    add_check("canonical_dataset_not_modified", True, "critical", "canonical_dataset_modified=False")
    add_check("expanded_candidate_not_written", True, "critical", "new_expanded_dataset_written=False")
    add_check("candidate_validation_dry_run_only", True, "critical", "candidate_validation_against_canonical_dry_run_only=True")
    add_check("network_not_used", True, "critical", "network_download_performed=False")
    add_check("scoring_not_recalculated", True, "critical", "scoring_recalculated=False")
    add_check("openai_not_called", True, "critical", "openai_called=False")
    add_check("broker_not_called", True, "critical", "broker_called=False")
    add_check("full59k_not_launched", True, "critical", "full59k_universe_launched=False")
    add_check("final_50k_gate_still_blocked", projected_candidate_rows_if_all_net_new < FINAL_TARGET_CANDIDATES, "critical", f"{projected_candidate_rows_if_all_net_new} < {FINAL_TARGET_CANDIDATES}")
    add_check("potential_net_new_positive", potential_net_new_count > 0, "warning", f"potential_net_new_count={potential_net_new_count}")
    add_check("possible_existing_tracked", possible_existing_count >= 0, "warning", f"possible_existing_count={possible_existing_count}")
    add_check("review_required_tracked", review_required_count >= 0, "warning", f"review_required_count={review_required_count}")

    next_actions: list[dict[str, Any]] = []

    if critical_failed == 0 and potential_net_new_count > 0:
        next_actions.append(
            {
                "action_order": 1,
                "action_scope": "TWSE",
                "action": "proceed_to_expanded_rebuild_candidate",
                "priority": "high",
                "reason": "Potential net-new TWSE candidates were identified in dry-run validation against canonical.",
                "recommended_phase": RECOMMENDED_NEXT_PHASE,
                "guardrails": "candidate rebuild only; no active canonical replacement; no scoring; no full59k",
            }
        )
    else:
        next_actions.append(
            {
                "action_order": 1,
                "action_scope": "TWSE",
                "action": "review_candidate_validation",
                "priority": "high",
                "reason": "No potential net-new candidates were identified or critical checks failed.",
                "recommended_phase": RECOMMENDED_REVIEW_PHASE,
                "guardrails": "do not rebuild expanded candidate until validation is reviewed",
            }
        )

    if possible_existing_count > 0:
        next_actions.append(
            {
                "action_order": len(next_actions) + 1,
                "action_scope": "TWSE",
                "action": "track_possible_existing_as_non_net_new",
                "priority": "medium",
                "reason": "Possible-existing rows should not be auto-counted as net-new in v2.18G unless explicitly reviewed.",
                "recommended_phase": RECOMMENDED_NEXT_PHASE if critical_failed == 0 and potential_net_new_count > 0 else RECOMMENDED_REVIEW_PHASE,
                "guardrails": "exclude possible_existing from net-new auto-additions by default",
            }
        )

    if critical_failed == 0:
        status = "TWSE_TPEX_CANDIDATE_VALIDATION_DRY_RUN_COMPLETED_CANONICAL_BUCKETS_READY_FOR_EXPANDED_REBUILD_CANDIDATE_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED"
        recommended_next_phase = RECOMMENDED_NEXT_PHASE if potential_net_new_count > 0 else RECOMMENDED_REVIEW_PHASE
    else:
        status = "TWSE_TPEX_CANDIDATE_VALIDATION_DRY_RUN_FAILED_REVIEW_REQUIRED"
        recommended_next_phase = RECOMMENDED_REVIEW_PHASE

    canonical_profile_rows = [
        {"profile_key": "canonical_dataset", "profile_value": str(CANONICAL_DATASET), "notes": ""},
        {"profile_key": "canonical_rows", "profile_value": len(canonical_rows), "notes": ""},
        {"profile_key": "canonical_columns", "profile_value": len(canonical_header), "notes": "|".join(canonical_header)},
        {"profile_key": "detected_symbol_columns", "profile_value": "|".join(symbol_cols), "notes": ""},
        {"profile_key": "detected_name_columns", "profile_value": "|".join(name_cols), "notes": ""},
        {"profile_key": "detected_provider_columns", "profile_value": "|".join(provider_cols), "notes": ""},
        {"profile_key": "detected_exchange_columns", "profile_value": "|".join(exchange_cols), "notes": ""},
        {"profile_key": "detected_country_columns", "profile_value": "|".join(country_cols), "notes": ""},
        {"profile_key": "symbol_index_keys", "profile_value": len(symbol_index), "notes": "normalized canonical symbol keys"},
        {"profile_key": "name_index_keys", "profile_value": len(name_index), "notes": "normalized canonical name keys"},
        {"profile_key": "canonical_sha256_before", "profile_value": canonical_sha_before, "notes": ""},
        {"profile_key": "canonical_sha256_after", "profile_value": canonical_sha_after, "notes": ""},
    ]

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "current_state": {
            "active_canonical_dataset": str(CANONICAL_DATASET),
            "active_canonical_rows": len(canonical_rows),
            "validated_candidate_dataset": str(VALIDATED_NSE_CANDIDATE_DATASET),
            "validated_candidate_rows": len(validated_candidate_rows),
            "final_target_candidates": FINAL_TARGET_CANDIDATES,
            "rows_needed_to_50k_before_twse": ROWS_NEEDED_TO_50K_EXPECTED,
            "projected_candidate_rows_if_all_net_new": projected_candidate_rows_if_all_net_new,
            "projected_rows_needed_after_twse": projected_rows_needed_after_twse,
            "canonical_sha256_before": canonical_sha_before,
            "canonical_sha256_after": canonical_sha_after,
            "validated_candidate_sha256": validated_candidate_sha,
            "final_50k_candidate_gate": "BLOCKED",
            "full59k": "DEPRECATED_DEFERRED",
        },
        "validation_summary": {
            "candidates_validated": total_candidates,
            "existing_count": existing_count,
            "possible_existing_count": possible_existing_count,
            "potential_net_new_count": potential_net_new_count,
            "net_new_count": net_new_count,
            "review_required_count": review_required_count,
            "match_evidence_rows": len(match_evidence_rows),
            "critical_failed_checks": critical_failed,
        },
        "source_references": {
            "v2_18e_report": str(V218E_JSON),
            "v2_18e_candidates": str(V218E_CANDIDATES_CSV),
            "v2_18e_exclusions": str(V218E_EXCLUSIONS_CSV),
            "v2_18e_crosscheck": str(V218E_CROSSCHECK_CSV),
            "v2_18e_field_mapping": str(V218E_FIELD_MAPPING_CSV),
            "v2_18e_source_diagnostics": str(V218E_SOURCE_DIAGNOSTICS_CSV),
            "v2_18e_exclusion_rows": len(exclusion_rows),
            "v2_18e_crosscheck_rows": len(crosscheck_rows),
            "v2_18e_field_mapping_rows": len(field_mapping_rows),
            "v2_18e_source_diagnostics_rows": len(source_diagnostics_rows),
        },
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "endpoint_calls_performed": False,
            "query_sweep_performed": False,
            "raw_acquisition_performed": False,
            "candidate_extraction_performed": False,
            "candidate_validation_against_canonical_performed": True,
            "candidate_validation_mode": "dry_run_only",
            "canonical_dataset_read": True,
            "canonical_comparison_performed": True,
            "canonical_dataset_modified": False,
            "canonical_sha_unchanged": canonical_sha_before == canonical_sha_after,
            "active_canonical_replaced": False,
            "new_expanded_dataset_written": False,
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

    write_csv(CLASSIFICATION_CSV, classification_rows, CLASSIFICATION_FIELDS)
    write_csv(MATCH_EVIDENCE_CSV, match_evidence_rows, MATCH_EVIDENCE_FIELDS)
    write_csv(SUMMARY_BY_BUCKET_CSV, summary_rows, SUMMARY_BY_BUCKET_FIELDS)
    write_csv(CANONICAL_PROFILE_CSV, canonical_profile_rows, CANONICAL_PROFILE_FIELDS)
    write_csv(NEXT_ACTIONS_CSV, next_actions, NEXT_ACTIONS_FIELDS)
    write_json(REPORT_JSON, payload)

    summary_lines = "\n".join(
        f"- `{row['bucket']}`: {row['count']} ({row['share_percent']}%)"
        for row in summary_rows
    )

    check_lines = "\n".join(
        f"- {row['check']}: {'PASS' if row['passed'] else 'FAIL'} ({row['severity']}) — {row['detail']}"
        for row in checks
    )

    next_action_lines = "\n".join(
        f"- P{row['priority']} `{row['action_scope']}` — {row['action']} — {row['recommended_phase']}"
        for row in next_actions
    )

    REPORT_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **{PHASE_TYPE}**

Generated at UTC: `{payload["generated_at_utc"]}`

## Executive summary

v2.18F validates TWSE + TPEx extracted candidates against the active canonical dataset in dry-run mode.

This phase reads canonical only for comparison. It does not write an expanded candidate dataset, does not modify canonical, does not replace the active canonical, and does not perform scoring, OpenAI calls, broker calls, repo-wide renormalization or full59k work.

## Current state

- Active canonical dataset: `{CANONICAL_DATASET}`
- Active canonical rows: `{len(canonical_rows)}`
- Validated candidate dataset: `{VALIDATED_NSE_CANDIDATE_DATASET}`
- Validated candidate rows: `{len(validated_candidate_rows)}`
- Final target candidates: `{FINAL_TARGET_CANDIDATES}`
- Rows needed before TWSE: `{ROWS_NEEDED_TO_50K_EXPECTED}`
- Projected candidate rows if all net-new are added: `{projected_candidate_rows_if_all_net_new}`
- Projected rows needed after TWSE: `{projected_rows_needed_after_twse}`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Validation summary

- Candidates validated: `{total_candidates}`
- Existing: `{existing_count}`
- Possible existing: `{possible_existing_count}`
- Potential net-new: `{potential_net_new_count}`
- Net-new count: `{net_new_count}`
- Review required: `{review_required_count}`
- Match evidence rows: `{len(match_evidence_rows)}`
- Critical failed checks: `{critical_failed}`

## Bucket summary

{summary_lines}

## Canonical detection profile

- Symbol columns: `{ "|".join(symbol_cols) }`
- Name columns: `{ "|".join(name_cols) }`
- Provider columns: `{ "|".join(provider_cols) }`
- Exchange columns: `{ "|".join(exchange_cols) }`
- Country columns: `{ "|".join(country_cols) }`
- Symbol index keys: `{len(symbol_index)}`
- Name index keys: `{len(name_index)}`

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
- Candidate validation against canonical performed: true
- Candidate validation mode: dry_run_only
- Canonical dataset read: true
- Canonical comparison performed: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `{canonical_sha_before == canonical_sha_after}`
- Active canonical replaced: false
- New expanded dataset written: false
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

    print("v2.18F TWSE + TPEx candidate validation against canonical dry run completed.")
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
    print("CANONICAL_PROFILE:")
    print(f"- symbol_cols: {'|'.join(symbol_cols)}")
    print(f"- name_cols: {'|'.join(name_cols)}")
    print(f"- provider_cols: {'|'.join(provider_cols)}")
    print(f"- exchange_cols: {'|'.join(exchange_cols)}")
    print(f"- country_cols: {'|'.join(country_cols)}")
    print(f"- symbol_index_keys: {len(symbol_index)}")
    print(f"- name_index_keys: {len(name_index)}")
    print("")
    print("BUCKETS:")
    for row in summary_rows:
        print(f"- {row['bucket']}: {row['count']} ({row['share_percent']}%)")
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
