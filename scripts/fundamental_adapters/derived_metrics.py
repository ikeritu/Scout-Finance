"""Block G: derive calculated metrics (margins, ROA, YoY growth, and the
still-blocked debt/FCF metrics) from already-normalized FundamentalRecord
rows. No network, no raw provider data touched -- this module only reads
the output of block F's normalizers.

Rules enforced here, all directly from the phase-5 encargo:
  - A derived metric is only computed when every component it needs is
    itself a real, non-null, schema-valid value -- never approximated,
    never partially computed from a missing piece.
  - Division by zero never raises and never silently produces inf/nan: the
    record becomes value=None + missing_reason="calculation_impossible_
    missing_components" instead.
  - A negative denominator in a ratio still computes an arithmetically
    correct number, but is flagged (quality_flags) rather than presented
    as an ordinary ratio, since e.g. a negative-equity ROE is technically
    a valid division but not an intuitively comparable "return".
  - Reported vs calculated is always distinguishable: every record from
    this module carries value_status="calculated" and
    statement_type="derived_calculated_by_scout_finance", distinct from
    the provider's own reported ratios (statement_type=
    "derived_reported_by_provider", e.g. J-Quants ROE).
  - No aggregate score of any kind is produced here -- that is explicitly
    out of scope for block G (and for phase 5 entirely).
"""
from __future__ import annotations

import hashlib
from collections import defaultdict

NORMALIZER_VERSION = "1.0.0"
CALC_STATEMENT_TYPE = "derived_calculated_by_scout_finance"
BLOCKED_REASON = "calculation_impossible_missing_components"
NEGATIVE_DENOMINATOR_FLAG = "negative_denominator_ratio_not_directly_comparable"
NEGATIVE_BASE_GROWTH_FLAG = "negative_base_period_growth_not_directly_comparable"

# Metrics whose components are confirmed absent from BOTH approved sources
# (see config/fundamental_metrics_v1.json) -- these always resolve to
# BLOCKED_REASON, but the block still emits one explicit record per asset
# per period so the coverage manifest shows a documented "why", not a
# silent gap.
ALWAYS_BLOCKED_METRICS = {
    "gross_debt": ["current_debt", "noncurrent_debt"],
    "net_debt": ["gross_debt", "cash_and_equivalents"],
    "free_cash_flow": ["operating_cash_flow", "capex"],
}


RESTATEMENT_PRIORITY = {"restated": 2, "original": 1, "unknown": 0}


def _prefer(existing: dict, candidate: dict) -> dict:
    """Explicit consolidated/restated priority rule (block F requirement):
    a restated disclosure always supersedes an original one for the same
    asset+period+metric; ties (same restatement_status) go to whichever
    was filed later. Never an arbitrary "last one wins" from file order."""
    existing_rank = RESTATEMENT_PRIORITY.get(existing["restatement_status"], 0)
    candidate_rank = RESTATEMENT_PRIORITY.get(candidate["restatement_status"], 0)
    if candidate_rank != existing_rank:
        return candidate if candidate_rank > existing_rank else existing
    existing_date = existing.get("filing_date") or ""
    candidate_date = candidate.get("filing_date") or ""
    return candidate if candidate_date > existing_date else existing


def _group_by_period(records: list[dict]) -> dict[tuple, dict[str, dict]]:
    """asset+period -> {metric: record}, restricted to non-derived, valid-value
    rows, with restated disclosures explicitly preferred over original ones
    for the same asset+period+metric (see _prefer)."""
    groups: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in records:
        if r["statement_type"] in (CALC_STATEMENT_TYPE, "derived_reported_by_provider"):
            continue
        key = (r["asset_id"], r["period_type"], r["fiscal_year"], r["fiscal_quarter"], r["consolidation_scope"])
        bucket = groups[key]
        if r["metric"] in bucket:
            bucket[r["metric"]] = _prefer(bucket[r["metric"]], r)
        else:
            bucket[r["metric"]] = r
    return groups


def _record_id(*parts: str) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def _template_from(source_record: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "asset_id": source_record["asset_id"],
        "company_id": source_record["company_id"],
        "pilot_id": source_record["pilot_id"],
        "ticker": source_record["ticker"],
        "provider_symbol": source_record["provider_symbol"],
        "provider_record_id": None,
        "company_name": source_record["company_name"],
        "exchange": source_record["exchange"],
        "mic": source_record["mic"],
        "country": source_record["country"],
        "isin": source_record["isin"],
        "provider": source_record["provider"],
        "source_url_or_endpoint": source_record["source_url_or_endpoint"],
        "retrieved_at": source_record["retrieved_at"],
        "normalizer_version": NORMALIZER_VERSION,
        "statement_type": CALC_STATEMENT_TYPE,
        "period_type": source_record["period_type"],
        "fiscal_year": source_record["fiscal_year"],
        "fiscal_quarter": source_record["fiscal_quarter"],
        "period_start": source_record["period_start"],
        "period_end": source_record["period_end"],
        "filing_date": source_record["filing_date"],
        "publication_date": source_record["publication_date"],
        "restatement_status": source_record["restatement_status"],
        "consolidation_scope": source_record["consolidation_scope"],
        "accounting_standard": source_record["accounting_standard"],
        "currency": None,
        "raw_currency": None,
        "unit": "ratio",
        "scale": "units",
        "sign_convention": "natural",
        "value_status": "calculated",
        "source_status": "received",
        "normalization_status": "normalized",
        "validation_status": "pending",
        "quality_flags": [],
        "transformation_notes": None,
    }


def _finalize(record: dict) -> dict:
    record["record_id"] = _record_id(record["asset_id"], "scout_finance_derived", record["statement_type"], record["period_type"], record["fiscal_year"], str(record["fiscal_quarter"]), record["metric"], record["consolidation_scope"])
    return record


def _ratio(by_metric: dict[str, dict], numerator: str, denominator: str, metric_id: str, raw_metric_label: str) -> dict | None:
    num_rec = by_metric.get(numerator)
    den_rec = by_metric.get(denominator)
    if num_rec is None or den_rec is None or num_rec["value"] is None or den_rec["value"] is None:
        return None  # a component is genuinely absent this period -- caller handles the blocked record

    record = _template_from(num_rec)
    record["metric"] = metric_id
    record["raw_metric"] = raw_metric_label
    if den_rec["value"] == 0:
        record["value"] = None
        record["raw_value"] = None
        record["missing_reason"] = BLOCKED_REASON
    else:
        record["value"] = num_rec["value"] / den_rec["value"]
        record["raw_value"] = record["value"]
        record["missing_reason"] = None
        if den_rec["value"] < 0:
            record["quality_flags"] = [NEGATIVE_DENOMINATOR_FLAG]
    return _finalize(record)


def _blocked_record(any_record_in_group: dict, metric_id: str, missing_components: list[str]) -> dict:
    record = _template_from(any_record_in_group)
    record["metric"] = metric_id
    record["raw_metric"] = "+".join(missing_components)
    record["value"] = None
    record["raw_value"] = None
    record["missing_reason"] = BLOCKED_REASON
    record["unit"] = "currency"
    return _finalize(record)


def compute_margins_and_roa(by_metric: dict[str, dict]) -> list[dict]:
    records = []
    for numerator, denominator, metric_id in [
        ("gross_profit", "revenue", "gross_margin"),
        ("operating_income", "revenue", "operating_margin"),
        ("net_income", "revenue", "net_margin"),
        ("net_income", "total_assets", "roa"),
        ("current_assets", "current_liabilities", "current_ratio"),
    ]:
        record = _ratio(by_metric, numerator, denominator, metric_id, f"{numerator}/{denominator}")
        if record is not None:
            records.append(record)
    return records


def compute_always_blocked(by_metric: dict[str, dict], any_record: dict) -> list[dict]:
    return [_blocked_record(any_record, metric_id, components) for metric_id, components in ALWAYS_BLOCKED_METRICS.items()]


def compute_yoy_growth(groups: dict[tuple, dict[str, dict]]) -> list[dict]:
    """JPX only: match (asset, period_type, fiscal_quarter, consolidation_scope)
    one fiscal year apart. TWSE has a single snapshot period, so it never
    has a prior-year match and correctly produces no growth records."""
    by_asset_period_quarter: dict[tuple, dict[str, dict[str, dict]]] = defaultdict(dict)
    for key, by_metric in groups.items():
        asset_id, period_type, fiscal_year, fiscal_quarter, consolidation_scope = key
        try:
            fy_int = int(fiscal_year)
        except (TypeError, ValueError):
            continue
        by_asset_period_quarter[(asset_id, period_type, fiscal_quarter, consolidation_scope)][fy_int] = by_metric

    records = []
    for group_key, by_year in by_asset_period_quarter.items():
        for fy_int, by_metric in by_year.items():
            prior = by_year.get(fy_int - 1)
            if prior is None:
                continue
            for metric_name, growth_metric_id in [("revenue", "revenue_growth_yoy"), ("net_income", "net_income_growth_yoy")]:
                current_rec = by_metric.get(metric_name)
                prior_rec = prior.get(metric_name)
                if current_rec is None or prior_rec is None or current_rec["value"] is None or prior_rec["value"] is None:
                    continue
                record = _template_from(current_rec)
                record["metric"] = growth_metric_id
                record["raw_metric"] = f"{metric_name}[t]/{metric_name}[t-1y]"
                if prior_rec["value"] == 0:
                    record["value"] = None
                    record["raw_value"] = None
                    record["missing_reason"] = BLOCKED_REASON
                else:
                    growth = (current_rec["value"] - prior_rec["value"]) / abs(prior_rec["value"])
                    record["value"] = growth
                    record["raw_value"] = growth
                    record["missing_reason"] = None
                    if prior_rec["value"] < 0:
                        record["quality_flags"] = [NEGATIVE_BASE_GROWTH_FLAG]
                records.append(_finalize(record))
    return records


def compute_derived_records(normalized_records: list[dict]) -> list[dict]:
    groups = _group_by_period(normalized_records)
    derived: list[dict] = []
    for key, by_metric in groups.items():
        if not by_metric:
            continue
        any_record = next(iter(by_metric.values()))
        derived.extend(compute_margins_and_roa(by_metric))
        derived.extend(compute_always_blocked(by_metric, any_record))
    derived.extend(compute_yoy_growth(groups))
    return derived
