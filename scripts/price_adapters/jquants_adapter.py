"""Normalizer: J-Quants raw collection (v2.33G) -> canonical PriceRecord.

Reads the already-downloaded local JSON files from v2.33G (never re-fetches
anything -- this adapter has no network code at all, on purpose: fetching is
the pilot script's job, normalizing is this module's job). Kept separate so
a validator or the future coverage manifest can consume J-Quants data
without knowing anything about J-Quants' field abbreviations (O/H/L/C/Vo).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .schema import PriceRecord

PROVIDER = "jquants"
LICENSE_STATUS = "personal_use_unconfirmed"  # see v2.33N: not yet confirmed in writing


def normalize_file(path: Path) -> list[PriceRecord]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pilot = payload["pilot"]
    retrieved_at = datetime.now(timezone.utc).isoformat()
    records = []
    for row in payload["prices"]:
        no_trade = row.get("O") is None
        records.append(PriceRecord(
            asset_id=pilot["pilot_id"],
            provider=PROVIDER,
            provider_symbol=pilot.get("provider_symbol", ""),
            exchange="JPX",
            mic=None,
            country="JP",
            currency="JPY",
            date=row["Date"],
            open=row.get("O"),
            high=row.get("H"),
            low=row.get("L"),
            close=row.get("C"),
            adjusted_close=row.get("AdjC"),
            volume=row.get("Vo"),
            is_adjusted=row.get("AdjC") is not None,
            adjustment_source="provider_native" if row.get("AdjC") is not None else "not_available",
            retrieved_at=retrieved_at,
            source_window_start="2024-06-08",
            source_window_end="2026-06-08",
            license_status=LICENSE_STATUS,
            quality_status="no_trade_this_session" if no_trade else "ok",
        ))
    return records


def normalize_collection(raw_dir: Path) -> list[PriceRecord]:
    records = []
    for path in sorted(raw_dir.glob("P*.json")):
        records.extend(normalize_file(path))
    return records
