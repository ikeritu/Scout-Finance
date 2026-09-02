#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/us_price_history_acquisition_contract_v1.json"
SCHEMA = ROOT / "schemas/us_price_history_record_v1.schema.json"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert contract["phase"] == "v2.38I-us-price-history-acquisition"
    assert contract["batch_limit_max"] == 250
    assert "twelvedata" in contract["allowed_providers"]
    forbidden = set(contract["forbidden_actions"])
    assert {"scoring", "ranking", "recommendations", "predictions", "phase9c", "broker", "trading", "secret_publication", "raw_price_cache_in_git"} <= forbidden
    assert schema["additionalProperties"] is False
    assert {"date", "close", "provider", "provider_symbol"} <= set(schema["required"])
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert contract["raw_cache"] + "/" in gitignore
    print("PASS: v2.38I/contract/schema/gitignore/closed-guardrails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
