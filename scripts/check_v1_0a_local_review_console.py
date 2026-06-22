from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PHASE = "v1.0A"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if condition:
        ok(message)
    else:
        fail(message)


def require_file(path: Path) -> None:
    require(path.exists(), f"File exists: {path}")


def main() -> None:
    root = project_root()
    out = root / "outputs" / "scouting"
    review = out / "manual_review"

    print("Scout Finance — v1.0A Local Review Console checker")
    print("=" * 92)

    required = [
        root / "src" / "v1_0a_local_review_console.py",
        root / "scripts" / "check_v1_0a_local_review_console.py",
        out / "phase9e_memo_v2_red_flags_export.json",
        out / "v1_0a_local_review_console_summary.json",
        out / "v1_0a_local_review_console_report.md",
        review / "manual_review_state.json",
        review / "local_review_console.md",
        review / "manual_review_notes.md",
        review / "local_review_console_index.csv",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "v1_0a_local_review_console_summary.json")
    state = read_json(review / "manual_review_state.json")

    require(summary.get("phase") == PHASE, "Summary phase OK")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("candidates_loaded", 0) > 0, "Candidates loaded > 0")
    require(summary.get("review_records") == summary.get("candidates_loaded"), "Review records match candidates")
    require(state.get("phase") == PHASE, "State phase OK")
    require(isinstance(state.get("records"), dict), "State records dict")

    allowed = set(summary.get("manual_status_allowed_values", []))
    require(allowed == {"pending_review", "reviewed_watchlist", "reviewed_reject", "needs_more_data"}, "Manual statuses OK")

    for ticker, record in state.get("records", {}).items():
        require(record.get("manual_status") in allowed, f"{ticker}: manual status allowed")
        require(record.get("manual_review_required") is True, f"{ticker}: manual review required")
        require(record.get("not_financial_advice") is True, f"{ticker}: not financial advice")

    for key in [
        "openai_called", "api_called", "yfinance_called", "pipeline_recalculated",
        "app_modified", "filters_modified", "release_modified",
    ]:
        require(summary.get(key) is False, f"Control OK: {key}=False")
        require(state.get(key) is False, f"State control OK: {key}=False")

    with (review / "local_review_console_index.csv").open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == summary.get("candidates_loaded"), "Index row count matches candidates")

    console = (review / "local_review_console.md").read_text(encoding="utf-8")
    for text in ["Local Review Console", "OpenAI called", "Manual review required", "pending_review"]:
        require(text in console, f"Console contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.0A Local Review Console is valid")


if __name__ == "__main__":
    main()
