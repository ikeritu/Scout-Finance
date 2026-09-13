#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_product_readiness_gate_v2_38bz.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bz_product_readiness_gate"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "product_readiness_gate_summary_v2_38bz.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "product_readiness_gate_manifest_v2_38bz.json").read_text(encoding="utf-8"))
    checks = rows(OUT / "product_readiness_gate_checks_v2_38bz.csv")
    limitations = rows(OUT / "product_readiness_gate_limitations_v2_38bz.csv")
    assert summary["qa_status"] == "PASS"
    assert summary["status"] == "PRODUCT_READINESS_PASS_WITH_LIMITATIONS"
    assert summary["decision"] == "usable_for_local_research_with_limitations"
    assert summary["main_ranking_count"] == 318
    assert summary["partial_comparability_count"] == 373
    assert summary["review_required_count"] == 124
    assert summary["blocked_count"] == 270
    assert summary["not_yet_scored_count"] == 26
    assert summary["total_assets"] == 1111
    assert summary["limitations_count"] == 8
    assert all(row["status"] == "PASS" for row in checks)
    assert len(limitations) == 8
    assert all(row["blocks_local_research_use"] == "false" for row in limitations)
    assert all(row["blocks_financial_advice_or_broker_use"] == "true" for row in limitations)
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
    print("PASS: v2.38BZ/product-readiness-gate/pass-with-limitations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
