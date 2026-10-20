#!/usr/bin/env python3
"""QA for v2.50I (phase 5a): the age of a coin (tag below 90 days, cap 44 below 30) and the Binance derivatives (verified by price, information only).
Pure checks with scripted transports, then the real app through AppTest with a fake CoinGecko and a fake Binance. The real Binance is never
reached: the fake is patched in, because the code under test swallows transport errors (a blocked network would look like "derivatives
unavailable" and hide a real call). No network, no real key."""
from __future__ import annotations

import json
import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

from qa_crypto_search_v2_50f import (FRESH_PRICE_STATUS, FRESH_PRICES, HISTORY_DAYS, Sandbox, FakeBinance, button, cards, direct_client, forbid_network,  # noqa: E402
                                     open_crypto_page, page_text, require)
from src.crypto_v2_50 import coingecko as cg  # noqa: E402
from src.crypto_v2_50 import derivatives as dv, scoring as sc  # noqa: E402
from src.crypto_v2_50.search import run_search  # noqa: E402
from src.crypto_v2_50.signals import HISTORY_CAP_DAYS, daily_signals  # noqa: E402
from src.ui_v2_37 import crypto_screen as screen  # noqa: E402


def list_transport(items):
    return lambda url, timeout: (200, {}, json.dumps(items).encode())


# --------------------------------------------------------------------------------------------------------------------- derivatives

def test_the_list_of_perpetuals_is_parsed_and_a_link_needs_the_price_to_agree() -> None:
    perps = dv.fetch_perpetuals(list_transport([
        {"symbol": "BTCUSDT", "markPrice": "60000", "lastFundingRate": "0.0001", "nextFundingTime": 1792454400000},
        {"symbol": "1000PEPEUSDT", "markPrice": "0.012", "lastFundingRate": "-0.0003"}, {"symbol": "PEPEUSDT", "markPrice": "0.5", "lastFundingRate": "0"},
        {"symbol": "1MBABYDOGEUSDT", "markPrice": "0.5", "lastFundingRate": "0"}, {"symbol": "1INCHUSDT", "markPrice": "0.3", "lastFundingRate": "0"},
        {"symbol": "ETHBTC", "markPrice": "0.05"}, {"symbol": "BTCUSDT_250627", "markPrice": "1"}, {"symbol": "BADUSDT", "markPrice": "abc"},
        {"symbol": "ZEROUSDT", "markPrice": "0"}, {"symbol": 5}, "junk", None]))
    require(set(perps) == {"BTC", "PEPE", "BABYDOGE", "1INCH"}, f"only well-formed USDT perpetuals, keyed by base asset: {sorted(perps)}")
    require(sorted(c["factor"] for c in perps["PEPE"]) == [1, 1000] and perps["BABYDOGE"][0]["factor"] == 1_000_000 and perps["1INCH"][0]["factor"] == 1, "x1000 / 1M contract multipliers; a real name starting with 1 is not one")
    require(perps["BTC"][0]["next_funding_time"] == 1792454400000 and perps["PEPE"][0]["funding_rate"] is not None, "fields")
    pepe = {"symbol": "PEPE", "price_usd": 0.000012}
    match, conflict = dv.match_perpetual(pepe, perps)
    require(match and match["symbol"] == "1000PEPEUSDT" and match["price_gap"] < 1e-9 and conflict is False, f"the x1000 contract is verified at 1/1000 of its quoted price: {match}")
    require(dv.match_perpetual({"symbol": "pepe", "price_usd": 0.000012}, perps)[0]["symbol"] == "1000PEPEUSDT", "symbols are compared in upper case")
    require(dv.match_perpetual({"symbol": "PEPE", "price_usd": 0.47}, perps)[0]["symbol"] == "PEPEUSDT", "of two candidates the one whose price agrees is chosen")
    require(dv.match_perpetual({"symbol": "BTC", "price_usd": 50000}, perps) == (None, True), "a perpetual with that symbol exists but its price disagrees: rejected and reported as a conflict")
    require(dv.match_perpetual({"symbol": "BTC", "price_usd": None}, perps) == (None, True), "no price to verify with: not linked")
    require(dv.match_perpetual({"symbol": "NOPE", "price_usd": 1.0}, perps) == (None, False), "no perpetual, no conflict")
    one = {"BTC": [{"symbol": "BTCUSDT", "factor": 1, "mark_price": 1.0999, "funding_rate": 0.0}]}
    require(dv.match_perpetual({"symbol": "BTC", "price_usd": 1.0}, one)[0] is not None, "9.99 % apart is accepted")
    one["BTC"][0]["mark_price"] = 1.1001
    require(dv.match_perpetual({"symbol": "BTC", "price_usd": 1.0}, one) == (None, True), "10.01 % apart is rejected")


def test_the_detail_of_a_perpetual_is_parsed_and_failures_are_safe() -> None:
    detail = dv.fetch_perp_detail({"symbol": "PUMPUSDT", "mark_price": 1.5}, FakeBinance())
    require(abs(detail["open_interest_usd"] - 1_500_000) < 1e-6, f"contracts x the price per contract: {detail['open_interest_usd']}")
    require(abs(detail["oi_change_7d_pct"] - (1_290_000 / 1_220_000 - 1) * 100) < 1e-9 and abs(detail["oi_change_30d_pct"] - 29.0) < 1e-9 and detail["oi_history_days"] == 30, str(detail))
    require(abs(detail["long_short_ratio"] - 2.0) < 1e-9 and detail["long_short_min_30d"] == 1.0 and abs(detail["long_account_share"] - 0.6) < 1e-9 and detail["ratio_history_days"] == 30, str(detail))

    def junk(url, timeout):
        if "openInterest?" in url:
            return 200, {}, json.dumps({"openInterest": "x"}).encode()
        return 200, {}, json.dumps([{"sumOpenInterestValue": "bad", "longShortRatio": None}, "row", None]).encode()

    empty = dv.fetch_perp_detail({"symbol": "XUSDT", "mark_price": 2.0}, junk)
    require(empty["open_interest_usd"] is None and empty["oi_change_7d_pct"] is None and empty["long_short_ratio"] is None and empty["oi_history_days"] == 0, f"garbage is None, never a guess: {empty}")
    secret = "SECRET-IN-ERROR"
    for transport, text in ((lambda u, t: (429, {}, b"{}"), "ritmo"), (lambda u, t: (418, {}, b"{}"), "ritmo"), (lambda u, t: (500, {}, b"{}"), "HTTP 500"),
                            (lambda u, t: (200, {}, b"<html>"), "no es JSON"), (lambda u, t: (_ for _ in ()).throw(RuntimeError(secret)), "no respondió")):
        try:
            dv.fetch_perpetuals(transport)
        except dv.DerivativesError as error:
            require(text in str(error) and secret not in str(error) and error.__cause__ is None, f"{text}: {error}")
        else:
            raise AssertionError(f"{text}: no error raised")
    try:
        dv.fetch_perpetuals(list_transport({"not": "a list"}))
    except dv.DerivativesError:
        pass
    else:
        raise AssertionError("a list that is not a list was accepted")


def test_the_squeeze_hint_is_negative_funding_with_a_rising_price() -> None:
    for funding, change, expected in ((-0.0001, 5.0, True), (-0.0001, 0.0, False), (-0.0001, -3.0, False), (0.0, 10.0, False), (0.0002, 10.0, False),
                                      (None, 10.0, False), (-0.0001, None, False), (float("nan"), 5.0, False)):
        require(dv.squeeze_hint(funding, change) is expected, f"funding {funding}, 7 d {change}: expected {expected}")


# ------------------------------------------------------------------------------------------------------------------------------- age

def series_of(days: int) -> list[dict]:
    return [{"date": f"d{i}", "price_usd": 1.0, "volume_usd": 100.0} for i in range(days)]


def test_history_length_is_measured_from_the_series_and_capped_at_a_year() -> None:
    row = {"volume_24h_usd": 100.0, "price_usd": 1.0}
    require(daily_signals(row, [])["history_days"] is None and daily_signals(row, [])["history_capped"] is None, "no series: unknown, not zero")
    for days, capped in ((1, False), (29, False), (30, False), (89, False), (90, False), (HISTORY_CAP_DAYS - 1, False), (HISTORY_CAP_DAYS, True), (365, True)):
        out = daily_signals(row, series_of(days))
        require(out["history_days"] == days and out["history_capped"] is capped, f"{days} days: {out['history_days']} {out['history_capped']}")


def strong_row() -> dict:
    return {"coin_id": "x", "symbol": "X", "market_cap_usd": 20e6, "volume_24h_usd": 8e6, "change_7d_pct": 40.0, "change_30d_pct": 120.0,
            "circulating_supply": 1.0, "total_supply": 1.0, "fdv_usd": 20e6}


def test_a_young_coin_is_tagged_below_90_days_and_capped_below_30() -> None:
    base = {"rel_vol_rolling": 8.0, "breakout_30d": True}
    mature = sc.score_row(strong_row(), base | {"history_days": 364, "history_capped": True})
    require(mature["score"] == 90 and mature["risk_flags"] == [] and mature["caps_applied"] == [], str(mature))
    for days, tagged in ((89, True), (90, False), (45, True), (30, True)):
        result = sc.score_row(strong_row(), base | {"history_days": days, "history_capped": False})
        require(("moneda reciente" in result["risk_flags"]) is tagged and result["score"] == 90 and result["caps_applied"] == [], f"{days} days: {result['risk_flags']} score {result['score']}")
    young = sc.score_row(strong_row(), base | {"history_days": 29, "history_capped": False})
    require(young["score"] == 44 and young["tier"] == sc.TIER_WATCH and young["caps_applied"][0]["reason"] == "moneda reciente (menos de 30 días de historial)" and "moneda reciente" in young["risk_flags"], str(young["caps_applied"]))
    for unknown in ({}, {"history_days": None, "history_capped": None}, {"history_days": 10, "history_capped": True}):
        result = sc.score_row(strong_row(), base | unknown)
        require("moneda reciente" not in result["risk_flags"] and result["score"] == 90, f"an unknown age, or a series as long as the plan allows, is never young: {unknown}")
    require(sc.is_young(29, False, 30) and not sc.is_young(30, False, 30) and not sc.is_young(None, None, 30) and not sc.is_young(5, True, 30) and not sc.is_young("x", False, 30), "is_young")


# ------------------------------------------------------------------------------------------------------------------------- the search

def test_the_search_links_verified_perpetuals_and_survives_a_binance_outage() -> None:
    with Sandbox() as box:
        client, cache, _ = direct_client(box)
        result = run_search(client, cache)
        coins = {r["coin_id"]: r for r in result.scored}
        s = result.summary
        require(coins["pump-coin"]["perp"]["symbol"] == "PUMPUSDT" and coins["pump-coin"]["perp"]["factor"] == 1, str(coins["pump-coin"]["perp"]))
        require(coins["low-coin"]["perp"]["symbol"] == "1000LOWCUSDT" and coins["low-coin"]["perp"]["factor"] == 1000, "the x1000 contract is linked")
        require(coins["dilute-coin"]["perp"] is None and coins["dilute-coin"]["perp_conflict"] is True, "same symbol, other price: not linked, reported")
        require(coins["sus-coin"]["perp"] is None and coins["sus-coin"]["perp_conflict"] is False, "no perpetual")
        require(s["perps_status"] == "ok" and s["with_perp"] == 2 and s["perp_conflicts"] == 1 and s["calls_used"] == 9, str(s))
        require(len(box.binance.calls) == 1 and "/premiumIndex" in box.binance.calls[0], "one public call for the whole list")
        healthy_scores = {k: v["score"] for k, v in coins.items()}
        fresh_call = [u for u in box.fake.calls if "/simple/price" in u]
        require(len(fresh_call) == 1 and all(c in fresh_call[0] for c in ("pump-coin", "low-coin", "dilute-coin")) and "sus-coin" not in fresh_call[0],
                "fresh prices are asked once, only for the coins whose symbol matches a perpetual")
    with Sandbox(binance_fails=True) as box:
        client, cache, _ = direct_client(box)
        result = run_search(client, cache)
        require(result.summary["perps_status"] == "unavailable" and result.summary["with_perp"] == 0 and all(r["perp"] is None for r in result.scored), "Binance down: the search still works, without derivatives")
        require({r["coin_id"]: r["score"] for r in result.scored} == healthy_scores, "and no score changes: derivatives never add points")


# ----------------------------------------------------------------------------------------------------------------------------- the page

def searched():
    at = open_crypto_page()
    button(at, "crypto_search").click().run()
    require(not at.exception, f"the search crashed: {[e.value[:120] for e in at.exception]}")
    return at


def table_with(at, row_label: str):
    """The two-column table (Dato / Valor) that has a row with this label; the score-by-signal table has other columns."""
    return next(d.value for d in at.dataframe if "Dato" in d.value.columns and row_label in set(d.value["Dato"]))


def open_coin(at, coin_id: str):
    button(at, f"crypto_fullpage_select_{screen.card_key(coin_id)}").click().run()
    require(not at.exception, f"the coin page crashed: {[e.value[:120] for e in at.exception]}")
    return at


def test_cards_show_the_perpetual_and_the_squeeze_hint() -> None:
    with Sandbox() as box:
        at = searched()
        shown = {("Pump Coin" in c, "Low Coin" in c): c for c in cards(at)}
        pump = next(c for c in cards(at) if "Pump Coin" in c)
        low = next(c for c in cards(at) if "Low Coin" in c)
        require("Con perpetuo · financiación -0,0200 %" in pump and "Financiación negativa con subida" in pump, "negative funding with a rising price is flagged on the card")
        require("Con perpetuo · financiación +0,0100 %" in low and "Financiación negativa con subida" not in low, "positive funding is not")
        require(any(c for c in cards(at) if "Con perpetuo" not in c), "coins without a perpetual carry no derivatives chip")
        text = page_text(at)
        require("Derivados (Binance, datos públicos): 2 monedas tienen perpetuo con identidad verificada por precio fresco." in text and "Se descartaron 1 coincidencias de símbolo cuyo precio fresco no encajaba" in text, text[:800])
        require(len(box.binance.calls) == 1 and len(shown) >= 1, "one Binance call for the whole page")
    with Sandbox(binance_fails=True):
        at = searched()
        require("No se pudo consultar la lista de perpetuas de Binance" in page_text(at) and not any("Con perpetuo" in c for c in cards(at)), "a Binance outage is said, never a crash")


def test_the_derivatives_tab_shows_the_data_once_and_explains_every_case() -> None:
    with Sandbox() as box:
        at = open_coin(searched(), "pump-coin")
        require([t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico", "Derivados", "Seguridad", "Calidad"], str([t.label for t in at.tabs]))
        table = table_with(at, "Open interest (valor)")
        values = dict(zip(table["Dato"], table["Valor"]))
        require(values["Open interest (valor)"] == "1,5 M$" and values["Tasa de financiación actual (por periodo)"] == "-0,0200 %" and values["Cambio del open interest a 30 d"] == "+29,0 %", str(values))
        require(values["Ratio largos/cortos (cuentas, último día)"] == "2,00" and values["Cuentas largas"] == "60,0 %", str(values))
        require(any("Financiación negativa con subida a 7 días" in w.value for w in at.warning), "the squeeze indication, worded as an indication")
        require(any("los derivados no suman puntos" in c.value for c in at.caption), "information only")
        require(any("Identidad verificada" in c.value for c in at.caption), "the identity check is stated")
        calls = len(box.binance.calls)
        require(calls == 4, f"the list plus three small calls: {calls}")
        at.run()
        require(len(box.binance.calls) == calls, "a rerun (a tab switch) is served from the five-minute memory cache")
        low = open_coin(searched(), "low-coin")
        require(any("no se da ahora en esta moneda" in m.value for m in low.markdown) and not any("Financiación negativa con subida a 7 días" in w.value for w in low.warning), "no squeeze setup: said so")
        conflict = open_coin(searched(), "dilute-coin")
        require(any("podría ser otra moneda" in i.value for i in conflict.info), "a symbol conflict is explained")
        none = open_coin(searched(), "sus-coin")
        require(any("no tiene perpetuo USDT en Binance" in i.value for i in none.info), "no perpetual is explained")
    with Sandbox(binance_detail_fails=True):
        at = open_coin(searched(), "pump-coin")
        require(any("Binance respondió con HTTP 500" in i.value for i in at.info), "a failing detail call is explained")
    with Sandbox(binance_fails=True):
        at = open_coin(searched(), "pump-coin")
        require(any("No se pudo consultar la lista de perpetuas" in i.value for i in at.info), "an outage during the search is explained on the page")


def test_the_age_is_shown_and_a_young_coin_is_tagged_and_capped() -> None:
    with Sandbox():
        HISTORY_DAYS["pump-coin"] = 45
        at = searched()
        pump = next(c for c in cards(at) if "Pump Coin" in c)
        require("Moneda reciente" in pump and "/100" in pump, "the card carries the tag")
        require(next(r for r in at.session_state["crypto_results"] if r["coin_id"] == "pump-coin")["score"] == 90, "45 days: tagged, not capped")
        at = open_coin(at, "pump-coin")
        market = table_with(at, "Historial en CoinGecko")
        require(dict(zip(market["Dato"], market["Valor"]))["Historial en CoinGecko"] == "45 días", "the age on the Datos tab")
        require("Moneda reciente." in page_text(at) and "menos de 90 días de historial" in page_text(at), "the risk is explained")
    with Sandbox():
        HISTORY_DAYS["pump-coin"] = 365
        at = open_coin(searched(), "pump-coin")
        market = table_with(at, "Historial en CoinGecko")
        require(dict(zip(market["Dato"], market["Valor"]))["Historial en CoinGecko"] == "un año o más" and "Moneda reciente" not in page_text(at), "a year of history: no tag")
    with Sandbox():
        HISTORY_DAYS["pump-coin"] = 25
        at = searched()
        pump = next(r for r in at.session_state["crypto_results"] if r["coin_id"] == "pump-coin")
        require(pump["score"] <= 44 and pump["tier"] == sc.TIER_WATCH and pump["caps_applied"][0]["reason"].startswith("moneda reciente"), f"under 30 days: capped, tier watch: {pump['caps_applied']}")


def test_identity_is_checked_against_a_fresh_price_not_the_cached_one() -> None:
    with Sandbox() as box:
        FRESH_PRICES.update({"dilute-coin": 295.0, "pump-coin": 1.2})  # the market data in the cache is hours old: by now the first has moved to the mark, the second has not
        client, cache, _ = direct_client(box)
        coins = {r["coin_id"]: r for r in run_search(client, cache).scored}
        require(coins["dilute-coin"]["perp"] is not None and coins["dilute-coin"]["perp"]["symbol"] == "DILUSDT", "a stale cached price no longer rejects a real match")
        require(coins["pump-coin"]["perp"] is None and coins["pump-coin"]["perp_conflict"] is True, "and a cached price that happened to agree does not confirm one that has moved away")
        require(abs(coins["dilute-coin"]["perp"]["price_gap"] - (300.0 / 295.0 - 1)) < 1e-9, "the gap shown is against the fresh price")
    with Sandbox() as box:
        FRESH_PRICE_STATUS["code"] = 500
        client, cache, _ = direct_client(box)
        result = run_search(client, cache)
        require(result.summary["perps_status"] == "unverified" and result.summary["with_perp"] == 0 and all(r["perp"] is None for r in result.scored), "no fresh prices: no link is made on a stale price")
        require(all(r["perp_conflict"] for r in result.scored if r["coin_id"] in ("pump-coin", "low-coin", "dilute-coin")), "the coins that matched a symbol say they could not be confirmed")


def test_fresh_prices_are_fetched_in_chunks_and_never_invented() -> None:
    from src.crypto_v2_50.usage import SAFETY_CAP, UsageCounter
    import tempfile

    seen = []

    def transport(url, headers, timeout):
        seen.append(url)
        ids = url.split("ids=")[1].split("&")[0].replace("%2C", ",").split(",")
        body = {i: {"usd": 1.0 + n} for n, i in enumerate(ids) if not i.endswith("7")}  # ids ending in 7 get no answer
        body["a-zero"] = {"usd": 0}
        body["a-text"] = {"usd": "x"}
        body["a-shape"] = "oops"
        return 200, {}, json.dumps(body).encode()

    with tempfile.TemporaryDirectory() as d:
        usage = UsageCounter(Path(d) / "u.json")
        client = cg.CoinGeckoClient("CG-FAKE", usage=usage, transport=transport, sleep=lambda s: None, min_interval=0.0)
        ids = [f"coin-{i:03d}" for i in range(250)]
        prices = cg.fetch_fresh_prices(client, ids)
        require(len(seen) == 3 and usage.calls_this_month() == 3, f"250 ids in chunks of 100: {len(seen)} calls")
        require(all(i in prices for i in ids if not i.endswith("7")) and not any(i.endswith("7") for i in prices), "a coin CoinGecko does not answer for is absent, never filled in")
        require("a-zero" not in prices and "a-text" not in prices and "a-shape" not in prices, "zero, non-numeric and malformed entries are dropped")
        require(cg.fetch_fresh_prices(client, []) == {} and len(seen) == 3, "nothing to ask: no call")
        UsageCounter(Path(d) / "u.json").record(SAFETY_CAP - usage.calls_this_month() - 2)
        try:
            cg.fetch_fresh_prices(client, ids)
        except cg.BudgetExhausted:
            require(len(seen) == 3, "the budget for all three chunks is checked before the first call")
        else:
            raise AssertionError("fresh prices were fetched without the budget")
        bad = cg.CoinGeckoClient("CG-FAKE", usage=UsageCounter(Path(d) / "u2.json"), transport=lambda u, h, t: (200, {}, b"[1, 2]"), sleep=lambda s: None, min_interval=0.0)
        try:
            cg.fetch_fresh_prices(bad, ["x"])
        except cg.CoinGeckoError:
            pass
        else:
            raise AssertionError("a response of the wrong shape was accepted")


def test_the_derivatives_module_is_quiet_and_keyless() -> None:
    source = (ROOT / "src" / "crypto_v2_50" / "derivatives.py").read_text(encoding="utf-8")
    require("print(" not in source and "logging" not in source and "api_key" not in source.lower() and "x-mbx-apikey" not in source.lower(), "no logging, no key")
    require("str(error)" not in source and "{error}" not in source, "transport error messages are never forwarded")
    ui = (ROOT / "src" / "ui_v2_37" / "crypto_screen.py").read_text(encoding="utf-8")
    require("str(error)" in ui.split("def _load_perp_detail")[1].split("def ")[0] and "DerivativesError" in ui, "the page forwards only the safe DerivativesError text")


CASES = [
    test_the_list_of_perpetuals_is_parsed_and_a_link_needs_the_price_to_agree,
    test_the_detail_of_a_perpetual_is_parsed_and_failures_are_safe,
    test_the_squeeze_hint_is_negative_funding_with_a_rising_price,
    test_history_length_is_measured_from_the_series_and_capped_at_a_year,
    test_a_young_coin_is_tagged_below_90_days_and_capped_below_30,
    test_the_search_links_verified_perpetuals_and_survives_a_binance_outage,
    test_identity_is_checked_against_a_fresh_price_not_the_cached_one,
    test_fresh_prices_are_fetched_in_chunks_and_never_invented,
    test_cards_show_the_perpetual_and_the_squeeze_hint,
    test_the_derivatives_tab_shows_the_data_once_and_explains_every_case,
    test_the_age_is_shown_and_a_young_coin_is_tagged_and_capped,
    test_the_derivatives_module_is_quiet_and_keyless,
]


def main() -> int:
    forbid_network()
    for case in CASES:
        case()
    print("v2.50I crypto safety 5a QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
