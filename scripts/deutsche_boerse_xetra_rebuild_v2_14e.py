from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path


VERSION = "v2.14E"
PHASE = "Deutsche Boerse Xetra Expanded Source Rebuild"
PHASE_TYPE = "rebuild-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

D4_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_taxonomy_validation_v2_14d4.json"
D2_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_header_diagnostic_v2_14d2.csv"

EXPANDED_CSV = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
EXCLUSIONS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_exclusions_v2_14e.csv"
ADDITIONS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_additions_v2_14e.csv"
MANIFEST_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_manifest_v2_14e.json"
MANIFEST_MD = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_report_v2_14e.md"

CURRENT_EXPANDED_ROWS = 36863
FULL_SOURCE_THRESHOLD = 50000
EXPECTED_XETRA_NET_NEW = 1425


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        EXPANDED_CSV,
        EXCLUSIONS_CSV,
        ADDITIONS_CSV,
        MANIFEST_JSON,
        MANIFEST_MD,
    ]
    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14E outputs:\n"
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


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def find_col(headers: list[str], names: list[str]) -> str:
    for header in headers:
        h_low = header.lower()
        h_cmp = compact(header)
        for name in names:
            if name.lower() in h_low or compact(name) == h_cmp:
                return header
    return ""


def find_baseline_csv() -> Path:
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
        raise SystemExit("Could not find baseline expanded universe CSV.")

    candidates.sort(reverse=True)
    return candidates[0][2]


def read_baseline(path: Path) -> tuple[list[str], list[dict]]:
    headers, rows = parse_delimited_bytes(path.read_bytes())
    if not headers or not rows:
        raise SystemExit(f"Could not parse baseline expanded universe: {path}")
    return headers, rows


def parse_main_xetra() -> tuple[dict, list[dict]]:
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


def baseline_key_sets(headers: list[str], rows: list[dict]) -> tuple[set[str], set[str]]:
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
        if exchange and ticker:
            exchange_tickers.add(f"{exchange}|{ticker}")

    return isins, exchange_tickers


def normalized_xetra_addition(row: dict, headers: list[str]) -> dict:
    isin_col = find_col(headers, ["ISIN"])
    mnemonic_col = find_col(headers, ["Mnemonic"])
    instrument_id_col = find_col(headers, ["Instrument ID", "InstrumentId"])
    group_col = find_col(headers, ["Product Assignment Group Description", "Product Assignment Group"])
    type_col = find_col(headers, ["Instrument Type", "Security Type"])

    isin = normalize_text(row.get(isin_col, "")).upper().replace(" ", "") if isin_col else ""
    ticker = normalize_text(row.get(mnemonic_col, "")).upper().replace(" ", "") if mnemonic_col else ""
    instrument_id = normalize_text(row.get(instrument_id_col, "")) if instrument_id_col else ""
    group = normalize_text(row.get(group_col, "")) if group_col else ""
    instrument_type = normalize_text(row.get(type_col, "")).upper() if type_col else ""

    company_name = group

    return {
        "provider": "deutsche_boerse_xetra",
        "source_provider": "deutsche_boerse_xetra_all_tradable_instruments",
        "source_phase": "v2.14E",
        "exchange": "XETR",
        "mic": "XETR",
        "ticker": ticker,
        "symbol": ticker,
        "isin": isin,
        "company_name": company_name,
        "security_name": company_name,
        "instrument_id": instrument_id,
        "instrument_type": instrument_type,
        "product_assignment_group_description": group,
        "asset_type": "equity_like",
        "currency": "",
        "country": isin[:2] if len(isin) >= 2 else "",
        "source_url": "deutsche_boerse_xetra_all_tradable_instruments_raw_v2_14c",
        "source_file": "001_downloads_en_t7-xetr-allTradableInstruments.csv",
        "source_version": VERSION,
    }


def merge_fieldnames(baseline_headers: list[str], addition_rows: list[dict]) -> list[str]:
    result = list(baseline_headers)
    seen = {h.lower(): h for h in result}

    preferred = [
        "provider",
        "source_provider",
        "source_phase",
        "exchange",
        "mic",
        "ticker",
        "symbol",
        "isin",
        "company_name",
        "security_name",
        "instrument_id",
        "instrument_type",
        "product_assignment_group_description",
        "asset_type",
        "currency",
        "country",
        "source_url",
        "source_file",
        "source_version",
    ]

    for field in preferred:
        if field.lower() not in seen:
            result.append(field)
            seen[field.lower()] = field

    for row in addition_rows:
        for field in row:
            if field.lower() not in seen:
                result.append(field)
                seen[field.lower()] = field

    return result


def main() -> None:
    no_overwrite_guard()

    d4 = read_json(D4_JSON)

    if not d4.get("rebuild_allowed_by_validation"):
        raise SystemExit("D4 validation did not approve rebuild review. Refusing v2.14E rebuild.")

    baseline_path = find_baseline_csv()
    baseline_headers, baseline_rows = read_baseline(baseline_path)
    baseline_isins, baseline_exchange_tickers = baseline_key_sets(baseline_headers, baseline_rows)

    parser_info, xetra_rows = parse_main_xetra()
    xetra_headers = parser_info["headers"]

    type_col = find_col(xetra_headers, ["Instrument Type", "Security Type"])
    isin_col = find_col(xetra_headers, ["ISIN"])
    mnemonic_col = find_col(xetra_headers, ["Mnemonic"])

    additions: list[dict] = []
    exclusions: list[dict] = []

    seen_new_isins = set()
    seen_new_exchange_tickers = set()

    for row in xetra_rows:
        instrument_type = normalize_text(row.get(type_col, "")).upper() if type_col else ""
        isin = normalize_text(row.get(isin_col, "")).upper().replace(" ", "") if isin_col else ""
        ticker = normalize_text(row.get(mnemonic_col, "")).upper().replace(" ", "") if mnemonic_col else ""

        exchange_key = f"XETR|{ticker}" if ticker else ""

        reason = ""

        if instrument_type != "CS":
            reason = f"excluded_non_common_equity_instrument_type_{instrument_type or 'blank'}"
        elif not isin:
            reason = "missing_isin"
        elif not ticker:
            reason = "missing_ticker"
        elif isin in baseline_isins:
            reason = "already_in_baseline_by_isin"
        elif exchange_key in baseline_exchange_tickers:
            reason = "already_in_baseline_by_exchange_ticker"
        elif isin in seen_new_isins:
            reason = "duplicate_within_xetra_by_isin"
        elif exchange_key in seen_new_exchange_tickers:
            reason = "duplicate_within_xetra_by_exchange_ticker"

        if reason:
            exclusions.append(
                {
                    "isin": isin,
                    "ticker": ticker,
                    "exchange": "XETR",
                    "instrument_type": instrument_type,
                    "exclusion_reason": reason,
                }
            )
            continue

        normalized = normalized_xetra_addition(row, xetra_headers)
        additions.append(normalized)
        seen_new_isins.add(isin)
        seen_new_exchange_tickers.add(exchange_key)

    fieldnames = merge_fieldnames(baseline_headers, additions)

    expanded_rows = []
    for row in baseline_rows:
        expanded_rows.append({field: row.get(field, "") for field in fieldnames})

    for row in additions:
        expanded_rows.append({field: row.get(field, "") for field in fieldnames})

    duplicate_exchange_tickers = 0
    seen_exchange_ticker = set()

    isin_col_expanded = find_col(fieldnames, ["isin"])
    ticker_col_expanded = find_col(fieldnames, ["ticker", "symbol", "mnemonic"])
    exchange_col_expanded = find_col(fieldnames, ["exchange", "mic", "venue", "market"])

    for row in expanded_rows:
        ticker = normalize_text(row.get(ticker_col_expanded, "")).upper().replace(" ", "") if ticker_col_expanded else ""
        exchange = normalize_text(row.get(exchange_col_expanded, "")).upper().replace(" ", "") if exchange_col_expanded else ""
        key = f"{exchange}|{ticker}"
        if exchange and ticker:
            if key in seen_exchange_ticker:
                duplicate_exchange_tickers += 1
            seen_exchange_ticker.add(key)

    expanded_count = len(expanded_rows)
    rows_needed_after = max(0, FULL_SOURCE_THRESHOLD - expanded_count)
    source_to_50k_after = round((expanded_count / FULL_SOURCE_THRESHOLD) * 100, 1)

    full_source_unlocked = expanded_count >= FULL_SOURCE_THRESHOLD

    manifest = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "DEUTSCHE_BOERSE_XETRA_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED",
        "generated_at_utc": utc_now(),
        "selected_provider": "deutsche_boerse_xetra_all_tradable_instruments",
        "source_decision": "DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE",
        "baseline": {
            "baseline_path": str(baseline_path),
            "baseline_rows": len(baseline_rows),
            "baseline_isins": len(baseline_isins),
            "baseline_exchange_ticker_keys": len(baseline_exchange_tickers),
        },
        "xetra_source": {
            "raw_path": parser_info["raw_path"],
            "member": parser_info["member"],
            "gross_rows": len(xetra_rows),
            "header_line_number_one_based": parser_info["header_line_number_one_based"],
            "instrument_type_rule": "Only Instrument Type CS accepted.",
        },
        "counts": {
            "baseline_rows": len(baseline_rows),
            "xetra_gross_rows_reviewed": len(xetra_rows),
            "xetra_rows_added": len(additions),
            "xetra_rows_excluded": len(exclusions),
            "expanded_rows": expanded_count,
            "expanded_delta": expanded_count - len(baseline_rows),
            "duplicate_exchange_ticker_keys": duplicate_exchange_tickers,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "full_source_unlocked": full_source_unlocked,
            "rows_needed_after_xetra": rows_needed_after,
            "source_to_50k_after_xetra_percent": source_to_50k_after,
        },
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed_for_rebuild": True,
            "normalization_performed": True,
            "net_new_filtering_performed": True,
            "expanded_universe_rebuilt": True,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "previous_phase_commit": "8ef6af6",
        "recommended_next_phase": "v2.14F - Deutsche Boerse Xetra Expanded Validation",
    }

    if duplicate_exchange_tickers > 0:
        manifest["status"] = "DEUTSCHE_BOERSE_XETRA_REBUILD_COMPLETED_WITH_DUPLICATE_WARNINGS_FULL_SOURCE_STILL_BLOCKED"

    write_csv(EXPANDED_CSV, expanded_rows, fieldnames)

    write_csv(
        ADDITIONS_CSV,
        additions,
        [
            "provider",
            "source_provider",
            "source_phase",
            "exchange",
            "mic",
            "ticker",
            "symbol",
            "isin",
            "company_name",
            "security_name",
            "instrument_id",
            "instrument_type",
            "product_assignment_group_description",
            "asset_type",
            "currency",
            "country",
            "source_url",
            "source_file",
            "source_version",
        ],
    )

    write_csv(
        EXCLUSIONS_CSV,
        exclusions,
        ["isin", "ticker", "exchange", "instrument_type", "exclusion_reason"],
    )

    write_json(MANIFEST_JSON, manifest)

    MANIFEST_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{manifest["status"]}**

Phase type: **rebuild-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `{manifest["generated_at_utc"]}`

## Decision

- Source decision: **DEUTSCHE_BOERSE_XETRA_ACCEPTED_FOR_CONSERVATIVE_EXPANDED_SOURCE**
- Full source unlocked: **{str(full_source_unlocked).lower()}**
- Full 59k: **blocked**
- Recommended next phase: **v2.14F - Deutsche Boerse Xetra Expanded Validation**

## Counts

- Baseline rows: {len(baseline_rows)}
- Xetra gross rows reviewed: {len(xetra_rows)}
- Xetra rows added: {len(additions)}
- Xetra rows excluded: {len(exclusions)}
- Expanded rows: {expanded_count}
- Expanded delta: {expanded_count - len(baseline_rows)}
- Duplicate exchange+ticker keys: {duplicate_exchange_tickers}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Rows needed after Xetra: {rows_needed_after}
- Source-to-50k after Xetra: {source_to_50k_after}%

## Taxonomy rule

Only `Instrument Type = CS` is accepted as equity-like Xetra source row.

All non-CS instrument types are excluded from the expanded source.

## Guards

- Network download performed in v2.14E: false
- Raw files downloaded in v2.14E: false
- Raw files modified after write: false
- Workbook/CSV parsed for rebuild: true
- Normalization performed: true
- Net-new filtering performed: true
- Expanded universe rebuilt: true
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase creates a new expanded source universe only. It does not launch scoring, OpenAI, broker APIs or full 59k.
""",
        encoding="utf-8",
    )

    print("v2.14E Deutsche Boerse Xetra rebuild-only completed.")
    print(f"- expanded csv: {EXPANDED_CSV}")
    print(f"- additions csv: {ADDITIONS_CSV}")
    print(f"- exclusions csv: {EXCLUSIONS_CSV}")
    print(f"- manifest json: {MANIFEST_JSON}")
    print(f"- report md: {MANIFEST_MD}")
    print("")
    print("COUNTS:")
    for key, value in manifest["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in manifest["hard_guards"].items():
        print(f"- {key}: {value}")
    print("")
    print("NEXT:")
    print("- recommended_next_phase: v2.14F - Deutsche Boerse Xetra Expanded Validation")


if __name__ == "__main__":
    main()
