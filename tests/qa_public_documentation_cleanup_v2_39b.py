#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_public_documentation_cleanup_v2_39b.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39b_public_documentation_cleanup"
REQUIRED_OUTPUTS = [
    "public_documentation_cleanup_matrix_v2_39b.csv",
    "public_documentation_index_v2_39b.csv",
    "public_documentation_cleanup_summary_v2_39b.json",
    "public_documentation_cleanup_manifest_v2_39b.json",
    "PUBLIC_DOCUMENTATION_CLEANUP_v2_39b.md",
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
    assert (ROOT / "docs/PUBLIC_DOCUMENTATION_INDEX_v2_39b.md").exists()
    assert (ROOT / "docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md").exists()
    summary = json.loads((OUT / "public_documentation_cleanup_summary_v2_39b.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "public_documentation_cleanup_manifest_v2_39b.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "public_documentation_cleanup_matrix_v2_39b.csv")
    index = rows(OUT / "public_documentation_index_v2_39b.csv")
    public_guide = (ROOT / "docs/LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md").read_text(encoding="utf-8")
    docs_text = "\n".join((ROOT / name).read_text(encoding="utf-8") for name in ["README.md", "VERSION.md", "CHANGELOG.md", "ROADMAP_v2_38_CURRENT.md"])
    assert summary["phase"] == "v2.39B-public-documentation-cleanup"
    assert summary["status"] == "PUBLIC_DOCUMENTATION_CLEANUP_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["source_status"] == "STABLE_RELEASE_TAG_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["source_commit"] == "56e773b"
    assert summary["cycle_status"] == "V2_38_LOCAL_CYCLE_CLOSED"
    assert summary["publication_scope"] == "local_research_tool_only"
    assert summary["fail_count"] == 0
    assert summary["blocking_issue_count"] == 0
    assert summary["ranking_total"] == 1111
    assert summary["ranking_main_count"] == 318
    assert summary["ranking_partial_count"] == 373
    assert summary["ranking_review_required_count"] == 124
    assert summary["ranking_blocked_count"] == 270
    assert summary["ranking_no_adapter_count"] == 26
    for key in ["network_used", "scoring_recomputed", "weights_changed", "ranking_changed", "methodology_changed", "datasets_mutated", "ui_changed", "financial_advice_created", "recommendations_created", "broker_actions_allowed", "tag_created", "github_release_created"]:
        assert summary[key] is False, key
    assert len(matrix) >= 15
    assert all(row["status"] == "PASS" for row in matrix)
    assert len(index) >= 6
    for phrase in ["local research tool", "not financial advice", "does not include a broker workflow", "experimental ranking", "v2.38CJ-local-stable", "phase9b-global-enrichment-v2-38b", "Windows paths with spaces or emoji must be wrapped in quotes"]:
        assert phrase in public_guide
    for phrase in ["v2.39B", "v2.39C"]:
        assert phrase in docs_text
    assert not FORBIDDEN_ADVICE.search(public_guide)
    assert manifest["outputs"]
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.39B/public-documentation-cleanup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
