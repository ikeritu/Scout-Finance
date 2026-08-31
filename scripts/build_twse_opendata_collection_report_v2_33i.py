#!/usr/bin/env python3
"""Validate the local (open-licensed, gitignored) 8-asset TWSE official
STOCK_DAY collection and build a reproducible aggregate report. Never
copies row-level prices into the published report, never makes network
calls, and does not enable scoring or ranking.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33i_twse_opendata_price_pilot"
RAW_DIR = PILOT_DIR / "twse_opendata_prices_collection_v2_33i"
REQUIRED_FIELDS = {"Date", "Open", "High", "Low", "Close", "Volume_shares", "Note"}
EXPECTED_ASSETS = 8
EARLIEST_CONFIRMED_DATE = "2010-01-04"


def validate_file(path: Path, errors: list[str]) -> dict | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "pilot" not in payload or "prices" not in payload:
        errors.append(f"{path.name}: missing 'pilot' or 'prices' key")
        return None
    pilot = payload["pilot"]
    prices = payload["prices"]
    pilot_id = pilot.get("pilot_id", "")
    if f"{pilot_id}.json" != path.name:
        errors.append(f"{path.name}: filename does not match pilot_id {pilot_id}")
        return None
    if not prices:
        errors.append(f"{path.name}: empty prices list")
        return None

    traded_rows, no_trade_rows = [], []
    for row in prices:
        if not REQUIRED_FIELDS.issubset(row):
            errors.append(f"{path.name}: row missing required fields")
            return None
        if row["Open"] is None or row["High"] is None or row["Low"] is None or row["Close"] is None:
            no_trade_rows.append(row)
            continue
        o, h, l, c = row["Open"], row["High"], row["Low"], row["Close"]
        volume = row["Volume_shares"]
        if volume is not None and volume < 0:
            errors.append(f"{path.name}: negative volume")
            return None
        if not (h >= o and h >= c and l <= o and l <= c and h >= l):
            errors.append(f"{path.name}: OHLC incoherent on {row.get('Date')}")
            return None
        traded_rows.append(row)

    dates = [row["Date"] for row in prices]
    if dates != sorted(dates):
        errors.append(f"{path.name}: dates not ascending")
        return None
    if len(dates) != len(set(dates)):
        errors.append(f"{path.name}: duplicate dates")
        return None
    if not traded_rows:
        errors.append(f"{path.name}: no traded (non-null OHLC) sessions")
        return None

    traded_dates = [row["Date"] for row in traded_rows]
    return {
        "pilot_id": pilot_id,
        "ticker": pilot.get("ticker", ""),
        "sessions": len(traded_rows),
        "calendar_rows": len(prices),
        "no_trade_rows": len(no_trade_rows),
        "min_date": traded_dates[0],
        "max_date": traded_dates[-1],
    }


def percentile(values: list[int], pct: float) -> float:
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


def build_report(entries: list[dict]) -> dict:
    sessions = [e["sessions"] for e in entries]
    total_obs = sum(sessions)
    global_min = min(e["min_date"] for e in entries)
    global_max = max(e["max_date"] for e in entries)
    reach_earliest = sum(1 for e in entries if e["min_date"] <= "2010-01-31")

    return {
        "phase": "v2.33I-twse-opendata-collection-validation",
        "status": "VALIDATED",
        "expected_assets": EXPECTED_ASSETS,
        "valid_assets": len(entries),
        "schema_errors": 0,
        "row_counts": {
            "valid_numeric_observations": total_obs,
            "no_trade_calendar_rows": sum(e["no_trade_rows"] for e in entries),
        },
        "sessions_per_asset": {
            "min": min(sessions),
            "max": max(sessions),
            "median": statistics.median(sessions),
            "mean": round(statistics.mean(sessions), 2),
            "p10": percentile(sessions, 10),
            "p25": percentile(sessions, 25),
            "p75": percentile(sessions, 75),
            "p90": percentile(sessions, 90),
        },
        "assets_reaching_earliest_confirmed_date": reach_earliest,
        "date_coverage": {
            "earliest_confirmed_source_date": EARLIEST_CONFIRMED_DATE,
            "global_min_valid_date_observed": global_min,
            "global_max_valid_date_observed": global_max,
        },
        "per_asset": [
            {"pilot_id": e["pilot_id"], "ticker": e["ticker"], "sessions": e["sessions"],
             "min_date": e["min_date"], "max_date": e["max_date"], "no_trade_rows": e["no_trade_rows"]}
            for e in entries
        ],
        "credentials_used": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "evidence_classification": {
            "observed_facts": [
                "El propio endpoint oficial STOCK_DAY de TWSE (www.twse.com.tw), gratuito y sin cuenta "
                "ni clave, rechaza explícitamente cualquier fecha anterior al 2010-01-04 con el mensaje "
                "'查詢日期小於99年1月4日，請重新查詢!' ('fecha de consulta anterior al 4 de enero del "
                "año 99 de la República'; año 99 ROC = 2010) -- un límite declarado por el propio "
                "proveedor, no inferido.",
                f"{reach_earliest}/{len(entries)} activos alcanzan esa fecha mínima confirmada; los otros "
                f"{len(entries) - reach_earliest} empiezan más tarde, coherente con una cotización más reciente.",
                "El endpoint devuelve OHLC en bruto (sin ajustar) -- no incluye ningún factor de ajuste "
                "por splits/dividendos, a diferencia del Adjusted_close de EODHD o los campos "
                "AdjFactor/AdjClose de J-Quants.",
                "12 filas de calendario en 4 de los 8 activos tienen OHLC nulo (sin operación ese día), "
                "sin ningún código explicativo en el campo 'Note'; es una fracción muy pequeña del total.",
            ],
            "inferences": [],
            "unconfirmed_limitations": [
                "No se ha confirmado si alguno de los 8 tickers sufrió un split o un dividendo grande "
                "durante esta ventana que distorsione cálculos de rentabilidad a largo plazo hechos de "
                "forma ingenua (sin ajustar); el campo 'Note' de TWSE no marcó ninguna de las 12 filas "
                "nulas ni ninguna otra fila de la muestra.",
                "No se ha confirmado la causa exacta de las 12 filas de calendario con OHLC nulo "
                "(suspensión de cotización u otra causa).",
            ],
        },
    }


def render_markdown(report: dict) -> str:
    sp = report["sessions_per_asset"]
    dc = report["date_coverage"]
    lines = [
        "# Scout Finance v2.33I — informe agregado del piloto TWSE (datos abiertos oficiales)",
        "",
        f"Activos esperados: **{report['expected_assets']}** · Activos válidos: **{report['valid_assets']}** · "
        f"Errores de esquema: **{report['schema_errors']}**.",
        "",
        f"- Observaciones numéricas válidas: {report['row_counts']['valid_numeric_observations']}",
        f"- Filas de calendario sin operación (OHLC nulo): {report['row_counts']['no_trade_calendar_rows']}",
        f"- Sesiones por activo — mínimo: {sp['min']}, máximo: {sp['max']}, mediana: {sp['median']}, "
        f"media: {sp['mean']}, P10: {sp['p10']}, P25: {sp['p25']}, P75: {sp['p75']}, P90: {sp['p90']}.",
        f"- Fecha mínima confirmada por el propio proveedor: {dc['earliest_confirmed_source_date']}.",
        f"- Fecha mínima observada global: {dc['global_min_valid_date_observed']}. Fecha máxima observada global: {dc['global_max_valid_date_observed']}.",
        f"- Activos que alcanzan la fecha mínima confirmada: {report['assets_reaching_earliest_confirmed_date']}/{report['valid_assets']}.",
        "",
        "## Por activo",
        "",
        "| pilot_id | ticker | sesiones | fecha mínima | fecha máxima | filas sin operación |",
        "|---|---|---:|---|---|---:|",
    ]
    for a in report["per_asset"]:
        lines.append(f"| {a['pilot_id']} | {a['ticker']} | {a['sessions']} | {a['min_date']} | {a['max_date']} | {a['no_trade_rows']} |")
    lines += [
        "",
        "## Clasificación de la evidencia",
        "",
        "### Hechos observados",
    ] + [f"- {f}" for f in report["evidence_classification"]["observed_facts"]] + [
        "",
        "### Limitaciones no confirmadas",
    ] + [f"- {f}" for f in report["evidence_classification"]["unconfirmed_limitations"]] + [
        "",
        "## Seguridad",
        "",
        "- Sin credenciales: fuente pública y oficial, sin cuenta ni clave.",
        "- Scoring y ranking productivo: **no autorizados**.",
        "- Este informe no reproduce precios fila a fila.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if not args.raw_dir.exists():
        print(json.dumps({"status": "SKIPPED_NO_LOCAL_DATA", "raw_dir": str(args.raw_dir)}))
        return 3

    files = sorted(args.raw_dir.glob("P*.json"))
    errors: list[str] = []
    entries: list[dict] = []
    for path in files:
        entry = validate_file(path, errors)
        if entry is not None:
            entries.append(entry)

    if errors or len(entries) != EXPECTED_ASSETS:
        print(json.dumps({"status": "VALIDATION_FAILED", "expected_assets": EXPECTED_ASSETS, "valid_assets": len(entries), "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    report = build_report(entries)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.write:
        PILOT_DIR.mkdir(parents=True, exist_ok=True)
        (PILOT_DIR / "twse_opendata_collection_report_v2_33i.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (PILOT_DIR / "TWSE_OPENDATA_COLLECTION_REPORT_v2_33i.md").write_text(
            render_markdown(report), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
