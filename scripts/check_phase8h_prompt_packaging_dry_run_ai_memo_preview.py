from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "scouting"
PROMPT_DIR = OUTPUT_DIR / "research_memo_ai_prompts"

PHASE = "8H"
MAX_TOP_N = 3


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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    print("Scout Finance — Phase 8H Prompt Packaging and Dry-run AI Memo Preview checker")
    print("=" * 92)

    required_files = [
        OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_summary.json",
        OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_report.md",
        OUTPUT_DIR / "phase8h_ai_prompt_packages.json",
        OUTPUT_DIR / "phase8h_ai_prompt_packages_index.csv",
        OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_audit.json",
        PROJECT_ROOT / "src" / "phase8h_prompt_packaging_dry_run_ai_memo_preview.py",
    ]

    for path in required_files:
        require(path.exists(), f"File exists: {path}")

    summary: Dict[str, Any] = read_json(OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_summary.json")
    packages: List[Dict[str, Any]] = read_json(OUTPUT_DIR / "phase8h_ai_prompt_packages.json")
    audit: Dict[str, Any] = read_json(OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_audit.json")

    require(summary.get("phase") == PHASE, "Summary phase is 8H")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("default_top_n") == 3, "Default TOP N OK: 3")
    require(summary.get("max_top_n") == MAX_TOP_N, "MAX TOP N OK: 3")
    require(summary.get("prompt_packages_created") == len(packages), "Summary package count matches export")
    require(len(packages) <= MAX_TOP_N, f"Prompt package count <= 3: {len(packages)}")
    require(len(packages) >= 1, f"Prompt package count >= 1: {len(packages)}")
    require(PROMPT_DIR.exists(), f"Prompt directory exists: {PROMPT_DIR}")

    for flag in [
        "openai_called",
        "api_called",
        "yfinance_called",
        "pipeline_recalculated",
        "app_modified",
        "filters_modified",
        "release_modified",
    ]:
        require(summary.get(flag) is False, f"Control OK: {flag}=False")

    for pkg in packages:
        ticker = pkg.get("ticker", "UNKNOWN")
        for field in [
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
            "system_prompt",
            "user_prompt",
            "dry_run_preview",
            "prompt_sha256",
            "estimated_cost",
            "model_used",
            "openai_called",
            "prompt_package_json_path",
            "prompt_package_md_path",
        ]:
            require(field in pkg, f"Prompt package field OK: {ticker}::{field}")

        require(pkg.get("phase") == PHASE, f"Package phase OK: {ticker}")
        require(pkg.get("openai_called") is False, f"Package openai_called OK: {ticker}")
        require(float(pkg.get("estimated_cost", -1)) == 0.0, f"Package cost OK: {ticker}")
        require(pkg.get("model_used") is None, f"Package model_used OK: {ticker}")
        require(isinstance(pkg.get("user_prompt"), dict), f"User prompt is dict: {ticker}")
        require(isinstance(pkg.get("dry_run_preview"), dict), f"Dry-run preview is dict: {ticker}")
        require(pkg["dry_run_preview"].get("openai_called") is False, f"Dry-run openai_called OK: {ticker}")

        json_path = Path(pkg.get("prompt_package_json_path", ""))
        md_path = Path(pkg.get("prompt_package_md_path", ""))
        require(json_path.exists(), f"Prompt JSON exists: {ticker}")
        require(md_path.exists(), f"Prompt Markdown exists: {ticker}")
        md = md_path.read_text(encoding="utf-8")
        for needle in [
            "AI Research Memo Prompt Package",
            "Dry-run preview",
            "OpenAI called: False",
            "No inventar datos",
            "data_insufficient",
        ]:
            require(needle in md, f"Prompt Markdown contains {needle}: {ticker}")

    with (OUTPUT_DIR / "phase8h_ai_prompt_packages_index.csv").open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    require(len(rows) == len(packages), "Index CSV row count matches packages")

    require(audit.get("phase") == PHASE, "Audit phase OK")
    require(audit.get("status") == "OK", "Audit status OK")
    require(audit.get("packages_created") == len(packages), "Audit package count matches export")
    for report in audit.get("reports", []):
        ticker = report.get("ticker", "UNKNOWN")
        require(report.get("json_exists") is True, f"Audit JSON exists: {ticker}")
        require(bool(report.get("json_sha256")), f"Audit JSON sha256 present: {ticker}")
        require(report.get("md_exists") is True, f"Audit Markdown exists: {ticker}")
        require(bool(report.get("md_sha256")), f"Audit Markdown sha256 present: {ticker}")
        require(report.get("openai_called") is False, f"Audit openai_called OK: {ticker}")
        require(float(report.get("estimated_cost", -1)) == 0.0, f"Audit cost OK: {ticker}")

    report_text = (OUTPUT_DIR / "phase8h_prompt_packaging_dry_run_report.md").read_text(encoding="utf-8")
    for needle in [
        "Phase 8H",
        "Prompt packages created",
        "OpenAI called: False",
        "No inventar datos",
        "data_insufficient",
        "Objective data",
        "AI interpretation",
        "8I",
    ]:
        require(needle in report_text, f"Report contains: {needle}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 8H Prompt Packaging and Dry-run AI Memo Preview is valid")


if __name__ == "__main__":
    main()
