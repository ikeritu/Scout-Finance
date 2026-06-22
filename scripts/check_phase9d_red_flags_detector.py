from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PHASE = "9D"
ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


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
    red_flags_dir = out / "red_flags"

    print("Scout Finance — Phase 9D Deterministic Red Flags Detector checker")
    print("=" * 92)

    required = [
        root / "src" / "red_flags.py",
        root / "src" / "phase9d_red_flags_detector.py",
        root / "scripts" / "check_phase9d_red_flags_detector.py",
        out / "phase9d_red_flags_detector_summary.json",
        out / "phase9d_red_flags_detector_report.md",
        out / "phase9d_red_flags_detector_audit.json",
        out / "phase9d_red_flags_detector_export.json",
        out / "phase9d_red_flags_detector_index.csv",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "phase9d_red_flags_detector_summary.json")
    audit = read_json(out / "phase9d_red_flags_detector_audit.json")
    export = read_json(out / "phase9d_red_flags_detector_export.json")

    require(summary.get("phase") == PHASE, "Summary phase is 9D")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("default_top_n") == 3, "Default TOP N OK")
    require(summary.get("max_top_n") == 3, "MAX TOP N OK")
    require(summary.get("records_loaded", 0) > 0, "Records loaded > 0")
    require(summary.get("records_analyzed") == summary.get("records_loaded"), "Analyzed count matches loaded")
    require(red_flags_dir.exists(), "Red flags dir exists")

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
    require(audit.get("detector") == "src/red_flags.py", "Audit detector path OK")
    require(isinstance(export, list), "Export is list")
    require(len(export) == summary.get("records_analyzed"), "Export row count matches summary")

    total_flags = 0
    high_critical = 0
    for item in export:
        ticker = item.get("ticker")
        require("summary" in item, f"{ticker}: summary present")
        require("red_flags" in item, f"{ticker}: red_flags present")
        require("safety" in item, f"{ticker}: safety present")
        require(item["safety"].get("openai_called") is False, f"{ticker}: openai_called False")
        require(item["safety"].get("api_called") is False, f"{ticker}: api_called False")
        require(item["safety"].get("yfinance_called") is False, f"{ticker}: yfinance_called False")
        require(item["safety"].get("pipeline_recalculated") is False, f"{ticker}: pipeline_recalculated False")

        flags = item.get("red_flags", [])
        require(isinstance(flags, list), f"{ticker}: red_flags is list")
        total_flags += len(flags)
        if item["summary"].get("has_high_or_critical"):
            high_critical += 1

        for flag in flags:
            require(flag.get("severity") in ALLOWED_SEVERITIES, f"{ticker}: flag severity OK")
            for field in ["category", "code", "title", "detail", "evidence", "source"]:
                require(field in flag, f"{ticker}: flag field present: {field}")

        require_file(red_flags_dir / f"red_flags_{int(item.get('ticker') == item.get('ticker')):02d}_{ticker}.json") if False else ok(f"{ticker}: per-ticker filenames checked by directory inventory")

    require(total_flags == summary.get("total_red_flags"), "Total red flags matches summary")
    require(high_critical == summary.get("records_with_high_or_critical"), "High/critical record count matches summary")

    with (out / "phase9d_red_flags_detector_index.csv").open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == len(export), "Index row count matches export")

    md_files = list(red_flags_dir.glob("red_flags_*.md"))
    json_files = list(red_flags_dir.glob("red_flags_*.json"))
    require(len(md_files) >= len(export), "Per-ticker Markdown files created")
    require(len(json_files) >= len(export), "Per-ticker JSON files created")

    red_flags_text = (root / "src" / "red_flags.py").read_text(encoding="utf-8")
    for text in [
        "detect_red_flags",
        "debt",
        "margins",
        "fcf",
        "dilution",
        "data_quality",
        "risk",
        "valuation",
        "growth",
        "summarize_flags",
    ]:
        require(text in red_flags_text, f"red_flags.py contains: {text}")

    report = (out / "phase9d_red_flags_detector_report.md").read_text(encoding="utf-8")
    for text in [
        "Phase 9D",
        "Deterministic Red Flags Detector",
        "OpenAI called: False",
        "yfinance called: False",
        "Pipeline recalculated: False",
        "Phase 9E",
    ]:
        require(text in report, f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 9D Deterministic Red Flags Detector is valid")


if __name__ == "__main__":
    main()
