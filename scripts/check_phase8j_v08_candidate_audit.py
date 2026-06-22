from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PHASE = "8J"
EXPECTED_PHASES = ["8A", "8B", "8C", "8D", "8E", "8F", "8G", "8H", "8I"]


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

    print("Scout Finance — Phase 8J v0.8 Candidate Audit checker")
    print("=" * 92)

    required = [
        out / "phase8j_v08_candidate_audit_summary.json",
        out / "phase8j_v08_candidate_audit_report.md",
        out / "phase8j_v08_candidate_audit.json",
        out / "phase8j_v08_candidate_readiness_decision.json",
        out / "phase8j_phase_status_matrix.csv",
        out / "phase8j_key_outputs_manifest.csv",
        root / "src" / "phase8j_v08_candidate_audit.py",
    ]
    for path in required:
        require_file(path)

    summary = read_json(out / "phase8j_v08_candidate_audit_summary.json")
    audit = read_json(out / "phase8j_v08_candidate_audit.json")
    readiness = read_json(out / "phase8j_v08_candidate_readiness_decision.json")

    require(summary.get("phase") == PHASE, "Summary phase is 8J")
    require(summary.get("status") in {"OK", "REVIEW"}, "Summary status is OK or REVIEW")
    require(summary.get("default_top_n") == 3, "Default TOP N OK: 3")
    require(summary.get("max_top_n") == 3, "MAX TOP N OK: 3")

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

    require(isinstance(summary.get("phases_audited"), list), "Phases audited is list")
    for phase in EXPECTED_PHASES:
        require(phase in summary.get("phases_audited", []), f"Phase audited: {phase}")

    require(audit.get("phase") == PHASE, "Audit phase OK")
    require("phase_status" in audit, "Audit contains phase_status")
    require("key_outputs" in audit, "Audit contains key_outputs")
    require("readiness" in audit, "Audit contains readiness")
    require("controls" in audit, "Audit contains controls")

    phase_status = audit["phase_status"]
    require(isinstance(phase_status, list), "Phase status is list")
    require(len(phase_status) == len(EXPECTED_PHASES), "Phase status count OK")

    seen = {row.get("phase") for row in phase_status}
    for phase in EXPECTED_PHASES:
        require(phase in seen, f"Phase status row present: {phase}")

    for row in phase_status:
        phase = row.get("phase")
        require(row.get("summary_exists") is True, f"Summary exists: {phase}")
        require(row.get("status") == "OK", f"Prior phase status OK: {phase}")
        if phase in {"8C", "8D", "8E", "8F", "8G", "8H", "8I"}:
            for flag in ["openai_called", "api_called", "yfinance_called", "pipeline_recalculated", "app_modified", "filters_modified", "release_modified"]:
                require(row.get(flag) in (False, None), f"Prior phase safe flag: {phase}::{flag}")

    require(readiness.get("readiness") in {"ready_for_v0_8_candidate", "not_ready"}, "Readiness value valid")
    require("blockers" in readiness and isinstance(readiness["blockers"], list), "Readiness blockers list")
    require("warnings" in readiness and isinstance(readiness["warnings"], list), "Readiness warnings list")
    require("recommendation" in readiness, "Readiness recommendation present")
    require("release_positioning" in readiness, "Release positioning present")
    require(readiness["release_positioning"].get("top_n") == 3, "Release positioning TOP N OK")

    with (out / "phase8j_phase_status_matrix.csv").open("r", encoding="utf-8", newline="") as fh:
        matrix_rows = list(csv.DictReader(fh))
    require(len(matrix_rows) == len(EXPECTED_PHASES), "Phase status matrix row count OK")

    with (out / "phase8j_key_outputs_manifest.csv").open("r", encoding="utf-8", newline="") as fh:
        manifest_rows = list(csv.DictReader(fh))
    require(len(manifest_rows) >= 10, "Key outputs manifest has entries")
    existing_with_sha = [r for r in manifest_rows if r.get("exists") == "True" and r.get("sha256")]
    require(len(existing_with_sha) >= 10, "Key outputs manifest contains SHA256 entries")

    report = (out / "phase8j_v08_candidate_audit_report.md").read_text(encoding="utf-8")
    for text in [
        "Phase 8J",
        "v0.8 candidate",
        "OpenAI called: False",
        "No inventar datos",
        "data_insufficient",
        "Real AI calls remain disabled by default",
        "release candidate",
    ]:
        require(text in report, f"Report contains: {text}")

    print()
    print("Result")
    print("-" * 92)
    print("OK   Phase 8J v0.8 Candidate Audit is valid")


if __name__ == "__main__":
    main()
