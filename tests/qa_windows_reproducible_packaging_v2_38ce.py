#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_windows_reproducible_packaging_v2_38ce.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ce_windows_reproducible_packaging"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "windows_reproducible_packaging_summary_v2_38ce.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "windows_reproducible_packaging_manifest_v2_38ce.json").read_text(encoding="utf-8"))
    checks = rows(OUT / "windows_reproducible_packaging_checklist_v2_38ce.csv")
    guide = (OUT / "WINDOWS_REPRODUCIBLE_PACKAGING_v2_38ce.md").read_text(encoding="utf-8")
    preflight = (OUT / "WINDOWS_PREFLIGHT_CHECKLIST_v2_38ce.md").read_text(encoding="utf-8")
    assert summary["status"] == "WINDOWS_PACKAGE_READY_WITH_WARNINGS"
    assert summary["qa_status"] == "PASS"
    assert summary["zip_created"] is False
    assert summary["total_files_in_package"] > 20
    assert summary["total_bytes"] > 0
    assert all(row["status"] == "PASS" for row in checks)
    assert manifest["packaging_mode"] == "manifest_based_reproducible_packaging"
    assert manifest["total_files_in_package"] == summary["total_files_in_package"]
    assert manifest["total_bytes"] == summary["total_bytes"]
    assert ".env" in manifest["excluded_patterns"]
    assert ".git/" in manifest["excluded_patterns"]
    assert all(value is False for value in manifest["guardrails"].values())
    assert "app_v2_37.py" in manifest["included_files"]
    assert "run_local_ui_v2_37.bat" in manifest["included_files"]
    assert "v2.38CF" in guide
    assert "D:\\Proyectos\\💰 Scout Finance" in preflight
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CE/windows-reproducible-packaging")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
