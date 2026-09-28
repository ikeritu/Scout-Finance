#!/usr/bin/env python3
"""Offline QA for the v2.38BT global unicorn flag. No network, no real
licensed data -- every fixture value below is synthetic."""
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_global_unicorn_flag_v2_38bt.py"

US_FIELDS = [
    "asset_id", "ticker", "company_name", "cik", "feature_quality_status",
    "revenue_yoy_growth", "net_income_yoy_growth", "net_margin", "margin_expansion_flag", "positive_fcf_flag", "fundamental_momentum_flag",
]
EUROPE_FIELDS = [
    "asset_id", "ticker", "company_name", "feature_quality_status",
    "revenue_yoy_growth", "net_profit_yoy_growth", "growth_acceleration_flag", "margin_expansion_flag",
]


def module():
    spec = importlib.util.spec_from_file_location("build_global_unicorn_flag_v2_38bt", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def us_row(asset_id, name, revenue_growth, momentum, margin_expansion="True", positive_fcf="True", quality="FEATURES_READY", cik="") -> dict:
    return {
        "asset_id": asset_id, "ticker": asset_id, "company_name": name, "cik": cik, "feature_quality_status": quality,
        "revenue_yoy_growth": revenue_growth, "margin_expansion_flag": margin_expansion,
        "positive_fcf_flag": positive_fcf, "fundamental_momentum_flag": momentum,
    }


def europe_row(asset_id, name, revenue_growth, acceleration, margin_expansion, quality="FEATURES_READY") -> dict:
    return {
        "asset_id": asset_id, "ticker": asset_id, "company_name": name, "feature_quality_status": quality,
        "revenue_yoy_growth": revenue_growth, "growth_acceleration_flag": acceleration, "margin_expansion_flag": margin_expansion,
    }


def build_with(tmp: Path, us_original=None, us_cboe=None, us_joby=None, europe=None, caches=(None, None)):
    mod = module()
    us_original_path = tmp / "us_original.csv"
    us_cboe_path = tmp / "us_cboe.csv"
    us_joby_path = tmp / "us_joby.csv"
    europe_path = tmp / "europe.csv"
    write_csv(us_original_path, US_FIELDS, us_original or [])
    write_csv(us_cboe_path, US_FIELDS, us_cboe or [])
    write_csv(us_joby_path, US_FIELDS, us_joby or [])
    write_csv(europe_path, EUROPE_FIELDS, europe or [])
    report = mod.build(us_original_path, us_cboe_path, us_joby_path, europe_path, tmp / "out", caches[0], caches[1])
    out_rows = {r["asset_id"]: r for r in csv.DictReader((tmp / "out" / "global_unicorn_flag_v2_38bt.csv").open(encoding="utf-8"))}
    return report, out_rows


def test_us_company_with_real_momentum_flag_true_is_unicorn():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_original=[us_row("U1", "Widget Manufacturing Inc", "0.25", "True")])
    assert rows["U1"]["unicorn_status"] == "EVALUATED_UNICORN"
    assert "fundamental_momentum_flag_true" in rows["U1"]["unicorn_reason"]


def test_us_company_with_real_momentum_flag_false_is_not_unicorn_not_dropped():
    """A real, evaluated company that simply doesn't meet the bar must
    still appear with an explicit false status -- never silently
    excluded, matching this project's fail-closed discipline of always
    tracking why, never a blank omission."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_original=[us_row("U1", "Steady State Corp", "0.02", "False")])
    assert rows["U1"]["unicorn_status"] == "EVALUATED_NOT_UNICORN"


def test_insufficient_growth_data_is_a_distinct_status_not_a_silent_false():
    """A company whose growth features could never be computed at all
    (no year-over-year comparison possible) must not be labeled the same
    as one that was genuinely evaluated and did not qualify -- this
    project never conflates 'we don't know' with 'no'."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_original=[us_row("U1", "Newly Listed Co", "", "False", quality="INSUFFICIENT_FEATURE_EVIDENCE")])
    assert rows["U1"]["unicorn_status"] == "INSUFFICIENT_DATA"


def test_europe_austria_needs_all_three_real_signals_no_fcf_required():
    """Austria's pipeline never computes free-cash-flow features (v2.38AK's
    own documented scope) -- the unicorn criterion there must use only
    the three real fields Austria actually has, never silently treat a
    missing FCF flag as a pass or a fail."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), europe=[
            europe_row("U1", "STRABAG SE", "0.05", "True", "True"),
            europe_row("U2", "OMV AG", "0.05", "False", "True"),
        ])
    assert rows["U1"]["unicorn_status"] == "EVALUATED_UNICORN"
    assert rows["U2"]["unicorn_status"] == "EVALUATED_NOT_UNICORN"
    assert "no_free_cash_flow_data_available_for_austria" in rows["U1"]["unicorn_reason"]


def test_negative_revenue_growth_never_qualifies_even_with_other_flags_true():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_original=[us_row("U1", "Declining Corp", "-0.10", "False", margin_expansion="True", positive_fcf="True")])
    assert rows["U1"]["unicorn_status"] == "EVALUATED_NOT_UNICORN"
    assert "revenue_growth_not_positive" in rows["U1"]["unicorn_reason"]


def test_joby_cayman_listing_is_a_duplicate_of_the_real_us_entity_not_a_second_unicorn():
    """The Cayman-ISIN-prefixed Xetra/Cboe listing is the same real company
    (same SEC CIK) as the US SEC-reporting entity: it must count once."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_joby=[us_row("U04441", "Joby Aviation, Inc.", "0.40", "True", cik="0001819848")])
    assert rows["U04441"]["unicorn_status"] == "EVALUATED_UNICORN"
    assert rows["U37518"]["unicorn_status"] == "DUPLICATE_LISTING"
    assert "duplicate_listing_of_U04441" in rows["U37518"]["unicorn_reason"]


def test_same_sec_registrant_listed_twice_counts_as_one_unicorn():
    """Real case: AMD on NASDAQ (original population) and 'AMDd' on Cboe Europe share one CIK."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            us_original=[us_row("U00169", "Advanced Micro Devices, Inc.", "0.14", "True", cik="0000002488")],
            us_cboe=[us_row("U09882", "Advanced Micro Devices Inc", "0.14", "True", cik="2488")],
        )
    assert rows["U00169"]["unicorn_status"] == "EVALUATED_UNICORN"
    assert rows["U09882"]["unicorn_status"] == "DUPLICATE_LISTING"
    assert report["unicorn_status_counts"]["EVALUATED_UNICORN"] == 1
    assert report["duplicate_listings_marked"] == 1


def test_rows_without_cik_are_never_merged():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_original=[us_row("U1", "A Co", "0.1", "True"), us_row("U2", "B Co", "0.1", "True")])
    assert rows["U1"]["unicorn_status"] == rows["U2"]["unicorn_status"] == "EVALUATED_UNICORN"


def test_company_absent_from_every_source_file_does_not_appear_at_all():
    """No growth-feature row anywhere means no claim either way -- the
    row must be entirely absent from this output, letting the UI's join
    default it to blank, never to a computed 'not a unicorn'."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_original=[us_row("U1", "Only Company Here", "0.10", "True")])
    assert "U999_NEVER_SEEN" not in rows
    assert report["companies_with_growth_features_evaluated"] == 1


def write_submission(cache_dir: Path, cik: str, sic: str, sic_description: str, tickers: list[str], exchanges: list[str]) -> None:
    import json

    path = cache_dir / "submissions" / f"CIK{int(cik):010d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cik": cik, "sic": sic, "sicDescription": sic_description, "tickers": tickers, "exchanges": exchanges}), encoding="utf-8")


def test_sec_sic_code_and_real_us_ticker_are_carried_from_the_local_submissions_cache():
    """Financial companies are recognised by SIC (60-64), and Cboe-only rows get their real US ticker."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_cache, secondary_cache = root / "orig", root / "sec"
        write_submission(original_cache, "1", "6022", "State Commercial Banks", ["BNK"], ["Nasdaq"])
        write_submission(secondary_cache, "2", "7372", "Services-Prepackaged Software", ["PLTR"], ["Nasdaq"])
        report, rows = build_with(
            root,
            us_original=[us_row("U1", "Some Bank", "0.2", "True", cik="0000000001")],
            us_cboe=[us_row("U2", "Palantir", "0.5", "True", cik="2")],
            caches=(original_cache, secondary_cache),
        )
    require = lambda ok, msg: (_ for _ in ()).throw(AssertionError(msg)) if not ok else None
    require(rows["U1"]["is_financial_sic"] == "true" and rows["U1"]["sic_description"] == "State Commercial Banks", "bank by SIC")
    require(rows["U2"]["is_financial_sic"] == "false" and rows["U2"]["us_ticker"] == "PLTR", "software company keeps its real US ticker")
    require(report["financial_sic_unicorns"] == 1, "financial unicorns are counted in the report")


def test_real_growth_figures_are_carried_for_us_and_austria():
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(
            Path(tmp),
            us_original=[us_row("U1", "Grower", "0.25", "True")],
            europe=[europe_row("U2", "PORR AG", "0.07", "True", "True") | {"net_profit_yoy_growth": "0.18"}],
        )
    assert rows["U1"]["revenue_yoy_growth"] == "0.25"
    assert rows["U2"]["revenue_yoy_growth"] == "0.07"
    assert rows["U2"]["net_income_yoy_growth"] == "0.18"  # Austria names it net_profit_yoy_growth


CASES = [
    test_us_company_with_real_momentum_flag_true_is_unicorn,
    test_us_company_with_real_momentum_flag_false_is_not_unicorn_not_dropped,
    test_insufficient_growth_data_is_a_distinct_status_not_a_silent_false,
    test_europe_austria_needs_all_three_real_signals_no_fcf_required,
    test_negative_revenue_growth_never_qualifies_even_with_other_flags_true,
    test_joby_cayman_listing_is_a_duplicate_of_the_real_us_entity_not_a_second_unicorn,
    test_same_sec_registrant_listed_twice_counts_as_one_unicorn,
    test_rows_without_cik_are_never_merged,
    test_sec_sic_code_and_real_us_ticker_are_carried_from_the_local_submissions_cache,
    test_real_growth_figures_are_carried_for_us_and_austria,
    test_company_absent_from_every_source_file_does_not_appear_at_all,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BT-global-unicorn-flag/reuses-existing-real-flags/no-new-scoring/never-silent-false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
