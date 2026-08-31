"""Normalizer: TWSE MOPS opendata raw snapshot rows -> canonical
FundamentalRecord dicts (block F). Reads only the already-downloaded local
JSON files from block D/E -- no network code here.

Two confirmed facts from v2.34B/v2.34E shape every decision here:
  1. Values in t187ap06_L_ci/t187ap07_L_ci are in THOUSANDS of TWD (verified
     in v2.34D by cross-checking against t187ap17_L's revenue-in-millions
     column: the ratio between the two is ~1000) -- normalized `value` is
     multiplied by 1000 to reach whole TWD, `raw_value`/`raw_scale` keep the
     provider's original thousands figure untouched.
  2. Each snapshot is ONE cumulative period per company (the disclosure
     cycle's running total for the fiscal year to date, per Taiwan's
     standard quarterly disclosure convention) -- this project has not
     independently confirmed with MOPS documentation whether the figures
     are cumulative-to-date or single-quarter-discrete, so every record
     carries a quality_flag noting that assumption rather than presenting
     it as a confirmed fact.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

NORMALIZER_VERSION = "1.0.0"
PROVIDER = "twse_mops_opendata"
THOUSANDS_TO_UNITS = 1000.0
CUMULATIVE_PERIOD_ASSUMPTION_FLAG = "period_cumulative_vs_discrete_unconfirmed"

INCOME_STATEMENT_FIELDS = [
    ("營業收入", "revenue"), ("營業成本", "cost_of_sales"), ("營業毛利（毛損）淨額", "gross_profit"),
    ("營業利益（損失）", "operating_income"), ("稅前淨利（淨損）", "pretax_income"),
    ("本期淨利（淨損）", "net_income"),
]
BALANCE_SHEET_FIELDS = [
    ("流動資產", "current_assets"), ("資產總計", "total_assets"),
    ("流動負債", "current_liabilities"), ("負債總計", "total_liabilities"),
    ("權益總計", "total_equity"),
]


def _record_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _roc_year_to_western(roc_year: str) -> str:
    return str(int(roc_year) + 1911)


QUARTER_END_MONTH_DAY = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}


def _period_end(fiscal_year: str, quarter: int) -> str:
    # Taiwan's fiscal year is the calendar year, so a quarter's calendar
    # end date is fixed -- this is calendar arithmetic, not an assumption
    # about the company's own reporting.
    return f"{fiscal_year}-{QUARTER_END_MONTH_DAY[quarter]}"


def _base_record(asset: dict, row: dict, retrieved_at: str, statement_type: str) -> dict:
    quarter = int(row.get("季別", "0") or 0)
    fiscal_year = _roc_year_to_western(row.get("年度", "0"))
    return {
        "schema_version": "1.0.0",
        "asset_id": asset["pilot_id"],
        "company_id": None,
        "pilot_id": asset["pilot_id"],
        "ticker": asset["ticker"],
        "provider_symbol": asset["provider_symbol_twse"].split(".")[0],
        "provider_record_id": None,
        "company_name": asset.get("company_name", ""),
        "exchange": "TWSE",
        "mic": None,
        "country": "TW",
        "isin": asset.get("isin") or None,
        "provider": PROVIDER,
        "source_url_or_endpoint": "/opendata/t187ap06_L_ci.csv+t187ap07_L_ci.csv",
        "retrieved_at": retrieved_at,
        "normalizer_version": NORMALIZER_VERSION,
        "statement_type": statement_type,
        "period_type": "quarterly",
        "fiscal_year": fiscal_year,
        "fiscal_quarter": quarter or None,
        "period_start": None,
        "period_end": _period_end(fiscal_year, quarter) if quarter in QUARTER_END_MONTH_DAY else fiscal_year + "-12-31",
        "filing_date": None,
        "publication_date": None,
        "restatement_status": "unknown",
        "consolidation_scope": "consolidated",
        "accounting_standard": "unknown",
        "currency": "TWD",
        "raw_currency": "TWD",
        "unit": "currency",
        "scale": "thousands",
        "sign_convention": "natural",
        "value_status": "ok",
        "source_status": "received",
        "normalization_status": "normalized",
        "validation_status": "pending",
        "quality_flags": [CUMULATIVE_PERIOD_ASSUMPTION_FLAG],
        "transformation_notes": "raw_value is the provider's original figure in thousands of TWD; value is raw_value * 1000 (whole TWD), per the scale confirmed in v2.34D.",
    }


def _value_record(base: dict, raw_field: str, metric: str, raw_value: str) -> dict:
    record = dict(base)
    record["metric"] = metric
    record["raw_metric"] = raw_field
    if raw_value in ("", None):
        record["value"] = None
        record["raw_value"] = None
        record["currency"] = None
        record["raw_currency"] = None
        record["missing_reason"] = "not_reported_by_company"
    else:
        try:
            raw_numeric = float(raw_value)
        except ValueError:
            record["value"] = None
            record["raw_value"] = raw_value
            record["missing_reason"] = "incomplete_response"
            record["normalization_status"] = "normalization_error"
            record["record_id"] = _record_id(record["asset_id"], record["provider"], record["statement_type"], record["period_type"], record["fiscal_year"], str(record["fiscal_quarter"]), record["metric"], record["consolidation_scope"])
            return record
        record["raw_value"] = raw_numeric
        record["value"] = raw_numeric * THOUSANDS_TO_UNITS
        record["missing_reason"] = None
    record["record_id"] = _record_id(
        record["asset_id"], record["provider"], record["statement_type"], record["period_type"],
        record["fiscal_year"], str(record["fiscal_quarter"]), record["metric"], record["consolidation_scope"],
    )
    return record


def normalize_file(path: Path) -> list[dict]:
    import json
    payload = json.loads(path.read_text(encoding="utf-8"))
    asset = payload["asset"]
    retrieved_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    snapshot_files = payload["snapshot_files"]

    records = []
    for row in snapshot_files.get("income_statement", []):
        base = _base_record(asset, row, retrieved_at, "income_statement")
        for raw_field, metric in INCOME_STATEMENT_FIELDS:
            records.append(_value_record(base, raw_field, metric, row.get(raw_field, "")))

    for row in snapshot_files.get("balance_sheet", []):
        base = _base_record(asset, row, retrieved_at, "balance_sheet")
        for raw_field, metric in BALANCE_SHEET_FIELDS:
            records.append(_value_record(base, raw_field, metric, row.get(raw_field, "")))

    return records


def normalize_collection(raw_dir: Path) -> list[dict]:
    records = []
    for path in sorted(raw_dir.glob("P*.json")):
        records.extend(normalize_file(path))
    return records
