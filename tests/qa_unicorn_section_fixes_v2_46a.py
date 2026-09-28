#!/usr/bin/env python3
"""Regression QA for the unicorn-section bug review (v2.46A). Runs the real
functions of app_v2_37.py on synthetic rows -- no network, no writes."""
from __future__ import annotations

import ast
import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import app_v2_37 as app  # noqa: E402

NAN = float("nan")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def unicorn_row(**extra) -> dict:
    base = {
        "asset_id": "U1", "ticker": "TST", "company_name": "Test Co", "country": "USA", "exchange": "NASDAQ",
        "overall_coverage_status": "GROWTH_READY", "eligibility_tier": "ELIGIBLE_FULL", "unicorn_status": "EVALUATED_UNICORN",
        "unicorn_reason": "us_fundamental_momentum_flag_true_real_revenue_growth_and_margin_expansion_and_positive_free_cash_flow",
    }
    return base | extra


def test_note_and_review_widgets_have_a_key_per_company() -> None:
    """Bug 1: fixed keys made a note typed for company A appear (and get saved) under company B."""
    tree = ast.parse((ROOT / "app_v2_37.py").read_text(encoding="utf-8"))
    forbidden = {
        "clean_unicorn_note", "clean_unicorn_review_status", "clean_unicorn_review_note",
        "global_unicorn_detail_note", "global_unicorn_detail_review_status", "global_unicorn_detail_review_note",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"text_area", "text_input", "selectbox"}:
            for keyword in node.keywords:
                if keyword.arg == "key" and isinstance(keyword.value, ast.Constant):
                    require(keyword.value.value not in forbidden, f"fixed widget key still used: {keyword.value.value}")


def test_us_and_usa_are_the_same_country_and_europe_means_europe() -> None:
    """Bug 5."""
    require(app.normalized_country("US") == "USA" and app.normalized_country("USA") == "USA", "US must normalise to USA")
    require(app.normalized_country("AT") == "AT", "other countries must be untouched")
    require(not app.is_european_country("US") and not app.is_european_country("USA"), "US is not Europe")
    require(app.is_european_country("AT") and app.is_european_country("LU"), "AT/LU are Europe")
    require(app.is_austria("AT") and app.is_austria("Austria") and not app.is_austria("US"), "Austria detection")


def test_cboe_local_tickers_are_never_sent_to_yahoo() -> None:
    """Cboe Europe tickers (AMDd, ADBd...) are local symbols, not US tickers; the real SEC ticker is used instead."""
    require(app.yfinance_symbol(unicorn_row(ticker="AMDd", country="USA", exchange="CBOE_EUROPE")) == "", "Cboe ticker must be skipped")
    require(app.yfinance_symbol(unicorn_row(ticker="1PLTRm", country="USA", exchange="CBOE_EUROPE", us_ticker="PLTR")) == "PLTR", "real US ticker must be used")
    require(app.yfinance_symbol(unicorn_row(ticker="BRK.B", country="USA", exchange="NYSE")) == "BRK-B", "NYSE ticker must map")
    require(app.yfinance_symbol(unicorn_row(ticker="AMD", country="US", exchange="NASDAQ")) == "AMD", "US-coded NASDAQ ticker must map")


def test_eligibility_tier_names_match_v2_38bo() -> None:
    """Bug 6: the tiers really produced by v2.38BO are ELIGIBLE_FULL / REVIEW_REQUIRED_FINANCIAL_INSTITUTION."""
    full = app.unicorn_probability(unicorn_row(eligibility_tier="ELIGIBLE_FULL", overall_coverage_status="GROWTH_PARTIAL"))
    partial = app.unicorn_probability(unicorn_row(eligibility_tier="ELIGIBLE_PARTIAL_NO_PRICE", overall_coverage_status="GROWTH_PARTIAL"))
    financial = app.unicorn_probability(unicorn_row(eligibility_tier="REVIEW_REQUIRED_FINANCIAL_INSTITUTION", overall_coverage_status="GROWTH_PARTIAL"))
    require(full == partial + 3, "ELIGIBLE_FULL must add its bonus")
    require(financial == partial - 3, "review-required tiers must be penalised")
    require(app.is_review_required_tier("REVIEW_REQUIRED_FINANCIAL_INSTITUTION") and not app.is_review_required_tier("ELIGIBLE_FULL"), "tier helper")
    grade = app.unicorn_evidence_grade(unicorn_row(eligibility_tier="REVIEW_REQUIRED_FINANCIAL_INSTITUTION"))[0]
    require(grade == "Requiere revision", "a financial institution must never read as 'Muy respaldado'")
    require(app.unicorn_evidence_grade(unicorn_row())[0] == "Muy respaldado", "a clean full-coverage row keeps its grade")


def market(**fields) -> dict:
    return unicorn_row(**{"market_cap_usd": 1e9, "last_price": 50.0, **fields})


def test_large_company_with_low_share_count_is_not_a_squeeze() -> None:
    """Bug 3: Casey's-like row (22B cap, 37M shares, 3% short) was tagged 'Short squeeze'."""
    row = market(company_name="Caseys General Stores", market_cap_usd=22e9, last_price=598.0, float_shares=37e6, short_float_pct=3.0, relative_volume=0.9, price_change_20d=2.0)
    status = app.explosive_unicorn_status(row)
    require(status[0] == "DATOS_MERCADO_PARCIALES" and "squeeze" not in status[1].lower(), f"unexpected status {status}")


def test_micro_in_the_company_name_is_not_a_micro_cap() -> None:
    """Bug 3: 'Advanced Micro Devices' / 'Allegro MicroSystems' got 'Multibagger investigable'."""
    row = market(company_name="Advanced Micro Devices, Inc.", ticker="AMD", market_cap_usd=250e9, last_price=200.0)
    require("Multibagger" not in app.explosive_unicorn_status(row)[1], "name substring must not create the tag")


def test_status_and_score_never_contradict_each_other() -> None:
    """Bug 3: 25 'explosive candidates' were WATCH_ONLY in the score model."""
    weak = market(market_cap_usd=200e6, last_price=4.0, short_float_pct=16.0, relative_volume=1.0, price_change_20d=1.0, float_shares=60e6)
    strong = market(
        market_cap_usd=100e6, last_price=3.0, relative_volume=4.0, price_change_20d=50.0, float_shares=10e6,
        short_float_pct=25.0, breakout_signal="true", catalyst_note="fda approval pending",
    )
    for row in (weak, strong, market(), unicorn_row()):
        tier = app.explosive_candidate_score(row)["tier"]
        status = app.explosive_unicorn_status(row)[0]
        require((status == "EXPLOSIVE_CANDIDATE") == tier.startswith("EXPLOSIVE_CANDIDATE"), f"contradiction: {status} vs {tier}")
    require(app.explosive_candidate_score(weak)["tier"] == "WATCH_ONLY" and app.explosive_unicorn_status(weak)[0] != "EXPLOSIVE_CANDIDATE", "weak signals stay in watch")
    require(app.explosive_unicorn_status(strong)[0] == "EXPLOSIVE_CANDIDATE", "strong combined signals are candidates")


def test_empty_csv_cells_count_as_missing_not_as_data() -> None:
    """Empty overlay cells arrive as NaN: they must not print 'nan' nor hide missing critical signals."""
    require(app.is_blank(NAN) and app.is_blank("") and app.is_blank(None) and not app.is_blank(0) and not app.is_blank("x"), "is_blank")
    require(app.numeric_value(NAN) is None, "NaN must not be a number")
    row = market(relative_volume=NAN, price_change_20d=NAN, float_shares=NAN, short_float_pct=NAN, breakout_signal=NAN, catalyst_note=NAN)
    result = app.explosive_candidate_score(row)
    require({"relative_volume", "price_change_20d", "float_shares", "short_float_pct"} <= set(result["missing_signals"]), "NaN fields must be reported missing")
    frame = app.explosive_candidate_detail_frame(row | result)
    require(frame.set_index("Campo").loc["breakout_signal", "Dato"] == "N/D", "NaN must render as N/D")
    require("nan" not in app.explosive_candidate_professional_explanation(row | result).lower().replace("financ", ""), "no 'nan' text in the explanation")
    merged = app.apply_explosive_overlay([unicorn_row(asset_id="U9")], app.pd.DataFrame([{"asset_id": "U9", "ticker": "TST", "last_price": 5.0, "breakout_signal": NAN}]))
    require("breakout_signal" not in merged[0], "NaN overlay cells must not be merged into rows")


def test_provider_tag_is_not_counted_as_a_documented_catalyst() -> None:
    base = market(market_cap_usd=100e6, last_price=3.0, relative_volume=4.0, price_change_20d=50.0, float_shares=10e6, short_float_pct=25.0, breakout_signal="true")
    for tag in ("yfinance_real_market_snapshot_v2_45c", "polygon_read_only_market_cache_v2_45n"):
        require("catalizador documentado" not in app.explosive_candidate_score(base | {"catalyst_note": tag})["drivers"], f"{tag} is provenance, not a catalyst")
    require("catalizador documentado" in app.explosive_candidate_score(base | {"catalyst_note": "contrato con el DoD"})["drivers"], "a real note still counts")


def test_ranking_breaks_ties_by_real_revenue_growth_not_by_name() -> None:
    """Bug 4: 105 unicorns shared 96% and were ordered alphabetically."""
    slow = unicorn_row(asset_id="U1", company_name="AAA Slow", revenue_yoy_growth="0.05")
    fast = unicorn_row(asset_id="U2", company_name="ZZZ Fast", revenue_yoy_growth="0.80")
    unknown = unicorn_row(asset_id="U3", company_name="BBB Unknown", revenue_yoy_growth="")
    ordered = sorted([slow, unknown, fast], key=app.unicorn_internal_rank_key)
    require([r["asset_id"] for r in ordered] == ["U2", "U1", "U3"], f"unexpected order {[r['asset_id'] for r in ordered]}")
    by_sort_mode = sorted([slow, unknown, fast], key=lambda r: app.unicorn_sort_key(r, "Crecimiento de ingresos"))
    require(by_sort_mode[0]["asset_id"] == "U2" and by_sort_mode[-1]["asset_id"] == "U3", "growth sort mode")
    summary = app.unicorn_growth_summary(unicorn_row(revenue_yoy_growth="0.142", net_income_yoy_growth="-0.05", net_margin="0.098"))
    require(summary == "Ingresos +14,2 % · Beneficio -5,0 % · Margen neto 9,8 %", summary)
    require(app.unicorn_growth_summary(unicorn_row()) == "Sin cifras de crecimiento en la matriz local", "missing figures are stated, not invented")


def test_financial_companies_are_recognised_by_sec_sic_code() -> None:
    """Bug 7: the name heuristic missed 'Carter Bankshares'; the SIC code (60-64) does not."""
    bank = unicorn_row(company_name="Carter Bankshares, Inc.", eligibility_tier="ELIGIBLE_PARTIAL_NO_PRICE", is_financial_sic="true", sic_description="National Commercial Banks")
    require(app.unicorn_needs_financial_review(bank), "SIC-financial company must need review")
    grade, _, reason = app.unicorn_evidence_grade(bank)
    require(grade == "Requiere revision" and "National Commercial Banks" in reason, (grade, reason))
    require(not app.unicorn_needs_financial_review(unicorn_row(is_financial_sic="false")), "industrial company is not flagged")


def test_ohlcv_bars_from_yahoo_are_cached_and_drawn() -> None:
    """Bug 9: v2.38I files hold only close/volume, so candles could never render."""
    import tempfile

    dates = app.pd.date_range("2026-06-01", periods=30, freq="B", tz="America/New_York")
    history = app.pd.DataFrame({"Open": range(10, 40), "High": range(11, 41), "Low": range(9, 39), "Close": range(10, 40), "Volume": [1000] * 30}, index=dates)
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp)
        require(app.save_explosive_ohlcv({"asset_id": "U77", "ticker": "TST"}, history, cache), "bars must be saved")
        require(not list(cache.glob("*.tmp")), "no stray temp file")
        original_roots = app.EXPLOSIVE_OHLCV_LOCAL_ROOTS
        app.EXPLOSIVE_OHLCV_LOCAL_ROOTS = [cache]
        try:
            loaded = app.load_explosive_candidate_ohlcv({"asset_id": "U77", "ticker": "TST"})
        finally:
            app.EXPLOSIVE_OHLCV_LOCAL_ROOTS = original_roots
        require(len(loaded) == 30 and {"Open", "High", "Low", "Close"} <= set(loaded.columns), "cached bars must load as OHLCV")
        require(not app.save_explosive_ohlcv({"asset_id": "U78"}, app.pd.DataFrame({"Close": [1.0]}), cache), "close-only history is never turned into fake candles")


def test_refreshing_one_provider_keeps_the_rest_of_the_market_cache() -> None:
    """A Polygon refresh used to replace the whole cache (and vice versa)."""
    pd = app.pd
    old = pd.DataFrame([
        {"asset_id": "U1", "ticker": "AAA", "last_price": 1.0, "catalyst_note": "yfinance_real_market_snapshot_v2_45c"},
        {"asset_id": "U2", "ticker": "BBB", "last_price": 2.0, "catalyst_note": "yfinance_real_market_snapshot_v2_45c"},
    ])
    fresh = pd.DataFrame([
        {"asset_id": "U1", "ticker": "AAA", "last_price": 9.0, "catalyst_note": "polygon_read_only_market_cache_v2_45n"},
        {"asset_id": "U2", "ticker": "BBB", "last_price": 3.0, "catalyst_note": "yfinance_real_market_snapshot_v2_45c"},
    ])
    merged = app.merge_explosive_overlay(old, fresh)
    keys = sorted((r["asset_id"], app.provider_from_overlay_note(r["catalyst_note"]), r["last_price"]) for r in merged.to_dict("records"))
    require(keys == [("U1", "polygon", 9.0), ("U1", "yfinance", 1.0), ("U2", "yfinance", 3.0)], keys)
    require(app.merge_explosive_overlay(pd.DataFrame(), fresh).equals(fresh), "empty cache returns the fresh rows")


def test_notes_are_written_atomically_and_a_damaged_file_is_set_aside() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "notes.json"
        app.atomic_write_json(path, {"U1": "nota"})
        require(app.load_json_dict(path) == {"U1": "nota"} and not list(Path(tmp).glob("*.tmp")), "atomic round trip")
        path.write_text("{ not json", encoding="utf-8")
        require(app.load_json_dict(path) == {}, "damaged file reads as empty")
        require(not path.exists() and list(Path(tmp).glob("notes.json.corrupt-*")), "the damaged file is kept for recovery, not overwritten")


def test_ca_bundle_path_with_emoji_is_copied_to_an_ascii_path_for_yfinance() -> None:
    """Live finding: curl_cffi encodes the CA path as cp1252, so a project folder with an emoji broke every yfinance request."""
    import os
    import tempfile

    import certifi

    original_where, original_env = certifi.where, os.environ.get("SSL_CERT_FILE")
    with tempfile.TemporaryDirectory() as tmp:
        emoji_dir = Path(tmp) / "\U0001f4b0 carpeta"
        emoji_dir.mkdir()
        fake_pem = emoji_dir / "cacert.pem"
        fake_pem.write_text("-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n", encoding="utf-8")
        certifi.where = lambda: str(fake_pem)
        try:
            result = app.ensure_ascii_ca_bundle()
            result.encode("cp1252")  # must not raise
            require(Path(result).read_text(encoding="utf-8") == fake_pem.read_text(encoding="utf-8"), "the copy must be identical")
            require(os.environ.get("SSL_CERT_FILE") == result, "SSL_CERT_FILE must point to the ASCII copy")
            certifi.where = original_where
            plain = app.ensure_ascii_ca_bundle()
            require(plain == original_where() or plain.encode("cp1252") is not None, "a normal path is returned untouched or safely copied")
        finally:
            certifi.where = original_where
            if original_env is None:
                os.environ.pop("SSL_CERT_FILE", None)
            else:
                os.environ["SSL_CERT_FILE"] = original_env


def test_candlestick_figure_is_really_built_with_plotly() -> None:
    """Live finding: once OHLCV data existed, `go.Figure` failed because the navigation helper go() shadowed plotly's `go`."""
    dates = app.pd.date_range("2026-06-01", periods=40, freq="B")
    closes = [10 + i * 0.5 + (i % 3) for i in range(40)]
    ohlcv = app.pd.DataFrame({
        "Date": dates, "Open": closes, "High": [c + 1 for c in closes], "Low": [c - 1 for c in closes],
        "Close": closes, "Volume": [1000 + i for i in range(40)],
    })
    figure = app.explosive_candlestick_figure(ohlcv, "TST · velas locales")
    kinds = [trace.type for trace in figure.data]
    require("candlestick" in kinds and "bar" in kinds and kinds.count("scatter") == 3, f"unexpected traces {kinds}")
    require(callable(app.go) and not hasattr(app.go, "Figure"), "go() must stay the navigation helper")


def test_every_plotly_chart_has_a_unique_key() -> None:
    """Live finding: the featured candlestick and the same company's card chart shared one auto-generated id."""
    import inspect

    source = inspect.getsource(app.render_explosive_candidate_candlestick)
    require("key=f\"{key_prefix}_" in source, "candlestick chart must be keyed")
    require("explosive_candles_featured" in inspect.getsource(app.render_featured_explosive_candlestick), "featured chart uses its own prefix")
    require(inspect.signature(app.render_explosive_candidate_candlestick).parameters["key_prefix"].default == "explosive_candles_card", "cards use the default prefix")


CASES = [
    test_note_and_review_widgets_have_a_key_per_company,
    test_us_and_usa_are_the_same_country_and_europe_means_europe,
    test_cboe_local_tickers_are_never_sent_to_yahoo,
    test_eligibility_tier_names_match_v2_38bo,
    test_large_company_with_low_share_count_is_not_a_squeeze,
    test_micro_in_the_company_name_is_not_a_micro_cap,
    test_status_and_score_never_contradict_each_other,
    test_empty_csv_cells_count_as_missing_not_as_data,
    test_provider_tag_is_not_counted_as_a_documented_catalyst,
    test_ranking_breaks_ties_by_real_revenue_growth_not_by_name,
    test_financial_companies_are_recognised_by_sec_sic_code,
    test_ohlcv_bars_from_yahoo_are_cached_and_drawn,
    test_refreshing_one_provider_keeps_the_rest_of_the_market_cache,
    test_notes_are_written_atomically_and_a_damaged_file_is_set_aside,
    test_ca_bundle_path_with_emoji_is_copied_to_an_ascii_path_for_yfinance,
    test_candlestick_figure_is_really_built_with_plotly,
    test_every_plotly_chart_has_a_unique_key,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.46A unicorn section fixes QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
