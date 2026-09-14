#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_security_sensitive_files_audit_v2_39c.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39c_security_sensitive_files_audit"
REQUIRED = [
    "security_sensitive_files_audit_matrix_v2_39c.csv",
    "security_sensitive_patterns_v2_39c.csv",
    "security_sensitive_files_summary_v2_39c.json",
    "security_sensitive_files_manifest_v2_39c.json",
    "SECURITY_SENSITIVE_FILES_AUDIT_v2_39c.md",
    "README.md",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "security_sensitive_files_summary_v2_39c.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "security_sensitive_files_manifest_v2_39c.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "security_sensitive_files_audit_matrix_v2_39c.csv")
    report = (OUT / "SECURITY_SENSITIVE_FILES_AUDIT_v2_39c.md").read_text(encoding="utf-8")
    assert summary["phase"] == "v2.39C-security-sensitive-files-audit"
    assert summary["status"] == "SECURITY_SENSITIVE_FILES_AUDIT_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_status"] == "PUBLIC_DOCUMENTATION_CLEANUP_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["publication_scope"] == "local_research_tool_only"
    assert summary["blocker_count"] == 0
    assert summary["tracked_files_scanned"] > 0
    assert summary["patterns_checked"] >= 8
    assert summary["next_recommended_phase"] == "v2.39D-clean-windows-install-validation"
    for key in ["network_used", "datasets_mutated", "scoring_recomputed", "weights_changed", "ranking_changed", "methodology_changed", "ui_changed", "financial_advice_created", "broker_actions_allowed", "tag_created", "github_release_created"]:
        assert summary[key] is False, key
    assert {row["status"] for row in matrix} <= {"PASS", "WARN", "BLOCKER"}
    assert not any(row["status"] == "BLOCKER" for row in matrix)
    if summary["warn_count"] > 0:
        assert "Warnings Documented" in report
    assert manifest["outputs"]
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.39C/security-sensitive-files-audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
