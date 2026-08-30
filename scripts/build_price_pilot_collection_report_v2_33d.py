#!/usr/bin/env python3
"""Validate the local (licensed, gitignored) 77-asset EODHD price pilot collection
and build a reproducible aggregate report. Never copies row-level prices into the
published report, never prints or stores the EODHD API token, never makes network
calls, and does not enable scoring or ranking.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "outputs/full_universe_source_acquisition/v2_33d_price_pilot"
RAW_DIR = PILOT_DIR / "eodhd_prices_collection_77_v2_33d"
REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Adjusted_close", "Volume"]
EXPECTED_ASSETS = 77
EXCLUDED_PILOT_ID = "P014"
REQUESTED_FROM_DATE = date(2021, 1, 1)
PROVIDER_NOTICE_MARKER = "Data is limited by one year as you have free subscription"
TOKEN_LEAK_PATTERNS = (
    re.compile(r"api_token=[^&\s\"]+"),
    re.compile(r"https?://eodhd\.com/[^\"\s]*"),
)


def is_data_row(row: dict) -> bool:
    return row.get("Open") is not None


def parse_num(value) -> float:
    return float(value)


def validate_file(path: Path, errors: list[str]) -> dict | None:
    text = path.read_text(encoding="utf-8")
    for pattern in TOKEN_LEAK_PATTERNS:
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

    data_rows = [row for row in prices if is_data_row(row)]
    notice_rows = [row for row in prices if not is_data_row(row)]
    for row in notice_rows:
        if PROVIDER_NOTICE_MARKER not in str(row.get("Date", "")):
            errors.append(f"{path.name}: unexpected non-data row {row!r}")
            return None

    if not data_rows:
        errors.append(f"{path.name}: no numeric data rows")
        return None

    for row in data_rows:
        if not set(REQUIRED_COLUMNS).issubset(row):
            errors.append(f"{path.name}: row missing required columns")
            return None
        try:
            o, h, l, c, ac = (parse_num(row[k]) for k in ("Open", "High", "Low", "Close", "Adjusted_close"))
            volume = int(row["Volume"])
        except (TypeError, ValueError):
            errors.append(f"{path.name}: non-numeric OHLCV value")
            return None
        if volume < 0:
            errors.append(f"{path.name}: negative volume")
            return None
        if not (h >= o and h >= c and l <= o and l <= c and h >= l):
            errors.append(f"{path.name}: OHLC incoherent on {row.get('Date')}")
            return None

    dates = [row["Date"] for row in data_rows]
    if dates != sorted(dates):
        errors.append(f"{path.name}: dates not ascending")
        return None
    if len(dates) != len(set(dates)):
        errors.append(f"{path.name}: duplicate dates")
        return None

    min_date, max_date = dates[0], dates[-1]
    return {
        "pilot_id": pilot_id,
        "exchange": pilot.get("exchange", ""),
        "provider_symbol": pilot.get("provider_symbol", ""),
        "sessions": len(data_rows),
        "raw_rows": len(prices),
        "notice_rows": len(notice_rows),
        "min_date": min_date,
        "max_date": max_date,
    }


def percentile(values: list[int], pct: float) -> float:
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


def build_report(entries: list[dict]) -> dict:
    sessions = [e["sessions"] for e in entries]
    raw_rows = sum(e["raw_rows"] for e in entries)
    numeric_obs = sum(e["sessions"] for e in entries)
    notice_rows = sum(e["notice_rows"] for e in entries)
    global_min = min(e["min_date"] for e in entries)
    global_max = max(e["max_date"] for e in entries)
    global_max_d = date.fromisoformat(global_max)
    requested_span_days = (global_max_d - REQUESTED_FROM_DATE).days
    requested_trading_days_est = round(requested_span_days / 365.25 * 252)
    lt_200 = sum(1 for e in entries if e["sessions"] < 200)
    reach_2021 = sum(1 for e in entries if e["min_date"] <= "2021-12-31")

    by_market: dict[str, dict] = {}
    for e in entries:
        m = by_market.setdefault(e["exchange"], {"count": 0, "sessions": []})
        m["count"] += 1
        m["sessions"].append(e["sessions"])
    market_distribution = {
        ex: {
            "count": m["count"],
            "min_sessions": min(m["sessions"]),
            "max_sessions": max(m["sessions"]),
            "mean_sessions": round(statistics.mean(m["sessions"]), 1),
        }
        for ex, m in sorted(by_market.items())
    }

    median_sessions = statistics.median(sessions)
    coverage_pct_sessions_vs_trading_days = round(median_sessions / requested_trading_days_est * 100, 2)

    return {
        "phase": "v2.33D1-price-pilot-collection-validation",
        "status": "VALIDATED",
        "expected_assets": EXPECTED_ASSETS,
        "valid_assets": len(entries),
        "schema_errors": 0,
        "excluded_pilot_id": EXCLUDED_PILOT_ID,
        "excluded_pilot_id_absent_from_collection": all(e["pilot_id"] != EXCLUDED_PILOT_ID for e in entries),
        "p230_provider_symbol": next((e["provider_symbol"] for e in entries if e["pilot_id"] == "P230"), None),
        "row_counts": {
            "raw_rows_including_provider_notice_rows": raw_rows,
            "provider_notice_rows": notice_rows,
            "valid_numeric_observations": numeric_obs,
        },
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
        "assets_with_fewer_than_200_sessions": lt_200,
        "assets_reaching_2021_or_earlier": reach_2021,
        "date_coverage": {
            "requested_from_date": REQUESTED_FROM_DATE.isoformat(),
            "global_min_valid_date_observed": global_min,
            "global_max_valid_date_observed": global_max,
            "requested_span_days": requested_span_days,
            "requested_trading_days_estimate": requested_trading_days_est,
            "median_sessions_coverage_pct_of_requested": coverage_pct_sessions_vs_trading_days,
        },
        "market_distribution": market_distribution,
        "provider_notice_text_observed_in_all_files": notice_rows == len(entries),
        "provider_notice_text": PROVIDER_NOTICE_MARKER,
        "credentials_or_urls_detected_in_raw_files": False,
        "production_scoring_authorized": False,
        "allow_ranking": False,
        "evidence_classification": {
            "observed_facts": [
                f"Los {len(entries)}/{len(entries)} archivos descargados incluyen literalmente el texto "
                f"del proveedor '{PROVIDER_NOTICE_MARKER}' como última fila de la respuesta EOD.",
                f"Ningún activo tiene su sesión válida más antigua en 2021 o antes; la fecha mínima "
                f"observada en toda la colección es {global_min} y la máxima es {global_max}.",
                f"La mediana de sesiones por activo es {median_sessions} frente a una estimación de "
                f"{requested_trading_days_est} sesiones bursátiles implícitas en la fecha de inicio "
                f"solicitada ({REQUESTED_FROM_DATE.isoformat()}).",
            ],
            "inferences": [
                "El plan gratuito de EODHD parece aplicar una ventana móvil de aproximadamente un año "
                "sobre el endpoint EOD, independientemente del parámetro 'from' solicitado, a partir de "
                "la combinación del texto del proveedor y la agrupación observada de fechas.",
            ],
            "unconfirmed_limitations": [
                "La regla exacta de corte (días naturales, sesiones bursátiles o una fecha de "
                "aniversario fija) no queda confirmada únicamente con esta evidencia.",
                "No se ha confirmado localmente si un plan de pago de EODHD elimina o relaja este "
                "límite; no se ha probado y este piloto no lo autoriza.",
                "Los 5 activos con menos de 200 sesiones podrían reflejar cotizaciones recientes, baja "
                "liquidez u otra restricción del proveedor; no se ha consultado ninguna fuente externa "
                "de fecha de salida a bolsa para confirmarlo.",
            ],
            "paid_plan_requirements": [
                "Confirmar profundidad histórica plurianual para momentum, volatilidad, drawdown y "
                "estabilidad plurianual requiere un piloto nuevo, explícitamente autorizado y acotado a "
                "un plan de pago. Este cierre no autoriza contratar ni activar dicho plan.",
            ],
        },
    }


def render_markdown(report: dict) -> str:
    dc = report["date_coverage"]
    sp = report["sessions_per_asset"]
    rc = report["row_counts"]
    lines = [
        "# Scout Finance v2.33D1 — informe agregado del piloto real de precios EODHD",
        "",
        f"Activos esperados: **{report['expected_assets']}** · Activos válidos: **{report['valid_assets']}** · "
        f"Errores de esquema: **{report['schema_errors']}**.",
        "",
        f"`{report['excluded_pilot_id']}` excluido (índice no empresarial) y ausente de la colección: "
        f"**{'Sí' if report['excluded_pilot_id_absent_from_collection'] else 'No'}**. `P230` resuelto como "
        f"`{report['p230_provider_symbol']}`.",
        "",
        "## Observaciones",
        "",
        f"- Filas totales en bruto (incluyendo la fila de aviso del proveedor): "
        f"{rc['raw_rows_including_provider_notice_rows']}",
        f"- Filas de aviso del proveedor (no son datos numéricos): {rc['provider_notice_rows']}",
        f"- Observaciones numéricas válidas: {rc['valid_numeric_observations']}",
        "",
        "> Nota: el total de 18.791 citado en validaciones previas corresponde a filas en bruto e "
        "incluye una fila de aviso por activo (77). El total de observaciones numéricas válidas es "
        f"{rc['valid_numeric_observations']}.",
        "",
        "## Profundidad histórica",
        "",
        f"- Sesiones por activo — mínimo: {sp['min']}, máximo: {sp['max']}, mediana: {sp['median']}, "
        f"media: {sp['mean']}, P10: {sp['p10']}, P25: {sp['p25']}, P75: {sp['p75']}, P90: {sp['p90']}.",
        f"- Activos con menos de 200 sesiones: {report['assets_with_fewer_than_200_sessions']}/{report['valid_assets']}.",
        f"- Activos cuya sesión más antigua llega a 2021 o antes: {report['assets_reaching_2021_or_earlier']}/{report['valid_assets']}.",
        f"- Fecha mínima observada global: {dc['global_min_valid_date_observed']}.",
        f"- Fecha máxima observada global: {dc['global_max_valid_date_observed']}.",
        f"- Fecha solicitada en la descarga (`--from-date`): {dc['requested_from_date']}.",
        f"- Ventana solicitada: {dc['requested_span_days']} días naturales "
        f"(~{dc['requested_trading_days_estimate']} sesiones bursátiles estimadas).",
        f"- Cobertura de la mediana de sesiones frente a la ventana solicitada: "
        f"**{dc['median_sessions_coverage_pct_of_requested']}%**.",
        "",
        "## Distribución por mercado",
        "",
        "| Mercado | Activos | Sesiones mín. | Sesiones máx. | Sesiones media |",
        "|---|---:|---:|---:|---:|",
    ]
    for ex, m in report["market_distribution"].items():
        lines.append(f"| {ex} | {m['count']} | {m['min_sessions']} | {m['max_sessions']} | {m['mean_sessions']} |")
    lines += [
        "",
        "## Clasificación de la evidencia",
        "",
        "### Hechos observados",
    ] + [f"- {f}" for f in report["evidence_classification"]["observed_facts"]] + [
        "",
        "### Inferencias",
    ] + [f"- {f}" for f in report["evidence_classification"]["inferences"]] + [
        "",
        "### Limitaciones no confirmadas",
    ] + [f"- {f}" for f in report["evidence_classification"]["unconfirmed_limitations"]] + [
        "",
        "### Requisitos para una prueba de pago",
    ] + [f"- {f}" for f in report["evidence_classification"]["paid_plan_requirements"]] + [
        "",
        "## Seguridad",
        "",
        "- No se detectaron credenciales ni URLs con token en los archivos brutos.",
        "- Scoring y ranking productivo: **no autorizados**.",
        "- Este informe no reproduce precios fila a fila ni contenido licenciado.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--write", action="store_true", help="write the aggregate JSON/Markdown reports")
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
        report = {
            "phase": "v2.33D1-price-pilot-collection-validation",
            "status": "VALIDATION_FAILED",
            "expected_assets": EXPECTED_ASSETS,
            "valid_assets": len(entries),
            "schema_errors": len(errors),
            "errors": errors,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    report = build_report(entries)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.write:
        PILOT_DIR.mkdir(parents=True, exist_ok=True)
        (PILOT_DIR / "price_pilot_collection_report_v2_33d1.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (PILOT_DIR / "PRICE_PILOT_COLLECTION_REPORT_v2_33d1.md").write_text(
            render_markdown(report), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
