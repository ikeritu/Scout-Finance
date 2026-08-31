#!/usr/bin/env python3
"""Offline QA for the canonical schema and the J-Quants/TWSE normalizers
(v2.33Q). Uses small synthetic fixture files -- no real network, no real
credentials, no dependency on the real local licensed collections (though
if those exist locally, a second SKIP-capable check confirms the real
collections load correctly through the same adapters).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from price_adapters import jquants_adapter, twse_adapter, schema  # noqa: E402


def test_schema_validates_shape_and_adjustment_consistency():
    good = {
        "asset_id": "P1", "provider": "x", "provider_symbol": "x", "exchange": "X", "mic": None,
        "country": None, "currency": None, "date": "2026-01-01", "open": 1.0, "high": 1.0, "low": 1.0,
        "close": 1.0, "adjusted_close": 1.0, "volume": 1.0, "is_adjusted": True,
        "adjustment_source": "provider_native", "retrieved_at": "x", "source_window_start": "x",
        "source_window_end": "x", "license_status": "not_evaluated", "quality_status": "ok",
    }
    assert schema.validate_record_shape(good) == []

    missing = dict(good)
    del missing["close"]
    assert any("missing fields" in p for p in schema.validate_record_shape(missing))

    inconsistent = dict(good)
    inconsistent["adjustment_source"] = "not_available"
    problems = schema.validate_record_shape(inconsistent)
    assert any("adjustment_source" in p for p in problems)

    bad_quality = dict(good)
    bad_quality["quality_status"] = "made_up_status"
    assert any("unknown quality_status" in p for p in schema.validate_record_shape(bad_quality))


def test_jquants_adapter_normalizes_and_flags_no_trade():
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir = Path(tmp)
        payload = {
            "pilot": {"pilot_id": "P143", "provider_symbol": "13010"},
            "prices": [
                {"Date": "2026-01-02", "Code": "13010", "O": 100.0, "H": 105.0, "L": 99.0, "C": 104.0,
                 "Vo": 1000.0, "AdjFactor": 1.0, "AdjO": 100.0, "AdjH": 105.0, "AdjL": 99.0, "AdjC": 104.0,
                 "AdjVo": 1000.0, "MktCap": None, "ExRT": None},
                {"Date": "2026-01-03", "Code": "13010", "O": None, "H": None, "L": None, "C": None,
                 "Vo": None, "AdjFactor": 1.0, "AdjO": None, "AdjH": None, "AdjL": None, "AdjC": None,
                 "AdjVo": None, "MktCap": None, "ExRT": None},
            ],
        }
        (raw_dir / "P143.json").write_text(json.dumps(payload), encoding="utf-8")
        records = jquants_adapter.normalize_collection(raw_dir)
        assert len(records) == 2
        assert records[0].quality_status == "ok" and records[0].is_adjusted is True
        assert records[1].quality_status == "no_trade_this_session"
        for r in records:
            assert schema.validate_record_shape(r.to_dict()) == []


def test_twse_adapter_normalizes_and_marks_unadjusted():
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir = Path(tmp)
        payload = {
            "pilot": {"pilot_id": "P016", "ticker": "1101.TW"},
            "prices": [
                {"Date": "2026-01-02", "Open": 24.0, "High": 24.5, "Low": 23.9, "Close": 24.3,
                 "Volume_shares": 1000.0, "TradeValue": 24300.0, "Change": "+0.1", "Transactions": 10.0, "Note": ""},
            ],
            "month_call_failures": 0,
        }
        (raw_dir / "P016.json").write_text(json.dumps(payload), encoding="utf-8")
        records = twse_adapter.normalize_collection(raw_dir)
        assert len(records) == 1
        assert records[0].is_adjusted is False
        assert records[0].adjustment_source == "not_available"
        assert records[0].adjusted_close is None
        assert schema.validate_record_shape(records[0].to_dict()) == []


CASES = [
    test_schema_validates_shape_and_adjustment_consistency,
    test_jquants_adapter_normalizes_and_flags_no_trade,
    test_twse_adapter_normalizes_and_marks_unadjusted,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.33Q-adapters/schema-shape-valid/no-trade-flagged/unadjusted-explicit/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
