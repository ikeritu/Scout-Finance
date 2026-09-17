"""Scout Finance v2.37 — local research product."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from html import escape
from io import StringIO
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

from src.ui_v2_37.global_ranking import load_global_ranking
from src.ui_v2_37.global_universe import load_global_matrix, rebuild_global_matrix
from src.ui_v2_37.repository import DataMode, load_fundamentals, load_price_series, load_product_data
from src.ui_v2_37.reports import DISCLAIMER, asset_markdown, manifest, ranking_markdown, to_html, watchlist_markdown
from src.ui_v2_37.safe_demo import SAFE_DEMO_LABEL, blocked_message, is_safe_demo_mode, render_safe_demo_banner
from src.ui_v2_37.ui import apply, banner, heading
from src.ui_v2_37.watchlists import STATUSES, add, atomic_write, create, export_csv, read, remove, scan, update

ROOT = Path(__file__).resolve().parent
UNICORN_NOTES_PATH = ROOT / "data" / "user_unicorn_notes_v2_44i.json"
UNICORN_REVIEW_HISTORY_PATH = ROOT / "data" / "user_unicorn_review_history_v2_44k.json"
EXPLOSIVE_UNICORN_OVERLAY_PATH = ROOT / "data" / "user_explosive_unicorn_market_overlay_v2_45b.csv"
st.set_page_config(page_title="Scout Finance — Investigación local", page_icon="🔎", layout="wide")
apply(st)
SAFE_DEMO_MODE = is_safe_demo_mode()

SCREENS = {
    "home": "🏠 Inicio", "global_unicorns": "🦄 Unicornios", "global_universe": "🌍 Universo global (43.089)", "global_ranking": "🏆 Ranking global (experimental)", "universe": "🌐 Universo",
    "ranking": "📊 Ranking experimental", "asset": "🔎 Ficha de empresa", "compare": "⚖️ Comparador",
    "watchlist": "⭐ Watchlist", "reports": "📄 Informes", "final_guide": "🧭 Guía final y uso responsable", "help": "❓ Metodología y ayuda",
}
GLOBAL_STATUS_LABELS = {
    "NO_DATA_YET": "Sin datos todavía",
    "IDENTITY_ONLY_NO_FUNDAMENTALS_YET": "Solo identidad, sin fundamentales todavía",
    "IDENTITY_ONLY_NOT_AN_OPERATING_COMPANY": "Solo identidad — no es una empresa operativa (fondo de inversión)",
    "IDENTITY_ONLY_FUNDAMENTALS_BLOCKED_REAL_REASON_CONFIRMED": "Solo identidad — fundamentales bloqueados (motivo real confirmado)",
    "IDENTITY_ONLY_NO_PUBLIC_DISCLOSURE_REQUIRED": "Solo identidad — sin obligación legal de divulgación pública",
    "FUNDAMENTALS_PARTIAL_NO_GROWTH_YET": "Fundamentales parciales, sin crecimiento todavía",
    "FUNDAMENTALS_READY_NO_GROWTH_YET": "Fundamentales completos, sin crecimiento todavía",
    "GROWTH_PARTIAL": "Crecimiento parcial",
    "GROWTH_READY": "Crecimiento completo",
}
GLOBAL_FUNDAMENTALS_OR_BETTER = {"FUNDAMENTALS_PARTIAL_NO_GROWTH_YET", "FUNDAMENTALS_READY_NO_GROWTH_YET", "GROWTH_PARTIAL", "GROWTH_READY"}
GLOBAL_GROWTH_STATUSES = {"GROWTH_PARTIAL", "GROWTH_READY"}
GLOBAL_TABLE_LIMIT = 2000
GLOBAL_ELIGIBILITY_LABELS = {
    "ELIGIBLE_FULL": "Elegible completo (crecimiento + precio real)",
    "ELIGIBLE_PARTIAL_NO_PRICE": "Elegible parcial (sin precio real)",
    "ELIGIBLE_PARTIAL_SINGLE_PERIOD": "Elegible parcial (un solo periodo)",
    "REVIEW_REQUIRED_FINANCIAL_INSTITUTION": "Revisión requerida (entidad financiera)",
    "NOT_ELIGIBLE": "No elegible todavía",
    "": "Sin clasificar (pulsa Actualizar)",
}
GLOBAL_ELIGIBLE_TIERS = {"ELIGIBLE_FULL", "ELIGIBLE_PARTIAL_NO_PRICE", "ELIGIBLE_PARTIAL_SINGLE_PERIOD"}
GLOBAL_UNICORN_ICON = "🦄"
EXPLOSIVE_UNICORN_REQUIRED_SIGNALS = [
    "capitalizacion pequena o micro-cap real",
    "precio actual bajo o penny-stock real",
    "volumen anomalo / breakout real",
    "float reducido o short interest real",
    "catalizador verificable o momentum de precio reciente",
]
EXPLOSIVE_UNICORN_AVAILABLE_FIELDS = {
    "market_cap",
    "market_cap_usd",
    "float_shares",
    "short_interest",
    "short_float_pct",
    "avg_volume",
    "relative_volume",
    "last_price",
    "price_change_5d",
    "price_change_20d",
    "breakout_signal",
    "squeeze_signal",
    "penny_stock_signal",
    "micro_cap_signal",
}
EXPLOSIVE_UNICORN_DATA_CONTRACT = [
    {
        "field": "market_cap_usd",
        "label": "Capitalizacion bursatil USD",
        "required_for": "Micro-cap / small-cap / multibagger",
        "gate": "Bloquea etiqueta explosiva si falta",
        "source_policy": "Proveedor de mercado verificado o dataset local versionado",
    },
    {
        "field": "last_price",
        "label": "Precio actual o ultimo cierre",
        "required_for": "Penny stock / low-price runner",
        "gate": "Bloquea penny-stock si falta",
        "source_policy": "Precio real local; nunca estimado",
    },
    {
        "field": "relative_volume",
        "label": "Volumen relativo frente a media",
        "required_for": "Breakout / meme runner",
        "gate": "Bloquea breakout si falta",
        "source_policy": "Historico de volumen local con ventana documentada",
    },
    {
        "field": "float_shares",
        "label": "Acciones flotantes",
        "required_for": "Short squeeze / baja flotacion",
        "gate": "Bloquea squeeze si falta junto a short interest",
        "source_policy": "Dato corporativo/proveedor; sin inferencia manual",
    },
    {
        "field": "short_float_pct",
        "label": "Short interest sobre float",
        "required_for": "Short squeeze",
        "gate": "Bloquea squeeze si falta",
        "source_policy": "Dato real de short interest; no proxy fundamental",
    },
    {
        "field": "price_change_20d",
        "label": "Momentum precio 20 sesiones",
        "required_for": "Breakout / multibagger temprano",
        "gate": "Bloquea momentum explosivo si falta",
        "source_policy": "Calculado desde precios locales versionados",
    },
    {
        "field": "breakout_signal",
        "label": "Ruptura tecnica validada",
        "required_for": "Breakout stock",
        "gate": "Debe derivarse de precio/volumen, no de fundamentales",
        "source_policy": "Regla local reproducible con ventana y umbral",
    },
    {
        "field": "catalyst_note",
        "label": "Catalizador verificable",
        "required_for": "Meme/catalyst runner",
        "gate": "Opcional pero visible; si falta, rebaja confianza",
        "source_policy": "Solo texto trazable aportado por el usuario o fuente versionada",
    },
]
GLOBAL_UNICORN_STATUS_LABELS = {
    "EVALUATED_UNICORN": "🦄 Sí — cumple los 3 criterios de crecimiento reales",
    "EVALUATED_NOT_UNICORN": "No — evaluado, no cumple los criterios",
    "INSUFFICIENT_DATA": "Sin datos suficientes para evaluar",
    "": "Sin evaluar (pulsa Actualizar)",
}
GLOBAL_RANKING_STATUS_LABELS = {
    "ELIGIBLE_PARTIAL": "Ranking principal",
    "PARTIAL_COMPARABILITY": "Comparabilidad parcial (confianza baja)",
    "REVIEW_REQUIRED": "Revisión requerida",
    "BLOCKED": "Cobertura real insuficiente",
    "NOT_YET_SCORED_NO_ADAPTER": "Sin adaptador de datos todavía",
}
GLOBAL_RANKING_REVIEW_REASON_LABELS = {
    "absolute_margin_outside_300pct": "Margen fuera de ±300 % — revisión manual",
    "financial_institution_requires_separate_factor_contract": "Entidad financiera — necesita un contrato de factores distinto",
    "no_fundamentals_growth_ratio_adapter_built_yet_for_this_country": "Sin adaptador real de ratios/crecimiento todavía para este país",
}
GLOBAL_RANKING_EMPTY_MESSAGES = {
    "ELIGIBLE_PARTIAL": "No hay empresas en el ranking principal para los filtros actuales. Ajusta busqueda, pais, confianza, score, cobertura o Top N; la app no relaja criterios ni recalcula puntuaciones.",
    "PARTIAL_COMPARABILITY": "No hay empresas en comparabilidad parcial en esta vista. Si ocurre con datos reales, revisa que v2.38BV siga presente y que los filtros no hayan ocultado la poblacion.",
    "REVIEW_REQUIRED": "No hay empresas pendientes de revision en esta vista. La ausencia de filas no convierte ningun activo en apto para ranking.",
    "BLOCKED": "No hay empresas bloqueadas visibles en esta vista. La app nunca imputa datos para rellenar cobertura.",
    "NOT_YET_SCORED_NO_ADAPTER": "No hay empresas sin adaptador visibles en esta vista. Las limitaciones finales siguen documentadas en v2.41D.",
}
GLOBAL_RANKING_EXPORT_FILENAME = "scout_finance_ranking_experimental_filtered_v2_42a.csv"


def google_finance_search_url(company_name: str) -> str:
    """A plain Google Search deep-link, deliberately NOT a direct
    google.com/finance/quote/TICKER:EXCHANGE URL -- this project has no
    verified, real mapping from its own internal exchange codes to
    Google's exchange mnemonics (NASDAQ, ETR, BIT, LON...) across the
    dozens of markets in the census, and guessing one wrong for even a
    fraction of 43,089 companies would silently send the user to the
    wrong company's page. A name-based search always resolves to a real,
    legitimate Google results page (Google's own Finance card included,
    when Google has one) without that risk -- purely a manual-lookup
    convenience link, Scout Finance never fetches or stores anything
    from it."""
    return f"https://www.google.com/search?q={quote(f'{company_name} stock')}"


def explain_unicorn_reason(reason: str, country: str) -> list[str]:
    details = []
    lowered = reason.casefold()
    if "revenue_growth" in lowered or "fundamental_momentum_flag_true" in lowered:
        details.append("Crecimiento real de ingresos positivo en los datos fundamentales ya cargados.")
    if "margin_expansion" in lowered:
        details.append("Expansión real de margen: la empresa mejora rentabilidad operativa/negocio frente al periodo comparable.")
    if "positive_free_cash_flow" in lowered:
        details.append("Flujo de caja libre real positivo, cuando el origen de datos lo permite.")
    if "no_free_cash_flow_data_available_for_austria" in lowered:
        details.append("Para Austria no existe flujo de caja libre en este contrato local; se usa el criterio equivalente documentado: crecimiento positivo, aceleración de crecimiento y expansión de margen.")
    if "cross_referenced_from_real_us_entity" in lowered:
        details.append("Se conserva una referencia cruzada con la entidad estadounidense real equivalente ya identificada en fases anteriores.")
    if not details:
        details.append("Cumple el flag `EVALUATED_UNICORN` generado por v2.38BT usando señales reales ya existentes, sin estimaciones nuevas.")
    details.append(f"País/origen revisado en esta fila: {country or 'no informado'}.")
    details.append("No es una recomendación de compra: solo identifica empresas que cumplen el criterio interno de crecimiento combinado.")
    return details


def unicorn_criterion_badges(reason: str, country: str) -> list[str]:
    lowered = reason.casefold()
    badges = ["Crecimiento positivo", "Margen en expansión"]
    if "positive_free_cash_flow" in lowered:
        badges.append("FCF positivo")
    if "no_free_cash_flow_data_available_for_austria" in lowered or country == "Austria":
        badges.append("Criterio Austria")
    if "cross_referenced_from_real_us_entity" in lowered:
        badges.append("Referencia cruzada")
    return badges


def unicorn_probability(row: dict) -> int:
    """Confidence that the local unicorn label is well supported, not return probability."""
    reason = row.get("unicorn_reason", "").casefold()
    score = 68
    if "revenue_growth" in reason or "fundamental_momentum_flag_true" in reason:
        score += 8
    if "margin_expansion" in reason:
        score += 8
    if "positive_free_cash_flow" in reason:
        score += 8
    if "no_free_cash_flow_data_available_for_austria" in reason:
        score += 5
    if row.get("overall_coverage_status") == "GROWTH_READY":
        score += 4
    if row.get("eligibility_tier") == "SCORE_ELIGIBLE_FULL":
        score += 3
    if row.get("overall_coverage_status") == "GROWTH_PARTIAL":
        score -= 4
    if row.get("eligibility_tier") in {"REVIEW_REQUIRED", "PARTIAL_COMPARABILITY"}:
        score -= 3
    return max(55, min(score, 96))


def unicorn_evidence_grade(row: dict) -> tuple[str, str, str]:
    probability = unicorn_probability(row)
    if probability >= 90 and row.get("overall_coverage_status") == "GROWTH_READY":
        return "Muy respaldado", "green", "Criterios completos y cobertura de crecimiento completa."
    if probability >= 78:
        return "Respaldado", "blue", "Evidencia suficiente, con alguna limitacion menor de cobertura o comparabilidad."
    if row.get("overall_coverage_status") == "GROWTH_PARTIAL":
        return "Parcial", "orange", "Etiqueta valida, pero con cobertura de crecimiento parcial."
    return "Requiere revision", "red", "Conviene revisar la evidencia manualmente antes de priorizar."


def explosive_unicorn_data_fields(row: dict) -> list[str]:
    return [field for field in EXPLOSIVE_UNICORN_AVAILABLE_FIELDS if row.get(field) not in ("", None)]


def numeric_value(value) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def truthy_value(value) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "si", "sí", "y"}


def explosive_unicorn_status(row: dict) -> tuple[str, str, str]:
    fields = explosive_unicorn_data_fields(row)
    if not fields:
        return (
            "DATOS_INSUFICIENTES",
            "No evaluable como explosivo",
            "Faltan señales de mercado necesarias: capitalización, precio actual, float/short interest, volumen relativo, breakout o catalizador.",
        )
    reason = row.get("unicorn_reason", "").casefold()
    ticker = (row.get("ticker") or "").casefold()
    company = (row.get("company_name") or "").casefold()
    market_cap = numeric_value(row.get("market_cap_usd") or row.get("market_cap"))
    last_price = numeric_value(row.get("last_price"))
    relative_volume = numeric_value(row.get("relative_volume"))
    price_change_20d = numeric_value(row.get("price_change_20d"))
    float_shares = numeric_value(row.get("float_shares"))
    short_float_pct = numeric_value(row.get("short_float_pct") or row.get("short_interest"))
    tags = []
    if truthy_value(row.get("micro_cap_signal")) or (market_cap is not None and market_cap <= 300_000_000):
        tags.append("Micro-cap")
    if truthy_value(row.get("penny_stock_signal")) or (last_price is not None and last_price <= 5):
        tags.append("Penny stock")
    if truthy_value(row.get("squeeze_signal")) or (short_float_pct is not None and short_float_pct >= 15) or (float_shares is not None and float_shares <= 50_000_000 and short_float_pct is not None):
        tags.append("Short squeeze")
    if truthy_value(row.get("breakout_signal")) or (relative_volume is not None and relative_volume >= 2 and price_change_20d is not None and price_change_20d >= 20):
        tags.append("Breakout")
    if "growth" in reason and ("micro" in company or "micro" in ticker):
        tags.append("Multibagger investigable")
    if tags:
        return ("EXPLOSIVE_CANDIDATE", " / ".join(dict.fromkeys(tags)), "Tiene señales locales de mercado compatibles con una hipótesis explosiva; requiere revisión manual estricta.")
    return (
        "DATOS_MERCADO_PARCIALES",
        "Datos parciales, sin señal explosiva",
        "Hay algún dato de mercado, pero no basta para clasificarla como breakout, multibagger, squeeze, penny o micro-cap.",
    )


def explosive_unicorn_score(row: dict) -> int:
    status, _, _ = explosive_unicorn_status(row)
    if status == "EXPLOSIVE_CANDIDATE":
        return 72
    if status == "DATOS_MERCADO_PARCIALES":
        return 35
    return 0


def explosive_unicorn_contract_frame() -> pd.DataFrame:
    return pd.DataFrame(EXPLOSIVE_UNICORN_DATA_CONTRACT)


def explosive_unicorn_missing_fields(row: dict) -> list[str]:
    return [
        item["field"]
        for item in EXPLOSIVE_UNICORN_DATA_CONTRACT
        if row.get(item["field"]) in ("", None)
    ]


def explosive_unicorn_contract_report(rows: list[dict]) -> str:
    missing_counts = Counter(field for row in rows for field in explosive_unicorn_missing_fields(row))
    contract_lines = "\n".join(
        f"| {item['field']} | {item['label']} | {item['required_for']} | {item['gate']} |"
        for item in EXPLOSIVE_UNICORN_DATA_CONTRACT
    )
    missing_lines = "\n".join(
        f"- {field}: falta en {missing_counts.get(field, 0):,} de {len(rows):,} filas de calidad fundamental"
        for field in [item["field"] for item in EXPLOSIVE_UNICORN_DATA_CONTRACT]
    )
    return f"""# Contrato de datos para Unicornio explosivo — v2.45A

## Objetivo
Separar empresas de calidad fundamental de candidatos explosivos tipo breakout, multibagger, meme stock, short squeeze, penny stock o micro-cap.

## Regla de seguridad
Scout Finance no clasifica una accion como explosiva si faltan datos reales de mercado. Crecimiento, margen y caja ayudan a calidad fundamental, pero no bastan para squeeze, breakout o penny/micro-cap.

## Campos obligatorios
| Campo | Etiqueta | Uso | Gate |
|---|---|---|---|
{contract_lines}

## Cobertura actual
{missing_lines}

## Estado v2.45A
La capa queda preparada y cerrada: 0 candidatos explosivos evaluables si la matriz local no contiene los campos anteriores. No hay red, no hay API, no hay recomendacion, no hay precio objetivo y no hay trading.
"""


def explosive_unicorn_template_frame(rows: list[dict]) -> pd.DataFrame:
    sample = sorted(rows, key=unicorn_internal_rank_key)[:25]
    columns = [
        "asset_id",
        "ticker",
        "company_name",
        "market_cap_usd",
        "last_price",
        "relative_volume",
        "float_shares",
        "short_float_pct",
        "price_change_20d",
        "breakout_signal",
        "catalyst_note",
    ]
    records = []
    for row in sample:
        records.append({
            "asset_id": row.get("asset_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "market_cap_usd": "",
            "last_price": "",
            "relative_volume": "",
            "float_shares": "",
            "short_float_pct": "",
            "price_change_20d": "",
            "breakout_signal": "",
            "catalyst_note": "",
        })
    return pd.DataFrame(records, columns=columns)


def normalize_explosive_overlay(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    required = {"asset_id", "ticker", "market_cap_usd", "last_price", "relative_volume", "float_shares", "short_float_pct", "price_change_20d", "breakout_signal", "catalyst_note"}
    missing = sorted(required - set(df.columns))
    if missing:
        return pd.DataFrame(), [f"Faltan columnas obligatorias: {', '.join(missing)}"]
    normalized = df.copy()
    normalized["asset_id"] = normalized["asset_id"].fillna("").astype(str).str.strip()
    normalized["ticker"] = normalized["ticker"].fillna("").astype(str).str.strip()
    if not (normalized["asset_id"].astype(bool) | normalized["ticker"].astype(bool)).any():
        return pd.DataFrame(), ["Cada fila debe incluir asset_id o ticker para poder cruzarse con la matriz local."]
    return normalized, []


def load_explosive_overlay() -> pd.DataFrame:
    if not EXPLOSIVE_UNICORN_OVERLAY_PATH.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(EXPLOSIVE_UNICORN_OVERLAY_PATH)
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame()


def save_explosive_overlay(df: pd.DataFrame) -> None:
    EXPLOSIVE_UNICORN_OVERLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(EXPLOSIVE_UNICORN_OVERLAY_PATH, index=False)


def apply_explosive_overlay(rows: list[dict], overlay: pd.DataFrame) -> list[dict]:
    if overlay.empty:
        return rows
    by_asset = {str(item.get("asset_id", "")).strip(): item for item in overlay.to_dict("records") if str(item.get("asset_id", "")).strip()}
    by_ticker = {str(item.get("ticker", "")).strip().casefold(): item for item in overlay.to_dict("records") if str(item.get("ticker", "")).strip()}
    merged = []
    for row in rows:
        extra = by_asset.get(row.get("asset_id", "")) or by_ticker.get((row.get("ticker") or "").casefold()) or {}
        merged.append(row | {key: value for key, value in extra.items() if key not in {"company_name"} and value not in ("", None)})
    return merged


def yfinance_symbol(row: dict) -> str:
    ticker = (row.get("ticker") or "").strip()
    exchange = (row.get("exchange") or "").strip().upper()
    country = (row.get("country") or "").strip().upper()
    if not ticker:
        return ""
    if country == "USA" or exchange in {"NASDAQ", "NYSE", "AMEX", "NYSEARCA"}:
        return ticker.replace(".", "-")
    return ""


def pct_change_20d_from_history(history: pd.DataFrame) -> float | None:
    if history is None or history.empty or "Close" not in history or len(history["Close"].dropna()) < 21:
        return None
    closes = history["Close"].dropna()
    previous = float(closes.iloc[-21])
    latest = float(closes.iloc[-1])
    if previous == 0:
        return None
    return round(((latest / previous) - 1) * 100, 2)


def fetch_yfinance_explosive_overlay(rows: list[dict], limit: int = 40) -> tuple[pd.DataFrame, dict]:
    try:
        import yfinance as yf
    except ImportError:
        return pd.DataFrame(), {"status": "YFINANCE_NOT_INSTALLED", "processed": 0, "ok": 0, "failed": 0, "message": "yfinance no está instalado."}
    candidates = [row for row in sorted(rows, key=unicorn_internal_rank_key) if yfinance_symbol(row)][:limit]
    records = []
    failures = []
    for row in candidates:
        symbol = yfinance_symbol(row)
        try:
            ticker = yf.Ticker(symbol)
            fast = getattr(ticker, "fast_info", {}) or {}
            info = ticker.info or {}
            history = ticker.history(period="3mo", interval="1d", auto_adjust=False)
            price = fast.get("last_price") or info.get("currentPrice") or info.get("regularMarketPrice")
            market_cap = fast.get("market_cap") or info.get("marketCap")
            volume = fast.get("last_volume") or info.get("volume")
            avg_volume = info.get("averageVolume") or info.get("averageDailyVolume10Day")
            relative_volume = round(float(volume) / float(avg_volume), 2) if volume and avg_volume else ""
            short_float = info.get("shortPercentOfFloat")
            if short_float not in ("", None) and float(short_float) <= 1:
                short_float = round(float(short_float) * 100, 2)
            float_shares = info.get("floatShares")
            price_change_20d = pct_change_20d_from_history(history)
            breakout = bool(relative_volume not in ("", None) and price_change_20d is not None and float(relative_volume) >= 2 and price_change_20d >= 20)
            records.append({
                "asset_id": row.get("asset_id", ""),
                "ticker": row.get("ticker", ""),
                "company_name": row.get("company_name", ""),
                "market_cap_usd": market_cap or "",
                "last_price": price or "",
                "relative_volume": relative_volume,
                "float_shares": float_shares or "",
                "short_float_pct": short_float or "",
                "price_change_20d": price_change_20d if price_change_20d is not None else "",
                "breakout_signal": "true" if breakout else "",
                "catalyst_note": "yfinance_real_market_snapshot_v2_45c",
            })
        except Exception as exc:
            failures.append({"ticker": symbol, "error": str(exc)[:180]})
    summary = {
        "status": "OK" if records else "NO_ROWS",
        "processed": len(candidates),
        "ok": len(records),
        "failed": len(failures),
        "message": "Datos reales consultados via yfinance; sin broker, sin OpenAI y sin recomendacion.",
    }
    return pd.DataFrame(records), summary


def render_explosive_unicorn_overlay_import(rows: list[dict]) -> list[dict]:
    st.markdown("#### Motor explosivo")
    auto_cols = st.columns([1, 1, 3])
    max_rows = auto_cols[0].number_input("Tickers", min_value=5, max_value=100, value=40, step=5, key="explosive_yfinance_limit")
    if SAFE_DEMO_MODE:
        auto_cols[1].button("Actualizar datos reales", disabled=True, help=blocked_message("Actualizar datos reales de candidatos explosivos"))
    elif auto_cols[1].button("Actualizar datos reales", type="primary", help="Consulta yfinance para tickers compatibles, guarda cache local y no ejecuta broker ni recomendaciones."):
        with st.spinner("Consultando datos reales de mercado via yfinance..."):
            fetched, summary = fetch_yfinance_explosive_overlay(rows, int(max_rows))
        if fetched.empty:
            st.warning(f"No se pudo generar overlay automático. Estado: {summary['status']} · fallos: {summary['failed']}")
        else:
            normalized, errors = normalize_explosive_overlay(fetched)
            if errors:
                for error in errors:
                    st.error(error)
            else:
                save_explosive_overlay(normalized)
                st.success(f"Overlay automático guardado: {summary['ok']:,}/{summary['processed']:,} tickers OK · fallos {summary['failed']:,}.")
    auto_cols[2].caption("Fuente principal: yfinance real + cache local. CSV manual solo como fallback.")

    template = explosive_unicorn_template_frame(rows)
    current_overlay = load_explosive_overlay()
    if not current_overlay.empty:
        st.caption(f"Cache de mercado activa: {len(current_overlay):,} filas.")
    with st.expander("Fallback manual y cache de mercado", expanded=False):
        st.markdown("##### Fallback manual v2.45B")
        st.caption("Usa esto solo si el proveedor automático no cubre una acción o quieres revisar el cache guardado.")
        controls = st.columns(2)
        controls[0].download_button(
            "Descargar plantilla CSV",
            data=template.to_csv(index=False).encode("utf-8"),
            file_name="scout_finance_explosive_unicorn_overlay_template_v2_45b.csv",
            mime="text/csv",
        )
        uploaded = controls[1].file_uploader("Subir CSV de señales explosivas", type=["csv"], key="explosive_unicorn_overlay_upload")
        if uploaded is not None:
            try:
                uploaded_df = pd.read_csv(StringIO(uploaded.getvalue().decode("utf-8-sig")))
            except (UnicodeDecodeError, pd.errors.ParserError):
                st.error("No se pudo leer el CSV. Usa UTF-8 y separador coma.")
                uploaded_df = pd.DataFrame()
            normalized, errors = normalize_explosive_overlay(uploaded_df)
            if errors:
                for error in errors:
                    st.error(error)
            elif SAFE_DEMO_MODE:
                st.info(blocked_message("Guardar overlay de candidatos explosivos"))
                current_overlay = normalized
            else:
                save_explosive_overlay(normalized)
                current_overlay = normalized
                st.success(f"Overlay local guardado: {len(normalized):,} filas de señales explosivas.")
        if not current_overlay.empty:
            st.dataframe(current_overlay.head(50), use_container_width=True, hide_index=True, height=260)
    return apply_explosive_overlay(rows, current_overlay)


def unicorn_semantic_summary(rows: list[dict]) -> dict[str, int]:
    explosive_ready = [row for row in rows if explosive_unicorn_status(row)[0] == "EXPLOSIVE_CANDIDATE"]
    partial_market = [row for row in rows if explosive_unicorn_status(row)[0] == "DATOS_MERCADO_PARCIALES"]
    return {
        "quality": len(rows),
        "explosive": len(explosive_ready),
        "partial_market": len(partial_market),
        "blocked": len(rows) - len(explosive_ready) - len(partial_market),
    }


def render_unicorn_semantic_split(rows: list[dict]) -> tuple[str, list[dict]]:
    summary = unicorn_semantic_summary(rows)
    cols = st.columns(4)
    cols[0].metric("Calidad fundamental", f"{summary['quality']:,}")
    cols[1].metric("Explosivos evaluables", f"{summary['explosive']:,}")
    cols[2].metric("Datos mercado parciales", f"{summary['partial_market']:,}")
    cols[3].metric("Bloqueados por datos", f"{summary['blocked']:,}")
    mode = st.radio(
        "Tipo de descubrimiento",
        ["Calidad fundamental", "Unicornio explosivo"],
        horizontal=True,
        key="global_unicorn_semantic_mode",
        help="Calidad fundamental usa crecimiento/margen/caja. Unicornio explosivo exige señales de mercado como micro-cap, penny, short interest, float, volumen o breakout.",
    )
    if mode == "Unicornio explosivo":
        rows = render_explosive_unicorn_overlay_import(rows)
        summary = unicorn_semantic_summary(rows)
        st.caption("Busca Breakout Stocks, Multibaggers, Meme Stocks, Short Squeeze, Penny Stocks y Micro-Caps con datos reales de mercado.")
        st.caption("Exige capitalización, precio, volumen relativo, float, short interest, momentum y breakout/catalizador; no usa rentabilidad fundamental como sustituto.")
        st.caption(f"Resultado: {summary['explosive']:,} candidatos explosivos · {summary['partial_market']:,} con datos parciales · {summary['blocked']:,} bloqueados.")
        if summary["explosive"] == 0:
            st.warning("Sin candidatos explosivos evaluables todavía: faltan señales reales suficientes de mercado.")
        with st.expander("Contrato técnico y señales requeridas", expanded=False):
            contract_df = explosive_unicorn_contract_frame()
            missing_counts = Counter(field for row in rows for field in explosive_unicorn_missing_fields(row))
            coverage_df = pd.DataFrame([
                {
                    "Campo": item["field"],
                    "Uso": item["required_for"],
                    "Filas con dato": len(rows) - missing_counts.get(item["field"], 0),
                    "Filas sin dato": missing_counts.get(item["field"], 0),
                    "Gate": item["gate"],
                }
                for item in EXPLOSIVE_UNICORN_DATA_CONTRACT
            ])
            st.dataframe(coverage_df, use_container_width=True, hide_index=True, height=260)
            download_cols = st.columns(2)
            download_cols[0].download_button(
                "Descargar contrato CSV",
                data=contract_df.to_csv(index=False).encode("utf-8"),
                file_name="scout_finance_explosive_unicorn_data_contract_v2_45a.csv",
                mime="text/csv",
            )
            contract_report = explosive_unicorn_contract_report(rows)
            download_cols[1].download_button(
                "Descargar contrato Markdown",
                data=contract_report.encode("utf-8"),
                file_name="scout_finance_explosive_unicorn_data_contract_v2_45a.md",
                mime="text/markdown",
            )
            st.markdown("**Señales obligatorias:**")
            for signal in EXPLOSIVE_UNICORN_REQUIRED_SIGNALS:
                st.write(f"- {signal}")
    return mode, rows


def unicorn_internal_rank_key(row: dict) -> tuple:
    grade, _, _ = unicorn_evidence_grade(row)
    grade_order = {"Muy respaldado": 0, "Respaldado": 1, "Parcial": 2, "Requiere revision": 3}
    return (grade_order.get(grade, 9), -unicorn_probability(row), row.get("company_name", ""))


def unicorn_radar_values(row: dict) -> dict[str, int]:
    reason = row.get("unicorn_reason", "").casefold()
    return {
        "Crecimiento": 100 if "revenue_growth" in reason or "fundamental_momentum_flag_true" in reason else 70,
        "Margen": 100 if "margin_expansion" in reason else 65,
        "Caja": 100 if "positive_free_cash_flow" in reason else 70 if row.get("country") == "Austria" else 55,
        "Cobertura": 95 if row.get("overall_coverage_status") == "GROWTH_READY" else 72,
        "Evidencia": unicorn_probability(row),
    }


def load_unicorn_notes() -> dict[str, str]:
    if not UNICORN_NOTES_PATH.exists():
        return {}
    try:
        data = json.loads(UNICORN_NOTES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_unicorn_notes(notes: dict[str, str]) -> None:
    UNICORN_NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNICORN_NOTES_PATH.write_text(json.dumps(notes, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def load_unicorn_review_history() -> dict[str, dict]:
    if not UNICORN_REVIEW_HISTORY_PATH.exists():
        return {}
    try:
        data = json.loads(UNICORN_REVIEW_HISTORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_unicorn_review_history(history: dict[str, dict]) -> None:
    UNICORN_REVIEW_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNICORN_REVIEW_HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def unicorn_review_entry(history: dict[str, dict], asset_id: str) -> dict:
    entry = history.get(asset_id, {})
    return entry if isinstance(entry, dict) else {}


def unicorn_review_status(history: dict[str, dict], asset_id: str) -> str:
    status = unicorn_review_entry(history, asset_id).get("status", "PENDING")
    return status if status in UNICORN_REVIEW_STATUS_LABELS else "PENDING"


def update_unicorn_review_history(history: dict[str, dict], row: dict, status: str, note: str = "") -> None:
    history[row["asset_id"]] = {
        "status": status,
        "status_label": UNICORN_REVIEW_STATUS_LABELS[status],
        "reviewed_at": datetime.now().isoformat(timespec="seconds"),
        "asset_id": row["asset_id"],
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "note": note.strip(),
    }


def professional_unicorn_comparison(rows: list[dict]) -> str:
    lines = ["# Comparador profesional de unicornios", ""]
    for row in rows:
        grade, _, grade_reason = unicorn_evidence_grade(row)
        lines.extend([
            f"## {row.get('company_name')} ({row.get('ticker') or row.get('asset_id')})",
            f"- Posibilidad de unicornio: {unicorn_probability(row)}%",
            f"- Calidad de evidencia: {grade}. {grade_reason}",
            f"- Criterios: {', '.join(unicorn_criterion_badges(row.get('unicorn_reason', ''), row.get('country', '')))}",
            f"- Estado: {GLOBAL_STATUS_LABELS.get(row.get('overall_coverage_status', ''), row.get('overall_coverage_status', 'N/D'))}",
            "",
        ])
    lines.extend([
        "## Lectura responsable",
        "La comparacion ordena evidencia local, no atractivo financiero. No significa comprar, vender o mantener; no es precio objetivo ni probabilidad de rentabilidad.",
    ])
    return "\n".join(lines)


def global_unicorn_executive_report(rows: list[dict], all_rows: list[dict]) -> str:
    grade_counts = Counter(unicorn_evidence_grade(row)[0] for row in rows)
    country_counts = Counter(row.get("country") or "N/D" for row in rows)
    exchange_counts = Counter(row.get("exchange") or "N/D" for row in rows)
    top_rows = sorted(rows, key=unicorn_internal_rank_key)[:10]
    top_lines = "\n".join(
        f"- {row.get('company_name')} ({row.get('ticker') or row.get('asset_id')}): {unicorn_probability(row)}%, {unicorn_evidence_grade(row)[0]}"
        for row in top_rows
    ) or "- Sin resultados con los filtros actuales."
    grade_lines = "\n".join(f"- {label}: {count}" for label, count in grade_counts.most_common()) or "- Sin datos."
    country_lines = "\n".join(f"- {label}: {count}" for label, count in country_counts.most_common(10)) or "- Sin datos."
    exchange_lines = "\n".join(f"- {label}: {count}" for label, count in exchange_counts.most_common(10)) or "- Sin datos."
    return f"""# Informe ejecutivo global de unicornios

## 1. Resumen ejecutivo
Scout Finance identifica {len(all_rows)} unicornios locales con el flag `EVALUATED_UNICORN`. El subconjunto filtrado actual contiene {len(rows)} empresas. Este informe resume distribucion, calidad de evidencia, concentraciones y principales candidatos a revision humana; no ordena por rentabilidad esperada ni constituye asesoramiento financiero.

## 2. Calidad de evidencia
{grade_lines}

## 3. Distribucion por pais
{country_lines}

## 4. Distribucion por bolsa
{exchange_lines}

## 5. Primeros casos para revision
{top_lines}

## 6. Limitaciones de lectura
- El informe solo usa datos locales ya calculados.
- El ranking interno prioriza calidad de evidencia, no atractivo financiero.
- Las concentraciones por pais o bolsa pueden reflejar sesgos de cobertura del dataset.
- Cualquier decision fuera de Scout Finance exige revision manual independiente.

## 7. Conclusion responsable
El conjunto de unicornios es una lista de investigacion priorizada. No significa comprar, vender o mantener; no es precio objetivo y no es probabilidad de rentabilidad.
"""


def unicorn_portfolio_report(rows: list[dict], title: str) -> str:
    grade_counts = Counter(unicorn_evidence_grade(row)[0] for row in rows)
    country_counts = Counter(row.get("country") or "N/D" for row in rows)
    exchange_counts = Counter(row.get("exchange") or "N/D" for row in rows)
    lines = [f"# {title}", "", f"Unicornios incluidos: {len(rows)}", ""]
    lines.append("## Distribucion por calidad de evidencia")
    lines.extend(f"- {label}: {count}" for label, count in grade_counts.most_common())
    lines.append("")
    lines.append("## Distribucion por pais")
    lines.extend(f"- {label}: {count}" for label, count in country_counts.most_common(10))
    lines.append("")
    lines.append("## Distribucion por bolsa")
    lines.extend(f"- {label}: {count}" for label, count in exchange_counts.most_common(10))
    lines.append("")
    lines.append("## Componentes")
    for row in sorted(rows, key=unicorn_internal_rank_key):
        lines.append(f"- {row.get('company_name')} ({row.get('ticker') or row.get('asset_id')}): {unicorn_probability(row)}%, {unicorn_evidence_grade(row)[0]}, {row.get('country') or 'N/D'}, {row.get('exchange') or 'N/D'}")
    lines.extend([
        "",
        "## Lectura responsable",
        "Esta vista agrupa seguimiento de investigacion. No es cartera recomendada, no implica asignacion, no es precio objetivo y no constituye asesoramiento financiero.",
    ])
    return "\n".join(lines)


def analytical_unicorn_signal_rows(row: dict) -> list[dict[str, str]]:
    reason = row.get("unicorn_reason", "")
    radar = unicorn_radar_values(row)
    grade, _, grade_reason = unicorn_evidence_grade(row)
    return [
        {"Bloque": "Crecimiento", "Lectura": "Cumple" if radar["Crecimiento"] >= 100 else "Parcial", "Evidencia": "Crecimiento real positivo detectado en la razon tecnica."},
        {"Bloque": "Margen", "Lectura": "Cumple" if radar["Margen"] >= 100 else "Parcial", "Evidencia": "Expansion de margen presente en la razon tecnica."},
        {"Bloque": "Caja", "Lectura": "Cumple" if radar["Caja"] >= 100 else "Equivalente/limitado", "Evidencia": "FCF positivo en EE. UU.; Austria usa criterio equivalente sin FCF."},
        {"Bloque": "Cobertura", "Lectura": GLOBAL_STATUS_LABELS.get(row.get("overall_coverage_status", ""), row.get("overall_coverage_status", "N/D")), "Evidencia": f"{radar['Cobertura']}/100 en radar local."},
        {"Bloque": "Calidad", "Lectura": grade, "Evidencia": grade_reason},
        {"Bloque": "Motivo tecnico", "Lectura": row.get("unicorn_status", "N/D"), "Evidencia": reason or "Sin razon tecnica disponible."},
    ]


def analytical_unicorn_takeaways(row: dict) -> list[str]:
    company = row.get("company_name") or "La empresa"
    country = row.get("country") or "N/D"
    coverage = row.get("overall_coverage_status", "")
    eligibility = row.get("eligibility_tier", "")
    reason = row.get("unicorn_reason", "").casefold()
    takeaways = [
        f"{company} entra en la lista porque la evidencia local combina varias senales de crecimiento, no por una unica metrica aislada.",
    ]
    if "positive_free_cash_flow" in reason:
        takeaways.append("La lectura es mas robusta que un simple crecimiento de ventas: incorpora caja libre positiva, por lo que la expansion no aparece desligada de generacion de efectivo.")
    if "no_free_cash_flow_data_available_for_austria" in reason or country == "Austria":
        takeaways.append("El caso usa el contrato especifico de Austria: crecimiento positivo, aceleracion y expansion de margen, sin inventar FCF donde el dataset no lo contiene.")
    if "cross_referenced_from_real_us_entity" in reason:
        takeaways.append("La ficha exige especial cuidado operativo: existe una referencia cruzada con la entidad estadounidense real equivalente, asi que conviene revisar que ticker, mercado y entidad legal coincidan antes de cualquier analisis externo.")
    if coverage == "GROWTH_READY":
        takeaways.append("La cobertura de crecimiento esta completa dentro del contrato local, lo que mejora la confianza de clasificacion.")
    elif coverage == "GROWTH_PARTIAL":
        takeaways.append("La cobertura de crecimiento es parcial: la etiqueta puede ser valida, pero requiere mas revision manual que una ficha con crecimiento completo.")
    if eligibility in {"REVIEW_REQUIRED_FINANCIAL_INSTITUTION", "REVIEW_REQUIRED"}:
        takeaways.append("La elegibilidad requiere revision: la empresa no debe compararse mecanicamente con companias industriales sin revisar su contrato de factores.")
    elif eligibility:
        takeaways.append(f"La elegibilidad local figura como `{eligibility}`, dato util para entender comparabilidad, pero no convierte la etiqueta en recomendacion.")
    return takeaways


def analytical_unicorn_exit_triggers(row: dict) -> list[str]:
    country = row.get("country") or ""
    triggers = [
        "Crecimiento de ingresos deja de ser positivo en el proximo recálculo local.",
        "El margen deja de expandirse frente al periodo comparable.",
    ]
    if country == "Austria" or "no_free_cash_flow_data_available_for_austria" in row.get("unicorn_reason", ""):
        triggers.append("La aceleracion de crecimiento deja de cumplirse en el contrato especifico de Austria.")
    else:
        triggers.append("El flujo de caja libre deja de ser positivo en los datos fundamentales locales.")
    triggers.extend([
        "La empresa pasa a cobertura parcial, datos insuficientes o revision manual no comparable.",
        "Un recálculo local posterior con datos actualizados cambia el flag `EVALUATED_UNICORN`.",
    ])
    return triggers


def professional_unicorn_report(row: dict) -> str:
    probability = unicorn_probability(row)
    badges = unicorn_criterion_badges(row.get("unicorn_reason", ""), row.get("country", ""))
    details = explain_unicorn_reason(row.get("unicorn_reason", ""), row.get("country", ""))
    company = row.get("company_name") or "Empresa sin nombre"
    ticker = row.get("ticker") or row.get("asset_id") or "N/D"
    status = GLOBAL_STATUS_LABELS.get(row.get("overall_coverage_status", ""), row.get("overall_coverage_status", "N/D"))
    eligibility = GLOBAL_ELIGIBILITY_LABELS.get(row.get("eligibility_tier", ""), row.get("eligibility_tier", "N/D"))
    grade, _, grade_reason = unicorn_evidence_grade(row)
    radar = unicorn_radar_values(row)
    badge_text = ", ".join(badges)
    detail_text = "\n".join(f"- {item}" for item in details)
    signal_table = "\n".join(
        f"| {item['Bloque']} | {item['Lectura']} | {item['Evidencia']} |"
        for item in analytical_unicorn_signal_rows(row)
    )
    takeaways = "\n".join(f"- {item}" for item in analytical_unicorn_takeaways(row))
    exit_triggers = "\n".join(f"- {item}" for item in analytical_unicorn_exit_triggers(row))
    radar_text = "\n".join(f"- {key}: {value}/100" for key, value in radar.items())
    return f"""# Informe profesional de unicornio: {company}

## 1. Resumen ejecutivo
{company} ({ticker}) aparece marcada como unicornio porque cumple el flag local `EVALUATED_UNICORN` calculado en `v2.38BT`. La posibilidad de unicornio es {probability}% y la calidad de evidencia se clasifica como **{grade}**. Esta lectura mide confianza de clasificacion con la evidencia local disponible; no mide rentabilidad esperada, precio objetivo ni probabilidad de subida.

## 2. Identificacion y cobertura
- ID interno: {row.get("asset_id", "N/D")}
- Ticker: {ticker}
- Pais: {row.get("country") or "N/D"}
- Bolsa: {row.get("exchange") or "N/D"}
- Estado de cobertura: {status}
- Elegibilidad: {eligibility}
- Fuente del flag unicornio: {row.get("unicorn_source") or "N/D"}
- Fase de calculo: {row.get("unicorn_phase") or "v2.38BT"}

## 3. Tesis analitica personalizada
{takeaways}

## 4. Matriz de senales
| Bloque | Lectura | Evidencia |
|---|---|---|
{signal_table}

## 5. Radar cuantitativo local
{radar_text}

## 6. Senales que justifican la etiqueta
{detail_text}

## 7. Lectura tecnica de la posibilidad
La puntuacion {probability}% resume cuanta evidencia local acompana a la etiqueta: criterios cumplidos ({badge_text}), estado de crecimiento, calidad de cobertura y elegibilidad. En esta ficha, la lectura principal es: {grade_reason} Un porcentaje alto indica que la clasificacion esta mejor respaldada dentro del dataset local; no convierte la empresa en una recomendacion ni estima su rendimiento futuro.

## 8. Que podria hacer que deje de ser unicornio
{exit_triggers}

## 9. Limitaciones conocidas
- La etiqueta reutiliza datos locales ya calculados; no descarga informacion nueva.
- No valida noticias, guidance, deuda reciente, riesgos regulatorios ni eventos posteriores a la fecha del dataset.
- Si la cobertura es parcial o requiere revision, la lectura debe considerarse preliminar.
- Los codigos de bolsa internos no se transforman en una recomendacion operativa ni en una orden ejecutable.

## 10. Revision manual recomendada para {company}
- Revisar los ultimos estados financieros oficiales de {company}.
- Contrastar si el crecimiento positivo se mantiene y si no depende de un evento extraordinario.
- Verificar si la expansion de margen es operativa, contable o puntual.
- Revisar deuda, dilucion, liquidez, guidance y riesgos especificos del mercado {row.get("country") or "N/D"} / {row.get("exchange") or "N/D"}.
- Confirmar que la empresa sigue siendo comparable con su universo de referencia antes de usarla en cualquier analisis externo.
- Recalcular la pestaña de unicornios cuando entren nuevos fundamentales locales.

## 11. Conclusion responsable
{company} merece revision prioritaria como caso de crecimiento dentro de Scout Finance porque combina las senales locales exigidas por el criterio de unicornio. La lectura profesional es positiva para investigacion, pero sigue condicionada por frescura de datos, cobertura y revision manual. No constituye asesoramiento financiero. No significa comprar, vender o mantener; no es precio objetivo y no es probabilidad de beneficio.

## 12. Motivo tecnico original
```text
{row.get("unicorn_reason", "Sin motivo tecnico disponible")}
```
"""


def unicorn_ai_prompt_template(row: dict) -> str:
    report = professional_unicorn_report(row)
    radar = unicorn_radar_values(row)
    grade, _, grade_reason = unicorn_evidence_grade(row)
    return f"""# Prompt IA opcional — analisis extendido de unicornio

Actua como analista financiero tecnico y prudente. Tu tarea es redactar una explicacion profesional extensa usando EXCLUSIVAMENTE los datos locales estructurados incluidos abajo.

## Reglas obligatorias
- No recomiendes comprar, vender ni mantener.
- No des precio objetivo.
- No estimes rentabilidad futura.
- No inventes datos, noticias, guidance, deuda, ratios o eventos no incluidos.
- Si falta evidencia, dilo explicitamente.
- Distingue entre senales positivas, limitaciones y revision manual pendiente.
- Usa tono profesional, claro y no promocional.
- Incluye siempre: "No constituye asesoramiento financiero".

## Formato de salida requerido
1. Resumen ejecutivo.
2. Por que aparece como unicornio.
3. Calidad de evidencia.
4. Fortalezas observables.
5. Limitaciones y riesgos de interpretacion.
6. Preguntas para revision manual.
7. Conclusion responsable.

## Datos estructurados permitidos
- Empresa: {row.get("company_name")}
- ID interno: {row.get("asset_id")}
- Ticker: {row.get("ticker") or "N/D"}
- Pais: {row.get("country") or "N/D"}
- Bolsa: {row.get("exchange") or "N/D"}
- Posibilidad de unicornio: {unicorn_probability(row)}%
- Calidad de evidencia: {grade}. {grade_reason}
- Radar local: {radar}
- Criterios: {", ".join(unicorn_criterion_badges(row.get("unicorn_reason", ""), row.get("country", "")))}

## Informe local base
{report}

## Control final antes de responder
Comprueba que no has anadido una recomendacion financiera, un precio objetivo, una rentabilidad esperada ni datos externos no incluidos.
"""


def render_unicorn_presentation_mode(rows: list[dict], all_rows: list[dict]) -> None:
    top_rows = sorted(rows, key=unicorn_internal_rank_key)[:10]
    best_rows = top_rows[:3]
    grade_counts = Counter(unicorn_evidence_grade(row)[0] for row in rows)
    country_counts = Counter(row.get("country") or "N/D" for row in rows)

    st.markdown("### Modo presentación")
    st.caption("Vista limpia para enseñar Scout Finance: sin edición, sin tablas largas y sin controles técnicos. Solo evidencia local ya calculada.")
    st.info("Clasificación de investigación. No constituye asesoramiento financiero, no estima rentabilidad y no recomienda comprar, vender ni mantener.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Unicornios filtrados", f"{len(rows):,}")
    k2.metric("Universo unicornio", f"{len(all_rows):,}")
    k3.metric("Muy respaldados", f"{grade_counts.get('Muy respaldado', 0):,}")
    k4.metric("Países", f"{len(country_counts):,}")

    st.markdown("### Top 10 por evidencia local")
    top_table = pd.DataFrame([{
        "Empresa": row["company_name"],
        "Ticker": row["ticker"] or row["asset_id"],
        "País": row["country"],
        "Bolsa": row["exchange"],
        "Posibilidad": f"{unicorn_probability(row)}%",
        "Evidencia": unicorn_evidence_grade(row)[0],
    } for row in top_rows])
    st.dataframe(top_table, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Evidencia")
        st.bar_chart(pd.DataFrame({"Unicornios": dict(grade_counts)}))
    with c2:
        st.markdown("### Países principales")
        st.bar_chart(pd.DataFrame({"Unicornios": dict(country_counts.most_common(8))}))

    st.markdown("### Tres fichas destacadas")
    card_cols = st.columns(3)
    for col, row in zip(card_cols, best_rows):
        grade, _, reason = unicorn_evidence_grade(row)
        badges = " · ".join(unicorn_criterion_badges(row.get("unicorn_reason", ""), row.get("country", "")))
        col.markdown(
            f"""
            <div style="border:1px solid #d8e2ef;border-radius:8px;padding:14px;background:#ffffff;min-height:230px;">
              <div style="font-size:18px;font-weight:700;color:#0f172a;">{GLOBAL_UNICORN_ICON} {escape(row["company_name"])}</div>
              <div style="color:#64748b;font-size:13px;margin:4px 0 10px 0;">{escape(row["ticker"] or row["asset_id"])} · {escape(row["country"] or "N/D")} · {escape(row["exchange"] or "N/D")}</div>
              <div style="font-size:32px;font-weight:800;color:#0f766e;">{unicorn_probability(row)}%</div>
              <div style="font-size:13px;color:#475569;margin-bottom:8px;">posibilidad de etiqueta unicornio</div>
              <div style="font-weight:700;color:#334155;">{escape(grade)}</div>
              <div style="font-size:13px;color:#475569;margin:8px 0;">{escape(reason)}</div>
              <div style="font-size:12px;color:#64748b;">{escape(badges)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    presentation_report = global_unicorn_executive_report(rows, all_rows)
    st.download_button(
        "Descargar resumen de presentación",
        data=presentation_report.encode("utf-8"),
        file_name="scout_finance_presentacion_unicornios_v2_44n.md",
        mime="text/markdown",
    )


def render_unicorn_full_catalog(rows: list[dict], notes: dict[str, str], review_history: dict[str, dict]) -> None:
    st.markdown("### Fichas completas")
    st.caption("Catálogo completo de unicornios filtrados. Haz scroll por la lista y pulsa una compañía para abrir todos sus datos disponibles.")
    if not rows:
        st.info("No hay unicornios con los filtros actuales.")
        return

    left, right = st.columns([1.05, 1.95])
    with left:
        st.caption(f"{len(rows):,} compañías")
        for row in rows:
            grade, grade_color, _ = unicorn_evidence_grade(row)
            selected = st.session_state.get("selected_unicorn_asset_id") == row["asset_id"]
            label = f"{GLOBAL_UNICORN_ICON} {row['company_name']} · {row.get('ticker') or row['asset_id']} · {unicorn_probability(row)}%"
            if st.button(label, key=f"unicorn_full_select_{row['asset_id']}", type="primary" if selected else "secondary", use_container_width=True):
                st.session_state.selected_unicorn_asset_id = row["asset_id"]
            st.markdown(
                f"<div style='height:4px;background:{escape(grade_color)};border-radius:4px;margin:-8px 0 8px 0;' title='{escape(grade)}'></div>",
                unsafe_allow_html=True,
            )

    with right:
        selected_asset_id = st.session_state.get("selected_unicorn_asset_id")
        selected_row = next((row for row in rows if row["asset_id"] == selected_asset_id), rows[0])
        st.session_state.selected_unicorn_asset_id = selected_row["asset_id"]
        grade, _, grade_reason = unicorn_evidence_grade(selected_row)
        review_entry = unicorn_review_entry(review_history, selected_row["asset_id"])

        st.markdown(f"### {selected_row['company_name']}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Posibilidad", f"{unicorn_probability(selected_row)}%")
        k2.metric("Evidencia", grade)
        k3.metric("Ticker", selected_row.get("ticker") or "N/D")
        k4.metric("Revisión", UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, selected_row["asset_id"])])
        st.info(grade_reason)

        st.markdown("#### Identidad y mercado")
        identity = {
            "ID interno": selected_row.get("asset_id", ""),
            "Empresa": selected_row.get("company_name", ""),
            "Ticker": selected_row.get("ticker", ""),
            "País": selected_row.get("country", ""),
            "Bolsa": selected_row.get("exchange", ""),
            "Estado cobertura": GLOBAL_STATUS_LABELS.get(selected_row.get("overall_coverage_status", ""), selected_row.get("overall_coverage_status", "")),
            "Elegibilidad": GLOBAL_ELIGIBILITY_LABELS.get(selected_row.get("eligibility_tier", ""), selected_row.get("eligibility_tier", "")),
        }
        st.dataframe(pd.DataFrame([{"Campo": key, "Valor": value} for key, value in identity.items()]), use_container_width=True, hide_index=True)

        st.markdown("#### Evidencia unicornio")
        st.write(" · ".join(unicorn_criterion_badges(selected_row.get("unicorn_reason", ""), selected_row.get("country", ""))))
        st.bar_chart(pd.DataFrame({"Valor": unicorn_radar_values(selected_row)}).T)
        for item in explain_unicorn_reason(selected_row.get("unicorn_reason", ""), selected_row.get("country", "")):
            st.write(f"- {item}")

        st.markdown("#### Seguimiento local")
        follow_up = {
            "Nota personal": notes.get(selected_row["asset_id"], ""),
            "Estado revisión": UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, selected_row["asset_id"])],
            "Última revisión": review_entry.get("reviewed_at", ""),
            "Comentario revisión": review_entry.get("note", ""),
        }
        st.dataframe(pd.DataFrame([{"Campo": key, "Valor": value} for key, value in follow_up.items()]), use_container_width=True, hide_index=True)

        with st.expander("Todos los campos técnicos disponibles"):
            raw_rows = [{"Campo": key, "Valor": value} for key, value in sorted(selected_row.items())]
            st.dataframe(pd.DataFrame(raw_rows), use_container_width=True, hide_index=True, height=420)
        with st.expander("Informe profesional"):
            report = professional_unicorn_report(selected_row)
            st.markdown(report)
            st.download_button(
                "Descargar informe Markdown",
                data=report.encode("utf-8"),
                file_name=f"scout_finance_ficha_completa_unicornio_{selected_row['asset_id']}_v2_44o.md",
                mime="text/markdown",
                key="full_unicorn_report_download",
            )
        with st.expander("Prompt IA opcional"):
            ai_prompt = unicorn_ai_prompt_template(selected_row)
            st.code(ai_prompt, language="markdown")
            st.download_button(
                "Descargar prompt IA",
                data=ai_prompt.encode("utf-8"),
                file_name=f"scout_finance_prompt_ia_unicornio_{selected_row['asset_id']}_v2_44o.md",
                mime="text/markdown",
                key="full_unicorn_ai_prompt_download",
            )
        st.markdown(f"[Abrir búsqueda manual en Google Finance]({google_finance_search_url(selected_row['company_name'])})")


def render_unicorn_recalculation_panel(matrix, unicorn_rows: list[dict]) -> None:
    st.markdown("### Actualización de unicornios")
    before_ids = {row["asset_id"] for row in unicorn_rows}
    before_names = {row["asset_id"]: row["company_name"] for row in unicorn_rows}
    current_cutoff = matrix.generated_at or "no disponible"
    cols = st.columns([1, 3])
    if SAFE_DEMO_MODE:
        cols[0].button("Recalcular universo y unicornios", disabled=True, help=blocked_message("Recalcular universo y unicornios"))
        cols[1].info("Recalculo bloqueado en Modo demo seguro: la demo muestra datos locales estaticos.")
        return
    cols[1].caption(
        f"Último cálculo local: {current_cutoff} (UTC). El recálculo permite que entren y salgan empresas según los fundamentales y crecimiento locales disponibles."
    )
    if cols[0].button(
        "Recalcular universo y unicornios",
        type="primary",
        help="Reconstruye matriz, elegibilidad y flag de unicornios desde datos locales ya recolectados. No descarga datos nuevos ni consulta APIs.",
    ):
        with st.spinner("Recalculando universo, elegibilidad y unicornios desde datos locales..."):
            result = rebuild_global_matrix(ROOT)
        global_matrix_snapshot.clear()
        refreshed = global_matrix_snapshot()
        after_rows = [row for row in refreshed.rows if row.get("unicorn_status") == "EVALUATED_UNICORN"] if refreshed.available else []
        after_ids = {row["asset_id"] for row in after_rows}
        after_names = {row["asset_id"]: row["company_name"] for row in after_rows}
        entered = sorted(after_ids - before_ids, key=lambda asset_id: after_names.get(asset_id, asset_id))
        exited = sorted(before_ids - after_ids, key=lambda asset_id: before_names.get(asset_id, asset_id))
        (st.success if result.ok else st.error)(
            "Unicornios recalculados correctamente." if result.ok else "El recálculo falló; revisa el detalle técnico."
        )
        d1, d2, d3 = st.columns(3)
        d1.metric("Unicornios actuales", f"{len(after_ids):,}", delta=len(after_ids) - len(before_ids))
        d2.metric("Entraron", f"{len(entered):,}")
        d3.metric("Salieron", f"{len(exited):,}")
        if entered or exited:
            changes = []
            changes.extend({"Cambio": "Entra", "Empresa": after_names.get(asset_id, asset_id), "ID": asset_id} for asset_id in entered)
            changes.extend({"Cambio": "Sale", "Empresa": before_names.get(asset_id, asset_id), "ID": asset_id} for asset_id in exited)
            st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)
        else:
            st.info("No hubo cambios en la lista de unicornios con los datos locales actuales.")
        with st.expander("Detalle técnico del recálculo", expanded=not result.ok):
            for step in result.steps:
                (st.success if step.ok else st.error)(f"{step.label} · {step.seconds:.1f} s")
                if step.detail:
                    st.code(step.detail, language="text")


def unicorn_signal_timeline(row: dict) -> pd.DataFrame:
    radar = unicorn_radar_values(row)
    grade, _, _ = unicorn_evidence_grade(row)
    review_status = unicorn_review_status(load_unicorn_review_history(), row["asset_id"])
    steps = [
        ("Datos locales", max(55, radar["Cobertura"] - 8), "COVERAGE_READY" if radar["Cobertura"] >= 90 else "COVERAGE_PARTIAL"),
        ("Crecimiento", radar["Crecimiento"], "GROWTH_SIGNAL_OK" if radar["Crecimiento"] >= 100 else "GROWTH_SIGNAL_LIMITED"),
        ("Margen", radar["Margen"], "MARGIN_SIGNAL_OK" if radar["Margen"] >= 100 else "MARGIN_SIGNAL_LIMITED"),
        ("Caja / equivalente", radar["Caja"], "CASH_SIGNAL_OK" if radar["Caja"] >= 100 else "CASH_SIGNAL_EQUIVALENT_OR_LIMITED"),
        ("Etiqueta unicornio", radar["Evidencia"], row.get("unicorn_status", "EVALUATED_UNICORN")),
        ("Revision local", radar["Evidencia"] if review_status != "DISCARDED" else 45, review_status),
    ]
    return pd.DataFrame([
        {"Paso": label, "Confianza": value, "Estado": state, "Calidad": grade}
        for label, value, state in steps
    ])


def unicorn_visual_event_feed(row: dict, review_history: dict[str, dict]) -> pd.DataFrame:
    review_entry = unicorn_review_entry(review_history, row["asset_id"])
    events = [
        {"Evento": "Datos locales disponibles", "Detalle": GLOBAL_STATUS_LABELS.get(row.get("overall_coverage_status", ""), row.get("overall_coverage_status", "N/D"))},
        {"Evento": "Criterio unicornio evaluado", "Detalle": row.get("unicorn_status", "EVALUATED_UNICORN")},
        {"Evento": "Fuente del flag", "Detalle": row.get("unicorn_source") or "N/D"},
        {"Evento": "Calidad de evidencia", "Detalle": unicorn_evidence_grade(row)[0]},
    ]
    if review_entry:
        events.append({"Evento": "Revision local", "Detalle": f"{review_entry.get('status_label', 'N/D')} · {review_entry.get('reviewed_at', '')}"})
    else:
        events.append({"Evento": "Revision local", "Detalle": "Pendiente de revision manual"})
    events.append({"Evento": "Proximo recálculo", "Detalle": "Puede mantener, entrar en revision o salir si cambian crecimiento, margen, caja o cobertura."})
    return pd.DataFrame(events)


def render_unicorn_formula_panel(row: dict) -> None:
    country = row.get("country") or "N/D"
    cash_leg = "FCF positivo" if country != "Austria" else "aceleracion de crecimiento (contrato Austria)"
    st.code(
        "\n".join([
            "Etiqueta unicornio = crecimiento positivo + margen en expansion + caja/equivalente",
            f"Para esta empresa: crecimiento + margen + {cash_leg}",
            "Confianza visual = cobertura + calidad de senal + comparabilidad + revision local",
            "Salida de lista = falla cualquier pata clave en un recálculo local posterior",
        ]),
        language="text",
    )


def render_unicorn_company_motion(row: dict, grade: str, review_label: str) -> None:
    probability = unicorn_probability(row)
    radar = unicorn_radar_values(row)
    signal_rows = [
        ("Crecimiento", radar["Crecimiento"]),
        ("Margen", radar["Margen"]),
        ("Caja", radar["Caja"]),
        ("Cobertura", radar["Cobertura"]),
        ("Evidencia", radar["Evidencia"]),
    ]
    signal_html = "".join(
        f'<div class="sf-signal-row"><span>{escape(label)}</span><div class="sf-signal-bar" style="--sf-fill:{value}%"><span></span></div><strong>{value}</strong></div>'
        for label, value in signal_rows
    )
    checks = [
        "Crecimiento positivo validado",
        "Margen en expansión detectado",
        "Caja/equivalente revisado",
        f"Evidencia: {grade}",
    ]
    checks_html = "".join(
        f'<div class="sf-check"><span class="sf-check-dot">✓</span><span>{escape(item)}</span></div>'
        for item in checks
    )
    flow = ["Datos", "Crecimiento", "Margen", "Caja", "Unicornio", "Revisión"]
    flow_html = "".join(
        f'<span class="sf-verify-step {"active" if item in {"Unicornio", "Revisión"} else ""}">{escape(item)}</span>{"" if idx == len(flow) - 1 else "<span class=\"sf-verify-arrow\">→</span>"}'
        for idx, item in enumerate(flow)
    )
    st.markdown(
        f"""
        <div class="sf-company-motion">
          <div class="sf-gauge" style="--p:{probability}">
            <div class="sf-gauge-inner">
              <div class="sf-gauge-value">{probability}%</div>
              <div class="sf-gauge-label">confianza local</div>
            </div>
          </div>
          <div>
            <div class="sf-checklist">{checks_html}</div>
            <div class="sf-verify-flow">{flow_html}</div>
            <div class="sf-signal-bars">{signal_html}</div>
            <div style="margin-top:8px;color:#64748b;font-size:13px;">Estado local: {escape(review_label)} · no constituye asesoramiento financiero.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_unicorn_visual_analytics(rows: list[dict], notes: dict[str, str], review_history: dict[str, dict], generated_at: str) -> None:
    st.markdown("### Analítica visual de unicornios")
    st.caption("Vista más visual: tarjetas nítidas de selección y ficha a ancho completo para leer el informe sin dropdown borroso.")
    if not rows:
        st.info("No hay unicornios con los filtros actuales.")
        return
    if "selected_unicorn_asset_id" not in st.session_state or not any(row["asset_id"] == st.session_state.selected_unicorn_asset_id for row in rows):
        st.session_state.selected_unicorn_asset_id = rows[0]["asset_id"]

    page_size = 12
    total_pages = max(1, (len(rows) + page_size - 1) // page_size)
    selected_index = next((idx for idx, row in enumerate(rows) if row["asset_id"] == st.session_state.selected_unicorn_asset_id), 0)
    selected_page = selected_index // page_size
    current_page = min(st.session_state.get("unicorn_visual_cards_page", selected_page), total_pages - 1)
    if selected_page != current_page and st.session_state.get("unicorn_visual_sync_page", True):
        current_page = selected_page
    st.session_state.unicorn_visual_cards_page = current_page
    page_start = current_page * page_size
    page_end = min(page_start + page_size, len(rows))
    visual_rows = rows[page_start:page_end]
    st.caption(f"{len(rows):,} unicornios filtrados · mostrando {page_start + 1}-{page_end} · página {current_page + 1}/{total_pages}.")
    st.markdown(
        f"""
        <div class="sf-analysis-engine" aria-label="Motor visual de analisis local">
          <div class="sf-engine-grid">
            <div>
              <div class="sf-engine-title">Motor local analizando unicornios</div>
              <div class="sf-engine-sub">Crecimiento · margen · caja/equivalente · cobertura · revisión</div>
              <div class="sf-engine-progress"><span></span></div>
            </div>
            <div class="sf-node-map">
              <div class="sf-node-line"></div>
              <span class="sf-node" style="left:8%;top:36px;"></span>
              <span class="sf-node"></span>
              <span class="sf-node"></span>
              <span class="sf-node"></span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="sf-live-ticker" aria-label="Actividad local de analisis">
          <div class="sf-live-ticker-track">
            <span><span class="sf-live-dot"></span>Analizando evidencia local</span>
            <span>Sin red · datos locales</span>
            <span>{len(rows):,} unicornios filtrados</span>
            <span>Página {current_page + 1}/{total_pages}</span>
            <span>Informe personalizado listo al seleccionar ficha</span>
            <span><span class="sf-live-dot"></span>Analizando evidencia local</span>
            <span>Sin red · datos locales</span>
            <span>{len(rows):,} unicornios filtrados</span>
            <span>Página {current_page + 1}/{total_pages}</span>
            <span>Informe personalizado listo al seleccionar ficha</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for chunk_start in range(0, len(visual_rows), 3):
        cols = st.columns(3)
        for col, row in zip(cols, visual_rows[chunk_start:chunk_start + 3]):
            grade, grade_color, _ = unicorn_evidence_grade(row)
            selected = row["asset_id"] == st.session_state.selected_unicorn_asset_id
            with col:
                st.markdown(
                    f"""
                    <div class="sf-motion-card {'is-selected' if selected else ''}" style="--sf-fill:{unicorn_probability(row)}%;border:1px solid {'#0f766e' if selected else '#d8e2ef'};border-left:6px solid {escape(grade_color)};border-radius:8px;padding:10px 12px;background:{'#ecfeff' if selected else '#ffffff'};min-height:128px;margin-bottom:6px;">
                      <div style="font-weight:800;color:#0f172a;font-size:14px;line-height:1.25;">{escape(row.get("company_name") or "")}</div>
                      <div style="color:#64748b;font-size:12px;margin-top:4px;">{escape(row.get("ticker") or row.get("asset_id") or "")} · {escape(row.get("country") or "N/D")} · {escape(row.get("exchange") or "N/D")}</div>
                      <div style="display:flex;gap:10px;align-items:baseline;margin-top:8px;">
                        <span style="font-size:24px;font-weight:900;color:#0f766e;">{unicorn_probability(row)}%</span>
                        <span style="font-size:12px;color:#334155;">{escape(grade)}</span>
                      </div>
                      <div class="sf-confidence-track"><div class="sf-confidence-fill"></div></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Ver ficha", key=f"unicorn_visual_card_select_{row['asset_id']}", type="primary" if selected else "secondary", use_container_width=True):
                    st.session_state.selected_unicorn_asset_id = row["asset_id"]
                    st.session_state.unicorn_visual_sync_page = True

    nav_prev, nav_info, nav_next = st.columns([1, 2, 1])
    if nav_prev.button("← Anteriores", disabled=current_page == 0, use_container_width=True, key="unicorn_visual_prev_page"):
        st.session_state.unicorn_visual_cards_page = max(0, current_page - 1)
        st.session_state.unicorn_visual_sync_page = False
        st.rerun()
    nav_info.caption(f"Cards {page_start + 1}-{page_end} de {len(rows):,}")
    if nav_next.button("Siguientes →", disabled=current_page >= total_pages - 1, use_container_width=True, key="unicorn_visual_next_page"):
        st.session_state.unicorn_visual_cards_page = min(total_pages - 1, current_page + 1)
        st.session_state.unicorn_visual_sync_page = False
        st.rerun()

    selected = next((row for row in rows if row["asset_id"] == st.session_state.selected_unicorn_asset_id), rows[0])
    grade, _, grade_reason = unicorn_evidence_grade(selected)
    review_label = UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, selected["asset_id"])]
    st.markdown(f"## {GLOBAL_UNICORN_ICON} {selected.get('company_name')}")
    st.caption(f"{selected.get('ticker') or selected.get('asset_id')} · {selected.get('country') or 'N/D'} · {selected.get('exchange') or 'N/D'} · corte {generated_at[:10] if generated_at else 'N/D'}")
    hero = st.columns(4)
    hero[0].metric("Posibilidad", f"{unicorn_probability(selected)}%")
    hero[1].metric("Evidencia", grade)
    hero[2].metric("Estado", "Se mantiene")
    hero[3].metric("Revision", review_label)
    st.info(grade_reason)
    render_unicorn_company_motion(selected, grade, review_label)

    summary_tab, report_tab, technical_tab = st.tabs(["Resumen visual", "Informe completo personalizado", "Datos técnicos"])
    with summary_tab:
        formula_col, radar_col = st.columns([1.1, 1.0])
        with formula_col:
            st.markdown("#### Fórmula de señal")
            render_unicorn_formula_panel(selected)
        with radar_col:
            st.markdown("#### Radar local")
            st.bar_chart(pd.DataFrame({"Valor": unicorn_radar_values(selected)}).T)

        st.markdown("#### Timeline de señal")
        timeline = unicorn_signal_timeline(selected)
        st.line_chart(timeline.set_index("Paso")["Confianza"])
        st.dataframe(timeline, use_container_width=True, hide_index=True)

        st.markdown("#### Feed de recálculo y revisión")
        st.dataframe(unicorn_visual_event_feed(selected, review_history), use_container_width=True, hide_index=True)
        note = notes.get(selected["asset_id"], "").strip()
        if note:
            st.markdown("#### Nota personal")
            st.write(note)

    with report_tab:
        report = professional_unicorn_report(selected)
        st.markdown(report)
        st.download_button(
            "Descargar informe completo personalizado",
            data=report.encode("utf-8"),
            file_name=f"scout_finance_informe_personalizado_unicornio_{selected['asset_id']}_v2_44t.md",
            mime="text/markdown",
            key=f"visual_unicorn_report_download_{selected['asset_id']}",
        )

    with technical_tab:
        st.markdown("#### Estado técnico")
        st.dataframe(pd.DataFrame(analytical_unicorn_signal_rows(selected)), use_container_width=True, hide_index=True)
        st.markdown("#### Salidas posibles de la lista")
        for trigger in analytical_unicorn_exit_triggers(selected):
            st.write(f"- {trigger}")
        with st.expander("Todos los campos disponibles"):
            raw_rows = [{"Campo": key, "Valor": value} for key, value in sorted(selected.items())]
            st.dataframe(pd.DataFrame(raw_rows), use_container_width=True, hide_index=True, height=360)


def unicorn_sort_key(row: dict, sort_mode: str) -> tuple:
    if sort_mode == "País":
        return (row.get("country", ""), row.get("company_name", ""))
    if sort_mode == "Bolsa":
        return (row.get("exchange", ""), row.get("company_name", ""))
    if sort_mode == "Crecimiento completo primero":
        return (row.get("overall_coverage_status") != "GROWTH_READY", row.get("company_name", ""))
    if sort_mode == "Elegibilidad":
        return (row.get("eligibility_tier", ""), row.get("company_name", ""))
    return (row.get("company_name", ""),)


def unicorn_watchlist_asset(row: dict) -> dict:
    return {
        "asset_id": row["asset_id"],
        "ticker": row["ticker"],
        "company_name": row["company_name"],
        "market": row.get("country") or row.get("exchange") or "",
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
UNICORN_REVIEW_STATUS_LABELS = {
    "PENDING": "Pendiente",
    "REVIEWED": "Revisado",
    "FOLLOW": "Seguir",
    "DISCARDED": "Descartado",
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
def global_matrix_snapshot():
    return load_global_matrix(ROOT)


@st.cache_data(show_spinner=False)
def global_ranking_snapshot():
    return load_global_ranking(ROOT)


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


def display_rows(assets):
    return pd.DataFrame([{
        "ID": a["asset_id"], "Ticker": a["ticker"], "Empresa": a["company_name"], "Mercado": a["market"],
        "Estado": status_badge(a["eligibility_status"]), "Confianza": CONFIDENCE_LABELS.get(a["confidence"], a["confidence"]),
        "Score experimental": "N/D" if a.get("total_score") is None else f'{a["total_score"]:.2f}',
        "Posición": "N/D" if a.get("rank") is None else str(a["rank"]), "Sesiones": a["price_sessions"],
    } for a in assets])


def global_ranking_status_label(value: str) -> str:
    return GLOBAL_RANKING_STATUS_LABELS.get(value, value)


def global_ranking_review_reason_label(value: str) -> str:
    return GLOBAL_RANKING_REVIEW_REASON_LABELS.get(value, value.replace("_", " "))


def global_ranking_percentage(value) -> str:
    if value is None or value == "":
        return "N/D"
    return f"{float(value) * 100:.0f}%"


def global_ranking_empty_message(status: str) -> str:
    return GLOBAL_RANKING_EMPTY_MESSAGES.get(status, "No hay filas para mostrar con los filtros actuales.")


def global_ranking_search_match(row: dict, needle: str) -> bool:
    if not needle:
        return True
    return any(needle in str(row.get(key, "")).casefold() for key in ("asset_id", "ticker", "company_name", "country"))


def filter_global_ranking_rows(
    rows: list[dict],
    *,
    status: str,
    search: str = "",
    countries: list[str] | None = None,
    confidences: list[str] | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    min_coverage: float | None = None,
    max_coverage: float | None = None,
    top_n: int | None = None,
) -> list[dict]:
    """Pure UI helper: filter already-computed v2.38BV rows without scoring."""
    countries = countries or []
    confidences = confidences or []
    needle = search.casefold().strip()
    filtered = []
    for row in rows:
        if row.get("eligibility_status") != status:
            continue
        score = row.get("total_score")
        coverage = row.get("coverage_weight")
        if not global_ranking_search_match(row, needle):
            continue
        if countries and row.get("country", "") not in countries:
            continue
        if confidences and row.get("confidence", "") not in confidences:
            continue
        if min_score is not None and score is not None and float(score) < min_score:
            continue
        if max_score is not None and score is not None and float(score) > max_score:
            continue
        if min_coverage is not None and coverage is not None and float(coverage) < min_coverage:
            continue
        if max_coverage is not None and coverage is not None and float(coverage) > max_coverage:
            continue
        filtered.append(row)
    filtered.sort(key=lambda row: (row.get("rank") is None, row.get("rank") or 999999, -(row.get("total_score") or 0), row.get("ticker", "")))
    return filtered[:top_n] if top_n else filtered


def global_ranking_export_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{
        "rank": row.get("rank", ""),
        "asset_id": row.get("asset_id", ""),
        "ticker": row.get("ticker", ""),
        "company_name": row.get("company_name", ""),
        "country": row.get("country", ""),
        "eligibility_status": row.get("eligibility_status", ""),
        "eligibility_label": global_ranking_status_label(row.get("eligibility_status", "")),
        "confidence": row.get("confidence", ""),
        "total_score": row.get("total_score", ""),
        "coverage_weight": row.get("coverage_weight", ""),
        "review_reasons": "|".join(row.get("review_reasons", []) or []),
        "google_finance_search": google_finance_search_url(row.get("company_name", "")),
    } for row in rows])


def global_ranking_display_frame(rows: list[dict], *, include_rank: bool = True, include_reason: bool = False) -> pd.DataFrame:
    output = []
    for row in rows:
        item = {
            "Ticker": row.get("ticker", ""),
            "Empresa": row.get("company_name", ""),
            "País": row.get("country", ""),
            "Estado": global_ranking_status_label(row.get("eligibility_status", "")),
            "Confianza": CONFIDENCE_LABELS.get(row.get("confidence", ""), row.get("confidence", "")),
            "Score": "" if row.get("total_score") is None else round(float(row["total_score"]), 2),
            "Cobertura": global_ranking_percentage(row.get("coverage_weight")),
            "Google Finance": google_finance_search_url(row.get("company_name", "")),
        }
        if include_rank:
            item = {"Posición": row.get("rank", "")} | item
        if include_reason:
            item["Motivo"] = " · ".join(global_ranking_review_reason_label(reason) for reason in row.get("review_reasons", []) or [])
        output.append(item)
    return pd.DataFrame(output)


def render_home(data):
    heading(st, "Scout Finance", "Centro local de investigación financiera · v2.37")
    render_safe_demo_banner(st, SAFE_DEMO_MODE)
    banner(st)
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
    st.write("Explorar el universo, revisar el ranking experimental, consultar fichas, comparar activos, mantener una watchlist privada y exportar informes con trazabilidad.")
    st.markdown("### Qué no hace Scout Finance")
    st.write("No recomienda operaciones, no predice rentabilidad, no se conecta a brokers y no ejecuta trading automático.")


def render_global_universe(_data):
    heading(st, "Universo global", "Las 43.089 empresas del censo operativo completo, con el estado real de identidad, fundamentales, crecimiento y precio de cada una — lo que falta se marca, nunca se oculta.")
    render_safe_demo_banner(st, SAFE_DEMO_MODE)
    action_col, info_col = st.columns([1, 3])
    if SAFE_DEMO_MODE:
        action_col.button("🔄 Actualizar", disabled=True, help=blocked_message("Actualizar"))
        info_col.info("Actualización bloqueada en Modo demo seguro: la demo usa datos estáticos/offline ya generados.")
    elif action_col.button("🔄 Actualizar", type="primary", help="Recalcula la matriz a partir de los datos ya recolectados hasta ahora. No descarga ni consulta nada nuevo."):
        with st.spinner("Actualizando matriz de cobertura, contexto geopolítico, elegibilidad para scoring e icono unicornio (sin conexión de red)…"):
            result = rebuild_global_matrix(ROOT)
        global_matrix_snapshot.clear()
        (st.success if result.ok else st.error)("Matriz actualizada correctamente." if result.ok else "La actualización falló — revisa el detalle abajo.")
        with st.expander("Detalle de la actualización", expanded=not result.ok):
            for step in result.steps:
                (st.success if step.ok else st.error)(f"{step.label} · {step.seconds:.1f} s")
                if step.detail:
                    st.code(step.detail, language="text")
    matrix = global_matrix_snapshot()
    if not matrix.available:
        info_col.info(matrix.error)
        return
    info_col.caption(f"Última actualización: {matrix.generated_at} (UTC) · {len(matrix.rows):,} empresas · sin conexión de red — recalcula solo lo ya recolectado")
    counts = Counter(row["overall_coverage_status"] for row in matrix.rows)
    eligibility_counts = Counter(row.get("eligibility_tier", "") for row in matrix.rows)
    unicorn_counts = Counter(row.get("unicorn_status", "") for row in matrix.rows)
    metric_cols = st.columns(6)
    metric_cols[0].metric("Censo total", f"{len(matrix.rows):,}")
    metric_cols[1].metric("Con identidad real", f"{sum(v for k, v in counts.items() if k != 'NO_DATA_YET'):,}")
    metric_cols[2].metric("Con fundamentales reales", f"{sum(v for k, v in counts.items() if k in GLOBAL_FUNDAMENTALS_OR_BETTER):,}")
    metric_cols[3].metric("Con crecimiento real", f"{sum(v for k, v in counts.items() if k in GLOBAL_GROWTH_STATUSES):,}")
    metric_cols[4].metric("Elegibles para scoring", f"{sum(v for k, v in eligibility_counts.items() if k in GLOBAL_ELIGIBLE_TIERS):,}", help="Suma de los tres niveles ELIGIBLE_*; no incluye las que están en revisión por ser entidades financieras. Pulsa Actualizar si no se ha calculado todavía (v2.38BO).")
    metric_cols[5].metric(f"{GLOBAL_UNICORN_ICON} Unicornios", f"{unicorn_counts.get('EVALUATED_UNICORN', 0):,}", help="Empresas cuyo crecimiento real ya calculado cumple los 3 criterios reales combinados (v2.38BT): crecimiento de ingresos positivo, expansión real de margen y (en EE. UU.) flujo de caja libre real positivo. Nunca un score ni un ranking — una clasificación real sobre datos ya existentes. Pulsa Actualizar si no se ha calculado todavía.")
    st.markdown("### Desglose por estado")
    status_rows = [{"Estado": GLOBAL_STATUS_LABELS.get(status, status), "Empresas": count} for status, count in sorted(counts.items(), key=lambda kv: -kv[1])]
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    st.markdown("### Buscar en el censo")
    search = st.text_input("Buscar", placeholder="Empresa, ticker o ID", key="global_search")
    c1, c2, c3 = st.columns(3)
    countries = sorted({row["country"] for row in matrix.rows if row["country"]})
    country_filter = c1.multiselect("País", countries, placeholder="Todos")
    status_filter = c2.multiselect("Estado", sorted(counts), format_func=lambda value: GLOBAL_STATUS_LABELS.get(value, value), placeholder="Todos")
    eligibility_filter = c3.multiselect("Elegibilidad para scoring", sorted(eligibility_counts), format_func=lambda value: GLOBAL_ELIGIBILITY_LABELS.get(value, value), placeholder="Todas")
    unicorn_only = st.checkbox(f"Mostrar solo {GLOBAL_UNICORN_ICON} unicornios", help="Empresas con el criterio de crecimiento real más exigente ya calculado (v2.38BT) — nunca un ranking, solo las que cumplen los 3 criterios reales.")
    needle = search.casefold().strip()
    filtered = [
        row for row in matrix.rows
        if (not needle or any(needle in str(row.get(key, "")).casefold() for key in ("company_name", "ticker", "asset_id")))
        and (not country_filter or row["country"] in country_filter)
        and (not status_filter or row["overall_coverage_status"] in status_filter)
        and (not eligibility_filter or row.get("eligibility_tier", "") in eligibility_filter)
        and (not unicorn_only or row.get("unicorn_status", "") == "EVALUATED_UNICORN")
    ]
    st.caption(f"{len(filtered):,} de {len(matrix.rows):,} empresas")
    if len(filtered) > GLOBAL_TABLE_LIMIT:
        st.warning(f"Mostrando las primeras {GLOBAL_TABLE_LIMIT:,} filas de {len(filtered):,} — afina la búsqueda o los filtros para ver el resto.")
    table_rows = [{
        "ID": row["asset_id"], "Ticker": row["ticker"], "Empresa": row["company_name"],
        "Bolsa": row["exchange"], "País": row["country"], "Identidad": row["identity_status"],
        "Fundamentales": row["fundamentals_status"], "Crecimiento": row["growth_status"], "Precio": row["price_status"],
        "Estado": GLOBAL_STATUS_LABELS.get(row["overall_coverage_status"], row["overall_coverage_status"]),
        "Elegibilidad": GLOBAL_ELIGIBILITY_LABELS.get(row.get("eligibility_tier", ""), row.get("eligibility_tier", "")),
        GLOBAL_UNICORN_ICON: GLOBAL_UNICORN_ICON if row.get("unicorn_status") == "EVALUATED_UNICORN" else "",
        "Google Finance": google_finance_search_url(row["company_name"]),
    } for row in filtered[:GLOBAL_TABLE_LIMIT]]
    st.dataframe(
        pd.DataFrame(table_rows), use_container_width=True, hide_index=True,
        column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver 🔗", help="Abre una búsqueda real de Google para esta empresa — Scout Finance no descarga ni procesa ningún dato de Google, solo te lleva hasta allí para que lo consultes tú.")},
    )


def render_global_unicorns(_data):
    heading(st, "Unicornios", "Centro de descubrimiento separado: calidad fundamental ya calculada frente a candidatos explosivos tipo breakout, multibagger, squeeze, penny stock o micro-cap.")
    render_safe_demo_banner(st, SAFE_DEMO_MODE)
    matrix = global_matrix_snapshot()
    if not matrix.available:
        st.info(matrix.error)
        return
    unicorn_rows = [row for row in matrix.rows if row.get("unicorn_status") == "EVALUATED_UNICORN"]
    evaluated_rows = [row for row in matrix.rows if row.get("unicorn_status") in {"EVALUATED_UNICORN", "EVALUATED_NOT_UNICORN", "INSUFFICIENT_DATA"}]
    counts = Counter(row.get("overall_coverage_status", "") for row in unicorn_rows)
    metric_cols = st.columns(5)
    semantic_counts = unicorn_semantic_summary(unicorn_rows)
    metric_cols[0].metric("Calidad fundamental", f"{semantic_counts['quality']:,}")
    metric_cols[1].metric("Empresas evaluadas", f"{len(evaluated_rows):,}")
    metric_cols[2].metric("Con crecimiento completo", f"{counts.get('GROWTH_READY', 0):,}")
    metric_cols[3].metric("Explosivos evaluables", f"{semantic_counts['explosive']:,}")
    metric_cols[4].metric("Censo total", f"{len(matrix.rows):,}")
    st.info("Cambio v2.44Z: los 161 casos heredados pasan a leerse como `Calidad fundamental / momentum fundamental`, no como acciones explosivas. La categoría `Unicornio explosivo` queda separada y exige señales de mercado que hoy no están en la matriz local.")
    st.caption("El porcentaje actual mide confianza de clasificación fundamental; no es probabilidad de subida, short squeeze, multibagger, precio objetivo ni consejo de compra.")
    st.caption(f"Última actualización: {matrix.generated_at} (UTC) · {len(unicorn_rows):,} casos de calidad fundamental · sin conexión de red")
    discovery_mode, semantic_rows = render_unicorn_semantic_split(unicorn_rows)
    if discovery_mode == "Unicornio explosivo":
        explosive_rows = [row for row in semantic_rows if explosive_unicorn_status(row)[0] == "EXPLOSIVE_CANDIDATE"]
        if explosive_rows:
            st.success(f"{len(explosive_rows):,} candidatos explosivos evaluables con señales locales de mercado.")
            unicorn_rows = explosive_rows
            counts = Counter(row.get("overall_coverage_status", "") for row in unicorn_rows)
        else:
            st.stop()
    render_unicorn_recalculation_panel(matrix, unicorn_rows)
    notes = load_unicorn_notes()
    review_history = load_unicorn_review_history()

    st.markdown("### Buscar calidad fundamental")
    search = st.text_input("Buscar", placeholder="Empresa, ticker o ID", key="global_unicorn_search")
    c1, c2, c3 = st.columns(3)
    countries = sorted({row["country"] for row in unicorn_rows if row["country"]})
    country_filter = c1.multiselect("País", countries, placeholder="Todos", key="global_unicorn_country")
    status_filter = c2.multiselect("Estado", sorted(counts), format_func=lambda value: GLOBAL_STATUS_LABELS.get(value, value), placeholder="Todos", key="global_unicorn_status")
    eligibility_counts = Counter(row.get("eligibility_tier", "") for row in unicorn_rows)
    eligibility_filter = c3.multiselect("Elegibilidad para scoring", sorted(eligibility_counts), format_func=lambda value: GLOBAL_ELIGIBILITY_LABELS.get(value, value), placeholder="Todas", key="global_unicorn_eligibility")
    with st.expander("Búsqueda avanzada", expanded=False):
        a1, a2, a3, a4 = st.columns(4)
        min_probability = a1.slider("Porcentaje mínimo", min_value=55, max_value=96, value=55, step=1, key="global_unicorn_min_probability")
        evidence_filter = a2.multiselect("Calidad de evidencia", ["Muy respaldado", "Respaldado", "Parcial", "Requiere revision"], placeholder="Todas", key="global_unicorn_evidence_filter")
        review_filter = a3.multiselect("Estado de revisión", list(UNICORN_REVIEW_STATUS_LABELS), format_func=lambda value: UNICORN_REVIEW_STATUS_LABELS[value], placeholder="Todos", key="global_unicorn_review_filter")
        notes_only = a4.checkbox("Solo con notas personales", key="global_unicorn_notes_only")
    quick_filter = st.radio(
        "Filtros rápidos",
        ["Todos", "Top confianza", "Muy respaldados", "Crecimiento completo", "Revisión requerida", "USA", "Europa"],
        horizontal=True,
        key="global_unicorn_quick_filter",
    )
    needle = search.casefold().strip()
    filtered = [
        row for row in unicorn_rows
        if (not needle or any(needle in str(row.get(key, "")).casefold() for key in ("company_name", "ticker", "asset_id")))
        and (not country_filter or row["country"] in country_filter)
        and (not status_filter or row["overall_coverage_status"] in status_filter)
        and (not eligibility_filter or row.get("eligibility_tier", "") in eligibility_filter)
        and unicorn_probability(row) >= min_probability
        and (not evidence_filter or unicorn_evidence_grade(row)[0] in evidence_filter)
        and (not review_filter or unicorn_review_status(review_history, row["asset_id"]) in review_filter)
        and (not notes_only or bool(notes.get(row["asset_id"], "").strip()))
    ]
    if quick_filter == "Top confianza":
        filtered = [row for row in filtered if unicorn_probability(row) >= 90]
    elif quick_filter == "Muy respaldados":
        filtered = [row for row in filtered if unicorn_evidence_grade(row)[0] == "Muy respaldado"]
    elif quick_filter == "Crecimiento completo":
        filtered = [row for row in filtered if row.get("overall_coverage_status") == "GROWTH_READY"]
    elif quick_filter == "Revisión requerida":
        filtered = [row for row in filtered if row.get("eligibility_tier") == "REVIEW_REQUIRED"]
    elif quick_filter == "USA":
        filtered = [row for row in filtered if row.get("country") == "USA"]
    elif quick_filter == "Europa":
        filtered = [row for row in filtered if row.get("country") and row.get("country") != "USA"]
    controls = st.columns([1, 1, 1])
    sort_mode = controls[0].selectbox("Ordenar por", ["Ranking interno de unicornios", "Empresa", "País", "Bolsa", "Crecimiento completo primero", "Elegibilidad"], key="global_unicorn_sort")
    filtered = sorted(filtered, key=unicorn_internal_rank_key if sort_mode == "Ranking interno de unicornios" else lambda row: unicorn_sort_key(row, sort_mode))
    st.caption(f"{len(filtered):,} de {len(unicorn_rows):,} unicornios")
    grade_counts = Counter(unicorn_evidence_grade(row)[0] for row in filtered)
    grade_cols = st.columns(4)
    for col, label in zip(grade_cols, ["Muy respaldado", "Respaldado", "Parcial", "Requiere revision"]):
        col.metric(label, f"{grade_counts.get(label, 0):,}")
    review_counts = Counter(unicorn_review_status(review_history, row["asset_id"]) for row in filtered)
    review_cols = st.columns(4)
    for col, status in zip(review_cols, ["PENDING", "REVIEWED", "FOLLOW", "DISCARDED"]):
        col.metric(UNICORN_REVIEW_STATUS_LABELS[status], f"{review_counts.get(status, 0):,}")
    st.caption("Ranking interno y semáforo ordenan calidad de evidencia local, no rentabilidad esperada ni recomendación financiera.")
    view_mode = st.radio("Vista", ["Analítica visual", "Fichas completas", "Presentación/demo", "Cockpit limpio", "Tarjetas visuales", "Tabla completa"], horizontal=True, key="global_unicorn_view_mode")
    if filtered and "selected_unicorn_asset_id" not in st.session_state:
        st.session_state.selected_unicorn_asset_id = filtered[0]["asset_id"]
    watchlist_path = watchlist_data = None
    if SAFE_DEMO_MODE:
        st.info(blocked_message("Añadir unicornios a watchlist"))
    else:
        watchlist_path, watchlist_data = select_watchlist()
        if watchlist_data is None:
            st.info("Crea una watchlist en la pantalla ⭐ Watchlist antes de guardar unicornios.")
    top_country_rows = [{"País": country or "N/D", "Unicornios": count} for country, count in Counter(row.get("country", "") for row in filtered).most_common(8)]
    top_exchange_rows = [{"Bolsa": exchange or "N/D", "Unicornios": count} for exchange, count in Counter(row.get("exchange", "") for row in filtered).most_common(8)]
    summary_cols = st.columns(2)
    with summary_cols[0]:
        st.markdown("### Top países")
        st.dataframe(pd.DataFrame(top_country_rows), use_container_width=True, hide_index=True)
    with summary_cols[1]:
        st.markdown("### Top bolsas")
        st.dataframe(pd.DataFrame(top_exchange_rows), use_container_width=True, hide_index=True)

    executive_report = global_unicorn_executive_report(filtered, unicorn_rows)
    with st.expander("Informe ejecutivo global de unicornios"):
        st.markdown(executive_report)
        st.download_button(
            "Descargar informe ejecutivo global",
            data=executive_report.encode("utf-8"),
            file_name="scout_finance_informe_ejecutivo_global_unicornios_v2_44j.md",
            mime="text/markdown",
        )

    watchlist_ids = {item.get("asset_id") for item in watchlist_data.get("items", [])} if watchlist_data else set()
    portfolio_rows = [row for row in unicorn_rows if row["asset_id"] in watchlist_ids]
    portfolio_title = "Portfolio/watchlist de unicornios"
    if not portfolio_rows:
        portfolio_rows = [row for row in unicorn_rows if notes.get(row["asset_id"], "").strip()]
        portfolio_title = "Seguimiento local de unicornios con notas"
    with st.expander("Portfolio/watchlist de unicornios"):
        st.caption("Agrupa unicornios guardados en la watchlist seleccionada; si no hay watchlist con unicornios, usa los que tienen notas personales.")
        if portfolio_rows:
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Incluidos", f"{len(portfolio_rows):,}")
            p2.metric("Muy respaldados", f"{sum(unicorn_evidence_grade(row)[0] == 'Muy respaldado' for row in portfolio_rows):,}")
            p3.metric("Países", f"{len({row.get('country') for row in portfolio_rows if row.get('country')}):,}")
            p4.metric("Bolsas", f"{len({row.get('exchange') for row in portfolio_rows if row.get('exchange')}):,}")
            portfolio_table = pd.DataFrame([{
                "Empresa": row["company_name"],
                "Ticker": row["ticker"] or row["asset_id"],
                "País": row["country"],
                "Bolsa": row["exchange"],
                "Posibilidad": f"{unicorn_probability(row)}%",
                "Evidencia": unicorn_evidence_grade(row)[0],
                "Nota": notes.get(row["asset_id"], ""),
            } for row in sorted(portfolio_rows, key=unicorn_internal_rank_key)])
            st.dataframe(portfolio_table, use_container_width=True, hide_index=True)
            portfolio_report = unicorn_portfolio_report(portfolio_rows, portfolio_title)
            st.download_button(
                "Descargar portfolio Markdown",
                data=portfolio_report.encode("utf-8"),
                file_name="scout_finance_portfolio_unicornios_v2_44l.md",
                mime="text/markdown",
            )
            st.download_button(
                "Exportar portfolio CSV",
                data=portfolio_table.to_csv(index=False).encode("utf-8"),
                file_name="scout_finance_portfolio_unicornios_v2_44l.csv",
                mime="text/csv",
            )
        else:
            st.info("Todavía no hay unicornios guardados en watchlist ni unicornios con notas personales.")

    if view_mode == "Analítica visual":
        render_unicorn_visual_analytics(filtered, notes, review_history, matrix.generated_at)

    if view_mode == "Fichas completas":
        render_unicorn_full_catalog(filtered, notes, review_history)

    if view_mode == "Presentación/demo":
        render_unicorn_presentation_mode(filtered, unicorn_rows)

    if view_mode == "Cockpit limpio":
        st.markdown("### Cockpit limpio")
        left, right = st.columns([1.15, 1.85])
        with left:
            st.caption("Lista compacta ordenada por evidencia local.")
            for row in filtered[:40]:
                grade_label, grade_color, _ = unicorn_evidence_grade(row)
                review_label = UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, row["asset_id"])]
                selected = st.session_state.get("selected_unicorn_asset_id") == row["asset_id"]
                label = f"{GLOBAL_UNICORN_ICON} {row['company_name']} · {unicorn_probability(row)}% · {grade_label} · {review_label}"
                if st.button(label, key=f"unicorn_clean_select_{row['asset_id']}", type="primary" if selected else "secondary", use_container_width=True):
                    st.session_state.selected_unicorn_asset_id = row["asset_id"]
                st.markdown(
                    f"<div style='height:4px;background:{escape(grade_color)};border-radius:4px;margin:-8px 0 8px 0;'></div>",
                    unsafe_allow_html=True,
                )
            if len(filtered) > 40:
                st.caption(f"Mostrando 40 de {len(filtered)}. Usa búsqueda avanzada para afinar.")
        with right:
            selected_asset_id = st.session_state.get("selected_unicorn_asset_id")
            selected_row = next((row for row in filtered if row["asset_id"] == selected_asset_id), filtered[0] if filtered else None)
            if selected_row:
                grade_label, _, grade_reason = unicorn_evidence_grade(selected_row)
                st.markdown(f"### {selected_row['company_name']}")
                k1, k2, k3 = st.columns(3)
                k1.metric("Posibilidad", f"{unicorn_probability(selected_row)}%")
                k2.metric("Evidencia", grade_label)
                k3.metric("Revisión", UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, selected_row["asset_id"])])
                st.info(grade_reason)
                st.write("**Criterios**")
                st.write(" · ".join(unicorn_criterion_badges(selected_row.get("unicorn_reason", ""), selected_row.get("country", ""))))
                st.write("**Radar**")
                st.bar_chart(pd.DataFrame({"Valor": unicorn_radar_values(selected_row)}).T)
                with st.expander("Informe profesional"):
                    report = professional_unicorn_report(selected_row)
                    st.markdown(report)
                    st.download_button(
                        "Descargar informe Markdown",
                        data=report.encode("utf-8"),
                        file_name=f"scout_finance_informe_unicornio_{selected_row['asset_id']}_v2_44j.md",
                        mime="text/markdown",
                        key="clean_unicorn_report_download",
                    )
                with st.expander("Prompt IA opcional"):
                    ai_prompt = unicorn_ai_prompt_template(selected_row)
                    st.caption("Plantilla para copiar/pegar en una IA o integrar con API en una fase futura. No ejecuta llamadas externas.")
                    st.code(ai_prompt, language="markdown")
                    st.download_button(
                        "Descargar prompt IA",
                        data=ai_prompt.encode("utf-8"),
                        file_name=f"scout_finance_prompt_ia_unicornio_{selected_row['asset_id']}_v2_44m.md",
                        mime="text/markdown",
                        key="clean_unicorn_ai_prompt_download",
                    )
                st.markdown("**Notas personales**")
                note_value = st.text_area("Nota local", value=notes.get(selected_row["asset_id"], ""), key="clean_unicorn_note", height=120)
                st.markdown("**Historial de revisión**")
                current_status = unicorn_review_status(review_history, selected_row["asset_id"])
                status_choice = st.selectbox(
                    "Estado de revisión",
                    list(UNICORN_REVIEW_STATUS_LABELS),
                    index=list(UNICORN_REVIEW_STATUS_LABELS).index(current_status),
                    format_func=lambda value: UNICORN_REVIEW_STATUS_LABELS[value],
                    key="clean_unicorn_review_status",
                )
                review_note = st.text_input("Comentario de revisión", value=unicorn_review_entry(review_history, selected_row["asset_id"]).get("note", ""), key="clean_unicorn_review_note")
                if SAFE_DEMO_MODE:
                    st.caption(blocked_message("Guardar notas e historial"))
                elif st.button("Guardar nota e historial", key="clean_unicorn_note_save"):
                    notes[selected_row["asset_id"]] = note_value.strip()
                    save_unicorn_notes(notes)
                    update_unicorn_review_history(review_history, selected_row, status_choice, review_note)
                    save_unicorn_review_history(review_history)
                    st.success("Nota e historial guardados localmente.")

    if view_mode == "Tarjetas visuales":
        st.markdown("### Explorador visual")
        st.caption("Todas las empresas filtradas aparecen como tarjetas. Usa scroll y pulsa Ver detalle para abrir la explicación completa.")
        for start in range(0, len(filtered), 3):
            cols = st.columns(3)
            for col, row in zip(cols, filtered[start:start + 3]):
                badges = "".join(
                    f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:3px 7px;border-radius:8px;background:#e8f5e9;color:#0b6b2b;font-size:12px;">{escape(badge)}</span>'
                    for badge in unicorn_criterion_badges(row.get("unicorn_reason", ""), row.get("country", ""))
                )
                status_label = GLOBAL_STATUS_LABELS.get(row["overall_coverage_status"], row["overall_coverage_status"])
                probability = unicorn_probability(row)
                grade_label, grade_color, grade_reason = unicorn_evidence_grade(row)
                radar = unicorn_radar_values(row)
                radar_text = " · ".join(f"{key} {value}" for key, value in radar.items())
                col.markdown(
                    f"""
                    <div style="border:1px solid #d8e2ef;border-radius:8px;padding:12px 14px;margin-bottom:8px;background:#ffffff;">
                      <div style="font-size:18px;font-weight:700;color:#0f172a;">{GLOBAL_UNICORN_ICON} {escape(row["company_name"])}</div>
                      <div style="color:#64748b;font-size:13px;margin:3px 0 8px 0;">{escape(row["ticker"] or row["asset_id"])} · {escape(row["country"] or "N/D")} · {escape(row["exchange"] or "N/D")}</div>
                      <div style="font-size:26px;font-weight:800;color:#0f766e;margin:4px 0;">{probability}%</div>
                      <div style="color:#64748b;font-size:12px;margin-bottom:8px;">posibilidad de etiqueta unicornio</div>
                      <div style="display:inline-block;margin-bottom:8px;padding:4px 8px;border-radius:8px;background:#f8fafc;color:#334155;border-left:5px solid {escape(grade_color)};">{escape(grade_label)}</div>
                      <div style="margin-bottom:8px;">{badges}</div>
                      <div style="color:#334155;font-size:13px;">{escape(status_label)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with col.expander("Ver detalle"):
                    st.metric("Posibilidad de unicornio", f"{probability}%", help="Confianza de clasificación según señales locales ya calculadas. No mide rentabilidad esperada.")
                    st.write("**Criterios cumplidos**")
                    st.write(" · ".join(unicorn_criterion_badges(row.get("unicorn_reason", ""), row.get("country", ""))))
                    st.write("**Explicación**")
                    for item in explain_unicorn_reason(row.get("unicorn_reason", ""), row.get("country", "")):
                        st.write(f"- {item}")
                    st.write(f"**Calidad de evidencia:** {grade_label}. {grade_reason}")
                    st.write(f"**Radar:** {radar_text}")
                    note_value = st.text_area("Notas personales", value=notes.get(row["asset_id"], ""), key=f"unicorn_note_{row['asset_id']}", height=90)
                    current_status = unicorn_review_status(review_history, row["asset_id"])
                    status_choice = st.selectbox(
                        "Estado de revisión",
                        list(UNICORN_REVIEW_STATUS_LABELS),
                        index=list(UNICORN_REVIEW_STATUS_LABELS).index(current_status),
                        format_func=lambda value: UNICORN_REVIEW_STATUS_LABELS[value],
                        key=f"unicorn_review_status_{row['asset_id']}",
                    )
                    review_note = st.text_input("Comentario de revisión", value=unicorn_review_entry(review_history, row["asset_id"]).get("note", ""), key=f"unicorn_review_note_{row['asset_id']}")
                    if SAFE_DEMO_MODE:
                        st.caption(blocked_message("Guardar notas e historial"))
                    elif st.button("Guardar nota e historial", key=f"unicorn_note_save_{row['asset_id']}"):
                        notes[row["asset_id"]] = note_value.strip()
                        save_unicorn_notes(notes)
                        update_unicorn_review_history(review_history, row, status_choice, review_note)
                        save_unicorn_review_history(review_history)
                        st.success("Nota e historial guardados localmente.")
                    st.caption("No significa comprar, vender o mantener. No es precio objetivo ni probabilidad de rentabilidad.")
                    if st.checkbox("Generar informe profesional", key=f"unicorn_report_toggle_{row['asset_id']}"):
                        report = professional_unicorn_report(row)
                        st.markdown(report)
                        st.caption("Informe offline generado con datos locales. Preparado para IA opcional futura, pero sin llamadas externas ni API keys en esta fase.")
                        st.download_button(
                            "Descargar informe Markdown",
                            data=report.encode("utf-8"),
                            file_name=f"scout_finance_informe_unicornio_{row['asset_id']}_v2_44h.md",
                            mime="text/markdown",
                            key=f"unicorn_report_download_{row['asset_id']}",
                        )
                    if st.checkbox("Preparar prompt IA", key=f"unicorn_ai_prompt_toggle_{row['asset_id']}"):
                        ai_prompt = unicorn_ai_prompt_template(row)
                        st.caption("Prompt estructurado para analisis IA opcional; no ejecuta llamadas externas.")
                        st.code(ai_prompt, language="markdown")
                        st.download_button(
                            "Descargar prompt IA",
                            data=ai_prompt.encode("utf-8"),
                            file_name=f"scout_finance_prompt_ia_unicornio_{row['asset_id']}_v2_44m.md",
                            mime="text/markdown",
                            key=f"unicorn_ai_prompt_download_{row['asset_id']}",
                        )
                if watchlist_data is not None and col.button("Añadir a watchlist", key=f"unicorn_watchlist_{row['asset_id']}"):
                    try:
                        add(watchlist_data, unicorn_watchlist_asset(row), "WATCHLIST", "Unicornio v2.38BT revisado desde la pantalla Unicornios.")
                        atomic_write(watchlist_path, watchlist_data)
                        st.success(f'{row["ticker"] or row["asset_id"]} añadido a "{watchlist_data["name"]}".')
                    except ValueError as exc:
                        st.error(str(exc))

    table_rows = [{
        "ID": row["asset_id"],
        "Ticker": row["ticker"],
        "Empresa": row["company_name"],
        "Bolsa": row["exchange"],
        "País": row["country"],
        "Estado": GLOBAL_STATUS_LABELS.get(row["overall_coverage_status"], row["overall_coverage_status"]),
        "Elegibilidad": GLOBAL_ELIGIBILITY_LABELS.get(row.get("eligibility_tier", ""), row.get("eligibility_tier", "")),
        "Posibilidad unicornio": f"{unicorn_probability(row)}%",
        "Calidad evidencia": unicorn_evidence_grade(row)[0],
        "Estado revisión": UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, row["asset_id"])],
        "Última revisión": unicorn_review_entry(review_history, row["asset_id"]).get("reviewed_at", ""),
        "Nota personal": notes.get(row["asset_id"], ""),
        "Comentario revisión": unicorn_review_entry(review_history, row["asset_id"]).get("note", ""),
        "Motivo unicornio": row.get("unicorn_reason", ""),
        "Google Finance": google_finance_search_url(row["company_name"]),
    } for row in filtered]
    table = pd.DataFrame(table_rows)
    csv_bytes = table.to_csv(index=False).encode("utf-8")
    controls[1].download_button(
        "Exportar unicornios filtrados",
        data=csv_bytes,
        file_name="scout_finance_unicornios_filtrados_v2_44e.csv",
        mime="text/csv",
        disabled=table.empty,
    )
    report_pack = "\n\n---\n\n".join(professional_unicorn_report(row) for row in filtered[:25])
    controls[1].download_button(
        "Export pack investigación",
        data=report_pack.encode("utf-8"),
        file_name="scout_finance_pack_investigacion_unicornios_v2_44i.md",
        mime="text/markdown",
        disabled=not report_pack,
        help="Exporta hasta 25 informes profesionales combinados en Markdown.",
    )
    compare_options = [f'{row["company_name"]} · {row["ticker"] or row["asset_id"]}' for row in filtered]
    compare_selection = controls[2].multiselect("Comparar 2-3", compare_options, max_selections=3, key="global_unicorn_compare")
    if compare_selection:
        st.markdown("### Comparador de unicornios")
        compared = [filtered[compare_options.index(label)] for label in compare_selection]
        compare_rows = []
        for row in compared:
            compare_rows.append({
                "Empresa": row["company_name"],
                "Ticker": row["ticker"] or row["asset_id"],
                "País": row["country"],
                "Bolsa": row["exchange"],
                "Estado": GLOBAL_STATUS_LABELS.get(row["overall_coverage_status"], row["overall_coverage_status"]),
                "Elegibilidad": GLOBAL_ELIGIBILITY_LABELS.get(row.get("eligibility_tier", ""), row.get("eligibility_tier", "")),
                "Posibilidad unicornio": f"{unicorn_probability(row)}%",
                "Calidad evidencia": unicorn_evidence_grade(row)[0],
                "Estado revisión": UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, row["asset_id"])],
                "Criterios": " · ".join(unicorn_criterion_badges(row.get("unicorn_reason", ""), row.get("country", ""))),
            })
        st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)
        comparison_report = professional_unicorn_comparison(compared)
        with st.expander("Comparador profesional"):
            st.markdown(comparison_report)
            st.download_button(
                "Descargar comparador profesional",
                data=comparison_report.encode("utf-8"),
                file_name="scout_finance_comparador_profesional_unicornios_v2_44i.md",
                mime="text/markdown",
            )
    selected_index = None
    if filtered:
        options = [f'{row["company_name"]} · {row["ticker"] or row["asset_id"]}' for row in filtered]
        selected_asset_id = st.session_state.get("selected_unicorn_asset_id")
        if selected_asset_id not in {row["asset_id"] for row in filtered}:
            selected_asset_id = filtered[0]["asset_id"]
            st.session_state.selected_unicorn_asset_id = selected_asset_id
        fallback_index = selected_index if selected_index is not None else next((i for i, row in enumerate(filtered) if row["asset_id"] == selected_asset_id), 0)
        selected_label = st.selectbox("Detalle del unicornio", options, index=fallback_index, help="Selecciona una fila de la tabla o elige aquí una empresa para ver por qué está marcada como unicornio.")
        selected_row = filtered[options.index(selected_label)]
        st.session_state.selected_unicorn_asset_id = selected_row["asset_id"]
        st.markdown("### Por qué es unicornio")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Empresa", selected_row["company_name"])
        c2.metric("Ticker", selected_row["ticker"] or "N/D")
        c3.metric("País", selected_row["country"] or "N/D")
        c4.metric("Revisión", UNICORN_REVIEW_STATUS_LABELS[unicorn_review_status(review_history, selected_row["asset_id"])])
        c5.metric("Posibilidad unicornio", f"{unicorn_probability(selected_row)}%", help="Confianza de clasificación con los datos locales disponibles; no es probabilidad de rentabilidad.")
        st.caption("Esta posibilidad es una lectura de evidencia local del flag unicornio: no significa comprar, vender o mantener, no es precio objetivo y no constituye asesoramiento financiero.")
        grade_label, _, grade_reason = unicorn_evidence_grade(selected_row)
        st.info(f"Semáforo de calidad de evidencia: {grade_label}. {grade_reason}")
        st.markdown("**Criterios cumplidos**")
        st.write(" · ".join(unicorn_criterion_badges(selected_row.get("unicorn_reason", ""), selected_row.get("country", ""))))
        st.markdown("**Radar de evidencia**")
        radar = unicorn_radar_values(selected_row)
        st.bar_chart(pd.DataFrame({"Valor": radar}).T)
        st.markdown("**Explicación detallada**")
        for item in explain_unicorn_reason(selected_row.get("unicorn_reason", ""), selected_row.get("country", "")):
            st.write(f"- {item}")
        st.markdown("**Notas personales**")
        detail_note = st.text_area("Nota local de investigación", value=notes.get(selected_row["asset_id"], ""), key="global_unicorn_detail_note", height=110)
        st.markdown("**Historial de revisión**")
        current_status = unicorn_review_status(review_history, selected_row["asset_id"])
        detail_status = st.selectbox(
            "Estado de revisión",
            list(UNICORN_REVIEW_STATUS_LABELS),
            index=list(UNICORN_REVIEW_STATUS_LABELS).index(current_status),
            format_func=lambda value: UNICORN_REVIEW_STATUS_LABELS[value],
            key="global_unicorn_detail_review_status",
        )
        detail_review_note = st.text_input("Comentario de revisión", value=unicorn_review_entry(review_history, selected_row["asset_id"]).get("note", ""), key="global_unicorn_detail_review_note")
        if SAFE_DEMO_MODE:
            st.caption(blocked_message("Guardar notas e historial"))
        elif st.button("Guardar nota e historial de esta empresa", key="global_unicorn_detail_note_save"):
            notes[selected_row["asset_id"]] = detail_note.strip()
            save_unicorn_notes(notes)
            update_unicorn_review_history(review_history, selected_row, detail_status, detail_review_note)
            save_unicorn_review_history(review_history)
            st.success("Nota e historial guardados localmente.")
        with st.expander("Ver motivo técnico original"):
            st.code(selected_row.get("unicorn_reason", "Sin motivo técnico disponible"), language="text")
        with st.expander("Generar informe profesional completo"):
            report = professional_unicorn_report(selected_row)
            st.markdown(report)
            st.caption("Informe offline generado con datos locales. La integración con IA queda preparada como mejora opcional futura, siempre con guardrails de no asesoramiento.")
            st.download_button(
                "Descargar informe Markdown",
                data=report.encode("utf-8"),
                file_name=f"scout_finance_informe_unicornio_{selected_row['asset_id']}_v2_44h.md",
                mime="text/markdown",
                key="global_unicorn_detail_report_download",
            )
        with st.expander("IA opcional para análisis extendido"):
            st.info("Preparado para una integración futura con API de IA, pero desactivado en esta fase: no hay API key, no hay llamadas externas y no se envían datos fuera de Scout Finance.")
            ai_prompt = unicorn_ai_prompt_template(selected_row)
            st.code(ai_prompt, language="markdown")
            st.download_button(
                "Descargar prompt IA",
                data=ai_prompt.encode("utf-8"),
                file_name=f"scout_finance_prompt_ia_unicornio_{selected_row['asset_id']}_v2_44m.md",
                mime="text/markdown",
                key="global_unicorn_detail_ai_prompt_download",
            )
        st.markdown(f"[Abrir búsqueda manual en Google Finance]({google_finance_search_url(selected_row['company_name'])})")
        if watchlist_data is not None and st.button("Añadir este unicornio a watchlist", key="global_unicorn_detail_add_watchlist", type="primary"):
            try:
                add(watchlist_data, unicorn_watchlist_asset(selected_row), "WATCHLIST", "Unicornio v2.38BT revisado desde la ficha de detalle.")
                atomic_write(watchlist_path, watchlist_data)
                st.success(f'{selected_row["ticker"] or selected_row["asset_id"]} añadido a "{watchlist_data["name"]}".')
            except ValueError as exc:
                st.error(str(exc))

    if view_mode == "Tabla completa":
        try:
            event = st.dataframe(
                table, use_container_width=True, hide_index=True, height=620, on_select="rerun", selection_mode="single-row",
                column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver 🔗", help="Abre una búsqueda manual en Google. Scout Finance no descarga ni procesa datos de Google.")},
            )
            selected_rows = getattr(getattr(event, "selection", None), "rows", [])
            if selected_rows:
                st.session_state.selected_unicorn_asset_id = filtered[selected_rows[0]]["asset_id"]
        except TypeError:
            st.dataframe(
                table, use_container_width=True, hide_index=True, height=620,
                column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver 🔗", help="Abre una búsqueda manual en Google. Scout Finance no descarga ni procesa datos de Google.")},
            )


def render_global_ranking(_data):
    heading(st, "Ranking global (experimental)", "Prioridad cuantitativa de investigacion sobre el universo elegible (v2.38BO), calculada en v2.38BV y auditada en v2.38BX. Esta pantalla solo lee resultados ya generados: no recalcula scores, no cambia pesos y no crea recomendaciones.")
    render_safe_demo_banner(st, SAFE_DEMO_MODE)
    ranking = global_ranking_snapshot()
    if not ranking.available:
        st.error(ranking.error)
        st.caption("Estado seguro: pantalla bloqueada en lectura, sin red, sin credenciales, sin scoring nuevo y sin recomendaciones.")
        return
    if not ranking.rows:
        st.warning("El ranking global experimental esta disponible pero no contiene filas. Ejecuta la QA de v2.38BV antes de usar esta pantalla.")
        st.caption("Estado seguro: no se muestran scores vacios ni se fabrican poblaciones.")
        return
    st.markdown(f'<div class="sf-banner"><strong>Fase 9C — ranking experimental de investigacion.</strong><br>{DISCLAIMER}</div>', unsafe_allow_html=True)
    st.info("Uso previsto: ordenar trabajo de investigacion. No es asesoramiento financiero, no estima precios objetivo, no promete rentabilidad, no ejecuta operaciones y no se conecta a brokers.")
    st.caption(f"Última actualización: {ranking.generated_at} (UTC) · {len(ranking.rows):,} empresas evaluadas · sin conexión de red")
    counts = Counter(row["eligibility_status"] for row in ranking.rows)
    metric_cols = st.columns(5)
    metric_cols[0].metric("Ranking principal", f"{counts.get('ELIGIBLE_PARTIAL', 0):,}", help="Confianza HIGH o MEDIUM — cobertura contractual real de al menos el 65% de los factores.")
    metric_cols[1].metric("Comparabilidad parcial", f"{counts.get('PARTIAL_COMPARABILITY', 0):,}", help="Confianza LOW (50–65% de cobertura real) — puntuado, pero fuera del ranking principal.")
    metric_cols[2].metric("Revisión requerida", f"{counts.get('REVIEW_REQUIRED', 0):,}", help="Margen real fuera de ±300%, o entidad financiera que necesita un contrato de factores distinto — nunca puntuado.")
    metric_cols[3].metric("Cobertura insuficiente", f"{counts.get('BLOCKED', 0):,}", help="Menos del 50% real de los factores disponibles — nunca se imputa ni se estima.")
    metric_cols[4].metric("Sin adaptador todavía", f"{counts.get('NOT_YET_SCORED_NO_ADAPTER', 0):,}", help="Luxemburgo y Reino Unido — sin un adaptador real de ratios/crecimiento construido todavía (v2.38BV).")

    st.markdown("### Ranking principal")
    countries = sorted({row.get("country", "") for row in ranking.rows if row.get("country")})
    main_ranking = [row for row in ranking.rows if row["eligibility_status"] == "ELIGIBLE_PARTIAL" and row.get("rank")]
    scores = [float(row["total_score"]) for row in main_ranking if row.get("total_score") is not None]
    coverages = [float(row["coverage_weight"]) for row in main_ranking if row.get("coverage_weight") is not None]
    if not main_ranking or not scores or not coverages:
        st.warning(global_ranking_empty_message("ELIGIBLE_PARTIAL"))
        st.caption("Se mantienen visibles las poblaciones no principales abajo; no se recalcula ranking ni se rellenan scores.")
        score_range = (0.0, 100.0)
        coverage_range = (0.0, 100.0)
        search = ""
        country_filter = []
        confidence_filter = []
        top_n_label = "Todos"
    else:
        c1, c2, c3 = st.columns([2, 1, 1])
        search = c1.text_input("Buscar", placeholder="Empresa, ticker, ID o país", key="global_ranking_search")
        country_filter = c2.multiselect("País", countries, placeholder="Todos", key="global_ranking_country")
        confidence_filter = c3.multiselect("Confianza", ["HIGH", "MEDIUM"], format_func=lambda value: CONFIDENCE_LABELS.get(value, value), placeholder="Todas", key="global_ranking_confidence")
        f1, f2, f3 = st.columns([1, 1, 1])
        score_range = f1.slider("Rango de score", min_value=float(int(min(scores))), max_value=float(int(max(scores)) + 1), value=(float(int(min(scores))), float(int(max(scores)) + 1)), step=1.0, key="global_ranking_score_range")
        coverage_range = f2.slider("Rango de cobertura", min_value=float(int(min(coverages) * 100)), max_value=100.0, value=(float(int(min(coverages) * 100)), 100.0), step=1.0, key="global_ranking_coverage_range")
        top_n_label = f3.selectbox("Top N", ["Todos", "10", "25", "50", "100"], index=0, key="global_ranking_top_n")
    filtered_main = filter_global_ranking_rows(
        main_ranking,
        status="ELIGIBLE_PARTIAL",
        search=search,
        countries=country_filter,
        confidences=confidence_filter,
        min_score=score_range[0],
        max_score=score_range[1],
        min_coverage=coverage_range[0] / 100,
        max_coverage=coverage_range[1] / 100,
        top_n=None if top_n_label == "Todos" else int(top_n_label),
    )
    st.caption(f"{len(filtered_main):,} de {len(main_ranking):,} empresas en el ranking principal")
    main_table = global_ranking_display_frame(filtered_main)
    if filtered_main:
        st.dataframe(
            main_table,
            use_container_width=True,
            hide_index=True,
            column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")},
        )
    else:
        st.info(global_ranking_empty_message("ELIGIBLE_PARTIAL"))
    export_frame = global_ranking_export_frame(filtered_main)
    st.caption("El CSV exporta solo la vista filtrada y columnas seguras de investigacion: no incluye watchlists privadas, secretos ni datos de broker.")
    st.download_button(
        "Descargar CSV filtrado",
        export_frame.to_csv(index=False).encode("utf-8"),
        GLOBAL_RANKING_EXPORT_FILENAME,
        "text/csv",
        help="Exporta solo columnas de investigacion del ranking ya calculado. No incluye watchlists privadas ni recalcula ningun score.",
    )

    if filtered_main:
        st.markdown("### Ficha rápida")
        options = {f'#{row["rank"]} · {row["ticker"]} · {row["company_name"]}': row for row in filtered_main}
        selected_label = st.selectbox("Selecciona una empresa del ranking principal", options)
        selected = options[selected_label]
        detail_cols = st.columns(4)
        detail_cols[0].metric("Score", f'{selected["total_score"]:.2f}')
        detail_cols[1].metric("Confianza", CONFIDENCE_LABELS.get(selected["confidence"], selected["confidence"]))
        detail_cols[2].metric("Cobertura real", f'{selected["coverage_weight"] * 100:.0f}%')
        detail_cols[3].metric("Posición", f'#{selected["rank"]}')
        st.caption("Ficha de lectura: muestra el desglose ya calculado por v2.38BV. No recalcula ni interpreta la empresa como compra, venta o mantener.")
        pillar_rows = [{"Pilar": PILLAR_LABELS.get(pillar, pillar), "Puntuación": round(score, 1)} for pillar, score in sorted(selected.get("pillar_scores", {}).items())]
        if pillar_rows:
            st.dataframe(pd.DataFrame(pillar_rows), use_container_width=True, hide_index=True)
        explanation = selected.get("explanation") or {}
        if explanation:
            st.caption(explanation.get("summary", ""))
        st.link_button("Ver en Google Finance", google_finance_search_url(selected["company_name"]))
        if SAFE_DEMO_MODE:
            st.info(blocked_message("Añadir a watchlist"))
        else:
            wpath, wdata = select_watchlist()
            if wdata is None:
                st.info("Crea una watchlist en la pantalla ⭐ Watchlist antes de añadir empresas desde aquí.")
            elif st.button(f'Añadir {selected["ticker"]} a "{wdata["name"]}"', key="global_ranking_add_watchlist", type="primary"):
                try:
                    add(wdata, {"asset_id": selected["asset_id"], "ticker": selected["ticker"], "company_name": selected["company_name"], "market": selected.get("country", "")}, "WATCHLIST", "")
                    atomic_write(wpath, wdata)
                    st.success("Añadida a la watchlist.")
                except ValueError as exc:
                    st.error(str(exc))

    status_tabs = st.tabs(["Comparabilidad parcial", "Revisión requerida", "Cobertura insuficiente", "Sin adaptador"])
    partial_rows = filter_global_ranking_rows(ranking.rows, status="PARTIAL_COMPARABILITY")
    with status_tabs[0]:
        st.caption("Confianza LOW (50–65% de cobertura real) — puntuadas, pero fuera del ranking principal por baja comparabilidad, nunca excluidas silenciosamente.")
        if partial_rows:
            st.dataframe(
                global_ranking_display_frame(partial_rows, include_rank=False),
                use_container_width=True,
                hide_index=True,
                column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")},
            )
        else:
            st.info(global_ranking_empty_message("PARTIAL_COMPARABILITY"))

    review_rows = filter_global_ranking_rows(ranking.rows, status="REVIEW_REQUIRED")
    with status_tabs[1]:
        st.caption("Nunca puntuadas con el contrato industrial — margen real fuera de ±300%, o entidad financiera que necesita un modelo de factores distinto.")
        if review_rows:
            st.dataframe(
                global_ranking_display_frame(review_rows, include_rank=False, include_reason=True),
                use_container_width=True,
                hide_index=True,
                column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")},
            )
        else:
            st.info(global_ranking_empty_message("REVIEW_REQUIRED"))

    blocked_rows = filter_global_ranking_rows(ranking.rows, status="BLOCKED")
    with status_tabs[2]:
        st.caption("Menos del 50% de cobertura real de factores. No se estima, no se imputa y no entra en ranking principal.")
        if blocked_rows:
            st.dataframe(
                global_ranking_display_frame(blocked_rows, include_rank=False),
                use_container_width=True,
                hide_index=True,
                column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")},
            )
        else:
            st.info(global_ranking_empty_message("BLOCKED"))

    pending_rows = filter_global_ranking_rows(ranking.rows, status="NOT_YET_SCORED_NO_ADAPTER")
    with status_tabs[3]:
        st.caption("Luxemburgo y Reino Unido — elegibles segun fases previas, pero sin adaptador real de ratios/crecimiento para esta fase. Nunca se les asigna un score inventado.")
        if pending_rows:
            st.dataframe(
                global_ranking_display_frame(pending_rows, include_rank=False, include_reason=True),
                use_container_width=True,
                hide_index=True,
                column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")},
            )
        else:
            st.info(global_ranking_empty_message("NOT_YET_SCORED_NO_ADAPTER"))

    with st.expander(f"Comparabilidad parcial ({counts.get('PARTIAL_COMPARABILITY', 0):,})"):
        st.caption("Vista heredada mantenida por compatibilidad con v2.38BW.")
        st.dataframe(global_ranking_display_frame(partial_rows, include_rank=False), use_container_width=True, hide_index=True, column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")})

    with st.expander(f"Revisión requerida ({counts.get('REVIEW_REQUIRED', 0):,})"):
        st.caption("Vista heredada mantenida por compatibilidad con v2.38BW.")
        st.dataframe(global_ranking_display_frame(review_rows, include_rank=False, include_reason=True), use_container_width=True, hide_index=True, column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")})

    with st.expander(f"Cobertura insuficiente ({counts.get('BLOCKED', 0):,})"):
        st.caption("Bloqueadas por cobertura real inferior al minimo contractual. Quedan visibles para revisar huecos, pero sin score utilizable.")
        st.dataframe(global_ranking_display_frame(blocked_rows, include_rank=False), use_container_width=True, hide_index=True, column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")})

    with st.expander(f"Sin adaptador todavía ({counts.get('NOT_YET_SCORED_NO_ADAPTER', 0):,})"):
        st.caption("Vista heredada mantenida por compatibilidad con v2.38BW.")
        st.dataframe(global_ranking_display_frame(pending_rows, include_rank=False, include_reason=True), use_container_width=True, hide_index=True, column_config={"Google Finance": st.column_config.LinkColumn("Google Finance", display_text="Ver")})


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
    render_safe_demo_banner(st, SAFE_DEMO_MODE)
    if SAFE_DEMO_MODE:
        st.info("Watchlists bloqueadas en Modo demo seguro para evitar escrituras o datos privados.")
        return
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


def render_final_guide(data):
    heading(st, "Guía final y uso responsable", "Lectura práctica de Scout Finance como herramienta local de investigación, con límites visibles antes de cualquier uso externo.")
    render_safe_demo_banner(st, SAFE_DEMO_MODE)
    st.markdown("### Qué es Scout Finance")
    st.write("Scout Finance es una herramienta local de investigación financiera que reúne datos ya generados, cobertura, ranking experimental, watchlists e informes trazables. Usa datos locales/offline y no descarga información nueva desde esta pantalla.")
    st.markdown("### Qué puedes hacer")
    st.write("Explorar el universo global, revisar el ranking experimental, filtrar poblaciones, exportar CSV de la vista filtrada, consultar fichas, mantener watchlists locales y abrir documentación de apoyo.")
    st.markdown("### Qué no hace")
    st.warning("No constituye asesoramiento financiero. No recomienda comprar, vender ni mantener. No predice rentabilidad. No ejecuta órdenes. No se conecta a broker. No habilita trading automático.")
    st.markdown("### Cómo leer el ranking experimental")
    st.write("El ranking experimental sirve para priorizar investigación, no para decidir operaciones. El score resume factores reales disponibles de calidad, crecimiento, valoración, momentum y riesgo, con cobertura y confianza visibles.")
    st.markdown("### Estados del ranking")
    st.write("Ranking principal: población con cobertura suficiente. Comparabilidad parcial: puntuable pero con menor confianza. Revisión requerida: casos que necesitan revisión manual o contrato específico. Cobertura insuficiente: no se estima ni se imputa. Sin adaptador: países o fuentes todavía sin adaptador real.")
    st.markdown("### Cobertura y confianza")
    st.write("La cobertura mide cuántos factores reales respaldan la lectura. La confianza alta no significa alta probabilidad de rentabilidad; solo indica mejor completitud/comparabilidad de los datos disponibles.")
    st.markdown("### Limitaciones conocidas")
    st.write("Las limitaciones finales están documentadas en v2.41D: Luxemburgo, Reino Unido, Cboe Europe, precios europeos, manual reviews, entidades financieras, margen extremo, cobertura bajo umbral, riesgo de publicación externa, seguridad y wording legal/producto.")
    st.markdown("### Modo demo seguro")
    st.write("El modo demo seguro se activa con SCOUT_FINANCE_SAFE_DEMO_MODE=1. Mantiene datos estáticos/offline, bloquea acciones de escritura peligrosas y conserva visible que el ranking es experimental, sin asesoramiento financiero y sin broker.")
    st.markdown("### Antes de usar fuera del entorno local")
    st.write("Revisa manualmente la fuente, cobertura, confianza, motivos de revisión, limitaciones documentadas, fecha de corte y cualquier evento posterior no reflejado en los datos locales. Cualquier decisión externa debe hacerse fuera de Scout Finance y bajo responsabilidad humana.")
    st.markdown("### Documentación útil")
    docs = [
        ("FINAL_COVERAGE_LIMITATIONS_v2_41d.md", "Limitaciones finales de cobertura"),
        ("FINAL_UX_HARDENING_v2_42a.md", "Hardening UX final del ranking"),
        ("LOCAL_USAGE_PUBLIC_GUIDE_v2_39b.md", "Guía pública de uso local"),
        ("USER_GUIDE.md", "Guía de usuario"),
        ("QUICKSTART.md", "Arranque rápido"),
    ]
    st.dataframe(pd.DataFrame([{"Documento": name, "Uso": purpose} for name, purpose in docs]), use_container_width=True, hide_index=True)
    st.caption(f"Fecha de corte local: {data.as_of_date or 'no disponible'} · Datos locales/offline · Ranking experimental · Sin recomendaciones · Sin broker")


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
        if SAFE_DEMO_MODE:
            st.success(SAFE_DEMO_LABEL)
        selected = st.radio("Navegación", list(SCREENS), format_func=SCREENS.get, index=list(SCREENS).index(st.session_state.screen))
        st.session_state.screen = selected
        st.divider(); st.caption(f"Datos: {data.mode.value}"); st.caption("Fase 7: INSUFFICIENT_EVIDENCE"); st.caption("Sin conexión a broker")
    if data.mode in {DataMode.BLOCKED_MISSING_DATA, DataMode.INCOMPATIBLE_VERSION}:
        render_home(data); st.error("La aplicación queda bloqueada: " + "; ".join(data.errors)); return
    {"home": render_home, "global_unicorns": render_global_unicorns, "global_universe": render_global_universe, "global_ranking": render_global_ranking, "universe": render_universe, "ranking": render_ranking, "asset": render_asset, "compare": render_compare, "watchlist": render_watchlist, "reports": render_reports, "final_guide": render_final_guide, "help": render_help}[selected](data)


if __name__ == "__main__":
    main()
