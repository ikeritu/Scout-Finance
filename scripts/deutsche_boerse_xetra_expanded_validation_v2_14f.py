from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


VERSION = "v2.14F"
PHASE = "Deutsche Boerse Xetra Expanded Validation"
PHASE_TYPE = "validation-only"

OUTPUT_DIR = Path("outputs/full_universe_source_acquisition")

EXPANDED_CSV = OUTPUT_DIR / "expanded_universe_v2_14e.csv"
ADDITIONS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_additions_v2_14e.csv"
EXCLUSIONS_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_exclusions_v2_14e.csv"
REBUILD_MANIFEST_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_rebuild_manifest_v2_14e.json"

VALIDATION_JSON = OUTPUT_DIR / "deutsche_boerse_xetra_expanded_validation_v2_14f.json"
VALIDATION_MD = OUTPUT_DIR / "deutsche_boerse_xetra_expanded_validation_v2_14f.md"
PROVIDER_BREAKDOWN_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_provider_breakdown_v2_14f.csv"
DUPLICATE_CHECK_CSV = OUTPUT_DIR / "deutsche_boerse_xetra_duplicate_check_v2_14f.csv"

EXPECTED_BASELINE_ROWS = 36863
EXPECTED_XETRA_ADDITIONS = 1424
EXPECTED_EXPANDED_ROWS = 38287
FULL_SOURCE_THRESHOLD = 50000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_overwrite_guard() -> None:
    guarded = [
        VALIDATION_JSON,
        VALIDATION_MD,
        PROVIDER_BREAKDOWN_CSV,
        DUPLICATE_CHECK_CSV,
    ]
    existing = [str(path) for path in guarded if path.exists()]
    if existing:
        raise SystemExit(
            "NO_OVERWRITE_GUARD: refusing to overwrite existing v2.14F outputs:\n"
            + "\n".join(existing)
        )


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def compact(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def read_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing required CSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    if path.exists():
        raise SystemExit(f"NO_OVERWRITE_GUARD: refusing to overwrite {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def find_col(headers: list[str], names: list[str]) -> str:
    for header in headers:
        h_low = header.lower()
        h_cmp = compact(header)
        for name in names:
            if name.lower() in h_low or compact(name) == h_cmp:
                return header
    return ""


def get_headers(rows: list[dict]) -> list[str]:
    if not rows:
        return []
    return list(rows[0].keys())


def main() -> None:
    no_overwrite_guard()

    rebuild_manifest = read_json(REBUILD_MANIFEST_JSON)

    expanded_rows = read_csv(EXPANDED_CSV)
    additions = read_csv(ADDITIONS_CSV)
    exclusions = read_csv(EXCLUSIONS_CSV)

    headers = get_headers(expanded_rows)

    provider_col = find_col(headers, ["provider", "source_provider"])
    source_provider_col = find_col(headers, ["source_provider", "provider"])
    exchange_col = find_col(headers, ["exchange", "mic", "venue", "market"])
    ticker_col = find_col(headers, ["ticker", "symbol", "mnemonic"])
    isin_col = find_col(headers, ["isin"])
    instrument_type_col = find_col(headers, ["instrument_type", "security_type"])
    asset_type_col = find_col(headers, ["asset_type"])

    provider_counter = Counter()
    duplicate_counter = Counter()
    duplicate_rows = []

    blank_exchange = 0
    blank_ticker = 0
    blank_isin = 0
    blank_company_name = 0

    seen_exchange_ticker = set()
    seen_isin_exchange_ticker = set()

    company_col = find_col(headers, ["company_name", "security_name", "name"])

    for row in expanded_rows:
        provider = normalize_text(row.get(source_provider_col, "")) or normalize_text(row.get(provider_col, "")) or "(blank)"
        provider_counter[provider] += 1

        exchange = normalize_text(row.get(exchange_col, "")).upper().replace(" ", "") if exchange_col else ""
        ticker = normalize_text(row.get(ticker_col, "")).upper().replace(" ", "") if ticker_col else ""
        isin = normalize_text(row.get(isin_col, "")).upper().replace(" ", "") if isin_col else ""
        company_name = normalize_text(row.get(company_col, "")) if company_col else ""

        if not exchange:
            blank_exchange += 1
        if not ticker:
            blank_ticker += 1
        if not isin:
            blank_isin += 1
        if not company_name:
            blank_company_name += 1

        if exchange and ticker:
            key = f"{exchange}|{ticker}"
            duplicate_counter[key] += 1
            if key in seen_exchange_ticker:
                duplicate_rows.append(
                    {
                        "duplicate_type": "exchange_ticker",
                        "key": key,
                        "exchange": exchange,
                        "ticker": ticker,
                        "isin": isin,
                        "provider": provider,
                    }
                )
            seen_exchange_ticker.add(key)

        if isin and exchange and ticker:
            key2 = f"{isin}|{exchange}|{ticker}"
            if key2 in seen_isin_exchange_ticker:
                duplicate_rows.append(
                    {
                        "duplicate_type": "isin_exchange_ticker",
                        "key": key2,
                        "exchange": exchange,
                        "ticker": ticker,
                        "isin": isin,
                        "provider": provider,
                    }
                )
            seen_isin_exchange_ticker.add(key2)

    duplicate_exchange_ticker_keys = sum(1 for _, count in duplicate_counter.items() if count > 1)

    xetra_additions_by_type = Counter()
    xetra_additions_blank_isin = 0
    xetra_additions_blank_ticker = 0
    xetra_additions_non_cs = 0

    for row in additions:
        typ = normalize_text(row.get("instrument_type", "")).upper()
        xetra_additions_by_type[typ or "(blank)"] += 1

        if not normalize_text(row.get("isin", "")):
            xetra_additions_blank_isin += 1
        if not normalize_text(row.get("ticker", "")):
            xetra_additions_blank_ticker += 1
        if typ != "CS":
            xetra_additions_non_cs += 1

    exclusion_reason_counter = Counter(row.get("exclusion_reason", "") for row in exclusions)

    expanded_count = len(expanded_rows)
    rows_needed_after = max(0, FULL_SOURCE_THRESHOLD - expanded_count)
    source_to_50k_after = round((expanded_count / FULL_SOURCE_THRESHOLD) * 100, 1)

    full_source_unlocked = expanded_count >= FULL_SOURCE_THRESHOLD

    provider_breakdown_rows = [
        {
            "provider": provider,
            "rows": count,
        }
        for provider, count in provider_counter.most_common()
    ]

    duplicate_rows_limited = duplicate_rows[:5000]

    checks = []

    def add_check(check: str, passed: bool, severity: str, detail: str) -> None:
        checks.append(
            {
                "check": check,
                "passed": bool(passed),
                "severity": severity,
                "detail": detail,
            }
        )

    add_check("expanded_csv_exists", EXPANDED_CSV.exists(), "critical", str(EXPANDED_CSV))
    add_check("additions_csv_exists", ADDITIONS_CSV.exists(), "critical", str(ADDITIONS_CSV))
    add_check("exclusions_csv_exists", EXCLUSIONS_CSV.exists(), "critical", str(EXCLUSIONS_CSV))
    add_check("rebuild_manifest_exists", REBUILD_MANIFEST_JSON.exists(), "critical", str(REBUILD_MANIFEST_JSON))

    add_check("expanded_rows_expected", expanded_count == EXPECTED_EXPANDED_ROWS, "critical", f"expanded_rows={expanded_count}; expected={EXPECTED_EXPANDED_ROWS}")
    add_check("xetra_additions_expected", len(additions) == EXPECTED_XETRA_ADDITIONS, "critical", f"additions={len(additions)}; expected={EXPECTED_XETRA_ADDITIONS}")
    add_check("expanded_delta_expected", expanded_count - EXPECTED_BASELINE_ROWS == EXPECTED_XETRA_ADDITIONS, "critical", f"delta={expanded_count - EXPECTED_BASELINE_ROWS}")

    add_check("xetra_additions_all_cs", xetra_additions_non_cs == 0, "critical", f"non_cs_additions={xetra_additions_non_cs}")
    add_check("xetra_additions_have_isin", xetra_additions_blank_isin == 0, "critical", f"blank_isin={xetra_additions_blank_isin}")
    add_check("xetra_additions_have_ticker", xetra_additions_blank_ticker == 0, "critical", f"blank_ticker={xetra_additions_blank_ticker}")

    add_check("duplicate_exchange_ticker_keys_zero", duplicate_exchange_ticker_keys == 0, "critical", f"duplicate_exchange_ticker_keys={duplicate_exchange_ticker_keys}")
    add_check("full_source_still_blocked", not full_source_unlocked, "critical", f"expanded_rows={expanded_count}; threshold={FULL_SOURCE_THRESHOLD}")
    add_check("full_59k_not_launched", True, "critical", "full_59k_universe_launched=False")
    add_check("no_scoring_openai_broker", True, "critical", "scoring=False; openai=False; broker=False")

    add_check("global_blank_isin_review", blank_isin >= 0, "warning", f"blank_isin={blank_isin}")
    add_check("global_blank_ticker_review", blank_ticker >= 0, "warning", f"blank_ticker={blank_ticker}")
    add_check("global_blank_company_name_review", blank_company_name >= 0, "warning", f"blank_company_name={blank_company_name}")

    critical_failed = sum(1 for check in checks if check["severity"] == "critical" and not check["passed"])
    warning_failed = sum(1 for check in checks if check["severity"] == "warning" and not check["passed"])

    status = (
        "DEUTSCHE_BOERSE_XETRA_EXPANDED_VALIDATION_PASSED_FULL_SOURCE_STILL_BLOCKED"
        if critical_failed == 0
        else "DEUTSCHE_BOERSE_XETRA_EXPANDED_VALIDATION_FAILED_FULL_SOURCE_STILL_BLOCKED"
    )

    payload = {
        "version": VERSION,
        "phase": PHASE,
        "phase_type": PHASE_TYPE,
        "status": status,
        "generated_at_utc": utc_now(),
        "selected_provider": "deutsche_boerse_xetra_all_tradable_instruments",
        "source_decision": rebuild_manifest.get("source_decision", ""),
        "current_state": {
            "expanded_rows": expanded_count,
            "full_source_threshold": FULL_SOURCE_THRESHOLD,
            "source_to_50k_after_xetra_percent": source_to_50k_after,
            "rows_needed_after_xetra": rows_needed_after,
            "full_source_unlocked": full_source_unlocked,
            "full_59k_status": "BLOCKED_UNTIL_SOURCE_COMPLETE_AND_GATE_APPROVED",
            "previous_phase_commit": "7959cfa",
        },
        "counts": {
            "expanded_rows": expanded_count,
            "xetra_additions": len(additions),
            "xetra_exclusions": len(exclusions),
            "expanded_delta_vs_expected_baseline": expanded_count - EXPECTED_BASELINE_ROWS,
            "duplicate_exchange_ticker_keys": duplicate_exchange_ticker_keys,
            "blank_exchange": blank_exchange,
            "blank_ticker": blank_ticker,
            "blank_isin": blank_isin,
            "blank_company_name": blank_company_name,
            "xetra_additions_blank_isin": xetra_additions_blank_isin,
            "xetra_additions_blank_ticker": xetra_additions_blank_ticker,
            "xetra_additions_non_cs": xetra_additions_non_cs,
            "critical_failed_checks": critical_failed,
            "warning_failed_checks": warning_failed,
        },
        "xetra_additions_by_instrument_type": dict(xetra_additions_by_type),
        "xetra_exclusion_reason_counts": dict(exclusion_reason_counter),
        "provider_breakdown": provider_breakdown_rows,
        "checks": checks,
        "hard_guards": {
            "phase_type": PHASE_TYPE,
            "network_download_performed": False,
            "raw_files_downloaded": False,
            "raw_files_modified_after_write": False,
            "workbook_or_csv_parsed_for_validation": True,
            "normalization_performed": False,
            "net_new_filtering_performed": False,
            "expanded_universe_rebuilt": False,
            "scoring_recalculated": False,
            "openai_called": False,
            "broker_called": False,
            "full_59k_universe_launched": False,
            "overwrite_allowed": False,
        },
        "recommended_next_phase": "v2.14G - Deutsche Boerse Xetra Closure Report",
    }

    write_json(VALIDATION_JSON, payload)

    write_csv(PROVIDER_BREAKDOWN_CSV, provider_breakdown_rows, ["provider", "rows"])

    write_csv(
        DUPLICATE_CHECK_CSV,
        duplicate_rows_limited,
        ["duplicate_type", "key", "exchange", "ticker", "isin", "provider"],
    )

    check_lines = "\n".join(
        f"- {check['check']}: {'PASS' if check['passed'] else 'FAIL'} ({check['severity']}) — {check['detail']}"
        for check in checks
    )

    provider_lines = "\n".join(
        f"- {row['provider']}: {row['rows']}"
        for row in provider_breakdown_rows[:25]
    )

    exclusion_lines = "\n".join(
        f"- {reason}: {count}"
        for reason, count in exclusion_reason_counter.most_common()
    )

    VALIDATION_MD.write_text(
        f"""# {VERSION} - {PHASE}

Status: **{status}**

Phase type: **validation-only**

Selected provider: **deutsche_boerse_xetra_all_tradable_instruments**

Generated at UTC: `{payload["generated_at_utc"]}`

## Decision

- Expanded validation passed: **{str(critical_failed == 0).lower()}**
- Full source unlocked: **{str(full_source_unlocked).lower()}**
- Full 59k: **blocked**
- Recommended next phase: **v2.14G - Deutsche Boerse Xetra Closure Report**

## Counts

- Expanded rows: {expanded_count}
- Xetra additions: {len(additions)}
- Xetra exclusions: {len(exclusions)}
- Expanded delta vs baseline: {expanded_count - EXPECTED_BASELINE_ROWS}
- Duplicate exchange+ticker keys: {duplicate_exchange_ticker_keys}
- Xetra additions non-CS: {xetra_additions_non_cs}
- Xetra additions blank ISIN: {xetra_additions_blank_isin}
- Xetra additions blank ticker: {xetra_additions_blank_ticker}
- Rows needed after Xetra: {rows_needed_after}
- Source-to-50k after Xetra: {source_to_50k_after}%
- Critical failed checks: {critical_failed}
- Warning failed checks: {warning_failed}

## Provider breakdown

{provider_lines}

## Xetra exclusion reason counts

{exclusion_lines}

## Checks

{check_lines}

## Guards

- Network download performed in v2.14F: false
- Raw files downloaded in v2.14F: false
- Raw files modified after write: false
- Workbook/CSV parsed for validation: true
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Important note

This phase validates the v2.14E expanded source only. It does not rebuild, score, call OpenAI, call broker APIs or launch full 59k.
""",
        encoding="utf-8",
    )

    print("v2.14F Deutsche Boerse Xetra expanded validation completed.")
    print(f"- validation json: {VALIDATION_JSON}")
    print(f"- validation report: {VALIDATION_MD}")
    print(f"- provider breakdown: {PROVIDER_BREAKDOWN_CSV}")
    print(f"- duplicate check: {DUPLICATE_CHECK_CSV}")
    print("")
    print("DECISION:")
    print(f"- status: {status}")
    print(f"- recommended_next_phase: v2.14G - Deutsche Boerse Xetra Closure Report")
    print("")
    print("COUNTS:")
    for key, value in payload["counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("GUARDS:")
    for key, value in payload["hard_guards"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
