"""Normalizer: TWSE official STOCK_DAY raw collection (v2.33I) -> canonical
PriceRecord. Same principle as the J-Quants adapter: no network code here,
only shape translation. TWSE's own endpoint never adjusts for splits or
dividends, so every record from this adapter is is_adjusted=False,
adjustment_source="not_available" -- explicit, not a silent gap.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .schema import PriceRecord

PROVIDER = "twse_opendata"
LICENSE_STATUS = "open_government_data"


def normalize_file(path: Path) -> list[PriceRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pilot = payload["pilot"]
    retrieved_at = datetime.now(timezone.utc).isoformat()
    dates = [row["Date"] for row in payload["prices"]]
    window_start = min(dates) if dates else ""
    window_end = max(dates) if dates else ""
    records = []
    for row in payload["prices"]:
        no_trade = row.get("Open") is None
        records.append(PriceRecord(
            asset_id=pilot["pilot_id"],
            provider=PROVIDER,
            provider_symbol=pilot.get("ticker", ""),
            exchange="TWSE",
            mic=None,
            country="TW",
            currency="TWD",
            date=row["Date"],
            open=row.get("Open"),
            high=row.get("High"),
            low=row.get("Low"),
            close=row.get("Close"),
            adjusted_close=None,
            volume=row.get("Volume_shares"),
            is_adjusted=False,
            adjustment_source="not_available",
            retrieved_at=retrieved_at,
            source_window_start=window_start,
            source_window_end=window_end,
            license_status=LICENSE_STATUS,
            quality_status="no_trade_this_session" if no_trade else "ok",
        ))
    return records


def normalize_collection(raw_dir: Path) -> list[PriceRecord]:
    records = []
    for path in sorted(raw_dir.glob("P*.json")):
        records.extend(normalize_file(path))
    return records
