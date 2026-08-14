from __future__ import annotations
import json
from pathlib import Path
OUT=Path("outputs/full_universe_source_acquisition")
POLICY=OUT/"universe_refresh_policy_v2_26a.json"
def main():
    p=json.loads(POLICY.read_text(encoding="utf-8"))
    assert p["operational_identity_rows"]==p["metadata_comparison_rows"]==43089
    assert sum(x["baseline_rows"] for x in p["provider_cadence_registry"])==43089
    assert len(p["provider_cadence_registry"])==14
    assert [x["stage"] for x in p["lifecycle"] if x["pointer_write_allowed"]]==["ATOMIC_POINTER_SWAP"]
    assert p["production_scoring_authorized"] is False and p["scoring_promoted"] is False
    assert p["operational_pointer_modified"] is False and p["refresh_executed"] is False
    print(json.dumps({"valid":True,"status":p["status"],"critical_failed_checks":p["critical_failed_checks"],
      "recommended_next_phase":p["recommended_next_phase"]},indent=2))
if __name__=="__main__": main()
