#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit"


def main() -> int:
    rows = list(csv.DictReader((OUTPUT / "provider_route_matrix_v2_38a.csv").open(encoding="utf-8", newline="")))
    by_exchange = {r["exchange"]: r for r in rows}
    assert len(rows) == 15 and sum(int(r["rows"]) for r in rows) == 43089
    assert by_exchange["JPX"]["route_status"] == "PILOT_VALIDATED_NOT_SCALED"
    assert by_exchange["TWSE"]["license_status"] == "open_government_data"
    assert by_exchange["CBOE_EUROPE"]["route_status"] == "EXCLUDED_NO_ACTIONABLE_SOURCE"
    assert by_exchange["ASX"]["route_status"] == "EXCLUDED_NO_FREE_SOURCE"
    assert all(r["network_calls"] == "0" and r["limitation"] for r in rows)
    manifest = json.loads((OUTPUT / "global_universe_manifest_v2_38a.json").read_text(encoding="utf-8"))
    assert manifest["decision"] == "COMPLETED_GLOBAL_CENSUS_READY_FOR_SOURCE_PLANNING"
    assert manifest["guardrails"] == {"allow_ranking": False, "credentials_used": False, "network_calls": 0, "phase9b_authorized": False, "production_scoring_authorized": False}
    print("PASS: v2.38A/routes/15-markets/license-limitations/no-network/no-phase9b")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
