#!/usr/bin/env python3
"""Offline QA for the v2.38BB Cboe Europe secondary-listing identity
pilot. No real network calls -- monkeypatches the module's own HTTP
function with fixture GLEIF-shaped responses.
"""
from __future__ import annotations

import csv
import importlib.util
import lzma
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_cboe_secondary_identity_pilot_v2_38bb.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_cboe_secondary_identity_pilot_v2_38bb", SCRIPT)
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
    fields = ["resolution_status", "resolved_company_name"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()


def write_empty_census_xz(path: Path) -> None:
    fields = ["asset_id", "company_name", "country"]
    with lzma.open(path, "wt", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()


def test_normalize_key_converges_regardless_of_trailing_period():
    """Real bug found live: GLEIF spells "Inc." with a trailing period,
    Cboe's data spells "Inc" without one -- both must normalize to the
    same key, or the two never match."""
    mod = module()
    assert mod.normalize_key("Uber Technologies Inc") == mod.normalize_key("UBER TECHNOLOGIES, INC.")
    assert mod.normalize_key("eBay Inc") == mod.normalize_key("EBAY INC.")


def test_public_limited_company_full_form_matches_plc_abbreviation():
    """Real case: GLEIF spells Croda's legal form fully as "Public Limited
    Company" while the Cboe source abbreviates it "PLC" -- both must
    converge to the same search key."""
    mod = module()
    assert mod.normalize_key("Croda International PLC") == mod.normalize_key("CRODA INTERNATIONAL PUBLIC LIMITED COMPANY")


def test_spelled_out_legal_forms_converge_with_their_abbreviations():
    """Real bug found live: the source often abbreviates a legal form
    ("Ltd", "Corp", "Co") while GLEIF spells it out in full ("Limited",
    "Corporation", "Company") -- the single biggest yield improvement
    found in this pilot (confirmed live with China Overseas Land &
    Investment Ltd/Limited and Canadian National Railway Co/Company)."""
    mod = module()
    assert mod.normalize_key("China Overseas Land & Investment Ltd") == mod.normalize_key("China Overseas Land & Investment Limited")
    assert mod.normalize_key("Canadian National Railway Co") == mod.normalize_key("Canadian National Railway Company")
    assert mod.normalize_key("Some Corp") == mod.normalize_key("Some Corporation")


def test_etf_named_rows_are_excluded_from_candidates():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [
            cboe_row("U1", "AAA", "WisdomTree Silver - EUR Daily Hedged"),
            cboe_row("U2", "BBB", "Real Company Name Inc"),
        ])
        eu = root / "eu.csv"
        write_empty_eu_identity_csv(eu)
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        candidates = mod.select_candidates(home, mod.load_known_names(eu, census))
    assert len(candidates) == 1
    assert candidates[0]["company_name"] == "Real Company Name Inc"


def test_already_known_eu_company_is_excluded_as_duplicate():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [cboe_row("U1", "ALV", "Allianz SE")])
        eu = root / "eu.csv"
        with eu.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["resolution_status", "resolved_company_name"], lineterminator="\n")
            writer.writeheader()
            writer.writerow({"resolution_status": "resolved", "resolved_company_name": "ALLIANZ SE"})
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        candidates = mod.select_candidates(home, mod.load_known_names(eu, census))
    assert candidates == []


def test_exact_single_match_resolves_with_real_country():
    mod = module()

    def fake_http_get_json(url):
        assert "uber" in url.lower()
        return 200, {"data": [gleif_entity("Uber Technologies, Inc.", "US")], "meta": {"pagination": {"total": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [cboe_row("U1", "0QFd", "Uber Technologies Inc")])
        eu = root / "eu.csv"
        write_empty_eu_identity_csv(eu)
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        report = mod.build(home, eu, census, root / "out", sample_size=1, seed=1, execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_cboe_secondary_identity_pilot_matrix_v2_38bb.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["country"] == "US"


def test_raw_first_word_query_preserves_internal_punctuation():
    """Real bug found live: GLEIF's own legalName filter does a literal
    prefix match including punctuation -- querying "WW" (periods
    stripped by our normalization) finds nothing, but "W.W." (the real
    spelling, periods intact) finds "W.W. GRAINGER, INC." immediately.
    The query sent to GLEIF must use the original spelling, never the
    punctuation-stripped comparison key."""
    mod = module()
    seen_queries = []

    def fake_http_get_json(url):
        seen_queries.append(url)
        if "W.W." in url or "W%2EW%2E" in url:
            return 200, {"data": [gleif_entity("W.W. Grainger, Inc.", "US")], "meta": {"pagination": {"total": 1}}}
        return 200, {"data": [], "meta": {"pagination": {"total": 0}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [cboe_row("U1", "GWW", "W.W. Grainger Inc")])
        eu = root / "eu.csv"
        write_empty_eu_identity_csv(eu)
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        report = mod.build(home, eu, census, root / "out", sample_size=1, seed=1, execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_cboe_secondary_identity_pilot_matrix_v2_38bb.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["query_strategy"] == "first_word"


def test_two_word_fallback_finds_match_first_word_alone_misses():
    """Real case: "Check Point Software Technologies Ltd" -- querying
    just "Check" alone (too generic) never surfaces it among unrelated
    "Check ..." companies, but "Check Point" (first two words) does. The
    two-word fallback must only fire when the one-word query found no
    exact match, and never overwrite a match the one-word query already
    found."""
    mod = module()

    def fake_http_get_json(url):
        if "Check%20Point" in url or "Check+Point" in url:
            return 200, {"data": [gleif_entity("Check Point Software Technologies, Inc.", "US")], "meta": {"pagination": {"total": 1}}}
        return 200, {"data": [gleif_entity("Check Something Unrelated Ltd", "GB")], "meta": {"pagination": {"total": 1}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [cboe_row("U1", "CHKP", "Check Point Software Technologies Ltd")])
        eu = root / "eu.csv"
        write_empty_eu_identity_csv(eu)
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        report = mod.build(home, eu, census, root / "out", sample_size=1, seed=1, execute=True)
        rows = list(csv.DictReader((root / "out" / "europe_cboe_secondary_identity_pilot_matrix_v2_38bb.csv").open(encoding="utf-8")))
    assert report["resolved"] == 1
    assert rows[0]["country"] == "US"
    assert rows[0]["query_strategy"] == "first_two_words"


def test_multiple_distinct_countries_stays_ambiguous_never_guessed():
    mod = module()

    def fake_http_get_json(url):
        return 200, {"data": [gleif_entity("Protector Forsikring ASA", "NO"), gleif_entity("Protector Forsikring ASA", "SE")], "meta": {"pagination": {"total": 2}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [cboe_row("U1", "PROT", "Protector Forsikring ASA")])
        eu = root / "eu.csv"
        write_empty_eu_identity_csv(eu)
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        report = mod.build(home, eu, census, root / "out", sample_size=1, seed=1, execute=True)
    assert report["ambiguous"] == 1
    assert report["resolved"] == 0


def test_no_gleif_match_stays_unresolved():
    mod = module()

    def fake_http_get_json(url):
        return 200, {"data": [], "meta": {"pagination": {"total": 0}}}

    mod.http_get_json = fake_http_get_json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [cboe_row("U1", "XYZ", "Some Obscure Company Ltd")])
        eu = root / "eu.csv"
        write_empty_eu_identity_csv(eu)
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        report = mod.build(home, eu, census, root / "out", sample_size=1, seed=1, execute=True)
    assert report["unresolved"] == 1


def test_dry_run_never_touches_network():
    mod = module()
    calls = []
    mod.http_get_json = lambda url: calls.append(url) or (0, None)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        home = root / "home.csv"
        write_home_exchange_csv(home, [cboe_row("U1", "AAA", "Real Company Inc")])
        eu = root / "eu.csv"
        write_empty_eu_identity_csv(eu)
        census = root / "census.csv.xz"
        write_empty_census_xz(census)
        report = mod.build(home, eu, census, root / "out", sample_size=1, seed=1, execute=False)
    assert report["status"] == "DRY_RUN"
    assert calls == []


CASES = [
    test_normalize_key_converges_regardless_of_trailing_period,
    test_public_limited_company_full_form_matches_plc_abbreviation,
    test_spelled_out_legal_forms_converge_with_their_abbreviations,
    test_etf_named_rows_are_excluded_from_candidates,
    test_already_known_eu_company_is_excluded_as_duplicate,
    test_exact_single_match_resolves_with_real_country,
    test_raw_first_word_query_preserves_internal_punctuation,
    test_two_word_fallback_finds_match_first_word_alone_misses,
    test_multiple_distinct_countries_stays_ambiguous_never_guessed,
    test_no_gleif_match_stays_unresolved,
    test_dry_run_never_touches_network,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BB-europe-cboe-secondary-identity-pilot/period-bug-fix/plc-full-form/etf-filter/dedup/exact-match/ambiguous/unresolved/dry-run/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
