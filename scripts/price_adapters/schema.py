"""Canonical OHLCV record schema for Scout Finance's multi-source price
architecture (v2.33Q). Every adapter normalizes its provider's raw output
into this shape before anything downstream (validators, reports, manifest)
touches it -- so a validator or report only ever has to understand one
schema, not one per provider.

This module has no network dependency and no side effects; it is pure
data-shape definition plus the normalization contract each adapter must
satisfy. It does not compute anything, score anything, or rank anything.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

# Distinguishes *why* a numeric field has no value -- collapsing these into
# a single None/null would make "we don't have this yet" indistinguishable
# from "this genuinely doesn't apply", which is exactly the kind of
# ambiguity that silently penalizes a company with no fault of its own.
QualityStatus = Literal[
    "ok",  # a real, validated observation
    "no_trade_this_session",  # provider recorded the calendar day but no trade matched (seen in both J-Quants and TWSE data)
    "not_applicable",  # e.g. adjusted_close on a source that never adjusts
    "not_available_by_license",  # the provider has the data but our license/plan doesn't
]

LicenseStatus = Literal[
    "open_government_data",  # e.g. TWSE's Open Government Data License v1.0
    "personal_use_confirmed_in_writing",  # explicit written confirmation obtained
    "personal_use_unconfirmed",  # provider's terms plausibly allow it, not confirmed in writing (e.g. J-Quants pending v2.33N)
    "not_evaluated",
]


@dataclass(frozen=True)
class PriceRecord:
    """One (asset, date) OHLCV observation in the canonical shape."""

    asset_id: str  # this project's internal pilot_id / universe row identifier, never the provider's own id
    provider: str  # e.g. "jquants", "twse_opendata", "eodhd" -- matches the adapter module name
    provider_symbol: str  # the exact identifier passed to the provider's API
    exchange: str
    mic: str | None
    country: str | None
    currency: str | None

    date: str  # ISO 8601, YYYY-MM-DD
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    adjusted_close: float | None
    volume: float | None

    is_adjusted: bool  # whether close/adjusted_close already accounts for splits & dividends
    adjustment_source: str | None  # e.g. "provider_native", "not_available" -- never "estimated" or "simulated"; this project does not fabricate adjustment factors

    retrieved_at: str  # ISO 8601 timestamp of when THIS run fetched the record
    source_window_start: str  # ISO date -- the earliest date this provider/plan combination is confirmed to serve
    source_window_end: str  # ISO date -- the latest date observed in this collection run

    license_status: LicenseStatus
    quality_status: QualityStatus

    def to_dict(self) -> dict:
        return asdict(self)


REQUIRED_FIELDS = tuple(PriceRecord.__dataclass_fields__.keys())


def validate_record_shape(record: dict) -> list[str]:
    """Return a list of problems (empty = valid shape). Does not check
    business rules like OHLC coherence -- that stays in each pilot's own
    validator, which already has provider-specific context (e.g. what a
    provider's own "no trade" sentinel looks like)."""
    problems = []
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        problems.append(f"missing fields: {missing}")
    if "quality_status" in record and record["quality_status"] not in (
        "ok", "no_trade_this_session", "not_applicable", "not_available_by_license"
    ):
        problems.append(f"unknown quality_status: {record['quality_status']!r}")
    if "is_adjusted" in record and record["is_adjusted"] and record.get("adjustment_source") in (None, "", "not_available"):
        problems.append("is_adjusted=True but adjustment_source does not name a real source")
    return problems
