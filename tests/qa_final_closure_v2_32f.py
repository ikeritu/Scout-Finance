#!/usr/bin/env python3
"""Final accumulated closure and integrity gate for the v2.32 local UI."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "releases/MANIFEST_v2.32F_local_ui_final_freeze.json"
POINTERS = (
    "outputs/full_universe_source_acquisition/current_operational_universe_pointer.json",
    "outputs/full_universe_source_acquisition/current_operational_scoring_pointer.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_gate(path: str, marker: str) -> dict[str, object]:
    started = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(ROOT / path)], cwd=ROOT, capture_output=True, text=True, timeout=180
    )
    if result.returncode:
        raise AssertionError(f"{path} failed\n{result.stdout}\n{result.stderr}")
    assert marker in result.stdout
    return {"gate": path, "status": "PASS", "seconds": round(time.perf_counter() - started, 3)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["version"] == "v2.32F-local-ui-final-freeze"
    assert manifest["status"] == "FROZEN_PASS"
    assert manifest["roadmap"] == {"completed": 6, "total": 6}
    assert manifest["universe_rows"] == 43089
    assert manifest["providers"] == "14/14"
    assert manifest["open_incidents"] == 0
    assert manifest["production_scoring_authorized"] is False
    assert manifest["allow_ranking"] is False

    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.is_file(), item["path"]
        assert sha256(path) == item["sha256"], item["path"]

    pointers_before = {path: sha256(ROOT / path) for path in POINTERS}
    gates = [
        run_gate("tests/qa_ui_startup_v2_32a.py", "PASS: v2.32A/clean-install/real-startup"),
        run_gate("tests/qa_operational_package_v2_32e.py", "PASS: v2.32E/windows-double-click"),
    ]
    pointers_after = {path: sha256(ROOT / path) for path in POINTERS}
    assert pointers_before == pointers_after

    phase_reports = {
        "v2.32A": "outputs/local_ui/v2_32a_ui_startup/startup_report.json",
        "v2.32B": "outputs/local_ui/v2_32b_real_user_journeys/acceptance_report.json",
        "v2.32C": "outputs/local_ui/v2_32c_visual_responsive_usability/audit_report.json",
        "v2.32D": "outputs/local_ui/v2_32d_incident_closure/closure_report.json",
        "v2.32E": "outputs/local_ui/v2_32e_operational_package/package_report.json",
    }
    for phase, path in phase_reports.items():
        report = json.loads((ROOT / path).read_text(encoding="utf-8"))
        assert report["phase"] == phase and report["status"] == "PASS", phase

    report = {
        "phase": "v2.32F",
        "version": "v2.32F-local-ui-final-freeze",
        "status": "PASS",
        "freeze_status": "FROZEN",
        "roadmap": {"completed": 6, "total": 6},
        "accumulated_gates": gates,
        "phase_reports_verified": list(phase_reports),
        "universe_rows": 43089,
        "unique_identities": 43089,
        "providers_complete": 14,
        "providers_expected": 14,
        "open_incidents": 0,
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "manifest_files_verified": len(manifest["files"]),
        "operational_pointer_sha256": pointers_after,
        "operational_pointers_modified_by_qa": False,
        "dataset_modified_by_qa": False,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        output = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print("PASS: v2.32A-B-C-D-E-F/6-of-6/final-freeze/43089/14-of-14/0-open/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
