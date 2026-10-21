#!/usr/bin/env python3
"""QA for v2.50K (phase 7): protocol quality data from DefiLlama (TVL, fees, revenue), as information only. Pure checks (parsing, identity mapping,
the one-hour memory cache, safe failures, ratios), the search flow, and the real app through AppTest with a fake CoinGecko, Binance, GoPlus and
DefiLlama that are always patched in. Checks that the coin <-> protocol link is exact (CoinGecko id), that "no data" is worded as neutral, that the
data adds no points, that a DefiLlama outage changes nothing, and that nothing is written to disk. No network, no real key."""
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

from qa_crypto_search_v2_50f import (FEES, PROTOCOLS, REVENUE, FakeDefiLlama, Sandbox, button, cards, direct_client, forbid_network, open_crypto_page,  # noqa: E402
                                     page_text, require)
from src.crypto_v2_50 import quality as q  # noqa: E402
from src.crypto_v2_50.search import filter_results, run_search  # noqa: E402
from src.ui_v2_37 import crypto_screen as screen  # noqa: E402


def transport_returning(payload, status=200):
    return lambda url, timeout: (status, {}, json.dumps(payload).encode())


# ------------------------------------------------------------------------------------------------------------------------------ parsing

def test_protocols_are_parsed_and_only_those_with_a_coingecko_id_are_kept() -> None:
    parsed = q.parse_protocols(PROTOCOLS + [{"id": 7, "name": " ", "slug": "x", "gecko_id": "  seven  ", "chains": ["A", 5, "B"], "tvl": "abc", "change_1d": float("nan")}])
    require(set(parsed) == {"101", "102", "7"}, f"junk, non-dict and protocols without a gecko_id are dropped: {sorted(parsed)}")
    pump = parsed["101"]
    require(pump["gecko_id"] == "pump-coin" and pump["tvl"] == 14_600_000 and pump["tvl_change_7d"] == -3.2 and pump["chains"] == ["Ethereum", "Base"] and pump["category"] == "Dexs", str(pump))
    odd = parsed["7"]
    require(odd["gecko_id"] == "seven" and odd["name"] == "x" and odd["tvl"] is None and odd["tvl_change_1d"] is None and odd["chains"] == ["A", "B"], f"garbage is None, never a guess: {odd}")
    require(len(q.parse_protocols([{"id": i, "gecko_id": f"c{i}", "chains": [f"c{j}" for j in range(40)]} for i in range(3)])["0"]["chains"]) == 12, "the chain list is trimmed")
    try:
        q.parse_protocols({"not": "a list"})
    except q.QualityError:
        pass
    else:
        raise AssertionError("a protocol list of the wrong shape was accepted")


def test_fees_and_revenue_are_mapped_through_the_protocol_id() -> None:
    fees = q.parse_dimension({"protocols": FEES + [None, "junk", {"total30d": 1}, {"defillamaId": 5, "total24h": "x", "total30d": 2}]})
    require(set(fees) == {"101", "999", "5"} and fees["101"] == {"24h": 1500.0, "7d": 10_000.0, "30d": 43_000.0, "1y": 600_000.0} and fees["5"]["24h"] is None and fees["5"]["30d"] == 2.0, str(fees))
    for bad in (None, [], {"protocols": "x"}, {"other": []}):
        try:
            q.parse_dimension(bad)
        except q.QualityError:
            continue
        raise AssertionError(f"a fees list of the wrong shape was accepted: {bad!r}")
    index = q.build_index(q.parse_protocols(PROTOCOLS), q.parse_dimension({"protocols": FEES}), q.parse_dimension({"protocols": REVENUE}))
    require(set(index) == {"pump-coin", "low-coin"}, "the index is keyed by CoinGecko id")
    pump = index["pump-coin"]
    require(pump["fees_30d"] == 43_000 and pump["fees_1y"] == 600_000 and pump["revenue_30d"] == 14_000 and pump["url"] == "https://defillama.com/protocol/pump-protocol", str(pump))
    low = index["low-coin"]
    require(low["tvl"] == 0 and low["fees_30d"] is None and low["revenue_1y"] is None, "tracked but without fees: None, not zero")
    require("999" not in {k for k in index} and not any(v.get("fees_30d") == 5 for v in index.values()), "fees of a protocol that is not in the list are ignored")


def test_data_presence_and_ratios_follow_positive_denominators() -> None:
    for record, expected in (({"tvl": 1.0}, True), ({"fees_30d": 0.5}, True), ({"tvl": 0, "fees_30d": 0}, False), ({"tvl": None, "fees_30d": None}, False), ({"tvl": -5}, False),
                             ({"tvl": float("nan"), "fees_30d": 3}, True), ({}, False), (None, False)):
        require(q.has_protocol_data(record) is expected, f"{record}: expected {expected}")
    r = q.valuation_ratios({"tvl": 10.0, "fees_1y": 4.0, "revenue_1y": 0}, 100.0)
    require(r == {"mcap_to_tvl": 10.0, "mcap_to_fees_1y": 25.0, "mcap_to_revenue_1y": None}, f"a zero denominator gives no ratio: {r}")
    require(all(v is None for v in q.valuation_ratios({"tvl": 10.0, "fees_1y": 4.0}, None).values()) and all(v is None for v in q.valuation_ratios({"tvl": 10.0}, 0).values()), "no market cap, no ratio")


# ----------------------------------------------------------------------------------------------------------------------- fetch and cache

def test_the_index_is_cached_in_memory_for_an_hour_and_failures_are_safe() -> None:
    q.clear_cache()
    fake, clock = FakeDefiLlama(), [1000.0]
    now = lambda: clock[0]  # noqa: E731
    index = q.fetch_quality_index(fake, now=now)
    require(len(fake.calls) == 3 and set(index) == {"pump-coin", "low-coin"}, "protocols, fees and revenue: three downloads")
    clock[0] += 3599
    require(q.fetch_quality_index(fake, now=now) is index and len(fake.calls) == 3, "served from memory inside the hour")
    clock[0] += 2
    require(q.fetch_quality_index(fake, now=now) is not index and len(fake.calls) == 6, "an hour later it downloads again")
    require(q.fetch_quality_index(fake, now=now, use_cache=False) and len(fake.calls) == 9, "the cache can be bypassed")
    q.clear_cache()
    secret = "SECRET-IN-ERROR"
    for transport, text in ((lambda u, t: (429, {}, b"{}"), "ritmo"), (lambda u, t: (500, {}, b"{}"), "HTTP 500"), (lambda u, t: (200, {}, b"<html>"), "no es JSON"),
                            (lambda u, t: (_ for _ in ()).throw(RuntimeError(secret)), "no respondió"), (transport_returning({"not": "a list"}), "forma inesperada")):
        try:
            q.fetch_quality_index(transport, now=now)
        except q.QualityError as error:
            require(text in str(error) and secret not in str(error) and error.__cause__ is None, f"{text}: {error}")
        else:
            raise AssertionError(f"{text}: no error raised")
        require(not q._CACHE, "a failure never poisons the cache")


# ----------------------------------------------------------------------------------------------------------------------------- the search

def test_the_search_attaches_the_quality_data_and_it_adds_no_points() -> None:
    with Sandbox() as box:
        client, cache, _ = direct_client(box)
        result = run_search(client, cache)
        coins = {r["coin_id"]: r for r in result.scored}
        s = result.summary
        require(coins["pump-coin"]["quality"]["tvl"] == 14_600_000 and q.has_protocol_data(coins["pump-coin"]["quality"]), "a protocol with TVL and fees")
        require(coins["low-coin"]["quality"] is not None and not q.has_protocol_data(coins["low-coin"]["quality"]), "tracked by DefiLlama, with nothing to show")
        require(all(coins[c]["quality"] is None for c in ("dilute-coin", "sus-coin", "quiet-1")), "not a protocol: None, which is neutral")
        require(s["quality_status"] == "ok" and s["with_quality"] == 1 and s["protocol_matches"] == 2 and len(box.defillama.calls) == 3, str(s))
        healthy = {k: v["score"] for k, v in coins.items()}
    with Sandbox(defillama_fails=True) as box:
        client, cache, _ = direct_client(box)
        result = run_search(client, cache)
        s = result.summary
        require(s["quality_status"] == "unavailable" and s["with_quality"] == 0 and all(r["quality"] is None for r in result.scored), "DefiLlama down: the search still works, without it")
        require({r["coin_id"]: r["score"] for r in result.scored} == healthy, "and no score changes: protocol data never adds or removes points")


def test_the_protocol_filter_keeps_only_coins_with_data() -> None:
    with Sandbox() as box:
        client, cache, _ = direct_client(box)
        scored = run_search(client, cache).scored
        require([r["coin_id"] for r in filter_results(scored, protocol_only=True)] == ["pump-coin"], "only the coin with TVL or fees")
        require(filter_results(scored, "low", protocol_only=True) == [] and [r["coin_id"] for r in filter_results(scored, "pump", level="candidates", protocol_only=True)] == ["pump-coin"], "it combines with the text and the level")
        require(len(filter_results(scored, protocol_only=False)) == len(filter_results(scored)), "off by default")


# ----------------------------------------------------------------------------------------------------------------------------- the page

def searched():
    at = open_crypto_page()
    button(at, "crypto_search").click().run()
    require(not at.exception, f"the search crashed: {[e.value[:120] for e in at.exception]}")
    return at


def open_coin(at, coin_id: str):
    button(at, f"crypto_fullpage_select_{screen.card_key(coin_id)}").click().run()
    require(not at.exception, f"the coin page crashed: {[e.value[:120] for e in at.exception]}")
    return at


def table_with(at, row_label: str):
    return next(d.value for d in at.dataframe if "Dato" in d.value.columns and row_label in set(d.value["Dato"]))


def test_cards_show_the_protocol_chips_only_when_there_is_data_and_the_summary_says_how_many() -> None:
    with Sandbox():
        at = searched()
        pump = next(c for c in cards(at) if "Pump Coin" in c)
        require("Protocolo · TVL 14,6 M$" in pump and "Comisiones 30 d 43 k$" in pump, "the card of a protocol with data")
        require(not any("Protocolo ·" in c or "Comisiones 30 d" in c for c in cards(at) if "Pump Coin" not in c), "no chip for a coin that is not a protocol, or that has no data")
        text = page_text(at)
        require("Calidad (DefiLlama, datos públicos): 1 monedas tienen datos de protocolo" in text and "no es una señal negativa" in text, "the summary says how many and that the rest is neutral")
    with Sandbox(defillama_fails=True):
        at = searched()
        require("No se pudieron consultar los datos de protocolo de DefiLlama" in page_text(at) and not any("Protocolo ·" in c for c in cards(at)), "an outage is said, never a crash")


def test_the_list_filter_and_going_back_keep_it() -> None:
    with Sandbox():
        at = searched()
        require("Mostrando 1–9 de 13 monedas" in page_text(at), "13 scored coins at first")
        box_ = next(w for w in at.selectbox if w.key == "crypto_filter_protocol")
        require(box_.options == ["Todas", "Con datos de protocolo"] and box_.value == "Todas", "the filter, off by default")
        box_.set_value("Con datos de protocolo").run()
        require(len(cards(at)) == 1 and "Pump Coin" in cards(at)[0] and "Mostrando 1–1 de 1 monedas" in page_text(at), "only the coin with data")
        open_coin(at, "pump-coin")
        require(at.session_state["crypto_filter_protocol"] == "Con datos de protocolo", "kept while the coin's page is open")
        button(at, "crypto_fullpage_back").click().run()
        require(at.session_state["crypto_filter_protocol"] == "Con datos de protocolo" and "Mostrando 1–1 de 1 monedas" in page_text(at), "and back at the list")
        next(w for w in at.selectbox if w.key == "crypto_filter_protocol").set_value("Todas").run()
        require("Mostrando 1–9 de 13 monedas" in page_text(at), "turning it off shows everything again")


def test_the_quality_tab_explains_every_case_as_information() -> None:
    with Sandbox():
        at = open_coin(searched(), "pump-coin")
        require([t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico", "Derivados", "Seguridad", "Calidad"], str([t.label for t in at.tabs]))
        values = dict(zip(*[table_with(at, "TVL (valor depositado)")[c] for c in ("Dato", "Valor")]))
        require(values["TVL (valor depositado)"] == "14,6 M$" and values["Cambio del TVL a 7 d"] == "-3,2 %" and values["Cambio del TVL a 1 mes"] == "+20,0 %", str(values))
        require(values["Comisiones 30 d"] == "43 k$" and values["Comisiones 1 año"] == "600 k$" and values["Ingresos del protocolo 30 d"] == "14 k$", str(values))
        require(values["Capitalización / TVL"] == "1,37" and values["Capitalización / comisiones del último año"] == "33,33" and values["Capitalización / ingresos del último año"] == "100,00", str(values))
        text = page_text(at)
        require("Protocolo **Pump Protocol**" in text and "https://defillama.com/protocol/pump-protocol" in text and "Ethereum, Base" in text, "the protocol, its chains and the link")
        require("Solo información: no suma puntos. Fuente: DefiLlama" in text and "doble recuento" in text, "information only, with the caveats")
        low = open_coin(searched(), "low-coin")
        require("no registra TVL ni comisiones" in page_text(low), "a tracked protocol with no data says so")
        none = open_coin(searched(), "sus-coin")
        require("no es un protocolo DeFi seguido por DefiLlama" in page_text(none) and "no es una señal negativa ni positiva" in page_text(none), "a coin that is not a protocol: neutral")
    with Sandbox(defillama_fails=True):
        down = open_coin(searched(), "pump-coin")
        require("No se pudieron consultar los datos de protocolo de DefiLlama en esta búsqueda" in page_text(down), "an outage is explained on the page")


def test_the_quality_data_changes_no_score_on_the_page_and_nothing_reaches_the_disk() -> None:
    with Sandbox() as box:
        at = searched()
        with_data = {r["coin_id"]: r["score"] for r in at.session_state["crypto_results"]}
    with Sandbox(defillama_fails=True) as box2:
        at2 = searched()
        require({r["coin_id"]: r["score"] for r in at2.session_state["crypto_results"]} == with_data, "the same scores with and without DefiLlama")
        require(all(p.suffix in (".bin", ".json") for p in box2.data_dir.rglob("*") if p.is_file() and p.name != "crypto_revolut_assets.txt"), "only the encrypted CoinGecko cache and the call counter are on disk")
    with Sandbox() as box3:
        searched()
        blob = b"".join(p.read_bytes() for p in box3.data_dir.rglob("*") if p.is_file())
        require(b"Pump Protocol" not in blob and b"14600000" not in blob and b"pump-protocol" not in blob, "nothing from DefiLlama is written to disk")


def test_the_module_is_quiet_keyless_and_writes_nothing() -> None:
    source = (ROOT / "src" / "crypto_v2_50" / "quality.py").read_text(encoding="utf-8")
    require("print(" not in source and "logging" not in source and "write_text" not in source and not re.search(r"(?<![a-z])open\(", source) and "to_csv" not in source, "no printing, logging or writing")
    require("api_key" not in source.lower() and "authorization" not in source.lower(), "no key")
    require("str(error)" not in source and "{error}" not in source, "transport error messages are never forwarded")
    ui = (ROOT / "src" / "ui_v2_37" / "crypto_screen.py").read_text(encoding="utf-8")
    require(not re.search(r"font-size:(\d|1[01])px", ui), "no text under 12 px")


CASES = [
    test_protocols_are_parsed_and_only_those_with_a_coingecko_id_are_kept,
    test_fees_and_revenue_are_mapped_through_the_protocol_id,
    test_data_presence_and_ratios_follow_positive_denominators,
    test_the_index_is_cached_in_memory_for_an_hour_and_failures_are_safe,
    test_the_search_attaches_the_quality_data_and_it_adds_no_points,
    test_the_protocol_filter_keeps_only_coins_with_data,
    test_cards_show_the_protocol_chips_only_when_there_is_data_and_the_summary_says_how_many,
    test_the_list_filter_and_going_back_keep_it,
    test_the_quality_tab_explains_every_case_as_information,
    test_the_quality_data_changes_no_score_on_the_page_and_nothing_reaches_the_disk,
    test_the_module_is_quiet_keyless_and_writes_nothing,
]


def main() -> int:
    forbid_network()
    for case in CASES:
        case()
    print("v2.50K crypto quality QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
