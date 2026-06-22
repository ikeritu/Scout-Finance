from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


PHASE = "8I"
MAX_TOP_N = 3


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

    print("Scout Finance — Phase 8I Optional AI Execution Sandbox checker")
    print("=" * 92)

    required_files = [
        out / "phase8i_optional_ai_execution_sandbox_summary.json",
        out / "phase8i_optional_ai_execution_sandbox_report.md",
        out / "phase8i_ai_execution_sandbox_decision.json",
        out / "phase8i_ai_execution_sandbox_results.json",
        out / "phase8i_ai_execution_sandbox_index.csv",
        out / "phase8i_ai_execution_sandbox_audit.json",
        root / "src" / "phase8i_optional_ai_execution_sandbox.py",
    ]

    for path in required_files:
        require_file(path)

    summary = read_json(out / "phase8i_optional_ai_execution_sandbox_summary.json")
    decision = read_json(out / "phase8i_ai_execution_sandbox_decision.json")
    results = read_json(out / "phase8i_ai_execution_sandbox_results.json")
    audit = read_json(out / "phase8i_ai_execution_sandbox_audit.json")

    require(summary.get("phase") == PHASE, "Summary phase is 8I")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("default_top_n") == 3, "Default TOP N OK: 3")
    require(summary.get("max_top_n") == MAX_TOP_N, "MAX TOP N OK: 3")

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

    require(isinstance(decision, dict), "Decision is a dict")
    for field in ["phase", "gate_status", "ai_allowed", "reason", "hard_blockers", "settings"]:
        require(field in decision, f"Decision field OK: {field}")

    require(isinstance(results, list), "Sandbox results is a list")
    require(len(results) <= MAX_TOP_N, f"Sandbox results count <= 3: {len(results)}")
    require(len(results) >= 1, f"Sandbox results count >= 1: {len(results)}")
    require(summary.get("sandbox_executions_created") == len(results), "Summary execution count matches results")

    sandbox_dir = out / "research_memo_ai_execution_sandbox"
    require(sandbox_dir.exists(), f"Sandbox directory exists: {sandbox_dir}")

    required_result_fields = [
        "phase",
        "prompt_version",
        "schema_version",
        "ticker",
        "company_name",
        "ranking_position",
        "quant_score",
        "memo_status",
        "ai_gate_status",
        "ai_allowed",
        "execution_status",
        "skip_reason",
        "prompt_payload",
        "prompt_sha256",
        "simulated_response",
        "estimated_cost",
        "model_used",
        "openai_called",
        "api_called",
        "yfinance_called",
        "execution_json_path",
        "execution_md_path",
    ]

    for item in results:
        ticker = item.get("ticker", "UNKNOWN")
        for field in required_result_fields:
            require(field in item, f"Sandbox field OK: {ticker}::{field}")

        require(item.get("phase") == PHASE, f"Sandbox phase OK: {ticker}")
        require(item.get("estimated_cost") == 0.0, f"Sandbox cost OK: {ticker}")
        require(item.get("model_used") is None, f"Sandbox model_used OK: {ticker}")
        require(item.get("openai_called") is False, f"Sandbox openai_called OK: {ticker}")
        require(item.get("api_called") is False, f"Sandbox api_called OK: {ticker}")
        require(item.get("yfinance_called") is False, f"Sandbox yfinance_called OK: {ticker}")
        require(isinstance(item.get("prompt_payload"), dict), f"Prompt payload is dict: {ticker}")
        require(isinstance(item.get("simulated_response"), dict), f"Simulated response is dict: {ticker}")
        require(item.get("simulated_response", {}).get("data_policy", {}).get("no_inventar_datos") is True, f"No inventar datos policy OK: {ticker}")

        json_path = Path(item["execution_json_path"])
        md_path = Path(item["execution_md_path"])
        require(json_path.exists(), f"Execution JSON exists: {ticker}")
        require(md_path.exists(), f"Execution Markdown exists: {ticker}")

        md = md_path.read_text(encoding="utf-8")
        for text in [
            "AI Execution Sandbox",
            "OpenAI called: False",
            "No inventar datos",
            "data_insufficient",
            "Objective data",
            "AI interpretation",
        ]:
            require(text in md, f"Execution Markdown contains {text}: {ticker}")

    with (out / "phase8i_ai_execution_sandbox_index.csv").open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == len(results), "Index CSV row count matches results")

    require(audit.get("phase") == PHASE, "Audit phase OK")
    require(audit.get("status") == "OK", "Audit status OK")
    require(audit.get("executions_count") == len(results), "Audit execution count matches results")

    for entry in audit.get("executions", []):
        ticker = entry.get("ticker", "UNKNOWN")
        require(Path(entry["json_path"]).exists(), f"Audit JSON exists: {ticker}")
        require(bool(entry.get("json_sha256")), f"Audit JSON sha256 present: {ticker}")
        require(Path(entry["markdown_path"]).exists(), f"Audit Markdown exists: {ticker}")
        require(bool(entry.get("markdown_sha256")), f"Audit Markdown sha256 present: {ticker}")
        require(entry.get("openai_called") is False, f"Audit openai_called OK: {ticker}")
        require(entry.get("estimated_cost") == 0.0, f"Audit cost OK: {ticker}")

    report = (out / "phase8i_optional_ai_execution_sandbox_report.md").read_text(encoding="utf-8")
    for text in [
        "Phase 8I",
        "Sandbox executions created",
        "OpenAI called: False",
        "No inventar datos",
        "data_insufficient",
        "Objective data",
        "AI interpretation",
        "8J",
    ]:
        require(text in report, f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 8I Optional AI Execution Sandbox is valid")


if __name__ == "__main__":
    main()
