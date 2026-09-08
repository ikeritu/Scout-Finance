#!/usr/bin/env python3
"""Block v2.38BT: flag which companies show the strongest already-computed
real growth signal ("unicornio" in the app's UI) -- reusing existing real
fields, never inventing a new weighted score or picking an arbitrary
threshold.

Why this exists: the user asked for a "unicornio" icon on the companies
with the most growth potential, on top of the "Ver en Google Finance"
convenience link. Picking a growth-magnitude cutoff (e.g. "revenue growth
above X%") would be exactly the kind of methodology judgment call Phase
9C's scoring is meant to formalize -- explicitly not authorized yet. This
block avoids that by reusing a flag that ALREADY EXISTS, already computed
and already documented, in v2.38G's US fundamental-feature extraction:
`fundamental_momentum_flag` -- real revenue growth > 0 AND a real margin
expansion versus the prior period AND a real positive free cash flow, all
three already-computed booleans, combined with a plain AND, never a
weighted composite.

Europe (Austria, via v2.38AK) never computed free-cash-flow-derived
features at all -- its own docstring says so explicitly, because
Austria's captured concepts do not include operating cash flow or capex.
Silently treating a missing FCF flag as "pass" would fabricate a signal
Austria's data was never able to support, so this block does NOT reuse
US_MOMENTUM's exact formula there. Instead it builds the closest same-
spirit combination using only the three real fields Austria's pipeline
actually produced: real revenue growth > 0 AND real growth acceleration
(this year's growth outpacing last year's) AND real margin expansion --
the same "more than one real signal must agree" idea, scoped honestly to
what each region's real data can support.

Every row keeps an explicit unicorn_status, never a silent False:
EVALUATED_UNICORN, EVALUATED_NOT_UNICORN (real data checked, criteria not
met), or INSUFFICIENT_DATA (the underlying growth features could not be
computed at all, so nothing is being claimed either way). Companies with
no real growth-feature row in any of the four source files simply do not
appear here at all -- the UI join defaults them to blank, the same
fail-open-to-blank convention already used for v2.38BO's eligibility
join, never "unicorn: false".

This block computes zero scores, zero ranks, and zero weighted composites.
Phase 9C remains explicitly unauthorized.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38BT-global-unicorn-flag"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bt_global_unicorn_flag"

US_ORIGINAL_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38g_us_sec_fundamental_features/us_sec_fundamental_features_v2_38g.csv"
US_CBOE_SECONDARY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bk_us_cboe_secondary_sec_fundamentals/us_cboe_secondary_sec_fundamental_features_v2_38bk.csv"
US_JOBY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ba_us_joby_aviation_fundamentals/us_joby_aviation_fundamental_features_v2_38ba.csv"
EUROPE_AUSTRIA_GROWTH_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ak_europe_growth_features/europe_growth_features_v2_38ak.csv"

# Same real cross-reference v2.38AL already applies: this Xetra/Cboe
# listing (8TQ) is the same real company as the original US asset, its
# ISIN's KY prefix reflecting only a 2021 SPAC-era shell, not its current
# Delaware/SEC-reporting reality.
JOBY_CAYMAN_ASSET_ID = "U37518"
JOBY_REAL_US_ASSET_ID = "U04441"

FIELDS = ["asset_id", "ticker", "company_name", "country", "source", "unicorn_status", "unicorn_reason", "phase"]

TRUE_STRINGS = {"true", "1", "yes"}


def flag(value: str | None) -> bool:
    return (value or "").strip().casefold() in TRUE_STRINGS


def as_float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def classify_us(row: dict[str, str]) -> tuple[str, str]:
    quality = row.get("feature_quality_status", "")
    if quality not in ("FEATURES_READY", "FEATURES_PARTIAL") or not row.get("revenue_yoy_growth"):
        return "INSUFFICIENT_DATA", "us_growth_features_not_computable_for_this_company"
    if flag(row.get("fundamental_momentum_flag")):
        return "EVALUATED_UNICORN", "us_fundamental_momentum_flag_true_real_revenue_growth_and_margin_expansion_and_positive_free_cash_flow"
    missing = []
    revenue_growth = as_float(row.get("revenue_yoy_growth"))
    if revenue_growth is None or revenue_growth <= 0:
        missing.append("revenue_growth_not_positive")
    if not flag(row.get("margin_expansion_flag")):
        missing.append("no_real_margin_expansion")
    if not flag(row.get("positive_fcf_flag")):
        missing.append("no_real_positive_free_cash_flow")
    return "EVALUATED_NOT_UNICORN", "us_fundamental_momentum_flag_false:" + ",".join(missing)


def classify_europe_austria(row: dict[str, str]) -> tuple[str, str]:
    quality = row.get("feature_quality_status", "")
    if quality not in ("FEATURES_READY", "FEATURES_PARTIAL") or not row.get("revenue_yoy_growth"):
        return "INSUFFICIENT_DATA", "europe_austria_growth_features_not_computable_for_this_company"
    revenue_growth = as_float(row.get("revenue_yoy_growth"))
    positive_growth = revenue_growth is not None and revenue_growth > 0
    accelerating = flag(row.get("growth_acceleration_flag"))
    margin_expanding = flag(row.get("margin_expansion_flag"))
    if positive_growth and accelerating and margin_expanding:
        return "EVALUATED_UNICORN", "europe_austria_real_revenue_growth_positive_and_accelerating_and_margin_expanding_no_free_cash_flow_data_available_for_austria"
    missing = []
    if not positive_growth:
        missing.append("revenue_growth_not_positive")
    if not accelerating:
        missing.append("no_real_growth_acceleration")
    if not margin_expanding:
        missing.append("no_real_margin_expansion")
    return "EVALUATED_NOT_UNICORN", "europe_austria_criteria_not_met:" + ",".join(missing)


def build_rows(source_rows: list[dict[str, str]], source: str, country: str, classify) -> list[dict[str, Any]]:
    rows = []
    for row in source_rows:
        status, reason = classify(row)
        rows.append({
            "asset_id": row.get("asset_id", ""), "ticker": row.get("ticker", ""), "company_name": row.get("company_name", ""),
            "country": country, "source": source, "unicorn_status": status, "unicorn_reason": reason, "phase": PHASE,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(
    us_original_path: Path, us_cboe_secondary_path: Path, us_joby_path: Path, europe_austria_path: Path, output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: dict[str, dict[str, Any]] = {}
    for entry in build_rows(read_csv(us_original_path), "us_sec_v2_38g", "US", classify_us):
        rows[entry["asset_id"]] = entry
    for entry in build_rows(read_csv(us_cboe_secondary_path), "us_cboe_secondary_sec_v2_38bk", "US", classify_us):
        rows[entry["asset_id"]] = entry
    for entry in build_rows(read_csv(us_joby_path), "us_joby_v2_38ba", "US", classify_us):
        rows[entry["asset_id"]] = entry
        if entry["asset_id"] == JOBY_REAL_US_ASSET_ID:
            cayman_entry = dict(entry)
            cayman_entry["asset_id"] = JOBY_CAYMAN_ASSET_ID
            cayman_entry["unicorn_reason"] = entry["unicorn_reason"] + ":cross_referenced_from_real_us_entity_u04441_same_real_company_per_v2_38az"
            rows[JOBY_CAYMAN_ASSET_ID] = cayman_entry
    for entry in build_rows(read_csv(europe_austria_path), "europe_austria_v2_38ak", "AT", classify_europe_austria):
        rows[entry["asset_id"]] = entry

    ordered_rows = list(rows.values())
    write_csv(output_dir / "global_unicorn_flag_v2_38bt.csv", ordered_rows, FIELDS)

    status_counts = Counter(r["unicorn_status"] for r in ordered_rows)
    unicorn_examples = [r["company_name"] for r in ordered_rows if r["unicorn_status"] == "EVALUATED_UNICORN"][:10]

    report = {
        "phase": PHASE,
        "status": "COMPLETED_GLOBAL_UNICORN_FLAG_DEFINED_NOT_SCORED",
        "companies_with_growth_features_evaluated": len(ordered_rows),
        "unicorn_status_counts": dict(sorted(status_counts.items())),
        "unicorn_examples": sorted(unicorn_examples),
        "note": "Flags companies whose ALREADY-COMPUTED real growth features (never re-derived or estimated here) meet a real, pre-existing multi-signal combination -- v2.38G's own fundamental_momentum_flag for US-origin companies (real revenue growth>0 AND real margin expansion AND real positive free cash flow), and the closest same-spirit combination for Austria (v2.38AK, no free-cash-flow data available there) using only its real fields (real revenue growth>0 AND real growth acceleration AND real margin expansion). No new weighted score, no arbitrary percentage threshold invented -- a plain AND over pre-existing real booleans. Companies with no growth-feature row in any of the four source files simply do not appear here; the UI defaults them to blank, never to a silent 'not a unicorn'.",
        "guardrails": {"network_used": False, "scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False, "phase9c_authorized": False},
    }
    write_text(output_dir / "global_unicorn_flag_report_v2_38bt.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest = {"phase": PHASE, "outputs": {"global_unicorn_flag_v2_38bt.csv": {"bytes": (output_dir / "global_unicorn_flag_v2_38bt.csv").stat().st_size, "sha256": sha256(output_dir / "global_unicorn_flag_v2_38bt.csv")}}, "guardrails": report["guardrails"]}
    write_text(output_dir / "global_unicorn_flag_manifest_v2_38bt.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--us-original-input", type=Path, default=US_ORIGINAL_INPUT)
    parser.add_argument("--us-cboe-secondary-input", type=Path, default=US_CBOE_SECONDARY_INPUT)
    parser.add_argument("--us-joby-input", type=Path, default=US_JOBY_INPUT)
    parser.add_argument("--europe-austria-input", type=Path, default=EUROPE_AUSTRIA_GROWTH_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.us_original_input, args.us_cboe_secondary_input, args.us_joby_input, args.europe_austria_input, args.output_dir)
    print(json.dumps({k: report[k] for k in ("phase", "status", "companies_with_growth_features_evaluated", "unicorn_status_counts")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
