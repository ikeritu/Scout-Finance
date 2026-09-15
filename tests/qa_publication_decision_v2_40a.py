#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_publication_decision_v2_40a.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_40a_publication_decision"
REQUIRED = [
    "publication_decision_matrix_v2_40a.csv",
    "publication_options_analysis_v2_40a.csv",
    "publication_policy_gate_v2_40a.csv",
    "publication_decision_summary_v2_40a.json",
    "publication_decision_manifest_v2_40a.json",
    "PUBLICATION_DECISION_v2_40a.md",
    "README.md",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "publication_decision_summary_v2_40a.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "publication_decision_manifest_v2_40a.json").read_text(encoding="utf-8"))
    gates = rows(OUT / "publication_policy_gate_v2_40a.csv")
    matrix = rows(OUT / "publication_decision_matrix_v2_40a.csv")
    report = (OUT / "PUBLICATION_DECISION_v2_40a.md").read_text(encoding="utf-8")
    assert summary["status"] == "PUBLICATION_DECISION_RECORDED"
    assert summary["source_status"] == "REAL_POST_RELEASE_LOCAL_SMOKE_TEST_READY"
    assert summary["selected_decision"] == "PUBLIC_DEMO_SAFE_MODE_REQUIRED_BEFORE_EXTERNAL_DEPLOYMENT"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["publication_scope_current"] == "local_research_tool_only"
    joined_gates = "\n".join(f"{g['phase']} {g['gate']} {g['decision']}" for g in gates)
    assert "v2.40B ALLOWED_HOSTING_PREPARATION_ONLY allowed" in joined_gates
    assert "v2.40C REQUIRED_BEFORE_PUBLIC_DEMO required" in joined_gates
    assert "v2.40D BLOCKED_UNTIL_V2_40B_AND_V2_40C_PASS blocked" in joined_gates
    for key in ["deployment_allowed", "github_release_created", "assets_uploaded", "tag_created", "network_used", "credential_preparation_done", "datasets_mutated", "scoring_recomputed", "ranking_changed", "weights_changed", "methodology_changed", "ui_changed", "financial_advice_created", "broker_actions_allowed"]:
        assert summary[key] is False, key
    assert summary["ranking_total"] == 1111
    assert summary["ranking_main_count"] == 318
    assert summary["ranking_partial_count"] == 373
    assert summary["ranking_review_required_count"] == 124
    assert summary["ranking_blocked_count"] == 270
    assert summary["ranking_no_adapter_count"] == 26
    assert summary["next_recommended_phase"] == "v2.40B-streamlit-cloud-hosting-prep"
    assert {row["status"] for row in matrix} <= {"PASS", "WARN", "BLOCKER"}
    assert not any(row["status"] == "BLOCKER" for row in matrix)
    assert "should not be deployed publicly yet" in report
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.40A/publication-decision")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
