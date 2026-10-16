#!/usr/bin/env python3
"""QA for v2.49A: the explosive view is a clean page (title, short description, one big search button) and the
candidates appear only after the search has run. Executes the real app headlessly with Streamlit's AppTest and a
FAKE market provider (a stand-in `yfinance` module), so there is no network; the user's data folder is redirected to
a temporary one with SCOUT_FINANCE_DATA_DIR, and the test checks the real cache was not touched."""
from __future__ import annotations

import logging
import os
import sys
import tempfile
import types
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import pandas as pd  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

REAL_OVERLAY = ROOT / "data" / "user_explosive_unicorn_market_overlay_v2_45b.csv"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeTicker:
    created: list[str] = []
    fail = False

    def __init__(self, symbol: str) -> None:
        FakeTicker.created.append(symbol)
        if FakeTicker.fail:
            raise RuntimeError("provider unavailable")
        self.symbol = symbol
        self.fast_info = {"last_price": 2.4, "market_cap": 120_000_000, "last_volume": 900_000}

    @property
    def info(self) -> dict:
        return {"averageVolume": 300_000, "shortPercentOfFloat": 0.21, "floatShares": 9_000_000, "currentPrice": 2.4}

    def history(self, period: str = "3mo", interval: str = "1d", auto_adjust: bool = False) -> pd.DataFrame:
        days = pd.bdate_range(end="2026-10-14", periods=40, name="Date")
        close = pd.Series([2.0 + i * 0.02 for i in range(len(days))], index=days)
        return pd.DataFrame({"Open": close, "High": close + 0.1, "Low": close - 0.1, "Close": close, "Volume": 500_000}, index=days)


class Sandbox:
    """Fake provider + temporary data folder for one test."""

    def __init__(self, provider_fails: bool = False) -> None:
        self.provider_fails = provider_fails

    def __enter__(self) -> "Sandbox":
        self.tmp = tempfile.TemporaryDirectory()
        self.saved_env = os.environ.get("SCOUT_FINANCE_DATA_DIR")
        self.saved_module = sys.modules.get("yfinance")
        self.real_overlay_before = REAL_OVERLAY.stat().st_mtime_ns if REAL_OVERLAY.exists() else None
        os.environ["SCOUT_FINANCE_DATA_DIR"] = self.tmp.name
        module = types.ModuleType("yfinance")
        module.Ticker = FakeTicker
        sys.modules["yfinance"] = module
        FakeTicker.created = []
        FakeTicker.fail = self.provider_fails
        self.data_dir = Path(self.tmp.name)
        return self

    def __exit__(self, *exc) -> None:
        if self.saved_module is None:
            sys.modules.pop("yfinance", None)
        else:
            sys.modules["yfinance"] = self.saved_module
        if self.saved_env is None:
            os.environ.pop("SCOUT_FINANCE_DATA_DIR", None)
        else:
            os.environ["SCOUT_FINANCE_DATA_DIR"] = self.saved_env
        real_overlay_after = REAL_OVERLAY.stat().st_mtime_ns if REAL_OVERLAY.exists() else None
        self.tmp.cleanup()
        FakeTicker.fail = False
        require(real_overlay_after == self.real_overlay_before, "the test must never touch the user's real market cache")


def new_app() -> AppTest:
    at = AppTest.from_file(str(ROOT / "app_v2_37.py"), default_timeout=300)
    at.run()
    return at


def button(at: AppTest, key: str):
    return next(b for b in at.button if b.key == key)


def keys(at: AppTest) -> list[str]:
    return [b.key for b in at.button]


def open_explosive_page() -> AppTest:
    at = new_app()
    button(at, "home_stocks").click().run()
    require(not at.exception, f"opening the page crashed: {[e.value[:100] for e in at.exception]}")
    return at


def card_buttons(at: AppTest) -> list:
    return [b for b in at.button if (b.key or "").startswith("explosive_fullpage_select_")]


def searchable_count() -> int:
    import app_v2_37 as app

    _, visible, _ = app.global_unicorn_population(app.global_matrix_snapshot())
    return sum(1 for row in visible if app.yfinance_symbol(row))


def test_the_page_is_clean_until_the_search_runs() -> None:
    with Sandbox():
        at = open_explosive_page()
        require(at.session_state["screen"] == "global_unicorns" and at.session_state["global_unicorn_semantic_mode"] == "Unicornio explosivo", "lands on the explosive view")
        require([t.value for t in at.title] == ["Unicornios explosivos"], [t.value for t in at.title])
        require("explosive_search" in keys(at), "the big search button")
        require(button(at, "explosive_search").label == "🔎 Buscar Unicornios explosivos", button(at, "explosive_search").label)
        require(not at.metric, "no KPI row on the clean page")
        require(not card_buttons(at), "no candidate cards before searching")
        require(not any(r.label == "Tipo de descubrimiento" for r in at.radio), "the old mode radio is gone from this page")
        require("Actualizar datos reales" not in [b.label for b in at.button], "the old refresh control is behind the advanced toggle")
        require(not FakeTicker.created, "nothing is fetched until the button is pressed")


def test_search_scans_every_searchable_unicorn_and_shows_the_candidates() -> None:
    with Sandbox() as box:
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        require(not at.exception, f"the search crashed: {[e.value[:120] for e in at.exception]}")
        expected = searchable_count()
        require(expected > 100, f"sanity: expected most of the ~141 unicorns to be searchable, got {expected}")
        require(len(FakeTicker.created) == expected, f"the search must cover every searchable unicorn, not a sample: {len(FakeTicker.created)} of {expected}")
        require(any("Búsqueda terminada" in s.value for s in at.success), [s.value for s in at.success])
        require(len(card_buttons(at)) == 9, f"results show the candidate cards: {len(card_buttons(at))}")
        require("explosive_search" in keys(at), "the button stays available to search again")
        saved = pd.read_csv(box.data_dir / "user_explosive_unicorn_market_overlay_v2_45b.csv")
        require(len(saved) == expected, f"the market cache holds what was found: {len(saved)} of {expected}")


def test_results_survive_opening_and_closing_a_candidate_page() -> None:
    with Sandbox():
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        fetched = len(FakeTicker.created)
        card_buttons(at)[0].click().run()
        require(not at.exception, f"the candidate page crashed: {[e.value[:100] for e in at.exception]}")
        require([t.label for t in at.tabs] == ["Por qué puntúa así", "Ficha explosiva profesional", "Precio y velas OHLCV"], [t.label for t in at.tabs])
        # AppTest keeps the buttons of the run that called st.rerun(), so the page is judged by its heading (checked in a real browser too).
        require(not at.title, "an open candidate page shows only the candidate, not the search page header")
        require(any(b.label == "← Volver al dashboard" for b in at.button), "there is a way back")
        next(b for b in at.button if b.label == "← Volver al dashboard").click().run()
        require(not at.exception and card_buttons(at), "the results are still there after coming back")
        require(len(FakeTicker.created) == fetched, "coming back must not search again")


def test_quality_view_is_one_click_away_and_the_way_back_keeps_the_results() -> None:
    with Sandbox():
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        button(at, "explosive_to_quality").click().run()
        require(not at.exception, f"quality view crashed: {[e.value[:100] for e in at.exception]}")
        mode = next(r for r in at.radio if r.label == "Tipo de descubrimiento")
        require(mode.value == "Calidad fundamental", mode.value)
        mode.set_value("Unicornio explosivo").run()
        require(not at.exception and "explosive_search" in keys(at), "switching back lands on the explosive page")
        require(card_buttons(at), "the earlier results are still shown")


def test_a_failing_provider_is_reported_not_crashed() -> None:
    with Sandbox(provider_fails=True) as box:
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        require(not at.exception, f"a provider failure must not crash: {[e.value[:100] for e in at.exception]}")
        require(any("no obtuvo datos" in w.value for w in at.warning), [w.value for w in at.warning])
        require(not card_buttons(at), "no results without data")
        require(not (box.data_dir / "user_explosive_unicorn_market_overlay_v2_45b.csv").exists(), "nothing is saved when nothing was found")


def test_entering_from_the_home_always_starts_clean() -> None:
    with Sandbox():
        at = open_explosive_page()
        button(at, "explosive_search").click().run()
        require(card_buttons(at), "results shown")
        at.session_state["screen"] = "home"
        at.run()
        button(at, "home_stocks").click().run()
        require(not card_buttons(at) and "explosive_search" in keys(at), "a new entry from the home shows the clean page again")


def test_simple_shared_link_mode_uses_the_same_page() -> None:
    with Sandbox():
        at = AppTest.from_file(str(ROOT / "app_v2_37.py"), default_timeout=300)
        at.query_params["modo"] = "unicornios"
        at.run()
        require(not at.exception, f"simple mode crashed: {[e.value[:100] for e in at.exception]}")
        require("explosive_search" in keys(at), "the search button is there")
        require(any("Buscar Unicornios explosivos" in i.value for i in at.info), "the onboarding explains the new flow")


CASES = [
    test_the_page_is_clean_until_the_search_runs,
    test_search_scans_every_searchable_unicorn_and_shows_the_candidates,
    test_results_survive_opening_and_closing_a_candidate_page,
    test_quality_view_is_one_click_away_and_the_way_back_keeps_the_results,
    test_a_failing_provider_is_reported_not_crashed,
    test_entering_from_the_home_always_starts_clean,
    test_simple_shared_link_mode_uses_the_same_page,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49A explosive search page QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
