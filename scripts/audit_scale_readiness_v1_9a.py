from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v1.9A"
METHOD = "scale_readiness_audit_v1"

OUT_DIR = ROOT / "outputs" / "scale_readiness"
OUT_JSON = OUT_DIR / "scale_readiness_audit_v1_9a.json"
OUT_MD = OUT_DIR / "scale_readiness_audit_v1_9a.md"
OUT_CSV = OUT_DIR / "scale_readiness_files_v1_9a.csv"


CRITICAL_FILES = [
    "outputs/scouting/active_real_universe_top_candidates.csv",
    "outputs/scouting/combined_score_v1_candidates.csv",
    "outputs/scoring/combined_score_v1_breakdown.csv",
    "outputs/scoring/combined_score_v1_summary.json",
    "outputs/research/current_ranking/current_ranking_research_index.json",
    "outputs/research/current_ranking_compare/current_ranking_compare_v1_7b.json",
    "outputs/research/current_ranking/manual_review_log_v1_8a.json",
    "src/combined_scoring_v1.py",
    "app.py",
]

CSV_REQUIRED_COLUMNS = {
    "outputs/scouting/active_real_universe_top_candidates.csv": [
        "ticker",
        "score",
        "combined_score_v1",
        "category_final",
        "stage3_status",
        "status",
    ],
    "outputs/scouting/combined_score_v1_candidates.csv": [
        "ticker",
        "combined_score_v1",
        "metadata_score_component",
        "market_data_score_component",
        "fundamentals_score_component",
    ],
    "outputs/scoring/combined_score_v1_breakdown.csv": [
        "ticker",
        "metadata_score_component",
        "market_data_score_component",
        "fundamentals_score_component",
        "combined_score_v1",
    ],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_csv_header_and_count(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        return list(reader.fieldnames or []), len(rows)


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def file_info(path_str: str) -> dict[str, object]:
    path = ROOT / path_str
    info: dict[str, object] = {
        "path": path_str,
        "exists": path.exists(),
        "size_bytes": None,
        "type": path.suffix.lower().lstrip("."),
        "rows": None,
        "columns": [],
        "missing_required_columns": [],
        "status": "MISSING",
    }

    if not path.exists():
        return info

    info["size_bytes"] = path.stat().st_size
    info["status"] = "OK"

    if path.suffix.lower() == ".csv":
        try:
            columns, rows = load_csv_header_and_count(path)
            info["columns"] = columns
            info["rows"] = rows
            required = CSV_REQUIRED_COLUMNS.get(path_str, [])
            missing = [col for col in required if col not in columns]
            info["missing_required_columns"] = missing
            if missing:
                info["status"] = "MISSING_COLUMNS"
            if rows == 0:
                info["status"] = "EMPTY_CSV"
        except Exception as exc:
            info["status"] = "CSV_ERROR"
            info["error"] = str(exc)

    if path.suffix.lower() == ".json":
        try:
            payload = load_json(path)
            if isinstance(payload, dict):
                info["json_top_level_keys"] = sorted(payload.keys())
                if "rows" in payload:
                    info["rows"] = payload.get("rows")
            else:
                info["json_type"] = type(payload).__name__
        except Exception as exc:
            info["status"] = "JSON_ERROR"
            info["error"] = str(exc)

    return info


def readiness_score(file_reports: list[dict[str, object]]) -> tuple[int, list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    for item in file_reports:
        path = str(item["path"])
        status = str(item["status"])

        if status == "MISSING":
            blockers.append(f"Missing critical file: {path}")
        elif status in {"CSV_ERROR", "JSON_ERROR", "MISSING_COLUMNS", "EMPTY_CSV"}:
            blockers.append(f"{path}: {status}")

        size = item.get("size_bytes")
        if isinstance(size, int) and size > 25_000_000:
            warnings.append(f"Large file may need streaming/pagination: {path} ({size} bytes)")

        rows = item.get("rows")
        if isinstance(rows, int) and rows > 10_000:
            warnings.append(f"High row count should be tested for UI/performance: {path} ({rows} rows)")

    score = 100
    score -= len(blockers) * 20
    score -= len(warnings) * 5
    score = max(0, min(100, score))

    return score, blockers, warnings


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    reports = [file_info(path) for path in CRITICAL_FILES]
    score, blockers, warnings = readiness_score(reports)

    if blockers:
        readiness_status = "NOT_READY"
    elif warnings:
        readiness_status = "READY_WITH_WARNINGS"
    else:
        readiness_status = "READY_FOR_CONTROLLED_SCALE_TEST"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "readiness_status": readiness_status,
        "readiness_score": score,
        "critical_files_checked": len(reports),
        "blockers": blockers,
        "warnings": warnings,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "large_universe_launched": False,
            "financial_advice": False,
        },
        "files": reports,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = [
            "path",
            "exists",
            "status",
            "type",
            "size_bytes",
            "rows",
            "missing_required_columns",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for item in reports:
            writer.writerow(
                {
                    "path": item.get("path"),
                    "exists": item.get("exists"),
                    "status": item.get("status"),
                    "type": item.get("type"),
                    "size_bytes": item.get("size_bytes"),
                    "rows": item.get("rows"),
                    "missing_required_columns": " | ".join(item.get("missing_required_columns", [])),
                }
            )

    md: list[str] = []
    md.append("# Scout Finance ? v1.9A Scale Readiness Audit")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Readiness status: **{readiness_status}**")
    md.append(f"- Readiness score: **{score}/100**")
    md.append(f"- Critical files checked: {len(reports)}")
    md.append("")
    md.append("## Controls")
    md.append("")
    md.append("- OpenAI called: false")
    md.append("- Broker called: false")
    md.append("- Market data recalculated: false")
    md.append("- Scoring recalculated: false")
    md.append("- Large universe launched: false")
    md.append("- Financial advice: false")
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
    md.append("## Critical files")
    md.append("")
    for item in reports:
        md.append(
            f"- `{item['path']}` ? {item['status']} ? "
            f"rows: {item.get('rows')} ? size: {item.get('size_bytes')}"
        )

    md.append("")
    md.append("## Recommendation")
    md.append("")
    if readiness_status == "READY_FOR_CONTROLLED_SCALE_TEST":
        md.append("Proceed to v1.9B with a controlled scale test, not full 59k universe yet.")
    elif readiness_status == "READY_WITH_WARNINGS":
        md.append("Proceed only with a limited scale test and monitor the listed warnings.")
    else:
        md.append("Do not proceed to v1.9B until blockers are resolved.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v1.9A Scale Readiness Audit")
    print("=" * 92)
    print(f"OK   Critical files checked: {len(reports)}")
    print(f"OK   Readiness status: {readiness_status}")
    print(f"OK   Readiness score: {score}/100")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Large universe launched: False")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
