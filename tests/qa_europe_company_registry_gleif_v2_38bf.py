#!/usr/bin/env python3
"""Offline QA for v2.38BF -- the country-parameterized generalization of
v2.38AW's Luxembourg GLEIF resolver, now used for Austria and Finland. No
real network calls -- monkeypatches the underlying v2.38BB module's
http_get_json after loading it through this block's own load_bb_module().
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_company_registry_gleif_v2_38bf.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_company_registry_gleif_v2_38bf", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gleif_entity(name: str, country: str, registered_as: str = "", status: str = "ACTIVE") -> dict:
    return {"id": f"LEI-{name}-{country}", "attributes": {"entity": {"legalName": {"name": name}, "legalAddress": {"country": country}, "registeredAs": registered_as, "status": status}}}


def write_bc_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "status", "country", "legal_name"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def bc_row(asset_id: str, ticker: str, country: str, legal_name: str, status: str = "resolved") -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "status": status, "country": country, "legal_name": legal_name}


def test_country_filter_only_selects_matching_rows():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [
            bc_row("U1", "A", "AT", "Some Austrian Company AG"),
            bc_row("U2", "B", "FI", "Some Finnish Company Oyj"),
        ])
        at_candidates = mod.select_candidates(bc, "AT", set(), None)
        fi_candidates = mod.select_candidates(bc, "FI", set(), None)
    assert len(at_candidates) == 1 and at_candidates[0]["ticker"] == "A"
    assert len(fi_candidates) == 1 and fi_candidates[0]["ticker"] == "B"


def test_already_known_names_excluded():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "A", "AT", "Erste Group Bank AG")])
        candidates = mod.select_candidates(bc, "AT", {"ERSTE GROUP BANK AG"}, None)
    assert candidates == []


def test_exact_single_country_scoped_match_resolves():
    mod = module()
    bb_mod = mod.load_bb_module()

    def fake_http_get_json(url):
        assert "country" in url.lower() or "AT" in url
        return 200, {"data": [gleif_entity("Addiko Bank AG", "AT", "350921k")], "meta": {"pagination": {"total": 1}}}

    bb_mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "ADKOv", "AT", "Addiko Bank AG")])
        report = mod.build(bc, "AT", set(), root / "out", execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_company_registry_gleif_matrix_v2_38bf_at.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["national_registration_number"] == "350921k"


def test_two_word_fallback_reused_from_v2_38bb():
    mod = module()
    bb_mod = mod.load_bb_module()

    def fake_http_get_json(url):
        if "Raiffeisen%20Bank" in url or "Raiffeisen+Bank" in url:
            return 200, {"data": [gleif_entity("Raiffeisen Bank International AG", "AT", "122119m")], "meta": {"pagination": {"total": 1}}}
        return 200, {"data": [gleif_entity("Raiffeisen Unrelated Sparkasse", "AT", "999999z")], "meta": {"pagination": {"total": 1}}}

    bb_mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "RBIv", "AT", "Raiffeisen Bank International AG")])
        report = mod.build(bc, "AT", set(), root / "out", execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_company_registry_gleif_matrix_v2_38bf_at.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["national_registration_number"] == "122119m"
    assert rows[0]["query_strategy"] == "first_two_words"


def test_dry_run_never_touches_network():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bc = root / "bc.csv"
        write_bc_matrix(bc, [bc_row("U1", "A", "FI", "Some Finnish Company Oyj")])
        report = mod.build(bc, "FI", set(), root / "out", execute=False)
    assert report["status"] == "DRY_RUN"
    assert report["new_candidates"] == 1


CASES = [
    test_country_filter_only_selects_matching_rows,
    test_already_known_names_excluded,
    test_exact_single_country_scoped_match_resolves,
    test_two_word_fallback_reused_from_v2_38bb,
    test_dry_run_never_touches_network,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BF-europe-company-registry-gleif/country-filter/dedup/exact-match/two-word-fallback/dry-run/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
