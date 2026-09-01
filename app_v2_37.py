"""Scout Finance v2.37 — local research product."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.ui_v2_37.repository import DataMode, load_fundamentals, load_price_series, load_product_data
from src.ui_v2_37.recommendations import MIN_INTEREST_SCORE, candidate_explanation, select_interesting_companies
from src.ui_v2_37.reports import DISCLAIMER, asset_markdown, manifest, ranking_markdown, to_html, watchlist_markdown
from src.ui_v2_37.ui import apply, banner, heading
from src.ui_v2_37.watchlists import STATUSES, add, atomic_write, create, export_csv, read, remove, scan, update

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Scout Finance — Investigación local", page_icon="🔎", layout="wide")
apply(st)

SCREENS = {
    "home": "🏠 Inicio", "universe": "🌐 Universo", "ranking": "📊 Ranking experimental",
    "asset": "🔎 Ficha de empresa", "compare": "⚖️ Comparador", "watchlist": "⭐ Watchlist",
    "reports": "📄 Informes", "help": "❓ Metodología y ayuda",
}
STATUS_LABELS = {
    "ELIGIBLE_PARTIAL": "Clasificable parcial", "PARTIAL_COMPARABILITY": "Comparabilidad parcial",
    "REVIEW_REQUIRED": "Revisión requerida", "BLOCKED": "Bloqueado",
}
CONFIDENCE_LABELS = {"HIGH": "Alta", "MEDIUM": "Media", "LOW": "Baja", "NOT_RANKABLE": "No clasificable"}
RESEARCH_STATUS_LABELS = {
    "WATCHLIST": "En seguimiento", "REJECT": "Descartado",
    "NEEDS_MORE_DATA": "Necesita más datos", "REVIEW_LATER": "Revisar más adelante",
}
PILLAR_LABELS = {"quality": "Calidad", "growth": "Crecimiento", "valuation": "Valoración", "momentum": "Tendencia", "risk": "Riesgo"}
FACTOR_LABELS = {
    "operating_margin": "Margen operativo", "net_margin": "Margen neto", "roa": "Rentabilidad sobre activos",
    "roe_reported": "Rentabilidad sobre patrimonio", "revenue_growth_yoy": "Crecimiento anual de ingresos",
    "net_income_growth_yoy": "Crecimiento anual del beneficio", "earnings_yield": "Rentabilidad del beneficio",
    "book_yield": "Rentabilidad del valor contable", "return_3m": "Rentabilidad a 3 meses",
    "return_6m": "Rentabilidad a 6 meses", "return_12m": "Rentabilidad a 12 meses",
    "distance_sma200": "Distancia a la media de 200 sesiones", "volatility_12m": "Volatilidad a 12 meses",
    "max_drawdown_12m": "Caída máxima a 12 meses",
    "revenue": "Ingresos", "cost_of_sales": "Coste de ventas", "gross_profit": "Beneficio bruto",
    "operating_income": "Beneficio operativo", "ordinary_income": "Beneficio ordinario",
    "pretax_income": "Beneficio antes de impuestos", "net_income": "Beneficio neto",
    "eps_basic": "Beneficio por acción básico", "eps_diluted": "Beneficio por acción diluido",
    "cash_and_equivalents": "Efectivo y equivalentes", "current_debt": "Deuda corriente",
    "noncurrent_debt": "Deuda no corriente", "gross_debt": "Deuda bruta", "net_debt": "Deuda neta",
    "current_assets": "Activo corriente", "total_assets": "Activo total",
    "current_liabilities": "Pasivo corriente", "total_liabilities": "Pasivo total",
    "total_equity": "Patrimonio neto", "book_value_per_share": "Valor contable por acción",
    "shares_outstanding": "Acciones en circulación", "operating_cash_flow": "Flujo de caja operativo",
    "investing_cash_flow": "Flujo de caja de inversión", "financing_cash_flow": "Flujo de caja de financiación",
    "capex": "Inversión en activos", "free_cash_flow": "Flujo de caja libre",
    "dividends_paid": "Dividendos pagados", "buybacks": "Recompras",
    "equity_ratio_reported": "Ratio de patrimonio", "gross_margin": "Margen bruto",
    "current_ratio": "Ratio corriente",
}
SOURCE_LABELS = {"jquants_fins_summary": "J-Quants · resumen financiero", "twse_mops_opendata": "TWSE MOPS · datos abiertos"}
REVIEW_REASON_LABELS = {
    "absolute_margin_outside_300pct": "Margen absoluto superior al 300 %; requiere revisión manual",
    "financial_institution_requires_separate_factor_contract": "Entidad financiera: requiere un contrato de factores específico",
}


@st.cache_data(show_spinner=False)
def product_snapshot():
    return load_product_data(ROOT)


@st.cache_data(show_spinner=False)
def price_snapshot(asset_id: str, market: str):
    return load_price_series(ROOT, {"asset_id": asset_id, "market": market})


@st.cache_data(show_spinner=False)
def fundamental_snapshot(asset_id: str):
    return load_fundamentals(ROOT, asset_id)


def go(screen: str, asset_id: str | None = None):
    if asset_id:
        st.session_state.selected_asset = asset_id
    st.session_state.pending_screen = screen
    st.rerun()


def status_badge(value: str) -> str:
    return STATUS_LABELS.get(value, value)


def factor_label(value: str) -> str:
    return FACTOR_LABELS.get(value, value.replace("_", " ").capitalize())


def explanation_item(value: str) -> str:
    kind, name, *score = value.split(":")
    fixed = {
        "criterion:high_confidence": "Confianza alta",
        "criterion:score_above": f"Supera el umbral de {MIN_INTEREST_SCORE:.0f}/100",
        "limitation:aggregate_detail_unavailable": "Detalle de factores no disponible en este equipo",
    }
    if f"{kind}:{name}" in fixed:
        return fixed[f"{kind}:{name}"]
    label = PILLAR_LABELS.get(name, factor_label(name)) if kind == "pillar" else factor_label(name)
    return f"{label} ({score[0]}/100)" if score else label


def display_rows(assets):
    return pd.DataFrame([{
        "ID": a["asset_id"], "Ticker": a["ticker"], "Empresa": a["company_name"], "Mercado": a["market"],
        "Estado": status_badge(a["eligibility_status"]), "Confianza": CONFIDENCE_LABELS.get(a["confidence"], a["confidence"]),
        "Score experimental": "N/D" if a.get("total_score") is None else f'{a["total_score"]:.2f}',
        "Posición": "N/D" if a.get("rank") is None else str(a["rank"]), "Sesiones": a["price_sessions"],
    } for a in assets])


def render_home(data):
    heading(st, "Scout Finance", "Empresas interesantes para investigar · v2.38")
    banner(st)
    candidates = select_interesting_companies(data.assets)
    st.markdown("## Selección actual")
    st.write(
        f"He encontrado **{len(candidates)} empresas interesantes para investigar** con los datos disponibles. "
        f"La selección varía automáticamente y exige confianza alta y un score mínimo de {MIN_INTEREST_SCORE:.0f}/100."
    )
    if not candidates:
        st.warning("Ahora mismo ninguna empresa supera los criterios. Scout Finance no fuerza recomendaciones.")
    for asset in candidates:
        explanation = candidate_explanation(asset)
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.subheader(f'{asset["company_name"]} · {asset["ticker"]}')
            left.write(explanation["summary"])
            left.write("**Por qué resulta interesante:** " + ", ".join(explanation_item(item) for item in explanation["reasons"]))
            left.write("**Qué conviene vigilar:** " + ", ".join(explanation_item(item) for item in explanation["cautions"]))
            right.metric("Posición", asset.get("rank") or "N/D")
            if right.button("Ver análisis", key=f'home-{asset["asset_id"]}'):
                go("asset", asset["asset_id"])
    st.caption("Selección cuantitativa para priorizar investigación; no equivale a una recomendación de compra.")
    st.divider()
    cols = st.columns(4)
    cols[0].metric("Activos", len(data.assets))
    cols[1].metric("Ranking principal", sum(a["eligibility_status"] == "ELIGIBLE_PARTIAL" for a in data.assets))
    cols[2].metric("Comparabilidad parcial", sum(a["eligibility_status"] == "PARTIAL_COMPARABILITY" for a in data.assets))
    cols[3].metric("Revisión requerida", sum(a["eligibility_status"] == "REVIEW_REQUIRED" for a in data.assets))
    st.markdown("### Estado de los datos")
    labels = {
        DataMode.REAL_LOCAL_READY: ("Datos locales completos", "Precios, fundamentales y scoring detallado disponibles."),
        DataMode.AGGREGATE_ONLY: ("Solo evidencia agregada", "Puedes consultar el universo y la shortlist publicada; el detalle local no está en este equipo."),
        DataMode.PARTIAL_DATA: ("Datos locales parciales", "Algunas vistas detalladas estarán limitadas."),
        DataMode.BLOCKED_MISSING_DATA: ("Datos bloqueados", "Faltan contratos canónicos."),
        DataMode.INCOMPATIBLE_VERSION: ("Versión incompatible", "Los datos no cumplen el contrato de producto."),
    }
    title, body = labels[data.mode]
    (st.success if data.mode == DataMode.REAL_LOCAL_READY else st.warning)(f"{title}: {body}")
    st.caption(f"Fecha de corte: {data.as_of_date or 'no disponible'} · Sin llamadas de red · Ejecución local")
    st.markdown("### Qué puedes hacer")
    st.write("Empezar por la selección propuesta, abrir sus argumentos, comparar empresas, mantener una watchlist privada y exportar informes con trazabilidad.")
    st.markdown("### Qué no hace Scout Finance")
    st.write("No recomienda operaciones, no predice rentabilidad, no se conecta a brokers y no ejecuta trading automático.")


def render_universe(data):
    heading(st, "Universo", "50 activos con identidad verificada: 42 JPX y 8 TWSE.")
    banner(st)
    search = st.text_input("Buscar", placeholder="Empresa, ticker o ID")
    c1, c2, c3 = st.columns(3)
    markets = c1.multiselect("Mercado", sorted({a["market"] for a in data.assets}), placeholder="Todos")
    states = c2.multiselect("Estado", list(STATUS_LABELS), format_func=status_badge, placeholder="Todos")
    confidence = c3.multiselect("Confianza", ["HIGH", "MEDIUM", "LOW", "NOT_RANKABLE"], format_func=lambda value: CONFIDENCE_LABELS[value], placeholder="Todas")
    needle = search.casefold().strip()
    rows = [a for a in data.assets if (not needle or any(needle in str(a[k]).casefold() for k in ("asset_id", "ticker", "company_name"))) and (not markets or a["market"] in markets) and (not states or a["eligibility_status"] in states) and (not confidence or a["confidence"] in confidence)]
    st.caption(f"{len(rows)} resultados")
    st.dataframe(display_rows(rows), use_container_width=True, hide_index=True)
    if rows:
        options = {f'{a["ticker"]} · {a["company_name"]} · {status_badge(a["eligibility_status"])}': a["asset_id"] for a in rows}
        selected = st.selectbox("Activo seleccionado", options)
        if st.button("Abrir ficha", type="primary"):
            go("asset", options[selected])


def render_ranking(data):
    heading(st, "Ranking experimental", "Prioridad cuantitativa de investigación; no es una clasificación predictiva.")
    banner(st)
    ranked = sorted((a for a in data.assets if a.get("rank")), key=lambda a: a["rank"])
    if data.mode == DataMode.AGGREGATE_ONLY:
        st.info("Modo agregado: se muestran las 10 posiciones publicadas. El ranking completo de 41 activos permanece en los datos locales.")
    st.markdown("### Ranking principal · JPX")
    st.dataframe(display_rows(ranked), use_container_width=True, hide_index=True)
    partial = [a for a in data.assets if a["eligibility_status"] == "PARTIAL_COMPARABILITY"]
    review = [a for a in data.assets if a["eligibility_status"] == "REVIEW_REQUIRED"]
    with st.expander(f"Comparabilidad parcial · TWSE ({len(partial)})"):
        st.warning("TWSE no compite con JPX: solo dispone de un periodo fundamental y sus precios no están ajustados.")
        st.dataframe(display_rows(partial), use_container_width=True, hide_index=True)
    with st.expander(f"Revisión requerida ({len(review)})"):
        st.dataframe(display_rows(review), use_container_width=True, hide_index=True)
        st.caption("P020 conserva una anomalía real; P178 requiere un contrato específico para entidades financieras.")


def render_asset(data):
    heading(st, "Ficha de empresa", "Identidad, datos disponibles, scoring y limitaciones.")
    options = {f'{a["ticker"]} · {a["company_name"]}': a["asset_id"] for a in data.assets}
    labels = list(options)
    requested = st.session_state.pop("selected_asset", None)
    selected_index = next((index for index, label in enumerate(labels) if options[label] == requested), 0)
    selected_label = st.selectbox("Selecciona un activo", labels, index=selected_index)
    asset_id = options[selected_label]
    asset = data.by_id(asset_id)
    banner(st)
    st.subheader(f'{asset["company_name"]} · {asset["ticker"]}')
    cols = st.columns(4)
    cols[0].metric("Mercado", asset["market"])
    cols[1].metric("Estado", status_badge(asset["eligibility_status"]))
    cols[2].metric("Confianza", CONFIDENCE_LABELS.get(asset["confidence"], asset["confidence"]))
    cols[3].metric("Score experimental", "N/D" if asset.get("total_score") is None else f'{asset["total_score"]:.2f}')
    if asset["eligibility_status"] == "REVIEW_REQUIRED":
        st.error("Este activo no tiene posición automática. Motivo: " + "; ".join(REVIEW_REASON_LABELS.get(reason, reason) for reason in asset["review_reasons"]))
    if asset["market"] == "TWSE":
        st.warning("Comparabilidad parcial: precio sin ajustar y un único periodo fundamental utilizable.")
    st.markdown("### Precio")
    prices = price_snapshot(asset["asset_id"], asset["market"])
    if prices:
        frame = pd.DataFrame(prices).set_index("Date")
        st.line_chart(frame, y="Close")
        st.caption(f'{len(prices)} sesiones · {prices[0]["Date"]} a {prices[-1]["Date"]} · {"ajustado" if asset["price_adjusted"] else "sin ajustar"}')
    else:
        st.info("El histórico detallado no está disponible en este equipo.")
    st.markdown("### Pilares del scoring")
    pillars = asset.get("pillar_scores") or {}
    if pillars:
        translated_pillars = {PILLAR_LABELS.get(key, key): value for key, value in pillars.items()}
        st.bar_chart(pd.DataFrame({"Puntuación": translated_pillars}))
    else:
        st.info("Los pilares detallados solo están disponibles con el resultado local de fase 6.")
    c1, c2, c3 = st.columns(3)
    c1.write("**Fortalezas disponibles**"); c1.write(", ".join(factor_label(value) for value in (asset.get("strength_factors") or [])) or "No disponibles")
    c2.write("**Factores débiles**"); c2.write(", ".join(factor_label(value) for value in (asset.get("weakness_factors") or [])) or "No disponibles")
    c3.write("**Factores ausentes**"); c3.write(", ".join(factor_label(value) for value in (asset.get("missing_factors") or [])) or "No disponibles")
    fundamentals = fundamental_snapshot(asset["asset_id"])
    st.markdown("### Fundamentales")
    if fundamentals:
        latest = {}
        for row in fundamentals:
            latest.setdefault(row["metric"], row)
        st.dataframe(pd.DataFrame([{"Métrica": factor_label(key), "Valor": row["value"], "Periodo": row.get("period_end") or "N/D", "Moneda": row.get("currency") or "N/D", "Fuente": SOURCE_LABELS.get(row.get("provider"), row.get("provider") or "N/D")} for key, row in sorted(latest.items())]), use_container_width=True, hide_index=True)
    else:
        st.info("Los fundamentales detallados no están disponibles en este equipo.")
    report = asset_markdown(asset, data.as_of_date)
    st.download_button("Descargar ficha HTML", to_html(report), f'{asset["asset_id"]}_research.html', "text/html")


def render_compare(data):
    heading(st, "Comparador", "Compara de dos a cuatro activos sin ocultar diferencias de mercado o cobertura.")
    options = {f'{a["ticker"]} · {a["company_name"]}': a["asset_id"] for a in data.assets}
    selected = st.multiselect("Activos", options, max_selections=4, placeholder="Selecciona de 2 a 4 activos")
    assets = [data.by_id(options[label]) for label in selected]
    if len(assets) < 2:
        st.info("Selecciona entre 2 y 4 activos."); return
    banner(st)
    if len({a["market"] for a in assets}) > 1:
        st.warning("Comparabilidad parcial: los mercados no comparten la misma profundidad fundamental ni el mismo tratamiento de precios.")
    st.dataframe(display_rows(assets), use_container_width=True, hide_index=True)
    pillars = sorted({key for a in assets for key in (a.get("pillar_scores") or {})})
    if pillars:
        frame = pd.DataFrame({a["ticker"]: {PILLAR_LABELS.get(p, p): a.get("pillar_scores", {}).get(p) for p in pillars} for a in assets})
        st.bar_chart(frame, stack=False)
    else:
        st.info("Comparación de pilares no disponible en modo agregado.")


def select_watchlist():
    available, errors = scan(ROOT)
    for path, error in errors:
        st.warning(f"Se omitió {path.name}: {error}")
    if not available:
        return None, None
    labels = {f'{data["name"]} ({len(data["items"])})': path for path, data in available}
    path = labels[st.selectbox("Watchlist", labels)]
    return path, read(path)


def render_watchlist(data):
    heading(st, "Watchlist privada", "Notas y decisiones de investigación guardadas solo en este equipo.")
    with st.expander("Crear watchlist"):
        name = st.text_input("Nombre"); description = st.text_input("Descripción")
        if st.button("Crear watchlist"):
            try: create(ROOT, name, description); st.rerun()
            except ValueError as exc: st.error(str(exc))
    path, watch = select_watchlist()
    if not watch:
        st.info("Todavía no hay watchlists v2.37."); return
    st.markdown("### Añadir activo")
    options = {f'{a["ticker"]} · {a["company_name"]}': a for a in data.assets}
    choice = st.selectbox("Activo", options)
    status = st.selectbox("Estado de investigación", STATUSES, format_func=lambda value: RESEARCH_STATUS_LABELS[value])
    note = st.text_area("Nota")
    if st.button("Añadir", type="primary"):
        try: add(watch, options[choice], status, note); atomic_write(path, watch); st.rerun()
        except ValueError as exc: st.error(str(exc))
    st.markdown(f'### Activos ({len(watch["items"])})')
    if watch["items"]:
        watch_rows = pd.DataFrame(watch["items"]).rename(columns={
            "asset_id": "ID", "ticker": "Ticker", "company_name": "Empresa", "market": "Mercado",
            "research_status": "Estado", "note": "Nota", "added_at_utc": "Añadido (UTC)",
        })
        watch_rows["Estado"] = watch_rows["Estado"].map(lambda value: RESEARCH_STATUS_LABELS.get(value, value))
        st.dataframe(watch_rows, use_container_width=True, hide_index=True)
    else:
        st.info("La watchlist está vacía.")
    if watch["items"]:
        items = {f'{x["ticker"]} · {x["company_name"]}': x for x in watch["items"]}
        label = st.selectbox("Editar activo guardado", items)
        item = items[label]
        new_status = st.selectbox("Nuevo estado", STATUSES, index=STATUSES.index(item["research_status"]), format_func=lambda value: RESEARCH_STATUS_LABELS[value])
        new_note = st.text_area("Editar nota", item.get("note", ""))
        c1, c2, c3 = st.columns(3)
        if c1.button("Guardar cambios"): update(watch, item["asset_id"], new_status, new_note); atomic_write(path, watch); st.rerun()
        if c2.button("Abrir ficha"): go("asset", item["asset_id"])
        if c3.button("Eliminar"): remove(watch, item["asset_id"]); atomic_write(path, watch); st.rerun()
    st.download_button("Exportar watchlist CSV", export_csv(watch), f'{path.stem}.csv', "text/csv")


def render_reports(data):
    heading(st, "Informes", "Exportaciones locales con procedencia, fecha de corte y advertencias.")
    kind = st.selectbox("Tipo", ["Ranking experimental", "Ficha de empresa", "Watchlist"])
    if kind == "Ranking experimental":
        markdown = ranking_markdown(list(data.assets), data.as_of_date); stem = "ranking_experimental"; report_kind = "ranking"
    elif kind == "Ficha de empresa":
        options = {f'{a["ticker"]} · {a["company_name"]}': a for a in data.assets}; label = st.selectbox("Activo", options)
        markdown = asset_markdown(options[label], data.as_of_date); stem = options[label]["asset_id"]; report_kind = "asset"
    else:
        _, watch = select_watchlist()
        if not watch: st.info("Crea una watchlist para exportarla."); return
        markdown = watchlist_markdown(watch, data.as_of_date); stem = "watchlist"; report_kind = "watchlist"
    st.markdown(markdown)
    st.download_button("Descargar HTML", to_html(markdown), f"{stem}.html", "text/html")
    st.download_button("Descargar manifiesto", manifest(report_kind, data.as_of_date), f"{stem}.manifest.json", "application/json")


def render_help(data):
    heading(st, "Metodología y ayuda", "Guía breve para interpretar Scout Finance sin conocimientos técnicos.")
    banner(st)
    with st.expander("¿Qué significa el score?", expanded=True): st.write("Es una puntuación relativa calculada con factores de calidad, crecimiento, valoración, momentum y riesgo. Sirve para ordenar investigación, no para predecir rentabilidad.")
    with st.expander("¿Qué significa la confianza?"): st.write("Mide cobertura y comparabilidad de los factores disponibles. HIGH no significa alta probabilidad de ganar dinero.")
    with st.expander("¿Qué significa INSUFFICIENT_EVIDENCE?"): st.write("No existe suficiente histórico point-in-time para validar el scoring fuera de muestra. No demuestra éxito ni fracaso predictivo.")
    with st.expander("¿Por qué TWSE está separado?"): st.write("Tiene un único periodo fundamental utilizable y precios sin ajustar por splits y dividendos.")
    with st.expander("¿Por qué P020 y P178 requieren revisión?"): st.write("P020 conserva un margen extremo real. P178 es un banco y necesita un contrato específico para financieras.")
    with st.expander("¿Dónde se guardan mis listas?"): st.write("En data/watchlists, únicamente en tu ordenador y excluidas de Git.")
    st.markdown("### Inicio en Windows")
    st.code("run_local_ui_v2_37.bat", language="powershell")
    st.caption(DISCLAIMER)


def main():
    data = product_snapshot()
    if "screen" not in st.session_state: st.session_state.screen = "home"
    if "pending_screen" in st.session_state: st.session_state.screen = st.session_state.pop("pending_screen")
    with st.sidebar:
        st.markdown("## Scout Finance")
        st.caption("Producto local · v2.37")
        selected = st.radio("Navegación", list(SCREENS), format_func=SCREENS.get, index=list(SCREENS).index(st.session_state.screen))
        st.session_state.screen = selected
        st.divider(); st.caption(f"Datos: {data.mode.value}"); st.caption("Fase 7: INSUFFICIENT_EVIDENCE"); st.caption("Sin conexión a broker")
    if data.mode in {DataMode.BLOCKED_MISSING_DATA, DataMode.INCOMPATIBLE_VERSION}:
        render_home(data); st.error("La aplicación queda bloqueada: " + "; ".join(data.errors)); return
    {"home": render_home, "universe": render_universe, "ranking": render_ranking, "asset": render_asset, "compare": render_compare, "watchlist": render_watchlist, "reports": render_reports, "help": render_help}[selected](data)


if __name__ == "__main__":
    main()
