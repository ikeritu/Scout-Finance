"""Canonical FundamentalRecord (v1) for Scout Finance phase 5. Mirrors
schemas/fundamental_record_v1.schema.json exactly -- this module is the
code-facing counterpart; the JSON file is the formal, language-agnostic
contract. Validate against the JSON schema (validate_record below) rather
than trusting the dataclass shape alone, since the JSON schema is the
source of truth and is what external tooling would consult.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/fundamental_record_v1.schema.json"
METRICS_CATALOG_PATH = ROOT / "config/fundamental_metrics_v1.json"
MISSING_REASONS_PATH = ROOT / "config/fundamental_missing_reasons_v1.json"

SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class FundamentalRecord:
    schema_version: str
    record_id: str
    asset_id: str
    company_id: str | None
    pilot_id: str
    ticker: str
    provider_symbol: str
    provider_record_id: str | None
    company_name: str
    exchange: str
    mic: str | None
    country: str
    isin: str | None
    provider: str
    source_url_or_endpoint: str
    retrieved_at: str
    normalizer_version: str
    statement_type: str
    period_type: str
    fiscal_year: str
    fiscal_quarter: int | None
    period_start: str | None
    period_end: str
    filing_date: str | None
    publication_date: str | None
    restatement_status: str
    consolidation_scope: str
    accounting_standard: str
    metric: str
    raw_metric: str
    value: float | None
    raw_value: float | str | None
    currency: str | None
    raw_currency: str | None
    unit: str
    scale: str
    sign_convention: str
    value_status: str
    source_status: str
    normalization_status: str
    validation_status: str
    missing_reason: str | None
    quality_flags: list[str]
    transformation_notes: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_metrics_catalog() -> dict[str, dict]:
    payload = json.loads(METRICS_CATALOG_PATH.read_text(encoding="utf-8"))
    return {m["id"]: m for m in payload["metrics"]}


@lru_cache(maxsize=1)
def load_missing_reasons() -> set[str]:
    payload = json.loads(MISSING_REASONS_PATH.read_text(encoding="utf-8"))
    return {r["code"] for r in payload["missing_reasons"]}


def validate_record(record: dict) -> list[str]:
    """Return a list of problems (empty = valid). Checks JSON-schema shape,
    that `metric` is a known canonical id, and that `missing_reason` is a
    known closed-catalog code whenever `value` is null -- catching exactly
    the "silently converted to zero/omitted" failure mode rule 3.3 forbids.
    """
    problems = []
    validator = jsonschema.Draft202012Validator(load_schema())
    for error in validator.iter_errors(record):
        problems.append(error.message)
    if problems:
        return problems  # shape errors make further checks unreliable

    metrics = load_metrics_catalog()
    if record["metric"] not in metrics:
        problems.append(f"unknown canonical metric id: {record['metric']!r}")

    if record["value"] is None:
        if not record.get("missing_reason"):
            problems.append("value is null but missing_reason is not set")
        elif record["missing_reason"] not in load_missing_reasons():
            problems.append(f"missing_reason not in closed catalog: {record['missing_reason']!r}")
    else:
        if record.get("missing_reason") is not None:
            problems.append("value is present but missing_reason is also set -- pick one")

    if record["value_status"] == "estimated":
        problems.append("value_status='estimated' is forbidden in phase 5 (rule 3.1: no synthetic values)")

    return problems
