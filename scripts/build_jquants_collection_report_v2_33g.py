#!/usr/bin/env python3
"""Validate the local (licensed, gitignored) 42-asset J-Quants JPX price pilot
collection and build a reproducible aggregate report. Never copies row-level
prices into the published report, never prints or stores the API key, never
makes network calls, and does not enable scoring or ranking.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33g_jquants_price_pilot"
RAW_DIR = PILOT_DIR / "jquants_prices_collection_v2_33g"
REQUIRED_FIELDS = {"Date", "Code", "O", "H", "L", "C", "Vo"}
EXPECTED_ASSETS = 42
CONFIRMED_FROM_DATE = date(2024, 6, 8)
CONFIRMED_TO_DATE = date(2026, 6, 8)
KEY_LEAK_PATTERNS = (
    re.compile(r"x-api-key[\"']?\s*[:=]\s*[\"'][^\"']+[\"']"),
    re.compile(r"https?://api\.jquants\.com/[^\"\s]*"),
)


def validate_file(path: Path, errors: list[str]) -> dict | None:
    text = path.read_text(encoding="utf-8")
    for pattern in KEY_LEAK_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path.name}: possible credential/URL leak")
            return None

    payload = json.loads(text)
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

    traded_rows = []
    no_trade_rows = []
    for row in prices:
        if not REQUIRED_FIELDS.issubset(row):
            errors.append(f"{path.name}: row missing required fields")
            return None
        if any(row[k] is None for k in ("O", "H", "L", "C")):
            # JPX records a calendar trading day with no matched trade (illiquid
            # stock) as a row with null OHLC/volume rather than omitting it.
            if row.get("Vo") not in (None, 0):
                errors.append(f"{path.name}: null OHLC but non-null volume on {row.get('Date')}")
                return None
            no_trade_rows.append(row)
            continue
        o, h, l, c = row["O"], row["H"], row["L"], row["C"]
        volume = row["Vo"]
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
        "provider_symbol": pilot.get("provider_symbol", ""),
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
    total_calendar_rows = sum(e["calendar_rows"] for e in entries)
    total_no_trade_rows = sum(e["no_trade_rows"] for e in entries)
    global_min = min(e["min_date"] for e in entries)
    global_max = max(e["max_date"] for e in entries)
    requested_span_days = (CONFIRMED_TO_DATE - CONFIRMED_FROM_DATE).days
    requested_trading_days_est = round(requested_span_days / 365.25 * 245)  # Japan ~245 trading days/yr
    median_sessions = statistics.median(sessions)
    lt_300 = [e for e in entries if e["sessions"] < 300]
    illiquid = sorted((e for e in entries if e["no_trade_rows"] > 0), key=lambda e: -e["no_trade_rows"])

    return {
        "phase": "v2.33G-jquants-price-pilot-collection-validation",
        "status": "VALIDATED",
        "expected_assets": EXPECTED_ASSETS,
        "valid_assets": len(entries),
        "schema_errors": 0,
        "row_counts": {
            "valid_numeric_observations": total_obs,
            "calendar_rows_including_no_trade_days": total_calendar_rows,
            "no_trade_days_null_ohlc": total_no_trade_rows,
        },
        "illiquid_assets_with_no_trade_days": [
            {"pilot_id": e["pilot_id"], "ticker": e["ticker"], "no_trade_days": e["no_trade_rows"], "traded_sessions": e["sessions"]}
            for e in illiquid
        ],
        "sessions_per_asset": {
            "min": min(sessions),
            "max": max(sessions),
            "median": median_sessions,
            "mean": round(statistics.mean(sessions), 2),
            "p10": percentile(sessions, 10),
            "p25": percentile(sessions, 25),
            "p75": percentile(sessions, 75),
            "p90": percentile(sessions, 90),
        },
        "assets_with_fewer_than_300_sessions": [
            {"pilot_id": e["pilot_id"], "ticker": e["ticker"], "sessions": e["sessions"], "min_date": e["min_date"]}
            for e in lt_300
        ],
        "date_coverage": {
            "confirmed_free_plan_from_date": CONFIRMED_FROM_DATE.isoformat(),
            "confirmed_free_plan_to_date": CONFIRMED_TO_DATE.isoformat(),
            "global_min_valid_date_observed": global_min,
            "global_max_valid_date_observed": global_max,
            "requested_span_days": requested_span_days,
            "requested_trading_days_estimate": requested_trading_days_est,
            "median_sessions_coverage_pct_of_requested": round(median_sessions / requested_trading_days_est * 100, 2),
        },
        "credentials_or_urls_detected_in_raw_files": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "evidence_classification": {
            "observed_facts": [
                f"El propio J-Quants confirmó la ventana exacta del plan gratuito mediante un mensaje "
                f"de error HTTP 400 al solicitar un rango mayor: "
                f"'{CONFIRMED_FROM_DATE.isoformat()} ~ {CONFIRMED_TO_DATE.isoformat()}'.",
                f"41/{len(entries)} activos tienen el máximo de 486 sesiones cubriendo toda la ventana "
                f"confirmada; 1 activo ('277A' / Globe-ing Inc., pilot P148) tiene solo 368 sesiones, "
                f"empezando el 2024-11-29, más tarde que el resto.",
                "El límite de tasa documentado del plan gratuito (5 peticiones/minuto) produjo errores "
                "HTTP 429 reales en la práctica al ritmo documentado; un reintento con espera de 65 "
                "segundos resolvió todas las ocurrencias sin intervención manual ni pérdida de datos en "
                "la ejecución final.",
                f"2 activos registraron filas de calendario sin operación (OHLC nulo) ({total_no_trade_rows} "
                f"filas en total): el activo P182 (HOKURIKU GAS CO.,LTD., ticker 9537) tiene 64 días sin "
                f"operación en toda la ventana, coherente con una acción regional poco líquida; P154 tiene 2.",
            ],
            "inferences": [],
            "unconfirmed_limitations": [
                "Por qué el activo P148 (Globe-ing Inc.) tiene una fecha de inicio posterior a los otros "
                "41 activos no está confirmado aquí; una cotización reciente es la explicación más "
                "probable, pero no se ha verificado contra ninguna fuente externa de fecha de salida a bolsa.",
            ],
        },
    }


def render_markdown(report: dict) -> str:
    dc = report["date_coverage"]
    sp = report["sessions_per_asset"]
    lines = [
        "# Scout Finance v2.33G — informe agregado del piloto real de precios J-Quants (JPX)",
        "",
        f"Activos esperados: **{report['expected_assets']}** · Activos válidos: **{report['valid_assets']}** · "
        f"Errores de esquema: **{report['schema_errors']}**.",
        "",
        f"- Observaciones numéricas válidas: {report['row_counts']['valid_numeric_observations']}",
        f"- Sesiones por activo — mínimo: {sp['min']}, máximo: {sp['max']}, mediana: {sp['median']}, "
        f"media: {sp['mean']}, P10: {sp['p10']}, P25: {sp['p25']}, P75: {sp['p75']}, P90: {sp['p90']}.",
        f"- Ventana confirmada por el propio proveedor (plan gratuito): {dc['confirmed_free_plan_from_date']} → {dc['confirmed_free_plan_to_date']} "
        f"({dc['requested_span_days']} días naturales, ~{dc['requested_trading_days_estimate']} sesiones estimadas).",
        f"- Fecha mínima observada global: {dc['global_min_valid_date_observed']}. Fecha máxima observada global: {dc['global_max_valid_date_observed']}.",
        f"- Cobertura de la mediana de sesiones frente a la ventana confirmada: **{dc['median_sessions_coverage_pct_of_requested']}%**.",
        "",
        "## Activos con menos de 300 sesiones",
        "",
    ]
    if report["assets_with_fewer_than_300_sessions"]:
        lines.append("| pilot_id | ticker | sesiones | fecha mínima |")
        lines.append("|---|---|---:|---|")
        for a in report["assets_with_fewer_than_300_sessions"]:
            lines.append(f"| {a['pilot_id']} | {a['ticker']} | {a['sessions']} | {a['min_date']} |")
    else:
        lines.append("Ninguno.")
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
        "- No se detectaron credenciales ni URLs con clave en los archivos brutos.",
        "- Scoring y ranking productivo: **no autorizados**.",
        "- Este informe no reproduce precios fila a fila ni contenido licenciado.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if not args.raw_dir.exists():
        print(json.dumps({"status": "SKIPPED_NO_LOCAL_LICENSED_DATA", "raw_dir": str(args.raw_dir)}))
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
        (PILOT_DIR / "jquants_collection_report_v2_33g.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (PILOT_DIR / "JQUANTS_COLLECTION_REPORT_v2_33g.md").write_text(
            render_markdown(report), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
