from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.11D"
PHASE = "Cboe Europe Validation"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "cboe_europe_v2_11c"

MANIFEST_CSV = OUTPUT_DIR / "cboe_europe_download_manifest_v2_11c.csv"
DISCOVERED_LINKS_CSV = OUTPUT_DIR / "cboe_europe_discovered_links_v2_11c.csv"

VALIDATION_JSON = OUTPUT_DIR / "cboe_europe_validation_v2_11d.json"
VALIDATION_MD = OUTPUT_DIR / "cboe_europe_validation_report_v2_11d.md"
CSV_PROFILE_CSV = OUTPUT_DIR / "cboe_europe_csv_profile_v2_11d.csv"
DECISION_CSV = OUTPUT_DIR / "cboe_europe_validation_decision_v2_11d.csv"
BASELINE_COMPARE_CSV = OUTPUT_DIR / "cboe_europe_baseline_compare_v2_11d.csv"

BASELINE_EXPECTED_ROWS = 9200
FIRST_EXPANSION_THRESHOLD = 15000
ROWS_NEEDED_FIRST_EXPANSION = 5800
FULL_SOURCE_THRESHOLD = 50000
ROWS_NEEDED_FULL_SOURCE = 40800


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def no_overwrite_guard() -> None:
    guarded = [
        VALIDATION_JSON,
        VALIDATION_MD,
        CSV_PROFILE_CSV,
        DECISION_CSV,
        BASELINE_COMPARE_CSV,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.11D outputs:\n"
            + "\n".join(existing)
        )


def read_csv_dicts(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def sniff_dialect(sample: str):
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except Exception:
        return csv.excel


def clean_preview(value: str, limit: int = 220) -> str:
    return " ".join(value.replace("\x00", "").split())[:limit]



def read_csv_records_with_metadata_skip(raw_text: str):
    lines = raw_text.splitlines()
    if not lines:
        return [], [], csv.excel, 0

    sample = "\n".join(lines[:25])
    dialect = sniff_dialect(sample)
    rows = list(csv.reader(lines, dialect))

    header_index = 0
    for index, row in enumerate(rows[:12]):
        lowered = [cell.strip().lower() for cell in row]
        if (
            "company_name" in lowered
            and "bats_name" in lowered
            and "isin" in lowered
        ):
            header_index = index
            break
        if (
            "tick_type" in lowered
            and "min_price" in lowered
            and "tick_size" in lowered
        ):
            header_index = index
            break

    headers = [cell.strip() for cell in rows[header_index]] if rows else []
    data_rows = rows[header_index + 1 :] if rows else []

    return headers, data_rows, dialect, header_index

def classify_headers(headers: list[str]) -> dict:
    lowered = [h.strip().lower() for h in headers]

    symbol_candidates = [
        h for h in lowered
        if h in {"symbol", "ticker", "bats name", "bats_name", "instrument", "security", "isin"}
        or "symbol" in h
        or "ticker" in h
        or h == "isin"
    ]

    name_candidates = [
        h for h in lowered
        if h in {"name", "company", "company name", "issuer", "issuer name", "security name"}
        or "issuer" in h
        or "company" in h
        or "security name" in h
    ]

    mic_candidates = [
        h for h in lowered
        if h in {"mic", "venue", "market", "exchange", "book", "listing market"}
        or "mic" in h
        or "venue" in h
        or "market" in h
        or "exchange" in h
    ]

    currency_candidates = [
        h for h in lowered
        if h in {"currency", "trading currency", "price currency", "ccy"}
        or "currency" in h
    ]

    country_candidates = [
        h for h in lowered
        if h in {"country", "domicile", "country of incorporation"}
        or "country" in h
        or "domicile" in h
    ]

    asset_class_candidates = [
        h for h in lowered
        if h in {"asset_class", "asset class", "asset type", "security type", "instrument type"}
        or "asset" in h
        or "security type" in h
        or "instrument type" in h
    ]

    return {
        "symbol_candidate_headers": "|".join(symbol_candidates),
        "name_candidate_headers": "|".join(name_candidates),
        "mic_or_venue_candidate_headers": "|".join(mic_candidates),
        "currency_candidate_headers": "|".join(currency_candidates),
        "country_candidate_headers": "|".join(country_candidates),
        "asset_class_candidate_headers": "|".join(asset_class_candidates),
        "has_symbol_like_header": bool(symbol_candidates),
        "has_name_like_header": bool(name_candidates),
        "has_mic_or_venue_like_header": bool(mic_candidates),
        "has_currency_like_header": bool(currency_candidates),
        "has_country_like_header": bool(country_candidates),
        "has_asset_class_like_header": bool(asset_class_candidates),
    }


def profile_csv(raw_path: Path, manifest_row: dict) -> dict:
    bytes_size = raw_path.stat().st_size if raw_path.exists() else 0
    sha256 = sha256_file(raw_path) if raw_path.exists() else ""

    profile = {
        "raw_path": str(raw_path),
        "exists": raw_path.exists(),
        "family": manifest_row.get("family", ""),
        "target": manifest_row.get("target", ""),
        "source_link_text": manifest_row.get("source_link_text", ""),
        "url": manifest_row.get("url", ""),
        "status_code": manifest_row.get("status_code", ""),
        "content_type": manifest_row.get("content_type", ""),
        "bytes": bytes_size,
        "sha256": sha256,
        "parse_status": "NOT_PARSED",
        "delimiter": "",
        "encoding_used": "utf-8-sig/errors=replace",
        "row_count_excluding_header": 0,
        "column_count": 0,
        "headers_json": "[]",
        "first_row_preview": "",
        "is_tiny_file_lt_1kb": bytes_size < 1024,
        "is_small_file_lt_10kb": bytes_size < 10_000,
        "validation_notes": "",
        "symbol_candidate_headers": "",
        "name_candidate_headers": "",
        "mic_or_venue_candidate_headers": "",
        "currency_candidate_headers": "",
        "country_candidate_headers": "",
        "asset_class_candidate_headers": "",
        "has_symbol_like_header": False,
        "has_name_like_header": False,
        "has_mic_or_venue_like_header": False,
        "has_currency_like_header": False,
        "has_country_like_header": False,
        "has_asset_class_like_header": False,
    }

    if not raw_path.exists():
        profile["parse_status"] = "MISSING_RAW_FILE"
        profile["validation_notes"] = "Raw file referenced in manifest does not exist."
        return profile

    try:
        raw_text = raw_path.read_text(encoding="utf-8-sig", errors="replace")
        headers, data_rows, dialect, header_index = read_csv_records_with_metadata_skip(raw_text)
        profile["delimiter"] = getattr(dialect, "delimiter", ",")

        row_count = 0
        first_row_preview = ""

        for row in data_rows:
            if not row or all(not cell.strip() for cell in row):
                continue

            row_count += 1
            if not first_row_preview:
                first_row_preview = clean_preview(" | ".join(row))

        header_features = classify_headers(headers)

        profile.update(
            {
                "parse_status": "PARSED_AS_CSV",
                "row_count_excluding_header": row_count,
                "column_count": len(headers),
                "headers_json": json.dumps(headers, ensure_ascii=False),
                "first_row_preview": first_row_preview,
                **header_features,
            }
        )

        notes = []
        if bytes_size < 1024:
            notes.append("TINY_FILE_REVIEW_REQUIRED")
        elif bytes_size < 10_000:
            notes.append("SMALL_FILE_REVIEW_REQUIRED")

        if header_index > 0:
            notes.append(f"SKIPPED_METADATA_ROWS_{header_index}")
        if row_count == 0:
            notes.append("ZERO_DATA_ROWS")
        if len(headers) <= 1:
            notes.append("LOW_COLUMN_COUNT")
        if not header_features["has_symbol_like_header"]:
            notes.append("NO_SYMBOL_LIKE_HEADER")
        if not header_features["has_name_like_header"]:
            notes.append("NO_NAME_LIKE_HEADER")

        profile["validation_notes"] = "|".join(notes) if notes else "OK_FOR_STRUCTURAL_REVIEW"

    except Exception as exc:
        profile["parse_status"] = "CSV_PARSE_FAILED"
        profile["validation_notes"] = repr(exc)

    return profile


def find_baseline_universe() -> Path | None:
    candidates = [
        OUTPUT_DIR / "expanded_universe_v2_8e.csv",
        Path("outputs") / "expanded_universe_v2_8e.csv",
        Path("data") / "expanded_universe_v2_8e.csv",
        Path("expanded_universe_v2_8e.csv"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    matches = [
        p for p in Path(".").rglob("expanded_universe_v2_8e.csv")
        if ".git" not in p.parts and ".venv" not in p.parts
    ]

    return matches[0] if matches else None


def load_baseline_tickers(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()

    try:
        with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            lowered = {h.lower(): h for h in headers}

            ticker_col = None
            for candidate in ["ticker", "symbol"]:
                if candidate in lowered:
                    ticker_col = lowered[candidate]
                    break

            if ticker_col is None:
                return set()

            return {
                str(row.get(ticker_col, "")).strip().upper()
                for row in reader
                if str(row.get(ticker_col, "")).strip()
            }

    except Exception:
        return set()


def collect_candidate_symbols(csv_profiles: list[dict]) -> set[str]:
    symbols: set[str] = set()

    for profile in csv_profiles:
        if profile["parse_status"] != "PARSED_AS_CSV":
            continue

        raw_path = Path(profile["raw_path"])
        headers = json.loads(profile["headers_json"])
        lowered = {h.lower(): h for h in headers}

        symbol_col = None
        for candidate in ["symbol", "ticker", "bats name", "bats_name"]:
            if candidate in lowered:
                symbol_col = lowered[candidate]
                break

        if symbol_col is None:
            continue

        try:
            raw_text = raw_path.read_text(encoding="utf-8-sig", errors="replace")
            actual_headers, data_rows, _, _ = read_csv_records_with_metadata_skip(raw_text)
            actual_header_indexes = {header.lower(): index for index, header in enumerate(actual_headers)}
            symbol_index = actual_header_indexes.get(symbol_col.lower())

            if symbol_index is None:
                continue

            for row in data_rows:
                if symbol_index >= len(row):
                    continue
                value = str(row[symbol_index]).strip().upper()
                if value:
                    symbols.add(value)
        except Exception:
            continue

    return symbols


def decision_from_profiles(csv_profiles: list[dict], baseline_tickers: set[str]) -> dict:
    total_rows = sum(int(p["row_count_excluding_header"]) for p in csv_profiles)
    large_csv_rows = sum(
        int(p["row_count_excluding_header"])
        for p in csv_profiles
        if int(p["bytes"]) >= 100_000
    )

    parsed_files = sum(1 for p in csv_profiles if p["parse_status"] == "PARSED_AS_CSV")
    tiny_files = sum(1 for p in csv_profiles if str(p["is_tiny_file_lt_1kb"]) == "True")
    small_files = sum(1 for p in csv_profiles if str(p["is_small_file_lt_10kb"]) == "True")

    files_with_symbol = sum(1 for p in csv_profiles if str(p["has_symbol_like_header"]) == "True")
    files_with_name = sum(1 for p in csv_profiles if str(p["has_name_like_header"]) == "True")
    files_with_mic = sum(1 for p in csv_profiles if str(p["has_mic_or_venue_like_header"]) == "True")

    candidate_symbols = collect_candidate_symbols(csv_profiles)

    if baseline_tickers:
        candidate_symbol_overlap = len(candidate_symbols & baseline_tickers)
        candidate_symbol_not_in_baseline = len(candidate_symbols - baseline_tickers)
    else:
        candidate_symbol_overlap = 0
        candidate_symbol_not_in_baseline = 0

    first_expansion_unlocked_by_raw_rows = large_csv_rows >= ROWS_NEEDED_FIRST_EXPANSION
    full_source_unlocked_by_raw_rows = large_csv_rows >= ROWS_NEEDED_FULL_SOURCE

    if parsed_files == 0:
        decision = "CBOE_EUROPE_VALIDATION_FAILED_NO_PARSEABLE_CSV"
        rebuild_allowed = False
        recommended_next_phase = "v2.11G_CLOSURE_OR_MANUAL_REVIEW"
    elif large_csv_rows >= ROWS_NEEDED_FIRST_EXPANSION and files_with_symbol > 0:
        decision = "CBOE_EUROPE_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW"
        rebuild_allowed = True
        recommended_next_phase = "v2.11E_REBUILD_EXPANDED_SOURCE_WITH_CBOE_EUROPE_REQUIRES_EXPLICIT_APPROVAL"
    else:
        decision = "CBOE_EUROPE_VALID_BUT_NOT_ENOUGH_FOR_REBUILD"
        rebuild_allowed = False
        recommended_next_phase = "v2.11G_CLOSURE_OR_NEXT_PROVIDER_ROUTE"

    return {
        "decision": decision,
        "recommended_next_phase": recommended_next_phase,
        "rebuild_allowed_by_validation": rebuild_allowed,
        "parsed_csv_files": parsed_files,
        "total_csv_rows_excluding_headers_all_csvs": total_rows,
        "large_csv_rows_excluding_headers_files_ge_100kb": large_csv_rows,
        "tiny_files_lt_1kb": tiny_files,
        "small_files_lt_10kb": small_files,
        "files_with_symbol_like_header": files_with_symbol,
        "files_with_name_like_header": files_with_name,
        "files_with_mic_or_venue_like_header": files_with_mic,
        "candidate_unique_symbols_diagnostic_only": len(candidate_symbols),
        "baseline_tickers_loaded": len(baseline_tickers),
        "candidate_symbol_overlap_diagnostic_only": candidate_symbol_overlap,
        "candidate_symbol_not_in_baseline_diagnostic_only": candidate_symbol_not_in_baseline,
        "current_expanded_rows": BASELINE_EXPECTED_ROWS,
        "rows_needed_first_expansion": ROWS_NEEDED_FIRST_EXPANSION,
        "rows_needed_full_source": ROWS_NEEDED_FULL_SOURCE,
        "first_expansion_unlocked_by_raw_rows": first_expansion_unlocked_by_raw_rows,
        "full_source_unlocked_by_raw_rows": full_source_unlocked_by_raw_rows,
        "normalization_performed": False,
        "net_new_filtering_performed": False,
        "expanded_universe_rebuilt": False,
        "scoring_recalculated": False,
        "openai_called": False,
        "broker_called": False,
        "full_59k_universe_launched": False,
    }


def main() -> None:
    no_overwrite_guard()

    if not RAW_DIR.exists():
        raise SystemExit(f"Missing raw directory: {RAW_DIR}")

    manifest_rows = read_csv_dicts(MANIFEST_CSV)
    discovered_links = read_csv_dicts(DISCOVERED_LINKS_CSV)

    csv_manifest_rows = [
        row for row in manifest_rows
        if str(row.get("raw_output_path", "")).lower().endswith(".csv")
    ]

    csv_profiles = [
        profile_csv(Path(row["raw_output_path"]), row)
        for row in csv_manifest_rows
    ]

    family_counter = Counter(p["family"] for p in csv_profiles)
    status_counter = Counter(p["parse_status"] for p in csv_profiles)
    notes_counter = Counter(
        note
        for p in csv_profiles
        for note in str(p["validation_notes"]).split("|")
        if note
    )

    baseline_path = find_baseline_universe()
    baseline_tickers = load_baseline_tickers(baseline_path)

    decision = decision_from_profiles(csv_profiles, baseline_tickers)

    baseline_compare_rows = [
        {
            "baseline_path": str(baseline_path) if baseline_path else "",
            "baseline_tickers_loaded": decision["baseline_tickers_loaded"],
            "candidate_unique_symbols_diagnostic_only": decision["candidate_unique_symbols_diagnostic_only"],
            "candidate_symbol_overlap_diagnostic_only": decision["candidate_symbol_overlap_diagnostic_only"],
            "candidate_symbol_not_in_baseline_diagnostic_only": decision["candidate_symbol_not_in_baseline_diagnostic_only"],
            "important_note": "Diagnostic only. No accepted net-new filtering or rebuild performed in v2.11D.",
        }
    ]

    validation = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "CBOE_EUROPE_VALIDATION_COMPLETED",
        "generated_at_utc": utc_now(),
        "hard_guards": {
            "network_download_performed": False,
            "raw_files_modified": False,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "input_sources": {
            "raw_dir": str(RAW_DIR),
            "manifest_csv": str(MANIFEST_CSV),
            "discovered_links_csv": str(DISCOVERED_LINKS_CSV),
            "baseline_universe_path": str(baseline_path) if baseline_path else "",
        },
        "counts": {
            "manifest_rows": len(manifest_rows),
            "discovered_links": len(discovered_links),
            "csv_files_profiled": len(csv_profiles),
            "family_counter": dict(family_counter),
            "parse_status_counter": dict(status_counter),
            "validation_notes_counter": dict(notes_counter),
        },
        "decision": decision,
        "csv_profiles": csv_profiles,
    }

    write_json(VALIDATION_JSON, validation)

    write_csv(
        CSV_PROFILE_CSV,
        csv_profiles,
        [
            "raw_path",
            "exists",
            "family",
            "target",
            "source_link_text",
            "url",
            "status_code",
            "content_type",
            "bytes",
            "sha256",
            "parse_status",
            "delimiter",
            "encoding_used",
            "row_count_excluding_header",
            "column_count",
            "headers_json",
            "first_row_preview",
            "is_tiny_file_lt_1kb",
            "is_small_file_lt_10kb",
            "validation_notes",
            "symbol_candidate_headers",
            "name_candidate_headers",
            "mic_or_venue_candidate_headers",
            "currency_candidate_headers",
            "country_candidate_headers",
            "asset_class_candidate_headers",
            "has_symbol_like_header",
            "has_name_like_header",
            "has_mic_or_venue_like_header",
            "has_currency_like_header",
            "has_country_like_header",
            "has_asset_class_like_header",
        ],
    )

    write_csv(
        DECISION_CSV,
        [decision],
        [
            "decision",
            "recommended_next_phase",
            "rebuild_allowed_by_validation",
            "parsed_csv_files",
            "total_csv_rows_excluding_headers_all_csvs",
            "large_csv_rows_excluding_headers_files_ge_100kb",
            "tiny_files_lt_1kb",
            "small_files_lt_10kb",
            "files_with_symbol_like_header",
            "files_with_name_like_header",
            "files_with_mic_or_venue_like_header",
            "candidate_unique_symbols_diagnostic_only",
            "baseline_tickers_loaded",
            "candidate_symbol_overlap_diagnostic_only",
            "candidate_symbol_not_in_baseline_diagnostic_only",
            "current_expanded_rows",
            "rows_needed_first_expansion",
            "rows_needed_full_source",
            "first_expansion_unlocked_by_raw_rows",
            "full_source_unlocked_by_raw_rows",
            "normalization_performed",
            "net_new_filtering_performed",
            "expanded_universe_rebuilt",
            "scoring_recalculated",
            "openai_called",
            "broker_called",
            "full_59k_universe_launched",
        ],
    )

    write_csv(
        BASELINE_COMPARE_CSV,
        baseline_compare_rows,
        [
            "baseline_path",
            "baseline_tickers_loaded",
            "candidate_unique_symbols_diagnostic_only",
            "candidate_symbol_overlap_diagnostic_only",
            "candidate_symbol_not_in_baseline_diagnostic_only",
            "important_note",
        ],
    )

    top_profiles = sorted(
        csv_profiles,
        key=lambda p: int(p["row_count_excluding_header"]),
        reverse=True,
    )[:8]

    report = f"""# {VERSION} — {PHASE}

Status: **CBOE_EUROPE_VALIDATION_COMPLETED**

Phase type: **validation-only**

Generated at UTC: `{validation["generated_at_utc"]}`

## Hard guards

- Network download performed: false
- Raw files modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Inputs

- Raw directory: `{RAW_DIR}`
- Manifest: `{MANIFEST_CSV}`
- Discovered links: `{DISCOVERED_LINKS_CSV}`
- Baseline universe detected: `{baseline_path if baseline_path else "NOT_FOUND"}`

## CSV validation summary

- Manifest rows: {len(manifest_rows)}
- Discovered links: {len(discovered_links)}
- CSV files profiled: {len(csv_profiles)}
- Parsed CSV files: {decision["parsed_csv_files"]}
- Total CSV rows excluding headers, all CSVs: {decision["total_csv_rows_excluding_headers_all_csvs"]}
- Large CSV rows excluding headers, files >=100KB: {decision["large_csv_rows_excluding_headers_files_ge_100kb"]}
- Tiny files <1KB: {decision["tiny_files_lt_1kb"]}
- Small files <10KB: {decision["small_files_lt_10kb"]}

## Header capability summary

- Files with symbol-like header: {decision["files_with_symbol_like_header"]}
- Files with name-like header: {decision["files_with_name_like_header"]}
- Files with MIC/venue-like header: {decision["files_with_mic_or_venue_like_header"]}

## Diagnostic baseline comparison

This is diagnostic only. No accepted net-new filtering or rebuild was performed.

- Baseline tickers loaded: {decision["baseline_tickers_loaded"]}
- Candidate unique symbols: {decision["candidate_unique_symbols_diagnostic_only"]}
- Candidate symbol overlap: {decision["candidate_symbol_overlap_diagnostic_only"]}
- Candidate symbols not in baseline: {decision["candidate_symbol_not_in_baseline_diagnostic_only"]}

## Threshold review

- Current expanded rows: {BASELINE_EXPECTED_ROWS}
- Rows needed first expansion: {ROWS_NEEDED_FIRST_EXPANSION}
- Rows needed full source: {ROWS_NEEDED_FULL_SOURCE}
- First expansion unlocked by raw rows: {decision["first_expansion_unlocked_by_raw_rows"]}
- Full source unlocked by raw rows: {decision["full_source_unlocked_by_raw_rows"]}

## Validation decision

- Decision: **{decision["decision"]}**
- Rebuild allowed by validation: **{decision["rebuild_allowed_by_validation"]}**
- Recommended next phase: **{decision["recommended_next_phase"]}**

## Largest parsed CSV profiles

{chr(10).join(
    f"- `{Path(p['raw_path']).name}` — family={p['family']}; link={p['source_link_text']}; rows={p['row_count_excluding_header']}; columns={p['column_count']}; notes={p['validation_notes']}"
    for p in top_profiles
)}

## Important caution

BXE, CXE, DXE, TRF and SIS remain source/venue semantics until an explicitly approved rebuild phase.

v2.11D does not decide primary exchange mapping and does not create accepted normalized rows.

## Outputs

- `{VALIDATION_JSON}`
- `{VALIDATION_MD}`
- `{CSV_PROFILE_CSV}`
- `{DECISION_CSV}`
- `{BASELINE_COMPARE_CSV}`
"""

    VALIDATION_MD.write_text(report, encoding="utf-8")

    print("v2.11D validation-only completed.")
    print(f"- validation json: {VALIDATION_JSON}")
    print(f"- validation report: {VALIDATION_MD}")
    print(f"- csv profile: {CSV_PROFILE_CSV}")
    print(f"- decision csv: {DECISION_CSV}")
    print(f"- baseline compare: {BASELINE_COMPARE_CSV}")
    print("")
    print("DECISION:")
    for key, value in decision.items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in validation["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
