"""Read-only, fail-closed access to the canonical 50-asset product dataset."""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

UNIVERSE_REL = "outputs/full_universe_source_acquisition/v2_34a_fundamental_universe_audit/fundamental_universe_manifest_v2_34a.csv"
AGGREGATE_REL = "outputs/full_universe_source_acquisition/v2_35c_phase6_final_gate/scoring_aggregate_report_v2_35c.json"
LOCAL_RESULTS_REL = "outputs/full_universe_source_acquisition/v2_35_phase6_scoring_local/scoring_results_v2_35.json"
NORMALIZED_REL = "outputs/full_universe_source_acquisition/v2_34f_fundamental_dataset/fundamental_records_v2_34f.jsonl"
DERIVED_REL = "outputs/full_universe_source_acquisition/v2_34g_derived_metrics/derived_records_v2_34g.jsonl"
PRICE_RELS = {
    "JPX": "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot/jquants_prices_collection_v2_33g",
    "TWSE": "outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot/twse_opendata_prices_collection_v2_33i",
}


class DataMode(str, Enum):
    REAL_LOCAL_READY = "REAL_LOCAL_READY"
    AGGREGATE_ONLY = "AGGREGATE_ONLY"
    PARTIAL_DATA = "PARTIAL_DATA"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"
    INCOMPATIBLE_VERSION = "INCOMPATIBLE_VERSION"


@dataclass(frozen=True)
class ProductData:
    mode: DataMode
    assets: tuple[dict, ...]
    as_of_date: str
    errors: tuple[str, ...] = ()
    local_scoring: bool = False
    local_fundamentals: bool = False
    local_prices: bool = False

    def by_id(self, asset_id: str) -> dict:
        matches = [row for row in self.assets if row["asset_id"] == asset_id]
        if len(matches) != 1:
            raise ValueError("asset is missing or ambiguous")
        return matches[0]


def _rooted(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return candidate


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _base_asset(row: dict) -> dict:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["company_name"],
        "market": row["exchange"], "country": row["country"], "currency": row["quoting_currency"],
        "price_sessions": int(row["price_sessions_available"]), "price_start": row["price_date_range_start"],
        "price_end": row["price_date_range_end"], "price_adjusted": row["exchange"] == "JPX",
        "eligibility_status": "BLOCKED", "confidence": "NOT_RANKABLE", "total_score": None,
        "rank": None, "coverage_weight": None, "pillar_scores": {}, "raw_factors": {},
        "strength_factors": [], "weakness_factors": [], "missing_factors": [], "review_reasons": [],
    }


def _validate_assets(assets: list[dict]) -> None:
    if len(assets) != 50 or len({r["asset_id"] for r in assets}) != 50:
        raise ValueError("expected 50 unique phase-8 assets")
    by_id = {r["asset_id"]: r for r in assets}
    if by_id["P020"]["eligibility_status"] != "REVIEW_REQUIRED" or by_id["P178"]["eligibility_status"] != "REVIEW_REQUIRED":
        raise ValueError("review-required assets were promoted")
    if any(r.get("rank") for r in assets if r["market"] == "TWSE"):
        raise ValueError("TWSE entered the main ranking")
    for row in assets:
        score = row.get("total_score")
        if score is not None and (not math.isfinite(float(score)) or not 0 <= float(score) <= 100):
            raise ValueError("invalid score")


def load_product_data(root: Path) -> ProductData:
    errors: list[str] = []
    universe_path = _rooted(root, UNIVERSE_REL)
    aggregate_path = _rooted(root, AGGREGATE_REL)
    if not universe_path.is_file() or not aggregate_path.is_file():
        return ProductData(DataMode.BLOCKED_MISSING_DATA, (), "", ("canonical universe or aggregate gate missing",))
    with universe_path.open(encoding="utf-8", newline="") as handle:
        assets = [_base_asset(row) for row in csv.DictReader(handle)]
    aggregate = _load_json(aggregate_path)
    if aggregate.get("decision") != "COMPLETED_SCOPED" or aggregate.get("phase7_authorized") is not False:
        return ProductData(DataMode.INCOMPATIBLE_VERSION, (), "", ("phase-6 aggregate contract mismatch",))
    by_id = {row["asset_id"]: row for row in assets}
    for row in assets:
        if row["asset_id"] in {"P020", "P178"}:
            row["eligibility_status"] = "REVIEW_REQUIRED"
            row["review_reasons"] = ["absolute_margin_outside_300pct" if row["asset_id"] == "P020" else "financial_institution_requires_separate_factor_contract"]
        elif row["market"] == "TWSE":
            row.update({"eligibility_status": "PARTIAL_COMPARABILITY", "confidence": "LOW"})
        else:
            row.update({"eligibility_status": "ELIGIBLE_PARTIAL", "confidence": "HIGH"})
    for item in aggregate["shortlist"]:
        by_id[item["asset_id"]].update({"rank": item["rank"], "total_score": item["score"]})
    local_results = _rooted(root, LOCAL_RESULTS_REL)
    local_scoring = local_results.is_file()
    if local_scoring:
        details = _load_json(local_results)
        if len(details) != 50:
            errors.append("local scoring result count mismatch")
            local_scoring = False
        else:
            for detail in details:
                asset = by_id.get(detail.get("asset_id"))
                if not asset:
                    errors.append("unknown asset in local scoring")
                    local_scoring = False
                    break
                asset.update({key: detail.get(key) for key in ("eligibility_status", "confidence", "total_score", "rank", "coverage_weight", "pillar_scores", "raw_factors", "review_reasons")})
                explanation = detail.get("explanation") or {}
                asset.update({"strength_factors": explanation.get("strength_factors", []), "weakness_factors": explanation.get("weakness_factors", []), "missing_factors": explanation.get("missing_factors", [])})
    normalized = _rooted(root, NORMALIZED_REL).is_file()
    derived = _rooted(root, DERIVED_REL).is_file()
    local_fundamentals = normalized and derived
    local_prices = all(_rooted(root, rel).is_dir() for rel in PRICE_RELS.values())
    try:
        _validate_assets(assets)
    except ValueError as exc:
        return ProductData(DataMode.INCOMPATIBLE_VERSION, (), aggregate.get("as_of_date", ""), (str(exc),))
    mode = DataMode.REAL_LOCAL_READY if local_scoring and local_fundamentals and local_prices else (DataMode.PARTIAL_DATA if any((local_scoring, local_fundamentals, local_prices)) else DataMode.AGGREGATE_ONLY)
    return ProductData(mode, tuple(assets), aggregate["as_of_date"], tuple(errors), local_scoring, local_fundamentals, local_prices)


def load_price_series(root: Path, asset: dict) -> list[dict]:
    path = _rooted(root, PRICE_RELS[asset["market"]]) / f'{asset["asset_id"]}.json'
    if not path.is_file():
        return []
    payload = _load_json(path)
    rows = []
    for row in payload.get("prices", []):
        value = row.get("AdjC", row.get("Adjusted_close", row.get("Close")))
        if row.get("Date") and value not in (None, ""):
            rows.append({"Date": row["Date"], "Close": float(value)})
    return sorted(rows, key=lambda item: item["Date"])


def load_fundamentals(root: Path, asset_id: str) -> list[dict]:
    rows = []
    for rel in (NORMALIZED_REL, DERIVED_REL):
        path = _rooted(root, rel)
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if item.get("asset_id") == asset_id and item.get("value") is not None:
                    rows.append(item)
    rows.sort(key=lambda item: (item.get("period_end") or "", item.get("metric") or ""), reverse=True)
    return rows
