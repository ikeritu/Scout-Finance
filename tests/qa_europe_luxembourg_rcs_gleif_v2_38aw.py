#!/usr/bin/env python3
"""Offline QA for the v2.38AW Luxembourg RCS resolver. No real network
calls -- monkeypatches the module's own HTTP function with fixture
responses shaped exactly like real GLEIF payloads (captured live and
described in the script's own docstring), never the real endpoint.
"""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_luxembourg_rcs_gleif_v2_38aw.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_luxembourg_rcs_gleif_v2_38aw", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gleif_entity(name: str, rcs: str, status: str = "ACTIVE") -> dict:
    return {"id": f"LEI-{rcs}", "attributes": {"entity": {"legalName": {"name": name}, "registeredAs": rcs, "status": status}}}


def write_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "isin", "real_home_country_guess", "resolution_status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def lux_row(asset_id: str, ticker: str, name: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "resolved_company_name": name, "isin": "LU0000000000", "real_home_country_guess": "Luxembourg", "resolution_status": "resolved"}


def test_exact_single_word_name_resolves():
    """Real case: ArcelorMittal -- the parent entity has no legal-form
    suffix in GLEIF, only its many subsidiaries do."""
    mod = module()

    def fake_http_get_json(url):
        assert "arcelormittal" in url.lower()
        return 200, {"data": [
            gleif_entity("ArcelorMittal", "B82454"),
            gleif_entity("ArcelorMittal Sourcing", "B59577"),
            gleif_entity("ArcelorMittal Luxembourg", "B6990"),
        ], "meta": {"pagination": {"lastPage": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [lux_row("U1", "ARRD", "ARCELORMITTAL S.A. NOUV.")])
        report = mod.build(matrix, root / "out", execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["rcs_number"] == "B82454"


def test_truncated_last_word_matches_via_prefix():
    """Real case: Xetra truncates "Properties" to "PROPERT." -- the
    truncation marker (trailing ".") makes this a prefix match, never a
    guess at the full word."""
    mod = module()

    def fake_http_get_json(url):
        return 200, {"data": [gleif_entity("Grand City Properties S.A.", "B165560")], "meta": {"pagination": {"lastPage": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [lux_row("U1", "GYC", "GRAND CITY PROPERT.")])
        report = mod.build(matrix, root / "out", execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["rcs_number"] == "B165560"


def test_known_abbreviation_expands_for_non_last_token():
    """Real case: Millicom International Cellular -- "INTL" has no
    truncation dot (the whole word is contracted, not cut off), so it is
    matched via the small, dictionary-standard abbreviation table, never a
    fuzzy guess."""
    mod = module()

    def fake_http_get_json(url):
        return 200, {"data": [gleif_entity("Millicom International Cellular S.A.", "B40630")], "meta": {"pagination": {"lastPage": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [lux_row("U1", "M4M1", "MILLICOM INTL CELL.")])
        report = mod.build(matrix, root / "out", execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["rcs_number"] == "B40630"


def test_dropped_whole_word_stays_unresolved_never_guessed():
    """Real case: Corestate Capital -- the real entity is "Corestate
    Capital Holding S.A." (Xetra dropped "Holding" entirely, with no
    truncation marker to justify inserting it). Token-count mismatch with
    no marker must stay unresolved, not fuzzy-matched."""
    mod = module()

    def fake_http_get_json(url):
        return 200, {"data": [gleif_entity("Corestate Capital Holding S.A.", "B199780")], "meta": {"pagination": {"lastPage": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [lux_row("U1", "CCAP", "CORESTATE CAPITAL")])
        report = mod.build(matrix, root / "out", execute=True)
    assert report["resolved"] == 0
    assert report["unresolved_reasons"] == {"no_exact_normalized_name_match_in_luxembourg": 1}


def test_no_gleif_record_at_all_stays_unresolved():
    mod = module()

    def fake_http_get_json(url):
        return 200, {"data": [], "meta": {"pagination": {"lastPage": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [lux_row("U1", "LRND", "LEARND SE")])
        report = mod.build(matrix, root / "out", execute=True)
    assert report["resolved"] == 0
    assert report["unresolved_reasons"] == {"no_exact_normalized_name_match_in_luxembourg": 1}


def test_dotless_sa_legal_form_recognized():
    """Real case: "Aroundtown SA" (no periods) vs the more common
    "S.A." spelling elsewhere in the same registry -- both must strip
    cleanly so the bare-name search key matches."""
    mod = module()

    def fake_http_get_json(url):
        return 200, {"data": [
            gleif_entity("Aroundtown SA", "B217868"),
            gleif_entity("Aroundtown Finance Sarl", "B284284"),
        ], "meta": {"pagination": {"lastPage": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [lux_row("U1", "AT1", "AROUNDTOWN")])
        report = mod.build(matrix, root / "out", execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_luxembourg_rcs_gleif_matrix_v2_38aw.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["rcs_number"] == "B217868"


def test_non_luxembourg_rows_are_never_queried():
    mod = module()
    calls = []

    def fake_http_get_json(url):
        calls.append(url)
        return 200, {"data": [], "meta": {"pagination": {"lastPage": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        row = lux_row("U1", "SLYG", "SHELLY GROUP PLC")
        row["real_home_country_guess"] = "Bulgaria"
        write_matrix(matrix, [row])
        report = mod.build(matrix, root / "out", execute=True)
    assert report["input_assets"] == 0
    assert calls == []


CASES = [
    test_exact_single_word_name_resolves,
    test_truncated_last_word_matches_via_prefix,
    test_known_abbreviation_expands_for_non_last_token,
    test_dropped_whole_word_stays_unresolved_never_guessed,
    test_no_gleif_record_at_all_stays_unresolved,
    test_dotless_sa_legal_form_recognized,
    test_non_luxembourg_rows_are_never_queried,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AW-europe-luxembourg-rcs-gleif/exact-match/truncation/abbreviation/dropped-word/no-record/dotless-sa/country-filter/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
