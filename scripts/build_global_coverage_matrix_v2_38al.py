#!/usr/bin/env python3
"""Build the v2.38AL global coverage matrix: one row for every one of the
43,089 companies in the operational census (v2.38A), honestly flagging
how far this pipeline's real work has actually reached for each one --
never scoring, ranking, or recommending anything.

This is the first concrete piece of the architecture the user confirmed
wanting after the project's growth-shortlist reframing: press an
"actualizar" button and see the full 43,000-company universe, with
companies lacking real data plainly marked "sin datos todavia" rather
than hidden. Today's real coverage is tiny (689 Europe identities, 20
Austrian companies with real fundamentals/growth, 555 US companies with
real fundamentals, 554 with real prices) against a 43,089-company
census -- this script's whole purpose is to make that gap visible and
honest, not to close it.

Design choice, explained: identity -> fundamentals -> growth is treated
as one depth ladder (`overall_coverage_status`), because each stage
strictly requires the one before it in this pipeline. Price is tracked
as a SEPARATE column (`price_status`), never folded into that ladder --
Europe's real, confirmed finding (v2.38AJ: no free European price
source exists) would otherwise make every Europe growth-ready company
look exactly like "no data at all", which would bury the real signal
that IS there (identity, fundamentals, growth) under a structural gap
that has nothing to do with those companies' own data quality.

No census row is ever dropped or excluded here -- unlike every other
builder in this pipeline (which reports rejections for what it could
NOT compute), this script's entire point is that all 43,089 rows always
appear in the output, so "rejection" is not a concept that applies.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38al_global_coverage_matrix"
PHASE = "v2.38AL-global-coverage-matrix"

CENSUS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit/global_universe_audited_v2_38a.csv.xz"
US_FUNDAMENTALS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38g_us_sec_fundamental_features/us_sec_fundamental_features_v2_38g.csv"
US_PRICE_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38h_us_price_features/us_price_features_v2_38h.csv"
EUROPE_IDENTITY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ab_europe_full_identity_resolution/europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv"
EUROPE_FUNDAMENTALS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38x_europe_candidate_feature_matrix/europe_fundamental_features_v2_38x.csv"
EUROPE_GROWTH_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ak_europe_growth_features/europe_growth_features_v2_38ak.csv"

# v2.38G packs both same-period ratios AND growth-over-time features into
# one row per US company -- unlike Europe, where those two are split
# across separate phases (v2.38X ratios, v2.38AK growth). To place a US
# company correctly on the same identity->fundamentals->growth ladder as
# a European one, its single row is split back into these two groups by
# presence, using the exact field names from build_us_sec_fundamental_
# features_v2_38g.py.
US_GROWTH_FIELDS = ["revenue_yoy_growth", "net_income_yoy_growth", "operating_cash_flow_yoy_growth", "assets_yoy_growth", "equity_yoy_growth"]
US_FUNDAMENTAL_RATIO_FIELDS = ["net_margin", "return_on_assets", "return_on_equity", "operating_cash_flow_margin", "liabilities_to_assets", "equity_to_assets", "free_cash_flow", "free_cash_flow_margin", "capex_to_revenue", "cash_conversion_ratio"]

NOT_ATTEMPTED = "NOT_ATTEMPTED"
LADDER_STATUSES = ["INSUFFICIENT_FEATURE_EVIDENCE", "FEATURES_PARTIAL", "FEATURES_READY"]

FIELDS = [
    "asset_id", "ticker", "company_name", "exchange", "country", "sector",
    "census_eligibility_status", "census_route_status",
    "identity_status", "identity_source",
    "fundamentals_status", "fundamentals_source",
    "growth_status", "growth_source",
    "price_status", "price_source",
    "overall_coverage_status", "phase",
]


def relative_or_str(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_csv_xz(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    """Same atomic-write discipline as write_csv, but compressed -- this
    output carries one row per census company (43,089 rows), the same
    scale as v2.38A's own detailed audit file, which set the precedent
    of shipping that scale as .csv.xz (544KB compressed) rather than a
    multi-megabyte plain CSV in git."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with lzma.open(tmp, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def read_census(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"BLOCKED: required v2.38A global universe census not found: {path}")
    opener = lzma.open if path.suffix == ".xz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_csv_index(path: Path) -> dict[str, dict[str, str]]:
    """Index a CSV by asset_id. A missing file is treated as an honestly-
    empty index (0 companies covered by that phase yet), never an error --
    every other real block in this pipeline follows the same convention
    for an input that some future phase simply hasn't produced yet."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {row["asset_id"]: row for row in csv.DictReader(f)}


def present(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def classify_ladder(present_count: int, total_count: int) -> str:
    if total_count == 0 or present_count == 0:
        return "INSUFFICIENT_FEATURE_EVIDENCE"
    if present_count == total_count:
        return "FEATURES_READY"
    return "FEATURES_PARTIAL"


def build_row(census_row: dict[str, str], us_fund: dict[str, str] | None, us_price: dict[str, str] | None, eu_identity: dict[str, str] | None, eu_fund: dict[str, str] | None, eu_growth: dict[str, str] | None) -> dict[str, Any]:
    asset_id = census_row["asset_id"]
    row: dict[str, Any] = {field: NOT_ATTEMPTED for field in FIELDS}
    row.update({
        "asset_id": asset_id, "ticker": census_row.get("ticker", ""), "company_name": census_row.get("company_name", ""),
        "exchange": census_row.get("exchange", ""), "country": census_row.get("country", ""), "sector": census_row.get("sector", ""),
        "census_eligibility_status": census_row.get("eligibility_status", ""), "census_route_status": census_row.get("route_status", ""),
        "identity_source": "", "fundamentals_source": "", "growth_source": "", "price_source": "", "phase": PHASE,
    })

    if us_fund is not None:
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = "v2.38D-F"  # SEC CIK-matched foundation/enrichment/normalization
        growth_present = sum(1 for field in US_GROWTH_FIELDS if present(us_fund.get(field)))
        fund_present = sum(1 for field in US_FUNDAMENTAL_RATIO_FIELDS if present(us_fund.get(field)))
        row["fundamentals_status"] = classify_ladder(fund_present, len(US_FUNDAMENTAL_RATIO_FIELDS))
        row["fundamentals_source"] = "v2.38G"
        row["growth_status"] = classify_ladder(growth_present, len(US_GROWTH_FIELDS))
        row["growth_source"] = "v2.38G"
        if us_price is not None:
            row["price_status"] = us_price.get("price_feature_quality_status", NOT_ATTEMPTED)
            row["price_source"] = "v2.38H"
    elif eu_identity is not None:
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = "v2.38AB"
        # A real, confirmed negative finding (v2.38AJ: five sources
        # investigated, none viable) -- not "we haven't looked yet".
        row["price_status"] = "NOT_COLLECTED_NO_FREE_SOURCE_FOUND"
        row["price_source"] = "v2.38AJ"
        if eu_fund is not None:
            row["fundamentals_status"] = eu_fund.get("feature_quality_status", NOT_ATTEMPTED)
            row["fundamentals_source"] = "v2.38X"
        if eu_growth is not None:
            row["growth_status"] = eu_growth.get("feature_quality_status", NOT_ATTEMPTED)
            row["growth_source"] = "v2.38AK"

    row["overall_coverage_status"] = overall_status(row["identity_status"], row["fundamentals_status"], row["growth_status"])
    return row


def overall_status(identity_status: str, fundamentals_status: str, growth_status: str) -> str:
    if identity_status == NOT_ATTEMPTED:
        return "NO_DATA_YET"
    if fundamentals_status in (NOT_ATTEMPTED, "INSUFFICIENT_FEATURE_EVIDENCE"):
        return "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"
    if growth_status in (NOT_ATTEMPTED, "INSUFFICIENT_FEATURE_EVIDENCE"):
        return "FUNDAMENTALS_READY_NO_GROWTH_YET" if fundamentals_status == "FEATURES_READY" else "FUNDAMENTALS_PARTIAL_NO_GROWTH_YET"
    return "GROWTH_READY" if growth_status == "FEATURES_READY" else "GROWTH_PARTIAL"


def build(census_path: Path, us_fund_path: Path, us_price_path: Path, eu_identity_path: Path, eu_fund_path: Path, eu_growth_path: Path, output_dir: Path) -> dict[str, Any]:
    census = read_census(census_path)
    us_fund_idx = read_csv_index(us_fund_path)
    us_price_idx = read_csv_index(us_price_path)
    eu_identity_idx = read_csv_index(eu_identity_path)
    eu_fund_idx = read_csv_index(eu_fund_path)
    eu_growth_idx = read_csv_index(eu_growth_path)

    rows = [
        build_row(
            c, us_fund_idx.get(c["asset_id"]), us_price_idx.get(c["asset_id"]),
            eu_identity_idx.get(c["asset_id"]), eu_fund_idx.get(c["asset_id"]), eu_growth_idx.get(c["asset_id"]),
        )
        for c in census
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv_xz(output_dir / "global_coverage_matrix_v2_38al.csv.xz", rows, FIELDS)

    overall_counts = Counter(r["overall_coverage_status"] for r in rows)
    identity_counts = Counter(r["identity_status"] for r in rows)
    price_counts = Counter(r["price_status"] for r in rows)
    by_country: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_country[r["country"]][r["overall_coverage_status"]] += 1
    country_summary = [
        {"country": country, **{status: counts.get(status, 0) for status in overall_counts}}
        for country, counts in sorted(by_country.items(), key=lambda kv: -sum(kv[1].values()))
        if sum(counts.values()) >= 20  # keep the summary readable; the full per-company detail is in the main CSV regardless
    ]
    write_csv(output_dir / "global_coverage_country_summary_v2_38al.csv", country_summary, ["country"] + sorted(overall_counts))

    report = {
        "phase": PHASE,
        "companies_total": len(rows),
        "companies_expected_from_census": 43089,
        "overall_coverage_status_counts": dict(sorted(overall_counts.items())),
        "identity_status_counts": dict(sorted(identity_counts.items())),
        "price_status_counts": dict(sorted(price_counts.items())),
        "network_used": False, "scoring_created": False, "ranking_created": False,
        "recommendations_created": False, "phase9c_authorized": False,
        "inputs_used": {
            "census": relative_or_str(census_path),
            "us_fundamentals": relative_or_str(us_fund_path) if us_fund_idx else None,
            "us_price": relative_or_str(us_price_path) if us_price_idx else None,
            "europe_identity": relative_or_str(eu_identity_path) if eu_identity_idx else None,
            "europe_fundamentals": relative_or_str(eu_fund_path) if eu_fund_idx else None,
            "europe_growth": relative_or_str(eu_growth_path) if eu_growth_idx else None,
        },
        "note": "overall_coverage_status follows the identity->fundamentals->growth depth ladder only; price_status is tracked separately and deliberately excluded from that ladder, because Europe's confirmed 0% free price coverage (v2.38AJ) would otherwise make every Europe growth-ready company indistinguishable from one with no data at all. Every one of the census's rows appears exactly once in the output -- this script never drops or excludes a row, unlike every other builder in this pipeline.",
    }
    write_text(output_dir / "global_coverage_matrix_report_v2_38al.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census-input", type=Path, default=CENSUS_INPUT)
    parser.add_argument("--us-fundamentals-input", type=Path, default=US_FUNDAMENTALS_INPUT)
    parser.add_argument("--us-price-input", type=Path, default=US_PRICE_INPUT)
    parser.add_argument("--europe-identity-input", type=Path, default=EUROPE_IDENTITY_INPUT)
    parser.add_argument("--europe-fundamentals-input", type=Path, default=EUROPE_FUNDAMENTALS_INPUT)
    parser.add_argument("--europe-growth-input", type=Path, default=EUROPE_GROWTH_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.census_input, args.us_fundamentals_input, args.us_price_input, args.europe_identity_input, args.europe_fundamentals_input, args.europe_growth_input, args.output_dir)
    print(json.dumps({k: report[k] for k in ("phase", "companies_total", "overall_coverage_status_counts")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
