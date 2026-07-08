from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.13E"
PHASE = "Rebuild Expanded Source With JPX"
PHASE_TYPE = "rebuild-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

BASELINE_EXPANDED = OUTPUT_DIR / "expanded_universe_v2_12e.csv"
VALIDATION_JSON = OUTPUT_DIR / "jpx_validation_v2_13d.json"

EXPANDED_OUT = OUTPUT_DIR / "expanded_universe_v2_13e.csv"
REBUILD_JSON = OUTPUT_DIR / "jpx_rebuild_summary_v2_13e.json"
REBUILD_MD = OUTPUT_DIR / "jpx_rebuild_report_v2_13e.md"
ACCEPTED_ROWS_CSV = OUTPUT_DIR / "jpx_accepted_rows_v2_13e.csv"
EXCLUDED_ROWS_CSV = OUTPUT_DIR / "jpx_excluded_rows_v2_13e.csv"
PROVIDER_BREAKDOWN_CSV = OUTPUT_DIR / "provider_breakdown_v2_13e.csv"
REBUILD_DECISION_CSV = OUTPUT_DIR / "jpx_rebuild_decision_v2_13e.csv"

CURRENT_EXPANDED_ROWS = 33158
FULL_SOURCE_THRESHOLD = 50000

JPX_PROVIDER = "jpx_listed_securities"
JPX_EXCHANGE = "JPX"
JPX_COUNTRY = "JP"
JPX_CURRENCY = "JPY"

JPX_SOURCE_URL = "https://www.jpx.co.jp/english/markets/statistics-equities/misc/01.html"


HEADER_ALIASES = {
    "local_code": [
        "code",
        "localcode",
        "securitiescode",
        "issuecode",
        "stockcode",
        "codeoflistedissues",
    ],
    "company_name": [
        "name",
        "issuesname",
        "issuername",
        "companyname",
        "nameoflistedissues",
        "nameofissues",
        "securityname",
    ],
    "market_segment": [
        "market",
        "marketsegment",
        "section",
        "marketdivision",
        "newmarketsegment",
    ],
    "industry": [
        "industry",
        "33sector",
        "sector",
        "industryclassification",
    ],
    "date": [
        "date",
        "listingdate",
    ],
}


ALLOWED_DOMESTIC_SEGMENTS_COMPACT = {
    "primemarket(domestic)",
    "standardmarket(domestic)",
    "growthmarket(domestic)",
}

NON_COMMON_TOKENS = [
    "etf",
    "etn",
    "reit",
    "venture fund",
    "country fund",
    "infrastructure fund",
    "preferred",
    "preferred stock",
    "equity contribution",
    "investment trust",
    "fund",
    "warrant",
    "bond",
    "debt",
    "subscription warrant",
    "certificate",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        EXPANDED_OUT,
        REBUILD_JSON,
        REBUILD_MD,
        ACCEPTED_ROWS_CSV,
        EXCLUDED_ROWS_CSV,
        PROVIDER_BREAKDOWN_CSV,
        REBUILD_DECISION_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.13E outputs:\n"
            + "\n".join(existing)
        )


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_header_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def normalize_local_code(value: str) -> str:
    value = normalize_text(value)
    if re.fullmatch(r"\d+\.0", value):
        value = value[:-2]
    return value


def compact(value: str) -> str:
    return re.sub(r"\s+", "", normalize_text(value).lower())


def find_field(fieldnames: list[str], candidates: list[str]) -> str | None:
    lower_map = {field.lower(): field for field in fieldnames}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    for field in fieldnames:
        normalized = normalize_header_key(field)
        for candidate in candidates:
            if normalize_header_key(candidate) == normalized:
                return field

    return None


def load_baseline_rows(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise SystemExit(f"Missing baseline expanded universe: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    if not fieldnames:
        raise SystemExit(f"Baseline has no CSV header: {path}")

    return fieldnames, rows


def detect_header(rows: list[list[str]]) -> dict:
    best = {
        "header_row_index_zero_based": -1,
        "score": 0,
        "headers": [],
        "canonical_columns": {},
        "original_columns": {},
    }

    for idx, row in enumerate(rows[:80]):
        normalized = [normalize_header_key(value) for value in row]
        canonical_columns: dict[str, int] = {}
        original_columns: dict[str, str] = {}

        for col_idx, key in enumerate(normalized):
            for canonical, aliases in HEADER_ALIASES.items():
                if canonical in canonical_columns:
                    continue
                if key in aliases or any(alias in key for alias in aliases):
                    canonical_columns[canonical] = col_idx
                    original_columns[canonical] = row[col_idx]

        score = 0
        if "local_code" in canonical_columns:
            score += 5
        if "company_name" in canonical_columns:
            score += 5
        if "market_segment" in canonical_columns:
            score += 3
        if "industry" in canonical_columns:
            score += 1
        if "date" in canonical_columns:
            score += 1

        if score > best["score"]:
            best = {
                "header_row_index_zero_based": idx,
                "score": score,
                "headers": row,
                "canonical_columns": canonical_columns,
                "original_columns": original_columns,
            }

    return best


def read_xls_rows(path: Path) -> list[list[str]]:
    try:
        import xlrd
    except Exception as exc:
        raise SystemExit(
            "MISSING_DEPENDENCY: xlrd is required. "
            "Run: .\\.venv\\Scripts\\python.exe -m pip install xlrd==2.0.1"
        ) from exc

    workbook = xlrd.open_workbook(str(path), formatting_info=False)
    sheet = workbook.sheet_by_index(0)

    rows: list[list[str]] = []
    for row_idx in range(sheet.nrows):
        values: list[str] = []
        for col_idx in range(sheet.ncols):
            cell = sheet.cell(row_idx, col_idx)
            value = cell.value

            if cell.ctype == xlrd.XL_CELL_NUMBER:
                if float(value).is_integer():
                    values.append(str(int(value)))
                else:
                    values.append(str(value))
            else:
                values.append(normalize_text(value))

        rows.append(values)

    return rows


def row_get(row: list[str], col_idx: int | None) -> str:
    if col_idx is None or col_idx < 0 or col_idx >= len(row):
        return ""
    return normalize_text(row[col_idx])


def extract_jpx_rows(dataset_path: Path) -> tuple[dict, list[dict]]:
    rows = read_xls_rows(dataset_path)
    header = detect_header(rows)

    header_idx = int(header["header_row_index_zero_based"])
    cols = header["canonical_columns"]

    if header_idx < 0:
        raise SystemExit("JPX_HEADER_NOT_FOUND: unable to detect header row")

    required = ["local_code", "company_name", "market_segment"]
    missing = [name for name in required if name not in cols]
    if missing:
        raise SystemExit(f"JPX_REQUIRED_COLUMNS_MISSING: {missing}")

    extracted: list[dict] = []

    for row_number, row in enumerate(rows[header_idx + 1 :], start=header_idx + 2):
        local_code = normalize_local_code(row_get(row, cols.get("local_code")))
        company_name = row_get(row, cols.get("company_name"))
        market_segment = row_get(row, cols.get("market_segment"))
        industry = row_get(row, cols.get("industry"))
        source_date = row_get(row, cols.get("date"))

        if not local_code and not company_name:
            continue

        extracted.append(
            {
                "row_number": row_number,
                "local_code_raw_text": local_code,
                "company_name": company_name,
                "market_segment": market_segment,
                "industry": industry,
                "source_date": source_date,
            }
        )

    profile = {
        "dataset_path": str(dataset_path),
        "sheet_index": 0,
        "header_row_index_zero_based": header_idx,
        "header_score": header["score"],
        "detected_columns": "|".join(sorted(cols.keys())),
        "original_columns": header["original_columns"],
        "rows_extracted": len(extracted),
    }

    return profile, extracted


def exclusion_reason(row: dict, seen_local_codes: set[str], baseline_exchange_ticker_keys: set[tuple[str, str]]) -> str:
    local_code = normalize_local_code(row.get("local_code_raw_text", ""))
    company_name = normalize_text(row.get("company_name", ""))
    market_segment = normalize_text(row.get("market_segment", ""))
    industry = normalize_text(row.get("industry", ""))

    if not local_code:
        return "BLANK_LOCAL_CODE"

    if not company_name:
        return "BLANK_COMPANY_NAME"

    if local_code.upper() in seen_local_codes:
        return "DUPLICATE_LOCAL_CODE_IN_JPX_SOURCE"

    if (JPX_EXCHANGE, local_code.upper()) in baseline_exchange_ticker_keys:
        return "OVERLAP_BASELINE_EXCHANGE_TICKER"

    market_compact = compact(market_segment)
    if market_compact not in ALLOWED_DOMESTIC_SEGMENTS_COMPACT:
        if "foreign" in market_compact:
            return "FOREIGN_MARKET_SEGMENT_EXCLUDED"
        if "etfs" in market_compact or "etns" in market_compact:
            return "ETF_ETN_MARKET_SEGMENT_EXCLUDED"
        if "reit" in market_compact or "fund" in market_compact:
            return "REIT_OR_FUND_MARKET_SEGMENT_EXCLUDED"
        if "promarket" in market_compact:
            return "PRO_MARKET_REVIEW_EXCLUDED"
        return "MARKET_SEGMENT_NOT_IN_ALLOWLIST"

    blob = f"{market_segment} {industry} {company_name}".lower()
    if any(token in blob for token in NON_COMMON_TOKENS):
        return "NON_COMMON_EQUITY_REVIEW_EXCLUDED"

    return ""


def build_baseline_key_sets(
    rows: list[dict],
    ticker_field: str,
    exchange_field: str,
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()

    for row in rows:
        ticker = normalize_text(row.get(ticker_field, "")).upper()
        exchange = normalize_text(row.get(exchange_field, "")).upper()
        if ticker and exchange:
            keys.add((exchange, ticker))

    return keys


def build_jpx_output_row(fieldnames: list[str], source_row: dict, field_map: dict[str, str | None]) -> dict:
    output = {field: "" for field in fieldnames}

    local_code = normalize_local_code(source_row.get("local_code_raw_text", ""))
    company_name = normalize_text(source_row.get("company_name", ""))
    market_segment = normalize_text(source_row.get("market_segment", ""))
    industry = normalize_text(source_row.get("industry", ""))
    source_date = normalize_text(source_row.get("source_date", ""))

    assignments = {
        "ticker": local_code,
        "symbol": local_code,
        "company_name": company_name,
        "name": company_name,
        "security_name": company_name,
        "exchange": JPX_EXCHANGE,
        "mic": "XTKS",
        "country": JPX_COUNTRY,
        "country_code": JPX_COUNTRY,
        "currency": JPX_CURRENCY,
        "market_segment": market_segment,
        "market": market_segment,
        "industry": industry,
        "sector": industry,
        "security_type": "equity",
        "asset_type": "equity",
        "instrument_type": "equity",
        "provider": JPX_PROVIDER,
        "source_provider": JPX_PROVIDER,
        "data_provider": JPX_PROVIDER,
        "source": JPX_PROVIDER,
        "source_url": JPX_SOURCE_URL,
        "source_file": "jpx_v2_13c/raw_dataset_candidate_001",
        "source_version": VERSION,
        "acquisition_version": VERSION,
        "listing_date": source_date,
        "date": source_date,
    }

    for canonical, value in assignments.items():
        field = field_map.get(canonical)
        if field:
            output[field] = value

    return output


def provider_value(row: dict, provider_field: str | None, source_field: str | None) -> str:
    if provider_field:
        value = normalize_text(row.get(provider_field, ""))
        if value:
            return value
    if source_field:
        value = normalize_text(row.get(source_field, ""))
        if value:
            return value
    return "UNKNOWN"


def main() -> None:
    no_overwrite_guard()

    validation = read_json(VALIDATION_JSON)

    if not validation.get("rebuild_allowed_by_validation"):
        raise SystemExit("REBUILD_BLOCKED: v2.13D did not approve rebuild_allowed_by_validation=True")

    selected_dataset = validation.get("selected_dataset", {})
    dataset_path = Path(selected_dataset.get("file_path", ""))

    if not dataset_path.exists():
        raise SystemExit(f"SELECTED_JPX_DATASET_NOT_FOUND: {dataset_path}")

    fieldnames, baseline_rows = load_baseline_rows(BASELINE_EXPANDED)

    ticker_field = find_field(fieldnames, ["ticker", "symbol"])
    exchange_field = find_field(fieldnames, ["exchange"])
    company_field = find_field(fieldnames, ["company_name", "name", "security_name"])
    provider_field = find_field(fieldnames, ["source_provider", "provider", "data_provider"])
    source_field = find_field(fieldnames, ["source"])

    if not ticker_field:
        raise SystemExit("BASELINE_SCHEMA_ERROR: could not identify ticker/symbol field")
    if not exchange_field:
        raise SystemExit("BASELINE_SCHEMA_ERROR: could not identify exchange field")
    if not company_field:
        raise SystemExit("BASELINE_SCHEMA_ERROR: could not identify company/name field")

    field_map = {
        "ticker": find_field(fieldnames, ["ticker"]),
        "symbol": find_field(fieldnames, ["symbol"]),
        "company_name": find_field(fieldnames, ["company_name"]),
        "name": find_field(fieldnames, ["name"]),
        "security_name": find_field(fieldnames, ["security_name"]),
        "exchange": exchange_field,
        "mic": find_field(fieldnames, ["mic", "exchange_mic"]),
        "country": find_field(fieldnames, ["country"]),
        "country_code": find_field(fieldnames, ["country_code"]),
        "currency": find_field(fieldnames, ["currency"]),
        "market_segment": find_field(fieldnames, ["market_segment"]),
        "market": find_field(fieldnames, ["market"]),
        "industry": find_field(fieldnames, ["industry"]),
        "sector": find_field(fieldnames, ["sector"]),
        "security_type": find_field(fieldnames, ["security_type"]),
        "asset_type": find_field(fieldnames, ["asset_type"]),
        "instrument_type": find_field(fieldnames, ["instrument_type"]),
        "provider": find_field(fieldnames, ["provider"]),
        "source_provider": find_field(fieldnames, ["source_provider"]),
        "data_provider": find_field(fieldnames, ["data_provider"]),
        "source": source_field,
        "source_url": find_field(fieldnames, ["source_url"]),
        "source_file": find_field(fieldnames, ["source_file"]),
        "source_version": find_field(fieldnames, ["source_version"]),
        "acquisition_version": find_field(fieldnames, ["acquisition_version"]),
        "listing_date": find_field(fieldnames, ["listing_date"]),
        "date": find_field(fieldnames, ["date"]),
    }

    baseline_exchange_ticker_keys = build_baseline_key_sets(baseline_rows, ticker_field, exchange_field)

    jpx_profile, jpx_rows = extract_jpx_rows(dataset_path)

    accepted_source_rows: list[dict] = []
    excluded_rows: list[dict] = []
    seen_local_codes: set[str] = set()

    for row in jpx_rows:
        reason = exclusion_reason(row, seen_local_codes, baseline_exchange_ticker_keys)

        local_code = normalize_local_code(row.get("local_code_raw_text", ""))
        if not reason:
            accepted_source_rows.append(row)
            seen_local_codes.add(local_code.upper())
        else:
            excluded = dict(row)
            excluded["exclusion_reason"] = reason
            excluded_rows.append(excluded)
            if local_code:
                seen_local_codes.add(local_code.upper())

    appended_rows = [
        build_jpx_output_row(fieldnames, row, field_map)
        for row in accepted_source_rows
    ]

    output_rows = baseline_rows + appended_rows

    # Final duplicate check on exchange+ticker.
    final_keys = []
    duplicate_keys = []
    seen_final = set()

    for row in output_rows:
        ticker = normalize_text(row.get(ticker_field, "")).upper()
        exchange = normalize_text(row.get(exchange_field, "")).upper()
        if not ticker or not exchange:
            continue

        key = (exchange, ticker)
        final_keys.append(key)
        if key in seen_final:
            duplicate_keys.append(key)
        seen_final.add(key)

    duplicate_exchange_ticker_keys = len(set(duplicate_keys))

    provider_counter = Counter(
        provider_value(row, provider_field, source_field)
        for row in output_rows
    )

    accepted_by_market_segment = Counter(
        normalize_text(row.get("market_segment", ""))
        for row in accepted_source_rows
    )

    excluded_by_reason = Counter(
        row.get("exclusion_reason", "UNKNOWN")
        for row in excluded_rows
    )

    expanded_rows = len(output_rows)
    rows_added = len(appended_rows)
    rows_needed_after_jpx = max(FULL_SOURCE_THRESHOLD - expanded_rows, 0)
    full_source_unlocked = expanded_rows >= FULL_SOURCE_THRESHOLD

    hard_guards = {
        "phase_type": PHASE_TYPE,
        "network_download_performed": False,
        "raw_files_modified": False,
        "normalization_performed": True,
        "net_new_filtering_performed": True,
        "expanded_universe_rebuilt": True,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
        "overwrite_allowed": False,
    }

    critical_checks = {
        "v2_13d_rebuild_allowed": bool(validation.get("rebuild_allowed_by_validation")),
        "baseline_rows_match_expected": len(baseline_rows) == CURRENT_EXPANDED_ROWS,
        "accepted_rows_gt_zero": rows_added > 0,
        "expanded_rows_equals_baseline_plus_added": expanded_rows == len(baseline_rows) + rows_added,
        "duplicate_exchange_ticker_keys_zero": duplicate_exchange_ticker_keys == 0,
        "full_59k_universe_not_launched": hard_guards["full_59k_universe_launched"] is False,
    }

    rebuild_status = (
        "JPX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED"
        if all(critical_checks.values()) and not full_source_unlocked
        else "JPX_REBUILD_COMPLETED_REVIEW_REQUIRED"
    )

    write_csv(EXPANDED_OUT, output_rows, fieldnames)

    accepted_fieldnames = [
        "row_number",
        "local_code_raw_text",
        "company_name",
        "market_segment",
        "industry",
        "source_date",
    ]

    excluded_fieldnames = accepted_fieldnames + ["exclusion_reason"]

    write_csv(ACCEPTED_ROWS_CSV, accepted_source_rows, accepted_fieldnames)
    write_csv(EXCLUDED_ROWS_CSV, excluded_rows, excluded_fieldnames)

    provider_breakdown = [
        {"provider": provider, "rows": count}
        for provider, count in provider_counter.most_common()
    ]

    write_csv(PROVIDER_BREAKDOWN_CSV, provider_breakdown, ["provider", "rows"])

    decision_row = {
        "version": VERSION,
        "phase_type": PHASE_TYPE,
        "status": rebuild_status,
        "baseline_rows": len(baseline_rows),
        "jpx_source_rows_reviewed": len(jpx_rows),
        "jpx_rows_added": rows_added,
        "jpx_rows_excluded": len(excluded_rows),
        "expanded_rows": expanded_rows,
        "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
        "full_source_threshold": FULL_SOURCE_THRESHOLD,
        "full_source_unlocked": full_source_unlocked,
        "rows_needed_after_jpx": rows_needed_after_jpx,
        "full_59k_universe_launched": False,
        "recommended_next_phase": "v2.13F - Validate Expanded Source With JPX",
    }

    write_csv(
        REBUILD_DECISION_CSV,
        [decision_row],
        [
            "version",
            "phase_type",
            "status",
            "baseline_rows",
            "jpx_source_rows_reviewed",
            "jpx_rows_added",
            "jpx_rows_excluded",
            "expanded_rows",
            "duplicate_exchange_ticker_keys",
            "full_source_threshold",
            "full_source_unlocked",
            "rows_needed_after_jpx",
            "full_59k_universe_launched",
            "recommended_next_phase",
        ],
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": rebuild_status,
        "generated_at_utc": utc_now(),
        "source_validation_commit": "51e66dd",
        "baseline_input": str(BASELINE_EXPANDED),
        "expanded_output": str(EXPANDED_OUT),
        "selected_jpx_dataset": str(dataset_path),
        "jpx_profile": jpx_profile,
        "hard_guards": hard_guards,
        "critical_checks": critical_checks,
        "field_mapping": field_map,
        "counts": {
            "baseline_rows": len(baseline_rows),
            "jpx_source_rows_reviewed": len(jpx_rows),
            "jpx_rows_added": rows_added,
            "jpx_rows_excluded": len(excluded_rows),
            "expanded_rows": expanded_rows,
            "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_after_jpx": rows_needed_after_jpx,
            "full_59k_universe_launched": False,
        },
        "accepted_by_market_segment": dict(accepted_by_market_segment),
        "excluded_by_reason": dict(excluded_by_reason),
        "provider_breakdown": provider_breakdown,
        "decision": decision_row,
        "scope_note": (
            "v2.13E rebuilds the expanded source by appending conservative JPX domestic "
            "Prime/Standard/Growth equity candidates only. It does not perform scoring, OpenAI calls, "
            "broker calls, network downloads or full 59k launch."
        ),
    }

    write_json(REBUILD_JSON, payload)

    accepted_lines = "\n".join(
        f"- {segment}: {count}"
        for segment, count in accepted_by_market_segment.most_common()
    )

    excluded_lines = "\n".join(
        f"- {reason}: {count}"
        for reason, count in excluded_by_reason.most_common()
    )

    provider_lines = "\n".join(
        f"- {row['provider']}: {row['rows']}"
        for row in provider_breakdown
    )

    guard_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in hard_guards.items()
    )

    check_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in critical_checks.items()
    )

    md = f"""# {VERSION} - {PHASE}

Status: **{rebuild_status}**

Phase type: **rebuild-only**

Generated at UTC: `{payload["generated_at_utc"]}`

## Decision

- Baseline rows: {len(baseline_rows)}
- JPX source rows reviewed: {len(jpx_rows)}
- JPX rows added: {rows_added}
- JPX rows excluded: {len(excluded_rows)}
- Expanded rows: {expanded_rows}
- Duplicate exchange+ticker keys: {duplicate_exchange_ticker_keys}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Full source unlocked: {full_source_unlocked}
- Rows needed after JPX: {rows_needed_after_jpx}
- Full 59k universe launched: false
- Recommended next phase: **v2.13F - Validate Expanded Source With JPX**

## Accepted JPX rows by market segment

{accepted_lines}

## Excluded JPX rows by reason

{excluded_lines}

## Provider breakdown

{provider_lines}

## Critical checks

{check_lines}

## Hard guards

{guard_lines}

## Scope note

v2.13E is rebuild-only.

It appends only conservative JPX domestic Prime/Standard/Growth equity candidates.

It does not download anything, does not score, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Outputs

- `{EXPANDED_OUT}`
- `{REBUILD_JSON}`
- `{REBUILD_MD}`
- `{ACCEPTED_ROWS_CSV}`
- `{EXCLUDED_ROWS_CSV}`
- `{PROVIDER_BREAKDOWN_CSV}`
- `{REBUILD_DECISION_CSV}`
"""

    REBUILD_MD.write_text(md, encoding="utf-8")

    print("v2.13E JPX rebuild-only completed.")
    print(f"- expanded output: {EXPANDED_OUT}")
    print(f"- rebuild json: {REBUILD_JSON}")
    print(f"- rebuild report: {REBUILD_MD}")
    print(f"- accepted rows csv: {ACCEPTED_ROWS_CSV}")
    print(f"- excluded rows csv: {EXCLUDED_ROWS_CSV}")
    print(f"- provider breakdown csv: {PROVIDER_BREAKDOWN_CSV}")
    print(f"- decision csv: {REBUILD_DECISION_CSV}")
    print("")
    print("DECISION:")
    print(f"- status: {rebuild_status}")
    print(f"- recommended_next_phase: v2.13F - Validate Expanded Source With JPX")
    print("")
    print("COUNTS:")
    for key, value in payload["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("ACCEPTED_BY_MARKET_SEGMENT:")
    for key, value in accepted_by_market_segment.most_common():
        print(f"- {key}: {value}")
    print("")
    print("EXCLUDED_BY_REASON:")
    for key, value in excluded_by_reason.most_common():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in hard_guards.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
