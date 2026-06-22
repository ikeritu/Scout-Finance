from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PHASE = "9F"
EXPECTED_PROFILES = {"value_analyst", "quality_analyst", "risk_analyst", "skeptic_analyst"}


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
    prompt_dir = out / "ai_profiles_dry_run"

    print("Scout Finance — Phase 9F AI Profiles Dry-run checker")
    print("=" * 92)

    required = [
        root / "src" / "phase9f_ai_profiles_dry_run.py",
        root / "scripts" / "check_phase9f_ai_profiles_dry_run.py",
        out / "phase9f_ai_profiles_dry_run_summary.json",
        out / "phase9f_ai_profiles_dry_run_report.md",
        out / "phase9f_ai_profiles_dry_run_audit.json",
        out / "phase9f_ai_profiles_dry_run_export.json",
        out / "phase9f_ai_profiles_dry_run_index.csv",
        out / "phase9e_memo_v2_red_flags_export.json",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "phase9f_ai_profiles_dry_run_summary.json")
    audit = read_json(out / "phase9f_ai_profiles_dry_run_audit.json")
    export = read_json(out / "phase9f_ai_profiles_dry_run_export.json")

    require(summary.get("phase") == PHASE, "Summary phase is 9F")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("default_top_n") == 3, "Default TOP N OK")
    require(summary.get("max_top_n") == 3, "MAX TOP N OK")
    require(summary.get("memos_loaded", 0) > 0, "Memos loaded > 0")
    require(summary.get("profile_count") == 4, "Profile count is 4")
    require(set(summary.get("profiles", [])) == EXPECTED_PROFILES, "Expected profiles OK")
    require(summary.get("prompt_packages_created") == summary.get("expected_prompt_packages"), "Prompt package count OK")
    require(summary.get("dry_run_only_all") is True, "Dry-run only for all")
    require(summary.get("execution_allowed_any") is False, "No execution allowed")
    require(summary.get("estimated_cost") == 0.0, "Estimated cost zero")
    require(summary.get("model_used") is None, "Model used None")
    require(prompt_dir.exists(), "Prompt dir exists")

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
    require(len(export) == summary.get("prompt_packages_created"), "Export count matches summary")

    seen_profiles = set()
    tickers = set()
    for package in export:
        ticker = package.get("ticker")
        profile_id = package.get("profile_id")
        seen_profiles.add(profile_id)
        tickers.add(ticker)

        require(profile_id in EXPECTED_PROFILES, f"{ticker}/{profile_id}: profile OK")
        require(package.get("dry_run_only") is True, f"{ticker}/{profile_id}: dry_run_only True")
        require(package.get("execution_allowed") is False, f"{ticker}/{profile_id}: execution_allowed False")
        require("system_prompt" in package, f"{ticker}/{profile_id}: system prompt present")
        require("user_prompt_json" in package, f"{ticker}/{profile_id}: user prompt JSON present")
        require("prompt_package_sha256" in package, f"{ticker}/{profile_id}: sha present")

        user_prompt = package.get("user_prompt_json", {})
        contract = user_prompt.get("required_output_contract", {})
        require(contract.get("not_financial_advice") is True, f"{ticker}/{profile_id}: output contract not financial advice")
        require(contract.get("manual_review_required") is True, f"{ticker}/{profile_id}: output contract manual review")
        require("memo_context" in user_prompt, f"{ticker}/{profile_id}: memo context present")

        safety = package.get("safety", {})
        require(safety.get("openai_called") is False, f"{ticker}/{profile_id}: openai_called False")
        require(safety.get("api_called") is False, f"{ticker}/{profile_id}: api_called False")
        require(safety.get("yfinance_called") is False, f"{ticker}/{profile_id}: yfinance_called False")
        require(safety.get("pipeline_recalculated") is False, f"{ticker}/{profile_id}: pipeline_recalculated False")
        require(safety.get("estimated_cost") == 0.0, f"{ticker}/{profile_id}: estimated cost zero")
        require(safety.get("model_used") is None, f"{ticker}/{profile_id}: model used None")

    require(seen_profiles == EXPECTED_PROFILES, "All expected profiles present")

    with (out / "phase9f_ai_profiles_dry_run_index.csv").open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == len(export), "Index row count matches export")
    for row in rows:
        require(row.get("profile_id") in EXPECTED_PROFILES, f"{row.get('ticker')}/{row.get('profile_id')}: index profile OK")
        require(row.get("dry_run_only") == "True", f"{row.get('ticker')}/{row.get('profile_id')}: index dry run")
        require(row.get("execution_allowed") == "False", f"{row.get('ticker')}/{row.get('profile_id')}: index execution disabled")
        require(row.get("openai_called") == "False", f"{row.get('ticker')}/{row.get('profile_id')}: index openai false")

    md_files = list(prompt_dir.glob("*.md"))
    json_files = list(prompt_dir.glob("*.json"))
    require(len(md_files) >= len(export), "Per-package Markdown files created")
    require(len(json_files) >= len(export), "Per-package JSON files created")

    report = (out / "phase9f_ai_profiles_dry_run_report.md").read_text(encoding="utf-8")
    for text in [
        "Phase 9F",
        "AI Profiles Dry-run",
        "value_analyst",
        "quality_analyst",
        "risk_analyst",
        "skeptic_analyst",
        "OpenAI called: False",
        "yfinance called: False",
        "Pipeline recalculated: False",
        "Phase 9G",
    ]:
        require(text in report, f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 9F AI Profiles Dry-run is valid")


if __name__ == "__main__":
    main()
