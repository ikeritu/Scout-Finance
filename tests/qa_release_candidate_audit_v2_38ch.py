#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_release_candidate_audit_v2_38ch.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ch_release_candidate_audit"
REQUIRED_CATEGORIES = {"SOURCE_PHASE_STATUS", "RANKING_COUNTS", "GUARDRAILS", "DOCUMENTATION", "TRACEABILITY", "RISK_REGISTER", "ENVIRONMENT_WARNINGS", "PACKAGING", "FREEZE_READINESS"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "release_candidate_audit_summary_v2_38ch.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "release_candidate_audit_manifest_v2_38ch.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "release_candidate_audit_matrix_v2_38ch.csv")
    traceability = rows(OUT / "release_candidate_traceability_v2_38ch.csv")
    report = (OUT / "RELEASE_CANDIDATE_AUDIT_v2_38ch.md").read_text(encoding="utf-8")
    assert summary["status"] == "RELEASE_CANDIDATE_AUDIT_PASS_WITH_DOCUMENTED_LIMITATIONS"
    assert summary["qa_status"] == "PASS"
    assert summary["audit_count"] >= 20
    assert summary["fail_count"] == 0
    assert summary["blocking_issue_count"] == 0
    assert summary["documented_limitation_count"] >= 10
    assert summary["ranking_total"] == 1111
    assert summary["ranking_main_count"] == 318
    assert summary["ranking_partial_count"] == 373
    assert summary["ranking_review_required_count"] == 124
    assert summary["ranking_blocked_count"] == 270
    assert summary["ranking_no_adapter_count"] == 26
    assert REQUIRED_CATEGORIES.issubset({row["category"] for row in matrix})
    assert {"v2.38CD", "v2.38CE", "v2.38CF", "v2.38CG"}.issubset({row["source_phase"] for row in traceability})
    assert all(row["status"] != "FAIL" for row in matrix)
    assert all(value is False for value in manifest["guardrails"].values())
    assert "v2.38CI" in report
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CH/release-candidate-audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
