#!/usr/bin/env python3
"""Block v2.38BI: resolve a real SEC CIK for the 628 Cboe Europe secondary
candidates already carrying a GLEIF-only identity under country=US in the
v2.38AL coverage matrix (via v2.38BC's full-scale Cboe resolution).

Why this exists: GLEIF gives a real legal name and country, but no link
to any US fundamentals source. This project's whole US fundamentals
pipeline (v2.38E/F/G, reused unmodified for Joby Aviation in v2.38BA) is
keyed on a real SEC CIK. Upgrading these 628 companies from
"GLEIF-only" to "SEC CIK resolved" is what makes real US fundamentals
extraction possible for them, the same way v2.38AW's RCS number made
real fundamentals possible for Luxembourg.

Matching approach, offline only (SEC's company_tickers_exchange.json is
already cached locally, no live lookup needed): three fail-closed tiers,
each requiring a SINGLE distinct CIK to accept a match --
  1. normalized name (legal-form suffixes and SEC's own "/DE" /
     "/ DE" / "/DE/" state-of-incorporation suffix stripped, periods and
     commas treated as spaces, apostrophes deleted).
  2. squashed (all-whitespace-removed) normalized name -- SEC is
     internally inconsistent about apostrophes: "MCDONALDS CORP" (no
     apostrophe, no space) vs "O REILLY AUTOMOTIVE INC" (apostrophe
     replaced with a space, not deleted). Squashing removes the
     difference either way.
  3. sorted-token-set of the normalized name -- confirmed real SEC
     quirk: a handful of registrants are filed in inverted
     surname-first order ("PRICE T ROWE GROUP INC" for T. Rowe Price,
     "SMITH A O CORP" for A.O. Smith), a legacy catalog-indexing
     convention. Comparing the sorted word set instead of literal order
     resolves these without a manual alias table.
Multiple matches at any tier that resolve to more than one distinct CIK
stay unresolved as ambiguous -- never a best guess, same discipline as
every other resolver in this project (GLEIF, Firmenbuch, TOL).

Real, honest, and expected: not every real, currently-listed SEC
registrant appears in company_tickers_exchange.json (confirmed live via
a fresh authorized re-download, HTTP 200, 10,415 rows -- AvalonBay
Communities, Hologic, Sealed Air and Coterra Energy are all real,
current, large-cap SEC filers absent from this specific SEC file, not a
caching problem). Combined with genuinely delisted/acquired companies
still present in this historical Cboe listing snapshot (GrubHub,
Hortonworks, Cavium, Clovis Oncology...) and a handful of non-US
companies mislabeled country=US in the source census (AMG Critical
Materials NV, Bekaert SA, Huhtamaki Oyj...), this accounts for the
~14% left unresolved -- documented, not chased further.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = "v2.38BI-us-cboe-secondary-identity-sec"
COVERAGE_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38al_global_coverage_matrix/global_coverage_matrix_v2_38al.csv.xz"
SEC_TICKERS_INPUT = ROOT / "data/raw/source_providers/sec_company_tickers_exchange/company_tickers_exchange.json"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bi_us_cboe_secondary_identity_sec"

FIELDS = ["asset_id", "ticker", "company_name", "cik", "sec_name", "sec_ticker", "sec_exchange", "match_tier", "fetch_status", "fetch_reason", "phase", "created_at_utc"]

LEGAL_FORM_WORDS = r"\b(INC|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|LLC|PLC|GROUP|HOLDINGS?|INTERNATIONAL|LP|SA|NV|SPA|AG|SE)\b"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize(name: str, squash: bool = False) -> str:
    n = name.upper()
    n = n.replace("'", "").replace("’", "")
    n = re.sub(r"/\s*[A-Z]{1,5}\s*/?$", " ", n)  # SEC state-of-incorporation suffix: /DE, / DE, /DE/
    n = n.replace(".", " ").replace(",", " ")
    n = re.sub(LEGAL_FORM_WORDS, "", n)
    n = re.sub(r"[^A-Z0-9& ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    if squash:
        n = n.replace(" ", "")
    return n


def token_set_key(name: str) -> str:
    return " ".join(sorted(normalize(name).split()))


def load_sec_index(path: Path) -> dict[str, list[tuple[int, str, str, str]]] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("data", [])
    return rows


def build_indexes(sec_rows: list[list]) -> tuple[dict, dict, dict]:
    by_norm: dict[str, list] = {}
    by_squash: dict[str, list] = {}
    by_tokenset: dict[str, list] = {}
    for cik, name, ticker, exchange in sec_rows:
        entry = (cik, name, ticker, exchange)
        by_norm.setdefault(normalize(name), []).append(entry)
        by_squash.setdefault(normalize(name, squash=True), []).append(entry)
        by_tokenset.setdefault(token_set_key(name), []).append(entry)
    return by_norm, by_squash, by_tokenset


def resolve_one(company_name: str, by_norm: dict, by_squash: dict, by_tokenset: dict) -> dict[str, str]:
    for tier, index, key in (
        ("exact_normalized_name", by_norm, normalize(company_name)),
        ("squashed_normalized_name", by_squash, normalize(company_name, squash=True)),
        ("sorted_token_set", by_tokenset, token_set_key(company_name)),
    ):
        matches = index.get(key, [])
        distinct_ciks = {m[0] for m in matches}
        if len(distinct_ciks) == 1:
            cik, sec_name, sec_ticker, sec_exchange = matches[0]
            return {"fetch_status": "resolved", "fetch_reason": "", "cik": f"{int(cik):010d}", "sec_name": sec_name, "sec_ticker": sec_ticker, "sec_exchange": sec_exchange, "match_tier": tier}
        if len(distinct_ciks) > 1:
            return {"fetch_status": "ambiguous", "fetch_reason": "ambiguous_multiple_distinct_companies_matched", "cik": "", "sec_name": "", "sec_ticker": "", "sec_exchange": "", "match_tier": tier}
    return {"fetch_status": "unresolved", "fetch_reason": "no_exact_normalized_name_match", "cik": "", "sec_name": "", "sec_ticker": "", "sec_exchange": "", "match_tier": ""}


def read_candidates(coverage_path: Path) -> list[dict[str, str]]:
    import lzma

    if not coverage_path.exists():
        raise SystemExit(f"BLOCKED: required v2.38AL global coverage matrix not found: {coverage_path}")
    opener = lzma.open if coverage_path.suffix == ".xz" else open
    with opener(coverage_path, "rt", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r.get("country") == "US" and r.get("identity_status") == "RESOLVED" and r.get("identity_source") == "v2.38BC"]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
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


def build(coverage_path: Path, sec_tickers_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = read_candidates(coverage_path)
    sec_rows = load_sec_index(sec_tickers_path)
    rows: list[dict[str, Any]] = []
    if sec_rows is None:
        for c in candidates:
            rows.append({"asset_id": c["asset_id"], "ticker": c["ticker"], "company_name": c["company_name"], "cik": "", "sec_name": "", "sec_ticker": "", "sec_exchange": "", "match_tier": "", "fetch_status": "blocked", "fetch_reason": "sec_company_tickers_exchange_cache_unavailable", "phase": PHASE, "created_at_utc": now_iso()})
    else:
        by_norm, by_squash, by_tokenset = build_indexes(sec_rows)
        for c in candidates:
            result = resolve_one(c["company_name"], by_norm, by_squash, by_tokenset)
            rows.append({"asset_id": c["asset_id"], "ticker": c["ticker"], "company_name": c["company_name"], "phase": PHASE, "created_at_utc": now_iso(), **result})

    write_csv(output_dir / "us_cboe_secondary_identity_sec_v2_38bi.csv", FIELDS, rows)

    counts = Counter(r["fetch_status"] for r in rows)
    tier_counts = Counter(r["match_tier"] for r in rows if r["fetch_status"] == "resolved")
    reason_counts = Counter(r["fetch_reason"] for r in rows if r["fetch_status"] != "resolved")
    report = {
        "phase": PHASE,
        "status": "COMPLETED_US_CBOE_SECONDARY_IDENTITY_SEC" if sec_rows is not None else "BLOCKED_SEC_CACHE_UNAVAILABLE",
        "candidates_input": len(candidates),
        "resolved": counts.get("resolved", 0),
        "ambiguous": counts.get("ambiguous", 0),
        "unresolved": counts.get("unresolved", 0),
        "match_tier_counts": dict(tier_counts),
        "unresolved_reason_counts": dict(reason_counts),
        "sec_tickers_source_rows": len(sec_rows) if sec_rows is not None else 0,
        "guardrails": {"network_calls": 0, "recommendations_generated": False, "financial_advice": False, "broker_actions_allowed": False, "phase9c_authorized": False, "scoring_modified": False, "ranking_modified": False},
    }
    write_text(output_dir / "us_cboe_secondary_identity_sec_report_v2_38bi.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest = {"phase": PHASE, "outputs": {"us_cboe_secondary_identity_sec_v2_38bi.csv": {"bytes": (output_dir / "us_cboe_secondary_identity_sec_v2_38bi.csv").stat().st_size, "sha256": sha256(output_dir / "us_cboe_secondary_identity_sec_v2_38bi.csv")}}, "guardrails": report["guardrails"]}
    write_text(output_dir / "us_cboe_secondary_identity_sec_manifest_v2_38bi.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-input", type=Path, default=COVERAGE_INPUT)
    parser.add_argument("--sec-tickers-input", type=Path, default=SEC_TICKERS_INPUT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    report = build(args.coverage_input, args.sec_tickers_input, args.output_dir)
    print(json.dumps({k: report[k] for k in ("phase", "status", "candidates_input", "resolved", "ambiguous", "unresolved")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
