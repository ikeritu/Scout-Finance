#!/usr/bin/env python3
"""Offline QA for v2.38BQ -- the two-tier, fail-closed disambiguation of
v2.38BC's 530 ambiguous Cboe Europe candidates. No real network: GLEIF
responses are injected via a fake http_get_json patched onto the loaded
v2.38BB module. Every LEI/company name below is synthetic."""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_cboe_ambiguous_disambiguation_v2_38bq.py"
BB_SCRIPT = ROOT / "scripts/resolve_europe_cboe_secondary_identity_pilot_v2_38bb.py"

MATRIX_FIELDS = ["asset_id", "ticker", "company_name", "search_key", "status", "reason", "lei", "legal_name", "country", "candidate_count", "candidate_countries", "query_strategy", "phase", "created_at_utc"]


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gleif_record(lei: str, legal_name: str, country: str, reg_status: str) -> dict:
    return {"id": lei, "attributes": {"entity": {"legalName": {"name": legal_name}, "legalAddress": {"country": country}}, "registration": {"status": reg_status}}}


def ambiguous_row(asset_id: str, ticker: str, name: str) -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": name, "search_key": "", "status": "ambiguous", "reason": "multiple_distinct_countries_match_same_name", "lei": "", "legal_name": "", "country": "", "candidate_count": "2", "candidate_countries": "", "query_strategy": "", "phase": "", "created_at_utc": ""}


def write_matrix(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATRIX_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_with(tmp: Path, ambiguous_rows: list[dict], gleif_records_by_query: dict[str, list[dict]]):
    """gleif_records_by_query maps the exact query string (first raw word,
    or first two if the module falls back) to the fake raw GLEIF records
    that query would return -- mirrors the real gleif_query() contract."""
    mod = module(SCRIPT, f"bq_{id(ambiguous_rows)}")
    bb = mod.load_bb_module()

    def fake_http_get_json(url: str):
        for query, records in gleif_records_by_query.items():
            if f"filter%5Bentity.legalName%5D={query}" in url or query in url:
                return 200, {"data": records}
        return 200, {"data": []}

    bb.http_get_json = fake_http_get_json

    matrix_path = tmp / "bc_matrix.csv"
    write_matrix(matrix_path, ambiguous_rows)
    report = mod.build(matrix_path, tmp / "out", execute=True)
    out_rows = {r["asset_id"]: r for r in csv.DictReader((tmp / "out" / "europe_cboe_ambiguous_disambiguation_v2_38bq.csv").open(encoding="utf-8"))}
    return report, out_rows


def test_single_issued_candidate_resolves_tier1():
    """Real case: Volkswagen AG had a retired French fund and a real
    duplicate German registration alongside its one genuinely ISSUED
    German entity -- must resolve to the single ISSUED one."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [ambiguous_row("U1", "1VOW3m", "Volkswagen AG")],
            {"Volkswagen": [
                gleif_record("LEI1", "VOLKSWAGEN", "FR", "RETIRED"),
                gleif_record("LEI2", "VOLKSWAGEN AKTIENGESELLSCHAFT", "DE", "DUPLICATE"),
                gleif_record("LEI3", "VOLKSWAGEN AKTIENGESELLSCHAFT", "DE", "ISSUED"),
            ]},
        )
    row = rows["U1"]
    assert row["status"] == "resolved"
    assert row["match_tier"] == "tier1_single_issued"
    assert row["lei"] == "LEI3"
    assert row["country"] == "DE"


def test_multiple_issued_with_one_legal_form_match_is_narrowed_not_resolved():
    """Real case: AbbVie Inc had many real ISSUED national subsidiaries,
    and only the US one shares the source's own "Inc" legal form -- a
    real, useful narrowing, but deliberately NOT promoted to "resolved"
    (see the Danone counter-example test below for why)."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [ambiguous_row("U1", "4ABd", "AbbVie Inc")],
            {"AbbVie": [
                gleif_record("LEI1", "ABBVIE", "BE", "ISSUED"),
                gleif_record("LEI2", "ABBVIE GMBH", "AT", "ISSUED"),
                gleif_record("LEI3", "ABBVIE INC", "US", "ISSUED"),
            ]},
        )
    row = rows["U1"]
    assert row["status"] == "narrowed_unconfirmed"
    assert row["match_tier"] == "tier2_legal_form_match"
    assert row["lei"] == "LEI3"
    assert row["country"] == "US"


def test_dotted_italian_legal_form_is_collapsed_before_matching():
    """Real bug found and fixed for this block: GLEIF spells the Italian
    legal form "S.P.A." (dot-separated single letters); the Cboe source
    spells it "SpA". Both must normalize to the same key, and the
    trailing-form comparison must also collapse the dots so tier 2 can
    correctly prefer the real Italian entity over unrelated same-named
    French ones. Even though this specific real case resolves correctly,
    it still lands in narrowed_unconfirmed, not resolved -- tier 2 never
    knows in advance whether it got the right answer (see the Danone
    test below for a real case where the same heuristic is wrong)."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [ambiguous_row("U1", "ACEm", "ACEA SpA")],
            {"ACEA": [
                gleif_record("LEI1", "ACEA", "FR", "ISSUED"),
                gleif_record("LEI2", "ACEA", "FR", "LAPSED"),
                gleif_record("LEI3", "ACEA S.P.A.", "IT", "ISSUED"),
            ]},
        )
    row = rows["U1"]
    assert row["status"] == "narrowed_unconfirmed"
    assert row["match_tier"] == "tier2_legal_form_match"
    assert row["lei"] == "LEI3"
    assert row["country"] == "IT"


def test_legal_form_match_can_pick_the_wrong_entity_real_danone_case():
    """Real, confirmed failure mode found while validating this block
    against live GLEIF data (not hypothetical): "Danone SA" narrowed via
    the legal-form heuristic to a real, active Spanish subsidiary whose
    own name happens to carry the same "SA" suffix as the Cboe source
    name -- but the real French parent is registered at GLEIF simply as
    "DANONE", with no suffix at all, so it never matched and was
    silently passed over. This is exactly why tier 2 must never be
    labeled "resolved": the mechanism cannot tell this case apart from
    a correct one at decision time."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [ambiguous_row("U1", "1BNd", "Danone SA")],
            {"Danone": [
                gleif_record("LEI1", "DANONE", "FR", "ISSUED"),       # the real parent -- no suffix, never matches "SA"
                gleif_record("LEI2", "DANONE SA", "ES", "ISSUED"),    # a real subsidiary whose name happens to carry "SA"
            ]},
        )
    row = rows["U1"]
    assert row["status"] == "narrowed_unconfirmed"  # never "resolved" -- this is the wrong entity, and the mechanism cannot know that
    assert row["country"] == "ES"


def test_multiple_issued_no_legal_form_match_stays_ambiguous():
    """Real case: RTX Corp had three real ISSUED entities (LU, US, DK),
    none distinguishable by legal form alone -- must stay honestly
    ambiguous, never a coin-flip guess."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [ambiguous_row("U1", "5URd", "RTX Corp")],
            {"RTX": [
                gleif_record("LEI1", "RTX", "LU", "ISSUED"),
                gleif_record("LEI2", "RTX CORPORATION", "US", "ISSUED"),
                gleif_record("LEI3", "RTX A/S", "DK", "ISSUED"),
            ]},
        )
    row = rows["U1"]
    assert row["status"] == "ambiguous"
    assert row["reason"] == "multiple_active_candidates_survive_both_tiers"
    assert row["lei"] == ""


def test_no_exact_match_after_fix_stays_unresolved_never_guessed():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            [ambiguous_row("U1", "1XYZm", "Totally Unmatched Co")],
            {"Totally": []},
        )
    row = rows["U1"]
    assert row["status"] == "unresolved"
    assert row["reason"] == "no_exact_normalized_name_match_after_fix"


def test_resumable_skips_already_processed_keys():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix_path = root / "bc_matrix.csv"
        write_matrix(matrix_path, [ambiguous_row("U1", "1VOW3m", "Volkswagen AG")])
        mod = module(SCRIPT, "bq_resume")
        bb = mod.load_bb_module()
        calls = []

        def counting_http_get_json(url: str):
            calls.append(url)
            return 200, {"data": [gleif_record("LEI3", "VOLKSWAGEN AKTIENGESELLSCHAFT", "DE", "ISSUED")]}

        bb.http_get_json = counting_http_get_json
        mod.build(matrix_path, root / "out", execute=True)
        calls_after_first_run = len(calls)
        mod.build(matrix_path, root / "out", execute=True)  # second run, same input
    assert len(calls) == calls_after_first_run  # no new network call for the already-resolved key


def test_dry_run_makes_no_network_call():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix_path = root / "bc_matrix.csv"
        write_matrix(matrix_path, [ambiguous_row("U1", "1VOW3m", "Volkswagen AG")])
        mod = module(SCRIPT, "bq_dryrun")
        report = mod.build(matrix_path, root / "out", execute=False)
    assert report["status"] == "DRY_RUN"
    assert report["network_used"] is False
    assert not (root / "out" / "europe_cboe_ambiguous_disambiguation_v2_38bq.csv").exists()


def test_missing_matrix_input_raises_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        mod = module(SCRIPT, "bq_missing")
        root = Path(tmp)
        raised = False
        try:
            mod.build(root / "does_not_exist.csv", root / "out", execute=True)
        except SystemExit:
            raised = True
    assert raised


CASES = [
    test_single_issued_candidate_resolves_tier1,
    test_multiple_issued_with_one_legal_form_match_is_narrowed_not_resolved,
    test_dotted_italian_legal_form_is_collapsed_before_matching,
    test_legal_form_match_can_pick_the_wrong_entity_real_danone_case,
    test_multiple_issued_no_legal_form_match_stays_ambiguous,
    test_no_exact_match_after_fix_stays_unresolved_never_guessed,
    test_resumable_skips_already_processed_keys,
    test_dry_run_makes_no_network_call,
    test_missing_matrix_input_raises_blocked,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BQ-europe-cboe-ambiguous-disambiguation/two-tier/fail-closed/dotted-legal-form-fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
