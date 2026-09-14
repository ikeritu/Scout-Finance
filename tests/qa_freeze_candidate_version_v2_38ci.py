#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_freeze_candidate_version_v2_38ci.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ci_freeze_candidate_version"
REQUIRED_OUTPUTS = [
    "freeze_candidate_matrix_v2_38ci.csv",
    "freeze_candidate_traceability_v2_38ci.csv",
    "freeze_candidate_summary_v2_38ci.json",
    "freeze_candidate_manifest_v2_38ci.json",
    "FREEZE_CANDIDATE_VERSION_v2_38ci.md",
    "README.md",
]
FORBIDDEN_ADVICE = re.compile(r"\b(buy|sell|hold|target price|price target|recommendation|strong buy)\b", re.IGNORECASE)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED_OUTPUTS:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "freeze_candidate_summary_v2_38ci.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "freeze_candidate_manifest_v2_38ci.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "freeze_candidate_matrix_v2_38ci.csv")
    traces = rows(OUT / "freeze_candidate_traceability_v2_38ci.csv")
    report = (OUT / "FREEZE_CANDIDATE_VERSION_v2_38ci.md").read_text(encoding="utf-8")
    assert summary["phase"] == "v2.38CI-freeze-candidate-version"
    assert summary["status"] == "FREEZE_CANDIDATE_VERSION_LOCKED_WITH_DOCUMENTED_LIMITATIONS"
    assert summary["qa_status"] == "PASS"
    assert summary["fail_count"] == 0
    assert summary["warn_count"] == 0
    assert summary["blocking_issue_count"] == 0
    assert summary["documented_limitation_count"] > 0
    assert summary["ranking_total"] == 1111
    assert summary["ranking_main_count"] == 318
    assert summary["ranking_partial_count"] == 373
    assert summary["ranking_review_required_count"] == 124
    assert summary["ranking_blocked_count"] == 270
    assert summary["ranking_no_adapter_count"] == 26
    assert all(value is False for value in manifest["guardrails"].values())
    assert all(row["status"] != "FAIL" for row in matrix)
    assert all(row["status"] == "PASS" for row in traces)
    assert "v2.38CJ-release-handoff" in report
    assert not FORBIDDEN_ADVICE.search(report)
    assert manifest["outputs"]
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CI/freeze-candidate-version")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
