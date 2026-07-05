from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.2C"
METHOD = "source_validation_59k_v1"

DEFAULT_SOURCE = ROOT / "data" / "raw" / "universe_source_real_clean.csv"
OUT_DIR = ROOT / "outputs" / "large_universe_dry_run_59k"
OUT_JSON = OUT_DIR / "source_validation_v2_2c.json"
OUT_MD = OUT_DIR / "source_validation_v2_2c.md"
OUT_COLUMNS_CSV = OUT_DIR / "source_validation_columns_v2_2c.csv"

TICKER_ALIASES = ["ticker", "Ticker", "symbol", "Symbol", "SYMBOL", "ticker_symbol", "Ticker Symbol"]
RECOMMENDED_COLUMNS = {
    "company_name": ["company_name", "Company Name", "Name", "name"],
    "exchange": ["exchange", "Exchange"],
    "sector": ["sector", "Sector"],
    "industry": ["industry", "Industry"],
    "country": ["country", "Country"],
    "market_cap": ["market_cap", "Market Cap", "MarketCap", "market capitalization"],
}

EXPECTED_59K_ROWS = 59000
MIN_SOURCE_ROWS_FOR_SMALL_BATCH = 1000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def find_first_existing(columns: list[str], aliases: list[str]) -> str | None:
    for alias in aliases:
        if alias in columns:
            return alias
    lower_map = {col.lower(): col for col in columns}
    for alias in aliases:
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scout Finance v2.2C source validation for future 59k dry-run.")
    parser.add_argument(
        "--source",
        type=str,
        default=str(DEFAULT_SOURCE),
        help="Source CSV to validate.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source = resolve_path(args.source)

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    columns: list[str] = []
    rows: list[dict[str, str]] = []
    ticker_column: str | None = None

    source_exists = source.exists()
    source_size_bytes = source.stat().st_size if source_exists and source.is_file() else None
    source_size_mb = round(source_size_bytes / 1024 / 1024, 3) if isinstance(source_size_bytes, int) else None

    if not source_exists:
        blockers.append(f"Source file does not exist: {rel(source)}")
    elif not source.is_file():
        blockers.append(f"Source path is not a file: {rel(source)}")
    else:
        try:
            columns, rows = read_csv(source)
            positives.append(f"Source CSV is readable: {rel(source)}")
        except Exception as exc:
            blockers.append(f"Could not read source CSV: {exc}")

    if rows:
        row_count = len(rows)
        ticker_column = find_first_existing(columns, TICKER_ALIASES)

        if ticker_column:
            positives.append(f"Ticker column resolved: {ticker_column} -> ticker")
        else:
            blockers.append("No ticker-compatible column found.")

        if row_count >= EXPECTED_59K_ROWS:
            positives.append("Source appears large enough for a 59k dry-run.")
            source_scope = "FULL_59K_CANDIDATE"
        elif row_count >= MIN_SOURCE_ROWS_FOR_SMALL_BATCH:
            warnings.append(
                f"Source has {row_count} rows, below 59k. Valid for small batch, not full 59k."
            )
            source_scope = "PARTIAL_REAL_SOURCE_FOR_SMALL_BATCH"
        else:
            blockers.append(f"Source has only {row_count} rows, below minimum small-batch threshold.")
            source_scope = "TOO_SMALL"
    else:
        row_count = 0
        source_scope = "UNREADABLE_OR_EMPTY"

    ticker_stats = {
        "empty_tickers": None,
        "duplicate_tickers": None,
        "unique_tickers": None,
        "sample_duplicates": [],
    }

    if rows and ticker_column:
        tickers = [(row.get(ticker_column) or "").strip() for row in rows]
        empty = [ticker for ticker in tickers if not ticker]
        non_empty = [ticker.upper() for ticker in tickers if ticker]
        counts = Counter(non_empty)
        duplicates = sorted([ticker for ticker, count in counts.items() if count > 1])

        ticker_stats = {
            "empty_tickers": len(empty),
            "duplicate_tickers": len(duplicates),
            "unique_tickers": len(counts),
            "sample_duplicates": duplicates[:25],
        }

        if empty:
            warnings.append(f"Source contains {len(empty)} empty ticker values.")
        else:
            positives.append("No empty ticker values detected.")

        if duplicates:
            warnings.append(f"Source contains {len(duplicates)} duplicate tickers.")
        else:
            positives.append("No duplicate tickers detected.")

    recommended_mapping: dict[str, str | None] = {}
    missing_recommended: list[str] = []

    for canonical, aliases in RECOMMENDED_COLUMNS.items():
        found = find_first_existing(columns, aliases)
        recommended_mapping[canonical] = found
        if found:
            positives.append(f"Recommended column resolved: {found} -> {canonical}")
        else:
            missing_recommended.append(canonical)

    if missing_recommended:
        warnings.append("Missing recommended columns: " + ", ".join(missing_recommended))

    column_rows = []
    for col in columns:
        canonical = None
        if col == ticker_column:
            canonical = "ticker"
        else:
            for key, found in recommended_mapping.items():
                if found == col:
                    canonical = key
                    break

        column_rows.append(
            {
                "source_column": col,
                "canonical_column": canonical or "",
                "used": bool(canonical),
            }
        )

    with OUT_COLUMNS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source_column", "canonical_column", "used"])
        writer.writeheader()
        writer.writerows(column_rows)

    if blockers:
        validation_status = "SOURCE_VALIDATION_BLOCKED"
        readiness_score = 0
    elif warnings:
        validation_status = "SOURCE_VALID_FOR_SMALL_BATCH_WITH_WARNINGS"
        readiness_score = 80
    else:
        validation_status = "SOURCE_VALID_FOR_59K_DRY_RUN"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "validation_status": validation_status,
        "readiness_score": readiness_score,
        "source": {
            "path": rel(source),
            "exists": source_exists,
            "size_bytes": source_size_bytes,
            "size_mb": source_size_mb,
            "rows": row_count,
            "columns": len(columns),
            "source_scope": source_scope,
        },
        "ticker_mapping": {
            "source_column": ticker_column,
            "canonical_column": "ticker" if ticker_column else None,
        },
        "recommended_mapping": recommended_mapping,
        "ticker_stats": ticker_stats,
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
        },
        "recommendation": (
            "Proceed to v2.2D small batch dry-run using this partial real source."
            if validation_status == "SOURCE_VALID_FOR_SMALL_BATCH_WITH_WARNINGS"
            else "Proceed to v2.2D with full-source safeguards."
            if validation_status == "SOURCE_VALID_FOR_59K_DRY_RUN"
            else "Resolve blockers before any small batch dry-run."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.2C 59k Source Validation")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Validation status: **{validation_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Source: `{rel(source)}`")
    md.append(f"- Rows: {row_count}")
    md.append(f"- Columns: {len(columns)}")
    md.append(f"- Source scope: **{source_scope}**")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("")
    md.append("## Ticker mapping")
    md.append("")
    md.append(f"- Source column: {ticker_column}")
    md.append("- Canonical column: ticker" if ticker_column else "- Canonical column: unresolved")
    md.append("")
    md.append("## Ticker stats")
    md.append("")
    for key, value in ticker_stats.items():
        md.append(f"- {key}: {value}")
    md.append("")
    md.append("## Recommended mapping")
    md.append("")
    for key, value in recommended_mapping.items():
        md.append(f"- {key}: {value}")
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
    md.append("Important: v2.2C validates the source only. It does not execute scoring or a 59k dry-run.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.2C 59k Source Validation")
    print("=" * 92)
    print(f"OK   Validation status: {validation_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Source rows: {row_count}")
    print(f"OK   Source columns: {len(columns)}")
    print(f"OK   Ticker column: {ticker_column}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Columns CSV written: {OUT_COLUMNS_CSV}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
