#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_clean_windows_install_validation_v2_39d.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39d_clean_windows_install_validation"
REQUIRED = [
    "clean_windows_install_validation_matrix_v2_39d.csv",
    "clean_windows_install_checklist_v2_39d.ps1",
    "clean_windows_install_validation_summary_v2_39d.json",
    "clean_windows_install_validation_manifest_v2_39d.json",
    "CLEAN_WINDOWS_INSTALL_VALIDATION_v2_39d.md",
    "README.md",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "clean_windows_install_validation_summary_v2_39d.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "clean_windows_install_validation_manifest_v2_39d.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "clean_windows_install_validation_matrix_v2_39d.csv")
    checklist = (OUT / "clean_windows_install_checklist_v2_39d.ps1").read_text(encoding="utf-8")
    report = (OUT / "CLEAN_WINDOWS_INSTALL_VALIDATION_v2_39d.md").read_text(encoding="utf-8")
    assert summary["phase"] == "v2.39D-clean-windows-install-validation"
    assert summary["status"] == "CLEAN_WINDOWS_INSTALL_VALIDATION_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_status"] == "SECURITY_SENSITIVE_FILES_AUDIT_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["target_platform"] == "Windows"
    assert summary["blocker_count"] == 0
    assert summary["critical_files_missing_count"] == 0
    assert summary["required_outputs_missing_count"] == 0
    assert summary["launcher_status"] == "PASS"
    assert summary["requirements_status"] == "PASS"
    assert summary["local_usage_docs_status"] == "PASS"
    assert summary["manual_windows_steps_count"] >= 8
    for command in ["git clone", "py -m venv .venv", "pip install -r requirements.txt", "python -m py_compile app_v2_37.py", "run_local_ui_v2_37.bat", "http://localhost:8501"]:
        assert command in checklist, command
    for key in ["network_used", "dependency_install_executed", "datasets_mutated", "scoring_recomputed", "weights_changed", "ranking_changed", "methodology_changed", "ui_changed", "financial_advice_created", "broker_actions_allowed", "tag_created", "github_release_created"]:
        assert summary[key] is False, key
    assert summary["next_recommended_phase"] == "v2.39E-final-reproducible-package-release-assets"
    assert {r["status"] for r in matrix} <= {"PASS", "WARN", "BLOCKER"}
    assert not any(r["status"] == "BLOCKER" for r in matrix)
    if summary["warn_count"] > 0:
        assert "Warnings are expected" in report
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.39D/clean-windows-install-validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
