#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_35c_phase6_final_gate"


def main() -> int:
    report = json.loads((OUT / "scoring_aggregate_report_v2_35c.json").read_text(encoding="utf-8"))
    gate = (OUT / "PHASE6_FINAL_GATE_v2_35c.md").read_text(encoding="utf-8")
    assert report["decision"] == "COMPLETED_SCOPED"
    assert report["input_assets"] == report["assets_with_prices"] == report["assets_with_fundamentals"] == 50
    assert report["ranked_assets"] == 41 and report["partial_comparability_assets"] == 7 and report["review_required_assets"] == 2
    assert len(report["shortlist"]) == 10 and [r["rank"] for r in report["shortlist"]] == list(range(1, 11))
    assert report["deterministic_double_run"] is True and report["phase7_authorized"] is False
    assert {r["asset_id"] for r in report["review_required"]} == {"P020", "P178"}
    assert "FASE 7 PREPARADA PERO NO AUTORIZADA" in gate
    assert "recomendación de inversión" in gate
    print("PASS: v2.35C/phase6-completed-scoped/41-ranked/7-partial/2-review/no-phase7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
