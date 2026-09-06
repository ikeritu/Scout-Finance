#!/usr/bin/env python3
"""Block 9AU: fetch the real TOL 2008 classification (Finland's own
Statistics Finland industry classification, aligned with NACE Rev.2) for
the 5 Finnish companies already identity-resolved in v2.38AB, continuing
the attack on the Europe sector-classification gap.

Real desk research found the best official source of this entire
effort: the PRH (Finnish Patent and Registration Office) YTJ open-data
API (avoindata.prh.fi/opendata-ytj-api/v3), CC BY 4.0 licensed, no
account or key required, confirmed live and working. Unlike every other
country attacked so far, this API returns the sector description
**already translated to English** on every real record (languageCode
"3" -- confirmed live for Nokia Oyj: mainBusinessLine.type "70100" with
descriptions in Finnish, Swedish AND English "Activities of head
offices") -- no manual translation table needed at all.

A real, Finland-specific identity problem had to be solved first: none
of these 5 companies have a GLEIF record (a real, already-confirmed gap
from v2.38AF -- Finnish ISINs are absent from GLEIF's self-reported
mapping), so there is no pre-known Business ID to query by. Worse,
v2.38AB's Xetra-derived company names are corrupted in Finland-specific
ways never seen in other countries: "SRV YHTIOET OYJ" is Xetra's ASCII
transliteration of "SRV Yhtiöt Oyj" (o-umlaut rendered as the German-
style "OE" digraph, the same convention already seen for German/Austrian/
Swiss names elsewhere in this project, but never previously reversed),
and "UPM KYMMENE CORP." both drops the real hyphen ("UPM-Kymmene") and
uses an English "Corp." suffix instead of the real "Oyj". `normalize()`
reverses both confirmed corruptions for exact-match comparison, on top
of the same legal-suffix-stripping used everywhere else.

A second real problem, found only by testing live: the API matches
literally against the real registered name, so searching with the full
(space-separated) Xetra-derived string returns zero results whenever
Xetra used a space where the real name has a hyphen -- confirmed live
that "UPM KYMMENE" finds nothing but "UPM-Kymmene" finds it immediately.
Since the exact internal punctuation can't be reconstructed reliably,
the search query is always just the first normalized word (a safe,
always-correct literal substring regardless of what separator follows
it, e.g. "UPM", "SRV", "NOKIA") -- confirmed live this can return
hundreds of unrelated small businesses sharing that one word (991 for
"NOKIA" alone), so every results page is scanned, not just the first,
before the caller's own exact-match filter runs.

Blocked by default; --execute is required (no credential needed, but
real network calls stay gated behind this explicit flag, matching this
project's convention for every free no-key registry lookup).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38ab_europe_full_identity_resolution/europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38au_europe_finland_tol"
PHASE = "v2.38AU-europe-finland-tol"
JURISDICTION_FILTER = "FI"
SEARCH_URL = "https://avoindata.prh.fi/opendata-ytj-api/v3/companies"
MIN_SECONDS_BETWEEN_CALLS = 0.5
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 20.0
ENGLISH_LANGUAGE_CODE = "3"
MAX_PAGES = 20  # safety cap on pagination when a single-word query matches many unrelated small businesses

# "CORP"/"CORPORATION"/"PLC" are never real Finnish/Swedish legal-form
# suffixes -- confirmed real that Xetra substitutes one of these for the
# real suffix (e.g. "UPM KYMMENE CORP." for the real "UPM-Kymmene Oyj").
# "OYJ" (public), "OY" (private) and "ABP" (Swedish-language public) ARE
# real, and confirmed live to matter for disambiguation: "SRV Yhtiöt Oy"
# and "SRV Yhtiöt Oyj" are two distinct, currently active companies
# differing only by that suffix, so collapsing OY/OYJ together would
# create a false collision. `normalize_full` keeps a real suffix intact
# and only strips a wrong foreign one; `normalize_core` strips every
# suffix (real or wrong) and is used only as a fallback when Xetra's
# recorded suffix does not match anything real.
WRONG_SUFFIXES = ["CORPORATION", "CORP", "PLC"]
REAL_SUFFIXES = ["OYJ", "OY", "ABP"]


def _fix_transliteration_and_punctuation(name: str) -> str:
    text = name.upper()
    # Xetra's ASCII transliteration of Finnish/Swedish letters uses the
    # same German-style digraph convention already seen elsewhere in
    # this project (o-umlaut -> "OE", a-umlaut -> "AE") -- confirmed
    # real for "SRV YHTIOET OYJ" (Xetra) vs "SRV Yhtiöt Oyj" (PRH).
    # Reversed here before any other cleaning, in that order (AE first)
    # so a genuine "AE" is not double-mangled by a later "E" removal.
    text = text.replace("AE", "Ä").replace("OE", "Ö")
    text = text.replace(".", "").replace("-", " ")
    text = re.sub(r"[,()]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_trailing_share_class(words: list[str]) -> list[str]:
    # A trailing single-letter share-class marker (e.g. "SAMPO OYJ A")
    # is a Xetra annotation, never part of the real registered name.
    if words and len(words[-1]) == 1 and words[-1].isalpha():
        return words[:-1]
    return words


def _strip_suffixes(words: list[str], suffixes: list[str]) -> list[str]:
    changed = True
    while changed and words:
        changed = False
        for suffix in suffixes:
            suffix_words = suffix.split(" ")
            if words[-len(suffix_words):] == suffix_words:
                words = words[: -len(suffix_words)]
                changed = True
                break
    return words


def normalize_full(name: str) -> str:
    words = _strip_trailing_share_class(_fix_transliteration_and_punctuation(name).split(" "))
    return " ".join(_strip_suffixes(words, WRONG_SUFFIXES)).strip()


def normalize_core(name: str) -> str:
    words = _strip_trailing_share_class(_fix_transliteration_and_punctuation(name).split(" "))
    return " ".join(_strip_suffixes(words, WRONG_SUFFIXES + REAL_SUFFIXES)).strip()


def normalize(name: str) -> str:
    """Kept as the core-level normalizer for the search-query word (any
    suffix gets stripped there anyway, since only the first word survives)."""
    return normalize_core(name)


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


def search_query_word(name: str) -> str:
    """The API matches literally against the real registered name, so a
    multi-word Xetra-derived query fails whenever Xetra used a space
    where the real Finnish name has a hyphen (confirmed real: "UPM
    KYMMENE" finds nothing, but the real name "UPM-Kymmene" does). The
    first normalized word is always a safe, unambiguous literal substring
    of the real name regardless of what separator follows it."""
    first_word = normalize(name).split(" ")[0]
    return first_word


def fetch_page(query_word: str, page: int | None) -> dict:
    params = {"name": query_word}
    if page:
        params["page"] = page
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{SEARCH_URL}?{query}", headers={"User-Agent": "ScoutFinanceResearch/1.0 (+non-commercial research script)"})
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_ATTEMPTS:
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            raise
    raise RuntimeError("rate_limit_retries_exhausted")


def search_company(name: str) -> dict:
    """Searching by a single word (e.g. "NOKIA") can return hundreds of
    unrelated small businesses that happen to share that word -- so every
    page is scanned (up to MAX_PAGES, a real safety cap) rather than
    trusting the real target to be on page 1, and every page's results
    are merged before the caller applies its own exact-match filter."""
    query_word = search_query_word(name)
    first_page = fetch_page(query_word, None)
    companies = list(first_page.get("companies", []))
    total = first_page.get("totalResults", len(companies))
    page = 2
    while len(companies) < total and page <= MAX_PAGES:
        next_page = fetch_page(query_word, page)
        new_companies = next_page.get("companies", [])
        if not new_companies:
            break
        companies.extend(new_companies)
        page += 1
    return {"totalResults": total, "companies": companies}


# PRH's "type of name" codes (confirmed live via /v3/description?code=TLAJI):
# 1 = current official company name, 2 = parallel company name (e.g. the
# Finnish/Swedish bilingual pair), 3/4 = auxiliary trade name / its
# translation. A real, confirmed problem with matching against types 3/4:
# Nordic banks' decades of mergers (Merita -> Nordea, etc.) leave dozens of
# old marketing brand names attached to unrelated business IDs -- e.g. a
# bare "Nordea Bank" auxiliary name (no legal suffix) is attached to at
# least four different, unrelated business IDs going back to a 2001 merger,
# which collides with the real "Nordea Bank Abp" once suffix-stripping
# normalizes both to "NORDEA BANK". Restricting the match to types 1/2 --
# the real, current registered legal name(s) -- is what actually
# corresponds to what a company's Xetra-derived identity should mean.
PRIMARY_NAME_TYPES = {"1", "2"}


def _candidates_matching(target_name: str, payload: dict, normalize_fn) -> list[dict]:
    expected = normalize_fn(target_name)
    matches = []
    for company in payload.get("companies", []):
        candidate_names = [entry.get("name", "") for entry in company.get("names", []) if entry.get("type") in PRIMARY_NAME_TYPES]
        if any(normalize_fn(candidate) == expected for candidate in candidate_names):
            matches.append(company)
    return matches


def match_company(target_name: str, payload: dict) -> tuple[dict | None, str]:
    # Two-tier, most-specific-first: a match keeping the real legal
    # suffix (normalize_full) is always preferred and decided on its own
    # -- confirmed real that this alone resolves Nokia/Nordea/Sampo/SRV
    # correctly and specifically avoids the real Oy-vs-Oyj collision risk
    # (two distinct, currently active companies differing only by that
    # suffix). The suffix-stripped fallback (normalize_core) only runs
    # when Xetra recorded a wrong suffix and nothing matched at full
    # specificity (confirmed real for UPM-Kymmene, where Xetra wrote
    # "Corp." for the real "Oyj").
    full_matches = _candidates_matching(target_name, payload, normalize_full)
    if full_matches:
        distinct_ids = {c["businessId"]["value"] for c in full_matches}
        if len(distinct_ids) > 1:
            return None, "ambiguous_multiple_distinct_business_ids_match_name"
        return full_matches[0], "exact_normalized_name_match_full_suffix"

    core_matches = _candidates_matching(target_name, payload, normalize_core)
    if not core_matches:
        return None, "no_exact_normalized_name_match"
    distinct_ids = {c["businessId"]["value"] for c in core_matches}
    if len(distinct_ids) > 1:
        return None, "ambiguous_multiple_distinct_business_ids_match_name"
    return core_matches[0], "exact_normalized_name_match_core_fallback_wrong_xetra_suffix"


def english_description(main_business_line: dict | None) -> str:
    if not main_business_line:
        return ""
    for entry in main_business_line.get("descriptions", []):
        if entry.get("languageCode") == ENGLISH_LANGUAGE_CODE:
            return entry.get("description", "")
    return ""


def build_record(row: dict[str, str], status: str, reason: str, created_at: str, business_id: str = "", tol_code: str = "", description_en: str = "") -> dict[str, Any]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "business_id": business_id, "fetch_status": status, "fetch_reason": reason,
        "tol_code": tol_code, "tol_description_en": description_en, "phase": PHASE, "created_at_utc": created_at,
    }


FIELDS = ["asset_id", "ticker", "company_name", "isin", "business_id", "fetch_status", "fetch_reason", "tol_code", "tol_description_en", "phase", "created_at_utc"]


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_tol_codes_fetched": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def build(input_matrix: Path, output_dir: Path, execute: bool) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("home_country") == JURISDICTION_FILTER and r.get("resolution_status") == "resolved"]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "eligible_companies": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}

    records: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        try:
            payload = search_company(row["resolved_company_name"])
        except urllib.error.HTTPError as exc:
            records.append(build_record(row, "error", f"http_error_{exc.code}", created_at))
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            records.append(build_record(row, "error", type(exc).__name__, created_at))
            continue
        match, reason = match_company(row["resolved_company_name"], payload)
        if match is None:
            records.append(build_record(row, "unresolved", reason, created_at))
            continue
        main_business_line = match.get("mainBusinessLine")
        description_en = english_description(main_business_line)
        tol_code = (main_business_line or {}).get("type", "")
        if not tol_code:
            records.append(build_record(row, "no_tol_on_record", "main_business_line_absent", created_at, business_id=match["businessId"]["value"]))
            continue
        records.append(build_record(row, "resolved", reason, created_at, business_id=match["businessId"]["value"], tol_code=tol_code, description_en=description_en))

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_finland_tol_v2_38au.csv", records, FIELDS)
    resolved = sum(1 for r in records if r["fetch_status"] == "resolved")
    report = {
        "phase": PHASE, "status": "COMPLETED_EUROPE_FINLAND_TOL",
        "eligible_companies": len(rows), "companies_fetched": len(records), "companies_with_tol": resolved,
        "companies_unresolved": sum(1 for r in records if r["fetch_status"] == "unresolved"),
        "companies_error": sum(1 for r in records if r["fetch_status"] == "error"),
        "network_used": True, "credentials_used": False, "raw_cache_published": False,
        "scoring_created": False, "ranking_created": False, "recommendations_created": False, "phase9c_authorized": False,
        "note": "PRH's YTJ open-data API returns an already-English sector description on every real record -- no manual translation table needed, unlike every other country attacked so far. Same real, confirmed limitation as everywhere else: Nokia Oyj and Sampo Oyj both show TOL 70100/64210 ('Activities of head offices' / 'Activities of holding companies') -- the registered entity is the group's holding/management company for at least these two, not necessarily its full operating business.",
    }
    write_text(output_dir / "europe_finland_tol_report_v2_38au.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform the real PRH YTJ open-data lookups (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()

    if not args.execute:
        report = build(args.input_matrix, args.output_dir, False)
        print(json.dumps(report, sort_keys=True))
        return 0
    if not args.input_matrix.exists():
        return blocked("input_matrix_not_found")

    report = build(args.input_matrix, args.output_dir, True)
    print(json.dumps({k: report[k] for k in ("status", "eligible_companies", "companies_with_tol", "companies_error")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
