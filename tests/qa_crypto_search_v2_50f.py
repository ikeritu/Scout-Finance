#!/usr/bin/env python3
"""QA for v2.50F, the crypto page (search PR): the pure search flow and the real app through AppTest. Everything runs against a
scripted fake CoinGecko (a patched transport, a fake key and a temporary data folder); `urllib.request.urlopen` is blocked for the
whole run, and the checks verify that the key never reaches the page, that the call budget is respected, that the attribution and
the risk note are shown, and that the results follow the approved score. No network, no real key."""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import tempfile
import urllib.request
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
logging.disable(logging.CRITICAL)

from streamlit.testing.v1 import AppTest  # noqa: E402

from src.crypto_v2_50 import coingecko as cg  # noqa: E402
from src.crypto_v2_50 import derivatives as dv  # noqa: E402
from src.crypto_v2_50 import default_paths, scoring as sc  # noqa: E402
from src.crypto_v2_50.cache import ProtectedCache  # noqa: E402
from src.crypto_v2_50.search import filter_results, paginate, run_search  # noqa: E402
from src.crypto_v2_50.usage import SAFETY_CAP, UsageCounter  # noqa: E402
from src.ui_v2_37 import crypto_screen  # noqa: E402

FAKE_KEY = "CG-FAKE-TEST-KEY-NOT-REAL-0000"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def st_cache_clear() -> None:
    import streamlit as st

    st.cache_data.clear()  # the derivatives of a coin are cached in memory for five minutes: tests must not see each other's


def forbid_network() -> None:
    def refuse(*_a, **_k):
        raise AssertionError("a test tried to open a real network connection")

    urllib.request.urlopen = refuse  # type: ignore[assignment]


# ------------------------------------------------------------------------------------------------------------------ a fake CoinGecko

def raw(coin_id: str, symbol: str, cap: float, volume: float, c7: float = 0.0, c30: float = 0.0, price: float = 1.5, circ: float = 1e6, total: float = 1e6, rank: int = 100) -> dict:
    return {"id": coin_id, "symbol": symbol, "name": coin_id.replace("-", " ").title(), "market_cap_rank": rank, "current_price": price, "market_cap": cap,
            "fully_diluted_valuation": cap * total / circ, "total_volume": volume, "circulating_supply": circ, "total_supply": total, "max_supply": None,
            "price_change_percentage_24h_in_currency": 1.0, "price_change_percentage_7d_in_currency": c7, "price_change_percentage_14d_in_currency": c7,
            "price_change_percentage_30d_in_currency": c30, "last_updated": "2026-10-19T10:00:00.000Z"}


UNIVERSE = (
    [raw("pump-coin", "pump", 20e6, 8e6, 40, 120), raw("low-coin", "lowc", 80e6, 30e6, 35, 70, price=1.0), raw("dilute-coin", "dil", 50e6, 25e6, 40, 90, circ=2e5, total=1e6),
     raw("sus-coin", "sus", 10e6, 15e6, 50, 100), raw("broken-coin", "brk", 40e6, 16e6, 40, 100), raw("tiny-coin", "tiny", 2e6, 100e3, 90, 200),
     raw("thin-coin", "thin", 50e6, 100e3, 90, 200), raw("usd-fake", "usdf", 100e6, 50e6), raw("wrapped-fake", "wfk", 60e6, 20e6)]
    + [raw(f"quiet-{i}", f"q{i}", 20e6, 1e6, rank=200 + i) for i in range(1, 9)]
)
BASELINE_VOLUME = {"pump-coin": 1e6, "low-coin": 12e6, "dilute-coin": 6e6}  # volume now / baseline = 8, 2.5, 4.2


HISTORY_DAYS: dict[str, int] = {}  # coin id -> number of completed days its fake series has (default 120); tests set and clear it
FRESH_PRICES: dict[str, float] = {}  # coin id -> the price /simple/price returns now (default: the universe's price); tests set and clear it
FRESH_PRICE_STATUS = {"code": 200}  # tests set 500 to make /simple/price fail


def daily_payload(baseline: float, days: int = 120) -> dict:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    stamps = [int((today - timedelta(days=d)).timestamp() * 1000) for d in range(days, 0, -1)] + [int((today + timedelta(hours=8)).timestamp() * 1000)]
    return {"prices": [[s, 1.0] for s in stamps], "market_caps": [[s, 1e7] for s in stamps], "total_volumes": [[s, baseline] for s in stamps]}


class FakeCoinGecko:
    def __init__(self, rate_limited: bool = False) -> None:
        self.calls: list[str] = []
        self.rate_limited = rate_limited

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        require(headers.get(cg.KEY_HEADER) == FAKE_KEY, "the key goes in the header")
        require(FAKE_KEY not in url, "and never in the URL")
        if self.rate_limited:
            return 429, {"Retry-After": "0"}, json.dumps({"status": {"error_code": 429}}).encode()
        path, _, query = url[len(cg.BASE_URL):].partition("?")
        params = parse_qs(query)
        if path == "/coins/markets":
            category = params.get("category", [None])[0]
            by_category = {"stablecoins": ["usd-fake"], "wrapped-tokens": ["wrapped-fake"], "liquid-staking": []}
            if category is not None:
                return 200, {}, json.dumps([r for r in UNIVERSE if r["id"] in by_category[category]]).encode()
            return 200, {}, json.dumps(UNIVERSE if params["page"][0] == "1" else []).encode()
        if path == "/simple/price":
            if FRESH_PRICE_STATUS["code"] != 200:
                return FRESH_PRICE_STATUS["code"], {}, b"{}"
            prices = {r["id"]: r["current_price"] for r in UNIVERSE}
            return 200, {}, json.dumps({i: {"usd": FRESH_PRICES.get(i, prices[i])} for i in params["ids"][0].split(",") if i in prices}).encode()
        match = re.match(r"/coins/([^/]+)/market_chart", path)
        if match:
            coin = match.group(1)
            if coin == "broken-coin":
                return 404, {}, json.dumps({"error": "coin not found"}).encode()
            return 200, {}, json.dumps(daily_payload(BASELINE_VOLUME.get(coin, 1e6), HISTORY_DAYS.get(coin, 120))).encode()
        return 404, {}, b"{}"


PERPS = [
    {"symbol": "PUMPUSDT", "markPrice": "1.5", "lastFundingRate": "-0.00020000", "nextFundingTime": 1792454400000},  # verified; negative funding
    {"symbol": "1000LOWCUSDT", "markPrice": "1000.0", "lastFundingRate": "0.00010000", "nextFundingTime": 1792454400000},  # x1000 contract, verified
    {"symbol": "DILUSDT", "markPrice": "300.0", "lastFundingRate": "0.00010000", "nextFundingTime": 1792454400000},  # same symbol, another coin: rejected
    {"symbol": "BTCUSDT_250627", "markPrice": "1.0", "lastFundingRate": "0"}, {"symbol": "ETHBTC", "markPrice": "1.0", "lastFundingRate": "0"},
]


class FakeBinance:
    """Scripted public Binance futures: the list of perpetuals and the three small calls of a coin's page."""

    def __init__(self, fail: bool = False, fail_detail: bool = False) -> None:
        self.calls: list[str] = []
        self.fail, self.fail_detail = fail, fail_detail

    def __call__(self, url, timeout):
        self.calls.append(url)
        if self.fail or (self.fail_detail and "/premiumIndex" not in url):
            return 500, {}, b"{}"
        path, _, query = url[len(dv.BASE_URL):].partition("?")
        if path == "/fapi/v1/premiumIndex":
            return 200, {}, json.dumps(PERPS).encode()
        symbol = parse_qs(query).get("symbol", ["?"])[0]
        if path == "/fapi/v1/openInterest":
            return 200, {}, json.dumps({"symbol": symbol, "openInterest": "1000000", "time": 1792440384996}).encode()
        if path == "/futures/data/openInterestHist":
            return 200, {}, json.dumps([{"symbol": symbol, "sumOpenInterestValue": str(1_000_000 + i * 10_000), "timestamp": 1789862400000 + i * 86_400_000} for i in range(30)]).encode()
        if path == "/futures/data/globalLongShortAccountRatio":
            return 200, {}, json.dumps([{"symbol": symbol, "longShortRatio": str(1.0 + i / 29), "longAccount": "0.6", "shortAccount": "0.4", "timestamp": 1789862400000 + i * 86_400_000} for i in range(30)]).encode()
        return 404, {}, b"{}"


class Sandbox:
    """Temporary data folder, fake key, patched transports and an instant client. Restores everything on exit."""

    def __init__(self, key: str | None = FAKE_KEY, rate_limited: bool = False, usage_calls: int | None = None, binance_fails: bool = False, binance_detail_fails: bool = False) -> None:
        self.key, self.rate_limited, self.usage_calls = key, rate_limited, usage_calls
        self.binance_fails, self.binance_detail_fails = binance_fails, binance_detail_fails

    def __enter__(self) -> "Sandbox":
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name)
        self.saved = (os.environ.get("SCOUT_FINANCE_DATA_DIR"), os.environ.get(cg.KEY_ENV), cg.default_transport, dict(crypto_screen.CLIENT_OPTIONS), dv.default_transport)
        os.environ["SCOUT_FINANCE_DATA_DIR"] = self.tmp.name
        if self.key is None:
            os.environ.pop(cg.KEY_ENV, None)
        else:
            os.environ[cg.KEY_ENV] = self.key
        self.fake = FakeCoinGecko(self.rate_limited)
        cg.default_transport = self.fake
        self.binance = FakeBinance(self.binance_fails, self.binance_detail_fails)
        dv.default_transport = self.binance  # the real Binance is never reached: a swallowed "no network" error would hide it
        HISTORY_DAYS.clear()
        FRESH_PRICES.clear()
        FRESH_PRICE_STATUS["code"] = 200
        st_cache_clear()
        crypto_screen.CLIENT_OPTIONS.clear()
        crypto_screen.CLIENT_OPTIONS.update({"sleep": lambda s: None, "min_interval": 0.0})
        if self.usage_calls is not None:
            UsageCounter(default_paths(self.data_dir)[1]).record(self.usage_calls)
        return self

    def __exit__(self, *exc) -> None:
        data, key, transport, options, binance = self.saved
        for name, value in (("SCOUT_FINANCE_DATA_DIR", data), (cg.KEY_ENV, key)):
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        cg.default_transport = transport
        dv.default_transport = binance
        HISTORY_DAYS.clear()
        FRESH_PRICES.clear()
        FRESH_PRICE_STATUS["code"] = 200
        st_cache_clear()
        crypto_screen.CLIENT_OPTIONS.clear()
        crypto_screen.CLIENT_OPTIONS.update(options)
        self.tmp.cleanup()

    @property
    def usage(self) -> UsageCounter:
        return UsageCounter(default_paths(self.data_dir)[1])


def direct_client(box: Sandbox):
    cache_dir, usage_file = default_paths(box.data_dir)
    usage = UsageCounter(usage_file)
    return cg.CoinGeckoClient(FAKE_KEY, usage=usage, transport=box.fake, sleep=lambda s: None, min_interval=0.0), ProtectedCache(cache_dir), usage


# --------------------------------------------------------------------------------------------------------------------- the search flow

def test_the_search_flow_scores_and_reports_everything() -> None:
    with Sandbox() as box:
        client, cache, usage = direct_client(box)
        progress = []
        result = run_search(client, cache, progress=lambda d, t, label: progress.append((d, t, label)))
        s, by_id = result.summary, {r["coin_id"]: r for r in result.scored}
        require(s["universe"] == 17 and s["excluded"] == 2 and s["excluded_by"] == {"stablecoins": 1, "wrapped-tokens": 1} and s["kept"] == 15, str(s))
        require(s["gated"] == 13 and s["preselected"] == 4 and s["detail_loaded"] == 3 and s["detail_failed"] == 1 and s["detail_skipped"] == 0 and s["stopped"] is None, str(s))
        require(s["calls_used"] == 9 == usage.calls_this_month() == len(box.fake.calls), f"1 universe + 3 category pages + 4 series + 1 fresh-price call for the perpetual candidates: {s['calls_used']}")
        require(s["tiers"][sc.TIER_HIGH] == 1 and s["tiers"][sc.TIER_LOW] == 2 and s["tiers"][sc.TIER_MEDIUM] == 0 and s["tiers"][sc.TIER_WATCH] == 10 and s["tiers"][sc.TIER_NO_LIQUIDITY] == 2 and s["candidates"] == 3, str(s["tiers"]))
        require(by_id["pump-coin"]["tier"] == sc.TIER_HIGH and by_id["pump-coin"]["score"] == 90, str(by_id["pump-coin"]))
        require(by_id["low-coin"]["tier"] == sc.TIER_LOW and by_id["low-coin"]["score"] == 66, str(by_id["low-coin"]))
        dilute = by_id["dilute-coin"]
        require(dilute["tier"] == sc.TIER_LOW and dilute["score"] <= 69 and "dilución alta" in dilute["risk_flags"], f"a diluted coin tops out at the lowest tier: {dilute}")
        require("rotación sospechosa" in by_id["sus-coin"]["risk_flags"] and by_id["sus-coin"]["tier"] == sc.TIER_WATCH, str(by_id["sus-coin"]))
        require(by_id["broken-coin"]["tier"] == sc.TIER_WATCH and by_id["broken-coin"]["score"] <= 44 and "volumen relativo" in by_id["broken-coin"]["missing_signals"], "a failed series caps the coin and says what is missing")
        require(by_id["tiny-coin"]["tier"] == sc.TIER_NO_LIQUIDITY and by_id["thin-coin"]["tier"] == sc.TIER_NO_LIQUIDITY, "below the gates")
        require("usd-fake" not in by_id and "wrapped-fake" not in by_id, "excluded coins are not scored")
        order = [(sc.TIER_HIGH, sc.TIER_MEDIUM, sc.TIER_LOW, sc.TIER_WATCH, sc.TIER_NO_LIQUIDITY).index(r["tier"]) for r in result.scored]
        require(order == sorted(order) and result.scored[0]["coin_id"] == "pump-coin", "ordered by tier, then score")
        require(progress[0][2] == "lista de monedas" and progress[-1][0] == progress[-1][1] == 4, f"progress reports the start and every series: {progress}")
        calls = len(box.fake.calls)
        again = run_search(client, cache)
        require(len(box.fake.calls) == calls + 2 and again.summary["calls_used"] == 2 and again.summary["from_cache"] is True and again.summary["detail_failed"] == 1,
                "a repeated search is served from the 24 h cache; only the series that failed and the fresh prices (never cached) are asked for again")


def test_trouble_with_the_series_is_tolerated_but_a_missing_universe_is_not() -> None:
    with Sandbox(rate_limited=True) as box:
        client, cache, _ = direct_client(box)
        try:
            run_search(client, cache)
        except cg.RateLimited:
            pass
        else:
            raise AssertionError("with no universe the search must fail, not show an empty page")
    with Sandbox() as box:
        client, cache, usage = direct_client(box)
        original = box.fake.__call__

        def throttle_series(url, headers, timeout):
            if "/market_chart" in url:
                return 429, {"Retry-After": "0"}, b"{}"
            return original(url, headers, timeout)

        client._transport = throttle_series
        result = run_search(client, cache)
        s = result.summary
        require(s["stopped"] == "rate_limited" and s["detail_loaded"] == 0 and s["detail_skipped"] >= 1, f"a rate limit during the series stops them and says so: {s}")
        require(all(r["score"] <= 44 for r in result.scored if r["tier"] == sc.TIER_WATCH), "coins scored without the series stay capped")
    with Sandbox(usage_calls=SAFETY_CAP - 5) as box:
        client, cache, usage = direct_client(box)
        try:
            run_search(client, cache)
        except cg.BudgetExhausted:
            require(len(box.fake.calls) == 0, "the 8 pages of the universe are budgeted up front: with 5 calls left it refuses before spending any")
        else:
            raise AssertionError("a search started without the budget for its first stage")
    with Sandbox() as box:
        client, cache, usage = direct_client(box)
        cg.load_universe(client, cache)  # the lists are already cached: only the series cost calls
        cg.load_exclusion_sets(client, cache)
        spent = usage.calls_this_month()
        usage.record(SAFETY_CAP - spent - 2)  # two calls left for four series
        result = run_search(client, cache)
        s = result.summary
        require(s["stopped"] == "budget" and s["detail_loaded"] + s["detail_failed"] == 2 and s["detail_skipped"] == 2 and usage.calls_this_month() == SAFETY_CAP, f"the series stop when the budget is gone, and the cap is never crossed: {s}")
        require(all(r["score"] <= 44 for r in result.scored if r["tier"] == sc.TIER_WATCH and r["coin_id"] in ("sus-coin",)), "coins without their series stay capped")
    with Sandbox(usage_calls=SAFETY_CAP) as box:
        client, cache, _ = direct_client(box)
        try:
            run_search(client, cache)
        except cg.BudgetExhausted:
            require(len(box.fake.calls) == 0, "no call is made once the budget is gone")
        else:
            raise AssertionError("a search ran with no budget")


def test_filter_and_paginate_helpers() -> None:
    with Sandbox() as box:
        client, cache, _ = direct_client(box)
        scored = run_search(client, cache).scored
        require(len(filter_results(scored)) == 13 and len(filter_results(scored, level="candidates")) == 3 and len(filter_results(scored, level="watch")) == 10, "levels")
        require([r["coin_id"] for r in filter_results(scored, "PUMP")] == ["pump-coin"] and [r["coin_id"] for r in filter_results(scored, " lowc ")] == ["low-coin"], "text matches name, symbol or id, ignoring case and spaces")
        require(len(filter_results(scored, level="no_liquidity")) == 2 and len(filter_results(scored, level="all")) == 15, "no-liquidity and all")
        require(filter_results(scored, "zzz") == [], "no match is an empty list")
        rows = list(range(25))
        require(paginate(rows, 1, 9) == (rows[:9], 1, 3) and paginate(rows, 3, 9) == (rows[18:], 3, 3), "pages")
        require(paginate(rows, 99, 9)[1] == 3 and paginate(rows, -4, 9)[1] == 1 and paginate([], 5, 9) == ([], 1, 1) and paginate(rows, 1, 0)[2] == 25, "out-of-range pages are clamped, never an error")


# ------------------------------------------------------------------------------------------------------------------------- the page

def new_app() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app_v2_37.py"), default_timeout=300)
    at.run()
    return at


def button(at: AppTest, key: str):
    return next(b for b in at.button if b.key == key)


def open_crypto_page() -> AppTest:
    at = new_app()
    button(at, "home_crypto").click().run()
    require(not at.exception, f"opening the page crashed: {[e.value[:100] for e in at.exception]}")
    return at


def page_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption] + [i.value for i in at.info] + [w.value for w in at.warning] + [e.value for e in at.error]
    return "\n".join(parts)


def cards(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown if "Señales detectadas:" in m.value]


def test_home_opens_the_crypto_page_clean_with_attribution_and_risk_note() -> None:
    with Sandbox() as box:
        at = new_app()
        crypto = button(at, "home_crypto")
        require(not crypto.disabled and "Crypto" in crypto.label, f"the home button is active: {crypto.label} disabled={crypto.disabled}")
        require("Próximamente" not in page_text(at), "no 'coming soon' left on the home")
        crypto.click().run()
        require(not at.exception and at.session_state["screen"] == "crypto_unicorns", f"opens the crypto screen: {at.session_state['screen']}")
        text = page_text(at)
        require("Unicornios cripto" in " ".join(t.value for t in at.title) + text, "the page has its title")
        require('Powered by CoinGecko ↗' in text and 'target="_blank"' in text and 'rel="noopener noreferrer"' in text, "the attribution link the API terms require is shown")
        require("pueden perder casi todo su valor" in text and "no es una recomendación de compra ni una predicción" in text, "the risk note is shown")
        require(not cards(at) and "candidatas explosivas" not in text, "the page is clean until the search runs")
        require("explosive_search" not in [b.key for b in at.button] and "crypto_search" in [b.key for b in at.button], "it is the crypto page, not the stock one")
        require(len(box.fake.calls) == 0, "opening the page makes no call")
        require("Llamadas a CoinGecko este mes" in text and "0 de 8,000" in text.replace(".", ","), "the call counter is visible")
        require(any("Unicornios cripto" in r.options[i] for r in at.sidebar.radio for i in range(len(r.options))), "it is in the sidebar navigation")
        require(FAKE_KEY not in text, "the key is not on the page")


def test_without_a_key_the_page_explains_and_never_calls() -> None:
    with Sandbox(key=None) as box:
        at = open_crypto_page()
        text = page_text(at)
        require(cg.KEY_ENV in text and "Falta la clave gratuita de CoinGecko" in text, "it says which variable to set")
        require(button(at, "crypto_search").disabled, "the search button is disabled")
        require(len(box.fake.calls) == 0, "no call without a key")
        require('Powered by CoinGecko' in text, "the attribution is shown even then")


def test_a_search_shows_the_summary_and_the_cards() -> None:
    with Sandbox() as box:
        at = open_crypto_page()
        button(at, "crypto_search").click().run()
        require(not at.exception, f"the search crashed: {[e.value[:120] for e in at.exception]}")
        text = page_text(at)
        require("3 candidatas explosivas" in text and "17 monedas leídas" in text and "2 excluidas" in text and "13 con liquidez suficiente" in text, f"summary line: {text[:600]}")
        require("Esta búsqueda usó 9 llamadas" in text, "the search says how many calls it used")
        require("de 8,000" in text.replace(".", ","), "and the month's counter")
        shown = cards(at)
        require(len(shown) == 9, f"nine cards on the first page: {len(shown)}")
        require(all("/100</span>" in c and "CoinGecko ↗" in c and "Señales detectadas:" in c for c in shown), "score out of 100, CoinGecko link, signals")
        require("Candidato explosivo · alto" in shown[0] and "Pump Coin" in shown[0] and "90" in shown[0], "the best coin leads the list")
        require(any("Dilución alta" in c for c in shown) and any("Rotación sospechosa" in c for c in shown), "risk flags are shown as chips")
        require("min-height: 64px" in text, "the search button shrinks once there are results")
        require("coingecko.com/en/coins/pump-coin" in shown[0], "the link points at the verified CoinGecko id")
        require(FAKE_KEY not in text and FAKE_KEY not in json.dumps(dict(at.session_state.filtered_state), default=str), "the key is neither on the page nor in the session")
        require(len(box.fake.calls) == 9 and box.usage.calls_this_month() == 9, "nine calls, all counted")
        button(at, "crypto_search").click().run()
        require("Esta búsqueda usó 2 llamadas" in page_text(at) and len(box.fake.calls) == 11, "a second search the same day is served from the 24 h cache, except the series that failed and the fresh prices")
        require(not list(default_paths(box.data_dir)[0].glob("*.json")) and all(p.suffix == ".bin" for p in default_paths(box.data_dir)[0].glob("*")), "only encrypted files are on disk")


def test_filters_and_pagination() -> None:
    with Sandbox():
        at = open_crypto_page()
        button(at, "crypto_search").click().run()
        require("Mostrando 1–9 de 13 monedas" in page_text(at), "13 scored coins, nine per page")
        button(at, "crypto_page_next").click().run()
        # AppTest keeps the elements of the run that called st.rerun(), so the page is judged by its caption and by the leader being gone.
        require(not at.exception and "Mostrando 10–13 de 13 monedas" in page_text(at) and at.session_state["crypto_page"] == 2, "the second page")
        require(any("Quiet" in c for c in cards(at)), "the second page shows the last coins of the ordering")
        text_input = next(w for w in at.text_input if w.key == "crypto_filter_text")
        text_input.set_value("pump").run()
        require(len(cards(at)) == 1 and "Mostrando 1–1 de 1 monedas" in page_text(at), "searching by text also resets to the first page")
        text_input.set_value("zzzz").run()
        require("No hay monedas para estos filtros." in page_text(at) and not cards(at), "an empty result explains itself")
        text_input.set_value("").run()
        level = next(w for w in at.selectbox if w.key == "crypto_filter_level")
        level.set_value("Solo candidatas").run()
        require(len(cards(at)) == 3 and all("Candidato explosivo" in c for c in cards(at)), "only the candidates")
        level.set_value("Sin liquidez suficiente").run()
        require(len(cards(at)) == 2 and all("Sin liquidez suficiente" in c for c in cards(at)), "the coins below the gates are listed, not hidden")


def test_budget_and_rate_limit_failures_are_explained_not_crashed() -> None:
    with Sandbox(usage_calls=SAFETY_CAP) as box:
        at = open_crypto_page()
        button(at, "crypto_search").click().run()
        require(not at.exception and any("No hay presupuesto de llamadas suficiente" in w.value for w in at.warning), "no budget: a clear warning")
        require(len(box.fake.calls) == 0 and not cards(at), "no call and no results")
    with Sandbox(rate_limited=True) as box:
        at = open_crypto_page()
        button(at, "crypto_search").click().run()
        require(not at.exception and any("limitado el ritmo" in w.value for w in at.warning), "a rate limit: a clear warning")
        require(not cards(at), "no results shown from nothing")
        require(box.usage.calls_this_month() <= 3, f"the retries are bounded: {box.usage.calls_this_month()}")


def test_the_crypto_module_uses_legible_colours_and_never_writes_to_disk() -> None:
    from qa_explosive_visual_system_v2_49f import contrast

    tokens = {"ink": "#0f172a", "text": "#334155", "secondary": "#475569", "link": "#0f5f6b", "accent_text": "#b45309"}
    for name, colour in tokens.items():
        for surface in ("#ffffff", "#fffaf0"):
            require(contrast(colour, surface) >= 4.5, f"{name} {colour} on {surface}: {contrast(colour, surface):.2f}")
    source = (ROOT / "src" / "ui_v2_37" / "crypto_screen.py").read_text(encoding="utf-8")
    require(not re.search(r"font-size:(\d|1[01])px", source), "no text under 12 px")
    require("write_text" not in source and "open(" not in source and "to_csv" not in source and "json.dump" not in source, "the page writes nothing to disk itself")
    line = next(l for l in source.splitlines() if "La búsqueda falló" in l)
    require("type(error).__name__" in line and "str(error)" not in line and "{error}" not in line, f"an unexpected error shows only its type, never its message: {line.strip()}")


CASES = [
    test_the_search_flow_scores_and_reports_everything,
    test_trouble_with_the_series_is_tolerated_but_a_missing_universe_is_not,
    test_filter_and_paginate_helpers,
    test_home_opens_the_crypto_page_clean_with_attribution_and_risk_note,
    test_without_a_key_the_page_explains_and_never_calls,
    test_a_search_shows_the_summary_and_the_cards,
    test_filters_and_pagination,
    test_budget_and_rate_limit_failures_are_explained_not_crashed,
    test_the_crypto_module_uses_legible_colours_and_never_writes_to_disk,
]


def main() -> int:
    forbid_network()
    for case in CASES:
        case()
    print("v2.50F crypto search page QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
