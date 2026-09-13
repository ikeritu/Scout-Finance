#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_ranking_ux_hardening_v2_38by.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38by_ranking_ux_hardening"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "ranking_ux_hardening_summary_v2_38by.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "ranking_ux_hardening_manifest_v2_38by.json").read_text(encoding="utf-8"))
    checks = rows(OUT / "ranking_ux_hardening_checks_v2_38by.csv")
    assert summary["qa_status"] == "PASS"
    assert summary["status"] == "COMPLETED_RANKING_UX_HARDENING_READ_ONLY"
    assert summary["main_ranking_count"] == 318
    assert summary["partial_comparability_count"] == 373
    assert summary["review_required_count"] == 124
    assert summary["blocked_count"] == 270
    assert summary["not_yet_scored_count"] == 26
    assert summary["total_assets"] == 1111
    assert all(row["status"] == "PASS" for row in checks)
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
    print("PASS: v2.38BY/builder-summary-manifest-guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
