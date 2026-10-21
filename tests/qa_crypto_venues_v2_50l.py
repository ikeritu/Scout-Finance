#!/usr/bin/env python3
"""QA for v2.50L (phase 8): where a coin can be traded, Kraken's public catalogue and the person's own Revolut list, as a filter and as information.
Pure checks (list parsing, name agreement, Kraken parsing and identity, safe failures), the search flow, and the real app through AppTest with a fake
CoinGecko, Binance, GoPlus, DefiLlama and Kraken that are always patched in. Checks that availability is only ever CONFIRMED (symbol + fresh price for Kraken,
symbol + name + a single candidate for Revolut), that a missing source is said and never read as "not available", that nothing adds points, and that the
app never writes the person's list or anything from Kraken to disk. No network, no real key."""
from __future__ import annotations

import json
import logging
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

import qa_crypto_search_v2_50f as base  # noqa: E402
from qa_crypto_search_v2_50f import (FRESH_PRICE_STATUS, KRAKEN_PAIRS, KRAKEN_TICKERS, Sandbox, button, cards, direct_client, forbid_network, open_crypto_page,  # noqa: E402
                                     page_text, require)
from src.crypto_v2_50 import REVOLUT_FILENAME  # noqa: E402
from src.crypto_v2_50 import venues as v  # noqa: E402
from src.crypto_v2_50.search import filter_results, run_search  # noqa: E402
from src.ui_v2_37 import crypto_screen as screen  # noqa: E402

PARTIAL_LIST = "pump;Pump Coin\nlowc;Low Coin\nq1;Quiet 1\ndil;Wrong Name\n"


def returning(payload, status=200):
    return lambda url, timeout: (status, {}, json.dumps(payload).encode())


# ------------------------------------------------------------------------------------------------------------------------ the person's list

def test_the_revolut_list_accepts_the_usual_formats_and_ignores_the_rest() -> None:
    text = ("Ticker\tCriptomoneda\tEstado de verificación\n1INCH\t1inch Network\tVerificado: activo\n"
            "# a comment\n\n  aave ; Aave \nsol,Solana\nBTC\nbad ticker here\nAAVE;Duplicate\nthis-is-not-a-ticker;X\nTOOLONGTICKERSYMBOL;Y\nÑANDÚ;Z\n")
    entries, skipped = v.parse_revolut_list(text)
    require([e["symbol"] for e in entries] == ["1INCH", "AAVE", "SOL", "BTC"], f"tab, semicolon, comma and bare ticker; header, comment, blank and duplicate ignored: {entries}")
    require(entries[0]["name"] == "1inch Network" and entries[1]["name"] == "Aave" and entries[2]["name"] == "Solana" and entries[3]["name"] is None, "names are kept as written, None when absent")
    require(skipped == 4, f"lines that are not a ticker are counted, not guessed: {skipped}")
    require(v.parse_revolut_list("") == ([], 0) and v.parse_revolut_list("# nothing\n\n") == ([], 0), "an empty list is empty")


def test_loading_the_list_reports_missing_empty_and_unreadable_files() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / REVOLUT_FILENAME
        require(v.load_revolut_list(path)["status"] == "missing", "no file")
        path.write_text("# nothing yet\n", encoding="utf-8")
        require(v.load_revolut_list(path)["status"] == "empty", "a file with no tickers")
        path.write_bytes(b"\xff\xfe\x00\x80 not utf-8 \xc3\x28")
        require(v.load_revolut_list(path)["status"] == "unreadable", "bytes that are not text")
        path.write_bytes("﻿AAVE;Aave\nXTZ;Tezos\n".encode("utf-8"))
        loaded = v.load_revolut_list(path)
        require(loaded["status"] == "ok" and [e["symbol"] for e in loaded["entries"]] == ["AAVE", "XTZ"], f"a BOM from a text editor is tolerated: {loaded}")
        require(path.read_bytes() == "﻿AAVE;Aave\nXTZ;Tezos\n".encode("utf-8"), "the file is only read, never written")


def test_a_symbol_is_confirmed_only_when_the_name_agrees_and_one_coin_qualifies() -> None:
    for revolut, coin, expected in (("Aave", "Aave", True), ("Kyber Network Crystal v2", "Kyber Network Crystal", True), ("Sky", "Sky Protocol", True),
                                    ("POL (ex-MATIC)", "POL (ex-MATIC)", True), ("Sky", "Skyrim", False), ("Gensyn", "AI Network", False), ("Protocol Sky", "Sky Protocol", False),
                                    ("", "Aave", False), ("Aave", None, False), ("1inch Network", "1INCH Network", True)):
        require(v.names_agree(revolut, coin) is expected, f"{revolut!r} vs {coin!r}: expected {expected}")
    rows = [{"coin_id": "gensyn", "symbol": "ai", "name": "Gensyn"}, {"coin_id": "other-ai", "symbol": "AI", "name": "Other AI"}, {"coin_id": "aave", "symbol": "aave", "name": "Aave"},
            {"coin_id": "aave-fork", "symbol": "AAVE", "name": "Aave"}, {"coin_id": "skyrim", "symbol": "sky", "name": "Skyrim"}, {"coin_id": "not-listed", "symbol": "zzz", "name": "Zzz"}]
    out = v.match_revolut(rows, [{"symbol": "AI", "name": "Gensyn"}, {"symbol": "AAVE", "name": "Aave"}, {"symbol": "SKY", "name": "Sky"}])
    require(out["gensyn"]["status"] == "confirmed" and out["other-ai"]["status"] == "unverified", "the name picks the coin among those sharing a symbol")
    require(out["aave"]["status"] == "unverified" and out["aave-fork"]["status"] == "unverified", "two coins that both qualify: neither is confirmed")
    require(out["skyrim"]["status"] == "unverified" and out["skyrim"]["name"] == "Sky" and "not-listed" not in out, "another name: unverified, and a coin that is not listed is absent")


# ------------------------------------------------------------------------------------------------------------------------------ Kraken

def test_the_kraken_catalogue_is_parsed_to_usd_and_eur_markets() -> None:
    calls = []

    def transport(url, timeout):
        calls.append(url)
        path = url[len(v.KRAKEN_URL):]
        return 200, {}, json.dumps({"error": [], "result": KRAKEN_PAIRS if path == "/AssetPairs" else KRAKEN_TICKERS}).encode()

    markets = v.fetch_kraken_markets(transport)
    require(len(calls) == 2, f"two calls: the catalogue and every ticker: {calls}")
    require(set(markets) == {"PUMP", "LOWC", "DIL", "BTC"}, f"online USD/EUR markets only, XBT renamed, no cancel-only, no crypto quote, no pair without a name: {sorted(markets)}")
    require(markets["PUMP"] == [{"pair": "PUMP/USD", "quote": "USD", "price_usd": 1.5}], str(markets["PUMP"]))
    require(abs(markets["LOWC"][0]["price_usd"] - 0.9 * 1.1) < 1e-9 and markets["LOWC"][0]["quote"] == "EUR", f"a EUR market is converted with Kraken's own EUR/USD: {markets['LOWC']}")
    pairs = {k: p for k, p in KRAKEN_PAIRS.items() if k != "ZEURZUSD"}
    markets = v.fetch_kraken_markets(lambda url, t: (200, {}, json.dumps({"error": [], "result": pairs if url.endswith("/AssetPairs") else KRAKEN_TICKERS}).encode()))
    require("LOWC" not in markets and "PUMP" in markets, "without EUR/USD the EUR markets are left out rather than guessed")
    tickers = KRAKEN_TICKERS | {"PUMPUSD": {"c": ["nan", "1"]}, "DILUSD": {}}
    markets = v.fetch_kraken_markets(lambda url, t: (200, {}, json.dumps({"error": [], "result": KRAKEN_PAIRS if url.endswith("/AssetPairs") else tickers}).encode()))
    require("PUMP" not in markets and "DIL" not in markets and "LOWC" in markets, "a market without a usable price is dropped")


def test_kraken_failures_are_safe_and_never_repeat_the_request() -> None:
    secret = "https://api.kraken.com/0/public/AssetPairs?token=SECRET"

    def boom(url, timeout):
        raise OSError(secret)

    for transport, expected in ((boom, "no respondió"), (lambda u, t: (500, {}, b"{}"), "HTTP 500"), (lambda u, t: (429, {}, b"{}"), "limitó"), (lambda u, t: (200, {}, b"<html>"), "no es JSON"),
                                (returning({"error": ["EGeneral:Invalid"], "result": {}}), "error"), (returning([1, 2]), "forma inesperada"), (returning({"result": []}), "forma inesperada")):
        try:
            v.fetch_kraken_markets(transport)
        except v.VenueError as error:
            require(expected in str(error) and "SECRET" not in str(error) and "http" not in str(error), f"a short safe reason: {error}")
        else:
            raise AssertionError(f"a bad Kraken answer was accepted ({expected})")


def test_a_kraken_market_is_linked_only_when_the_fresh_price_agrees() -> None:
    markets = {"PUMP": [{"pair": "PUMP/EUR", "quote": "EUR", "price_usd": 1.6}, {"pair": "PUMP/USD", "quote": "USD", "price_usd": 1.5}], "DIL": [{"pair": "DIL/USD", "quote": "USD", "price_usd": 300.0}]}
    link, conflict = v.match_kraken({"symbol": "pump"}, markets, price=1.5)
    require(link["pair"] == "PUMP/USD" and link["price_gap"] == 0 and conflict is False, f"the closest market: {link}")
    link, conflict = v.match_kraken({"symbol": "PUMP"}, markets, price=1.45)
    require(link["pair"] == "PUMP/USD", "within 10%")
    require(v.match_kraken({"symbol": "DIL"}, markets, price=1.5) == (None, True), "same symbol, another coin: a conflict, not a link")
    require(v.match_kraken({"symbol": "PUMP"}, markets, price=None) == (None, True) and v.match_kraken({"symbol": "PUMP"}, markets, price=0) == (None, True), "no fresh price: nothing is linked")
    require(v.match_kraken({"symbol": "NOPE"}, markets, price=1.0) == (None, False), "a symbol Kraken does not list")
    require(v.match_kraken({"symbol": "X"}, {"X": [{"pair": "X/USD", "quote": "USD", "price_usd": 1.1}]}, price=1.0)[0] is None, "10% apart is not agreement")


def test_the_venue_helpers_only_count_confirmed_facts() -> None:
    both = {"kraken": {"pair": "A/USD"}, "revolut": {"status": "confirmed", "name": "A"}}
    only_k = {"kraken": {"pair": "A/USD"}, "revolut": {"status": "unverified", "name": "A"}}
    only_r = {"kraken": None, "kraken_conflict": True, "revolut": {"status": "confirmed", "name": "A"}}
    for venues, label, flags in ((both, "Kraken + Revolut", (True, True)), (only_k, "Kraken", (True, False)), (only_r, "Revolut", (False, True)), ({}, None, (False, False)), (None, None, (False, False))):
        require(v.venue_label(venues) == label and v.available(venues) == flags, f"{venues}: {label} {flags}")
    expected = {"all": (True, True, True, True, True), "any": (True, True, True, False, False), "kraken": (True, True, False, False, False), "revolut": (True, False, True, False, False),
                "both": (True, False, False, False, False)}
    for mode, results in expected.items():
        require(tuple(v.venue_matches(x, mode) for x in (both, only_k, only_r, {}, None)) == results, f"{mode}: {results}")


# ---------------------------------------------------------------------------------------------------------------------------- the search

def test_the_search_links_kraken_by_fresh_price_and_revolut_by_name() -> None:
    with Sandbox(revolut_text=PARTIAL_LIST) as box:
        client, cache, _ = direct_client(box)
        result = run_search(client, cache, revolut_path=box.data_dir / REVOLUT_FILENAME)
        coins, s = {r["coin_id"]: r for r in result.scored}, result.summary
        require(coins["pump-coin"]["venues"]["kraken"]["pair"] == "PUMP/USD" and coins["pump-coin"]["venues"]["revolut"] == {"status": "confirmed", "name": "Pump Coin"}, str(coins["pump-coin"]["venues"]))
        low = coins["low-coin"]["venues"]
        require(low["kraken"]["pair"] == "LOWC/EUR" and abs(low["kraken"]["price_gap"] - 0.01) < 1e-9 and low["revolut"]["status"] == "confirmed", f"a EUR-only market, converted: {low}")
        dil = coins["dilute-coin"]["venues"]
        require(dil["kraken"] is None and dil["kraken_conflict"] is True and dil["revolut"] == {"status": "unverified", "name": "Wrong Name"}, f"another coin with the symbol, and another name: {dil}")
        require(coins["quiet-1"]["venues"]["kraken"] is None and coins["quiet-1"]["venues"]["revolut"]["status"] == "confirmed" and coins["sus-coin"]["venues"] == {"kraken": None, "kraken_conflict": False, "revolut": None}, "Revolut only; neither")
        require(s["kraken_status"] == "ok" and s["with_kraken"] == 2 and s["kraken_conflicts"] == 1 and s["revolut_status"] == "ok" and s["revolut_listed"] == 4, str(s))
        require(s["with_revolut"] == 3 and s["revolut_unverified"] == 1 and s["with_both"] == 2 and s["revolut_skipped"] == 0, str(s))
        simple = [c for c in box.fake.calls if "/simple/price" in c]
        require(len(simple) == 1 and len(box.kraken.calls) == 2, f"fresh prices are asked once for the Binance and Kraken symbols together: {len(simple)} / {len(box.kraken.calls)}")
        scores = {k: r["score"] for k, r in coins.items()}
    with Sandbox(kraken_fails=True, revolut_text=PARTIAL_LIST) as box:
        client, cache, _ = direct_client(box)
        result = run_search(client, cache, revolut_path=box.data_dir / REVOLUT_FILENAME)
        s = result.summary
        require(s["kraken_status"] == "unavailable" and s["with_kraken"] == 0 and all(r["venues"]["kraken"] is None and not r["venues"]["kraken_conflict"] for r in result.scored), "Kraken down: no link and no conflict is invented")
        require(s["with_revolut"] == 3 and {r["coin_id"]: r["score"] for r in result.scored} == scores, "Revolut still works and no score changes")
    with Sandbox(revolut_text=PARTIAL_LIST) as box:
        FRESH_PRICE_STATUS["code"] = 500
        client, cache, _ = direct_client(box)
        result = run_search(client, cache, revolut_path=box.data_dir / REVOLUT_FILENAME)
        s = result.summary
        require(s["kraken_status"] == "unverified" and s["perps_status"] == "unverified" and s["with_kraken"] == 0, f"no fresh prices: no link on a stale price: {s['kraken_status']}")
    with Sandbox(revolut_text=None) as box:
        client, cache, _ = direct_client(box)
        result = run_search(client, cache, revolut_path=box.data_dir / REVOLUT_FILENAME)
        require(result.summary["revolut_status"] == "missing" and result.summary["with_revolut"] == 0 and not (box.data_dir / REVOLUT_FILENAME).exists(), "no list: said, and the app does not create one")


def test_the_venue_filter_combines_with_the_other_filters() -> None:
    with Sandbox(revolut_text=PARTIAL_LIST) as box:
        client, cache, _ = direct_client(box)
        scored = run_search(client, cache, revolut_path=box.data_dir / REVOLUT_FILENAME).scored

        def ids(**kw):
            return sorted(r["coin_id"] for r in filter_results(scored, level="all", **kw))

        require(ids(venue="any") == ["low-coin", "pump-coin", "quiet-1"], f"any: {ids(venue='any')}")
        require(ids(venue="kraken") == ["low-coin", "pump-coin"] and ids(venue="revolut") == ["low-coin", "pump-coin", "quiet-1"] and ids(venue="both") == ["low-coin", "pump-coin"], "kraken / revolut / both")
        require(len(ids(venue="all")) == len(ids()) == 15 and "dilute-coin" not in ids(venue="any"), "off by default; an unverified coin is in no venue list")
        require(ids(venue="any", needle="pump") == ["pump-coin"] and ids(venue="both", protocol_only=True) == ["pump-coin"], "it combines with the text and the protocol filter")


# ------------------------------------------------------------------------------------------------------------------------------ the page

def searched(**box_kw):
    at = open_crypto_page()
    button(at, "crypto_search").click().run()
    require(not at.exception, f"the search crashed: {[e.value[:120] for e in at.exception]}")
    return at


def venue_box(at):
    return next(w for w in at.selectbox if w.key == "crypto_filter_venue")


def show_all(at):
    venue_box(at).set_value("Todas").run()
    require(not at.exception, f"the filter crashed: {[e.value[:120] for e in at.exception]}")
    return at


def open_coin(at, coin_id: str):
    button(at, f"crypto_fullpage_select_{screen.card_key(coin_id)}").click().run()
    require(not at.exception, f"the coin page crashed: {[e.value[:120] for e in at.exception]}")
    return at


def test_the_list_shows_only_what_can_be_traded_by_default_and_labels_each_card() -> None:
    with Sandbox(revolut_text=PARTIAL_LIST):
        at = searched()
        box = venue_box(at)
        require(box.options == ["Revolut o Kraken", "Kraken", "Revolut", "En las dos", "Todas"] and box.value == "Revolut o Kraken", f"the filter, on by default: {box.options}")
        text = page_text(at)
        require("Mostrando 1–3 de 3 monedas" in text, f"only the coins available in Kraken or Revolut: {[c[:60] for c in cards(at)]}")
        pump = next(c for c in cards(at) if "Pump Coin" in c)
        require("Operable en Kraken + Revolut" in pump, "the card says where")
        require("Operable en Revolut" in next(c for c in cards(at) if "Quiet 1" in c) and "Operable en Kraken + Revolut" in next(c for c in cards(at) if "Low Coin" in c), "Revolut only / both")
        require("Kraken (catálogo público): 2 monedas" in text and "Se descartaron 1 coincidencias de símbolo" in text, "the Kraken line, with the discarded symbol match")
        require("Revolut (tu lista de 4 símbolos): 3 monedas confirmadas por símbolo y nombre." in text and "1 comparten símbolo con otra moneda o tienen otro nombre: no verificadas, no cuentan." in text and "En las dos plataformas: 2." in text, "the Revolut line")
        require("De las 3 candidatas explosivas, 2 se pueden operar en Revolut o Kraken." in text, "the summary says how many candidates can be traded (the dilute one cannot be confirmed anywhere)")
        for label, count in (("Kraken", 2), ("Revolut", 3), ("En las dos", 2), ("Revolut o Kraken", 3)):
            venue_box(at).set_value(label).run()
            require(len(cards(at)) == count and f"Mostrando 1–{count} de {count} monedas" in page_text(at), f"{label}: {count} cards")
        show_all(at)
        require("Mostrando 1–9 de 13 monedas" in page_text(at) and not any("Dilute Coin" in c and "Operable" in c for c in cards(at)), "«Todas» removes the filter; an unverified coin is never labelled")


def test_the_filter_and_going_back_keep_the_choice() -> None:
    with Sandbox(revolut_text=PARTIAL_LIST):
        at = searched()
        venue_box(at).set_value("En las dos").run()
        require(len(cards(at)) == 2, "two coins in both")
        open_coin(at, "pump-coin")
        require(at.session_state["crypto_filter_venue"] == "En las dos", "kept while the coin's page is open")
        button(at, "crypto_fullpage_back").click().run()
        require(venue_box(at).value == "En las dos" and len(cards(at)) == 2, "and back at the list")
        at.session_state["screen"] = "home"
        at.run()


def test_the_coin_page_says_where_it_can_be_traded_and_what_could_not_be_confirmed() -> None:
    with Sandbox(revolut_text=PARTIAL_LIST):
        at = searched()
        show_all(at)
        text = page_text(open_coin(at, "pump-coin"))
        require("Dónde operar" in text and "**Kraken:** mercado PUMP/USD" in text and "identidad verificada" in text and "**Revolut:** en tu lista como «Pump Coin»" in text, "both, with the proof")
        require("confírmalo en la plataforma antes de operar" in text and "Solo información: no suma puntos" in text, "the caveat")
        for coin_id, kraken, revolut in (("dilute-coin", "mismo símbolo, pero su precio no encaja", "no se puede confirmar que sea esta moneda"), ("sus-coin", "sin mercado en USD ni EUR", "no está en tu lista"),
                                         ("quiet-1", "sin mercado en USD ni EUR", "en tu lista como «Quiet 1»")):
            at2 = searched()
            show_all(at2)
            t = page_text(open_coin(at2, coin_id))
            require(kraken in t and revolut in t, f"{coin_id}: {kraken} / {revolut}")
    with Sandbox(revolut_text=None, kraken_fails=True):
        at = searched()
        t = page_text(at)
        require("No se pudo consultar el catálogo de Kraken" in t and f"No hay lista de Revolut: crea el archivo `data/{REVOLUT_FILENAME}`" in t, "both gaps are said")
        require("El filtro «Dónde operar» solo usa las fuentes que han respondido" in t and "No hay monedas para estos filtros" in t and "Dónde operar: Todas" in t, "the filter says what it cannot know, and the empty list says how out")
        show_all(at)
        t = page_text(open_coin(at, "pump-coin"))
        require("**Kraken:** no se pudo comprobar en esta búsqueda" in t and "**Revolut:** sin lista de Revolut que consultar" in t, "a missing source is not 'not available'")


def test_availability_changes_no_score_and_nothing_reaches_the_disk() -> None:
    with Sandbox(revolut_text=PARTIAL_LIST) as box:
        at = searched()
        with_venues = {r["coin_id"]: r["score"] for r in at.session_state["crypto_results"]}
        files = {p.name: p.read_bytes() for p in box.data_dir.rglob("*") if p.is_file()}
        require(files[REVOLUT_FILENAME] == PARTIAL_LIST.encode("utf-8"), "the person's list is untouched")
        blob = b"".join(b for n, b in files.items() if n != REVOLUT_FILENAME)
        require(b"PUMP/USD" not in blob and b"XXBTZUSD" not in blob and b"LOWC/EUR" not in blob and all(n.endswith((".bin", ".json")) or n == REVOLUT_FILENAME for n in files), "nothing from Kraken is written to disk")
    with Sandbox(kraken_fails=True, revolut_text=None) as box2:
        at2 = searched()
        require({r["coin_id"]: r["score"] for r in at2.session_state["crypto_results"]} == with_venues, "the same scores with and without the venues")


def test_the_modules_are_quiet_keyless_and_never_write() -> None:
    source = (ROOT / "src" / "crypto_v2_50" / "venues.py").read_text(encoding="utf-8")
    require("print(" not in source and "logging" not in source and "write_text" not in source and "write_bytes" not in source and not re.search(r"(?<![a-z])open\(", source), "no printing, logging or writing")
    require("api_key" not in source.lower() and "authorization" not in source.lower() and "str(error)" not in source and "{error}" not in source, "no key, and transport error messages are never forwarded")
    require(f"data/{REVOLUT_FILENAME}" in (ROOT / ".gitignore").read_text(encoding="utf-8"), "the person's list is never committed")
    ui = (ROOT / "src" / "ui_v2_37" / "crypto_screen.py").read_text(encoding="utf-8")
    require(not re.search(r"font-size:(\d|1[01])px", ui), "no text under 12 px")
    require("Mantener" not in ui and "comprar ahora" not in ui.lower() and "te recomendamos" not in ui.lower(), "no advice wording")


CASES = [
    test_the_revolut_list_accepts_the_usual_formats_and_ignores_the_rest,
    test_loading_the_list_reports_missing_empty_and_unreadable_files,
    test_a_symbol_is_confirmed_only_when_the_name_agrees_and_one_coin_qualifies,
    test_the_kraken_catalogue_is_parsed_to_usd_and_eur_markets,
    test_kraken_failures_are_safe_and_never_repeat_the_request,
    test_a_kraken_market_is_linked_only_when_the_fresh_price_agrees,
    test_the_venue_helpers_only_count_confirmed_facts,
    test_the_search_links_kraken_by_fresh_price_and_revolut_by_name,
    test_the_venue_filter_combines_with_the_other_filters,
    test_the_list_shows_only_what_can_be_traded_by_default_and_labels_each_card,
    test_the_filter_and_going_back_keep_the_choice,
    test_the_coin_page_says_where_it_can_be_traded_and_what_could_not_be_confirmed,
    test_availability_changes_no_score_and_nothing_reaches_the_disk,
    test_the_modules_are_quiet_keyless_and_never_write,
]


def main() -> int:
    forbid_network()
    for case in CASES:
        case()
    print("v2.50L crypto venues QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
