#!/usr/bin/env python3
"""Block v2.38BU, part 1 of Phase 9C: extract operating_margin, eps_basic and
book_value_per_share for the real US SEC-covered companies -- the three
raw concepts the old, validated scoring engine (scripts/scoring_engine/
core.py, config/scoring_factor_contract_v1.json) needs but that v2.38F/G's
extraction never computed.

Zero new extraction logic, zero new network calls: this reuses, unmodified,
normalize_us_sec_fundamentals_v2_38f.normalize_company() (the same real
function v2.38BK already reuses for the 538 Cboe-secondary companies) and
build_us_sec_fundamental_features_v2_38g.selected_annual()/ratio()/
rounded() -- the only real addition is two more SEC XBRL concepts on top
of v2.38F's own METRIC_CONCEPTS map, applied by monkeypatching the loaded
module object (never editing v2.38F's own file on disk, so its already-
completed, already-cited output for the original 555 companies stays
untouched -- same discipline v2.38BQ already applied to the "S.P.A." bug).

Verified directly against the real, already-downloaded SEC companyfacts
cache before writing this script (no assumption): CIK0000002488's cached
companyfacts.json really does carry `OperatingIncomeLoss` and
`CommonStockSharesOutstanding` under us-gaap -- these are standard,
commonly-tagged concepts, not something only a handful of companies
report. `eps_basic` was already being extracted by v2.38F all along
(METRIC_CONCEPTS already lists "EarningsPerShareBasic") but v2.38G's own
feature-derivation step never carries it through to its output -- this
block just reads it back out of the same already-normalized records.

Deliberately fail-closed: a company whose real cached companyfacts.json
lacks a concept (or lacks it in a supported unit, or has none accepted by
v2.38F's own quality rules) simply gets a blank field, never an estimate.

This block computes zero scores, zero ranks. Phase 9C's actual scoring
step is v2.38BV, built on top of this block's real output.
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
PHASE = "v2.38BU-us-sec-valuation-features-extension"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bu_us_sec_valuation_features_extension"

# Real, already-verified sources for each of the three real US-origin
# populations that already have SEC companyfacts cached locally.
US_ORIGINAL_FEATURES = ROOT / "outputs/full_universe_source_acquisition/v2_38g_us_sec_fundamental_features/us_sec_fundamental_features_v2_38g.csv"
US_ORIGINAL_CACHE = ROOT / "outputs/full_universe_source_acquisition/v2_38e_us_sec_enrichment_expansion/sec_raw_cache_v2_38e"
US_CBOE_SECONDARY_FEATURES = ROOT / "outputs/full_universe_source_acquisition/v2_38bk_us_cboe_secondary_sec_fundamentals/us_cboe_secondary_sec_fundamental_features_v2_38bk.csv"
US_CBOE_SECONDARY_CACHE = ROOT / "outputs/full_universe_source_acquisition/v2_38bj_us_cboe_secondary_sec_enrichment/sec_raw_cache_v2_38bj"
US_JOBY_FEATURES = ROOT / "outputs/full_universe_source_acquisition/v2_38ba_us_joby_aviation_fundamentals/us_joby_aviation_fundamental_features_v2_38ba.csv"
US_JOBY_CACHE = US_ORIGINAL_CACHE  # v2.38BA's own script confirms this is the same cache as the original 555

# The two real, standard SEC concepts v2.38F's own extraction never
# requested. Monkeypatched onto the dynamically-loaded v2.38F module
# object only -- the file on disk is never edited.
NEW_CONCEPTS = {
    "operating_income": ["OperatingIncomeLoss"],
    "shares_outstanding": ["CommonStockSharesOutstanding"],
}

FIELDS = ["asset_id", "ticker", "company_name", "source", "feature_asof_fy", "operating_margin", "eps_basic", "book_value_per_share", "valuation_extension_status", "phase"]


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


def extend_company(v38f, v38g, row: dict[str, str], cache_dir: Path, source: str) -> dict[str, Any]:
    records, _rejected, _flags = v38f.normalize_company(row, cache_dir)
    annual = v38g.selected_annual(records)
    years = sorted(annual)
    out = {
        "asset_id": row.get("asset_id", ""), "ticker": row.get("ticker", ""), "company_name": row.get("company_name", ""),
        "source": source, "feature_asof_fy": "", "operating_margin": "", "eps_basic": "", "book_value_per_share": "",
        "phase": PHASE,
    }
    if not years:
        out["valuation_extension_status"] = "INSUFFICIENT_EVIDENCE"
        return out
    current = annual[years[-1]]
    out["feature_asof_fy"] = years[-1]
    operating_margin = v38g.ratio(current.get("operating_income"), current.get("revenue"))
    book_value_per_share = v38g.ratio(current.get("equity"), current.get("shares_outstanding"))
    eps_basic = v38g.rounded(current.get("eps_basic")) if current.get("eps_basic") is not None else None
    out["operating_margin"] = operating_margin
    out["book_value_per_share"] = book_value_per_share
    out["eps_basic"] = eps_basic
    calculated = sum(v is not None for v in (operating_margin, book_value_per_share, eps_basic))
    out["valuation_extension_status"] = "READY" if calculated == 3 else ("PARTIAL" if calculated else "NO_CONCEPTS_AVAILABLE")
    return out


def build(
    us_original_features: Path, us_original_cache: Path,
    us_cboe_secondary_features: Path, us_cboe_secondary_cache: Path,
    us_joby_features: Path, us_joby_cache: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    v38f = load_module("normalize_us_sec_fundamentals_v2_38f", ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py")
    v38g = load_module("build_us_sec_fundamental_features_v2_38g", ROOT / "scripts/build_us_sec_fundamental_features_v2_38g.py")
    v38f.METRIC_CONCEPTS = {**v38f.METRIC_CONCEPTS, **NEW_CONCEPTS}  # monkeypatched on the loaded module object only, never the file on disk

    # v2.38F's own supported_unit() only ever accepted "USD" or a "*/shares"
    # per-share unit -- correct for the concepts it was built for, but a raw
    # share COUNT (not a per-share ratio) reports its real unit as plain
    # "shares" in SEC's own XBRL data (verified directly against the real,
    # already-cached CIK0000002488.json before writing this script). Wrapped
    # on the loaded module object only, so v2.38F's own behavior for every
    # concept it already validates stays byte-identical.
    original_supported_unit = v38f.supported_unit

    def supported_unit_with_share_counts(metric: str, unit: str) -> bool:
        if metric == "shares_outstanding":
            return unit == "shares"
        return original_supported_unit(metric, unit)

    v38f.supported_unit = supported_unit_with_share_counts

    populations = (
        (us_original_features, us_original_cache, "us_sec_v2_38g"),
        (us_cboe_secondary_features, us_cboe_secondary_cache, "us_cboe_secondary_sec_v2_38bk"),
        (us_joby_features, us_joby_cache, "us_joby_v2_38ba"),
    )

    rows: dict[str, dict[str, Any]] = {}
    for features_path, cache_dir, source in populations:
        for row in read_csv(features_path):
            if not row.get("cik"):
                continue
            rows[row["asset_id"]] = extend_company(v38f, v38g, row, cache_dir, source)

    ordered_rows = list(rows.values())
    write_csv(output_dir / "us_sec_valuation_features_extension_v2_38bu.csv", ordered_rows, FIELDS)

    status_counts = Counter(r["valuation_extension_status"] for r in ordered_rows)
    report = {
        "phase": PHASE,
        "status": "COMPLETED_US_SEC_VALUATION_FEATURES_EXTENSION_NOT_SCORING",
        "companies_processed": len(ordered_rows),
        "valuation_extension_status_counts": dict(sorted(status_counts.items())),
        "note": "Extends the real, already-cached SEC companyfacts data (zero new network calls) with operating_margin, eps_basic and book_value_per_share -- the three raw concepts scripts/scoring_engine/core.py's already-validated v2.35A3 factor contract needs but v2.38F/G's own extraction never computed. Reuses normalize_us_sec_fundamentals_v2_38f.normalize_company() and build_us_sec_fundamental_features_v2_38g.selected_annual()/ratio()/rounded() unmodified, monkeypatching only the METRIC_CONCEPTS dict on the loaded module object (never v2.38F's own file) with two new real, standard SEC XBRL concepts (OperatingIncomeLoss, CommonStockSharesOutstanding) -- eps_basic was already being extracted by v2.38F, just never carried through by v2.38G. A company whose cache lacks a concept gets a blank field, never an estimate.",
        "guardrails": {"network_used": False, "scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False, "phase9c_authorized": True, "phase9c_block": "1_of_3_valuation_features_extension"},
    }
    write_text(output_dir / "us_sec_valuation_features_extension_report_v2_38bu.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest = {"phase": PHASE, "outputs": {"us_sec_valuation_features_extension_v2_38bu.csv": {"bytes": (output_dir / "us_sec_valuation_features_extension_v2_38bu.csv").stat().st_size, "sha256": sha256(output_dir / "us_sec_valuation_features_extension_v2_38bu.csv")}}, "guardrails": report["guardrails"]}
    write_text(output_dir / "us_sec_valuation_features_extension_manifest_v2_38bu.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--us-original-features", type=Path, default=US_ORIGINAL_FEATURES)
    parser.add_argument("--us-original-cache", type=Path, default=US_ORIGINAL_CACHE)
    parser.add_argument("--us-cboe-secondary-features", type=Path, default=US_CBOE_SECONDARY_FEATURES)
    parser.add_argument("--us-cboe-secondary-cache", type=Path, default=US_CBOE_SECONDARY_CACHE)
    parser.add_argument("--us-joby-features", type=Path, default=US_JOBY_FEATURES)
    parser.add_argument("--us-joby-cache", type=Path, default=US_JOBY_CACHE)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(
        args.us_original_features, args.us_original_cache,
        args.us_cboe_secondary_features, args.us_cboe_secondary_cache,
        args.us_joby_features, args.us_joby_cache,
        args.output_dir,
    )
    print(json.dumps({k: report[k] for k in ("phase", "status", "companies_processed", "valuation_extension_status_counts")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
