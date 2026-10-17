#!/usr/bin/env python3
"""v2.49E: compares the relative volume the explosive screen uses today with one built only from the daily bars
already in the local candle cache. Read-only and offline: it never writes market data and never calls the network.

Today's figure (set when the search runs):  Yahoo's volume of the current day / Yahoo's 3-month average volume.
  - during the US session the numerator is partial;
  - after the close the average starts to include the day that just ended, so the same data gives another ratio.
Alternative:  volume of the last COMPLETED session / mean volume of the N sessions before it (that one excluded).
  - does not depend on the time of day of the search and uses one source for numerator and denominator.

Each company is re-scored with the alternative (relative volume and the breakout flag, which is relative volume >= 2
with a 20-day change >= 20 %) to show what would change. The live scoring is NOT touched by this script.

Usage: python scripts/compare_relative_volume_v2_49e.py [--window 60] [--markdown PATH]
The local data folder is data/, or SCOUT_FINANCE_DATA_DIR when set.
"""
from __future__ import annotations

import argparse
import logging
import sys
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import pandas as pd  # noqa: E402

import app_v2_37 as app  # noqa: E402

CUTS = (2.0, 3.0)  # the relative-volume thresholds the score uses


def alternative_relative_volume(volumes: pd.Series, window: int) -> float | None:
    values = pd.to_numeric(volumes, errors="coerce").dropna()
    if len(values) < window + 1:
        return None
    baseline = float(values.iloc[-(window + 1):-1].mean())
    return float(values.iloc[-1]) / baseline if baseline > 0 else None


def rescored(row: dict, relative_volume: float) -> dict:
    change = app.numeric_value(row.get("price_change_20d"))
    breakout = relative_volume >= 2 and change is not None and change >= 20
    return app.explosive_candidate_score(row | {"relative_volume": round(relative_volume, 2), "breakout_signal": "true" if breakout else ""})


def compare(window: int) -> dict[str, Any]:
    matrix = app.global_matrix_snapshot()
    if not matrix.available:
        raise SystemExit("The census matrix is not available locally; nothing to compare.")
    _, visible, _ = app.global_unicorn_population(matrix)
    scored = app.explosive_scored_rows(visible)
    with_data = [row for row in scored if row.get("tier") != "NO_DATA"]
    pairs, skipped = [], 0
    for row in with_data:
        current = app.numeric_value(row.get("relative_volume"))
        bars = app.load_explosive_candidate_ohlcv(row, max_sessions=400)
        alt = alternative_relative_volume(bars["Volume"], window) if not bars.empty and "Volume" in bars else None
        if current is None or alt is None:
            skipped += 1
            continue
        after = rescored(row, alt)
        pairs.append({"ticker": app.unicorn_ticker(row), "current": current, "alt": alt, "score_now": int(row["explosive_score_0_100"]), "tier_now": row["tier"],
                      "score_alt": int(after["explosive_score_0_100"]), "tier_alt": after["tier"]})
    frame = pd.DataFrame(pairs)
    result: dict[str, Any] = {"window": window, "population": len(scored), "with_market_data": len(with_data), "compared": len(frame), "skipped": skipped, "frame": frame}
    if frame.empty:
        return result
    result["spearman"] = float(frame["current"].rank().corr(frame["alt"].rank()))  # Spearman = Pearson of the ranks (no scipy needed)
    ratio = (frame["alt"] / frame["current"]).replace([float("inf")], float("nan")).dropna()
    result["ratio_quantiles"] = {q: float(ratio.quantile(q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)}
    result["cut_flips"] = {cut: int(((frame["current"] >= cut) != (frame["alt"] >= cut)).sum()) for cut in CUTS}
    result["at_or_above"] = {cut: (int((frame["current"] >= cut).sum()), int((frame["alt"] >= cut).sum())) for cut in CUTS}
    result["tier_now"] = dict(Counter(frame["tier_now"]))
    result["tier_alt"] = dict(Counter(frame["tier_alt"]))
    result["tier_changed"] = int((frame["tier_now"] != frame["tier_alt"]).sum())
    result["score_changed"] = int((frame["score_now"] != frame["score_alt"]).sum())
    result["max_score_move"] = int((frame["score_alt"] - frame["score_now"]).abs().max())
    return result


def render_markdown(result: dict[str, Any]) -> str:
    frame: pd.DataFrame = result["frame"]
    lines = [f"# Volumen relativo: cálculo actual frente a cálculo desde barras diarias (ventana {result['window']})", ""]
    lines.append(f"Población {result['population']} · con datos de mercado {result['with_market_data']} · comparables {result['compared']} · sin barras suficientes {result['skipped']}.")
    if frame.empty:
        return "\n".join(lines + ["", "No hay barras diarias suficientes en la caché local para comparar."]) + "\n"
    q = result["ratio_quantiles"]
    lines += [
        "", f"- Correlación de rangos (Spearman) entre ambos cálculos: **{result['spearman']:.3f}**.",
        f"- Cociente alternativo / actual: p5 {q[0.05]:.2f} · p25 {q[0.25]:.2f} · **mediana {q[0.5]:.2f}** · p75 {q[0.75]:.2f} · p95 {q[0.95]:.2f}.",
    ]
    for cut in CUTS:
        now, alt = result["at_or_above"][cut]
        lines.append(f"- Con volumen relativo ≥ {cut:g}: {now} empresas hoy, {alt} con el cálculo alternativo; {result['cut_flips'][cut]} cambian de lado.")
    lines += [
        f"- Puntuación distinta en {result['score_changed']} empresas (cambio máximo {result['max_score_move']} puntos); nivel distinto en {result['tier_changed']}.",
        f"- Niveles hoy: {result['tier_now']} · con el alternativo: {result['tier_alt']}.", "",
    ]
    moved = frame[(frame["tier_now"] != frame["tier_alt"]) | (frame["score_now"] != frame["score_alt"])].copy()
    moved["move"] = (moved["score_alt"] - moved["score_now"]).abs()
    moved = moved.sort_values(["move", "ticker"], ascending=[False, True]).head(12)
    if len(moved):
        lines += ["| Empresa | Vol. rel. hoy | Vol. rel. alternativo | Puntos hoy → alternativo | Nivel hoy → alternativo |", "|---|---|---|---|---|"]
        for r in moved.itertuples():
            lines.append(f"| {r.ticker} | {r.current:.2f} | {r.alt:.2f} | {r.score_now} → {r.score_alt} | {r.tier_now} → {r.tier_alt} |")
        lines.append("")
    lines.append("Solo cifras derivadas; los precios y volúmenes de origen quedan en la caché local.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--window", type=int, default=60, help="sessions in the baseline average (default 60)")
    parser.add_argument("--markdown", type=Path, help="also write the summary to this file (atomic)")
    args = parser.parse_args()
    text = render_markdown(compare(args.window))
    print(text)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.markdown.with_suffix(args.markdown.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        tmp.replace(args.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
