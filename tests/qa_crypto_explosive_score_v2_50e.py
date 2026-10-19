#!/usr/bin/env python3
"""QA for v2.50E, the crypto explosive score v1: every approved threshold at its boundary, the gates, the caps, the risk factors,
the tiers, monotonicity, that nothing missing is invented, and that the pre-selection never leaves out a coin that could still
become a candidate (checked exhaustively over a grid). No network, no key."""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.crypto_v2_50 import scoring as sc  # noqa: E402
from src.crypto_v2_50.signals import daily_signals, finite  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def row(**over) -> dict:
    """A coin that passes the gates, is not small, has no risk flag and earns nothing by default."""
    base = {"coin_id": "x", "symbol": "X", "market_cap_usd": 200_000_000.0, "volume_24h_usd": 2_000_000.0, "change_7d_pct": 0.0, "change_30d_pct": 0.0,
            "circulating_supply": 1.0, "total_supply": 1.0, "fdv_usd": 200_000_000.0}
    return base | over


def detail(rel=1.0, breakout=False) -> dict:
    return {"rel_vol_rolling": rel, "breakout_30d": breakout}


def points(r: dict, d: dict | None = None) -> int:
    return sc.score_row(r, d if d is not None else detail())["score"]


def test_each_signal_earns_the_approved_points_at_its_boundaries() -> None:
    cap = 200_000_000.0
    # rotation = volume / cap: partial from 0.10, strong from 0.25, suspicious from 1.00
    for turnover, expected in ((0.0999, 0), (0.10, 10), (0.2499, 10), (0.25, 20), (0.999, 20)):
        require(points(row(volume_24h_usd=cap * turnover)) == expected, f"turnover {turnover}: expected {expected}, got {points(row(volume_24h_usd=cap * turnover))}")
    for rel, expected in ((1.99, 0), (2.0, 12), (2.99, 12), (3.0, 22)):
        require(points(row(), detail(rel)) == expected, f"relative volume {rel}: expected {expected}")
    for value, expected in ((24.99, 0), (25.0, 8), (59.99, 8), (60.0, 16)):
        require(points(row(change_30d_pct=value)) == expected, f"30 d momentum {value}: expected {expected}")
    for value, expected in ((14.99, 0), (15.0, 6), (29.99, 6), (30.0, 12)):
        require(points(row(change_7d_pct=value)) == expected, f"7 d momentum {value}: expected {expected}")
    require(points(row(market_cap_usd=100_000_000.0, volume_24h_usd=1_000_000.0, fdv_usd=100_000_000.0)) == 6, "small cap (<= 100 M$): 6 points")
    require(points(row(market_cap_usd=100_000_001.0, volume_24h_usd=1_000_000.0, fdv_usd=100_000_001.0)) == 0, "above 100 M$ earns no size points")
    require(points(row(), detail(2.0, True)) == 12 + sc.BREAKOUT_POINTS, "breakout with relative volume >= 2 adds 14")
    require(points(row(), detail(1.99, True)) == 0, "a breakout without relative volume >= 2 earns nothing")
    require(points(row(), detail(5.0, False)) == 22, "relative volume without a breakout earns only its own points")
    require(sc.MAX_SCORE == 20 + 22 + 16 + 12 + 14 + 6 == 90, "the maximum is 90")


def test_gates_no_data_and_the_exact_boundaries() -> None:
    require(sc.score_row(row(market_cap_usd=4_999_999.0))["tier"] == sc.TIER_NO_LIQUIDITY, "market cap under 5 M$")
    require(sc.score_row(row(volume_24h_usd=499_999.0))["tier"] == sc.TIER_NO_LIQUIDITY, "volume under 0.5 M$")
    below = sc.score_row(row(market_cap_usd=4_000_000.0, change_30d_pct=500.0), detail(9.0, True))
    require(below["score"] == 0 and below["drivers"] == [] and below["tier"] == sc.TIER_NO_LIQUIDITY, "below the gates: not scored, however good the signals look")
    at = sc.score_row(row(market_cap_usd=5_000_000.0, volume_24h_usd=500_000.0, fdv_usd=5_000_000.0))
    require(at["tier"] != sc.TIER_NO_LIQUIDITY, "exactly on the gates passes")
    for bad in ({"market_cap_usd": None}, {"volume_24h_usd": None}, {"market_cap_usd": 0.0}, {"volume_24h_usd": -1.0}, {"market_cap_usd": float("nan")}):
        require(sc.score_row(row(**bad))["tier"] == sc.TIER_NO_DATA, f"{bad}: no data")
    require(sc.passes_gates(row()) and not sc.passes_gates(row(market_cap_usd=1.0)) and not sc.passes_gates({}), "passes_gates")


def test_caps_for_missing_data_and_for_the_number_of_strong_signals() -> None:
    great = row(volume_24h_usd=100_000_000.0 * 0.5, market_cap_usd=100_000_000.0, change_30d_pct=100.0, change_7d_pct=50.0, fdv_usd=100_000_000.0)
    full = sc.score_row(great, detail(4.0, True))
    require(full["score"] == 90 and full["strong_signals"] == 5 and full["tier"] == sc.TIER_HIGH, f"all signals strong: {full}")
    no_detail = sc.score_row(great, None)
    require(no_detail["score"] <= sc.CAP_MISSING and set(no_detail["missing_signals"]) == {"volumen relativo"} and no_detail["tier"] == sc.TIER_WATCH, f"missing relative volume: {no_detail}")
    no_30d = sc.score_row(great | {"change_30d_pct": None}, detail(4.0, True))
    require(no_30d["score"] <= 44 and no_30d["missing_signals"] == ["momentum 30 d"] and no_30d["tier"] == sc.TIER_WATCH, f"missing 30 d momentum: {no_30d}")
    two = sc.score_row(row(volume_24h_usd=60_000_000.0, market_cap_usd=100_000_000.0, change_30d_pct=100.0, fdv_usd=100_000_000.0), detail(1.0))  # 2 strong
    require(two["strong_signals"] == 2 and two["score"] <= sc.CAP_FEWER_THAN_3 and two["tier"] == sc.TIER_WATCH, f"2 strong signals: {two}")
    three = sc.score_row(row(volume_24h_usd=60_000_000.0, market_cap_usd=100_000_000.0, change_30d_pct=100.0, change_7d_pct=40.0, fdv_usd=100_000_000.0), detail(1.0))
    require(three["strong_signals"] == 3 and three["score"] <= sc.CAP_EXACTLY_3, f"3 strong signals: {three}")
    four_no_breakout = sc.score_row(great, detail(4.0, False))
    require(four_no_breakout["strong_signals"] == 4 and four_no_breakout["score"] <= sc.CAP_4_WITHOUT_BREAKOUT and four_no_breakout["tier"] == sc.TIER_MEDIUM, f"4 strong without breakout: {four_no_breakout}")


def test_risk_factors_cap_the_score_and_are_shown() -> None:
    strong = dict(market_cap_usd=100_000_000.0, change_30d_pct=100.0, change_7d_pct=50.0)
    sus = sc.score_row(row(volume_24h_usd=100_000_000.0, fdv_usd=100_000_000.0, **strong), detail(4.0, True))  # turnover exactly 1.0
    require("rotación sospechosa" in sus["risk_flags"] and sus["score"] <= sc.CAP_SUSPICIOUS and sus["tier"] == sc.TIER_WATCH, f"suspicious turnover: {sus}")
    require(not any("rotación" in d for d in sus["drivers"]), "a suspicious turnover earns no rotation points")
    just_below = sc.score_row(row(volume_24h_usd=99_999_999.0, fdv_usd=100_000_000.0, **strong), detail(4.0, True))
    require("rotación sospechosa" not in just_below["risk_flags"], "0.99999 is not suspicious")
    base = dict(volume_24h_usd=50_000_000.0, **strong)
    for label, over, flagged in (("circulating/total 0.29", {"circulating_supply": 0.29, "total_supply": 1.0, "fdv_usd": 100_000_000.0}, True),
                                 ("circulating/total exactly 0.30", {"circulating_supply": 0.30, "total_supply": 1.0, "fdv_usd": 100_000_000.0}, False),
                                 ("FDV/cap exactly 3", {"circulating_supply": 1.0, "total_supply": 1.0, "fdv_usd": 300_000_000.0}, True),
                                 ("FDV/cap 2.99", {"circulating_supply": 1.0, "total_supply": 1.0, "fdv_usd": 299_000_000.0}, False),
                                 ("no supply data at all", {"circulating_supply": None, "total_supply": None, "fdv_usd": None}, False)):
        result = sc.score_row(row(**base | over), detail(4.0, True))
        require(("dilución alta" in result["risk_flags"]) is flagged, f"{label}: flagged={('dilución alta' in result['risk_flags'])}")
        if flagged:
            require(result["score"] <= sc.CAP_DILUTION and result["tier"] == sc.TIER_LOW, f"{label}: a diluted coin tops out at the lowest candidate tier, not above: {result}")
        else:
            require(result["score"] == 90 and result["tier"] == sc.TIER_HIGH, f"{label}: untouched: {result}")


def test_tiers_follow_the_stock_rules() -> None:
    medium = sc.score_row(row(volume_24h_usd=100_000_000.0 * 0.5, market_cap_usd=100_000_000.0, change_30d_pct=100.0, change_7d_pct=50.0, fdv_usd=100_000_000.0), detail(4.0, False))
    low = sc.score_row(row(volume_24h_usd=60_000_000.0, market_cap_usd=100_000_000.0, change_30d_pct=100.0, change_7d_pct=40.0, fdv_usd=100_000_000.0), detail(2.0))  # 20+12+16+12+6 = 66
    one_short = sc.score_row(row(volume_24h_usd=60_000_000.0, market_cap_usd=100_000_000.0, change_30d_pct=100.0, change_7d_pct=40.0, fdv_usd=100_000_000.0), detail(1.0))  # 54
    require(one_short["score"] == 54 and one_short["strong_signals"] == 3 and one_short["tier"] == sc.TIER_WATCH, f"54 points with 3 strong signals is still watch: {one_short}")
    watch = sc.score_row(row(change_30d_pct=30.0), detail(1.0))
    require(medium["tier"] == sc.TIER_MEDIUM and low["tier"] == sc.TIER_LOW and watch["tier"] == sc.TIER_WATCH, f"{medium['tier']} {low['tier']} {watch['tier']}")
    require(low["score"] >= 55 and low["strong_signals"] >= 3, "the lowest candidate tier needs 55 points and 3 strong signals")
    for result in (medium, low, watch):
        require(result["guardrail_text"] == "No es una recomendación financiera ni predice rentabilidad.", "the guardrail text is always attached")
    require([sc.tier_label(t) for t in (sc.TIER_HIGH, sc.TIER_NO_LIQUIDITY, "weird")] == ["Candidato explosivo · alto", "Sin liquidez suficiente", "weird"], "tier labels")


def test_the_score_never_decreases_when_a_signal_improves_and_never_invents_data() -> None:
    def monotone(values, make):
        previous = -1
        for value in values:
            current = points(*make(value))
            require(current >= previous, f"the score fell from {previous} to {current} at {value}")
            previous = current
    monotone([0, 5, 15, 25, 40, 60, 100], lambda v: (row(change_30d_pct=v), detail(2.5, True)))
    monotone([0, 5, 15, 25, 30, 60], lambda v: (row(change_7d_pct=v, change_30d_pct=70.0), detail(3.0, True)))
    monotone([0.5, 1.0, 1.99, 2.0, 2.5, 3.0, 9.0], lambda v: (row(change_30d_pct=70.0, change_7d_pct=40.0), detail(v, True)))
    monotone([0.02, 0.1, 0.2, 0.25, 0.5, 0.99], lambda v: (row(volume_24h_usd=200_000_000.0 * v, change_30d_pct=70.0), detail(3.0, True)))
    unknown = sc.score_row(row(change_30d_pct=None, change_7d_pct=None), {"rel_vol_rolling": None, "breakout_30d": None})
    require(unknown["score"] == 0 and set(unknown["missing_signals"]) == {"volumen relativo", "momentum 30 d"}, f"nothing is filled in: {unknown}")
    nan = sc.score_row(row(change_30d_pct=float("nan"), change_7d_pct=float("inf")), {"rel_vol_rolling": float("nan"), "breakout_30d": True})
    require(nan["score"] == 0 and nan["tier"] == sc.TIER_WATCH, "NaN and infinite values earn nothing")
    require(sc.score_row(row(), {"rel_vol_rolling": 9.0, "breakout_30d": "yes"})["score"] == 22, "only a real True counts as a breakout")


def test_the_preselection_never_leaves_out_a_coin_that_could_become_a_candidate() -> None:
    caps = (4e6, 6e6, 30e6, 100e6, 400e6)
    volumes = (3e5, 6e5, 2e6, 50e6, 4e8)
    c30 = (None, -10.0, 0.0, 25.0, 60.0, 150.0)
    c7 = (None, -5.0, 15.0, 30.0, 80.0)
    supply = ({"circulating_supply": 1.0, "total_supply": 1.0, "fdv_usd": None}, {"circulating_supply": 0.1, "total_supply": 1.0, "fdv_usd": None})
    details = [None] + [{"rel_vol_rolling": r, "breakout_30d": b} for r in (None, 0.5, 2.0, 3.0, 8.0) for b in (None, False, True)]
    rows, checked, candidates = [], 0, 0
    for cap, vol, a, b, s in itertools.product(caps, volumes, c30, c7, supply):
        r = row(coin_id=f"{cap}-{vol}-{a}-{b}-{s['circulating_supply']}", market_cap_usd=cap, volume_24h_usd=vol, change_30d_pct=a, change_7d_pct=b, **s)
        r["turnover_24h"] = vol / cap
        rows.append(r)
    pool_ids = {r["coin_id"] for r in sc.preselect(rows, limit=10**9)}
    for r in rows:
        for d in details:
            checked += 1
            tier = sc.score_row(r, d)["tier"]
            if tier in (sc.TIER_LOW, sc.TIER_MEDIUM, sc.TIER_HIGH):
                candidates += 1
                require(r["coin_id"] in pool_ids, f"a coin that reaches {tier} was left out of the pre-selection: {r} {d}")
    require(candidates > 100, f"the grid must contain real candidates to mean anything: {candidates}")
    require(len(pool_ids) < len(rows) * 0.5, f"and the pre-selection must actually select: {len(pool_ids)} of {len(rows)}")
    ordered = sc.preselect(rows, limit=7)
    require(len(ordered) == 7 and ordered == sc.preselect(rows, limit=7), "the limit is respected and the order is deterministic")
    require(all(sc.can_reach_low(r) for r in ordered), "only coins that can still reach the lowest tier")
    require(not sc.can_reach_low(row(market_cap_usd=1e6)), "a coin below the gates is never pre-selected")


def test_daily_signals_moved_to_the_package_and_ignore_nan() -> None:
    series = [{"volume_usd": 100.0, "price_usd": 10.0} for _ in range(30)] + [{"volume_usd": 300.0, "price_usd": 10.0}]
    out = daily_signals({"volume_24h_usd": 250.0, "price_usd": 10.5}, series)
    require(out["breakout_30d"] is True and out["rel_vol_last_day"] == 3.0, str(out))
    nan_row = daily_signals({"volume_24h_usd": float("nan"), "price_usd": float("nan")}, series)
    require(nan_row["rel_vol_rolling"] is None and nan_row["breakout_30d"] is None, "NaN in the row gives no signal")
    require(finite(True) is None and finite("5") == 5.0 and finite(float("inf")) is None, "finite()")


CASES = [
    test_each_signal_earns_the_approved_points_at_its_boundaries,
    test_gates_no_data_and_the_exact_boundaries,
    test_caps_for_missing_data_and_for_the_number_of_strong_signals,
    test_risk_factors_cap_the_score_and_are_shown,
    test_tiers_follow_the_stock_rules,
    test_the_score_never_decreases_when_a_signal_improves_and_never_invents_data,
    test_the_preselection_never_leaves_out_a_coin_that_could_become_a_candidate,
    test_daily_signals_moved_to_the_package_and_ignore_nan,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.50E crypto explosive score QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
