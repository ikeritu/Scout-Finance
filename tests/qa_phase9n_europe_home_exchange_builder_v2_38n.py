#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_home_exchange_resolution_v2_38n.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("phase9n_builder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    builder = load_builder()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = root / "out"
        census = root / "eu.csv"
        contract = root / "contract.json"
        census.write_text(
            "\n".join([
                "asset_id,ticker,company_name,exchange,mic,country,currency,instrument_type,source_provider,eligibility_status,identity_status,readiness_status,blocker_reason,normalized_exchange_group,home_exchange_candidate,duplicate_group_candidate,home_exchange_status,price_route_status,fundamental_route_status,phase",
                "U10001,ABC,Alpha GmbH,XETR,XETR,DE,,EQTY,deutsche_boerse_xetra_all_tradable_instruments,ELIGIBLE,COMPLETE,EU_SOURCE_REQUIRED,,XETR,,,EU_SOURCE_REQUIRED,EU_SOURCE_REQUIRED,EU_SOURCE_REQUIRED,v2.38C",
                "U10002,ABCd,Alpha GmbH,CBOE_EUROPE,,,,EQTY,cboe_europe_reference_data,ELIGIBLE,COMPLETE,EU_ISIN_MISSING,Cboe Europe requires ISIN/home-exchange mapping,CBOE_EUROPE,,,EU_ISIN_MISSING,EU_SOURCE_REQUIRED,EU_SOURCE_REQUIRED,v2.38C",
                "U10003,ADR,Alpha Receipt,CBOE_EUROPE,,,,DR,cboe_europe_reference_data,ELIGIBLE,COMPLETE,EU_ISIN_MISSING,Cboe Europe requires ISIN/home-exchange mapping,CBOE_EUROPE,,,EU_ISIN_MISSING,EU_SOURCE_REQUIRED,EU_SOURCE_REQUIRED,v2.38C",
            ]) + "\n",
            encoding="utf-8",
        )
        contract.write_text(json.dumps({"input_universe_rows_expected": 43089, "cboe_europe_is_secondary_by_default": True}), encoding="utf-8")
        builder.EU_CENSUS = census
        builder.CONTRACT = contract
        builder.OUT = out
        rc = builder.main()
        assert rc == 0
        built = rows(out / "europe_home_exchange_resolution_v2_38n.csv")
        by_id = {r["asset_id"]: r for r in built}
        assert by_id["U10001"]["resolution_status"] == "HOME_EXCHANGE_RESOLVED"
        assert by_id["U10001"]["home_mic"] == "XETR"
        assert by_id["U10001"]["listing_role"] == "PRIMARY_HOME_EXCHANGE"
        assert by_id["U10002"]["resolution_status"] == "CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED"
        assert by_id["U10002"]["listing_role"] == "SECONDARY_CBOE_EUROPE"
        assert by_id["U10002"]["home_exchange"] == ""
        assert by_id["U10003"]["resolution_status"] == "ADR_GDR_REVIEW_REQUIRED"
        assert all(r["recommendations_generated"] == "false" for r in built)
        second = (out / "europe_home_exchange_resolution_v2_38n.csv").read_text(encoding="utf-8")
        builder.main()
        assert second == (out / "europe_home_exchange_resolution_v2_38n.csv").read_text(encoding="utf-8")
    print("PASS: v2.38N/builder/offline/deterministic/cboe-secondary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
