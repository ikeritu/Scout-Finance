#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_limitations_backlog_product_risk_register_v2_38cg.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cg_limitations_backlog_product_risk_register"
REQUIRED_CATEGORIES = {"DATA_COVERAGE", "DATA_QUALITY", "METHODOLOGY", "UX", "ENVIRONMENT", "PACKAGING", "LEGAL_COMPLIANCE", "PRODUCT_POSITIONING", "OPERATIONAL"}
ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
ALLOWED_LIKELIHOODS = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_STATUSES = {"OPEN", "MITIGATED", "ACCEPTED_LIMITATION", "DEFERRED", "BLOCKED"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "risk_register_summary_v2_38cg.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "risk_register_manifest_v2_38cg.json").read_text(encoding="utf-8"))
    risks = rows(OUT / "product_risk_register_v2_38cg.csv")
    backlog = rows(OUT / "limitations_backlog_v2_38cg.csv")
    report = (OUT / "LIMITATIONS_BACKLOG_PRODUCT_RISK_REGISTER_v2_38cg.md").read_text(encoding="utf-8")
    assert summary["status"] == "PRODUCT_RISK_REGISTER_READY_WITH_NON_BLOCKING_LIMITATIONS"
    assert summary["qa_status"] == "PASS"
    assert summary["risk_count"] == len(risks)
    assert summary["backlog_count"] == len(backlog)
    assert len(risks) >= 10
    assert summary["blocking_risk_count"] == 0
    assert REQUIRED_CATEGORIES.issubset({row["category"] for row in risks})
    assert {row["severity"] for row in risks}.issubset(ALLOWED_SEVERITIES)
    assert {row["likelihood"] for row in risks}.issubset(ALLOWED_LIKELIHOODS)
    assert {row["status"] for row in risks}.issubset(ALLOWED_STATUSES)
    assert any("screenshots" in row["title"].lower() for row in risks)
    assert any("270" in row["title"] or "270" in row["user_impact"] for row in risks)
    assert any("26" in row["title"] or "26" in row["user_impact"] for row in risks)
    assert any("124" in row["title"] or "124" in row["user_impact"] for row in risks)
    assert "v2.38CH" in report
    assert all(value is False for value in manifest["guardrails"].values())
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CG/limitations-backlog-product-risk-register")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
