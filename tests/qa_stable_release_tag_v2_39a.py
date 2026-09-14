#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_stable_release_tag_v2_39a.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39a_stable_release_tag"
REQUIRED_OUTPUTS = [
    "stable_release_tag_checklist_v2_39a.csv",
    "stable_release_tag_manifest_v2_39a.json",
    "stable_release_tag_summary_v2_39a.json",
    "STABLE_RELEASE_TAG_v2_39a.md",
    "README.md",
]
FORBIDDEN_ADVICE = re.compile(r"\b(strong buy|price target|target price|automatic trading signal)\b", re.IGNORECASE)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED_OUTPUTS:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "stable_release_tag_summary_v2_39a.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "stable_release_tag_manifest_v2_39a.json").read_text(encoding="utf-8"))
    checklist = rows(OUT / "stable_release_tag_checklist_v2_39a.csv")
    report = (OUT / "STABLE_RELEASE_TAG_v2_39a.md").read_text(encoding="utf-8")
    assert summary["phase"] == "v2.39A-stable-release-tag"
    assert summary["status"] == "STABLE_RELEASE_TAG_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["cycle_status"] == "V2_38_LOCAL_CYCLE_CLOSED"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["source_commit"] == "56e773b"
    assert summary["publication_scope"] == "local_research_tool_only"
    assert summary["tag_push_requires_user_confirmation"] is True
    assert summary["fail_count"] == 0
    assert summary["warn_count"] == 0
    assert summary["blocking_issue_count"] == 0
    assert summary["documented_limitation_count"] == 14
    assert summary["ranking_total"] == 1111
    assert summary["ranking_main_count"] == 318
    assert summary["ranking_partial_count"] == 373
    assert summary["ranking_review_required_count"] == 124
    assert summary["ranking_blocked_count"] == 270
    assert summary["ranking_no_adapter_count"] == 26
    for key in ["network_used", "scoring_recomputed", "weights_changed", "ranking_changed", "methodology_changed", "datasets_mutated", "ui_changed", "financial_advice_created", "recommendations_created", "broker_actions_allowed"]:
        assert summary[key] is False, key
    assert len(checklist) >= 10
    assert all(row["status"] == "PASS" for row in checklist)
    for phrase in ["v2.38CJ-local-stable", "56e773b", "local_research_tool_only", "v2.39B-public-documentation-cleanup", "explicit user authorization"]:
        assert phrase in report
    assert not FORBIDDEN_ADVICE.search(report)
    assert manifest["outputs"]
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.39A/stable-release-tag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
