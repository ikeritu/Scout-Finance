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

# Real new sources added in the twelfth reconstruction (2026-09-07),
# incorporating everything found while attacking the "hueco de Cboe
# Europe": the 25 mismatch assets (v2.38AV) that revealed 5 countries
# never touched before, Luxembourg's real fundamentals (original 20 via
# v2.38AW/AX plus 17 more via v2.38BE), Austria's and Finland's new
# identities (v2.38BF/BG/BH), Joby Aviation's real US identity correcting
# its Cayman-by-ISIN-prefix classification (v2.38AZ/BA), and the bulk
# 54-country Cboe Europe identity resolution (v2.38BC) for everything
# that does not have a more specific, richer source above it.
US_JOBY_AVIATION_FEATURES_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ba_us_joby_aviation_fundamentals/us_joby_aviation_fundamental_features_v2_38ba.csv"
JOBY_CAYMAN_ASSET_ID = "U37518"  # the Xetra/Cboe listing (8TQ) of the same real company as US asset U04441
JOBY_REAL_US_ASSET_ID = "U04441"

AV_MISMATCH_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38av_europe_mismatch_identity_resolution/europe_mismatch_identity_resolution_matrix_v2_38av.csv"
LUX_AW_RCS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38aw_europe_luxembourg_rcs_gleif/europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv"
LUX_AX_FUNDAMENTALS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ax_europe_luxembourg_fundamentals/europe_luxembourg_fundamental_records_v2_38ax.jsonl"
LUX_BE_RCS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38be_europe_cboe_luxembourg_extension/europe_cboe_luxembourg_extension_rcs_matrix_v2_38be.csv"
LUX_BE_FUNDAMENTALS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38be_europe_cboe_luxembourg_extension/europe_cboe_luxembourg_extension_fundamental_records_v2_38be.jsonl"
LUX_BE_FUND_COMPARTMENTS_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38be_europe_cboe_luxembourg_extension/europe_cboe_luxembourg_extension_fund_compartments_excluded_v2_38be.jsonl"
AT_BG_REGISTRY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bg_europe_cboe_austria_extension/europe_cboe_austria_extension_registry_matrix_v2_38bg.csv"
FI_BH_REGISTRY_SECTOR_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bh_europe_cboe_finland_extension/europe_cboe_finland_extension_registry_sector_v2_38bh.csv"
CBOE_BULK_IDENTITY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bc_europe_cboe_secondary_identity_full/europe_cboe_secondary_identity_full_matrix_v2_38bc.csv"

# Real new source added in the fourteenth reconstruction (2026-09-08),
# attacking the UK/US front the user chose after "consolidar primero"
# closed: 538 of the 628 country=US Cboe secondary candidates (already
# GLEIF-identified by v2.38BC) got a real SEC CIK match via v2.38BI,
# which then let v2.38BK reuse the exact same v2.38F/G fundamentals
# extraction already proven on the original 555 companies. Without this,
# these 538 would fall all the way through to the generic Cboe-bulk
# fallback branch below and be stuck at identity-only forever, despite
# now having real US GAAP fundamentals and growth on file.
US_CBOE_SECONDARY_IDENTITY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bi_us_cboe_secondary_identity_sec/us_cboe_secondary_identity_sec_v2_38bi.csv"
US_CBOE_SECONDARY_FEATURES_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bk_us_cboe_secondary_sec_fundamentals/us_cboe_secondary_sec_fundamental_features_v2_38bk.csv"

# v2.38AV reports the real country as a readable name (from the ISIN
# prefix), not the 2-letter code the rest of this matrix's "country"
# column already uses everywhere else -- mapped here just for display
# consistency, never used to decide anything.
AV_COUNTRY_NAME_TO_CODE = {"Luxembourg": "LU", "Bulgaria": "BG", "Liechtenstein": "LI", "Cayman Islands": "KY", "Malta": "MT"}

LUX_FUNDAMENTAL_CONCEPTS = ["revenue", "net_profit", "total_assets", "equity"]

# Real, confirmed legal facts added in the fifteenth reconstruction
# (2026-09-08): these 6 jurisdictions' company law does not require an
# exempted/non-resident company to publicly file financial statements at
# all -- confirmed per jurisdiction (Bermuda's Companies Act exempted-
# company regime, BVI's Business Companies Act annual financial return
# kept privately at the registered agent, Guernsey's Companies Law no
# public-filing requirement, the Marshall Islands' Associations Law for
# non-resident domestic corporations, the Isle of Man's Companies
# Registry not centrally holding filed accounts even for 1931 Act public
# companies, and Cayman's exempted-company regime already confirmed in
# v2.38AZ). This is a structural, jurisdiction-wide legal fact, not a
# per-company investigation -- it applies to every real company under
# that country code the same way v2.38BE's fund-compartment detection
# applies to every Luxembourg sub-fund. Jersey is deliberately excluded:
# its public companies DO have a real statutory duty to file audited
# accounts, and the census population here is overwhelmingly PLCs (3i
# Infrastructure PLC, B&M European Value Retail plc...) -- closing it the
# same way would risk hiding real disclosure, so it stays untouched
# pending its own investigation (v2.38BM's real, honest open question).
OFFSHORE_NO_DISCLOSURE_COUNTRIES = {"KY", "BM", "VG", "GG", "MH", "IM"}

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


def read_jsonl_concepts_by_asset(path: Path) -> dict[str, dict[str, str]]:
    """Index a v2.38AX/BE-style fundamentals jsonl by asset_id -> its
    'concepts' dict (each concept a {'label','value','field_id'} triple).
    A missing file is an honestly-empty index, same convention as
    read_csv_index."""
    if not path.exists():
        return {}
    index: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("fetch_status") == "resolved":
                index[record["asset_id"]] = record.get("concepts", {})
    return index


def read_jsonl_asset_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ids.add(json.loads(line)["asset_id"])
    return ids


def classify_lux_fundamentals(concepts: dict[str, str]) -> str:
    present_count = sum(1 for c in LUX_FUNDAMENTAL_CONCEPTS if c in concepts)
    return classify_ladder(present_count, len(LUX_FUNDAMENTAL_CONCEPTS))


def build_luxembourg_index(av_path: Path, aw_rcs_path: Path, ax_fund_path: Path, be_rcs_path: Path, be_fund_path: Path, be_fund_compartments_path: Path) -> dict[str, dict[str, Any]]:
    """Merge every Luxembourg source discovered across this project's
    Luxembourg effort into one asset_id-keyed index: the original 20
    identities (v2.38AV), their RCS numbers and real fundamentals
    (v2.38AW/AX), and the 17 more candidates v2.38BC/BE later found (11
    real companies + 6 investment fund compartments correctly excluded
    from fundamentals as a category error, not a data gap)."""
    index: dict[str, dict[str, Any]] = {}
    if av_path.exists():
        with av_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("real_home_country_guess") == "Luxembourg" and row.get("resolution_status") == "resolved":
                    index[row["asset_id"]] = {"identity_source": "v2.38AV", "is_fund": False}
    ax_concepts = read_jsonl_concepts_by_asset(ax_fund_path)
    for asset_id, concepts in ax_concepts.items():
        if asset_id in index:
            index[asset_id]["concepts"] = concepts
            index[asset_id]["fundamentals_source"] = "v2.38AX"
    if be_rcs_path.exists():
        with be_rcs_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("gleif_lookup_status") != "resolved":
                    continue
                is_fund = not row.get("rcs_number", "").startswith("B")
                index[row["asset_id"]] = {"identity_source": "v2.38BE", "is_fund": is_fund}
    be_concepts = read_jsonl_concepts_by_asset(be_fund_path)
    for asset_id, concepts in be_concepts.items():
        if asset_id in index:
            index[asset_id]["concepts"] = concepts
            index[asset_id]["fundamentals_source"] = "v2.38BE"
    for asset_id in read_jsonl_asset_ids(be_fund_compartments_path):
        if asset_id in index:
            index[asset_id]["is_fund"] = True
    return index


def build_at_bg_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    index: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("gleif_lookup_status") == "resolved":
                index[row["asset_id"]] = {"identity_source": "v2.38BF/BG"}
    return index


def build_fi_bh_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    index: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("fetch_status") == "resolved":
                index[row["asset_id"]] = {"identity_source": "v2.38BF/BH", "sector": row.get("tol_description_en", "")}
    return index


def build_av_other_index(path: Path) -> dict[str, dict[str, Any]]:
    """The 4 non-Luxembourg, non-Joby-special v2.38AV countries: Bulgaria,
    Liechtenstein, Malta (the 5th, Cayman Islands, is the Joby Aviation
    asset handled separately below since its real country is US, not the
    ISIN-prefix jurisdiction)."""
    if not path.exists():
        return {}
    index: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            country_name = row.get("real_home_country_guess", "")
            if row.get("resolution_status") == "resolved" and country_name in {"Bulgaria", "Liechtenstein", "Malta"}:
                index[row["asset_id"]] = {"identity_source": "v2.38AV", "country_code": AV_COUNTRY_NAME_TO_CODE.get(country_name, country_name)}
    return index


def build_us_cboe_secondary_index(identity_path: Path, features_path: Path) -> dict[str, dict[str, Any]]:
    """Merge v2.38BI's real SEC CIK matches with v2.38BK's fundamentals/
    growth features (reusing v2.38G's exact field names, since v2.38BK
    calls the same build_company() function). Only the 538 CIK-resolved
    candidates get an entry here -- the other 90 (delisted/acquired
    companies, or a handful mislabeled country=US in the source) fall
    through to the generic Cboe-bulk fallback branch unchanged, same as
    before this reconstruction."""
    if not identity_path.exists():
        return {}
    index: dict[str, dict[str, Any]] = {}
    with identity_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("fetch_status") == "resolved":
                index[row["asset_id"]] = {"identity_source": "v2.38BI"}
    if not features_path.exists():
        return index
    with features_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            asset_id = row.get("asset_id", "")
            if asset_id in index:
                index[asset_id]["features"] = row
    return index


def build_cboe_bulk_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    index: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") == "resolved":
                index[row["asset_id"]] = {"identity_source": "v2.38BC", "country_code": row.get("country", "")}
    return index


def classify_ladder(present_count: int, total_count: int) -> str:
    if total_count == 0 or present_count == 0:
        return "INSUFFICIENT_FEATURE_EVIDENCE"
    if present_count == total_count:
        return "FEATURES_READY"
    return "FEATURES_PARTIAL"


def build_row(
    census_row: dict[str, str], us_fund: dict[str, str] | None, us_price: dict[str, str] | None,
    eu_identity: dict[str, str] | None, eu_fund: dict[str, str] | None, eu_growth: dict[str, str] | None,
    joby_us_features: dict[str, str] | None, lux_entry: dict[str, Any] | None, at_entry: dict[str, Any] | None,
    fi_entry: dict[str, Any] | None, av_other_entry: dict[str, Any] | None, cboe_entry: dict[str, Any] | None,
    us_cboe_secondary_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
    elif asset_id == JOBY_CAYMAN_ASSET_ID and joby_us_features is not None:
        # Real correction from v2.38AZ: this Xetra/Cboe listing (8TQ) is
        # the SAME real company as US asset U04441 (Joby Aviation, Inc.)
        # -- its ISIN's KY prefix reflects only a 2021 SPAC-era shell, not
        # its current Delaware/SEC-reporting reality. Its fundamentals are
        # the real company's own SEC data, cross-referenced, not
        # duplicated or re-derived.
        row["country"] = "US"
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = "v2.38AZ (real country corrected from ISIN-prefix Cayman Islands to actual US/Delaware, via SEC EDGAR)"
        growth_present = sum(1 for field in US_GROWTH_FIELDS if present(joby_us_features.get(field)))
        fund_present = sum(1 for field in US_FUNDAMENTAL_RATIO_FIELDS if present(joby_us_features.get(field)))
        row["fundamentals_status"] = classify_ladder(fund_present, len(US_FUNDAMENTAL_RATIO_FIELDS))
        row["fundamentals_source"] = f"v2.38BA (via {JOBY_REAL_US_ASSET_ID}, same real company)"
        row["growth_status"] = classify_ladder(growth_present, len(US_GROWTH_FIELDS))
        row["growth_source"] = f"v2.38BA (via {JOBY_REAL_US_ASSET_ID}, same real company)"
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
    elif lux_entry is not None:
        row["country"] = "LU"
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = lux_entry["identity_source"]
        row["price_status"] = "NOT_COLLECTED_NO_FREE_SOURCE_FOUND"
        row["price_source"] = "v2.38AJ"
        if lux_entry.get("is_fund"):
            row["fundamentals_status"] = "NOT_APPLICABLE_INVESTMENT_FUND_NOT_AN_OPERATING_COMPANY"
            row["fundamentals_source"] = lux_entry.get("identity_source", "")
        elif "concepts" in lux_entry:
            row["fundamentals_status"] = classify_lux_fundamentals(lux_entry["concepts"])
            row["fundamentals_source"] = lux_entry.get("fundamentals_source", "")
    elif at_entry is not None:
        row["country"] = "AT"
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = at_entry["identity_source"]
        row["price_status"] = "NOT_COLLECTED_NO_FREE_SOURCE_FOUND"
        row["price_source"] = "v2.38AJ"
        # Fundamentals confirmed blocked by a real, exhausted firmenakte.at
        # quota (HTTP 429, live-tested) -- never re-attempted silently.
        row["fundamentals_status"] = "BLOCKED_PROVIDER_QUOTA_EXHAUSTED"
        row["fundamentals_source"] = "v2.38BG"
    elif fi_entry is not None:
        row["country"] = "FI"
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = fi_entry["identity_source"]
        if fi_entry.get("sector"):
            row["sector"] = fi_entry["sector"]
        row["price_status"] = "NOT_COLLECTED_NO_FREE_SOURCE_FOUND"
        row["price_source"] = "v2.38AJ"
        # Confirmed real negative finding: PRH's XBRL API only covers
        # small-company digital reporting, 0/7 real large caps tested.
        row["fundamentals_status"] = "NOT_COLLECTED_NO_FREE_SOURCE_FOUND_FOR_LARGE_CAPS"
        row["fundamentals_source"] = "v2.38BH"
    elif av_other_entry is not None:
        row["country"] = av_other_entry.get("country_code", row["country"])
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = av_other_entry["identity_source"]
    elif us_cboe_secondary_entry is not None:
        row["country"] = "US"  # v2.38BI only ever processes country=='US' candidates from v2.38BC; the base census row's own country field is blank for these Cboe-only assets
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = us_cboe_secondary_entry["identity_source"]
        features = us_cboe_secondary_entry.get("features")
        if features is not None:
            growth_present = sum(1 for field in US_GROWTH_FIELDS if present(features.get(field)))
            fund_present = sum(1 for field in US_FUNDAMENTAL_RATIO_FIELDS if present(features.get(field)))
            row["fundamentals_status"] = classify_ladder(fund_present, len(US_FUNDAMENTAL_RATIO_FIELDS))
            row["fundamentals_source"] = "v2.38BK"
            row["growth_status"] = classify_ladder(growth_present, len(US_GROWTH_FIELDS))
            row["growth_source"] = "v2.38BK"
        # Price not yet attempted for this new population (v2.38H's real
        # price extraction was scoped only to the original 555) -- left
        # honestly NOT_ATTEMPTED, never claimed as a confirmed gap the
        # way Europe's real v2.38AJ finding is.
    elif cboe_entry is not None:
        row["country"] = cboe_entry.get("country_code", row["country"])
        row["identity_status"] = "RESOLVED"
        row["identity_source"] = cboe_entry["identity_source"]

    if row["country"] in OFFSHORE_NO_DISCLOSURE_COUNTRIES and row["identity_status"] == "RESOLVED" and row["fundamentals_status"] == NOT_ATTEMPTED:
        # A structural legal fact, not a source we failed to find: none of
        # these 6 jurisdictions require an exempted/non-resident company
        # to publicly file financial statements at all -- confirmed per
        # jurisdiction (v2.38AZ for Cayman originally, v2.38BM for the
        # other 5). Applies regardless of which branch above resolved the
        # identity, so it is checked once here rather than duplicated in
        # every branch that could produce one of these 6 country codes.
        row["fundamentals_status"] = "NOT_APPLICABLE_NO_PUBLIC_DISCLOSURE_REQUIRED"
        row["fundamentals_source"] = "v2.38AZ/BM" if row["country"] == "KY" else "v2.38BM"

    row["overall_coverage_status"] = overall_status(row["identity_status"], row["fundamentals_status"], row["growth_status"])
    return row


def overall_status(identity_status: str, fundamentals_status: str, growth_status: str) -> str:
    if identity_status == NOT_ATTEMPTED:
        return "NO_DATA_YET"
    if fundamentals_status == "NOT_APPLICABLE_INVESTMENT_FUND_NOT_AN_OPERATING_COMPANY":
        return "IDENTITY_ONLY_NOT_AN_OPERATING_COMPANY"
    if fundamentals_status == "NOT_APPLICABLE_NO_PUBLIC_DISCLOSURE_REQUIRED":
        return "IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED"
    if fundamentals_status in ("BLOCKED_PROVIDER_QUOTA_EXHAUSTED", "NOT_COLLECTED_NO_FREE_SOURCE_FOUND_FOR_LARGE_CAPS"):
        return "IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED"
    if fundamentals_status in (NOT_ATTEMPTED, "INSUFFICIENT_FEATURE_EVIDENCE"):
        return "IDENTITY_ONLY_NO_FUNDAMENTALS_YET"
    if growth_status in (NOT_ATTEMPTED, "INSUFFICIENT_FEATURE_EVIDENCE"):
        return "FUNDAMENTALS_READY_NO_GROWTH_YET" if fundamentals_status == "FEATURES_READY" else "FUNDAMENTALS_PARTIAL_NO_GROWTH_YET"
    return "GROWTH_READY" if growth_status == "FEATURES_READY" else "GROWTH_PARTIAL"


def build(
    census_path: Path, us_fund_path: Path, us_price_path: Path, eu_identity_path: Path, eu_fund_path: Path, eu_growth_path: Path,
    joby_features_path: Path, av_mismatch_path: Path, lux_aw_rcs_path: Path, lux_ax_fund_path: Path, lux_be_rcs_path: Path,
    lux_be_fund_path: Path, lux_be_fund_compartments_path: Path, at_bg_path: Path, fi_bh_path: Path, cboe_bulk_path: Path,
    output_dir: Path, us_cboe_secondary_identity_path: Path = US_CBOE_SECONDARY_IDENTITY_INPUT,
    us_cboe_secondary_features_path: Path = US_CBOE_SECONDARY_FEATURES_INPUT,
) -> dict[str, Any]:
    census = read_census(census_path)
    us_fund_idx = read_csv_index(us_fund_path)
    us_price_idx = read_csv_index(us_price_path)
    eu_identity_idx = read_csv_index(eu_identity_path)
    eu_fund_idx = read_csv_index(eu_fund_path)
    eu_growth_idx = read_csv_index(eu_growth_path)
    joby_features_idx = read_csv_index(joby_features_path)
    lux_idx = build_luxembourg_index(av_mismatch_path, lux_aw_rcs_path, lux_ax_fund_path, lux_be_rcs_path, lux_be_fund_path, lux_be_fund_compartments_path)
    at_idx = build_at_bg_index(at_bg_path)
    fi_idx = build_fi_bh_index(fi_bh_path)
    av_other_idx = build_av_other_index(av_mismatch_path)
    cboe_idx = build_cboe_bulk_index(cboe_bulk_path)
    us_cboe_secondary_idx = build_us_cboe_secondary_index(us_cboe_secondary_identity_path, us_cboe_secondary_features_path)

    rows = [
        build_row(
            c, us_fund_idx.get(c["asset_id"]), us_price_idx.get(c["asset_id"]),
            eu_identity_idx.get(c["asset_id"]), eu_fund_idx.get(c["asset_id"]), eu_growth_idx.get(c["asset_id"]),
            joby_features_idx.get(c["asset_id"]), lux_idx.get(c["asset_id"]), at_idx.get(c["asset_id"]),
            fi_idx.get(c["asset_id"]), av_other_idx.get(c["asset_id"]), cboe_idx.get(c["asset_id"]),
            us_cboe_secondary_idx.get(c["asset_id"]),
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
            "joby_aviation_us_features": relative_or_str(joby_features_path) if joby_features_idx else None,
            "luxembourg_merged_av_aw_ax_be": len(lux_idx) or None,
            "austria_bf_bg": len(at_idx) or None,
            "finland_bf_bh": len(fi_idx) or None,
            "av_other_bulgaria_liechtenstein_malta": len(av_other_idx) or None,
            "cboe_europe_bulk_bc": len(cboe_idx) or None,
            "us_cboe_secondary_sec_bi_bk": len(us_cboe_secondary_idx) or None,
        },
        "note": "overall_coverage_status follows the identity->fundamentals->growth depth ladder only; price_status is tracked separately and deliberately excluded from that ladder, because Europe's confirmed 0% free price coverage (v2.38AJ) would otherwise make every Europe growth-ready company indistinguishable from one with no data at all. Every one of the census's rows appears exactly once in the output -- this script never drops or excludes a row, unlike every other builder in this pipeline. Twelfth reconstruction (2026-09-07): merges everything found while attacking the Cboe Europe gap -- the 25 v2.38AV mismatch assets (5 new countries), Luxembourg's real fundamentals (30 companies across v2.38AW/AX/BE), Austria's and Finland's new identities (v2.38BF/BG/BH), Joby Aviation's real US identity/fundamentals corrected from its Cayman-by-ISIN-prefix classification (v2.38AZ/BA), and the bulk 54-country Cboe Europe identity resolution (v2.38BC) for everything without a more specific source. Two new overall_coverage_status values distinguish a real, confirmed blocker from simply 'not attempted yet': IDENTITY_ONLY_NOT_AN_OPERATING_COMPANY (Luxembourg investment fund compartments) and IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED (Austria's exhausted firmenakte.at quota, Finland's confirmed no-source-for-large-caps finding). Fourteenth reconstruction (2026-09-08): the UK/US front chosen after consolidation closed -- 538 of the 628 country=US Cboe secondary candidates got a real SEC CIK match (v2.38BI, three-tier fail-closed name matching against SEC's own company_tickers_exchange.json) and, from that, real US GAAP fundamentals/growth reusing v2.38F/G unmodified at batch scale (v2.38BK) -- the same methodology already proven on the original 555 companies and individually on Joby Aviation. Fifteenth reconstruction (2026-09-08): closes 6 offshore jurisdictions (Cayman Islands, Bermuda, British Virgin Islands, Guernsey, Marshall Islands, Isle of Man -- 265 companies) with a new terminal status, IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED, confirming a real, structural legal fact per jurisdiction: none of these require an exempted/non-resident company to publicly file financial statements at all. Jersey (45 companies, overwhelmingly real PLCs with a genuine statutory duty to file audited accounts) is deliberately left untouched -- closing it the same way would risk hiding real disclosure that a separate investigation (v2.38BM) left as an open, unresolved question rather than forcing it into either bucket.",
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
    parser.add_argument("--joby-features-input", type=Path, default=US_JOBY_AVIATION_FEATURES_INPUT)
    parser.add_argument("--av-mismatch-input", type=Path, default=AV_MISMATCH_INPUT)
    parser.add_argument("--lux-aw-rcs-input", type=Path, default=LUX_AW_RCS_INPUT)
    parser.add_argument("--lux-ax-fundamentals-input", type=Path, default=LUX_AX_FUNDAMENTALS_INPUT)
    parser.add_argument("--lux-be-rcs-input", type=Path, default=LUX_BE_RCS_INPUT)
    parser.add_argument("--lux-be-fundamentals-input", type=Path, default=LUX_BE_FUNDAMENTALS_INPUT)
    parser.add_argument("--lux-be-fund-compartments-input", type=Path, default=LUX_BE_FUND_COMPARTMENTS_INPUT)
    parser.add_argument("--at-bg-input", type=Path, default=AT_BG_REGISTRY_INPUT)
    parser.add_argument("--fi-bh-input", type=Path, default=FI_BH_REGISTRY_SECTOR_INPUT)
    parser.add_argument("--cboe-bulk-input", type=Path, default=CBOE_BULK_IDENTITY_INPUT)
    parser.add_argument("--us-cboe-secondary-identity-input", type=Path, default=US_CBOE_SECONDARY_IDENTITY_INPUT)
    parser.add_argument("--us-cboe-secondary-features-input", type=Path, default=US_CBOE_SECONDARY_FEATURES_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(
        args.census_input, args.us_fundamentals_input, args.us_price_input, args.europe_identity_input,
        args.europe_fundamentals_input, args.europe_growth_input, args.joby_features_input, args.av_mismatch_input,
        args.lux_aw_rcs_input, args.lux_ax_fundamentals_input, args.lux_be_rcs_input, args.lux_be_fundamentals_input,
        args.lux_be_fund_compartments_input, args.at_bg_input, args.fi_bh_input, args.cboe_bulk_input, args.output_dir,
        args.us_cboe_secondary_identity_input, args.us_cboe_secondary_features_input,
    )
    print(json.dumps({k: report[k] for k in ("phase", "companies_total", "overall_coverage_status_counts")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
