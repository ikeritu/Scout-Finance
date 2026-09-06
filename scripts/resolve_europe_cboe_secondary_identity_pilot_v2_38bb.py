#!/usr/bin/env python3
"""Block 9BB: real, scoped pilot for the 21,066-row CBOE_SECONDARY_HOME_
EXCHANGE_REQUIRED bucket from v2.38N -- confirmed real, live evidence is
required before deciding whether to attack the full population, per the
user's explicit choice ("piloto pequeño primero").

Real desk characterization done before writing this script (never
guessed): of the 21,066 rows, ~10,176 (48%) are ETFs/ETPs by name pattern
(WisdomTree, iShares, Xtrackers, Ossiam, leveraged/crypto trackers, ...)
-- structurally out of scope for a company growth shortlist, since a fund
has no balance sheet or income statement to extract. Of the remaining
~10,890 real-company-shaped names, 387 already match a company this
project already resolved in the 689-scope Europe population (v2.38AB) --
Allianz, BNP Paribas, Deutsche Bank, Volkswagen, ING, Nokia, ABB, Credit
Agricole among them -- and 202 already match a name already present in
the US census, leaving roughly 7,500 genuinely new, real companies never
touched by this project.

The real, load-bearing obstacle: this Cboe Europe reference dataset (the
ONLY source for these rows) never carried an ISIN, country, currency,
sector or MIC -- confirmed live by inspecting the raw v2.38A census rows
directly (every field beyond ticker/company_name is blank, with
`missing_isin` explicitly flagged). This rules out the ISIN-prefix method
already used successfully for the 25 v2.38AV mismatch assets and for
Luxembourg (v2.38AW) -- there is no ISIN to read a country from. The only
remaining option is GLEIF's legal-name search with NO country filter
(unlike Luxembourg, where the country was already known) -- a genuinely
different, higher-ambiguity-risk situation that has never been tried at
this scale in this project.

This script draws a real, reproducible random sample (fixed seed, no
cherry-picking) from the ~7,500 genuinely-new companies and resolves
identity for just that sample, measuring the real match/ambiguity/miss
rate live -- before any decision is made about attacking the full
population.
"""
from __future__ import annotations

import argparse
import csv
import json
import lzma
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HOME_EXCHANGE_CSV = ROOT / "outputs/full_universe_source_acquisition/v2_38n_europe_home_exchange_resolution/europe_home_exchange_resolution_v2_38n.csv"
EU_IDENTITY_CSV = ROOT / "outputs/full_universe_source_acquisition/v2_38ab_europe_full_identity_resolution/europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv"
CENSUS_XZ = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit/global_universe_audited_v2_38a.csv.xz"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bb_europe_cboe_secondary_identity_pilot"
PHASE = "v2.38BB-europe-cboe-secondary-identity-pilot"
GLEIF_URL = "https://api.gleif.org/api/v1/lei-records"
GLEIF_MIN_SECONDS_BETWEEN_CALLS = 0.3
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0
SAMPLE_SIZE = 75
SAMPLE_SEED = 2026

ETF_MARKERS = [
    "ETF", "UCITS", "ETC ", "ETP", "WisdomTree", "iShares", "Xtrackers", "Lyxor",
    "Amundi", "SPDR", "Invesco", "VanEck", "HANetf", "Ossiam", "L&G ", "Vanguard",
    "GraniteShares", "Leverage", "Leveraged", "Daily Hedged", "Short Daily",
    "Daily Leveraged", "Tracker", "Index Fund", "Trust Units", "Physical ",
    "Bond ", "Govt Bond", "Gilt ", "Commodity", "Gold ", "Silver ", "Crude Oil",
    "Natural Gas", "Wheat", "Corn ", "Coffee", "Cocoa", "Sugar", "Cotton",
    "ProShares", "Direxion", "Global X", "Multi Asset", "Money Market",
    "Bitcoin", "Ethereum", "Crypto", "21Shares", "Digital Asset", "Solactive",
]
ETF_RE = re.compile("|".join(re.escape(m) for m in ETF_MARKERS), re.IGNORECASE)
LEGAL_FORM_RE = re.compile(
    r"\s+("
    r"PUBLIC LIMITED COMPANY|LIMITED COMPANY|AKTIENGESELLSCHAFT|AKTIEBOLAG|"
    r"ALLMENNAKSJESELSKAP|NAAMLOZE VENNOOTSCHAP|SOCIETA PER AZIONI|SOCIETE ANONYME|"
    r"CORPORATION|LIMITED|COMPANY|"
    r"S\.?A\.?|SE|SCA|S\.C\.A\.?|N\.?V\.?|PLC|AG|GMBH|LTD|INC|CORP|OYJ|ASA|AB|A/S|SPA|CO"
    r")$", re.IGNORECASE,
)


def normalize_key(name: str) -> str:
    """Real bug found and fixed via a live GLEIF probe: stripping the
    trailing legal-form token BEFORE removing punctuation misses names
    that spell it "Inc." (trailing period) rather than "Inc" -- the "$"
    anchor never matched with a period still attached, so "UBER
    TECHNOLOGIES, INC." (GLEIF's own spelling) and "Uber Technologies Inc"
    (Cboe's spelling) normalized to two different strings and never
    matched. Punctuation is now stripped FIRST, so both spellings always
    converge to the same key regardless of which source wrote it."""
    stripped = re.sub(r"[.,]", " ", name or "").strip()
    stripped = re.sub(r"\s+", " ", stripped)
    changed = True
    while changed:
        changed = False
        new_stripped = LEGAL_FORM_RE.sub("", stripped).strip()
        if new_stripped != stripped and new_stripped:
            stripped = new_stripped
            changed = True
    return stripped.upper().strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def load_known_names(eu_identity_csv: Path, census_xz: Path) -> set[str]:
    known: set[str] = set()
    if eu_identity_csv.exists():
        for row in read_csv(eu_identity_csv):
            if row.get("resolution_status") == "resolved":
                known.add(normalize_key(row["resolved_company_name"]))
    if census_xz.exists():
        with lzma.open(census_xz, "rt", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("country") in {"USA", "US"}:
                    key = normalize_key(row.get("company_name", ""))
                    if key:
                        known.add(key)
    return known


def select_candidates(home_exchange_csv: Path, known_names: set[str]) -> list[dict[str, str]]:
    candidates = []
    for row in read_csv(home_exchange_csv):
        if row.get("resolution_status") != "CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED":
            continue
        name = row.get("company_name", "")
        if not name or ETF_RE.search(name):
            continue
        key = normalize_key(name)
        if key in known_names:
            continue
        candidates.append(row)
    return candidates


def draw_sample(candidates: list[dict[str, str]], size: int, seed: int) -> list[dict[str, str]]:
    uniq: dict[str, dict[str, str]] = {}
    for row in candidates:
        key = normalize_key(row["company_name"])
        uniq.setdefault(key, row)
    pool = sorted(uniq.values(), key=lambda r: r["asset_id"])
    rng = random.Random(seed)
    return rng.sample(pool, min(size, len(pool)))


def http_get_json(url: str) -> tuple[int, dict | None]:
    request = urllib.request.Request(url)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            body = exc.read().decode("utf-8") if exc.fp else "{}"
            try:
                return exc.code, json.loads(body)
            except json.JSONDecodeError:
                return exc.code, None
    raise RuntimeError("rate_limit_retries_exhausted")


def raw_words(name: str, count: int) -> str:
    """The first `count` whitespace-separated tokens of the ORIGINAL,
    un-normalized name -- keeps internal punctuation (periods, ampersands)
    intact. Real bug found live: GLEIF's own legalName filter does a
    literal prefix match against its stored string, punctuation included
    -- querying "WW" (periods stripped by our own normalization) finds
    nothing, but querying "W.W." (the real Cboe/GLEIF spelling, periods
    kept) finds "W.W. GRAINGER, INC." immediately. The normalized,
    punctuation-free key is still used for the exact-match comparison
    afterwards -- only the query sent to GLEIF needs the original
    spelling."""
    tokens = (name or "").strip().split()
    return " ".join(tokens[:count])


def gleif_query(query_string: str) -> tuple[list[dict], str]:
    query = urllib.parse.urlencode({"filter[entity.legalName]": query_string, "page[size]": "50"})
    status, payload = http_get_json(f"{GLEIF_URL}?{query}")
    if status != 200 or payload is None:
        return [], f"gleif_http_error_{status}"
    return payload.get("data", []), "queried"


def find_exact_candidates(key: str, records: list[dict]) -> list[dict]:
    matches = []
    for rec in records:
        entity = rec.get("attributes", {}).get("entity", {})
        legal_name = (entity.get("legalName") or {}).get("name", "")
        if normalize_key(legal_name) == key:
            matches.append(rec)
    return matches


def gleif_lookup_no_country(original_name: str, key: str) -> tuple[list[dict], str, str]:
    """Two-step search, no country filter (the real country is exactly
    what this pilot is trying to discover). Step 1: query with the raw
    first word (original spelling, punctuation intact). Step 2 (real
    fallback, found live via "Check Point Software Technologies" --
    querying just "Check" returns dozens of unrelated small companies
    named "Check ..." and never finds it on page 1, but "Check Point"
    finds it immediately): if step 1 finds no exact match and the name
    has a second word, retry with the first two raw words together --
    strictly narrower than one word, so it only adds a real candidate,
    never removes one already found."""
    first = raw_words(original_name, 1)
    records, reason = gleif_query(first)
    if reason != "queried":
        return [], reason, "first_word"
    if find_exact_candidates(key, records):
        return records, "queried", "first_word"
    two = raw_words(original_name, 2)
    if two and two != first:
        more_records, reason2 = gleif_query(two)
        if reason2 == "queried" and find_exact_candidates(key, more_records):
            return more_records, "queried", "first_two_words"
    return records, "queried", "first_word"


def build(home_exchange_csv: Path, eu_identity_csv: Path, census_xz: Path, output_dir: Path, sample_size: int, seed: int, execute: bool) -> dict[str, Any]:
    known_names = load_known_names(eu_identity_csv, census_xz)
    candidates = select_candidates(home_exchange_csv, known_names)
    sample = draw_sample(candidates, sample_size, seed)

    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "total_cboe_secondary_rows": None, "eligible_new_company_candidates": len(candidates), "sample_size": len(sample), "sample_seed": seed, "network_used": False, "phase9c_authorized": False}

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    matrix = []
    for i, row in enumerate(sample):
        if i > 0:
            time.sleep(GLEIF_MIN_SECONDS_BETWEEN_CALLS)
        key = normalize_key(row["company_name"])
        records, reason, query_strategy = gleif_lookup_no_country(row["company_name"], key)
        if reason != "queried":
            matrix.append(_record(row, key, "unresolved", reason, created_at))
            continue
        exact = find_exact_candidates(key, records)
        if not exact:
            matrix.append(_record(row, key, "unresolved", "no_exact_normalized_name_match_gleif", created_at))
            continue
        countries = {(c.get("attributes", {}).get("entity", {}).get("legalAddress", {}) or {}).get("country", "") for c in exact}
        if len(countries) > 1:
            matrix.append(_record(row, key, "ambiguous", "multiple_distinct_countries_match_same_name", created_at, candidate_count=len(exact), candidate_countries="|".join(sorted(countries))))
            continue
        if len(exact) > 1:
            matrix.append(_record(row, key, "ambiguous", "multiple_distinct_entities_same_country_same_name", created_at, candidate_count=len(exact), candidate_countries="|".join(sorted(countries))))
            continue
        entity = exact[0].get("attributes", {}).get("entity", {})
        matrix.append(_record(
            row, key, "resolved", "exact_single_gleif_match_no_country_filter", created_at,
            lei=exact[0].get("id", ""), legal_name=(entity.get("legalName") or {}).get("name", ""),
            country=(entity.get("legalAddress") or {}).get("country", ""), query_strategy=query_strategy,
        ))

    resolved = [r for r in matrix if r["status"] == "resolved"]
    ambiguous = [r for r in matrix if r["status"] == "ambiguous"]
    unresolved = [r for r in matrix if r["status"] == "unresolved"]
    from collections import Counter
    by_country = Counter(r["country"] for r in resolved if r["country"])
    by_query_strategy = Counter(r["query_strategy"] for r in resolved if r["query_strategy"])

    report = {
        "phase": PHASE, "sample_size": len(sample), "sample_seed": seed,
        "total_cboe_secondary_rows": 21066, "eligible_new_company_candidates": len(candidates),
        "resolved": len(resolved), "ambiguous": len(ambiguous), "unresolved": len(unresolved),
        "resolved_rate_pct": round(100 * len(resolved) / len(sample), 1) if sample else 0,
        "ambiguous_rate_pct": round(100 * len(ambiguous) / len(sample), 1) if sample else 0,
        "resolved_by_country": dict(sorted(by_country.items(), key=lambda kv: -kv[1])),
        "resolved_by_query_strategy": dict(by_query_strategy),
        "projection_if_scaled_to_full_population": {
            "estimated_resolved": round(len(candidates) * (len(resolved) / len(sample))) if sample else 0,
            "estimated_ambiguous": round(len(candidates) * (len(ambiguous) / len(sample))) if sample else 0,
            "estimated_unresolved": round(len(candidates) * (len(unresolved) / len(sample))) if sample else 0,
            "caveat": "Linear extrapolation from a random sample -- a real signal of scale, not a guarantee; only a full run confirms the real number.",
        },
        "network_used": True, "credentials_used": False, "phase9c_authorized": False,
    }
    write_csv(output_dir / "europe_cboe_secondary_identity_pilot_matrix_v2_38bb.csv", matrix, MATRIX_FIELDS)
    write_text(output_dir / "europe_cboe_secondary_identity_pilot_summary_v2_38bb.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


MATRIX_FIELDS = ["asset_id", "ticker", "company_name", "search_key", "status", "reason", "lei", "legal_name", "country", "candidate_count", "candidate_countries", "query_strategy", "phase", "created_at_utc"]


def _record(row: dict[str, str], key: str, status: str, reason: str, created_at: str, lei: str = "", legal_name: str = "", country: str = "", candidate_count: int = 0, candidate_countries: str = "", query_strategy: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["company_name"], "search_key": key,
        "status": status, "reason": reason, "lei": lei, "legal_name": legal_name, "country": country,
        "candidate_count": candidate_count, "candidate_countries": candidate_countries, "query_strategy": query_strategy,
        "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home-exchange-csv", type=Path, default=HOME_EXCHANGE_CSV)
    parser.add_argument("--eu-identity-csv", type=Path, default=EU_IDENTITY_CSV)
    parser.add_argument("--census-xz", type=Path, default=CENSUS_XZ)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=SAMPLE_SEED)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = build(args.home_exchange_csv, args.eu_identity_csv, args.census_xz, args.output_dir, args.sample_size, args.seed, args.execute)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
