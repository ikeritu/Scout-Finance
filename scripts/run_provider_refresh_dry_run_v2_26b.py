from __future__ import annotations
import json
from pathlib import Path
OUT=Path("outputs/full_universe_source_acquisition")
REPORT=OUT/"provider_refresh_dry_run_v2_26b.json"
def main():
    r=json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(r["provider_results"])==14
    assert sum(x["baseline_rows"] for x in r["provider_results"])==43089
    replay=[x for x in r["provider_results"] if x["execution_mode"]=="REPOSITORY_ARTIFACT_REPLAY"]
    assert len(replay)==13 and sum(x["baseline_rows"] for x in replay)==41076
    assert all(x["threshold_result"]=="PASS" for x in replay)
    c=r["candidate_reference"]
    assert c["candidate_sha256"]==c["comparison_sha256"]
    assert c["promotion_eligible"] is False and r["operational_pointer_modified"] is False
    print(json.dumps({"valid":True,"status":r["status"],"replayed_provider_buckets":13,
      "live_freshness_verified":False,"recommended_next_phase":r["recommended_next_phase"]},indent=2))
if __name__=="__main__": main()
