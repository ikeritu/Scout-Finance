#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_final_operational_publication_v2_38cj.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cj_final_operational_publication"
REQUIRED_OUTPUTS = [
    "final_handoff_matrix_v2_38cj.csv",
    "final_operational_checklist_v2_38cj.csv",
    "final_operational_publication_summary_v2_38cj.json",
    "final_operational_publication_manifest_v2_38cj.json",
    "FINAL_OPERATIONAL_PUBLICATION_v2_38cj.md",
    "README.md",
]
FORBIDDEN_POSITIVE_ADVICE = re.compile(r"\b(strong buy|price target|target price|automatic trading signal)\b", re.IGNORECASE)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    for name in REQUIRED_OUTPUTS:
        assert (OUT / name).exists(), name
    summary = json.loads((OUT / "final_operational_publication_summary_v2_38cj.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "final_operational_publication_manifest_v2_38cj.json").read_text(encoding="utf-8"))
    matrix = rows(OUT / "final_handoff_matrix_v2_38cj.csv")
    checklist = rows(OUT / "final_operational_checklist_v2_38cj.csv")
    report = (OUT / "FINAL_OPERATIONAL_PUBLICATION_v2_38cj.md").read_text(encoding="utf-8")
    assert summary["phase"] == "v2.38CJ-final-operational-publication"
    assert summary["status"] == "FINAL_OPERATIONAL_PUBLICATION_READY_WITH_DOCUMENTED_LIMITATIONS"
    assert summary["cycle_status"] == "V2_38_LOCAL_CYCLE_CLOSED"
    assert summary["publication_scope"] == "local_research_tool_only"
    assert summary["final_publication_declared"] is True
    assert summary["qa_status"] == "PASS"
    assert summary["fail_count"] == 0
    assert summary["warn_count"] == 0
    assert summary["blocking_issue_count"] == 0
    assert summary["documented_limitation_count"] > 0
    assert summary["ranking_total"] == 1111
    assert summary["ranking_main_count"] == 318
    assert summary["ranking_partial_count"] == 373
    assert summary["ranking_review_required_count"] == 124
    assert summary["ranking_blocked_count"] == 270
    assert summary["ranking_no_adapter_count"] == 26
    for key in ["network_used", "scoring_recomputed", "weights_changed", "ranking_changed", "methodology_changed", "datasets_mutated", "ui_changed", "financial_advice_created", "recommendations_created", "broker_actions_allowed"]:
        assert summary[key] is False, key
    assert all(row["status"] == "PASS" for row in matrix)
    assert len(checklist) >= 8
    for phrase in ["herramienta local de investigacion", "not financial advice", "does not create recommendations", "does not include a broker workflow", "closes the local v2.38 cycle"]:
        assert phrase in report
    assert not FORBIDDEN_POSITIVE_ADVICE.search(report)
    assert manifest["outputs"]
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CJ/final-operational-publication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
