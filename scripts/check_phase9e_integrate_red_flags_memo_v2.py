from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PHASE = "9E"
ALLOWED_VERDICTS = {"WATCHLIST", "REJECT", "NEEDS_MORE_DATA"}


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
    memo_dir = out / "research_memos_v2_red_flags"

    print("Scout Finance — Phase 9E Memo v2 Red Flags Integration checker")
    print("=" * 92)

    required = [
        root / "src" / "phase9e_integrate_red_flags_memo_v2.py",
        root / "scripts" / "check_phase9e_integrate_red_flags_memo_v2.py",
        out / "phase9e_memo_v2_red_flags_summary.json",
        out / "phase9e_memo_v2_red_flags_report.md",
        out / "phase9e_memo_v2_red_flags_audit.json",
        out / "phase9e_memo_v2_red_flags_export.json",
        out / "phase9e_memo_v2_red_flags_index.csv",
        out / "phase9c_research_memo_v2_contract_export.json",
        out / "phase9d_red_flags_detector_export.json",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "phase9e_memo_v2_red_flags_summary.json")
    audit = read_json(out / "phase9e_memo_v2_red_flags_audit.json")
    export = read_json(out / "phase9e_memo_v2_red_flags_export.json")

    require(summary.get("phase") == PHASE, "Summary phase is 9E")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("default_top_n") == 3, "Default TOP N OK")
    require(summary.get("max_top_n") == 3, "MAX TOP N OK")
    require(summary.get("memos_loaded", 0) > 0, "Memos loaded > 0")
    require(summary.get("red_flag_records_loaded", 0) > 0, "Red flag records loaded > 0")
    require(summary.get("memos_exported") == summary.get("memos_loaded"), "Exported count matches loaded")
    require(summary.get("manual_review_required_all") is True, "Manual review required for all")
    require(summary.get("not_financial_advice_all") is True, "Not financial advice for all")
    require(set(summary.get("allowed_verdicts", [])) == ALLOWED_VERDICTS, "Allowed verdicts OK")
    require(summary.get("total_red_flags", 0) >= 0, "Total red flags present")
    require(memo_dir.exists(), "Memo red flags dir exists")

    for key in [
        "openai_called",
        "api_called",
        "yfinance_called",
        "pipeline_recalculated",
        "app_modified",
        "filters_modified",
        "release_modified",
    ]:
        require(summary.get(key) is False, f"Control OK: {key}=False")

    require(audit.get("phase") == PHASE, "Audit phase OK")
    require(isinstance(export, list), "Export is list")
    require(len(export) == summary.get("memos_exported"), "Export count matches summary")

    total_flags = 0
    high_critical = 0
    for memo in export:
        ticker = memo.get("ticker")
        for field in [
            "schema_version",
            "ticker",
            "normalized_verdict",
            "manual_review_required",
            "not_financial_advice",
            "red_flags",
            "verdict_policy",
            "metadata",
        ]:
            require(field in memo, f"{ticker}: field present: {field}")

        require(memo.get("normalized_verdict") in ALLOWED_VERDICTS, f"{ticker}: final verdict OK")
        require(memo.get("manual_review_required") is True, f"{ticker}: manual review required")
        require(memo.get("not_financial_advice") is True, f"{ticker}: not financial advice")

        red = memo.get("red_flags", {})
        require(isinstance(red.get("summary"), dict), f"{ticker}: red summary dict")
        require(isinstance(red.get("items"), list), f"{ticker}: red items list")
        require(red.get("source") == "phase9d_red_flags_detector_export.json", f"{ticker}: red source OK")

        total_flags += int(red.get("summary", {}).get("red_flag_count") or 0)
        if red.get("summary", {}).get("has_high_or_critical"):
            high_critical += 1
            require(memo.get("normalized_verdict") == "NEEDS_MORE_DATA", f"{ticker}: high/critical keeps NEEDS_MORE_DATA")

        policy = memo.get("verdict_policy", {})
        require(policy.get("final_normalized_verdict") == memo.get("normalized_verdict"), f"{ticker}: verdict policy matches final")
        require(set(policy.get("allowed_verdicts", [])) == ALLOWED_VERDICTS, f"{ticker}: policy allowed verdicts OK")

        meta = memo.get("metadata", {})
        require(meta.get("red_flags_integrated") is True, f"{ticker}: red flags integrated metadata")
        require(meta.get("openai_called") is False, f"{ticker}: metadata openai_called False")
        require(meta.get("api_called") is False, f"{ticker}: metadata api_called False")
        require(meta.get("yfinance_called") is False, f"{ticker}: metadata yfinance_called False")
        require(meta.get("pipeline_recalculated") is False, f"{ticker}: metadata pipeline_recalculated False")
        require(meta.get("estimated_cost") == 0.0, f"{ticker}: estimated cost zero")
        require(meta.get("model_used") is None, f"{ticker}: model used None")
        require("memo_with_red_flags_sha256" in meta, f"{ticker}: red flags memo sha present")

    require(total_flags == summary.get("total_red_flags"), "Total red flags matches summary")
    require(high_critical == summary.get("records_with_high_or_critical"), "High/critical count matches summary")

    with (out / "phase9e_memo_v2_red_flags_index.csv").open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == len(export), "Index row count matches export")
    for row in rows:
        require(row.get("final_verdict") in ALLOWED_VERDICTS, f"{row.get('ticker')}: index final verdict OK")
        require(row.get("manual_review_required") == "True", f"{row.get('ticker')}: index manual review required")
        require(row.get("not_financial_advice") == "True", f"{row.get('ticker')}: index not financial advice")

    md_files = list(memo_dir.glob("*.md"))
    json_files = list(memo_dir.glob("*.json"))
    require(len(md_files) >= len(export), "Per-ticker Markdown files created")
    require(len(json_files) >= len(export), "Per-ticker JSON files created")

    report = (out / "phase9e_memo_v2_red_flags_report.md").read_text(encoding="utf-8")
    for text in [
        "Phase 9E",
        "Integrate Red Flags",
        "OpenAI called: False",
        "yfinance called: False",
        "Pipeline recalculated: False",
        "NEEDS_MORE_DATA",
        "Phase 9F",
    ]:
        require(text in report, f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 9E Memo v2 Red Flags Integration is valid")


if __name__ == "__main__":
    main()
