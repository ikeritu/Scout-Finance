#!/usr/bin/env python3
"""Snapshot QA for the supervised v2.31D live-provider probe."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 from src.ui_v2_28.adapters import MAINTENANCE_REPORT,build_app_state
 expected="outputs/full_universe_source_acquisition/v2_31d_live_provider_probe/probe_report.json";assert MAINTENANCE_REPORT==expected
 r=json.loads((ROOT/expected).read_text(encoding="utf-8"));rows=r["provider_results"]
 assert len(rows)==14 and sum(x["operational_rows"] for x in rows)==43089
 assert all(x["result"].startswith("REACHABLE") for x in rows)
 assert sum(x["probe_mode"]=="DIRECT_MACHINE_READABLE" for x in rows)==4
 assert r["summary"]["unavailable_routes"]==0 and r["summary"]["blocking_incidents"]==0
 assert r["hard_guards"]["candidate_materialized"] is False and r["hard_guards"]["automated_promotion_allowed"] is False
 state=build_app_state(ROOT);assert state.maintenance.providers_complete==14 and state.maintenance.missing_rows==0 and not state.scoring.allow_ranking
 print("PASS: v2.31D/14-of-14-routes/43089-covered/4-direct/10-official-page/0-incidents/no-candidate/fail-closed")
 return 0
if __name__=="__main__":raise SystemExit(main())
