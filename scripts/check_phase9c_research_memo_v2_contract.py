from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PHASE = "9C"
SCHEMA_VERSION = "equity_research_memo_schema_v0_2"
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
    memo_dir = out / "research_memos_v2"

    print("Scout Finance — Phase 9C Research Memo v2 Contract checker")
    print("=" * 92)

    required = [
        root / "src" / "phase9c_research_memo_v2_contract.py",
        root / "scripts" / "check_phase9c_research_memo_v2_contract.py",
        root / "schemas" / "equity_research_memo_schema_v0_2.json",
        out / "phase9c_research_memo_v2_contract_summary.json",
        out / "phase9c_research_memo_v2_contract_report.md",
        out / "phase9c_research_memo_v2_contract_audit.json",
        out / "phase9c_research_memo_v2_contract_export.json",
        out / "phase9c_research_memo_v2_contract_index.csv",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "phase9c_research_memo_v2_contract_summary.json")
    audit = read_json(out / "phase9c_research_memo_v2_contract_audit.json")
    export = read_json(out / "phase9c_research_memo_v2_contract_export.json")
    schema = read_json(root / "schemas" / "equity_research_memo_schema_v0_2.json")

    require(summary.get("phase") == PHASE, "Summary phase is 9C")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("schema_version") == SCHEMA_VERSION, "Schema version OK")
    require(summary.get("default_top_n") == 3, "Default TOP N OK")
    require(summary.get("max_top_n") == 3, "MAX TOP N OK")
    require(summary.get("memos_loaded", 0) > 0, "Memos loaded > 0")
    require(summary.get("memos_exported_v2") == summary.get("memos_loaded"), "Exported count matches loaded")
    require(summary.get("manual_review_required_all") is True, "Manual review required for all")
    require(summary.get("not_financial_advice_all") is True, "Not financial advice for all")
    require(set(summary.get("allowed_verdicts", [])) == ALLOWED_VERDICTS, "Allowed verdicts OK")

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
    require(len(export) == summary.get("memos_exported_v2"), "Export memo count matches summary")
    require(memo_dir.exists(), "Memo v2 dir exists")

    required_memo_fields = [
        "schema_version",
        "ticker",
        "company_name",
        "ranking_position",
        "quant_score",
        "memo_status",
        "normalized_verdict",
        "manual_review_required",
        "not_financial_advice",
        "objective_data",
        "deterministic_analysis",
        "ai_interpretation",
        "data_gaps",
        "sources",
        "metadata",
    ]

    for memo in export:
        ticker = memo.get("ticker")
        for field in required_memo_fields:
            require(field in memo, f"{ticker}: field present: {field}")
        require(memo.get("schema_version") == SCHEMA_VERSION, f"{ticker}: schema version OK")
        require(memo.get("normalized_verdict") in ALLOWED_VERDICTS, f"{ticker}: normalized verdict OK")
        require(memo.get("manual_review_required") is True, f"{ticker}: manual review required")
        require(memo.get("not_financial_advice") is True, f"{ticker}: not financial advice")
        require(isinstance(memo.get("objective_data"), dict), f"{ticker}: objective_data dict")
        require(isinstance(memo.get("deterministic_analysis"), dict), f"{ticker}: deterministic_analysis dict")
        require(isinstance(memo.get("ai_interpretation"), dict), f"{ticker}: ai_interpretation dict")
        require(isinstance(memo.get("data_gaps"), list), f"{ticker}: data_gaps list")
        require(isinstance(memo.get("sources"), list), f"{ticker}: sources list")
        meta = memo.get("metadata", {})
        require(meta.get("openai_called") is False, f"{ticker}: metadata openai_called False")
        require(meta.get("api_called") is False, f"{ticker}: metadata api_called False")
        require(meta.get("yfinance_called") is False, f"{ticker}: metadata yfinance_called False")
        require(meta.get("pipeline_recalculated") is False, f"{ticker}: metadata pipeline_recalculated False")
        require(meta.get("estimated_cost") == 0.0, f"{ticker}: estimated cost zero")
        require(meta.get("model_used") is None, f"{ticker}: model used None")
        require("memo_sha256" in meta, f"{ticker}: memo sha present")

    with (out / "phase9c_research_memo_v2_contract_index.csv").open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == len(export), "Index row count matches export")
    for row in rows:
        require(row.get("normalized_verdict") in ALLOWED_VERDICTS, f"{row.get('ticker')}: index verdict OK")
        require(row.get("manual_review_required") == "True", f"{row.get('ticker')}: index manual review required")
        require(row.get("not_financial_advice") == "True", f"{row.get('ticker')}: index not financial advice")

    require(schema.get("title") == "Scout Finance Equity Research Memo v0.2", "Schema title OK")
    require("manual_review_required" in schema.get("required", []), "Schema requires manual_review_required")
    require("not_financial_advice" in schema.get("required", []), "Schema requires not_financial_advice")
    verdict_enum = schema.get("properties", {}).get("normalized_verdict", {}).get("enum", [])
    require(set(verdict_enum) == ALLOWED_VERDICTS, "Schema verdict enum OK")

    report = (out / "phase9c_research_memo_v2_contract_report.md").read_text(encoding="utf-8")
    for text in [
        "Phase 9C",
        "manual_review_required = true",
        "not_financial_advice = true",
        "WATCHLIST",
        "REJECT",
        "NEEDS_MORE_DATA",
        "OpenAI called: False",
        "yfinance called: False",
        "Pipeline recalculated: False",
        "Phase 9D",
    ]:
        require(text in report, f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 9C Research Memo v2 Contract is valid")


if __name__ == "__main__":
    main()
