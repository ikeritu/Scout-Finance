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
    "asset_id", "ticker", "company_name", "feature_quality_status",
    "revenue_yoy_growth", "margin_expansion_flag", "positive_fcf_flag", "fundamental_momentum_flag",
]
EUROPE_FIELDS = [
    "asset_id", "ticker", "company_name", "feature_quality_status",
    "revenue_yoy_growth", "growth_acceleration_flag", "margin_expansion_flag",
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


def us_row(asset_id, name, revenue_growth, momentum, margin_expansion="True", positive_fcf="True", quality="FEATURES_READY") -> dict:
    return {
        "asset_id": asset_id, "ticker": asset_id, "company_name": name, "feature_quality_status": quality,
        "revenue_yoy_growth": revenue_growth, "margin_expansion_flag": margin_expansion,
        "positive_fcf_flag": positive_fcf, "fundamental_momentum_flag": momentum,
    }


def europe_row(asset_id, name, revenue_growth, acceleration, margin_expansion, quality="FEATURES_READY") -> dict:
    return {
        "asset_id": asset_id, "ticker": asset_id, "company_name": name, "feature_quality_status": quality,
        "revenue_yoy_growth": revenue_growth, "growth_acceleration_flag": acceleration, "margin_expansion_flag": margin_expansion,
    }


def build_with(tmp: Path, us_original=None, us_cboe=None, us_joby=None, europe=None):
    mod = module()
    us_original_path = tmp / "us_original.csv"
    us_cboe_path = tmp / "us_cboe.csv"
    us_joby_path = tmp / "us_joby.csv"
    europe_path = tmp / "europe.csv"
    write_csv(us_original_path, US_FIELDS, us_original or [])
    write_csv(us_cboe_path, US_FIELDS, us_cboe or [])
    write_csv(us_joby_path, US_FIELDS, us_joby or [])
    write_csv(europe_path, EUROPE_FIELDS, europe or [])
    report = mod.build(us_original_path, us_cboe_path, us_joby_path, europe_path, tmp / "out")
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


def test_joby_cayman_listing_cross_references_the_real_us_entity():
    """Same real cross-reference v2.38AL already applies for this one
    company: the Cayman-ISIN-prefixed Xetra/Cboe listing is the same real
    company as the US SEC-reporting entity, not a second, independent
    one."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_joby=[us_row("U04441", "Joby Aviation, Inc.", "0.40", "True")])
    assert rows["U04441"]["unicorn_status"] == "EVALUATED_UNICORN"
    assert rows["U37518"]["unicorn_status"] == "EVALUATED_UNICORN"
    assert "cross_referenced_from_real_us_entity" in rows["U37518"]["unicorn_reason"]


def test_company_absent_from_every_source_file_does_not_appear_at_all():
    """No growth-feature row anywhere means no claim either way -- the
    row must be entirely absent from this output, letting the UI's join
    default it to blank, never to a computed 'not a unicorn'."""
    with tempfile.TemporaryDirectory() as tmp:
        report, rows = build_with(Path(tmp), us_original=[us_row("U1", "Only Company Here", "0.10", "True")])
    assert "U999_NEVER_SEEN" not in rows
    assert report["companies_with_growth_features_evaluated"] == 1


CASES = [
    test_us_company_with_real_momentum_flag_true_is_unicorn,
    test_us_company_with_real_momentum_flag_false_is_not_unicorn_not_dropped,
    test_insufficient_growth_data_is_a_distinct_status_not_a_silent_false,
    test_europe_austria_needs_all_three_real_signals_no_fcf_required,
    test_negative_revenue_growth_never_qualifies_even_with_other_flags_true,
    test_joby_cayman_listing_cross_references_the_real_us_entity,
    test_company_absent_from_every_source_file_does_not_appear_at_all,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BT-global-unicorn-flag/reuses-existing-real-flags/no-new-scoring/never-silent-false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
