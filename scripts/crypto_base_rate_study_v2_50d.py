#!/usr/bin/env python3
"""v2.50D: descriptive study of how the explosive signals of the crypto score distribute over the real universe, to choose thresholds
on evidence instead of by feel. It describes; it does not predict anything and it says nothing about future returns.

What it does: loads the ~2,000-coin universe and the exclusion sets through the v2.50C data layer (cached, encrypted, counted),
takes a stratified sample for the daily-series signals (volume against its own 30-day average, breakout), and prints how many
coins each candidate threshold would pass. Only AGGREGATES go to the optional markdown file: no per-coin figures are written, in
line with CoinGecko's terms on storing its data.

Usage: python scripts/crypto_base_rate_study_v2_50d.py [--sample 120] [--markdown PATH]
Needs SCOUT_FINANCE_COINGECKO_API_KEY. The data folder is data/, or SCOUT_FINANCE_DATA_DIR when set.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.crypto_v2_50 import default_paths  # noqa: E402
from src.crypto_v2_50.cache import ProtectedCache  # noqa: E402
from src.crypto_v2_50.signals import daily_signals  # noqa: E402,F401  (the definitions live in the package since v2.50E)
from src.crypto_v2_50.coingecko import CoinGeckoClient, apply_exclusions, load_daily_series, load_exclusion_sets, load_universe  # noqa: E402
from src.crypto_v2_50.usage import UsageCounter  # noqa: E402

BANDS = [("≥ 1.000 M$", 1e9, float("inf")), ("300 M$ – 1.000 M$", 3e8, 1e9), ("100 – 300 M$", 1e8, 3e8), ("30 – 100 M$", 3e7, 1e8), ("5 – 30 M$", 5e6, 3e7), ("< 5 M$", 0, 5e6)]
SAMPLE_BANDS = BANDS[:5]  # coins under 5 M$ are below the liquidity floor under study and are not sampled for detail


def pct(part: int, whole: int) -> str:
    return f"{part:,} ({100 * part / whole:.1f} %)" if whole else "0"


def quantiles(series: pd.Series) -> str:
    s = series.dropna()
    if s.empty:
        return "sin datos"
    q = s.quantile([0.1, 0.25, 0.5, 0.75, 0.9, 0.99])
    return " · ".join(f"p{int(k * 100)} {v:,.2f}" for k, v in q.items())


def stratified_sample(frame: pd.DataFrame, per_band: int) -> pd.DataFrame:
    """Deterministic: in each market-cap band, coins spaced evenly by rank (no randomness, so the study is reproducible)."""
    parts = []
    for _, low, high in SAMPLE_BANDS:
        band = frame[(frame["market_cap_usd"] >= low) & (frame["market_cap_usd"] < high)].sort_values("market_cap_usd", ascending=False)
        if len(band) <= per_band:
            parts.append(band)
        else:
            step = len(band) / per_band
            parts.append(band.iloc[[int(i * step) for i in range(per_band)]])
    return pd.concat(parts) if parts else frame.iloc[0:0]


def study(sample_size: int) -> dict:
    data_dir = Path(os.environ.get("SCOUT_FINANCE_DATA_DIR") or ROOT / "data")
    cache_dir, usage_file = default_paths(data_dir)
    usage = UsageCounter(usage_file)
    cache = ProtectedCache(cache_dir)
    client = CoinGeckoClient(usage=usage)
    before = usage.calls_this_month()
    universe = load_universe(client, cache)
    exclusions = load_exclusion_sets(client, cache)
    kept, excluded = apply_exclusions(universe.data, exclusions.data)
    frame = pd.DataFrame(kept)
    result = {"universe": len(universe.data), "from_cache": universe.from_cache, "fetched_at": universe.fetched_at, "excluded": len(excluded),
              "excluded_by": Counter(c for row in excluded for c in row["excluded_by"]), "kept": frame, "sample_details": []}
    per_band = max(1, sample_size // len(SAMPLE_BANDS))
    sample = stratified_sample(frame, per_band)
    details = []
    for _, row in sample.iterrows():
        series = load_daily_series(client, cache, row["coin_id"]).data
        details.append(row.to_dict() | daily_signals(row, series))
    result["sample"] = pd.DataFrame(details)
    result["calls_used"] = usage.calls_this_month() - before
    result["usage"] = usage.status()
    return result


def section_universe(r: dict) -> list[str]:
    kept: pd.DataFrame = r["kept"]
    n = len(kept)
    lines = [f"Universo leído: **{r['universe']:,}** monedas (datos de CoinGecko del {r['fetched_at']:%Y-%m-%d %H:%M} UTC{' · de la caché' if r['from_cache'] else ''}). "
             f"Excluidas por categoría: **{r['excluded']:,}** ({100 * r['excluded'] / r['universe']:.1f} %) — "
             + ", ".join(f"{k}: {v:,}" for k, v in sorted(r["excluded_by"].items())) + " (una moneda puede estar en más de una). "
             f"Quedan **{n:,}**.", "", "### Composición por capitalización (monedas no excluidas)", "", "| Banda | Monedas |", "|---|---|"]
    for label, low, high in BANDS:
        lines.append(f"| {label} | {pct(int(((kept['market_cap_usd'] >= low) & (kept['market_cap_usd'] < high)).sum()), n)} |")
    missing = int(kept["market_cap_usd"].isna().sum())
    lines += ["", f"Sin capitalización utilizable: {missing:,}.", ""]
    return lines


def section_markets_only(r: dict) -> list[str]:
    kept: pd.DataFrame = r["kept"]
    f = kept[kept["market_cap_usd"].notna()]
    n = len(f)
    lines = ["## A. Señales que salen solo de `/coins/markets` (todas las monedas no excluidas con capitalización)", "",
             f"Base: **{n:,}** monedas.", "", "### Distribuciones", "",
             f"- Capitalización (M$): {quantiles(f['market_cap_usd'] / 1e6)}",
             f"- Volumen 24 h (M$): {quantiles(f['volume_24h_usd'] / 1e6)}",
             f"- Rotación (volumen 24 h / capitalización): {quantiles(f['turnover_24h'])}",
             f"- Cambio 7 d (%): {quantiles(f['change_7d_pct'])}", f"- Cambio 14 d (%): {quantiles(f['change_14d_pct'])}", f"- Cambio 30 d (%): {quantiles(f['change_30d_pct'])}", ""]
    lines += ["### Cuántas monedas pasa cada umbral candidato", "", "| Señal | Umbral | Monedas que lo cumplen |", "|---|---|---|"]
    for label, mask, text in [
        ("Capitalización pequeña", f["market_cap_usd"] <= 5e7, "≤ 50 M$"), ("Capitalización pequeña", f["market_cap_usd"] <= 1e8, "≤ 100 M$"),
        ("Capitalización pequeña", f["market_cap_usd"] <= 5e8, "≤ 500 M$"),
        ("Liquidez mínima (suelo)", f["volume_24h_usd"] >= 1e5, "volumen 24 h ≥ 0,1 M$"), ("Liquidez mínima (suelo)", f["volume_24h_usd"] >= 5e5, "volumen 24 h ≥ 0,5 M$"),
        ("Liquidez mínima (suelo)", f["volume_24h_usd"] >= 1e6, "volumen 24 h ≥ 1 M$"),
        ("Rotación", f["turnover_24h"] >= 0.1, "≥ 0,10"), ("Rotación", f["turnover_24h"] >= 0.25, "≥ 0,25"), ("Rotación", f["turnover_24h"] >= 0.5, "≥ 0,50"),
        ("Rotación sospechosa", f["turnover_24h"] >= 1.0, "≥ 1,00 (el volumen de un día supera la capitalización)"),
        ("Momentum 7 d", f["change_7d_pct"] >= 15, "≥ +15 %"), ("Momentum 7 d", f["change_7d_pct"] >= 30, "≥ +30 %"),
        ("Momentum 30 d", f["change_30d_pct"] >= 25, "≥ +25 %"), ("Momentum 30 d", f["change_30d_pct"] >= 60, "≥ +60 %"), ("Momentum 30 d", f["change_30d_pct"] >= 100, "≥ +100 %"),
    ]:
        lines.append(f"| {label} | {text} | {pct(int(mask.fillna(False).sum()), n)} |")
    both = (f["volume_24h_usd"] >= 5e5) & (f["market_cap_usd"] >= 5e6)
    lines += ["", f"Con el suelo propuesto (capitalización ≥ 5 M$ **y** volumen 24 h ≥ 0,5 M$) quedan **{pct(int(both.sum()), n)}** monedas.", ""]
    dilution = f[f["circulating_supply"].notna() & f["total_supply"].notna() & (f["total_supply"] > 0)]
    ratio = dilution["circulating_supply"] / dilution["total_supply"]
    fdv = (f["fdv_usd"] / f["market_cap_usd"]).dropna()
    lines += ["### Dilución (factor de riesgo, no de puntos)", "",
              f"- Circulante / total: {quantiles(ratio)} (base {len(ratio):,}; sin total declarado: {n - len(ratio):,}).",
              f"- Circulante / total < 0,5: {pct(int((ratio < 0.5).sum()), len(ratio))} · < 0,3: {pct(int((ratio < 0.3).sum()), len(ratio))}.",
              f"- FDV / capitalización: {quantiles(fdv)} (base {len(fdv):,}). ≥ 3: {pct(int((fdv >= 3).sum()), len(fdv))}.", ""]
    return lines


def section_detail(r: dict) -> list[str]:
    s: pd.DataFrame = r["sample"]
    n = len(s)
    lines = ["## B. Señales que necesitan la serie diaria (muestra estratificada)", "",
             f"Muestra de **{n}** monedas repartidas por banda de capitalización (de 5 M$ para arriba), elegidas sin azar: a intervalos regulares por orden de capitalización dentro de cada banda. "
             "No es representativa del universo entero: sirve para ver el orden de magnitud de las señales con serie diaria.", ""]
    lines += ["| Banda | Monedas en la muestra |", "|---|---|"]
    for label, low, high in SAMPLE_BANDS:
        lines.append(f"| {label} | {int(((s['market_cap_usd'] >= low) & (s['market_cap_usd'] < high)).sum())} |")
    rv = s["rel_vol_rolling"].dropna()
    rv2 = s["rel_vol_last_day"].dropna()
    lines += ["", f"- Volumen relativo (volumen 24 h móvil / media de los últimos 30 días completos): {quantiles(rv)} (base {len(rv)}).",
              f"- Volumen relativo estable (último día completo / media de los 30 anteriores): {quantiles(rv2)} (base {len(rv2)}).", ""]
    lines += ["| Señal | Umbral | Monedas de la muestra |", "|---|---|---|"]
    for label, mask, text in [("Volumen relativo móvil", s["rel_vol_rolling"] >= 2, "≥ 2"), ("Volumen relativo móvil", s["rel_vol_rolling"] >= 3, "≥ 3"),
                              ("Volumen relativo estable", s["rel_vol_last_day"] >= 2, "≥ 2"), ("Volumen relativo estable", s["rel_vol_last_day"] >= 3, "≥ 3"),
                              ("Ruptura del máximo de cierre de 30 días", s["breakout_30d"] == True, "precio actual > máximo de los 30 cierres anteriores")]:  # noqa: E712
        lines.append(f"| {label} | {text} | {pct(int(mask.fillna(False).sum()), n)} |")
    both = ((s["rel_vol_rolling"] >= 2) & (s["breakout_30d"] == True)).sum()  # noqa: E712
    lines += ["", f"Ruptura **con** volumen relativo móvil ≥ 2: {pct(int(both), n)}.", ""]
    return lines


def render(r: dict) -> str:
    lines = ["# Estudio descriptivo de señales cripto sobre el universo real (v2.50D)", "",
             "Describe cuántas monedas pasaría cada umbral candidato. **No predice nada** ni mide rentabilidad futura. Solo agregados: no se guardan cifras por moneda.", ""]
    lines += section_universe(r) + section_markets_only(r) + section_detail(r)
    lines += [f"Llamadas usadas por esta ejecución: {r['calls_used']} · mes {r['usage']['month']}: {r['usage']['calls']:,} de {r['usage']['cap']:,} (tope de seguridad).", ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", type=int, default=120, help="coins for the daily-series signals (default 120)")
    parser.add_argument("--markdown", type=Path, help="also write the summary to this file (atomic)")
    args = parser.parse_args()
    text = render(study(args.sample))
    print(text)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.markdown.with_suffix(args.markdown.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        tmp.replace(args.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
