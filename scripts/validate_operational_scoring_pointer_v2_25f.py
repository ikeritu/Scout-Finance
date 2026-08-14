from __future__ import annotations
import hashlib, json
from pathlib import Path
OUT=Path("outputs/full_universe_source_acquisition")
POINTER=OUT/"current_operational_scoring_pointer.json"
EXPECTED_DIAGNOSTIC_SHA="4a041712e66034044388dddb0d556c17dbba4bc1a982a6ae7e43d7b57ded5a8f"
def validate(pointer):
    assert pointer["schema_version"]=="1.0"
    assert pointer["status"]=="NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED"
    assert pointer["active_scoring_available"] is False
    assert pointer["active_scoring_artifact"] is None and pointer["active_scoring_sha256"] is None
    assert pointer["production_scoring_authorized"] is False and pointer["scoring_promoted"] is False
    diagnostic=pointer["diagnostic_artifact"]
    assert diagnostic["role"]=="DATA_READINESS_ONLY" and diagnostic["production_eligible"] is False
    path=Path(diagnostic["path"])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==EXPECTED_DIAGNOSTIC_SHA
    assert pointer["consumer_contract"]["default_behavior"]=="FAIL_CLOSED"
    return {"valid":True,"operational_result":"SCORING_UNAVAILABLE","production_scoring_authorized":False}
def main():
    print(json.dumps(validate(json.loads(POINTER.read_text(encoding="utf-8"))),indent=2))
if __name__=="__main__": main()
