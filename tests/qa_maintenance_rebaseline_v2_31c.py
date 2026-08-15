#!/usr/bin/env python3
"""Maintenance baseline and alert gate for v2.31C."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha256(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def main():
 from src.ui_v2_28.adapters import MAINTENANCE_REPORT,build_app_state
 expected="outputs/full_universe_source_acquisition/v2_31c_maintenance_rebaseline/maintenance_report.json"
 assert MAINTENANCE_REPORT==expected
 report=json.loads((ROOT/expected).read_text(encoding="utf-8"))
 blocking=[a for a in report["alerts"] if a["id"].startswith("P")];pending=[a for a in report["alerts"] if a["state"].startswith("PENDING")]
 assert len(blocking)==10 and all(a["state"]=="OK" for a in blocking) and len(pending)==1 and pending[0]["id"]=="A01"
 state=build_app_state(ROOT);assert state.maintenance.providers_complete==14 and state.maintenance.providers_expected==14 and state.maintenance.missing_rows==0
 pointer=json.loads((ROOT/"outputs/full_universe_source_acquisition/current_operational_universe_pointer.json").read_text(encoding="utf-8"))
 dataset=ROOT/str(pointer["current_dataset"]).replace("\\","/");assert sha256(dataset)==pointer["current_dataset_sha256"]
 assert not state.scoring.allow_ranking and report["hard_guards"]["automated_promotion_allowed"] is False
 print("PASS: v2.31C/10-blocking-green/14-of-14/0-missing/1-advisory-pending/no-pointer-change/fail-closed")
 return 0
if __name__=="__main__":raise SystemExit(main())
