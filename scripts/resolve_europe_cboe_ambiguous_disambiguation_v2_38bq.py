#!/usr/bin/env python3
"""Block v2.38BQ: attack the 530 companies v2.38BC left "ambiguous" --
multiple distinct, real GLEIF legal-entity records exactly matching the
same normalized company name, where the fail-closed discipline correctly
refused to guess between them.

Real investigation before writing this script (not assumed): a live
pilot against a broad, real sample of the 530 showed that most of this
"ambiguity" is not genuine confusion between unrelated companies -- it is
a large multinational's many real, distinct, LEI-registered national
subsidiaries/predecessor entities sharing an identical name after legal-
form stripping (Volkswagen AG had a real duplicate DE registration and a
retired FR fund entity alongside its one real active DE parent; HP Inc
had a retired FR shell alongside the real active US entity; AbbVie Inc
had 12 real national subsidiaries, only one of which is currently
ISSUED with the source's own "Inc" legal form). Two real, GLEIF-provided
signals -- never a guess -- reliably narrow this down for a real
majority of cases:

  Tier 1 (resolved -- same trust level as every other name-based GLEIF
  match already accepted throughout this project): among the exact-name
  candidates, keep only those with registration.status == "ISSUED"
  (GLEIF's own signal that a registration is currently active and
  maintained, as opposed to LAPSED, RETIRED, ANNULLED or DUPLICATE --
  all real, GLEIF-assigned states, never inferred). If exactly one
  candidate survives, resolve. This introduces no new kind of inference
  beyond what v2.38BB/BC's original exact-single-match resolutions
  already carry.

  Tier 2 (narrowed_unconfirmed -- deliberately NOT "resolved", see the
  real counter-example below): only tried if Tier 1 leaves more than one
  candidate. Keeps only ISSUED candidates whose own trailing legal-form
  token (e.g. "AG", "Inc", "ASA", "SpA") matches the SOURCE company
  name's own trailing legal-form token. If exactly one survives, it is
  surfaced as a real, plausible narrowing -- but NOT promoted to
  resolved identity, because a real, confirmed counter-example was found
  while validating this exact heuristic: "Danone SA" narrowed cleanly to
  a real, active Spanish subsidiary ("DANONE SA", ES) whose own legal
  name happens to carry the same "SA" suffix as Cboe's source name --
  but the real French parent is registered at GLEIF simply as "DANONE"
  with NO suffix at all, so it never matched and was silently passed
  over. Cboe's reference data appending a generic legal-form label does
  not always reflect how the true target is actually registered at
  GLEIF. Unlike Tier 1, this is a genuinely NEW layer of inference this
  project has never relied on before, and it has now been shown to pick
  the wrong entity in a real, verifiable case -- so it stays a distinct,
  lower-confidence status, surfacing the candidate for a human to
  confirm rather than silently promoting a plausible guess into identity.

Anything that still has more than one candidate after both tiers stays
honestly ambiguous, with the real candidate count and countries
preserved -- never a best guess, same discipline as v2.38BB/BC.

Real bug found and fixed LOCALLY while building this (not in v2.38BB's
shared normalize_key): Italian companies are commonly registered at
GLEIF with dot-separated single-letter legal forms ("S.P.A." rather than
"SpA") -- v2.38BB's normalize_key replaces periods with spaces BEFORE
checking for a trailing legal-form word, so "S.P.A." becomes three
separate one-letter tokens ("S", "P", "A") and never matches the "SPA"
alternative in LEGAL_FORM_RE. This caused a real, confirmed miss: ACEA
SpA (a real, well-known Italian utility, Cboe ticker "ACEm" -- the "m"
suffix marking it as a mirror of its real Borsa Italiana listing) was
never even offered as a candidate under the buggy key, only two
unrelated French "ACEA" entities were -- live-verified that GLEIF
holds a real, active "ACEA S.P.A." (Italy, LEI 549300Q3448N041CTH56)
that the buggy key silently excluded. Fixed HERE by collapsing any
run of two or more single-letter-dot groups ("S.P.A.", "N.V.", "A.O.")
into one contiguous token before normalizing -- applied consistently to
both the source name and every candidate's legal name, so the fix can
never introduce an asymmetry between the two sides of a comparison.

This fix is deliberately NOT made to v2.38BB's own normalize_key in
place: that function is imported unmodified by several already-
completed, already-documented phases (v2.38BC's full 7,590-candidate
run, v2.38BF's Austria/Finland resolution) -- changing its behavior
retroactively would risk silently drifting their already-verified,
already-cited real results without a fresh re-verification pass. Fixing
it only within this new script's own re-query of the 530 keeps this
block's scope to what it was actually asked to do. Whether to fix
v2.38BB itself and re-run the full population (which could plausibly
rescue a few more Italian S.p.A. companies from the 3,294 genuinely
unresolved bucket too) is left as an explicit, real, deferred decision
for the user -- not undertaken here.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import time
import urllib.error
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BB_SCRIPT = ROOT / "scripts/resolve_europe_cboe_secondary_identity_pilot_v2_38bb.py"
BC_MATRIX = ROOT / "outputs/full_universe_source_acquisition/v2_38bc_europe_cboe_secondary_identity_full/europe_cboe_secondary_identity_full_matrix_v2_38bc.csv"
PHASE = "v2.38BQ-europe-cboe-ambiguous-disambiguation"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bq_europe_cboe_ambiguous_disambiguation"

GLEIF_MIN_SECONDS_BETWEEN_CALLS = 0.3
MAX_LIMIT = 600

DOTTED_ABBREVIATION_RE = re.compile(r"\b(?:[A-Za-z]\.){2,}")

MATRIX_FIELDS = [
    "asset_id", "ticker", "company_name", "search_key", "status", "reason",
    "lei", "legal_name", "country", "match_tier", "candidate_count_after_fix", "candidate_countries",
    "phase", "created_at_utc",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_bb_module():
    if not hasattr(load_bb_module, "_cached"):
        spec = importlib.util.spec_from_file_location("resolve_europe_cboe_secondary_identity_pilot_v2_38bb", BB_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        load_bb_module._cached = mod
    return load_bb_module._cached


def collapse_dotted_abbreviations(name: str) -> str:
    return DOTTED_ABBREVIATION_RE.sub(lambda m: m.group(0).replace(".", ""), name or "")


def fixed_key(bb, name: str) -> str:
    return bb.normalize_key(collapse_dotted_abbreviations(name))


def trailing_legal_form(name: str) -> str:
    collapsed = collapse_dotted_abbreviations(name)
    tokens = re.sub(r"[.,]", " ", collapsed).split()
    return tokens[-1].upper() if tokens else ""


def read_ambiguous(matrix_path: Path) -> list[dict[str, str]]:
    if not matrix_path.exists():
        raise SystemExit(f"BLOCKED: required v2.38BC matrix not found: {matrix_path}")
    with matrix_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r.get("status") == "ambiguous"]


def read_existing(output_path: Path) -> dict[str, dict[str, str]]:
    if not output_path.exists():
        return {}
    with output_path.open(encoding="utf-8", newline="") as f:
        return {row["asset_id"]: row for row in csv.DictReader(f)}


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


def resolve_key(bb, name: str, key: str, run=None) -> dict[str, Any]:
    """Real, fail-closed two-tier disambiguation for one normalized key.
    Reuses bb.gleif_lookup_no_country() unmodified for the network query
    (its own internal exact-match check may be wrong under the buggy
    key, but that only affects whether it ALSO tries a two-word retry --
    it only ever adds candidates, never removes any, so the raw records
    it returns are safe to re-filter here with the fixed key)."""
    records, reason, strategy = bb.gleif_lookup_no_country(name, key)
    if reason != "queried":
        return {"status": "unresolved", "reason": reason, "match_tier": "", "lei": "", "legal_name": "", "country": "", "candidate_count_after_fix": 0, "candidate_countries": ""}
    exact = [rec for rec in records if fixed_key(bb, (rec.get("attributes", {}).get("entity", {}).get("legalName") or {}).get("name", "")) == key]
    if not exact:
        return {"status": "unresolved", "reason": "no_exact_normalized_name_match_after_fix", "match_tier": "", "lei": "", "legal_name": "", "country": "", "candidate_count_after_fix": 0, "candidate_countries": ""}

    def entity_of(rec):
        return rec.get("attributes", {}).get("entity", {})

    def country_of(rec):
        return (entity_of(rec).get("legalAddress") or {}).get("country", "")

    def reg_status_of(rec):
        return (rec.get("attributes", {}).get("registration", {}) or {}).get("status", "")

    issued = [rec for rec in exact if reg_status_of(rec) == "ISSUED"]
    countries = "|".join(sorted({c for c in (country_of(r) for r in exact) if c}))

    if len(issued) == 1:
        ent = entity_of(issued[0])
        return {
            "status": "resolved", "reason": "tier1_single_issued_registration_among_exact_matches", "match_tier": "tier1_single_issued",
            "lei": issued[0].get("id", ""), "legal_name": (ent.get("legalName") or {}).get("name", ""), "country": country_of(issued[0]),
            "candidate_count_after_fix": len(exact), "candidate_countries": countries,
        }
    if len(issued) > 1:
        src_form = trailing_legal_form(name)
        form_matches = [rec for rec in issued if src_form and trailing_legal_form((entity_of(rec).get("legalName") or {}).get("name", "")) == src_form]
        if len(form_matches) == 1:
            # Real, confirmed failure mode found while building this block
            # (not hypothetical): "Danone SA" narrowed via this exact
            # suffix-match logic to "DANONE SA" (Spain), a real, active,
            # currently-ISSUED subsidiary -- but the real French parent
            # is registered at GLEIF with NO suffix at all ("DANONE",
            # bare), so it never matched the source's own "SA" suffix and
            # was silently passed over. Cboe's own reference data commonly
            # appends a generic legal-form label that does not always
            # match how the true target entity is actually registered at
            # GLEIF -- unlike Tier 1 (which carries the same irreducible
            # risk as every other name-based match already accepted
            # throughout this project's whole Cboe Europe effort), this
            # heuristic adds a NEW layer of inference this project has
            # never relied on before, and it has now been shown to pick
            # the wrong entity in a real, verifiable case. Never labeled
            # "resolved": kept as a distinct, lower-confidence status that
            # surfaces the real candidate for a human to confirm, rather
            # than silently promoting a plausible guess into identity.
            ent = entity_of(form_matches[0])
            return {
                "status": "narrowed_unconfirmed", "reason": "tier2_legal_form_suffix_matches_source_name_not_independently_verified", "match_tier": "tier2_legal_form_match",
                "lei": form_matches[0].get("id", ""), "legal_name": (ent.get("legalName") or {}).get("name", ""), "country": country_of(form_matches[0]),
                "candidate_count_after_fix": len(exact), "candidate_countries": countries,
            }
    return {"status": "ambiguous", "reason": "multiple_active_candidates_survive_both_tiers", "match_tier": "", "lei": "", "legal_name": "", "country": "", "candidate_count_after_fix": len(exact), "candidate_countries": countries}


def build(matrix_path: Path, output_dir: Path, execute: bool, limit: int | None = None) -> dict[str, Any]:
    bb = load_bb_module()
    ambiguous_rows = read_ambiguous(matrix_path)
    output_path = output_dir / "europe_cboe_ambiguous_disambiguation_v2_38bq.csv"
    existing = read_existing(output_path)

    by_key: dict[str, list[dict[str, str]]] = {}
    for row in ambiguous_rows:
        key = fixed_key(bb, row["company_name"])
        by_key.setdefault(key, []).append(row)

    already_done_keys = {fixed_key(bb, r["company_name"]) for r in existing.values()}
    remaining_keys = [k for k in by_key if k not in already_done_keys]

    if not execute:
        return {"phase": PHASE, "status": "DRY_RUN", "total_ambiguous_rows": len(ambiguous_rows), "unique_keys": len(by_key), "already_processed_keys": len(already_done_keys), "remaining_keys": len(remaining_keys), "network_used": False, "phase9c_authorized": False}

    selected_keys = remaining_keys[:limit] if limit else remaining_keys
    new_rows: list[dict[str, Any]] = []
    for key in selected_keys:
        rows_for_key = by_key[key]
        sample_name = rows_for_key[0]["company_name"]
        try:
            result = resolve_key(bb, sample_name, key)
        except urllib.error.HTTPError as exc:
            result = {"status": "unresolved", "reason": f"gleif_http_error_{exc.code}", "match_tier": "", "lei": "", "legal_name": "", "country": "", "candidate_count_after_fix": 0, "candidate_countries": ""}
        for row in rows_for_key:
            new_rows.append({
                "asset_id": row["asset_id"], "ticker": row["ticker"], "company_name": row["company_name"], "search_key": key,
                "phase": PHASE, "created_at_utc": now_iso(), **result,
            })
        time.sleep(GLEIF_MIN_SECONDS_BETWEEN_CALLS)

    all_rows = {**existing}
    for row in new_rows:
        all_rows[row["asset_id"]] = row
    final_rows = sorted(all_rows.values(), key=lambda r: r["asset_id"])
    write_csv(output_path, final_rows, MATRIX_FIELDS)

    status_counts = Counter(r["status"] for r in final_rows)
    tier_counts = Counter(r["match_tier"] for r in final_rows if r["match_tier"])
    report = {
        "phase": PHASE,
        "status": "COMPLETED_EUROPE_CBOE_AMBIGUOUS_DISAMBIGUATION" if len(all_rows) == len(ambiguous_rows) else "PARTIAL_EUROPE_CBOE_AMBIGUOUS_DISAMBIGUATION_RESUMABLE",
        "total_ambiguous_rows": len(ambiguous_rows),
        "unique_keys": len(by_key),
        "processed_this_run": len(selected_keys),
        "rows_written": len(final_rows),
        "complete": len(final_rows) == len(ambiguous_rows),
        "status_counts": dict(status_counts),
        "match_tier_counts": dict(tier_counts),
        "note": "Only status=resolved (tier1_single_issued) feeds v2.38AL's identity-resolved population. status=narrowed_unconfirmed (tier2_legal_form_match) is real, useful narrowing but NOT identity resolution -- a real, confirmed case (Danone SA) showed this specific heuristic can pick the wrong entity when the true target's own GLEIF registration carries no legal-form suffix at all. Surfaced for manual review, never auto-promoted.",
        "network_used": True, "scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False, "phase9c_authorized": False,
    }
    write_text(output_dir / "europe_cboe_ambiguous_disambiguation_report_v2_38bq.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-input", type=Path, default=BC_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and not 1 <= args.limit <= MAX_LIMIT:
        print(json.dumps({"status": "BLOCKED", "reason": "batch_limit_must_be_1_to_600"}))
        return 2
    report = build(args.matrix_input, args.output_dir, args.execute, args.limit)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
