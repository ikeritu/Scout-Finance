from __future__ import annotations
import csv, hashlib, json, math
from collections import Counter, defaultdict
from pathlib import Path

VERSION="v2.25C"
OUT=Path("outputs/full_universe_source_acquisition")
INPUT=OUT/"production_scoring_dry_run_v2_scores_v2_25b.csv"
EXPECTED_SHA="4a041712e66034044388dddb0d556c17dbba4bc1a982a6ae7e43d7b57ded5a8f"
def bucket(x):
    return "A" if x>=85 else "B" if x>=70 else "C" if x>=55 else "D" if x>=40 else "E"
def corr(a,b):
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    ab=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    aa=sum((x-ma)**2 for x in a); bb=sum((y-mb)**2 for y in b)
    return ab/math.sqrt(aa*bb)
def main():
    assert hashlib.sha256(INPUT.read_bytes()).hexdigest()==EXPECTED_SHA
    with INPUT.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    assert len(rows)==33498
    old=[float(r["reference_v2_23d_score"]) for r in rows]
    new=[float(r["dry_run_v2_25b_score"]) for r in rows]
    delta=[b-a for a,b in zip(old,new)]
    migration=Counter((bucket(a),bucket(b)) for a,b in zip(old,new))
    summary={"rows":len(rows),"pearson_score_correlation":round(corr(old,new),6),
      "changed_rows":sum(x!=0 for x in delta),"positive_delta_rows":sum(x>0 for x in delta),
      "negative_delta_rows":sum(x<0 for x in delta),
      "same_bucket_rows":sum(bucket(a)==bucket(b) for a,b in zip(old,new)),
      "bucket_changed_rows":sum(bucket(a)!=bucket(b) for a,b in zip(old,new)),
      "production_scoring_authorized":False,"scoring_promoted":False,
      "recommended_next_phase":"v2.25D - Score Explainability Report"}
    print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
