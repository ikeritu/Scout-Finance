from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.3A"
METHOD = "full_universe_source_acquisition_audit_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "full_universe_source_acquisition_audit_v2_3a.json"
OUT_MD = OUT_DIR / "full_universe_source_acquisition_audit_v2_3a.md"
OUT_CSV = OUT_DIR / "full_universe_source_candidates_v2_3a.csv"

SEARCH_DIRS = [
    ROOT / "data",
    ROOT / "outputs",
]

EXPECTED_FULL_ROWS = 59000
MIN_FULL_SOURCE_ROWS = 50000
MIN_SMALL_BATCH_ROWS = 1000

TICKER_ALIASES = {
    "ticker",
    "Ticker",
    "TICKER",
    "symbol",
    "Symbol",
    "SYMBOL",
    "ticker_symbol",
    "Ticker Symbol",
}

RECOMMENDED_ALIASES = {
    "company_name": {"company_name", "Company Name", "Name", "name", "company", "Company"},
    "exchange": {"exchange", "Exchange", "market", "Market"},
    "sector": {"sector", "Sector"},
    "industry": {"industry", "Industry"},
    "country": {"country", "Country"},
    "market_cap": {"market_cap", "Market Cap", "MarketCap", "market capitalization"},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def safe_read_csv_profile(path: Path) -> dict:
    profile = {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "readable": False,
        "rows": 0,
        "columns": 0,
        "column_names": [],
        "ticker_column": None,
        "empty_tickers": None,
        "duplicate_tickers": None,
        "unique_tickers": None,
        "recommended_columns_found": {},
        "candidate_scope": "UNKNOWN",
        "candidate_status": "UNREAD",
        "blockers": [],
        "warnings": [],
        "positives": [],
    }

    if not path.exists():
        profile["blockers"].append("File does not exist.")
        return profile

    if not path.is_file():
        profile["blockers"].append("Path is not a file.")
        return profile

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            columns = list(reader.fieldnames or [])
            rows = list(reader)
    except UnicodeDecodeError:
        try:
            with path.open("r", encoding="latin-1", newline="") as fh:
                reader = csv.DictReader(fh)
                columns = list(reader.fieldnames or [])
                rows = list(reader)
        except Exception as exc:
            profile["blockers"].append(f"Could not read CSV with utf-8-sig or latin-1: {exc}")
            return profile
    except Exception as exc:
        profile["blockers"].append(f"Could not read CSV: {exc}")
        return profile

    profile["readable"] = True
    profile["rows"] = len(rows)
    profile["columns"] = len(columns)
    profile["column_names"] = columns
    profile["positives"].append("CSV is readable.")

    ticker_column = next((col for col in columns if col in TICKER_ALIASES), None)
    profile["ticker_column"] = ticker_column

    if ticker_column:
        tickers = [(row.get(ticker_column) or "").strip().upper() for row in rows]
        empty = sum(1 for value in tickers if not value)
        non_empty = [value for value in tickers if value]
        unique = set(non_empty)
        duplicates = len(non_empty) - len(unique)

        profile["empty_tickers"] = empty
        profile["duplicate_tickers"] = duplicates
        profile["unique_tickers"] = len(unique)
        profile["positives"].append(f"Ticker column resolved: {ticker_column}")

        if empty:
            profile["warnings"].append(f"Empty ticker values detected: {empty}")
        if duplicates:
            profile["warnings"].append(f"Duplicate ticker values detected: {duplicates}")
    else:
        profile["blockers"].append("No ticker/symbol column detected.")

    for canonical, aliases in RECOMMENDED_ALIASES.items():
        found = next((col for col in columns if col in aliases), None)
        profile["recommended_columns_found"][canonical] = found

    if profile["rows"] >= MIN_FULL_SOURCE_ROWS:
        profile["candidate_scope"] = "FULL_UNIVERSE_CANDIDATE"
        profile["positives"].append(f"Rows meet full-source threshold: {profile['rows']} >= {MIN_FULL_SOURCE_ROWS}")
    elif profile["rows"] >= MIN_SMALL_BATCH_ROWS:
        profile["candidate_scope"] = "PARTIAL_REAL_SOURCE_FOR_SMALL_BATCH"
        profile["warnings"].append(f"Rows below full-source threshold: {profile['rows']} < {MIN_FULL_SOURCE_ROWS}")
    else:
        profile["candidate_scope"] = "TOO_SMALL_FOR_SCALE"
        profile["warnings"].append(f"Rows below small-batch threshold: {profile['rows']} < {MIN_SMALL_BATCH_ROWS}")

    if profile["blockers"]:
        profile["candidate_status"] = "BLOCKED"
    elif profile["candidate_scope"] == "FULL_UNIVERSE_CANDIDATE":
        profile["candidate_status"] = "POTENTIAL_FULL_SOURCE"
    elif profile["candidate_scope"] == "PARTIAL_REAL_SOURCE_FOR_SMALL_BATCH":
        profile["candidate_status"] = "PARTIAL_SOURCE_ONLY"
    else:
        profile["candidate_status"] = "NOT_USEFUL_FOR_SCALE"

    return profile


def find_csv_files() -> list[Path]:
    candidates: list[Path] = []

    for directory in SEARCH_DIRS:
        if not directory.exists():
            continue

        for path in directory.rglob("*.csv"):
            normalized = rel(path)

            if ".venv" in normalized:
                continue
            if "__pycache__" in normalized:
                continue

            candidates.append(path)

    return sorted(set(candidates), key=lambda p: rel(p).lower())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = find_csv_files()
    profiles = [safe_read_csv_profile(path) for path in csv_files]

    profiles_sorted = sorted(
        profiles,
        key=lambda item: (
            item.get("rows") or 0,
            item.get("size_bytes") or 0,
        ),
        reverse=True,
    )

    full_candidates = [p for p in profiles_sorted if p["candidate_status"] == "POTENTIAL_FULL_SOURCE"]
    partial_candidates = [p for p in profiles_sorted if p["candidate_status"] == "PARTIAL_SOURCE_ONLY"]

    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    if full_candidates:
        positives.append(f"Potential full universe candidates found: {len(full_candidates)}")
        audit_status = "FULL_SOURCE_CANDIDATE_FOUND"
        readiness_score = 80
    elif partial_candidates:
        warnings.append(f"No full universe source found. Partial candidates found: {len(partial_candidates)}")
        audit_status = "NO_FULL_SOURCE_FOUND_PARTIAL_AVAILABLE"
        readiness_score = 40
    else:
        blockers.append("No usable universe source candidate found.")
        audit_status = "NO_USABLE_SOURCE_FOUND"
        readiness_score = 0

    positives.append(f"CSV files scanned: {len(csv_files)}")

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "audit_status": audit_status,
        "readiness_score": readiness_score,
        "expected_full_rows": EXPECTED_FULL_ROWS,
        "minimum_full_source_rows": MIN_FULL_SOURCE_ROWS,
        "csv_files_scanned": len(csv_files),
        "full_candidates_count": len(full_candidates),
        "partial_candidates_count": len(partial_candidates),
        "top_candidates": profiles_sorted[:20],
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
            "Use the best full universe candidate for v2.3B source normalization."
            if full_candidates
            else "Acquire or build a real full-size source before repeating v2.2C/v2.2E for full 59k."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_fieldnames = [
        "path",
        "candidate_status",
        "candidate_scope",
        "rows",
        "columns",
        "size_bytes",
        "ticker_column",
        "empty_tickers",
        "duplicate_tickers",
        "unique_tickers",
    ]

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(profiles_sorted)

    md: list[str] = []
    md.append("# Scout Finance ? v2.3A Full Universe Source Acquisition Audit")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Audit status: **{audit_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- CSV files scanned: {len(csv_files)}")
    md.append(f"- Full candidates: {len(full_candidates)}")
    md.append(f"- Partial candidates: {len(partial_candidates)}")
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
    md.append("## Top candidates")
    md.append("")
    if profiles_sorted:
        for item in profiles_sorted[:15]:
            md.append(
                f"- `{item['path']}` ? status: **{item['candidate_status']}**, "
                f"scope: {item['candidate_scope']}, rows: {item['rows']}, "
                f"ticker column: {item['ticker_column']}"
            )
    else:
        md.append("- No CSV files found.")
    md.append("")
    md.append("## Positives")
    md.append("")
    for item in positives:
        md.append(f"- {item}")
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
    md.append("Important: v2.3A is an acquisition audit only. It does not execute scoring, OpenAI, broker calls, or full 59k.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.3A Full Universe Source Acquisition Audit")
    print("=" * 92)
    print(f"OK   Audit status: {audit_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   CSV files scanned: {len(csv_files)}")
    print(f"OK   Full candidates: {len(full_candidates)}")
    print(f"OK   Partial candidates: {len(partial_candidates)}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print(f"OK   Candidates CSV written: {OUT_CSV}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
