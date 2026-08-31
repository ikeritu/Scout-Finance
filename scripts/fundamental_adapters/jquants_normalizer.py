"""Normalizer: J-Quants /v2/fins/summary raw disclosures -> canonical
FundamentalRecord dicts (block F). Reads only the already-downloaded local
JSON files from block D/E -- no network code here, on purpose, mirroring
the phase-4 price_adapters split between fetching and normalizing.

Two things this normalizer explicitly does NOT do, both grounded in real
findings from v2.34E:
  1. It skips "EarnForecastRevision" and "DividendForecastRevision"
     disclosures entirely. These are the provider's own forward guidance,
     not a financial statement -- every actual/reported field is blank on
     them, and phase 5 forbids representing forecasts as reported data
     (value_status="estimated" is banned per rule 3.1).
  2. It never invents a value for a blank field. A blank string in the
     provider's JSON becomes value=None + an explicit missing_reason, never
     0 and never an inferred number.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

NORMALIZER_VERSION = "1.0.0"
PROVIDER = "jquants_fins_summary"
SKIPPED_DOC_TYPES = {"EarnForecastRevision", "DividendForecastRevision"}

PERIOD_TYPE_BY_CUR_PER_TYPE = {"1Q": "quarterly", "2Q": "quarterly", "3Q": "quarterly", "FY": "annual"}
FISCAL_QUARTER_BY_CUR_PER_TYPE = {"1Q": 1, "2Q": 2, "3Q": 3, "FY": None}

# (raw field, canonical metric) for the primary (consolidated-book) columns.
# The "NC"-prefixed columns mirror the same metrics for the non-consolidated
# book and are handled separately below.
CURRENCY_METRIC_FIELDS = [
    ("Sales", "revenue"), ("OP", "operating_income"),
    ("OdP", "ordinary_income"), ("NP", "net_income"),
    ("TA", "total_assets"), ("CashEq", "cash_and_equivalents"),
    ("CFO", "operating_cash_flow"), ("CFI", "investing_cash_flow"),
    ("CFF", "financing_cash_flow"),
]
EQUITY_METRIC_FIELDS = [("Eq", "total_equity"), ("ShEq", "total_equity")]  # both name the same concept; Eq preferred, ShEq fallback
PER_SHARE_METRIC_FIELDS = [("EPS", "eps_basic"), ("DEPS", "eps_diluted"), ("BPS", "book_value_per_share")]
RATIO_METRIC_FIELDS = [("EqAR", "equity_ratio_reported"), ("ROE", "roe_reported")]
SHARE_COUNT_METRIC_FIELDS = [("ShOutFY", "shares_outstanding"), ("AvgSh", "shares_outstanding")]
DIVIDEND_FIELDS = ["Div1Q", "Div2Q", "Div3Q", "DivFY", "DivAnn"]

NC_CURRENCY_METRIC_FIELDS = [("NCSales", "revenue"), ("NCOP", "operating_income"), ("NCOdP", "ordinary_income"), ("NCNP", "net_income"), ("NCTA", "total_assets")]
NC_EQUITY_METRIC_FIELDS = [("NCEq", "total_equity"), ("NCShEq", "total_equity")]
NC_PER_SHARE_METRIC_FIELDS = [("NCEPS", "eps_basic"), ("NCBPS", "book_value_per_share")]
NC_RATIO_METRIC_FIELDS = [("NCEqAR", "equity_ratio_reported"), ("NCROE", "roe_reported")]


def _record_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _restatement_status(disclosure: dict) -> str:
    flags = [disclosure.get(f, "") for f in ("ChgByASRev", "ChgNoASRev", "ChgAcEst", "RetroRst")]
    if not any(flags):
        return "unknown"
    return "restated" if any(f == "true" for f in flags) else "original"


def _accounting_standard(doc_type: str) -> str:
    if doc_type.endswith("_JP"):
        return "JGAAP"
    if doc_type.endswith("_IFRS"):
        return "IFRS"
    if doc_type.endswith("_US"):
        return "USGAAP"
    return "unknown"


def _consolidation_scope_from_doctype(doc_type: str) -> str:
    if "NonConsolidated" in doc_type:
        return "non_consolidated"
    if "Consolidated" in doc_type:
        return "consolidated"
    return "unknown"


def _base_record(asset: dict, disclosure: dict, retrieved_at: str, period_type: str,
                  fiscal_year: str, fiscal_quarter: int | None, statement_type: str,
                  consolidation_scope: str) -> dict:
    return {
        "schema_version": "1.0.0",
        "asset_id": asset["pilot_id"],
        "company_id": None,
        "pilot_id": asset["pilot_id"],
        "ticker": asset["ticker"],
        "provider_symbol": asset["provider_symbol_jquants"],
        "provider_record_id": disclosure.get("DiscNo") or None,
        "company_name": asset.get("company_name", ""),
        "exchange": "JPX",
        "mic": None,
        "country": "JP",
        "isin": asset.get("isin") or None,
        "provider": PROVIDER,
        "source_url_or_endpoint": "/v2/fins/summary",
        "retrieved_at": retrieved_at,
        "normalizer_version": NORMALIZER_VERSION,
        "statement_type": statement_type,
        "period_type": period_type,
        "fiscal_year": fiscal_year,
        "fiscal_quarter": fiscal_quarter,
        "period_start": disclosure.get("CurPerSt") or None,
        "period_end": disclosure.get("CurPerEn") or None,
        "filing_date": disclosure.get("DiscDate") or None,
        "publication_date": disclosure.get("DiscDate") or None,
        "restatement_status": _restatement_status(disclosure),
        "consolidation_scope": consolidation_scope,
        "accounting_standard": _accounting_standard(disclosure.get("DocType", "")),
        "currency": "JPY",
        "raw_currency": "JPY",
        "scale": "units",
        "sign_convention": "natural",
        "value_status": "ok",
        "source_status": "received",
        "normalization_status": "normalized",
        "validation_status": "pending",
        "quality_flags": [],
        "transformation_notes": None,
    }


def _value_record(base: dict, raw_field: str, metric: str, raw_value: str, unit: str) -> dict:
    record = dict(base)
    record["metric"] = metric
    record["raw_metric"] = raw_field
    money_denominated = unit in ("currency", "currency_per_share")
    if raw_value in ("", None):
        record["value"] = None
        record["raw_value"] = None
        record["missing_reason"] = "not_reported_by_company"
        record["currency"] = None
        record["raw_currency"] = None
    else:
        try:
            numeric = float(raw_value)
        except ValueError:
            record["value"] = None
            record["raw_value"] = raw_value
            record["missing_reason"] = "incomplete_response"
            record["normalization_status"] = "normalization_error"
            record["currency"] = None
            record["raw_currency"] = None
            return record
        record["value"] = numeric
        record["raw_value"] = numeric
        record["missing_reason"] = None
        if not money_denominated:
            record["currency"] = None
            record["raw_currency"] = None
    record["unit"] = unit
    record["record_id"] = _record_id(
        record["asset_id"], record["provider"], record["statement_type"], record["period_type"],
        record["fiscal_year"], str(record["fiscal_quarter"]), record["metric"], record["consolidation_scope"],
    )
    return record


def _dividend_record(base: dict, disclosure: dict) -> dict:
    values = [disclosure.get(f, "") for f in DIVIDEND_FIELDS]
    non_blank = [v for v in values if v not in ("", None)]
    record = dict(base)
    record["metric"] = "dividends_paid"
    record["raw_metric"] = "/".join(DIVIDEND_FIELDS)
    record["unit"] = "currency_per_share"
    if not non_blank:
        record["value"] = None
        record["raw_value"] = None
        record["currency"] = None
        record["raw_currency"] = None
        record["missing_reason"] = "not_reported_by_company"
    else:
        try:
            total = sum(float(v) for v in non_blank)
        except ValueError:
            record["value"] = None
            record["raw_value"] = "/".join(non_blank)
            record["missing_reason"] = "incomplete_response"
            record["normalization_status"] = "normalization_error"
            record["record_id"] = _record_id(record["asset_id"], record["provider"], record["statement_type"], record["period_type"], record["fiscal_year"], str(record["fiscal_quarter"]), record["metric"], record["consolidation_scope"])
            return record
        record["value"] = total
        record["raw_value"] = total
        record["missing_reason"] = None
    record["record_id"] = _record_id(record["asset_id"], record["provider"], record["statement_type"], record["period_type"], record["fiscal_year"], str(record["fiscal_quarter"]), record["metric"], record["consolidation_scope"])
    return record


def normalize_disclosure(asset: dict, disclosure: dict, retrieved_at: str) -> list[dict]:
    doc_type = disclosure.get("DocType", "")
    if doc_type in SKIPPED_DOC_TYPES:
        return []

    cur_per_type = disclosure.get("CurPerType", "")
    period_type = PERIOD_TYPE_BY_CUR_PER_TYPE.get(cur_per_type)
    if period_type is None:
        return []  # unrecognized period type -- do not guess, do not emit
    fiscal_quarter = FISCAL_QUARTER_BY_CUR_PER_TYPE.get(cur_per_type)
    fy_start = disclosure.get("CurFYSt", "")
    fiscal_year = fy_start[:4] if fy_start else ""

    records = []
    for consolidation_scope, currency_fields, equity_fields, per_share_fields, ratio_fields, share_fields in (
        (_consolidation_scope_from_doctype(doc_type), CURRENCY_METRIC_FIELDS, EQUITY_METRIC_FIELDS, PER_SHARE_METRIC_FIELDS, RATIO_METRIC_FIELDS, SHARE_COUNT_METRIC_FIELDS),
        ("non_consolidated", NC_CURRENCY_METRIC_FIELDS, NC_EQUITY_METRIC_FIELDS, NC_PER_SHARE_METRIC_FIELDS, NC_RATIO_METRIC_FIELDS, []),
    ):
        base = _base_record(asset, disclosure, retrieved_at, period_type, fiscal_year, fiscal_quarter, "income_statement", consolidation_scope)

        for raw_field, metric in currency_fields:
            statement_type = "balance_sheet" if metric == "total_assets" else ("cash_flow" if metric in ("operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "cash_and_equivalents") else "income_statement")
            record_base = dict(base, statement_type=statement_type)
            records.append(_value_record(record_base, raw_field, metric, disclosure.get(raw_field, ""), "currency"))

        for raw_field, metric in equity_fields:
            record_base = dict(base, statement_type="balance_sheet")
            records.append(_value_record(record_base, raw_field, metric, disclosure.get(raw_field, ""), "currency"))

        for raw_field, metric in per_share_fields:
            statement_type = "balance_sheet" if metric == "book_value_per_share" else "income_statement"
            record_base = dict(base, statement_type=statement_type)
            records.append(_value_record(record_base, raw_field, metric, disclosure.get(raw_field, ""), "currency_per_share"))

        for raw_field, metric in ratio_fields:
            record_base = dict(base, statement_type="derived_reported_by_provider")
            records.append(_value_record(record_base, raw_field, metric, disclosure.get(raw_field, ""), "ratio"))

        for raw_field, metric in share_fields:
            record_base = dict(base, statement_type="balance_sheet")
            records.append(_value_record(record_base, raw_field, metric, disclosure.get(raw_field, ""), "shares"))

        if consolidation_scope != "non_consolidated":
            record_base = dict(base, statement_type="cash_flow")
            records.append(_dividend_record(record_base, disclosure))

    return records


def normalize_file(path: Path) -> list[dict]:
    import json
    payload = json.loads(path.read_text(encoding="utf-8"))
    asset = payload["asset"]
    retrieved_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    records = []
    for disclosure in payload["disclosures"]:
        records.extend(normalize_disclosure(asset, disclosure, retrieved_at))
    return records


def normalize_collection(raw_dir: Path) -> list[dict]:
    records = []
    for path in sorted(raw_dir.glob("P*.json")):
        records.extend(normalize_file(path))
    return records
