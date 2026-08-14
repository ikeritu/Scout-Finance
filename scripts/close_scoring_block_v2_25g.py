from __future__ import annotations
import json
from pathlib import Path
OUT=Path("outputs/full_universe_source_acquisition")
FILES=[
 OUT/"production_scoring_readiness_gate_v2_25a.json",
 OUT/"production_scoring_dry_run_v2_v2_25b.json",
 OUT/"score_stability_audit_v2_25c.json",
 OUT/"score_explainability_v2_25d.json",
 OUT/"scoring_promotion_freeze_decision_v2_25e.json",
 OUT/"operational_scoring_pointer_hardening_v2_25f.json"]
def main():
    docs=[json.loads(p.read_text(encoding="utf-8")) for p in FILES]
    summaries=[d.get("summary",d) for d in docs]
    assert all(s["critical_failed_checks"]==0 for s in summaries)
    assert all(s["production_scoring_authorized"] is False for s in summaries)
    assert all(s["scoring_promoted"] is False for s in summaries)
    pointer=json.loads((OUT/"current_operational_scoring_pointer.json").read_text(encoding="utf-8"))
    assert pointer["active_scoring_available"] is False and pointer["active_scoring_artifact"] is None
    result={"version":"v2.25G","status":"SCORING_BLOCK_V2_25_CLOSED_FROZEN_NO_PRODUCTION_SCORING",
      "critical_failed_checks":0,"production_scoring_authorized":False,"scoring_promoted":False,
      "recommended_next_phase":"v2.26A - Universe Refresh Policy"}
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
