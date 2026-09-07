#!/usr/bin/env python3
"""Offline QA for v2.38BC -- scaling the v2.38BB Cboe Europe identity
method to the full candidate population. No real network calls --
monkeypatches the pilot module's http_get_json after loading it.
"""
from __future__ import annotations

import csv
import importlib.util
import lzma
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_cboe_secondary_identity_full_v2_38bc.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_cboe_secondary_identity_full_v2_38bc", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gleif_entity(name: str, country: str) -> dict:
    return {"id": f"LEI-{name}-{country}", "attributes": {"entity": {"legalName": {"name": name}, "legalAddress": {"country": country}}}}


def write_home_exchange_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "company_name", "resolution_status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def cboe_row(asset_id: str, ticker: str, name: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": name, "resolution_status": "CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED"}


def write_empty_eu_identity_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["resolution_status", "resolved_company_name"], lineterminator="\n")
        writer.writeheader()


def write_empty_census_xz(path: Path) -> None:
    with lzma.open(path, "wt", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["asset_id", "company_name", "country"], lineterminator="\n")
        writer.writeheader()


def setup_inputs(root: Path, rows: list[dict[str, str]]) -> tuple[Path, Path, Path]:
    home = root / "home.csv"
    write_home_exchange_csv(home, rows)
    eu = root / "eu.csv"
    write_empty_eu_identity_csv(eu)
    census = root / "census.csv.xz"
    write_empty_census_xz(census)
    return home, eu, census


def test_dry_run_never_touches_network():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home, eu, census = setup_inputs(root, [cboe_row("U1", "AAA", "Real Company Inc")])
        report = mod.build(home, eu, census, root / "matrix.csv", root / "out", execute=False, flush_every=1)
    assert report["status"] == "DRY_RUN"
    assert report["total_candidates"] == 1


def test_full_run_resolves_and_writes_matrix():
    mod = module()
    pilot = mod.load_pilot_module()

    def fake_http_get_json(url):
        return 200, {"data": [gleif_entity("Real Company, Inc.", "US")], "meta": {"pagination": {"total": 1}}}

    pilot.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home, eu, census = setup_inputs(root, [cboe_row("U1", "AAA", "Real Company Inc")])
        matrix_path = root / "matrix.csv"
        report = mod.build(home, eu, census, matrix_path, root / "out", execute=True, flush_every=1)
        rows = list(csv.DictReader(matrix_path.open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert report["complete"] is True
    assert rows[0]["country"] == "US"


def test_resumable_skips_asset_ids_already_in_matrix_never_requeries():
    """The whole point of scaling to thousands of real candidates: a run
    interrupted partway through must never re-query (and never lose) a
    company already resolved in a prior session."""
    mod = module()
    pilot = mod.load_pilot_module()
    call_count = {"n": 0}

    def fake_http_get_json(url):
        call_count["n"] += 1
        return 200, {"data": [gleif_entity("Second Company, Inc.", "GB")], "meta": {"pagination": {"total": 1}}}

    pilot.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home, eu, census = setup_inputs(root, [
            cboe_row("U1", "AAA", "First Company Inc"),
            cboe_row("U2", "BBB", "Second Company Inc"),
        ])
        matrix_path = root / "matrix.csv"
        # Pre-seed the matrix as if U1 was already resolved in a prior run.
        with matrix_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=mod.MATRIX_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerow({"asset_id": "U1", "ticker": "AAA", "company_name": "First Company Inc", "search_key": "FIRST COMPANY", "status": "resolved", "reason": "exact_single_gleif_match_no_country_filter", "lei": "LEI-PRIOR", "legal_name": "First Company, Inc.", "country": "US", "candidate_count": 1, "candidate_countries": "US", "query_strategy": "first_word", "phase": "v2.38BC-europe-cboe-secondary-identity-full", "created_at_utc": "2026-01-01T00:00:00Z"})
        report = mod.build(home, eu, census, matrix_path, root / "out", execute=True, flush_every=1)
        rows = list(csv.DictReader(matrix_path.open(encoding="utf-8")))
    assert call_count["n"] == 1  # only U2 queried, U1 skipped
    assert report["processed_this_session"] == 1
    assert report["processed_total"] == 2
    by_asset = {r["asset_id"]: r for r in rows}
    assert by_asset["U1"]["lei"] == "LEI-PRIOR"  # untouched, never re-queried or overwritten
    assert by_asset["U2"]["country"] == "GB"


def test_duplicate_normalized_names_only_queried_once():
    mod = module()
    pilot = mod.load_pilot_module()
    call_count = {"n": 0}

    def fake_http_get_json(url):
        call_count["n"] += 1
        return 200, {"data": [gleif_entity("Duplicate Name, Inc.", "US")], "meta": {"pagination": {"total": 1}}}

    pilot.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home, eu, census = setup_inputs(root, [
            cboe_row("U1", "AAA", "Duplicate Name Inc"),
            cboe_row("U2", "BBB", "Duplicate Name Inc"),
        ])
        report = mod.build(home, eu, census, root / "matrix.csv", root / "out", execute=True, flush_every=1)
    assert report["total_candidates"] == 1
    assert call_count["n"] == 1


CASES = [
    test_dry_run_never_touches_network,
    test_full_run_resolves_and_writes_matrix,
    test_resumable_skips_asset_ids_already_in_matrix_never_requeries,
    test_duplicate_normalized_names_only_queried_once,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BC-europe-cboe-secondary-identity-full/dry-run/full-run/resumable-skip/dedup-once/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
