#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_release_candidate_local_v2_38ca.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ca_release_candidate_local"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "release_candidate_local_summary_v2_38ca.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "release_candidate_local_manifest_v2_38ca.json").read_text(encoding="utf-8"))
    checklist = rows(OUT / "release_candidate_local_checklist_v2_38ca.csv")
    guide = (OUT / "OPERATOR_GUIDE_LOCAL_v2_38ca.md").read_text(encoding="utf-8")
    assert summary["qa_status"] == "PASS"
    assert summary["status"] == "RELEASE_CANDIDATE_LOCAL_READY_WITH_LIMITATIONS"
    assert summary["main_ranking_count"] == 318
    assert summary["partial_comparability_count"] == 373
    assert summary["review_required_count"] == 124
    assert summary["blocked_count"] == 270
    assert summary["not_yet_scored_count"] == 26
    assert summary["total_assets"] == 1111
    assert summary["operator_guide_created"] is True
    assert summary["startup_checklist_created"] is True
    assert summary["local_diagnostic_created"] is True
    assert summary["fail_count"] == 0
    assert all(row["status"] != "FAIL" for row in checklist)
    assert any(row["check_id"] == "bz_status" and row["status"] == "PASS" for row in checklist)
    assert "run_local_ui_v2_37.bat" in guide
    assert "requirements.txt" in guide
    assert "Ranking global (experimental)" in guide
    assert "not financial advice" in guide
    assert manifest["guardrails"]["scoring_recomputed"] is False
    assert manifest["guardrails"]["methodology_changed"] is False
    assert manifest["guardrails"]["weights_changed"] is False
    assert manifest["guardrails"]["network_used"] is False
    assert manifest["guardrails"]["ui_recomputes_scoring"] is False
    assert manifest["guardrails"]["financial_advice_created"] is False
    assert manifest["guardrails"]["broker_actions_allowed"] is False
    assert manifest["guardrails"]["recommendations_created"] is False
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CA/release-candidate-local/operator-guide-checklist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
