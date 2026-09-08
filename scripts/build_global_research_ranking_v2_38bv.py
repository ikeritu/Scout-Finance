#!/usr/bin/env python3
"""Block v2.38BV, part 2 of Phase 9C: apply the already-validated scoring
engine (scripts/scoring_engine/core.py, config/scoring_factor_contract_v1
.json, v2.35A3 -- the real engine behind the old 50-asset product's own
"Ranking experimental", confirmed by direct code reading, not the
disconnected legacy files combined_scoring_v1.py/filter_stage2/3.py) to
the global eligible universe defined by v2.38BO.

Zero new methodology invented: same 14-factor contract, same weights,
same percentile-rank (midrank) normalization, same per-asset weight
renormalization with the same 0.50 coverage floor, same HIGH/MEDIUM/LOW
confidence thresholds, same tie-breakers. core.build_raw_factors(),
core.percentile_scores(), core.score_assets() and core.explain_result()
are imported and called unmodified -- this script's only real job is
building the two input dicts (fundamentals, prices) the engine expects,
in the exact factor-id vocabulary its contract uses.

Two real populations scored in this first run, both already covered by
already-computed real data:
  - US-origin (v2.38G original 555 + v2.38BK Cboe-secondary 538 +
    v2.38BA Joby Aviation): net_margin/return_on_assets/return_on_equity/
    revenue_yoy_growth/net_income_yoy_growth from those three files,
    operating_margin/eps_basic/book_value_per_share from v2.38BU. Real
    daily price history (v2.38I) only exists for the original 555, so
    momentum/risk/valuation only apply there -- everyone else falls
    through the engine's own existing renormalize-weights path (quality+
    growth only), same mechanism TWSE already used in the old product.
  - Austria (v2.38X ratios + v2.38AK growth, 17 real companies): the only
    non-US population with a real quality+growth ratio set already
    computed. No price, no eps/book-value data there -- same reduced
    factor set as the no-price US companies.

Luxembourg (26 companies) and the 1 real GB company do not yet have a
ratio/growth adapter wired into this block -- they are NOT scored here
and are explicitly reported as NOT_YET_SCORED_NO_ADAPTER, never silently
dropped or given a fabricated score.

A real, second bug was found and fixed while building this block, before
any scoring ran: v2.38AL's own coverage matrix carries the literal
placeholder string "AST0" as company_name for every one of these new
Austria-origin rows (confirmed directly against the real coverage matrix
file), so v2.38BO's financial-institution name heuristic never had a
real name to check against for this population and could not catch two
real financial institutions among Austria's 17 eligible companies --
Erste Group Bank AG and UNIQA Insurance Group AG. This block re-applies
the SAME real heuristic (imported unmodified from
build_global_scoring_eligibility_v2_38bo.is_financial_institution) against
v2.38X's own real company_name field before scoring, and routes both to
REVIEW_REQUIRED via the engine's existing exclusions mechanism -- the
identical mechanism, and the identical reason string
("financial_institution_requires_separate_factor_contract"), the old
50-asset product already uses for its own single real bank (P178). The
underlying "AST0" placeholder in v2.38AL/v2.38BO stays unfixed upstream,
deliberately, matching this project's own established precedent (v2.38BQ
did not retroactively edit v2.38BB for the same reason) -- fixing it
there and re-running v2.38BO would move already-cited numbers, an
explicit decision left for the user.

This block computes real scores for the first time in this project's
history. It is still explicitly experimental research prioritization,
never a recommendation, never a prediction, never a trade.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38BV-global-research-ranking"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking"

ELIGIBILITY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bo_global_scoring_eligibility/global_scoring_eligibility_v2_38bo.csv"
US_ORIGINAL_FEATURES = ROOT / "outputs/full_universe_source_acquisition/v2_38g_us_sec_fundamental_features/us_sec_fundamental_features_v2_38g.csv"
US_CBOE_SECONDARY_FEATURES = ROOT / "outputs/full_universe_source_acquisition/v2_38bk_us_cboe_secondary_sec_fundamentals/us_cboe_secondary_sec_fundamental_features_v2_38bk.csv"
US_JOBY_FEATURES = ROOT / "outputs/full_universe_source_acquisition/v2_38ba_us_joby_aviation_fundamentals/us_joby_aviation_fundamental_features_v2_38ba.csv"
US_VALUATION_EXTENSION = ROOT / "outputs/full_universe_source_acquisition/v2_38bu_us_sec_valuation_features_extension/us_sec_valuation_features_extension_v2_38bu.csv"
US_PRICE_RAW_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_38i_us_price_history_acquisition/us_price_history_raw_v2_38i"
EUROPE_AUSTRIA_RATIOS = ROOT / "outputs/full_universe_source_acquisition/v2_38x_europe_candidate_feature_matrix/europe_fundamental_features_v2_38x.csv"
EUROPE_AUSTRIA_GROWTH = ROOT / "outputs/full_universe_source_acquisition/v2_38ak_europe_growth_features/europe_growth_features_v2_38ak.csv"

FINANCIAL_INSTITUTION_REASON = "financial_institution_requires_separate_factor_contract"

# Same field-name vocabulary core.build_raw_factors()/score_assets() are
# already contractually written for -- no engine code changes, only this
# mapping.
US_FIELD_MAP = {"net_margin": "net_margin", "roa": "return_on_assets", "roe_reported": "return_on_equity", "revenue_growth_yoy": "revenue_yoy_growth", "net_income_growth_yoy": "net_income_yoy_growth"}
AT_FIELD_MAP_RATIOS = {"net_margin": "net_margin", "operating_margin": "operating_margin", "roa": "return_on_assets", "roe_reported": "return_on_equity"}
AT_FIELD_MAP_GROWTH = {"revenue_growth_yoy": "revenue_yoy_growth", "net_income_growth_yoy": "net_profit_yoy_growth"}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def as_float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_eligibility(path: Path) -> tuple[dict[str, dict], set[str], set[str]]:
    display: dict[str, dict] = {}
    eligible_ids: set[str] = set()
    financial_ids: set[str] = set()
    for row in read_csv(path):
        asset_id = row["asset_id"]
        display[asset_id] = {"ticker": row.get("ticker", ""), "company_name": row.get("company_name", ""), "country": row.get("country", ""), "eligibility_tier": row.get("eligibility_tier", "")}
        if row.get("eligibility_tier", "").startswith("ELIGIBLE"):
            eligible_ids.add(asset_id)
        elif row.get("eligibility_tier", "") == "REVIEW_REQUIRED_FINANCIAL_INSTITUTION":
            financial_ids.add(asset_id)
    return display, eligible_ids, financial_ids


def build_us_fundamentals(universe: set[str], *feature_paths: Path, valuation_path: Path) -> dict[str, dict[str, float]]:
    fundamentals: dict[str, dict[str, float]] = {}
    for path in feature_paths:
        for row in read_csv(path):
            asset_id = row.get("asset_id", "")
            if asset_id not in universe:
                continue
            entry = {new: as_float(row.get(old)) for new, old in US_FIELD_MAP.items()}
            fundamentals[asset_id] = {k: v for k, v in entry.items() if v is not None}
    for row in read_csv(valuation_path):
        asset_id = row.get("asset_id", "")
        if asset_id not in universe:
            continue
        entry = fundamentals.setdefault(asset_id, {})
        for field in ("operating_margin", "eps_basic", "book_value_per_share"):
            value = as_float(row.get(field))
            if value is not None:
                entry[field] = value
    return fundamentals


def build_austria_fundamentals(universe: set[str], ratios_path: Path, growth_path: Path) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    fundamentals: dict[str, dict[str, float]] = {}
    real_names: dict[str, str] = {}
    for row in read_csv(ratios_path):
        asset_id = row.get("asset_id", "")
        if asset_id not in universe:
            continue
        real_names[asset_id] = row.get("company_name", "")
        entry = {new: as_float(row.get(old)) for new, old in AT_FIELD_MAP_RATIOS.items()}
        fundamentals[asset_id] = {k: v for k, v in entry.items() if v is not None}
    for row in read_csv(growth_path):
        asset_id = row.get("asset_id", "")
        if asset_id not in fundamentals:
            continue
        entry = fundamentals[asset_id]
        for new, old in AT_FIELD_MAP_GROWTH.items():
            value = as_float(row.get(old))
            if value is not None:
                entry[new] = value
    return fundamentals, real_names


def load_us_prices(universe: set[str], raw_dir: Path) -> dict[str, list[tuple[str, float]]]:
    prices: dict[str, list[tuple[str, float]]] = {}
    if not raw_dir.exists():
        return prices
    for path in raw_dir.glob("*.csv"):
        asset_id = path.stem
        if asset_id not in universe:
            continue
        rows: list[tuple[str, float]] = []
        for row in read_csv(path):
            date = row.get("date", "")
            close = as_float(row.get("adjusted_close")) or as_float(row.get("close"))
            if date and close is not None and close > 0:
                rows.append((date, close))
        rows.sort()
        if rows:
            prices[asset_id] = rows
    return prices


def build(
    eligibility_path: Path,
    us_original_features: Path, us_cboe_secondary_features: Path, us_joby_features: Path, us_valuation_extension: Path, us_price_raw_dir: Path,
    europe_austria_ratios: Path, europe_austria_growth: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    core = load_module("scoring_engine_core", ROOT / "scripts/scoring_engine/core.py")
    v38bo = load_module("build_global_scoring_eligibility_v2_38bo", ROOT / "scripts/build_global_scoring_eligibility_v2_38bo.py")
    contract = json.loads((ROOT / "config/scoring_factor_contract_v1.json").read_text(encoding="utf-8"))

    display, eligible_ids, financial_ids = load_eligibility(eligibility_path)
    universe = eligible_ids | financial_ids

    us_fundamentals = build_us_fundamentals(universe, us_original_features, us_cboe_secondary_features, us_joby_features, valuation_path=us_valuation_extension)
    at_fundamentals, at_real_names = build_austria_fundamentals(universe, europe_austria_ratios, europe_austria_growth)
    fundamentals = {**us_fundamentals, **at_fundamentals}
    prices = load_us_prices(universe, us_price_raw_dir)

    # Real bug found while building this block: v2.38AL's own coverage
    # matrix carries the literal placeholder "AST0" as company_name for
    # this whole Austria-origin population, so v2.38BO's financial-
    # institution heuristic never had a real name to check. Re-applied
    # here against v2.38X's real company_name before any scoring runs.
    exclusions: dict[str, str] = {asset_id: FINANCIAL_INSTITUTION_REASON for asset_id in financial_ids}
    recovered_financial_institutions: list[str] = []
    for asset_id, real_name in at_real_names.items():
        if asset_id not in exclusions and v38bo.is_financial_institution(real_name):
            exclusions[asset_id] = FINANCIAL_INSTITUTION_REASON
            recovered_financial_institutions.append(asset_id)

    scoped_fundamentals = {k: v for k, v in fundamentals.items() if k in universe}
    scoped_prices = {k: v for k, v in prices.items() if k in universe}

    raw = core.build_raw_factors(scoped_fundamentals, scoped_prices)
    normalized = core.percentile_scores(raw, contract)
    scored = core.score_assets(raw, normalized, contract, exclusions)

    rows: list[dict[str, Any]] = []
    for row in scored:
        asset_id = row["asset_id"]
        meta = display.get(asset_id, {})
        company_name = at_real_names.get(asset_id) or meta.get("company_name", "")
        explanation = core.explain_result(row, contract)
        rows.append({**row, "ticker": meta.get("ticker", ""), "company_name": company_name, "country": meta.get("country", ""), "explanation": explanation})

    scored_ids = {r["asset_id"] for r in rows}
    not_yet_scored = sorted(universe - scored_ids)
    for asset_id in not_yet_scored:
        meta = display.get(asset_id, {})
        rows.append({
            "asset_id": asset_id, "ticker": meta.get("ticker", ""), "company_name": meta.get("company_name", ""), "country": meta.get("country", ""),
            "eligibility_status": "NOT_YET_SCORED_NO_ADAPTER", "confidence": "NOT_RANKABLE", "coverage_weight": 0.0, "total_score": None,
            "raw_factors": {}, "normalized_factors": {}, "contributions": {}, "pillar_scores": {}, "review_reasons": ["no_fundamentals_growth_ratio_adapter_built_yet_for_this_country"],
            "explanation": {},
        })

    results_fields = ["asset_id", "ticker", "company_name", "country", "eligibility_status", "confidence", "coverage_weight", "total_score", "rank", "review_reasons", "phase"]
    csv_rows = [{**r, "rank": r.get("rank", ""), "review_reasons": "|".join(r.get("review_reasons", [])), "phase": PHASE} for r in rows]
    write_csv(output_dir / "global_research_ranking_v2_38bv.csv", csv_rows, results_fields)
    write_text(output_dir / "global_research_ranking_results_v2_38bv.json", core.canonical_json(rows))
    main_ranking = sorted((r for r in rows if r.get("eligibility_status") == "ELIGIBLE_PARTIAL" and r.get("rank")), key=lambda r: r["rank"])
    write_text(output_dir / "global_research_ranking_main_v2_38bv.json", core.canonical_json(main_ranking))

    status_counts = Counter(r["eligibility_status"] for r in rows)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_GLOBAL_RESEARCH_RANKING_EXPERIMENTAL",
        "universe_size": len(universe), "eligible_input": len(eligible_ids), "financial_institution_input": len(financial_ids),
        "financial_institutions_recovered_from_real_austria_names": sorted(recovered_financial_institutions),
        "eligibility_status_counts": dict(sorted(status_counts.items())),
        "not_yet_scored_no_adapter": not_yet_scored,
        "shortlist_size": contract["shortlist_size"],
        "shortlist": [r["asset_id"] for r in main_ranking[: contract["shortlist_size"]]],
        "note": "Applies the already-validated v2.35A3 scoring engine (scripts/scoring_engine/core.py) unchanged to the v2.38BO eligible universe -- same contract, same weights, same percentile-rank normalization, same renormalize-weights coverage floor, same confidence tiers. US-origin (v2.38G+BK+BA+BU) and Austria (v2.38X+AK) are scored; Luxembourg and GB have no ratio/growth adapter built yet and are reported explicitly as not_yet_scored_no_adapter, never silently dropped or fabricated. A real placeholder-company-name bug in v2.38AL/v2.38BO (literal 'AST0' for the whole new Austria population) meant two real financial institutions (Erste Group Bank AG, UNIQA Insurance Group AG) were not caught upstream -- recovered here by re-applying v2.38BO's own real heuristic against v2.38X's real company names, routed to REVIEW_REQUIRED via the engine's existing exclusions mechanism, same reason string the old product already uses for its own bank (P178). Experimental research prioritization only -- never investment advice, never a prediction, never a trade.",
        "guardrails": {"network_used": False, "recommendations_generated": False, "broker_actions_allowed": False, "financial_advice": False, "phase9c_authorized": True, "phase9c_block": "2_of_3_scoring_engine_applied"},
    }
    write_text(output_dir / "global_research_ranking_aggregate_report_v2_38bv.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest = {"phase": PHASE, "outputs": {"global_research_ranking_v2_38bv.csv": {"bytes": (output_dir / "global_research_ranking_v2_38bv.csv").stat().st_size, "sha256": sha256(output_dir / "global_research_ranking_v2_38bv.csv")}}, "guardrails": report["guardrails"]}
    write_text(output_dir / "global_research_ranking_manifest_v2_38bv.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eligibility-input", type=Path, default=ELIGIBILITY_INPUT)
    parser.add_argument("--us-original-features", type=Path, default=US_ORIGINAL_FEATURES)
    parser.add_argument("--us-cboe-secondary-features", type=Path, default=US_CBOE_SECONDARY_FEATURES)
    parser.add_argument("--us-joby-features", type=Path, default=US_JOBY_FEATURES)
    parser.add_argument("--us-valuation-extension", type=Path, default=US_VALUATION_EXTENSION)
    parser.add_argument("--us-price-raw-dir", type=Path, default=US_PRICE_RAW_DIR)
    parser.add_argument("--europe-austria-ratios", type=Path, default=EUROPE_AUSTRIA_RATIOS)
    parser.add_argument("--europe-austria-growth", type=Path, default=EUROPE_AUSTRIA_GROWTH)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(
        args.eligibility_input,
        args.us_original_features, args.us_cboe_secondary_features, args.us_joby_features, args.us_valuation_extension, args.us_price_raw_dir,
        args.europe_austria_ratios, args.europe_austria_growth,
        args.output_dir,
    )
    print(json.dumps({k: report[k] for k in ("phase", "status", "universe_size", "eligibility_status_counts", "not_yet_scored_no_adapter")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
