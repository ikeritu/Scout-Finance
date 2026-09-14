#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_streamlit_visual_smoke_test_v2_38cf.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cf_streamlit_visual_smoke_test"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "streamlit_visual_smoke_test_summary_v2_38cf.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "streamlit_visual_smoke_test_manifest_v2_38cf.json").read_text(encoding="utf-8"))
    checks = rows(OUT / "streamlit_visual_smoke_test_checklist_v2_38cf.csv")
    report = (OUT / "STREAMLIT_VISUAL_SMOKE_TEST_v2_38cf.md").read_text(encoding="utf-8")
    assert summary["status"] in {"STREAMLIT_VISUAL_SMOKE_PASS", "STREAMLIT_VISUAL_SMOKE_PASS_WITH_ENVIRONMENT_LIMITATIONS"}
    assert summary["qa_status"] == "PASS"
    assert summary["validation_mode"] in {"BROWSER_SMOKE_TEST", "STRUCTURAL_SMOKE_TEST"}
    assert summary["total_assets"] == 1111
    assert summary["main_ranking_count"] == 318
    assert summary["partial_comparability_count"] == 373
    assert summary["review_required_count"] == 124
    assert summary["blocked_count"] == 270
    assert summary["not_yet_scored_count"] == 26
    assert summary["fail_count"] == 0
    assert all(row["status"] != "FAIL" for row in checks)
    assert any(row["category"] == "ui_structure" and row["status"] == "PASS" for row in checks)
    assert manifest["source_phase"] == "v2.38CE-windows-reproducible-packaging"
    assert manifest["screenshots_available"] == summary["screenshots_available"]
    assert all(value is False for value in manifest["guardrails"].values())
    assert "v2.38CG" in report
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CF/streamlit-visual-smoke-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
