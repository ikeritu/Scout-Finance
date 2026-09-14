#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_local_startup_validation_v2_38cb.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38cb_local_startup_validation"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    summary = json.loads((OUT / "local_startup_validation_summary_v2_38cb.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "local_startup_validation_manifest_v2_38cb.json").read_text(encoding="utf-8"))
    checks = rows(OUT / "local_startup_validation_checks_v2_38cb.csv")
    troubleshooting = (OUT / "LOCAL_STARTUP_TROUBLESHOOTING_v2_38cb.md").read_text(encoding="utf-8")
    assert summary["qa_status"] == "PASS"
    assert summary["status"] in {"LOCAL_STARTUP_VALIDATED_WITH_ENVIRONMENT_WARNINGS", "LOCAL_STARTUP_VALIDATED"}
    assert summary["fail_count"] == 0
    assert summary["main_ranking_count"] == 318
    assert summary["partial_comparability_count"] == 373
    assert summary["review_required_count"] == 124
    assert summary["blocked_count"] == 270
    assert summary["not_yet_scored_count"] == 26
    assert summary["total_assets"] == 1111
    assert summary["startup_bat_validated"] is True
    assert summary["ranking_loader_validated"] is True
    assert summary["troubleshooting_created"] is True
    assert all(row["status"] != "FAIL" for row in checks)
    required_checks = {"app_ast_parseable", "ranking_loader_ast_parseable", "bat_uses_streamlit_run", "ranking_loader_real_json", "bz_status", "ca_status"}
    assert required_checks <= {row["check_id"] for row in checks}
    assert "fatal: not a git repository" in troubleshooting
    assert "C:\\Users\\ikeri" in troubleshooting
    assert "D:\\Proyectos\\💰 Scout Finance" in troubleshooting
    assert "port `8501`" in troubleshooting
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
    print("PASS: v2.38CB/local-startup-validation/dependencies-runner-loader")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
