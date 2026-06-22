from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PHASE = "9B"


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

    print("Scout Finance — Phase 9B Minimal DataHub checker")
    print("=" * 92)

    required = [
        root / "src" / "data_hub.py",
        root / "src" / "phase9b_minimal_datahub_cache.py",
        root / "scripts" / "check_phase9b_minimal_datahub_cache.py",
        out / "phase9b_minimal_datahub_cache_summary.json",
        out / "phase9b_minimal_datahub_cache_report.md",
        out / "phase9b_minimal_datahub_cache_audit.json",
        out / "phase9b_datahub_local_source_manifest.json",
        out / "phase9b_datahub_local_source_manifest.csv",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "phase9b_minimal_datahub_cache_summary.json")
    audit = read_json(out / "phase9b_minimal_datahub_cache_audit.json")
    manifest = read_json(out / "phase9b_datahub_local_source_manifest.json")

    require(summary.get("phase") == PHASE, "Summary phase is 9B")
    require(summary.get("status") == "OK", "Summary status OK")
    require(summary.get("default_top_n") == 3, "Default TOP N OK")
    require(summary.get("max_top_n") == 3, "MAX TOP N OK")
    require(summary.get("data_mode") in {"local_only", "audit_only"}, "Data mode safe")
    require(summary.get("external_fetch_allowed") is False, "External fetch disabled")
    require(summary.get("local_source_records", 0) > 0, "Local source records > 0")
    require(summary.get("outputs_scouting_records", 0) > 0, "outputs/scouting records > 0")
    require(summary.get("expected_paths", {}).get("releases/Scout_Finance_v0.8.0_candidate_FREEZE.zip") is True, "v0.8 freeze detected")

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
    require(audit.get("guard", {}).get("external_fetch_allowed") is False, "Audit guard external fetch disabled")
    require(audit.get("record_count") == summary.get("local_source_records"), "Audit record count matches summary")
    require(isinstance(audit.get("recommendations"), list), "Recommendations list present")

    require(manifest.get("external_fetch_allowed") is False, "Manifest external fetch disabled")
    require(manifest.get("record_count") == summary.get("local_source_records"), "Manifest record count matches summary")
    require(isinstance(manifest.get("records"), list), "Manifest records list present")

    with (out / "phase9b_datahub_local_source_manifest.csv").open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    require(len(rows) == summary.get("local_source_records"), "Manifest CSV row count matches summary")

    data_hub_text = (root / "src" / "data_hub.py").read_text(encoding="utf-8")
    for text in [
        "external_fetch_allowed",
        "yfinance_called",
        "openai_called",
        "load_local_json",
        "load_local_csv_rows",
        "discover_local_sources",
    ]:
        require(text in data_hub_text, f"data_hub.py contains: {text}")

    report = (out / "phase9b_minimal_datahub_cache_report.md").read_text(encoding="utf-8")
    for text in [
        "Phase 9B",
        "Minimal DataHub",
        "OpenAI called: False",
        "yfinance called: False",
        "Pipeline recalculated: False",
        "Phase 9C",
    ]:
        require(text in report, f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 9B Minimal DataHub is valid")


if __name__ == "__main__":
    main()
