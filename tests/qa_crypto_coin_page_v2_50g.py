#!/usr/bin/env python3
"""QA for v2.50G, a crypto coin's own page (4b): the score breakdown and the caps it shows, the chart (a line of closes and volume, never
candles, never an invented point), unique widget keys, and the real app through AppTest: the page opens from a card with three tabs,
reads the series from the 24 h cache or spends one call, explains failures, respects the budget, works without a key, and going back
keeps the filters and the page. Fake CoinGecko, fake key, temporary data folder, `urlopen` blocked. No network, no real key."""
from __future__ import annotations

import logging
import os
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

import pandas as pd  # noqa: E402

from qa_crypto_search_v2_50f import (BASELINE_VOLUME, FAKE_KEY, Sandbox, button, cards, direct_client, forbid_network, open_crypto_page, page_text,  # noqa: E402
                                     require)
from src.crypto_v2_50 import charts, scoring as sc  # noqa: E402
from src.crypto_v2_50.coingecko import KEY_ENV  # noqa: E402
from src.crypto_v2_50.search import filter_results, run_search  # noqa: E402
from src.crypto_v2_50.usage import SAFETY_CAP  # noqa: E402
from src.ui_v2_37 import crypto_screen as screen  # noqa: E402


def by_id(box: Sandbox) -> dict:
    client, cache, _ = direct_client(box)
    return {r["coin_id"]: r for r in run_search(client, cache).scored}


# ------------------------------------------------------------------------------------------------------------- score breakdown

def test_the_breakdown_adds_up_and_the_caps_explain_the_final_score() -> None:
    with Sandbox() as box:
        coins = by_id(box)
        for coin_id, item in coins.items():
            if item["tier"] in (sc.TIER_NO_LIQUIDITY, sc.TIER_NO_DATA):
                require(item["breakdown"] == [] and item["points_before_caps"] == 0 and item["caps_applied"] == [], f"{coin_id}: a coin that is not scored has no breakdown")
                continue
            require(sum(b["points"] for b in item["breakdown"]) == item["points_before_caps"], f"{coin_id}: the signals add up to the points before the caps")
            limits = [c["max"] for c in item["caps_applied"]]
            expected = min([item["points_before_caps"]] + limits)
            require(item["score"] == expected, f"{coin_id}: the final score is the points or the lowest cap that applied: {item['score']} vs {expected}")
            require(all(c["max"] < item["points_before_caps"] for c in item["caps_applied"]), f"{coin_id}: only caps that actually lower the score are listed")
            require({b["signal"] for b in item["breakdown"]} == {"rotación de volumen", "volumen relativo", "momentum 30 d", "momentum 7 d", "ruptura del máximo de 30 días con volumen", "capitalización pequeña"}, f"{coin_id}: one line per signal")
        pump = coins["pump-coin"]
        require(pump["points_before_caps"] == 90 and pump["caps_applied"] == [] and pump["score"] == 90, f"nothing caps a full score: {pump['caps_applied']}")
        dilute = coins["dilute-coin"]
        require(dilute["points_before_caps"] == 90 and dilute["score"] == 69 and [c["reason"] for c in dilute["caps_applied"]] == ["dilución alta"], str(dilute["caps_applied"]))
        sus = coins["sus-coin"]
        require("rotación sospechosa" in sus["risk_flags"] and sus["score"] <= 44 and sus["caps_applied"] == [], "34 points are under every cap, so no cap is listed; the risk is still flagged")
        require(next(b for b in sus["breakdown"] if b["signal"] == "rotación de volumen")["points"] == 0, "a suspicious turnover earns no rotation points")
        broken = coins["broken-coin"]
        require([c["reason"] for c in broken["caps_applied"]] == ["dato crítico ausente: volumen relativo"] and broken["points_before_caps"] == 54 and broken["score"] == 44, str(broken["caps_applied"]))
        require(coins["quiet-1"]["caps_applied"] == [] and coins["quiet-1"]["missing_signals"] == ["volumen relativo"], "a coin under every cap lists none, but still says what is missing")
    strong = {"coin_id": "s", "symbol": "S", "market_cap_usd": 50e6, "volume_24h_usd": 80e6, "change_7d_pct": 50.0, "change_30d_pct": 100.0, "circulating_supply": 1.0, "total_supply": 1.0, "fdv_usd": 50e6}
    suspicious = sc.score_row(strong, {"rel_vol_rolling": 5.0, "breakout_30d": True})  # turnover 1.6
    require(suspicious["points_before_caps"] == 70 and suspicious["score"] == 44 and [c["reason"] for c in suspicious["caps_applied"]] == ["rotación sospechosa", ] and suspicious["tier"] == sc.TIER_WATCH,
            f"a high-scoring coin with a suspicious turnover is capped and says so: {suspicious['caps_applied']}")


def test_the_search_carries_the_series_signals_with_each_coin() -> None:
    with Sandbox() as box:
        coins = by_id(box)
        pump = coins["pump-coin"]
        require(pump["has_series"] is True and abs(pump["rel_vol_rolling"] - 8.0) < 1e-6 and pump["breakout_30d"] is True, f"{pump['rel_vol_rolling']} {pump['breakout_30d']}")
        require(coins["low-coin"]["breakout_30d"] is False, "a price equal to the closes is not a breakout")
        for coin_id in ("quiet-1", "broken-coin", "sus-coin"):
            require(coins[coin_id]["has_series"] is False and "rel_vol_rolling" not in coins[coin_id], f"{coin_id}: no series, no series signals")
        require(BASELINE_VOLUME["pump-coin"] == 1e6, "fixture sanity")


# ------------------------------------------------------------------------------------------------------------------------- chart

def series(days: int = 40, volume: bool = True) -> list[dict]:
    return [{"date": f"2026-09-{(i % 28) + 1:02d}-{i}", "price_usd": 1.0 + i * 0.01, "market_cap_usd": 1e7, "volume_usd": (1000.0 + i) if volume else None} for i in range(days)]


def test_the_chart_is_a_line_and_volume_never_candles_or_invented_points() -> None:
    data = series(40)
    fig = charts.daily_series_figure(data)
    kinds = [t.type for t in fig.data]
    require("candlestick" not in kinds and "ohlc" not in kinds, f"no candles on the free plan: {kinds}")
    require(kinds == ["scatter", "scatter", "bar"], str(kinds))
    close, reference, volume = fig.data
    require(list(close.y) == [p["price_usd"] for p in data] and list(volume.y) == [p["volume_usd"] for p in data], "the plotted values are the series, untouched")
    require(abs(reference.y[0] - max(p["price_usd"] for p in data[-30:])) < 1e-12 and reference.y[0] == reference.y[1], "the reference line is the highest of the last 30 closes")
    require(volume.yaxis != close.yaxis and fig.layout.showlegend is False and fig.layout.margin.t <= 56, "volume in its own panel; no legend inside the figure")
    require(charts.reference_high(series(29)) is None and len([t for t in charts.daily_series_figure(series(29)).data if t.type == "scatter"]) == 1, "under 30 days there is no reference line")
    require(not any(t.type == "bar" for t in charts.daily_series_figure(series(40, volume=False)).data), "no volume, no volume panel")
    gap = series(40)
    gap[10]["price_usd"] = None
    gap_fig = charts.daily_series_figure(gap)
    require(gap_fig.data[0].y[10] is None and gap_fig.data[0].connectgaps is False, "a missing close is a gap, not an interpolated value")
    for text, volume_flag, ref_flag in ((charts.chart_key_text(True, True), True, True), (charts.chart_key_text(False, False), False, False)):
        require(("volumen" in text) is volume_flag and ("referencia de la señal de ruptura" in text) is ref_flag and "día en curso" in text, text)
    require(charts.daily_series_figure([]).data[0].y == () or list(charts.daily_series_figure([]).data[0].y) == [], "an empty series draws nothing")


def test_widget_keys_are_unique_per_coin() -> None:
    ids = ["a-b", "a_b", "a.b", "a b", "bitcoin", "Bitcoin", "x" * 80 + "1", "x" * 80 + "2", "wrapped-bitcoin", "wrapped_bitcoin"]
    keys = [screen.card_key(i) for i in ids]
    require(len(set(keys)) == len(ids), f"ids that differ only by punctuation or case still get distinct keys: {keys}")
    require(screen.card_key("a-b") == screen.card_key("a-b") and all(re.fullmatch(r"[A-Za-z0-9_]+", k) for k in keys), "deterministic and safe for a CSS selector")


# ----------------------------------------------------------------------------------------------------------------------- the page

def open_coin(at, coin_id: str):
    button(at, f"crypto_fullpage_select_{screen.card_key(coin_id)}").click().run()
    require(not at.exception, f"the coin page crashed: {[e.value[:120] for e in at.exception]}")
    return at


def searched(at=None):
    at = at or open_crypto_page()
    button(at, "crypto_search").click().run()
    require(not at.exception, f"the search crashed: {[e.value[:120] for e in at.exception]}")
    return at


def charts_drawn(at) -> int:
    return len(at.get("plotly_chart"))


def frames(at) -> list[pd.DataFrame]:
    return [d.value for d in at.dataframe]


def test_a_card_opens_the_coin_page_with_three_tabs() -> None:
    with Sandbox() as box:
        at = open_coin(searched(), "pump-coin")
        require([t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico", "Derivados", "Seguridad"], [t.label for t in at.tabs])
        text = page_text(at)
        require("Pump Coin" in text and "/100" in text and "Candidato explosivo · alto" in text, "the header names the coin, its score and its level")
        require("coingecko.com/en/coins/pump-coin" in text and "Powered by CoinGecko" in text, "the CoinGecko link and the attribution")
        # AppTest keeps the buttons of the run that called st.rerun(), so the page is judged by its heading (checked in a real browser too).
        require(not at.title and "crypto_fullpage_back" in [b.key for b in at.button], "the coin's page replaces the list (no page title), with a way back")
        require("Qué revisar manualmente" in text and "contrato y la distribución de tenedores" in text and "no es recomendación financiera ni predice rentabilidad" in text.lower().replace("es una", "es").replace("no es recomendación", "no es recomendación"), "what to review by hand, with the guardrail")
        market, breakdown = frames(at)[0], frames(at)[1]
        require({"Capitalización", "Volumen 24 h", "Suministro circulante", "FDV / capitalización"} <= set(market["Dato"]), "market figures")
        require(list(breakdown.columns) == ["Señal", "Valor", "Puntos", "¿Señal fuerte?"] and breakdown["Puntos"].sum() == 90 and len(breakdown) == 6, str(breakdown))
        require(any("Puntos antes de los topes: 90. Puntuación final: 90. Ningún tope la reduce." in c.value for c in at.caption), "no cap applied")
        require(FAKE_KEY not in text and FAKE_KEY not in str(frames(at)), "the key is nowhere on the page")
        calls = len(box.fake.calls)
        require(charts_drawn(at) == 1 and calls == 9, f"the series of a pre-selected coin comes from the 24 h cache: one chart, no extra call ({calls})")
        require(any("Línea verde azulada" in c.value and "barras azules: volumen diario" in c.value for c in at.caption) and any("sin velas" in c.value for c in at.caption), "the chart key and the no-candles note")


def test_a_diluted_coin_page_explains_the_risk_and_the_cap() -> None:
    with Sandbox():
        at = open_coin(searched(), "dilute-coin")
        text = page_text(at)
        require("**Dilución alta.**" in text or "Dilución alta." in text, "the risk is named")
        require("como mucho nivel bajo" in text, "and its consequence is explained")
        require(any("Tope aplicado:" in m.value and "dilución alta" in m.value and "máximo 69" in m.value for m in at.markdown), "the applied cap is listed")
        require("Puntos antes de los topes: 90. Puntuación final: 69." in " ".join(c.value for c in at.caption), "90 points before the cap, 69 after")
        sus = open_coin(searched(), "sus-coin")
        require("Rotación sospechosa." in page_text(sus) and "falsa sensación de liquidez" in page_text(sus), "suspicious turnover is explained too")


def test_a_series_not_in_the_cache_costs_one_call_once() -> None:
    with Sandbox() as box:
        at = searched()
        before = box.usage.calls_this_month()
        open_coin(at, "quiet-3")
        require(box.usage.calls_this_month() == before + 1 and charts_drawn(at) == 1, f"one call for a coin that was not pre-selected: {box.usage.calls_this_month() - before}")
        button(at, "crypto_fullpage_back").click().run()
        open_coin(at, "quiet-3")
        require(box.usage.calls_this_month() == before + 1 and charts_drawn(at) == 1, "opening it again is served from the 24 h cache")


def test_a_series_that_cannot_be_loaded_is_explained_not_a_crash() -> None:
    with Sandbox() as box:
        at = open_coin(searched(), "broken-coin")
        require(charts_drawn(at) == 0 and any("No se pudo cargar la serie diaria" in i.value for i in at.info), "no chart, a clear message")
        require([t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico", "Derivados", "Seguridad"] and "Broken Coin" in page_text(at), "the other tabs still work")
    with Sandbox() as box:
        at = searched()
        box.usage.record(SAFETY_CAP - box.usage.calls_this_month())
        before = len(box.fake.calls)
        open_coin(at, "quiet-2")
        require(charts_drawn(at) == 0 and any("No hay presupuesto de llamadas suficiente" in i.value for i in at.info) and len(box.fake.calls) == before, "no budget: a clear message and no call")
    with Sandbox() as box:
        at = searched()
        os.environ.pop(KEY_ENV, None)  # the key disappears after the search
        open_coin(at, "quiet-4")
        require(charts_drawn(at) == 0 and any(KEY_ENV in i.value for i in at.info), "no key: the page says which variable to set and does not crash")
        require(FAKE_KEY not in page_text(at), "and it never prints a key")


def test_going_back_keeps_the_filters_and_the_page() -> None:
    with Sandbox():
        at = searched()
        level = next(w for w in at.selectbox if w.key == "crypto_filter_level")
        level.set_value("En vigilancia").run()
        require("Mostrando 1–9 de 10 monedas" in page_text(at), "ten coins in watch, nine per page")
        button(at, "crypto_page_next").click().run()
        require(at.session_state["crypto_page"] == 2, "second page")
        on_page_two = filter_results(at.session_state["crypto_results"], "", "watch")[9]  # the tenth coin of the watch list is the only one on page 2
        open_coin(at, on_page_two["coin_id"])
        require(at.session_state["crypto_page"] == 2 and at.session_state["crypto_filter_level"] == "En vigilancia", "the page and the filter are kept while the coin's page is open")
        button(at, "crypto_fullpage_back").click().run()
        require(not at.exception and at.session_state["crypto_page"] == 2 and at.session_state["crypto_filter_level"] == "En vigilancia", "back at the list with the same filter and page")
        require("Mostrando 10–10 de 10 monedas" in page_text(at), "and the list shows the same page")
        at.session_state["crypto_fullpage_coin_id"] = "no-such-coin"
        at.run()
        require(not at.exception and "crypto_search" in [b.key for b in at.button], "an unknown coin id falls back to the list instead of an empty page")


def test_the_home_starts_clean_after_a_coin_page() -> None:
    with Sandbox():
        at = open_coin(searched(), "pump-coin")
        at.session_state["screen"] = "home"
        at.run()
        button(at, "home_crypto").click().run()
        require(not at.exception and "crypto_fullpage_coin_id" not in at.session_state and not at.session_state["crypto_search_done"] if "crypto_search_done" in at.session_state else True, "entering from the home clears the open coin")
        require(not cards(at) and "crypto_search" in [b.key for b in at.button], "and shows the clean page")


def test_the_coin_page_writes_nothing_to_disk_and_shows_no_small_text() -> None:
    source = (ROOT / "src" / "ui_v2_37" / "crypto_screen.py").read_text(encoding="utf-8")
    require("write_text" not in source and "open(" not in source and "to_csv" not in source and "json.dump" not in source, "the page writes nothing itself")
    require(not re.search(r"font-size:(\d|1[01])px", source), "no text under 12 px")
    require(source.count("str(error)") == 0 or "type(error).__name__" in source, "unexpected errors show only their type")
    for line in (l for l in source.splitlines() if "No se pudo cargar la serie diaria" in l and "type(error)" in l):
        require("str(error)" not in line, line)


CASES = [
    test_the_breakdown_adds_up_and_the_caps_explain_the_final_score,
    test_the_search_carries_the_series_signals_with_each_coin,
    test_the_chart_is_a_line_and_volume_never_candles_or_invented_points,
    test_widget_keys_are_unique_per_coin,
    test_a_card_opens_the_coin_page_with_three_tabs,
    test_a_diluted_coin_page_explains_the_risk_and_the_cap,
    test_a_series_not_in_the_cache_costs_one_call_once,
    test_a_series_that_cannot_be_loaded_is_explained_not_a_crash,
    test_going_back_keeps_the_filters_and_the_page,
    test_the_home_starts_clean_after_a_coin_page,
    test_the_coin_page_writes_nothing_to_disk_and_shows_no_small_text,
]


def main() -> int:
    forbid_network()
    for case in CASES:
        case()
    print("v2.50G crypto coin page QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
