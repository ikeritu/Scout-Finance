from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.3F"
METHOD = "expanded_source_validation_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "expanded_source_validation_v2_3f.json"
OUT_MD = OUT_DIR / "expanded_source_validation_v2_3f.md"
OUT_CSV = OUT_DIR / "expanded_source_validation_provider_results_v2_3f.csv"

BUILDER_JSON = OUT_DIR / "expanded_source_builder_skeleton_v2_3e.json"
PROVIDER_SCAN_CSV = OUT_DIR / "expanded_source_builder_provider_scan_v2_3e.csv"

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
TARGET_FIRST_EXPANSION_ROWS = 15000

REQUIRED_CANONICAL_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "country",
    "source_provider",
    "source_file",
    "instrument_type",
    "instrument_scope",
    "classification_confidence",
    "classification_reason",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_exists": False, "_path": rel(path)}

    data = json.loads(path.read_text(encoding="utf-8"))
    data["_exists"] = True
    data["_path"] = rel(path)
    return data


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def validate_provider_file(path: Path, provider_id: str) -> dict:
    result = {
        "provider_id": provider_id,
        "path": rel(path),
        "exists": path.exists(),
        "readable": False,
        "rows": 0,
        "columns": 0,
        "has_ticker_like_column": False,
        "ticker_like_column": "",
        "empty_tickers": 0,
        "duplicate_tickers": 0,
        "unique_tickers": 0,
        "status": "MISSING",
        "blockers": [],
        "warnings": [],
        "positives": [],
    }

    if not path.exists():
        result["blockers"].append("Selected provider file does not exist.")
        return result

    try:
        columns, rows = read_csv_rows(path)
    except Exception as exc:
        result["status"] = "READ_ERROR"
        result["blockers"].append(f"Could not read CSV: {exc}")
        return result

    result["readable"] = True
    result["rows"] = len(rows)
    result["columns"] = len(columns)
    result["positives"].append("Provider CSV is readable.")

    ticker_aliases = ["ticker", "Ticker", "TICKER", "symbol", "Symbol", "SYMBOL", "ACT Symbol", "code"]
    ticker_col = next((col for col in columns if col in ticker_aliases), "")

    if ticker_col:
        result["has_ticker_like_column"] = True
        result["ticker_like_column"] = ticker_col
        tickers = [(row.get(ticker_col) or "").strip().upper() for row in rows]
        non_empty = [ticker for ticker in tickers if ticker]
        result["empty_tickers"] = len(tickers) - len(non_empty)
        result["unique_tickers"] = len(set(non_empty))
        result["duplicate_tickers"] = len(non_empty) - len(set(non_empty))
        result["positives"].append(f"Ticker-like column found: {ticker_col}")

        if result["empty_tickers"]:
            result["warnings"].append(f"Empty ticker values: {result['empty_tickers']}")

        if result["duplicate_tickers"]:
            result["warnings"].append(f"Duplicate ticker values within provider: {result['duplicate_tickers']}")
    else:
        result["blockers"].append("No ticker-like column found.")

    if result["blockers"]:
        result["status"] = "PROVIDER_FILE_BLOCKED"
    elif result["warnings"]:
        result["status"] = "PROVIDER_FILE_VALID_WITH_WARNINGS"
    else:
        result["status"] = "PROVIDER_FILE_VALID"

    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    builder = read_json(BUILDER_JSON)

    if not builder.get("_exists"):
        blockers.append(f"Missing required v2.3E builder artifact: {rel(BUILDER_JSON)}")
        builder_status = None
    else:
        builder_status = builder.get("builder_status")
        positives.append(f"v2.3E builder artifact found: {rel(BUILDER_JSON)}")

    if builder_status in {
        "EXPANDED_SOURCE_BUILDER_SKELETON_READY",
        "EXPANDED_SOURCE_BUILDER_SKELETON_READY_WITH_WARNINGS",
    }:
        positives.append(f"v2.3E builder status usable: {builder_status}")
    else:
        blockers.append(f"v2.3E builder status is not usable: {builder_status}")

    if not PROVIDER_SCAN_CSV.exists():
        blockers.append(f"Missing provider scan CSV: {rel(PROVIDER_SCAN_CSV)}")
        scan_rows = []
    else:
        _, scan_rows = read_csv_rows(PROVIDER_SCAN_CSV)
        positives.append(f"Provider scan CSV found: {rel(PROVIDER_SCAN_CSV)}")

    found_provider_rows = [
        row for row in scan_rows
        if str(row.get("local_file_found", "")).lower() == "true"
        and row.get("selected_file")
    ]

    provider_results: list[dict] = []
    total_rows = 0
    total_unique_provider_tickers = 0
    valid_provider_files = 0

    for row in found_provider_rows:
        selected_file = ROOT / row["selected_file"]
        provider_id = row.get("provider_id") or "unknown_provider"
        result = validate_provider_file(selected_file, provider_id)
        provider_results.append(result)

        if result["status"] in {"PROVIDER_FILE_VALID", "PROVIDER_FILE_VALID_WITH_WARNINGS"}:
            valid_provider_files += 1
            total_rows += int(result["rows"])
            total_unique_provider_tickers += int(result["unique_tickers"])

    if not found_provider_rows:
        blockers.append("No local provider CSV files found. Add provider files before expanded source validation.")
    else:
        positives.append(f"Local provider CSV files found: {len(found_provider_rows)}")

    provider_blockers = []
    provider_warnings = []

    for result in provider_results:
        for item in result["blockers"]:
            provider_blockers.append(f"{result['provider_id']}: {item}")
        for item in result["warnings"]:
            provider_warnings.append(f"{result['provider_id']}: {item}")

    blockers.extend(provider_blockers)
    warnings.extend(provider_warnings)

    if total_rows >= MIN_FULL_SOURCE_ROWS:
        positives.append(f"Expanded source row count meets full threshold: {total_rows} >= {MIN_FULL_SOURCE_ROWS}")
    elif total_rows >= TARGET_FIRST_EXPANSION_ROWS:
        warnings.append(
            f"Expanded source meets first expansion target but not full threshold: "
            f"{total_rows} >= {TARGET_FIRST_EXPANSION_ROWS}, < {MIN_FULL_SOURCE_ROWS}"
        )
    elif total_rows > 0:
        warnings.append(f"Expanded source rows below first expansion target: {total_rows} < {TARGET_FIRST_EXPANSION_ROWS}")

    if blockers:
        if not found_provider_rows:
            validation_status = "EXPANDED_SOURCE_VALIDATION_BLOCKED_NO_PROVIDER_FILES"
        else:
            validation_status = "EXPANDED_SOURCE_VALIDATION_BLOCKED"
        readiness_score = 0
    elif warnings:
        validation_status = "EXPANDED_SOURCE_VALIDATION_READY_WITH_WARNINGS"
        readiness_score = 70
    else:
        validation_status = "EXPANDED_SOURCE_VALIDATION_READY"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "builder_input": {
            "path": rel(BUILDER_JSON),
            "exists": builder.get("_exists"),
            "builder_status": builder_status,
        },
        "targets": {
            "expected_full_rows": EXPECTED_FULL_ROWS,
            "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
            "target_first_expansion_rows": TARGET_FIRST_EXPANSION_ROWS,
        },
        "provider_scan": {
            "path": rel(PROVIDER_SCAN_CSV),
            "exists": PROVIDER_SCAN_CSV.exists(),
            "providers_scanned": len(scan_rows),
            "provider_files_found": len(found_provider_rows),
            "valid_provider_files": valid_provider_files,
        },
        "expanded_source_summary": {
            "total_rows": total_rows,
            "total_unique_provider_tickers": total_unique_provider_tickers,
            "required_canonical_columns": REQUIRED_CANONICAL_COLUMNS,
        },
        "provider_results": provider_results,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "network_download_performed": False,
            "active_outputs_overwritten": False,
            "expanded_source_written": False,
        },
        "recommendation": (
            "Add local provider CSV files under data/raw/source_providers/<provider_id>/ and rerun v2.3E, then rerun v2.3F."
            if validation_status == "EXPANDED_SOURCE_VALIDATION_BLOCKED_NO_PROVIDER_FILES"
            else "Proceed according to validation status. Do not run full 59k unless full-source gate is later unlocked."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_fields = [
        "provider_id",
        "path",
        "exists",
        "readable",
        "rows",
        "columns",
        "has_ticker_like_column",
        "ticker_like_column",
        "empty_tickers",
        "duplicate_tickers",
        "unique_tickers",
        "status",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(provider_results)

    md: list[str] = []
    md.append("# Scout Finance ? v2.3F Expanded Source Validation")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Provider files found: {len(found_provider_rows)}")
    md.append(f"- Valid provider files: {valid_provider_files}")
    md.append(f"- Total rows: {total_rows}")
    md.append(f"- Target first expansion rows: {TARGET_FIRST_EXPANSION_ROWS}")
    md.append(f"- Minimum full source rows: {MIN_FULL_SOURCE_ROWS}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Network download performed: false")
    md.append("- Active outputs overwritten: false")
    md.append("- Expanded source written: false")
    md.append("")
    md.append("## Provider results")
    md.append("")
    if provider_results:
        for result in provider_results:
            md.append(f"### {result['provider_id']}")
            md.append("")
            md.append(f"- Status: {result['status']}")
            md.append(f"- Path: `{result['path']}`")
            md.append(f"- Rows: {result['rows']}")
            md.append(f"- Columns: {result['columns']}")
            md.append(f"- Ticker-like column: {result['ticker_like_column']}")
            md.append(f"- Empty tickers: {result['empty_tickers']}")
            md.append(f"- Duplicate tickers: {result['duplicate_tickers']}")
            md.append(f"- Unique tickers: {result['unique_tickers']}")
            md.append("")
    else:
        md.append("- No provider files were available to validate.")
        md.append("")
    md.append("## Positives")
    md.append("")
    if positives:
        for item in positives:
            md.append(f"- {item}")
    else:
        md.append("- No positives detected.")
    md.append("")
    md.append("## Blockers")
    md.append("")
    if blockers:
        for item in blockers:
            md.append(f"- {item}")
    else:
        md.append("- No blockers detected.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for item in warnings:
            md.append(f"- {item}")
    else:
        md.append("- No warnings detected.")
    md.append("")
    md.append("## Recommendation")
    md.append("")
    md.append(payload["recommendation"])
    md.append("")
    md.append("Important: v2.3F is validation only. It does not download data, execute scoring, call OpenAI, call a broker, write an expanded source, or launch full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.3F Expanded Source Validation")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Provider files found: {len(found_provider_rows)}")
    print(f"OK   Valid provider files: {valid_provider_files}")
    print(f"OK   Total rows: {total_rows}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Provider results CSV written: {OUT_CSV}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")
    print("OK   Network download performed: False")
    print("OK   Expanded source written: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
