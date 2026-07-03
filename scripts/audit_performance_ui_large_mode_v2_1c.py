from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PHASE = "v2.1C"
METHOD = "performance_ui_large_mode_readiness_v1"

SCALE_ROOT = ROOT / "outputs" / "scale_tests"
APP_PATH = ROOT / "app.py"

OUT_DIR = ROOT / "outputs" / "large_universe_mode"
OUT_JSON = OUT_DIR / "performance_ui_large_mode_readiness_v2_1c.json"
OUT_MD = OUT_DIR / "performance_ui_large_mode_readiness_v2_1c.md"
OUT_CSV = OUT_DIR / "performance_ui_large_mode_files_v2_1c.csv"

CONTROLLED_SIZES = [250, 500, 1000]

EXPECTED_FILES = [
    "active_real_universe_top_candidates.csv",
    "local_score_v0_breakdown.csv",
    "local_score_v0_candidates.csv",
    "ranking_explainability_candidates.csv",
    "ranking_explainability_factors.csv",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return sum(1 for _ in reader)


def inspect_file(path: Path, size: int, file_name: str) -> dict[str, object]:
    if not path.exists():
        return {
            "size": size,
            "file_name": file_name,
            "path": rel(path),
            "exists": False,
            "rows": None,
            "size_bytes": None,
            "size_mb": None,
            "status": "MISSING",
            "risk": "BLOCKER",
        }

    try:
        rows = count_csv_rows(path)
        size_bytes = path.stat().st_size
        size_mb = round(size_bytes / 1024 / 1024, 3)

        if size_bytes > 25_000_000:
            risk = "HIGH"
            status = "LARGE_FILE"
        elif size_bytes > 10_000_000:
            risk = "MEDIUM"
            status = "MEDIUM_FILE"
        else:
            risk = "LOW"
            status = "OK"

        return {
            "size": size,
            "file_name": file_name,
            "path": rel(path),
            "exists": True,
            "rows": rows,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "status": status,
            "risk": risk,
        }

    except Exception as exc:
        return {
            "size": size,
            "file_name": file_name,
            "path": rel(path),
            "exists": True,
            "rows": None,
            "size_bytes": path.stat().st_size,
            "size_mb": round(path.stat().st_size / 1024 / 1024, 3),
            "status": "CSV_ERROR",
            "risk": "BLOCKER",
            "error": str(exc),
        }


def inspect_app() -> dict[str, object]:
    if not APP_PATH.exists():
        return {
            "exists": False,
            "status": "MISSING_APP",
            "has_streamlit_cache": False,
            "cache_hits": 0,
            "has_expanders": False,
            "expander_hits": 0,
            "has_pagination_terms": False,
            "pagination_hits": 0,
            "has_top_n_terms": False,
            "top_n_hits": 0,
            "has_dataframe_rendering": False,
            "dataframe_hits": 0,
            "risk": "BLOCKER",
        }

    text = APP_PATH.read_text(encoding="utf-8", errors="replace")

    cache_hits = len(re.findall(r"@st\.cache_data|st\.cache_data", text))
    expander_hits = len(re.findall(r"st\.expander", text))
    pagination_hits = len(re.findall(r"pagination|page_size|page_number|offset|limit", text, flags=re.IGNORECASE))
    top_n_hits = len(re.findall(r"top_n|head\(|nlargest|limit", text, flags=re.IGNORECASE))
    dataframe_hits = len(re.findall(r"st\.dataframe|st\.table|st\.data_editor", text))

    has_cache = cache_hits > 0
    has_row_limiting = pagination_hits > 0 or top_n_hits > 0

    warnings: list[str] = []

    if not has_cache:
        warnings.append("app.py does not show Streamlit cache markers.")
    if not has_row_limiting:
        warnings.append("app.py does not show clear pagination or row limiting markers.")
    if dataframe_hits > 0 and not has_row_limiting:
        warnings.append("Dataframe rendering exists without clear row limiting.")

    if warnings:
        status = "UI_READY_WITH_WARNINGS"
        risk = "MEDIUM"
    else:
        status = "UI_READY_FOR_CONTROLLED_LARGE_MODE"
        risk = "LOW"

    return {
        "exists": True,
        "status": status,
        "has_streamlit_cache": has_cache,
        "cache_hits": cache_hits,
        "has_expanders": expander_hits > 0,
        "expander_hits": expander_hits,
        "has_pagination_terms": pagination_hits > 0,
        "pagination_hits": pagination_hits,
        "has_top_n_terms": top_n_hits > 0,
        "top_n_hits": top_n_hits,
        "has_dataframe_rendering": dataframe_hits > 0,
        "dataframe_hits": dataframe_hits,
        "warnings": warnings,
        "risk": risk,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    file_reports: list[dict[str, object]] = []

    for size in CONTROLLED_SIZES:
        for file_name in EXPECTED_FILES:
            path = SCALE_ROOT / f"size_{size}" / file_name
            file_reports.append(inspect_file(path, size, file_name))

    app_report = inspect_app()

    blockers: list[str] = []
    warnings: list[str] = []

    for item in file_reports:
        if item["status"] in {"MISSING", "CSV_ERROR"}:
            blockers.append(f"{item['path']}: {item['status']}")
        elif item["risk"] == "HIGH":
            warnings.append(f"{item['path']}: high file-size risk")
        elif item["risk"] == "MEDIUM":
            warnings.append(f"{item['path']}: medium file-size risk")

    for item in app_report.get("warnings", []):
        warnings.append(str(item))

    total_size_bytes = sum(int(item["size_bytes"] or 0) for item in file_reports)
    total_size_mb = round(total_size_bytes / 1024 / 1024, 3)

    max_file = max(file_reports, key=lambda x: int(x["size_bytes"] or 0), default=None)

    if blockers:
        readiness_status = "PERFORMANCE_UI_READINESS_BLOCKED"
        readiness_score = 0
    else:
        readiness_score = 100
        readiness_score -= len(warnings) * 5
        readiness_score = max(60, readiness_score)

        if warnings:
            readiness_status = "READY_WITH_WARNINGS_FOR_LARGE_MODE_UI"
        else:
            readiness_status = "READY_FOR_LARGE_MODE_UI_REVIEW"

    payload = {
        "phase": PHASE,
        "method": METHOD,
        "created_at": now_iso(),
        "readiness_status": readiness_status,
        "readiness_score": readiness_score,
        "controlled_sizes": CONTROLLED_SIZES,
        "total_size_bytes": total_size_bytes,
        "total_size_mb": total_size_mb,
        "max_file": max_file,
        "blockers": blockers,
        "warnings": warnings,
        "app_report": app_report,
        "file_reports": file_reports,
        "controls": {
            "openai_called": False,
            "broker_called": False,
            "market_data_recalculated": False,
            "scoring_recalculated": False,
            "full_59000_universe_launched": False,
            "financial_advice": False,
        },
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = [
            "size",
            "file_name",
            "path",
            "exists",
            "rows",
            "size_bytes",
            "size_mb",
            "status",
            "risk",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(file_reports)

    md: list[str] = []
    md.append("# Scout Finance ? v2.1C Performance & UI Large Mode Readiness")
    md.append("")
    md.append(f"- Phase: {PHASE}")
    md.append(f"- Method: {METHOD}")
    md.append(f"- Created at: {payload['created_at']}")
    md.append(f"- Readiness status: **{readiness_status}**")
    md.append(f"- Readiness score: **{readiness_score}/100**")
    md.append(f"- Controlled sizes: {', '.join(str(s) for s in CONTROLLED_SIZES)}")
    md.append(f"- Total controlled output size: {total_size_mb} MB")
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
    md.append("## App.py readiness")
    md.append("")
    md.append(f"- Status: {app_report.get('status')}")
    md.append(f"- Streamlit cache markers: {app_report.get('cache_hits')}")
    md.append(f"- Expander markers: {app_report.get('expander_hits')}")
    md.append(f"- Pagination/limit markers: {app_report.get('pagination_hits')}")
    md.append(f"- top_n/head/limit markers: {app_report.get('top_n_hits')}")
    md.append(f"- Dataframe render markers: {app_report.get('dataframe_hits')}")
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
    md.append("## File reports")
    md.append("")
    for item in file_reports:
        md.append(
            f"- size_{item['size']}/`{item['file_name']}` ? "
            f"{item['status']} ? rows: {item['rows']} ? "
            f"{item['size_mb']} MB ? risk: {item['risk']}"
        )
    md.append("")
    md.append("## Recommendation")
    md.append("")
    if readiness_status == "READY_FOR_LARGE_MODE_UI_REVIEW":
        md.append("Proceed to a 59k decision gate. Do not launch 59k yet.")
    elif readiness_status == "READY_WITH_WARNINGS_FOR_LARGE_MODE_UI":
        md.append("Review UI/performance warnings before the 59k decision gate.")
    else:
        md.append("Fix blockers before continuing.")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("Scout Finance ? v2.1C Performance & UI Large Mode Readiness")
    print("=" * 92)
    print(f"OK   Readiness status: {readiness_status}")
    print(f"OK   Readiness score: {readiness_score}/100")
    print(f"OK   Total controlled output size: {total_size_mb} MB")
    print(f"OK   Blockers: {len(blockers)}")
    print(f"OK   Warnings: {len(warnings)}")
    print(f"OK   CSV written: {OUT_CSV}")
    print(f"OK   JSON written: {OUT_JSON}")
    print(f"OK   Report written: {OUT_MD}")
    print("OK   OpenAI called: False")
    print("OK   Broker called: False")
    print("OK   Scoring recalculated: False")
    print("OK   Full 59k universe launched: False")

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
