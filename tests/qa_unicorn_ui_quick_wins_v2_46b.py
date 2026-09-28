#!/usr/bin/env python3
"""Regression QA for the unicorn-screen UI/UX quick wins (v2.46B). Runs the real
helpers of app_v2_37.py on synthetic rows -- no network, no writes."""
from __future__ import annotations

import inspect
import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import app_v2_37 as app  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_cards_show_the_real_us_ticker_not_the_cboe_local_symbol() -> None:
    row = {"asset_id": "A", "ticker": "1PLTRm", "us_ticker": "PLTR", "exchange": "CBOE_EUROPE"}
    require(app.unicorn_ticker(row) == "PLTR", "the searchable ticker must win over the Cboe local symbol")
    require(app.unicorn_ticker({"asset_id": "B", "ticker": "MU"}) == "MU", "own ticker is kept when there is no us_ticker")
    require(app.unicorn_ticker({"asset_id": "C", "ticker": "", "us_ticker": float("nan")}) in {"C", "nan"} and app.unicorn_ticker({"asset_id": "C", "ticker": ""}) == "C", "falls back to asset_id")


def test_exchange_codes_are_readable() -> None:
    require(app.friendly_exchange("CBOE_EUROPE") == "Cboe Europe", "raw code must not reach the screen")
    require(app.friendly_exchange("XETR") == "Xetra" and app.friendly_exchange("") == "N/D" and app.friendly_exchange("OTHER") == "OTHER", "mapping/fallbacks")


def test_headline_figure_is_real_revenue_growth() -> None:
    row = {"revenue_yoy_growth": "0.692"}
    require(app.unicorn_headline_growth(row) == "+69,2 %", app.unicorn_headline_growth(row))
    require(app.unicorn_headline_growth({}) == "N/D", "missing growth stays N/D, never 0 %")
    label, value = app.unicorn_display_score({"revenue_yoy_growth": "0.15", "country": "USA"})
    require(label == "Ingresos interanual" and value == "+15,0 %", (label, value))


def test_population_medians_use_only_real_values() -> None:
    rows = [{"revenue_yoy_growth": "0.10"}, {"revenue_yoy_growth": "0.30"}, {"revenue_yoy_growth": ""}, {"revenue_yoy_growth": "0.20", "net_margin": "0.5"}]
    medians = app.unicorn_population_medians(rows)
    require(abs(medians["revenue_yoy_growth"] - 0.20) < 1e-9, medians)
    require(medians["net_margin"] == 0.5 and "net_income_yoy_growth" not in medians, "fields without data give no median")


def test_explosive_tiers_read_as_words() -> None:
    require(app.explosive_tier_label("WATCH_ONLY") == "En vigilancia" and app.explosive_tier_label("NO_DATA") == "Sin datos de mercado", "tier labels")
    require(app.explosive_tier_label("UNKNOWN_X") == "UNKNOWN_X", "unknown tiers pass through")


def test_fake_activity_and_decorative_widgets_are_gone() -> None:
    source = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
    for banned in ("Motor local analizando", "sf-live-ticker", "sf-analysis-engine", "unicorn_signal_timeline", "Radar de mercado activo",
                   "Top 3 candidatos calientes", "dropdown borroso", "Posibilidad de unicornio", "Requiere revision", "animation: sfRadarSweep", "animation: sfHotPulse"):
        require(banned not in source, f"{banned!r} must stay removed")
    require("unicorn_radar_values(selected_row)}).T" not in source, "the sum-of-constants radar bar chart must stay removed")


def test_screen_wording_is_consistent_and_accented() -> None:
    source = inspect.getsource(app.render_global_unicorns) + inspect.getsource(app.render_unicorn_visual_analytics)
    require("Cómo leer esta pantalla" in source and "Elige 2 o 3 empresas" in source, "help text collapsed / Spanish placeholder")
    require("Posibilidad" not in (ROOT / "app_v2_37.py").read_text(encoding="utf-8"), "one name for the evidence score: Confianza de clasificación")
    require(app.unicorn_evidence_grade({"eligibility_tier": "REVIEW_REQUIRED_FINANCIAL_INSTITUTION"})[0] == "Requiere revisión", "accent")


CASES = [
    test_cards_show_the_real_us_ticker_not_the_cboe_local_symbol,
    test_exchange_codes_are_readable,
    test_headline_figure_is_real_revenue_growth,
    test_population_medians_use_only_real_values,
    test_explosive_tiers_read_as_words,
    test_fake_activity_and_decorative_widgets_are_gone,
    test_screen_wording_is_consistent_and_accented,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.46B unicorn UI quick wins QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
