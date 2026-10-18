#!/usr/bin/env python3
"""QA for v2.49A/v2.49B: the explosive view is a clean page (title, short description, one big search button) and the
candidates appear only after the search has run. Executes the real app headlessly with Streamlit's AppTest and a
FAKE market provider (a stand-in `yfinance` module), so there is no network; the user's data folder is redirected to
a temporary one with SCOUT_FINANCE_DATA_DIR, and the test checks the real cache was not touched."""
from __future__ import annotations

import logging
import os
import re
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



def _tolerate_stale_checkbox() -> None:
    """AppTest keeps the chart switch of a page that is no longer drawn (the real app drops it), and reading its state raises
    KeyError on the next run. Read such a switch as its default so the tests can move between pages."""
    from streamlit.proto.WidgetStates_pb2 import WidgetState
    from streamlit.testing.v1 import element_tree

    def state(self):
        ws = WidgetState()
        ws.id = self.id
        try:
            ws.bool_value = self.value
        except KeyError:
            ws.bool_value = bool(getattr(self.proto, "default", False))
        return ws

    element_tree.Checkbox._widget_state = property(state)


_tolerate_stale_checkbox()
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
        self.saved_now = os.environ.get("SCOUT_FINANCE_FAKE_NOW_UTC")
        self.saved_module = sys.modules.get("yfinance")
        self.real_overlay_before = REAL_OVERLAY.stat().st_mtime_ns if REAL_OVERLAY.exists() else None
        os.environ["SCOUT_FINANCE_DATA_DIR"] = self.tmp.name
        os.environ["SCOUT_FINANCE_FAKE_NOW_UTC"] = "2026-10-17T12:00:00+00:00"  # a Saturday: the market is closed whenever the QA runs
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
        if self.saved_now is None:
            os.environ.pop("SCOUT_FINANCE_FAKE_NOW_UTC", None)
        else:
            os.environ["SCOUT_FINANCE_FAKE_NOW_UTC"] = self.saved_now
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
        require([t.label for t in at.tabs] == ["Resumen", "Datos", "Gráfico"], [t.label for t in at.tabs])
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


def captions(at: AppTest) -> list[str]:
    return [c.value for c in at.caption]


def showing(at: AppTest) -> str:
    return next((c for c in captions(at) if c.startswith("Mostrando ")), "")


def widget(items, key: str):
    return next(w for w in items if w.key == key)


def searched_page() -> AppTest:
    at = open_explosive_page()
    button(at, "explosive_search").click().run()
    require(not at.exception, f"the search crashed: {[e.value[:100] for e in at.exception]}")
    return at


def test_scope_is_stated_before_searching() -> None:
    with Sandbox():
        at = open_explosive_page()
        scope = next((c for c in captions(at) if c.startswith("Alcance:")), "")
        require("que ya cumplen el criterio de calidad fundamental" in scope and "no recorre las" in scope, scope or captions(at))
        require("entidades financieras" in scope, "it says the financial institutions are left out: " + scope)


def test_results_are_paginated_and_the_count_matches_the_cards() -> None:
    with Sandbox():
        at = searched_page()
        first = showing(at)
        require(first.startswith("Mostrando 1–9 de "), first)
        total = int(first.split(" de ")[1].split(" ")[0].replace(",", ""))
        require(total > 100 and len(card_buttons(at)) == 9, f"{total} found, {len(card_buttons(at))} cards")
        require(any("Página 1 de" in m.value for m in at.markdown), "the page indicator")
        button(at, "explosive_page_next").click().run()
        require(showing(at).startswith("Mostrando 10–18 de ") and len(card_buttons(at)) == 9, showing(at))
        button(at, "explosive_page_prev").click().run()
        require(showing(at).startswith("Mostrando 1–9 de "), showing(at))
        widget(at.selectbox, "explosive_dashboard_cards").set_value(24).run()
        require(showing(at).startswith("Mostrando 1–24 de ") and len(card_buttons(at)) == 24, f"{showing(at)} / {len(card_buttons(at))} cards")
        last_pages = (total + 23) // 24
        for _ in range(last_pages - 1):
            button(at, "explosive_page_next").click().run()
        require(button(at, "explosive_page_next").disabled, "the last page has no next")
        last_start = (last_pages - 1) * 24 + 1
        require(showing(at).startswith(f"Mostrando {last_start}–{total} de "), showing(at))


def test_any_company_can_be_found_by_name_or_ticker() -> None:
    import app_v2_37 as app

    with Sandbox():
        at = searched_page()
        _, visible, _ = app.global_unicorn_population(app.global_matrix_snapshot())
        needle = "pltr"
        expected = sum(1 for r in visible if any(needle in str(r.get(k, "")).casefold() for k in ("company_name", "ticker", "us_ticker", "asset_id")))
        require(expected >= 1, "sanity: the fixture population has Palantir")
        widget(at.text_input, "explosive_dashboard_search").set_value("PLTR").run()
        require(not at.exception, f"search crashed: {[e.value[:100] for e in at.exception]}")
        require(showing(at).startswith(f"Mostrando 1–{expected} de {expected} "), showing(at))
        require(len(card_buttons(at)) == expected, f"{len(card_buttons(at))} cards for {expected} matches")
        widget(at.button, "explosive_reset_filters").click().run()
        require(widget(at.text_input, "explosive_dashboard_search").value == "" and showing(at).startswith("Mostrando 1–9 de "), "Restablecer clears the search")
        widget(at.text_input, "explosive_dashboard_search").set_value("PLTR").run()
        card_buttons(at)[0].click().run()
        require([t.label for t in at.tabs][0] == "Resumen", "a company found by ticker opens its own page")
        require(at.session_state["saved_explosive_dashboard_search"] == "PLTR", "the search text is mirrored while its page is open")


def test_empty_result_explains_itself_and_offers_a_reset() -> None:
    with Sandbox():
        at = searched_page()
        widget(at.text_input, "explosive_dashboard_search").set_value("zzzzqqqq").run()
        require(not at.exception, f"crashed: {[e.value[:100] for e in at.exception]}")
        require(any("No hay resultados para estos filtros." in i.value for i in at.info), [i.value for i in at.info])
        require(not card_buttons(at), "no cards for an empty result")
        widget(at.button, "explosive_reset_filters_empty").click().run()
        require(len(card_buttons(at)) == 9, "Restablecer brings the companies back")


def test_page_and_filters_are_kept_while_a_candidate_page_is_open() -> None:
    """AppTest keeps the widgets of the run that called st.rerun(), so it cannot judge the way BACK; that was verified in a
    real browser (page 2, a typed search and a filter all came back). Here: what must be in the state while the page is open."""
    with Sandbox():
        at = searched_page()
        widget(at.selectbox, "explosive_dashboard_tier_filter").set_value("LOW+").run()
        button(at, "explosive_page_next").click().run()
        require(showing(at).startswith("Mostrando 10–18 de "), showing(at))
        card_buttons(at)[0].click().run()
        require(not at.exception, f"the candidate page crashed: {[e.value[:100] for e in at.exception]}")
        require(at.session_state["explosive_dashboard_page"] == 2, "the page number is kept")
        require(at.session_state["explosive_dashboard_tier_filter"] == "LOW+" and at.session_state["saved_explosive_dashboard_tier_filter"] == "LOW+", "the level filter is kept and mirrored")


def test_no_podium_and_the_threshold_is_stated_in_the_summary() -> None:
    with Sandbox():
        at = searched_page()
        html = " ".join(m.value for m in at.markdown)
        require("Top 3" not in html, "no podium on the results page")
        if re.search(r"(?<![\d,])0 candidatos explosivos", html):
            require("Ninguna supera el umbral explosivo" in html, "with 0 candidates the summary line says none passes the threshold")


def visible_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption] + [w.value for w in at.warning] + [i.value for i in at.info] + [x.value for x in at.success]
    return "\n".join(parts)


def test_the_numbers_say_what_they_mean_and_where_they_come_from() -> None:
    with Sandbox():
        at = open_explosive_page()
        scope = next((c for c in captions(at) if c.startswith("Alcance:")), "")
        require("Cálculo fundamental del 20" in scope, "the fundamental-calculation date is stated next to the scope: " + scope)
        button(at, "explosive_search").click().run()
        text = visible_text(at)
        require("cumplen el umbral" in text and "en vigilancia" in text and "sin datos suficientes" in text, "the summary spells out the three groups in words")
        require("Datos de mercado: Yahoo Finance, guardados el 20" in text, "the market data states its source and when it was saved, separately from the fundamental date")
        for old in (">High<", ">Medium<", ">Low<", ">Watch<"):
            require(old not in text, f"raw tier name {old} must not reach the screen")
        require("### Empresas por revisar" in text and "Dashboard de candidatos" not in text, "the list is named for what it is")
        require("Señales detectadas:" in text and "Drivers:" not in text, "cards use plain wording")


def test_no_internal_vocabulary_reaches_the_results_or_the_candidate_page() -> None:
    banned = ("fail-closed", "non_polygon_overlay", "v2.45G", "WATCH_ONLY", "contrato v2", "Drivers principales")
    with Sandbox():
        at = searched_page()
        text = visible_text(at)
        for word in banned:
            require(word not in text, f"{word!r} is internal vocabulary and must not appear on the results page")
        card_buttons(at)[0].click().run()
        require(not at.exception, f"candidate page crashed: {[e.value[:100] for e in at.exception]}")
        text = visible_text(at)
        for word in banned:
            require(word not in text, f"{word!r} must not appear on the candidate page")
        require("Señales detectadas" in text, "the first tab uses the plain heading")


CASES = [
    test_the_page_is_clean_until_the_search_runs,
    test_search_scans_every_searchable_unicorn_and_shows_the_candidates,
    test_results_survive_opening_and_closing_a_candidate_page,
    test_quality_view_is_one_click_away_and_the_way_back_keeps_the_results,
    test_a_failing_provider_is_reported_not_crashed,
    test_entering_from_the_home_always_starts_clean,
    test_simple_shared_link_mode_uses_the_same_page,
    test_scope_is_stated_before_searching,
    test_results_are_paginated_and_the_count_matches_the_cards,
    test_any_company_can_be_found_by_name_or_ticker,
    test_empty_result_explains_itself_and_offers_a_reset,
    test_page_and_filters_are_kept_while_a_candidate_page_is_open,
    test_no_podium_and_the_threshold_is_stated_in_the_summary,
    test_the_numbers_say_what_they_mean_and_where_they_come_from,
    test_no_internal_vocabulary_reaches_the_results_or_the_candidate_page,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.49A explosive search page QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
