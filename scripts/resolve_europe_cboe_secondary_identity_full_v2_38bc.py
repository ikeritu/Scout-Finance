#!/usr/bin/env python3
"""Block 9BC: scale the v2.38BB Cboe Europe secondary-listing identity
method (refined across 4 real, live-verified bug fixes, 28% -> 58.7% on a
75-company reproducible pilot) to the full ~9,630-candidate population,
per the user's explicit decision to scale after refinement.

Reuses v2.38BB's exact matching functions unmodified (normalize_key,
raw_words, gleif_query, find_exact_candidates, select_candidates,
load_known_names) -- this script only adds what scale requires that a
75-company pilot did not: resumability (skip any asset_id already
resolved in a prior run, since a run over ~9,630 real candidates takes
well over an hour and must survive an interruption), incremental atomic
writes (never hold the full result set in memory only, write progress as
it goes), and a progress report on stderr so a long-running background
job is observable.

Same fail-closed discipline throughout: zero or multiple distinct
countries for an exact name match -> unresolved/ambiguous, never guessed.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PILOT_SCRIPT = ROOT / "scripts/resolve_europe_cboe_secondary_identity_pilot_v2_38bb.py"
HOME_EXCHANGE_CSV = ROOT / "outputs/full_universe_source_acquisition/v2_38n_europe_home_exchange_resolution/europe_home_exchange_resolution_v2_38n.csv"
EU_IDENTITY_CSV = ROOT / "outputs/full_universe_source_acquisition/v2_38ab_europe_full_identity_resolution/europe_full_identity_resolution_xetra_source_matrix_v2_38ab.csv"
CENSUS_XZ = ROOT / "outputs/full_universe_source_acquisition/v2_38a_global_universe_audit/global_universe_audited_v2_38a.csv.xz"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bc_europe_cboe_secondary_identity_full"
PHASE = "v2.38BC-europe-cboe-secondary-identity-full"
MATRIX_PATH = OUT / "europe_cboe_secondary_identity_full_matrix_v2_38bc.csv"
GLEIF_MIN_SECONDS_BETWEEN_CALLS = 0.3
PROGRESS_EVERY = 100

MATRIX_FIELDS = ["asset_id", "ticker", "company_name", "search_key", "status", "reason", "lei", "legal_name", "country", "candidate_count", "candidate_countries", "query_strategy", "phase", "created_at_utc"]


def load_pilot_module():
    """Cached: reusing the same module object across calls (rather than a
    fresh exec_module() each time) is what lets a test monkeypatch its
    http_get_json once and have that patch actually take effect inside
    build()'s own internal call to this function."""
    if not hasattr(load_pilot_module, "_cached"):
        spec = importlib.util.spec_from_file_location("resolve_europe_cboe_secondary_identity_pilot_v2_38bb", PILOT_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        load_pilot_module._cached = mod
    return load_pilot_module._cached


def read_existing_matrix(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {row["asset_id"]: row for row in csv.DictReader(f)}


def append_rows(path: Path, rows: list[dict[str, Any]], write_header: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if path.exists() and not write_header else "w"
    with path.open(mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATRIX_FIELDS, lineterminator="\n", extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build(home_exchange_csv: Path, eu_identity_csv: Path, census_xz: Path, matrix_path: Path, output_dir: Path, execute: bool, flush_every: int, limit: int | None = None) -> dict[str, Any]:
    mod = load_pilot_module()
    known_names = mod.load_known_names(eu_identity_csv, census_xz)
    all_candidates = mod.select_candidates(home_exchange_csv, known_names)
    uniq: dict[str, dict[str, str]] = {}
    for row in all_candidates:
        key = mod.normalize_key(row["company_name"])
        uniq.setdefault(key, row)
    candidates = sorted(uniq.values(), key=lambda r: r["asset_id"])

    existing = read_existing_matrix(matrix_path)
    remaining_all = [row for row in candidates if row["asset_id"] not in existing]
    remaining = remaining_all[:limit] if limit else remaining_all

    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "total_candidates": len(candidates), "already_resolved_this_run_previously": len(existing), "remaining_to_process": len(remaining_all), "network_used": False, "phase9c_authorized": False}

    write_header = not matrix_path.exists()
    buffer: list[dict[str, Any]] = []
    processed_this_session = 0
    started_at = time.time()
    for i, row in enumerate(remaining):
        if i > 0:
            time.sleep(GLEIF_MIN_SECONDS_BETWEEN_CALLS)
        key = mod.normalize_key(row["company_name"])
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        records, reason, query_strategy = mod.gleif_lookup_no_country(row["company_name"], key)
        if reason != "queried":
            buffer.append(mod._record(row, key, "unresolved", reason, created_at))
        else:
            exact = mod.find_exact_candidates(key, records)
            if not exact:
                buffer.append(mod._record(row, key, "unresolved", "no_exact_normalized_name_match_gleif", created_at))
            else:
                countries = {(c.get("attributes", {}).get("entity", {}).get("legalAddress", {}) or {}).get("country", "") for c in exact}
                if len(countries) > 1:
                    buffer.append(mod._record(row, key, "ambiguous", "multiple_distinct_countries_match_same_name", created_at, candidate_count=len(exact), candidate_countries="|".join(sorted(countries))))
                elif len(exact) > 1:
                    buffer.append(mod._record(row, key, "ambiguous", "multiple_distinct_entities_same_country_same_name", created_at, candidate_count=len(exact), candidate_countries="|".join(sorted(countries))))
                else:
                    entity = exact[0].get("attributes", {}).get("entity", {})
                    buffer.append(mod._record(
                        row, key, "resolved", "exact_single_gleif_match_no_country_filter", created_at,
                        lei=exact[0].get("id", ""), legal_name=(entity.get("legalName") or {}).get("name", ""),
                        country=(entity.get("legalAddress") or {}).get("country", ""), query_strategy=query_strategy,
                    ))
        processed_this_session += 1
        if len(buffer) >= flush_every:
            append_rows(matrix_path, buffer, write_header)
            write_header = False
            buffer = []
        if processed_this_session % PROGRESS_EVERY == 0:
            elapsed = time.time() - started_at
            rate = processed_this_session / elapsed if elapsed > 0 else 0
            remaining_count = len(remaining) - processed_this_session
            eta_seconds = remaining_count / rate if rate > 0 else 0
            print(f"progress: {processed_this_session}/{len(remaining)} this session, {elapsed:.0f}s elapsed, ETA {eta_seconds / 60:.1f} min", file=sys.stderr, flush=True)
    if buffer:
        append_rows(matrix_path, buffer, write_header)

    final_rows = list(read_existing_matrix(matrix_path).values())
    resolved = [r for r in final_rows if r["status"] == "resolved"]
    ambiguous = [r for r in final_rows if r["status"] == "ambiguous"]
    unresolved = [r for r in final_rows if r["status"] == "unresolved"]
    by_country = Counter(r["country"] for r in resolved if r["country"])
    by_query_strategy = Counter(r["query_strategy"] for r in resolved if r["query_strategy"])

    report = {
        "phase": PHASE, "total_candidates": len(candidates), "processed_total": len(final_rows),
        "processed_this_session": processed_this_session, "resolved": len(resolved), "ambiguous": len(ambiguous),
        "unresolved": len(unresolved),
        "resolved_rate_pct": round(100 * len(resolved) / len(final_rows), 1) if final_rows else 0,
        "ambiguous_rate_pct": round(100 * len(ambiguous) / len(final_rows), 1) if final_rows else 0,
        "resolved_by_country": dict(sorted(by_country.items(), key=lambda kv: -kv[1])),
        "resolved_by_query_strategy": dict(by_query_strategy),
        "complete": len(final_rows) == len(candidates),
        "network_used": True, "credentials_used": False, "phase9c_authorized": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_text(output_dir / "europe_cboe_secondary_identity_full_summary_v2_38bc.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home-exchange-csv", type=Path, default=HOME_EXCHANGE_CSV)
    parser.add_argument("--eu-identity-csv", type=Path, default=EU_IDENTITY_CSV)
    parser.add_argument("--census-xz", type=Path, default=CENSUS_XZ)
    parser.add_argument("--matrix-path", type=Path, default=MATRIX_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None, help="process at most this many remaining candidates this invocation, then exit cleanly (0) -- for chunked/looped runs")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = build(args.home_exchange_csv, args.eu_identity_csv, args.census_xz, args.matrix_path, args.output_dir, args.execute, args.flush_every, args.limit)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
