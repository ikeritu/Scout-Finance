#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_real_post_release_local_smoke_test_v2_39f.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39f_real_post_release_local_smoke_test"
REQUIRED = [
    "real_post_release_local_smoke_matrix_v2_39f.csv",
    "real_post_release_local_manual_checklist_v2_39f.csv",
    "real_post_release_local_smoke_summary_v2_39f.json",
    "real_post_release_local_smoke_manifest_v2_39f.json",
    "REAL_POST_RELEASE_LOCAL_SMOKE_TEST_v2_39f.md",
    "README.md",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "real_post_release_local_smoke_summary_v2_39f.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "real_post_release_local_smoke_manifest_v2_39f.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "real_post_release_local_smoke_matrix_v2_39f.csv")
    report = (OUT / "REAL_POST_RELEASE_LOCAL_SMOKE_TEST_v2_39f.md").read_text(encoding="utf-8")
    assert summary["phase"] == "v2.39F-real-post-release-local-smoke-test"
    assert summary["status"] == "REAL_POST_RELEASE_LOCAL_SMOKE_TEST_READY"
    assert summary["source_status"] == "FINAL_REPRODUCIBLE_PACKAGE_RELEASE_ASSETS_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["publication_scope"] == "local_research_tool_only"
    assert summary["test_scope"] == "post_release_local_smoke"
    assert summary["target_runtime"] == "local_streamlit"
    assert summary["blocker_count"] == 0
    assert summary["compile_fail_count"] == 0
    assert summary["ranking_loader_status"] == "PASS"
    assert summary["ranking_available"] is True
    assert summary["ranking_total"] == 1111
    assert summary["ranking_main_count"] == 318
    assert summary["ranking_partial_count"] == 373
    assert summary["ranking_review_required_count"] == 124
    assert summary["ranking_blocked_count"] == 270
    assert summary["ranking_no_adapter_count"] == 26
    assert summary["launcher_status"] == "PASS"
    assert summary["browser_validation_status"] in {"MANUAL_REQUIRED", "PASS_REAL_BROWSER"}
    assert summary["browser_validation_status"] != "PASS_REAL_BROWSER"
    for key in ["github_release_created", "assets_uploaded", "tag_created", "network_used", "dependency_install_executed", "datasets_mutated", "scoring_recomputed", "ranking_changed", "weights_changed", "methodology_changed", "ui_changed", "financial_advice_created", "broker_actions_allowed"]:
        assert summary[key] is False, key
    assert summary["next_recommended_phase"] == "v2.40A-publication-decision"
    assert {r["status"] for r in matrix} <= {"PASS", "WARN", "BLOCKER"}
    assert not any(r["status"] == "BLOCKER" for r in matrix)
    if summary["warn_count"] > 0:
        assert "Warnings are documented" in report
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    assert manifest["ranking_counts"]["ranking_total"] == 1111
    print("PASS: v2.39F/real-post-release-local-smoke-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
