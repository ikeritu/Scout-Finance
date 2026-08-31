"""Block H: validation over the real block-F/G FundamentalRecord dataset --
accounting equations, temporal consistency, economic sanity, and a
per-asset data-QUALITY score (never an investment score). No network, no
credentials; reads only already-normalized/derived records.

Every check here follows the same rule: flag, never silently "fix". A
failed accounting equation, an implausible value, or a missing component
becomes a quality_flag or a documented "not_applicable" -- never a value
this module invents or corrects.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

# Tolerances are intentionally NOT zero -- these are independently
# rounded/scaled figures from the provider, and requiring exact equality
# would produce false failures on ordinary rounding, not real defects.
RELATIVE_TOLERANCE = 0.02  # 2%

CORE_METRICS = ["revenue", "operating_income", "net_income", "total_assets", "total_equity"]

# How many distinct real periods we expect a fully-continuous collection to
# have, per provider -- these are the real, already-confirmed structural
# limits (v2.34B/E), not aspirational targets: JPX gives ~2 years of
# quarterly + FY disclosures (documented as an ~8-period target), MOPS
# opendata gives exactly one snapshot period by design, so its own
# continuity target is 1 (never penalize a source for a limitation this
# project already accepted when approving it in block B).
CONTINUITY_TARGET_BY_PROVIDER = {"jquants_fins_summary": 8, "twse_mops_opendata": 1}

TODAY = date(2026, 8, 31)
FRESHNESS_WINDOW_DAYS = 730  # 2 years: freshness decays to 0 at this staleness, a defined convention, not an external standard


def _group_by_period(records: list[dict]) -> dict[tuple, dict[str, dict]]:
    groups: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in records:
        key = (r["asset_id"], r["period_type"], r["fiscal_year"], r["fiscal_quarter"], r["consolidation_scope"])
        groups[key][r["metric"]] = r
    return groups


def _within_tolerance(a: float, b: float) -> bool:
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) / scale <= RELATIVE_TOLERANCE


def check_accounting_equations(normalized_records: list[dict]) -> list[dict]:
    """One result per (asset, period, equation): {status: 'passed'|'failed'|'not_applicable', ...}.
    not_applicable means the components needed aren't independently
    reported for this source (e.g. JPX has no independent total_liabilities
    -- computing it FROM assets-equity and then "checking" assets=liabilities+equity
    would be circular, not a real validation, so it is never attempted)."""
    groups = _group_by_period(normalized_records)
    results = []
    for key, by_metric in groups.items():
        asset_id, period_type, fiscal_year, fiscal_quarter, consolidation_scope = key
        base = {"asset_id": asset_id, "period_type": period_type, "fiscal_year": fiscal_year, "fiscal_quarter": fiscal_quarter, "consolidation_scope": consolidation_scope}

        # balance_sheet_equation: only valid where liabilities are an
        # INDEPENDENTLY reported figure (TWSE), not one we'd have to derive
        # from the same two numbers we're checking against.
        total_assets = by_metric.get("total_assets")
        total_liabilities = by_metric.get("total_liabilities")
        total_equity = by_metric.get("total_equity")
        if total_assets and total_liabilities and total_equity and None not in (total_assets["value"], total_liabilities["value"], total_equity["value"]):
            passed = _within_tolerance(total_assets["value"], total_liabilities["value"] + total_equity["value"])
            results.append(dict(base, equation="balance_sheet_equation", status="passed" if passed else "failed"))
        else:
            results.append(dict(base, equation="balance_sheet_equation", status="not_applicable", reason="total_liabilities not independently reported for this source" if not total_liabilities else "missing_component"))

        revenue = by_metric.get("revenue")
        cost_of_sales = by_metric.get("cost_of_sales")
        gross_profit = by_metric.get("gross_profit")
        if revenue and cost_of_sales and gross_profit and None not in (revenue["value"], cost_of_sales["value"], gross_profit["value"]):
            passed = _within_tolerance(gross_profit["value"], revenue["value"] - cost_of_sales["value"])
            results.append(dict(base, equation="gross_profit_equation", status="passed" if passed else "failed"))
        else:
            results.append(dict(base, equation="gross_profit_equation", status="not_applicable", reason="missing_component"))

    return results


def check_temporal_consistency(normalized_records: list[dict]) -> list[dict]:
    """One flag per problem found; empty list means nothing to flag."""
    problems = []
    for r in normalized_records:
        if r["period_start"] and r["period_end"] and r["period_start"] > r["period_end"]:
            problems.append({"asset_id": r["asset_id"], "record_id": r["record_id"], "issue": "period_start_after_period_end"})
        if r["fiscal_quarter"] is not None and r["fiscal_quarter"] not in (1, 2, 3, 4):
            problems.append({"asset_id": r["asset_id"], "record_id": r["record_id"], "issue": "fiscal_quarter_out_of_range"})
    return problems


# (metric, plausible_min, plausible_max, applies_to) -- bounds are
# deliberately loose (real companies can have extreme but real results);
# these exist to catch clear provider/normalization defects (e.g. a scale
# error producing a 10000% margin), not to second-guess a real bad quarter.
SANITY_RANGES = [
    ("operating_margin", -5.0, 2.0), ("net_margin", -5.0, 2.0), ("gross_margin", -5.0, 2.0),
    ("roa", -5.0, 2.0), ("current_ratio", 0.0, 50.0),
    ("revenue_growth_yoy", -1.0, 20.0), ("net_income_growth_yoy", -50.0, 50.0),
]


def check_economic_sanity(records: list[dict]) -> list[dict]:
    flags = []
    bounds = {m: (lo, hi) for m, lo, hi in SANITY_RANGES}
    for r in records:
        if r["value"] is None:
            continue
        if r["metric"] == "total_assets" and r["value"] < 0:
            flags.append({"asset_id": r["asset_id"], "record_id": r["record_id"], "issue": "negative_total_assets_implausible"})
        if r["metric"] in bounds:
            lo, hi = bounds[r["metric"]]
            if not (lo <= r["value"] <= hi):
                flags.append({"asset_id": r["asset_id"], "record_id": r["record_id"], "issue": f"{r['metric']}_outside_plausible_range", "value": r["value"]})
    return flags


def compute_quality_scores(asset_id: str, provider: str, normalized_records: list[dict],
                            equation_results: list[dict], sanity_flags: list[dict]) -> dict:
    asset_normalized = [r for r in normalized_records if r["asset_id"] == asset_id]
    asset_equations = [e for e in equation_results if e["asset_id"] == asset_id]
    asset_sanity_flags = [f for f in sanity_flags if f["asset_id"] == asset_id]

    identity_score = 1.0  # all 50 assets are identity_verified per block A -- not recomputed here, just carried forward as evidence, not re-derived

    normalized_ok = sum(1 for r in asset_normalized if r["normalization_status"] == "normalized")
    provenance_score = normalized_ok / len(asset_normalized) if asset_normalized else 0.0

    core_present = {r["metric"] for r in asset_normalized if r["metric"] in CORE_METRICS and r["value"] is not None}
    completeness_score = len(core_present) / len(CORE_METRICS)

    periods_with_core_data = {(r["period_type"], r["fiscal_year"], r["fiscal_quarter"]) for r in asset_normalized if r["metric"] == "revenue" and r["value"] is not None}
    continuity_target = CONTINUITY_TARGET_BY_PROVIDER.get(provider, 1)
    continuity_score = min(1.0, len(periods_with_core_data) / continuity_target) if continuity_target else 0.0

    attempted_equations = [e for e in asset_equations if e["status"] != "not_applicable"]
    coherence_score = (sum(1 for e in attempted_equations if e["status"] == "passed") / len(attempted_equations)) if attempted_equations else None

    total_catalog_metrics = 29
    reported_metric_count = len({r["metric"] for r in asset_normalized if r["value"] is not None})
    comparability_score = min(1.0, reported_metric_count / total_catalog_metrics)

    latest_period_end = max((r["period_end"] for r in asset_normalized if r["period_end"]), default=None)
    if latest_period_end:
        staleness_days = (TODAY - date.fromisoformat(latest_period_end)).days
        freshness_score = max(0.0, 1.0 - staleness_days / FRESHNESS_WINDOW_DAYS)
    else:
        freshness_score = 0.0

    dimensions = {
        "identity": identity_score, "provenance": provenance_score, "completeness": completeness_score,
        "continuity": continuity_score, "coherence": coherence_score, "comparability": comparability_score,
        "freshness": freshness_score,
    }
    scored_dims = [v for v in dimensions.values() if v is not None]
    composite = sum(scored_dims) / len(scored_dims) if scored_dims else 0.0

    return {
        "asset_id": asset_id,
        "provider": provider,
        "dimensions": dimensions,
        "composite_quality_score": composite,
        "sanity_flags_count": len(asset_sanity_flags),
        "accounting_equations_attempted": len(attempted_equations),
        "accounting_equations_passed": sum(1 for e in attempted_equations if e["status"] == "passed"),
    }
