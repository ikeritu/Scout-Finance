#!/usr/bin/env python3
"""Build deterministic v2.38X Europe fundamental features (ratios only)
from every real structured-fundamentals block on file. No network, no
scoring, no ranking.

Records come from more than one concept vocabulary -- IFRS taxonomy
names (ifrs-full:*, from GB/Ireland's real iXBRL extraction) and
Austria's own German Bilanz/GuV field names (from firmenakte.at,
v2.38AI) -- resolved to a small set of canonical, source-agnostic slots
(see CONCEPT_ALIASES) before any ratio is computed, so adding a future
country's vocabulary never touches the ratio logic itself.

Unlike the US SEC features (v2.38G), no growth features are computed
here: only each company's single most recent reporting period feeds
these ratios, even for companies with several fiscal years on file
(e.g. Austria's up to 5 years) -- there is no prior-year comparison yet.
Every feature below is a same-period ratio, computable from one balance
sheet / income statement. Growth features stay explicitly out of scope
until a future phase deliberately adds them.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38x_europe_candidate_feature_matrix"
PHASE = "v2.38X-europe-fundamental-features"
# Every real block that has extracted structured fundamentals for any
# European company so far: v2.38W (Softcat, the original 3-4-identity
# pilot) and v2.38Y (the 40-identity GB expansion, Kingfisher) via real
# iXBRL, plus v2.38AI (20 Austrian companies) via firmenakte.at's parsed
# Bilanz/GuV. Each new such block should be added here so this matrix
# always reflects the full real evidence on file, not just whichever
# block happened to exist when this script was first written.
DEFAULT_RECORDS_INPUTS = [
    ROOT / "outputs/full_universe_source_acquisition/v2_38w_europe_ixbrl_fundamentals/europe_ixbrl_fundamental_records_v2_38w.jsonl",
    ROOT / "outputs/full_universe_source_acquisition/v2_38y_europe_gb_full_expansion/europe_ixbrl_fundamental_records_v2_38y.jsonl",
    ROOT / "outputs/full_universe_source_acquisition/v2_38ai_europe_austria_fundamentals/europe_austria_fundamental_records_v2_38ai.jsonl",
]

FEATURE_FIELDS = [
    "asset_id", "ticker", "company_name", "company_number", "feature_period_end",
    "feature_quality_status", "features_calculated", "features_missing", "quality_flags",
    "net_margin", "operating_margin", "pretax_margin", "return_on_assets", "return_on_equity",
    "liabilities_to_assets", "equity_to_assets", "cash_to_assets", "current_ratio",
    "profitability_positive_flag", "balance_strength_flag", "phase",
]
QUALITY_FIELDS = ["asset_id", "ticker", "company_name", "company_number", "features_calculated", "features_missing", "feature_quality_status", "quality_flags"]
REJECTION_FIELDS = ["asset_id", "ticker", "company_number", "feature", "reason", "phase"]
FEATURES = ["net_margin", "operating_margin", "pretax_margin", "return_on_assets", "return_on_equity", "liabilities_to_assets", "equity_to_assets", "cash_to_assets", "current_ratio"]
# Asset-level identity mismatches confirmed real and permanently unfixable
# via this pipeline (never a silent drop -- each exclusion is recorded in
# the rejections output with this exact reason string). U37446 is the one
# known case so far: v2.38V's Xetra-source correction re-identified it as
# SSE PLC, but the iXBRL records already extracted in v2.38W for that
# asset_id are Softcat plc's real, correctly-tagged financial data
# (attached before the correction, via the superseded OpenFIGI-based
# Companies House lookup). Repeating Companies House + accounts-document
# fetch specifically for SSE PLC (company number SC117119, done for real
# as part of v2.38Y's 40-company run) confirmed SSE's most recent accounts
# filing is PDF-only at Companies House -- no iXBRL package exists to
# extract, so there is no way to obtain real SSE PLC figures through this
# pipeline. Publishing Softcat's numbers under the SSE identity would be
# actively wrong, not just partial evidence, so this asset is excluded
# from the matrix rather than shown mislabeled.
KNOWN_IDENTITY_MISMATCH_EXCLUSIONS = {
    "U37446": "asset_reidentified_as_sse_plc_by_v2_38v_correction_but_records_are_softcat_plc_real_data_sse_confirmed_pdf_only_no_ixbrl_available",
}

# Records so far come from two different concept vocabularies: the IFRS
# taxonomy (ifrs-full:*, from GB/Ireland's real iXBRL extraction) and
# Austria's own German Bilanz/GuV field names (from firmenakte.at,
# v2.38AI). Rather than hardcode ratios against one vocabulary, every raw
# concept name is first resolved to a small set of canonical, source-
# agnostic slots -- adding a future country's vocabulary (e.g. a fourth
# real fundamentals source) only means adding its raw names here, never
# touching the ratio logic itself.
CONCEPT_ALIASES = {
    "revenue": ["ifrs-full:Revenue", "umsatzerloese"],
    "operating_profit": ["ifrs-full:ProfitLossFromOperatingActivities", "betriebsErfolg"],
    "pretax_profit": ["ifrs-full:ProfitLossBeforeTax", "ergebnisVorSteuern"],
    "net_profit": ["ifrs-full:ProfitLoss", "jahresueberschuss"],
    "total_assets": ["ifrs-full:Assets", "bilanzSumme"],
    "current_assets": ["ifrs-full:CurrentAssets", "umlaufvermoegen"],
    "current_liabilities": ["ifrs-full:CurrentLiabilities"],  # no Austrian equivalent was extracted in v2.38AI -- stays honestly missing, never guessed
    "equity": ["ifrs-full:Equity", "eigenkapital"],
    "cash": ["ifrs-full:CashAndCashEquivalents", "liquidesVermoegen"],
}
# "Liabilities" needs special handling: IFRS tags it as one figure, but
# Austria's statutory Bilanz splits it into Verbindlichkeiten (payables/
# borrowings) and Rueckstellungen (provisions) as two separate line items
# that sit alongside Eigenkapital under Bilanzsumme -- confirmed for real
# in v2.38AI (Assets = Verbindlichkeiten + Rueckstellungen + Eigenkapital,
# verified exactly for PORR AG's actual filing). The IFRS-style "total
# liabilities" figure is only comparable to the SUM of both components,
# never to Verbindlichkeiten alone, which would understate it.
LIABILITIES_DIRECT_ALIASES = ["ifrs-full:Liabilities"]
LIABILITIES_COMPONENT_ALIASES = ["verbindlichkeiten", "rueckstellungen"]

RATIO_RULES = {
    "net_margin": ("net_profit", "revenue"),
    "operating_margin": ("operating_profit", "revenue"),
    "pretax_margin": ("pretax_profit", "revenue"),
    "return_on_assets": ("net_profit", "total_assets"),
    "return_on_equity": ("net_profit", "equity"),
    "liabilities_to_assets": ("liabilities", "total_assets"),
    "equity_to_assets": ("equity", "total_assets"),
    "cash_to_assets": ("cash", "total_assets"),
    "current_ratio": ("current_assets", "current_liabilities"),
}


def canonicalize_concepts(company_records: list[dict[str, Any]]) -> dict[str, float]:
    """Resolve each record's raw, vocabulary-specific concept name to a
    canonical slot. A company's records come from exactly one vocabulary
    in practice, so alias collisions are not a real concern here -- but
    resolution always prefers whichever alias appears first in each list,
    deterministically, never averaging or picking arbitrarily."""
    by_raw = {r["concept"]: r["value"] for r in company_records if r["value"] is not None}
    by_canonical: dict[str, float] = {}
    for canonical, aliases in CONCEPT_ALIASES.items():
        for alias in aliases:
            if alias in by_raw:
                by_canonical[canonical] = by_raw[alias]
                break
    for alias in LIABILITIES_DIRECT_ALIASES:
        if alias in by_raw:
            by_canonical["liabilities"] = by_raw[alias]
            break
    else:
        if all(component in by_raw for component in LIABILITIES_COMPONENT_ALIASES):
            by_canonical["liabilities"] = sum(by_raw[component] for component in LIABILITIES_COMPONENT_ALIASES)
    return by_canonical


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_jsonl_many(paths: Path | list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    """Merge records from every existing path in `paths`. A path that does
    not exist yet (e.g. a records file some future block hasn't produced
    real data for) is skipped, never an error -- this mirrors how every
    other builder in this project treats an absent real-data file as
    honestly-empty rather than a hard failure."""
    path_list = [paths] if isinstance(paths, Path) else list(paths)
    all_records: list[dict[str, Any]] = []
    sources_used: list[str] = []
    for path in path_list:
        records = read_jsonl(path)
        if records:
            try:
                sources_used.append(str(path.relative_to(ROOT)))
            except ValueError:
                sources_used.append(str(path))
        all_records.extend(records)
    return all_records, sources_used


def rounded(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, 6)


def ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return rounded(num / den)


def build_company(company_records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    base = company_records[0]
    company_number = base.get("company_number") or base.get("fnr", "")
    company_name = base.get("company_name") or base.get("ticker", "")
    # Only the most recent period's records feed the ratios below (same
    # single-period, no-growth-features scope as before) -- a company
    # with multiple fiscal years on file (e.g. Austria's up to 5) uses
    # only its latest year here, consistent with GB/Ireland's own
    # extractors, which never kept more than one period per concept.
    period_ends = {r["period_end"] for r in company_records if r.get("period_end")}
    latest_period = max(period_ends) if period_ends else ""
    latest_records = [r for r in company_records if r.get("period_end") == latest_period] if latest_period else company_records
    by_canonical = canonicalize_concepts(latest_records)
    row: dict[str, Any] = {field: None for field in FEATURE_FIELDS}
    row.update({
        "asset_id": base["asset_id"], "ticker": base["ticker"], "company_name": company_name,
        "company_number": company_number, "feature_period_end": latest_period,
        "phase": PHASE,
    })
    rejections: list[dict[str, str]] = []
    missing: list[str] = []
    flags: set[str] = set()
    for feature, (num_concept, den_concept) in RATIO_RULES.items():
        value = ratio(by_canonical.get(num_concept), by_canonical.get(den_concept))
        row[feature] = value
        if value is None:
            missing.append(feature)
            reason = "missing_numerator" if num_concept not in by_canonical else ("missing_or_zero_denominator" if den_concept not in by_canonical else "unknown")
            rejections.append({"asset_id": base["asset_id"], "ticker": base["ticker"], "company_number": company_number, "feature": feature, "reason": reason, "phase": PHASE})
    if row["net_margin"] is not None and row["net_margin"] > 0:
        flags.add("net_margin_positive")
    if row["liabilities_to_assets"] is not None and row["equity_to_assets"] is not None and row["liabilities_to_assets"] < 0.75 and row["equity_to_assets"] > 0.25:
        flags.add("balance_strength_flag")
    row["profitability_positive_flag"] = bool(row["net_margin"] is not None and row["net_margin"] > 0)
    row["balance_strength_flag"] = "balance_strength_flag" in flags
    calculated = [f for f in FEATURES if row.get(f) is not None]
    row["features_calculated"] = len(calculated)
    row["features_missing"] = "|".join(sorted(missing))
    row["quality_flags"] = "|".join(sorted(flags))
    if len(calculated) == len(FEATURES):
        row["feature_quality_status"] = "FEATURES_READY"
    elif calculated:
        row["feature_quality_status"] = "FEATURES_PARTIAL"
    else:
        row["feature_quality_status"] = "INSUFFICIENT_FEATURE_EVIDENCE"
    return row, rejections


def build(records_paths: Path | list[Path], output_dir: Path) -> dict[str, Any]:
    records, sources_used = read_jsonl_many(records_paths)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["asset_id"])].append(record)

    feature_rows = []
    rejection_rows: list[dict[str, str]] = []
    for asset_id in sorted(grouped):
        if asset_id in KNOWN_IDENTITY_MISMATCH_EXCLUSIONS:
            base = grouped[asset_id][0]
            rejection_rows.append({
                "asset_id": asset_id, "ticker": base["ticker"], "company_number": base.get("company_number") or base.get("fnr", ""),
                "feature": "ALL", "reason": KNOWN_IDENTITY_MISMATCH_EXCLUSIONS[asset_id], "phase": PHASE,
            })
            continue
        row, rejections = build_company(grouped[asset_id])
        feature_rows.append(row)
        rejection_rows.extend(rejections)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_fundamental_features_v2_38x.csv", feature_rows, FEATURE_FIELDS)
    write_csv(output_dir / "europe_fundamental_feature_quality_v2_38x.csv", feature_rows, QUALITY_FIELDS)
    write_csv(output_dir / "europe_fundamental_feature_rejections_v2_38x.csv", rejection_rows, REJECTION_FIELDS)

    quality_counts = {status: sum(1 for r in feature_rows if r["feature_quality_status"] == status) for status in {"FEATURES_READY", "FEATURES_PARTIAL", "INSUFFICIENT_FEATURE_EVIDENCE"}}
    excluded = [a for a in grouped if a in KNOWN_IDENTITY_MISMATCH_EXCLUSIONS]
    report = {
        "phase": PHASE, "companies_input": len(grouped), "companies_excluded_known_identity_mismatch": len(excluded),
        "companies_features_ready": quality_counts["FEATURES_READY"],
        "companies_features_partial": quality_counts["FEATURES_PARTIAL"], "companies_insufficient": quality_counts["INSUFFICIENT_FEATURE_EVIDENCE"],
        "rejected_rows": len(rejection_rows), "network_used": False, "scoring_created": False, "ranking_created": False,
        "recommendations_created": False, "phase9c_authorized": False, "records_sources_used": sources_used,
        "note": "Growth features are out of scope: only each company's single most recent reporting period feeds these ratios, even when multiple fiscal years are on file (e.g. Austria's up to 5 years per company from v2.38AI) -- no prior-year comparison is computed yet.",
    }
    write_text(output_dir / "europe_fundamental_features_report_v2_38x.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report, feature_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-input", type=Path, nargs="+", default=DEFAULT_RECORDS_INPUTS, help="one or more iXBRL records JSONL files to merge (defaults to every real block on file: v2.38W + v2.38Y)")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report, _ = build(args.records_input, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
