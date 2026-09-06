#!/usr/bin/env python3
"""Block 9AW: resolve the real Luxembourg RCS ("B" registration) number for
each of the 20 Luxembourg companies identified in v2.38AV, as a prerequisite
for reading the Centrale des Bilans (STATEC) annual-accounts bulk XML files
-- those files key every filing by RcsNumber, confirmed live by fetching a
byte-range sample of the real 2026 Q1 file.

Real finding first: GLEIF's ISIN->LEI mapping, already the trusted method
for CH/IT/DK/AT/BE/FI/SE (v2.38AF) and NL (v2.38AE), has ZERO coverage for
all 20 Luxembourg ISINs from v2.38AV (checked live, one call per ISIN --
same class of confirmed gap already documented for Finland in v2.38AF).
This is not a bug in this project's method; GLEIF simply never received an
ISIN mapping for these particular securities.

Fallback: GLEIF's own legal-name search (filter[entity.legalName], scoped
to filter[entity.legalAddress.country]=LU) resolves this instead --
confirmed live that this filter behaves as a prefix/token match, not a
strict single-record exact match (e.g. searching "ArcelorMittal" returns
30 Luxembourg entities, one of them the real parent with no suffix at all).
Fail-closed discipline: this script never takes "the first result". It
strips a candidate's own trailing legal-form marker (S.A., SE, SCA, ...)
the same way it strips the search key's, then requires every remaining
token to match exactly EXCEPT a truncated trailing token (Xetra truncates
long words with a "." -- "PROPERT." for "Properties", "CELL." for
"Cellular" -- confirmed already in this project for share-type/denomination
markers, same truncation convention, just applied to whole words here),
which only needs to match as a case-insensitive prefix. Zero candidates or
more than one surviving candidate after this filter is unresolved, never
guessed.
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
INPUT_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38av_europe_mismatch_identity_resolution/europe_mismatch_identity_resolution_matrix_v2_38av.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38aw_europe_luxembourg_rcs_gleif"
PHASE = "v2.38AW-europe-luxembourg-rcs-gleif"
GLEIF_URL = "https://api.gleif.org/api/v1/lei-records"
GLEIF_MIN_SECONDS_BETWEEN_CALLS = 0.3
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 65.0
TARGET_COUNTRY = "LU"

# Share-class / share-type markers Xetra appends that this specific
# Luxembourg batch introduced and that v2.38AB's clean_company_name never
# needed to strip (NOUV. = "nouvelles" (new shares); NPV = no par value;
# ORD. = ordinary shares; DEM. = "demand"/registered marker seen on Eleving
# Group) -- presentation noise only, never part of the real legal name.
EXTRA_SHARE_MARKER_RE = re.compile(r"\s*(NOUV|NPV|ORD|DEM)\.?$", re.IGNORECASE)

# Trailing legal-form tokens, stripped from BOTH the search key and every
# GLEIF candidate before token-by-token comparison -- a real legal name may
# or may not carry one, so matching must work whether or not it is present.
# Confirmed live that Luxembourg entities spell "S.A." both with dots
# ("ArcelorMittal S.A.") and without ("Aroundtown SA") -- both accepted.
LEGAL_FORM_RE = re.compile(r"\s+(S\.?A\.?|SE|SCA|S\.C\.A\.?|N\.?V\.?|PLC|AG|GMBH|LTD|INC|CORP|S\.�\s*R\.?L\.?|SARL)$", re.IGNORECASE)

# Standard, dictionary-verifiable business-word abbreviations Xetra uses
# that are NOT truncations (no trailing "." marker, because the whole word
# is contracted, not cut off mid-word) -- confirmed real for two distinct
# companies (Millicom "Intl" for "International"; CPI/Global Fashion/Eleving
# "Grp" for "Group"). Generic and dictionary-standard, not a per-company
# guess -- the same class of fix as this project's existing AE/OE
# transliteration table for Finnish/German vowels.
TOKEN_ABBREVIATIONS = {"INTL": "INTERNATIONAL", "GRP": "GROUP", "CORP": "CORPORATION", "MGMT": "MANAGEMENT"}


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


def strip_legal_form(name: str) -> str:
    stripped = name.strip()
    changed = True
    while changed:
        changed = False
        new_stripped = LEGAL_FORM_RE.sub("", stripped).strip()
        if new_stripped != stripped and new_stripped:
            stripped = new_stripped
            changed = True
    return stripped


def search_key(resolved_company_name: str) -> str:
    """Strip Xetra's extra share-class markers, then the legal form, to get
    the string actually sent to GLEIF's legalName filter."""
    no_share_marker = EXTRA_SHARE_MARKER_RE.sub("", resolved_company_name).strip()
    return strip_legal_form(no_share_marker)


def tokens_match(search_tokens: list[str], candidate_tokens: list[str]) -> bool:
    """Every token must match exactly, except the LAST search token: if it
    ends with '.' (Xetra's truncation marker for a word cut short to fit
    column width), it only needs to be a case-insensitive prefix of the
    candidate's corresponding token."""
    if len(search_tokens) != len(candidate_tokens):
        return False
    for i, (s, c) in enumerate(zip(search_tokens, candidate_tokens)):
        is_last = i == len(search_tokens) - 1
        if is_last and s.endswith("."):
            if not c.lower().startswith(s[:-1].lower()):
                return False
        elif s.upper() in TOKEN_ABBREVIATIONS:
            if TOKEN_ABBREVIATIONS[s.upper()] != c.upper():
                return False
        elif s.lower() != c.lower():
            return False
    return True


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


MAX_PAGES = 10


def query_word(key: str) -> str:
    """GLEIF's legalName filter matches candidates whose legal name STARTS
    WITH the literal filter string (confirmed live: filter="ArcelorMittal"
    returns every "ArcelorMittal ..." subsidiary) -- it does not expand
    abbreviations. Sending it the full, still-abbreviated multi-word key
    (e.g. "MILLICOM INTL CELL.") therefore matches nothing, because no real
    legal name literally starts with an abbreviated middle word. The fix
    already proven for the same class of problem in Finland (v2.38AU):
    query with only the first token -- always the real, unabbreviated brand
    word in this batch -- and let this script's own token-by-token
    comparison (with truncation tolerance) do the precise matching among
    whatever candidates come back."""
    return key.split()[0] if key else key


def gleif_name_lookup(key: str, country: str) -> tuple[list[dict], str]:
    word = query_word(key)
    records: list[dict] = []
    page = 1
    while page <= MAX_PAGES:
        query = urllib.parse.urlencode({"filter[entity.legalName]": word, "filter[entity.legalAddress.country]": country, "page[size]": "200", "page[number]": str(page)})
        status, payload = http_get_json(f"{GLEIF_URL}?{query}")
        if status != 200 or payload is None:
            return [], f"gleif_http_error_{status}"
        batch = payload.get("data", [])
        records.extend(batch)
        pagination = payload.get("meta", {}).get("pagination", {})
        if page >= pagination.get("lastPage", page) or not batch:
            break
        page += 1
    return records, "queried"


def find_exact_candidates(key: str, records: list[dict]) -> list[dict]:
    search_tokens = key.split()
    matches = []
    for rec in records:
        entity = rec.get("attributes", {}).get("entity", {})
        legal_name = (entity.get("legalName") or {}).get("name", "")
        candidate_core = strip_legal_form(legal_name)
        candidate_tokens = candidate_core.split()
        if tokens_match(search_tokens, candidate_tokens):
            matches.append(rec)
    return matches


def build(input_matrix: Path, output_dir: Path, execute: bool) -> dict[str, Any]:
    rows = [r for r in read_csv(input_matrix) if r.get("real_home_country_guess") == "Luxembourg" and r.get("resolution_status") == "resolved"]
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if not execute:
        return {"status": "DRY_RUN", "eligible_assets": len(rows), "network_used": False, "phase9c_authorized": False}

    matrix = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(GLEIF_MIN_SECONDS_BETWEEN_CALLS)
        key = search_key(row["resolved_company_name"])
        records, reason = gleif_name_lookup(key, TARGET_COUNTRY)
        if reason != "queried":
            matrix.append(_record(row, key, "unresolved", reason, created_at))
            continue
        candidates = find_exact_candidates(key, records)
        if not candidates:
            matrix.append(_record(row, key, "unresolved", "no_exact_normalized_name_match_in_luxembourg", created_at))
            continue
        if len(candidates) > 1:
            matrix.append(_record(row, key, "unresolved", "ambiguous_multiple_luxembourg_entities_match_normalized_name", created_at))
            continue
        entity = candidates[0].get("attributes", {}).get("entity", {})
        legal_name = (entity.get("legalName") or {}).get("name", "")
        rcs_number = entity.get("registeredAs", "")
        status = entity.get("status", "")
        matrix.append(_record(row, key, "resolved", "exact_token_match_single_luxembourg_entity", created_at, lei=candidates[0].get("id", ""), legal_name=legal_name, rcs_number=rcs_number, entity_status=status))

    resolved = [r for r in matrix if r["gleif_lookup_status"] == "resolved"]
    report = {
        "phase": PHASE, "input_assets": len(rows), "resolved": len(resolved), "unresolved": len(matrix) - len(resolved),
        "unresolved_reasons": {reason: sum(1 for r in matrix if r["gleif_lookup_status"] == "unresolved" and r["gleif_lookup_reason"] == reason) for reason in sorted({r["gleif_lookup_reason"] for r in matrix if r["gleif_lookup_status"] == "unresolved"})},
        "isin_based_gleif_lookup_confirmed_zero_coverage": True,
        "resolution_method": "gleif_legal_name_prefix_filter_plus_exact_token_verification_country_lu",
        "credentials_used": False, "network_used": True, "phase9c_authorized": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv", matrix, MATRIX_FIELDS)
    write_text(output_dir / "europe_luxembourg_rcs_gleif_summary_v2_38aw.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


MATRIX_FIELDS = [
    "asset_id", "ticker", "resolved_company_name", "isin", "search_key", "gleif_lookup_status",
    "gleif_lookup_reason", "lei", "gleif_legal_name", "rcs_number", "entity_status", "phase", "created_at_utc",
]


def _record(row: dict[str, str], key: str, status: str, reason: str, created_at: str, lei: str = "", legal_name: str = "", rcs_number: str = "", entity_status: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "resolved_company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "search_key": key, "gleif_lookup_status": status, "gleif_lookup_reason": reason,
        "lei": lei, "gleif_legal_name": legal_name, "rcs_number": rcs_number, "entity_status": entity_status,
        "phase": PHASE, "created_at_utc": created_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = build(args.input_matrix, args.output_dir, args.execute)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
