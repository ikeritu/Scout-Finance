from __future__ import annotations

import csv
import json
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.11E"
PHASE = "Rebuild Expanded Source With Cboe Europe"
PHASE_TYPE = "rebuild-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")
RAW_DIR = OUTPUT_DIR / "raw" / "cboe_europe_v2_11c"

DECISION_CSV = OUTPUT_DIR / "cboe_europe_validation_decision_v2_11d.csv"
PROFILE_CSV = OUTPUT_DIR / "cboe_europe_csv_profile_v2_11d.csv"

EXPANDED_OUT = OUTPUT_DIR / "expanded_universe_v2_11e.csv"
EXCLUSIONS_OUT = OUTPUT_DIR / "expanded_universe_exclusions_v2_11e.csv"
CANDIDATES_OUT = OUTPUT_DIR / "cboe_europe_normalized_candidates_v2_11e.csv"
REBUILD_JSON = OUTPUT_DIR / "cboe_europe_rebuild_report_v2_11e.json"
REBUILD_MD = OUTPUT_DIR / "cboe_europe_rebuild_report_v2_11e.md"

BASELINE_EXPECTED_ROWS = 9200
FIRST_EXPANSION_THRESHOLD = 15000
FULL_SOURCE_THRESHOLD = 50000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        EXPANDED_OUT,
        EXCLUSIONS_OUT,
        CANDIDATES_OUT,
        REBUILD_JSON,
        REBUILD_MD,
    ]

    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.11E outputs:\n"
            + "\n".join(existing)
        )


def read_csv_dicts(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def find_baseline_universe() -> Path:
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

    if not matches:
        raise SystemExit("BASELINE_NOT_FOUND: expanded_universe_v2_8e.csv not found")

    return matches[0]


def validate_rebuild_gate() -> dict:
    rows = read_csv_dicts(DECISION_CSV)
    if not rows:
        raise SystemExit(f"MISSING_DECISION: {DECISION_CSV}")

    decision = rows[0]

    if decision.get("rebuild_allowed_by_validation") != "True":
        raise SystemExit(
            "REBUILD_GATE_BLOCKED: v2.11D did not approve rebuild review. "
            f"decision={decision.get('decision')}"
        )

    expected_decision = "CBOE_EUROPE_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW"
    if decision.get("decision") != expected_decision:
        raise SystemExit(
            "REBUILD_GATE_BLOCKED: unexpected v2.11D decision. "
            f"decision={decision.get('decision')}"
        )

    return decision


def sniff_dialect(sample: str):
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except Exception:
        return csv.excel


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

    headers = [cell.strip() for cell in rows[header_index]] if rows else []
    data_rows = rows[header_index + 1 :] if rows else []

    return headers, data_rows, dialect, header_index


def read_baseline(path: Path) -> tuple[list[dict], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        headers = reader.fieldnames or []

    if not rows:
        raise SystemExit(f"BASELINE_EMPTY: {path}")

    return rows, headers


def find_col(headers: list[str], candidates: list[str]) -> str | None:
    lowered = {h.lower(): h for h in headers}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def get_value(row: dict, *names: str) -> str:
    lowered = {str(k).lower(): v for k, v in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value is not None:
            return str(value).strip()
    return ""


def set_if_col(row: dict, headers: list[str], candidates: list[str], value: str) -> None:
    col = find_col(headers, candidates)
    if col:
        row[col] = value


def baseline_key_sets(rows: list[dict], headers: list[str]) -> dict:
    ticker_col = find_col(headers, ["ticker", "symbol"])
    exchange_col = find_col(headers, ["exchange", "market", "mic"])
    isin_col = find_col(headers, ["isin", "isin_code"])

    ticker_set = set()
    exchange_ticker_set = set()
    isin_set = set()

    for row in rows:
        ticker = str(row.get(ticker_col, "")).strip() if ticker_col else ""
        exchange = str(row.get(exchange_col, "")).strip() if exchange_col else ""
        isin = str(row.get(isin_col, "")).strip() if isin_col else ""

        if ticker:
            ticker_set.add(ticker.upper())
        if exchange and ticker:
            exchange_ticker_set.add((exchange.upper(), ticker.upper()))
        if isin:
            isin_set.add(isin.upper())

    return {
        "ticker_col": ticker_col or "",
        "exchange_col": exchange_col or "",
        "isin_col": isin_col or "",
        "ticker_set": ticker_set,
        "exchange_ticker_set": exchange_ticker_set,
        "isin_set": isin_set,
    }


def selected_cboe_csv_profiles() -> list[dict]:
    profiles = read_csv_dicts(PROFILE_CSV)
    selected = []

    for profile in profiles:
        raw_path = Path(profile.get("raw_path", ""))
        family = profile.get("family", "")
        bytes_size = int(profile.get("bytes") or 0)
        headers = profile.get("headers_json", "")

        if family != "symbols_csv_candidate":
            continue
        if bytes_size < 100_000:
            continue
        if "company_name" not in headers or "bats_name" not in headers or "isin" not in headers:
            continue
        if not raw_path.exists():
            continue

        selected.append(profile)

    if not selected:
        raise SystemExit("NO_CBOE_LARGE_SYMBOL_CSV_PROFILES_SELECTED")

    return selected


def normalize_cboe_candidates(
    profiles: list[dict],
    baseline_rows: list[dict],
    baseline_headers: list[str],
) -> tuple[list[dict], list[dict], list[dict]]:
    key_sets = baseline_key_sets(baseline_rows, baseline_headers)

    baseline_ticker_set = key_sets["ticker_set"]
    baseline_isin_set = key_sets["isin_set"]

    candidate_fieldnames = [
        "provider",
        "source_link_text",
        "source_raw_path",
        "cboe_company_name",
        "cboe_bats_name",
        "cboe_isin",
        "cboe_currency",
        "cboe_mic",
        "cboe_reuters_exchange_code",
        "cboe_live",
        "cboe_asset_class",
        "cboe_supported_services",
        "cboe_trading_segment",
        "cboe_printed_name",
        "candidate_key",
        "decision",
        "exclusion_reason",
    ]

    accepted_by_key: OrderedDict[str, dict] = OrderedDict()
    candidate_rows: list[dict] = []
    exclusions: list[dict] = []

    seen_candidate_keys = set()

    for profile in profiles:
        raw_path = Path(profile["raw_path"])
        raw_text = raw_path.read_text(encoding="utf-8-sig", errors="replace")
        headers, data_rows, _, _ = read_csv_records_with_metadata_skip(raw_text)
        header_indexes = {header.lower(): index for index, header in enumerate(headers)}

        def cell(row: list[str], name: str) -> str:
            index = header_indexes.get(name.lower())
            if index is None or index >= len(row):
                return ""
            return str(row[index]).strip()

        for row in data_rows:
            if not row or all(not str(cell).strip() for cell in row):
                continue

            company_name = cell(row, "company_name")
            bats_name = cell(row, "bats_name")
            isin = cell(row, "isin")
            currency = cell(row, "currency")
            mic = cell(row, "mic")
            reuters_exchange_code = cell(row, "reuters_exchange_code")
            live = cell(row, "live")
            asset_class = cell(row, "asset_class")
            supported_services = cell(row, "supported_services")
            trading_segment = cell(row, "trading_segment")
            printed_name = cell(row, "printed_name")

            candidate_key = bats_name.strip()
            candidate_key_upper = candidate_key.upper()

            candidate = {
                "provider": "cboe_europe_reference_data",
                "source_link_text": profile.get("source_link_text", ""),
                "source_raw_path": str(raw_path),
                "cboe_company_name": company_name,
                "cboe_bats_name": bats_name,
                "cboe_isin": isin,
                "cboe_currency": currency,
                "cboe_mic": mic,
                "cboe_reuters_exchange_code": reuters_exchange_code,
                "cboe_live": live,
                "cboe_asset_class": asset_class,
                "cboe_supported_services": supported_services,
                "cboe_trading_segment": trading_segment,
                "cboe_printed_name": printed_name,
                "candidate_key": candidate_key,
                "decision": "",
                "exclusion_reason": "",
            }

            exclusion_reason = ""

            if not bats_name:
                exclusion_reason = "MISSING_BATS_NAME"
            elif not company_name:
                exclusion_reason = "MISSING_COMPANY_NAME"
            elif not isin:
                exclusion_reason = "MISSING_ISIN"
            elif live.lower() not in {"t", "true", "1", "yes", "y"}:
                exclusion_reason = "NOT_LIVE"
            elif candidate_key in seen_candidate_keys:
                exclusion_reason = "DUPLICATE_CBOE_BATS_NAME"
            elif candidate_key_upper in baseline_ticker_set:
                exclusion_reason = "BASELINE_TICKER_ALREADY_PRESENT"
            elif isin.upper() in baseline_isin_set:
                exclusion_reason = "BASELINE_ISIN_ALREADY_PRESENT"

            if exclusion_reason:
                candidate["decision"] = "EXCLUDED"
                candidate["exclusion_reason"] = exclusion_reason
                exclusions.append(candidate)
                candidate_rows.append(candidate)
                continue

            seen_candidate_keys.add(candidate_key)

            candidate["decision"] = "ACCEPTED_FOR_REBUILD_CANDIDATE"
            candidate_rows.append(candidate)

            rebuilt_row = {header: "" for header in baseline_headers}

            set_if_col(rebuilt_row, baseline_headers, ["exchange", "market"], "CBOE_EUROPE")
            set_if_col(rebuilt_row, baseline_headers, ["ticker", "symbol"], bats_name)
            set_if_col(rebuilt_row, baseline_headers, ["company_name", "name", "issuer_name", "security_name"], company_name)
            set_if_col(rebuilt_row, baseline_headers, ["provider", "source", "source_provider"], "cboe_europe_reference_data")
            set_if_col(rebuilt_row, baseline_headers, ["isin", "isin_code"], isin)
            set_if_col(rebuilt_row, baseline_headers, ["currency", "trading_currency", "price_currency"], currency)
            set_if_col(rebuilt_row, baseline_headers, ["mic", "venue"], mic)
            set_if_col(rebuilt_row, baseline_headers, ["asset_class", "asset type", "security_type", "instrument_type"], asset_class)

            accepted_by_key[candidate_key] = rebuilt_row

    accepted_rows = list(accepted_by_key.values())
    return accepted_rows, candidate_rows, exclusions


def duplicate_exchange_ticker_count(rows: list[dict], headers: list[str]) -> int:
    ticker_col = find_col(headers, ["ticker", "symbol"])
    exchange_col = find_col(headers, ["exchange", "market", "mic"])

    if not ticker_col or not exchange_col:
        return 0

    keys = []
    for row in rows:
        exchange = str(row.get(exchange_col, "")).strip().upper()
        ticker = str(row.get(ticker_col, "")).strip().upper()
        if exchange and ticker:
            keys.append((exchange, ticker))

    counts = Counter(keys)
    return sum(1 for count in counts.values() if count > 1)


def main() -> None:
    no_overwrite_guard()

    decision = validate_rebuild_gate()

    baseline_path = find_baseline_universe()
    baseline_rows, baseline_headers = read_baseline(baseline_path)

    if len(baseline_rows) != BASELINE_EXPECTED_ROWS:
        print(
            f"WARNING: baseline row count is {len(baseline_rows)}, "
            f"expected {BASELINE_EXPECTED_ROWS}"
        )

    profiles = selected_cboe_csv_profiles()

    accepted_rows, candidate_rows, exclusions = normalize_cboe_candidates(
        profiles=profiles,
        baseline_rows=baseline_rows,
        baseline_headers=baseline_headers,
    )

    expanded_rows = baseline_rows + accepted_rows

    duplicate_keys = duplicate_exchange_ticker_count(expanded_rows, baseline_headers)

    new_total_rows = len(expanded_rows)
    cboe_rows_added = len(accepted_rows)
    first_expansion_unlocked = new_total_rows >= FIRST_EXPANSION_THRESHOLD
    full_source_unlocked = new_total_rows >= FULL_SOURCE_THRESHOLD

    candidate_fieldnames = [
        "provider",
        "source_link_text",
        "source_raw_path",
        "cboe_company_name",
        "cboe_bats_name",
        "cboe_isin",
        "cboe_currency",
        "cboe_mic",
        "cboe_reuters_exchange_code",
        "cboe_live",
        "cboe_asset_class",
        "cboe_supported_services",
        "cboe_trading_segment",
        "cboe_printed_name",
        "candidate_key",
        "decision",
        "exclusion_reason",
    ]

    exclusion_counter = Counter(row["exclusion_reason"] for row in exclusions)

    report = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": "CBOE_EUROPE_REBUILD_COMPLETED",
        "generated_at_utc": utc_now(),
        "hard_guards": {
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
        },
        "input_sources": {
            "baseline_universe": str(baseline_path),
            "validation_decision": str(DECISION_CSV),
            "validation_profile": str(PROFILE_CSV),
            "raw_dir": str(RAW_DIR),
        },
        "validation_gate": decision,
        "counts": {
            "baseline_rows": len(baseline_rows),
            "selected_cboe_csv_files": len(profiles),
            "candidate_rows_reviewed": len(candidate_rows),
            "cboe_rows_added": cboe_rows_added,
            "exclusions": len(exclusions),
            "new_expanded_rows": new_total_rows,
            "duplicate_exchange_ticker_keys": duplicate_keys,
            "first_expansion_threshold": FIRST_EXPANSION_THRESHOLD,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "first_expansion_unlocked": first_expansion_unlocked,
            "full_source_unlocked": full_source_unlocked,
        },
        "exclusion_counter": dict(exclusion_counter),
        "selected_profiles": [
            {
                "source_link_text": p.get("source_link_text", ""),
                "raw_path": p.get("raw_path", ""),
                "rows": p.get("row_count_excluding_header", ""),
                "bytes": p.get("bytes", ""),
            }
            for p in profiles
        ],
    }

    write_csv(EXPANDED_OUT, expanded_rows, baseline_headers)
    write_csv(CANDIDATES_OUT, candidate_rows, candidate_fieldnames)
    write_csv(EXCLUSIONS_OUT, exclusions, candidate_fieldnames)
    write_json(REBUILD_JSON, report)

    md = f"""# {VERSION} — {PHASE}

Status: **CBOE_EUROPE_REBUILD_COMPLETED**

Phase type: **rebuild-only**

Generated at UTC: `{report["generated_at_utc"]}`

## Hard guards

- Network download performed: false
- Raw files modified: false
- Normalization performed: true
- Net-new filtering performed: true
- Expanded universe rebuilt: true
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Inputs

- Baseline universe: `{baseline_path}`
- Validation decision: `{DECISION_CSV}`
- Validation profile: `{PROFILE_CSV}`
- Raw dir: `{RAW_DIR}`

## Validation gate

- v2.11D decision: `{decision.get("decision")}`
- Rebuild allowed by validation: `{decision.get("rebuild_allowed_by_validation")}`

## Rebuild summary

- Baseline rows: {len(baseline_rows)}
- Selected Cboe Europe CSV files: {len(profiles)}
- Candidate rows reviewed: {len(candidate_rows)}
- Cboe Europe rows added: {cboe_rows_added}
- Exclusions: {len(exclusions)}
- New expanded rows: {new_total_rows}
- Duplicate exchange+ticker keys: {duplicate_keys}

## Thresholds

- First expansion threshold: {FIRST_EXPANSION_THRESHOLD}
- First expansion unlocked: {first_expansion_unlocked}
- Full source threshold: {FULL_SOURCE_THRESHOLD}
- Full source unlocked: {full_source_unlocked}

## Exclusion breakdown

{chr(10).join(f"- {reason}: {count}" for reason, count in sorted(exclusion_counter.items()))}

## Important scope note

v2.11E creates a rebuilt expanded source candidate only.

It does not score, call OpenAI, call broker APIs, launch the full 59k universe, or validate final scoring readiness.

v2.11F must validate the rebuilt output before any downstream use.

## Outputs

- `{EXPANDED_OUT}`
- `{EXCLUSIONS_OUT}`
- `{CANDIDATES_OUT}`
- `{REBUILD_JSON}`
- `{REBUILD_MD}`
"""

    REBUILD_MD.write_text(md, encoding="utf-8")

    print("v2.11E rebuild-only completed.")
    print(f"- expanded universe: {EXPANDED_OUT}")
    print(f"- exclusions: {EXCLUSIONS_OUT}")
    print(f"- candidates: {CANDIDATES_OUT}")
    print(f"- rebuild json: {REBUILD_JSON}")
    print(f"- rebuild report: {REBUILD_MD}")
    print("")
    print("COUNTS:")
    for key, value in report["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("EXCLUSIONS:")
    for key, value in sorted(exclusion_counter.items()):
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in report["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
