#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_price_history_acquisition_plan_v2_38o.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("phase9o_plan", SCRIPT)
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
        base = Path(tmp)
        resolution = base / "resolution.csv"
        out = base / "out"
        raw = base / "raw"
        resolution.write_text(
            "\n".join([
                "asset_id,ticker,company_name,country,currency,exchange,mic,inferred_region,source_provider,home_exchange,home_mic,home_country,home_currency,listing_role,resolution_status,provider_route,provider_route_status,evidence_source,evidence_strength,review_reason,phase,scoring_calculated,ranking_calculated,recommendations_generated,phase9c_authorized",
                "U20001,ABC,Alpha AG,DE,EUR,XETR,XETR,EUROPE,fixture,XETRA,XETR,DE,EUR,PRIMARY_HOME_EXCHANGE,HOME_EXCHANGE_RESOLVED,stooq_daily_prices,READY_FOR_PRICE_HISTORY_PILOT,fixture,HIGH,,v2.38N-europe-home-exchange-resolution,false,false,false,false",
                "U20002,CBOEd,Beta Plc,,,,EUROPE,cboe_europe_reference_data,,,,,SECONDARY_CBOE_EUROPE,CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED,exchange_official_reference,BLOCKED_HOME_EXCHANGE_REQUIRED,fixture,HIGH,,v2.38N-europe-home-exchange-resolution,false,false,false,false",
            ]) + "\n",
            encoding="utf-8",
        )
        report = builder.build(resolution, out, raw, None)
        assert report["candidates_total"] == 1
        assert report["pending_assets"] == 1
        plan = rows(out / "europe_price_history_acquisition_plan_v2_38o.csv")
        assert len(plan) == 1
        assert plan[0]["asset_id"] == "U20001"
        assert plan[0]["provider"] == "stooq"
        assert plan[0]["provider_symbol"] == "abc.de"
        assert plan[0]["collection_status"] == "READY_FOR_COLLECTION"
        assert plan[0]["recommendations_generated"] == "false"
        raw.mkdir()
        cache = raw / "U20001.csv"
        cache.write_text(
            "date,open,high,low,close,adjusted_close,volume,provider,provider_symbol,home_exchange,home_mic,home_currency\n"
            + "".join(f"2025-01-{(i % 28) + 1:02d},1,1,1,1,1,1,stooq,abc.de,XETRA,XETR,EUR\n" for i in range(130)),
            encoding="utf-8",
        )
        report2 = builder.build(resolution, out, raw, None)
        plan2 = rows(out / "europe_price_history_acquisition_plan_v2_38o.csv")
        assert report2["collected_assets"] == 1
        assert plan2[0]["collection_status"] == "COLLECTED"
    print("PASS: v2.38O/plan/deterministic/home-exchange-only/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
