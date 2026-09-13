#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_phase9c_closure_audit_v2_38bx.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bx_phase9c_closure_audit"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "phase9c_closure_audit_summary_v2_38bx.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "phase9c_closure_audit_manifest_v2_38bx.json").read_text(encoding="utf-8"))
    populations = rows(OUT / "phase9c_population_reconciliation_v2_38bx.csv")
    sentinels = rows(OUT / "phase9c_sentinel_cases_v2_38bx.csv")
    guardrails = rows(OUT / "phase9c_guardrail_audit_v2_38bx.csv")
    ui = rows(OUT / "phase9c_ui_readonly_audit_v2_38bx.csv")
    assert summary["qa_status"] == "PASS"
    assert summary["status"] == "COMPLETED_PHASE9C_CLOSURE_AUDIT_EXPERIMENTAL_RANKING_VERIFIED"
    assert summary["main_ranking_count"] == 318
    assert summary["partial_comparability_count"] == 373
    assert summary["review_required_count"] == 124
    assert summary["blocked_count"] == 270
    assert summary["not_yet_scored_count"] == 26
    assert summary["total_assets"] == 1111
    assert all(row["status"] == "PASS" for row in populations + sentinels + guardrails + ui)
    assert {row["case_id"] for row in sentinels} == {"top_ranked_company", "nvidia_partial_no_price", "palantir_partial_no_price", "american_coastal_financial_review", "allegro_luxembourg_no_adapter"}
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
    print("PASS: v2.38BX/quality/real-counts-sentinels-guardrails-manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
