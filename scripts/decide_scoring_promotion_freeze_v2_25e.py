from __future__ import annotations
import hashlib, json
from pathlib import Path
OUT=Path("outputs/full_universe_source_acquisition")
INPUTS={
 "readiness":OUT/"production_scoring_readiness_gate_v2_25a.json",
 "dry_run":OUT/"production_scoring_dry_run_v2_v2_25b.json",
 "stability":OUT/"score_stability_audit_v2_25c.json",
 "explainability":OUT/"score_explainability_v2_25d.json"}
EXPECTED_SCORES_SHA="4a041712e66034044388dddb0d556c17dbba4bc1a982a6ae7e43d7b57ded5a8f"
def main():
    docs={k:json.loads(p.read_text(encoding="utf-8")) for k,p in INPUTS.items()}
    a=docs["readiness"]["summary"]; b=docs["dry_run"]["summary"]; c=docs["stability"]; d=docs["explainability"]
    assert a["production_scoring_authorized"] is False and b["scoring_promoted"] is False
    assert c["stability_promotion_ready"] is False and d["explainability_promotion_ready"] is False
    score_path=OUT/"production_scoring_dry_run_v2_scores_v2_25b.csv"
    assert hashlib.sha256(score_path.read_bytes()).hexdigest()==EXPECTED_SCORES_SHA
    decision={"version":"v2.25E","status":"SCORING_FROZEN_NO_PRODUCTION_PROMOTION",
      "decision":"FREEZE_CURRENT_FORMULA_AS_DATA_READINESS_DIAGNOSTIC",
      "production_scoring_authorized":False,"scoring_promoted":False,
      "diagnostic_score_role":"DATA_READINESS_ONLY",
      "recommended_next_phase":"v2.25F - Operational Scoring Pointer Hardening"}
    print(json.dumps(decision,indent=2))
if __name__=="__main__": main()
