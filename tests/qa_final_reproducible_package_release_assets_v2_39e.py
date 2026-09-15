#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_final_reproducible_package_release_assets_v2_39e.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_39e_final_reproducible_package_release_assets"
REQUIRED = [
    "final_reproducible_package_assets_matrix_v2_39e.csv",
    "final_reproducible_package_inventory_v2_39e.csv",
    "github_release_publication_checklist_v2_39e.csv",
    "RELEASE_NOTES_DRAFT_v2_39e.md",
    "FINAL_REPRODUCIBLE_PACKAGE_RELEASE_ASSETS_v2_39e.md",
    "final_reproducible_package_release_assets_summary_v2_39e.json",
    "final_reproducible_package_release_assets_manifest_v2_39e.json",
    "README.md",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "final_reproducible_package_release_assets_summary_v2_39e.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "final_reproducible_package_release_assets_manifest_v2_39e.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "final_reproducible_package_assets_matrix_v2_39e.csv")
    inventory = rows(OUT / "final_reproducible_package_inventory_v2_39e.csv")
    notes = (OUT / "RELEASE_NOTES_DRAFT_v2_39e.md").read_text(encoding="utf-8")
    report = (OUT / "FINAL_REPRODUCIBLE_PACKAGE_RELEASE_ASSETS_v2_39e.md").read_text(encoding="utf-8")
    assert summary["phase"] == "v2.39E-final-reproducible-package-release-assets"
    assert summary["status"] == "FINAL_REPRODUCIBLE_PACKAGE_RELEASE_ASSETS_READY"
    assert summary["source_status"] == "CLEAN_WINDOWS_INSTALL_VALIDATION_READY"
    assert summary["stable_tag"] == "v2.38CJ-local-stable"
    assert summary["release_asset_scope"] == "draft_assets_only"
    assert summary["critical_missing_count"] == 0
    assert summary["blocker_count"] == 0
    assert summary["release_notes_status"] == "READY"
    assert summary["publication_checklist_status"] == "READY"
    assert summary["package_inventory_status"] == "READY"
    for key in ["github_release_created", "assets_uploaded", "zip_created", "tag_created", "network_used", "dependency_install_executed", "datasets_mutated", "scoring_recomputed", "ranking_changed", "weights_changed", "methodology_changed", "ui_changed", "financial_advice_created", "broker_actions_allowed"]:
        assert summary[key] is False, key
    assert summary["next_recommended_phase"] == "v2.39F-real-post-release-local-smoke-test"
    for phrase in ["v2.38CJ-local-stable", "experimental ranking", "not financial advice", "no broker", "local research tool"]:
        assert phrase in notes, phrase
    assert {r["status"] for r in matrix} <= {"PASS", "WARN", "BLOCKER"}
    assert not any(r["status"] == "BLOCKER" for r in matrix)
    if summary["warn_count"] > 0:
        assert "Warnings are documented" in report
    assert any(r["sha256"] for r in inventory)
    for r in inventory:
        if r["status"] != "MISSING":
            assert re.fullmatch(r"[0-9a-f]{64}", r["sha256"]), r["asset_path"]
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.39E/final-reproducible-package-release-assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
