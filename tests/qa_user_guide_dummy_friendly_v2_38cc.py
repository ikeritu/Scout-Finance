#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_user_guide_dummy_friendly_v2_38cc.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cc_user_guide_dummy_friendly"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "user_guide_dummy_friendly_summary_v2_38cc.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "user_guide_dummy_friendly_manifest_v2_38cc.json").read_text(encoding="utf-8"))
    checks = rows(OUT / "user_guide_dummy_friendly_checks_v2_38cc.csv")
    guide = (OUT / "USER_GUIDE_DUMMY_FRIENDLY_v2_38cc.md").read_text(encoding="utf-8")
    faq = (OUT / "USER_GUIDE_FAQ_v2_38cc.md").read_text(encoding="utf-8")
    quick = (OUT / "USER_GUIDE_QUICK_START_v2_38cc.md").read_text(encoding="utf-8")
    assert summary["status"] == "USER_GUIDE_DUMMY_FRIENDLY_READY"
    assert summary["qa_status"] == "PASS"
    assert summary["guide_created"] is True
    assert summary["quick_start_created"] is True
    assert summary["faq_created"] is True
    assert summary["main_ranking_count"] == 318
    assert summary["partial_comparability_count"] == 373
    assert summary["review_required_count"] == 124
    assert summary["blocked_count"] == 270
    assert summary["not_yet_scored_count"] == 26
    assert summary["total_assets"] == 1111
    assert all(row["status"] == "PASS" for row in checks)
    assert "ELIGIBLE_PARTIAL" in guide
    assert "PARTIAL_COMPARABILITY" in guide
    assert "REVIEW_REQUIRED" in guide
    assert "BLOCKED" in guide
    assert "NOT_YET_SCORED_NO_ADAPTER" in guide
    assert "C:\\Users\\ikeri" in faq
    assert "D:\\Proyectos\\💰 Scout Finance" in faq
    assert "run_local_ui_v2_37.bat" in quick
    assert manifest["guardrails"]["scoring_recomputed"] is False
    assert manifest["guardrails"]["network_used"] is False
    assert manifest["guardrails"]["financial_advice_created"] is False
    assert manifest["guardrails"]["broker_actions_allowed"] is False
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    print("PASS: v2.38CC/user-guide-dummy-friendly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
