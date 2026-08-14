from __future__ import annotations
import csv, hashlib, json
from collections import Counter
from pathlib import Path
OUT=Path("outputs/full_universe_source_acquisition")
INPUT=OUT/"production_scoring_dry_run_v2_scores_v2_25b.csv"
EXPECTED_SHA="4a041712e66034044388dddb0d556c17dbba4bc1a982a6ae7e43d7b57ded5a8f"
def main():
    assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==EXPECTED_SHA
    with INPUT.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    assert len(rows)==33498
    errors=[]; archetypes=Counter()
    for r in rows:
        dq=float(r["data_quality_score"]); sc=float(r["scope_confidence_score"]); pq=float(r["provider_quality_score"])
        score=float(r["dry_run_v2_25b_score"]); rebuilt=round(.70*dq+.20*sc+.10*pq,4)
        errors.append(abs(rebuilt-score)); archetypes[(score,dq,sc,pq,r["score_bucket"])]+=1
    result={"version":"v2.25D","rows":len(rows),"max_formula_reconstruction_error":max(errors),
      "explanation_archetypes":len(archetypes),"mathematically_explainable":True,
      "investment_attractiveness_explainable":False,"production_scoring_authorized":False,
      "scoring_promoted":False,"recommended_next_phase":"v2.25E - Scoring Promotion / Freeze Decision"}
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
