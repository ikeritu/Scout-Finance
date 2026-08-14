from __future__ import annotations
import csv, hashlib, json
from collections import defaultdict
from pathlib import Path
OUT=Path("outputs/full_universe_source_acquisition")
BASE=OUT/"expanded_universe_v2_24f_metadata_promoted.csv"
CANDIDATE_REF=OUT/"provider_refresh_dry_run_candidate_reference_v2_26b.json"
EXPECTED_SHA="01fef82316a458c65d42c08cb993feed9e0cc8178f4f7bf4f08835f169bfa74c"
def norm(v): return (v or "").strip().upper()
def identity(r):
    if norm(r.get("isin")):
        return "ISIN|%s|%s|%s"%(norm(r.get("isin")),norm(r.get("exchange")),norm(r.get("ticker")))
    if norm(r.get("ticker")):
        return "PETIS|%s|%s|%s|%s|%s"%(norm(r.get("source_provider")),norm(r.get("exchange")),norm(r.get("ticker")),norm(r.get("instrument_id")),norm(r.get("symbol")))
    return "PEIS|%s|%s|%s|%s"%(norm(r.get("source_provider")),norm(r.get("exchange")),norm(r.get("instrument_id")),norm(r.get("symbol")))
def index(rows):
    out=defaultdict(list)
    for r in rows: out[identity(r)].append(r)
    return out
def compare(base,candidate):
    bi,ci=index(base),index(candidate)
    conflicts=sorted(k for k,v in ci.items() if len(v)!=1 or len(bi.get(k,[]))>1)
    added=sorted(set(ci)-set(bi)); removed=sorted(set(bi)-set(ci))
    modified=[]; unchanged=0
    for k in sorted(set(bi)&set(ci)-set(conflicts)):
        b,c=bi[k][0],ci[k][0]
        changes={f:(b.get(f,""),c.get(f,"")) for f in b if b.get(f,"")!=c.get(f,"")}
        if changes: modified.append((k,changes))
        else: unchanged+=1
    return {"added":added,"removed":removed,"modified":modified,"conflicts":conflicts,"unchanged":unchanged}
def main():
    ref=json.loads(CANDIDATE_REF.read_text(encoding="utf-8"))
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==EXPECTED_SHA==ref["candidate_sha256"]
    with BASE.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    result=compare(rows,rows)
    assert len(rows)==43089 and not any(result[k] for k in ["added","removed","modified","conflicts"])
    assert result["unchanged"]==43089
    print(json.dumps({"valid":True,"status":"ZERO_DELTA_REPLAY_CONTROL","unchanged":43089,
      "recommended_next_phase":"v2.26D - Rollback Validation"},indent=2))
if __name__=="__main__": main()
