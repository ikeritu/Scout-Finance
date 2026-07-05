from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.4A"
METHOD = "controlled_provider_source_acquisition_v1"

OUT_DIR = ROOT / "outputs" / "full_universe_source_acquisition"
OUT_JSON = OUT_DIR / "provider_source_acquisition_v2_4a.json"
OUT_MD = OUT_DIR / "provider_source_acquisition_v2_4a.md"

PROVIDER_ROOT = ROOT / "data" / "raw" / "source_providers"

SOURCES = [
    {
        "provider_id": "nasdaq_trader_nasdaqlisted",
        "url": "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt",
        "raw_filename": "nasdaqlisted.txt",
        "csv_filename": "nasdaq_trader_nasdaqlisted.csv",
        "delimiter": "|",
    },
    {
        "provider_id": "nasdaq_trader_otherlisted",
        "url": "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt",
        "raw_filename": "otherlisted.txt",
        "csv_filename": "nasdaq_trader_otherlisted.csv",
        "delimiter": "|",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def download_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ScoutFinance/controlled-source-acquisition"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def pipe_text_to_csv_rows(text: str, delimiter: str) -> tuple[list[str], list[dict[str, str]], list[str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    ignored_lines: list[str] = []

    if not lines:
        return [], [], ["Empty source file."]

    header_line = lines[0]
    headers = [item.strip() for item in header_line.split(delimiter)]

    rows: list[dict[str, str]] = []

    for line in lines[1:]:
        if line.lower().startswith("file creation time"):
            ignored_lines.append(line)
            continue

        values = [item.strip() for item in line.split(delimiter)]

        if len(values) != len(headers):
            ignored_lines.append(line)
            continue

        rows.append(dict(zip(headers, values)))

    return headers, rows, ignored_lines


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_ROOT.mkdir(parents=True, exist_ok=True)

    results = []
    blockers: list[str] = []
    warnings: list[str] = []
    positives: list[str] = []

    total_rows = 0

    for source in SOURCES:
        provider_id = source["provider_id"]
        provider_dir = PROVIDER_ROOT / provider_id
        provider_dir.mkdir(parents=True, exist_ok=True)

        raw_path = provider_dir / source["raw_filename"]
        csv_path = provider_dir / source["csv_filename"]

        result = {
            "provider_id": provider_id,
            "url": source["url"],
            "raw_path": rel(raw_path),
            "csv_path": rel(csv_path),
            "downloaded": False,
            "converted": False,
            "rows": 0,
            "columns": 0,
            "ignored_lines": 0,
            "blockers": [],
            "warnings": [],
            "positives": [],
        }

        try:
            text = download_text(source["url"])
            raw_path.write_text(text, encoding="utf-8")
            result["downloaded"] = True
            result["positives"].append("Source downloaded.")
        except Exception as exc:
            result["blockers"].append(f"Download failed: {exc}")
            blockers.append(f"{provider_id}: download failed.")
            results.append(result)
            continue

        headers, rows, ignored_lines = pipe_text_to_csv_rows(text, source["delimiter"])

        if not headers:
            result["blockers"].append("No headers detected.")
            blockers.append(f"{provider_id}: no headers detected.")
            results.append(result)
            continue

        if not rows:
            result["blockers"].append("No data rows detected.")
            blockers.append(f"{provider_id}: no data rows detected.")
            results.append(result)
            continue

        write_csv(csv_path, headers, rows)

        result["converted"] = True
        result["rows"] = len(rows)
        result["columns"] = len(headers)
        result["ignored_lines"] = len(ignored_lines)
        result["positives"].append("Pipe-delimited source converted to CSV.")
        total_rows += len(rows)

        if ignored_lines:
            result["warnings"].append(f"Ignored non-data lines: {len(ignored_lines)}")

        results.append(result)

    for result in results:
        positives.extend([f"{result['provider_id']}: {item}" for item in result["positives"]])
        warnings.extend([f"{result['provider_id']}: {item}" for item in result["warnings"]])
        blockers.extend([f"{result['provider_id']}: {item}" for item in result["blockers"]])

    if blockers:
        acquisition_status = "PROVIDER_SOURCE_ACQUISITION_BLOCKED"
        readiness_score = 0
    elif warnings:
        acquisition_status = "PROVIDER_SOURCE_ACQUISITION_COMPLETED_WITH_WARNINGS"
        readiness_score = 85
    else:
        acquisition_status = "PROVIDER_SOURCE_ACQUISITION_COMPLETED"
        readiness_score = 100

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "acquisition_status": acquisition_status,
        "readiness_score": readiness_score,
        "provider_count": len(SOURCES),
        "total_rows": total_rows,
        "results": results,
        "blockers": blockers,
        "warnings": warnings,
        "positives": positives,
        "controls": {
            "network_download_performed": True,
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
            "expanded_source_written": False,
        },
        "recommendation": (
            "Rerun v2.3E, then rerun v2.3F to validate local provider CSVs."
            if not blockers
            else "Resolve acquisition blockers before rerunning v2.3E/v2.3F."
        ),
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md: list[str] = []
    md.append("# Scout Finance ? v2.4A Controlled Provider Source Acquisition")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Acquisition status: **{acquisition_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Provider count: {len(SOURCES)}")
    md.append(f"- Total rows: {total_rows}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- Network download performed: true")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Full 59k universe launched: false")
    md.append("- Financial advice: false")
    md.append("- Expanded source written: false")
    md.append("")
    md.append("## Results")
    md.append("")
    for result in results:
        md.append(f"### {result['provider_id']}")
        md.append("")
        md.append(f"- URL: {result['url']}")
        md.append(f"- Raw path: `{result['raw_path']}`")
        md.append(f"- CSV path: `{result['csv_path']}`")
        md.append(f"- Downloaded: {result['downloaded']}")
        md.append(f"- Converted: {result['converted']}")
        md.append(f"- Rows: {result['rows']}")
        md.append(f"- Columns: {result['columns']}")
        md.append(f"- Ignored lines: {result['ignored_lines']}")
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

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.4A Controlled Provider Source Acquisition")
    print("=" * 92)
    print(f"OK   Acquisition status: {acquisition_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Provider count: {len(SOURCES)}")
    print(f"OK   Total rows: {total_rows}")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   Network download performed: True")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
