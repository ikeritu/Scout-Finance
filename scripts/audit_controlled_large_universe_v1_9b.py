from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v1.9B"
METHOD = "controlled_large_universe_pipeline_audit_v1"

SCALE_ROOT = ROOT / "outputs" / "scale_tests"
OUT_DIR = ROOT / "outputs" / "large_universe"
OUT_JSON = OUT_DIR / "controlled_large_universe_audit_v1_9b.json"
OUT_MD = OUT_DIR / "controlled_large_universe_audit_v1_9b.md"
OUT_CSV = OUT_DIR / "controlled_large_universe_files_v1_9b.csv"

CONTROLLED_SIZES = [20, 50, 100]

EXPECTED_FILES = [
    "active_real_universe_top_candidates.csv",
    "local_score_v0_breakdown.csv",
    "local_score_v0_candidates.csv",
    "ranking_explainability_candidates.csv",
    "ranking_explainability_factors.csv",
]

REQUIRED_COLUMNS_BY_FILE = {
    "active_real_universe_top_candidates.csv": [
        "ticker",
    ],
    "local_score_v0_candidates.csv": [
        "ticker",
    ],
    "local_score_v0_breakdown.csv": [
        "ticker",
    ],
    "ranking_explainability_candidates.csv": [
        "ticker",
    ],
    "ranking_explainability_factors.csv": [
        "ticker",
    ],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_csv_header_and_count(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        return list(reader.fieldnames or []), len(rows)


def inspect_csv(path: Path, required_columns: list[str]) -> dict[str, object]:
    info: dict[str, object] = {
        "exists": path.exists(),
        "size_bytes": None,
        "rows": None,
        "columns": [],
        "missing_required_columns": [],
        "status": "MISSING",
    }

    if not path.exists():
        return info

    info["size_bytes"] = path.stat().st_size

    try:
        columns, rows = load_csv_header_and_count(path)
        info["rows"] = rows
        info["columns"] = columns
        missing = [col for col in required_columns if col not in columns]
        info["missing_required_columns"] = missing

        if rows == 0:
            info["status"] = "EMPTY_CSV"
        elif missing:
            info["status"] = "MISSING_COLUMNS"
        else:
            info["status"] = "OK"

    except Exception as exc:
        info["status"] = "CSV_ERROR"
        info["error"] = str(exc)

    return info


def inspect_size(size: int) -> dict[str, object]:
    size_dir = SCALE_ROOT / f"size_{size}"

    files: list[dict[str, object]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    for file_name in EXPECTED_FILES:
        path = size_dir / file_name
        required = REQUIRED_COLUMNS_BY_FILE.get(file_name, [])
        info = inspect_csv(path, required)
        info["size"] = size
        info["file_name"] = file_name
        info["path"] = str(path.relative_to(ROOT)).replace("\\", "/")
        files.append(info)

        status = str(info["status"])
        if status != "OK":
            blockers.append(f"size_{size}/{file_name}: {status}")

        rows = info.get("rows")
        if isinstance(rows, int) and rows > size * 5:
            warnings.append(f"size_{size}/{file_name}: unexpectedly high row count {rows}")

        size_bytes = info.get("size_bytes")
        if isinstance(size_bytes, int) and size_bytes > 10_000_000:
            warnings.append(f"size_{size}/{file_name}: large file {size_bytes} bytes")

    active_file = next(
        (item for item in files if item["file_name"] == "active_real_universe_top_candidates.csv"),
        None,
    )

    observed_active_rows = active_file.get("rows") if isinstance(active_file, dict) else None

    status = "OK"
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "OK_WITH_WARNINGS"

    return {
        "size": size,
        "path": str(size_dir.relative_to(ROOT)).replace("\\", "/"),
        "exists": size_dir.exists(),
        "status": status,
        "observed_active_rows": observed_active_rows,
        "files": files,
        "blockers": blockers,
        "warnings": warnings,
    }


def score_readiness(size_reports: list[dict[str, object]]) -> tuple[int, list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    for report in size_reports:
        size = report["size"]

        if not report.get("exists"):
            blockers.append(f"Missing scale test directory: size_{size}")

        blockers.extend(str(item) for item in report.get("blockers", []))
        warnings.extend(str(item) for item in report.get("warnings", []))

    score = 100
    score -= len(blockers) * 10
    score -= len(warnings) * 3
    score = max(0, min(100, score))

    return score, blockers, warnings


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    size_reports = [inspect_size(size) for size in CONTROLLED_SIZES]
    score, blockers, warnings = score_readiness(size_reports)

    if blockers:
        audit_status = "NOT_READY_FOR_LARGE_UNIVERSE"
    elif warnings:
        audit_status = "READY_WITH_WARNINGS_FOR_CONTROLLED_SCALE"
    else:
        audit_status = "READY_FOR_NEXT_CONTROLLED_SCALE_STEP"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "audit_status": audit_status,
        "readiness_score": score,
        "controlled_sizes": CONTROLLED_SIZES,
        "blockers": blockers,
        "warnings": warnings,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
        },
        "size_reports": size_reports,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    rows: list[dict[str, object]] = []
    for size_report in size_reports:
        for file_report in size_report["files"]:
            rows.append(
                {
                    "size": file_report.get("size"),
                    "file_name": file_report.get("file_name"),
                    "path": file_report.get("path"),
                    "status": file_report.get("status"),
                    "rows": file_report.get("rows"),
                    "size_bytes": file_report.get("size_bytes"),
                    "missing_required_columns": " | ".join(file_report.get("missing_required_columns", [])),
                }
            )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = [
            "size",
            "file_name",
            "path",
            "status",
            "rows",
            "size_bytes",
            "missing_required_columns",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md: list[str] = []
    md.append("# Scout Finance ? v1.9B Controlled Large Universe Pipeline Audit")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Audit status: **{audit_status}**")
    md.append(f"- Readiness score: **{score}/100**")
    md.append(f"- Controlled sizes: {', '.join(str(s) for s in CONTROLLED_SIZES)}")
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
    md.append("## Size reports")
    md.append("")

    for report in size_reports:
        md.append(f"### size_{report['size']}")
        md.append("")
        md.append(f"- Status: {report['status']}")
        md.append(f"- Observed active rows: {report.get('observed_active_rows')}")
        md.append("")
        for file_report in report["files"]:
            md.append(
                f"- `{file_report['file_name']}` ? {file_report['status']} ? "
                f"rows: {file_report.get('rows')} ? size: {file_report.get('size_bytes')}"
            )
        md.append("")

    md.append("## Recommendation")
    md.append("")
    if audit_status == "READY_FOR_NEXT_CONTROLLED_SCALE_STEP":
        md.append("Proceed to the next controlled scale step before attempting any full-universe run.")
    elif audit_status == "READY_WITH_WARNINGS_FOR_CONTROLLED_SCALE":
        md.append("Proceed cautiously and resolve warnings before increasing size.")
    else:
        md.append("Do not proceed to larger scale until blockers are resolved.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v1.9B Controlled Large Universe Pipeline Audit")
    print("=" * 92)
    print(f"OK   Controlled sizes checked: {CONTROLLED_SIZES}")
    print(f"OK   Audit status: {audit_status}")
    print(f"OK   Readiness score: {score}/100")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
