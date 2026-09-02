#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_sec_fundamental_normalization_contract_v1.json"
SCHEMA = ROOT / "schemas/us_sec_fundamental_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38F-us-sec-fundamental-normalization"
    assert contract["expected_us_rows"] == 9200
    assert contract["expected_us_eligible"] == 5011
    assert contract["expected_cik_resolved"] >= 4896
    assert set(contract["allowed_metrics"]) == set(schema["properties"]["metric"]["enum"])
    forbidden = set(contract["forbidden_actions"])
    assert {"network", "raw_sec_json_in_git", "scoring", "ranking", "recommendations", "predictions", "phase9c"} <= forbidden
    assert schema["additionalProperties"] is False
    assert "quality_flags" in schema["required"]
    print("PASS: v2.38F/schema/contract/SEC-fundamental-records/no-scoring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
