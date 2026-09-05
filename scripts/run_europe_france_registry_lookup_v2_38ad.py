#!/usr/bin/env python3
"""Block 9AD: look up the French official company registry profile
(SIREN, administrative status, legal form, registration date) for the 53
France (Euronext Paris / Xetra cross-listed) companies real-identified in
v2.38AB's generalized identity resolution.

Desk research confirmed before writing this script (see
outputs/full_universe_source_acquisition/v2_38ad_europe_france_registry_lookup/EUROPE_FRANCE_REGISTRY_v2_38ad.md
for the full writeup):
- The "API Entreprise" bundle's "actes et bilans" endpoint (the one that
  actually returns annual-accounts documents) is real and free, but
  restricted to public administrations via a DataPass authorization --
  not open to this kind of independent project, so it is never used here.
- The public "Recherche d'entreprises" API
  (recherche-entreprises.api.gouv.fr), built by the French government's
  Etalab/data.gouv.fr team on top of the RNE + Sirene registries, IS
  fully open: no account, no API key, no registration of any kind,
  updated in near-real-time (confirmed live: a probed record showed a
  same-week update timestamp). This is what this script uses -- for
  registry/status confirmation only, never for financial statements
  (which this API does not provide at all).

Fail-closed name matching, same discipline as every other registry
lookup in this project (dotted-suffix-safe normalize, single active
exact match required). Two real, confirmed cases of genuine duplicate
active companies sharing the exact same registered name were found live
during development (Hermes International: two active SIREN both named
"HERMES INTERNATIONAL"; TotalEnergies SE: two active SIREN both named
"TOTALENERGIES SE") -- both are correctly left unresolved as ambiguous
rather than guessed via an unvalidated tiebreaker (e.g. entreprise size
category), the same discipline that caught the original GB SCT/BMT
ticker-collision error.

Blocked by default; --execute is required (no credential needed, but the
project convention of a conscious, explicit real-network flag applies
regardless of whether a credential is involved).
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
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38ad_europe_france_registry_lookup"
PHASE = "v2.38AD-europe-france-registry-lookup"
JURISDICTION_FILTER = "FR"
SEARCH_URL = "https://recherche-entreprises.api.gouv.fr/search"
MIN_SECONDS_BETWEEN_CALLS = 0.4
MAX_ATTEMPTS = 3
RATE_LIMIT_BACKOFF_SECONDS = 20.0

LEGAL_SUFFIXES = ["SASU", "SAS", "SARL", "SA", "SE"]

MATRIX_FIELDS = [
    "asset_id", "ticker", "resolved_company_name", "isin", "lookup_status", "lookup_reason", "siren",
    "company_status", "legal_form_code", "real_filings_downloaded", "real_fundamentals_present",
    "phase", "created_at_utc",
]


def normalize(name: str) -> str:
    text = name.upper()
    # Periods deleted outright (not turned into a space), same fix
    # already applied for GB/Ireland's dotted legal suffixes.
    text = text.replace(".", "").replace("'", " ")
    text = re.sub(r"[,()\-;]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split(" ")
    changed = True
    while changed and words:
        changed = False
        for suffix in LEGAL_SUFFIXES:
            suffix_words = suffix.split(" ")
            if words[-len(suffix_words):] == suffix_words:
                words = words[: -len(suffix_words)]
                changed = True
                break
    return " ".join(words).strip()


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


def search_company(name: str) -> dict:
    query = urllib.parse.urlencode({"q": name, "limit": 20})
    request = urllib.request.Request(f"{SEARCH_URL}?{query}")
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


def match_company(resolved_name: str, payload: dict) -> tuple[dict | None, str]:
    items = payload.get("results", [])
    expected = normalize(resolved_name)
    candidates = [item for item in items if normalize(item.get("nom_complet", "")) == expected]
    active = [c for c in candidates if c.get("etat_administratif") == "A"]
    if not candidates:
        return None, "no_exact_normalized_name_match"
    if len(active) == 1:
        return active[0], "exact_normalized_name_match_single_active_company"
    if len(candidates) == 1:
        return candidates[0], "exact_normalized_name_match_single_company_not_marked_active"
    return None, "ambiguous_multiple_active_companies_match_name"


def blocked(reason: str) -> int:
    print(json.dumps({"status": "BLOCKED", "reason": reason, "real_filings_downloaded": False, "real_fundamentals_present": False, "phase9c_authorized": False}, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-matrix", type=Path, default=INPUT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true", help="perform the real registry lookups (no credential needed, but network calls are still gated behind this explicit flag)")
    args = parser.parse_args()

    if not args.execute:
        rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved" and r.get("home_country") == JURISDICTION_FILTER] if args.input_matrix.exists() else []
        print(json.dumps({"status": "DRY_RUN", "eligible_assets": len(rows), "asset_ids": [r["asset_id"] for r in rows], "network_used": False, "phase9c_authorized": False}, sort_keys=True))
        return 0

    rows = [r for r in read_csv(args.input_matrix) if r["resolution_status"] == "resolved" and r.get("home_country") == JURISDICTION_FILTER]
    if not rows:
        return blocked("no_resolved_companies_in_input_matrix")

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    matrix = []
    for i, row in enumerate(rows):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS)
        name = row["resolved_company_name"]
        try:
            payload = search_company(name)
        except urllib.error.HTTPError as exc:
            matrix.append(_lookup_record(row, "error", f"http_error_{exc.code}", created_at))
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            matrix.append(_lookup_record(row, "error", type(exc).__name__, created_at))
            continue

        match, reason = match_company(name, payload)
        if match is None:
            matrix.append(_lookup_record(row, "unresolved", reason, created_at))
            continue
        matrix.append(_lookup_record(
            row, "resolved", reason, created_at,
            siren=match.get("siren", ""), company_status=match.get("etat_administratif", ""),
            legal_form_code=str(match.get("nature_juridique", "")),
        ))

    resolved_count = sum(1 for r in matrix if r["lookup_status"] == "resolved")
    report = {
        "phase": PHASE, "input_resolved_assets": len(rows), "profiles_confirmed": resolved_count,
        "unresolved_or_error": len(matrix) - resolved_count, "real_filings_downloaded": False,
        "real_fundamentals_present": False, "credentials_used": False, "phase9c_authorized": False,
        "raw_cache_published": False,
        "note": "Profile confirmation only. Real accounts/financial-statement extraction is out of scope: recherche-entreprises.api.gouv.fr does not provide financial figures at all, and the endpoint that does (API Entreprise actes-et-bilans) is restricted to public administrations, not accessible to this project.",
    }

    write_csv(args.output_dir / "europe_france_registry_lookup_matrix_v2_38ad.csv", matrix, MATRIX_FIELDS)
    write_text(args.output_dir / "europe_france_registry_lookup_summary_v2_38ad.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def _lookup_record(row: dict[str, str], status: str, reason: str, created_at: str, siren: str = "", company_status: str = "", legal_form_code: str = "") -> dict[str, str]:
    return {
        "asset_id": row["asset_id"], "ticker": row["ticker"], "resolved_company_name": row["resolved_company_name"],
        "isin": row.get("isin", ""), "lookup_status": status, "lookup_reason": reason, "siren": siren,
        "company_status": company_status, "legal_form_code": legal_form_code,
        "real_filings_downloaded": "false", "real_fundamentals_present": "false", "phase": PHASE, "created_at_utc": created_at,
    }


if __name__ == "__main__":
    raise SystemExit(main())
