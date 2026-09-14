#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_required_outputs_diagnostics_v2_38cd.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cd_required_outputs_diagnostics"
ALLOWED = {"PRESENT", "MISSING", "DEGRADED", "OPTIONAL", "BLOCKING_MISSING", "NON_BLOCKING_MISSING"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "required_outputs_summary_v2_38cd.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "manifest_v2_38cd.json").read_text(encoding="utf-8"))
    checklist = rows(OUT / "required_outputs_checklist_v2_38cd.csv")
    missing = rows(OUT / "missing_data_diagnostics_v2_38cd.csv")
    report = (OUT / "REQUIRED_OUTPUTS_DIAGNOSTICS_v2_38cd.md").read_text(encoding="utf-8")
    assert summary["status"] == "LOCAL_APP_READY_WITH_WARNINGS"
    assert summary["qa_status"] == "PASS"
    assert summary["output_count"] == len(checklist)
    assert summary["missing_diagnostic_count"] == len(missing)
    assert summary["blocking_missing_count"] == 0
    assert {row["status"] for row in checklist}.issubset(ALLOWED)
    assert {row["status"] for row in missing}.issubset(ALLOWED)
    assert any(row["required_for"] == "local_app_startup" and row["status"] == "PRESENT" for row in checklist)
    assert any(row["required_for"] == "experimental_ranking" and row["status"] == "PRESENT" for row in checklist)
    assert any(row["required_for"] == "watchlists_exports" and row["status"] == "PRESENT" for row in checklist)
    assert any(row["diagnostic_id"] == "jurisdictions_without_adapter" and row["affected_count"] == "26" for row in missing)
    assert any(row["diagnostic_id"] == "low_coverage_blocked_assets" and row["affected_count"] == "270" for row in missing)
    assert "v2.38CE" in report
    for value in manifest["guardrails"].values():
        assert value is False
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CD/required-outputs-diagnostics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
