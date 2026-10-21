"""The crypto page (v2.50F/G): title, attribution, one big search button, the results after the search, and a coin's own page.

Drawing only: the search itself is `src.crypto_v2_50.search.run_search`. The app passes its tokens and helpers in `CryptoHooks`
(importing the app from here would run it twice). Results live in the session, in memory: nothing from CoinGecko is written to
disk here (the encrypted 24 h cache of the data layer is the only copy).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import pandas as pd
import streamlit as st

from src.crypto_v2_50 import REVOLUT_FILENAME, default_paths
from src.crypto_v2_50.cache import ProtectedCache
from src.crypto_v2_50.charts import chart_key_text, daily_series_figure, reference_high
from src.crypto_v2_50.derivatives import DerivativesError, fetch_perp_detail, squeeze_hint
from src.crypto_v2_50.contract_security import MAX_CHAINS, check_contract
from src.crypto_v2_50.coingecko import (ATTRIBUTION_TEXT, ATTRIBUTION_URL, KEY_ENV, BudgetExhausted, CoinGeckoClient, CoinGeckoError, MissingApiKey, RateLimited,
                                        load_daily_series, read_api_key)
from src.crypto_v2_50.quality import has_protocol_data, valuation_ratios
from src.crypto_v2_50.scoring import MAX_SCORE, TIER_HIGH, TIER_LOW, TIER_MEDIUM, TIER_NO_LIQUIDITY, TIER_WATCH, summarize, tier_label
from src.crypto_v2_50.search import CANDIDATE_TIERS, filter_results, overlay_checks, paginate, run_search
from src.crypto_v2_50.usage import UsageCounter
from src.crypto_v2_50.venues import venue_label, venue_matches

# Tests set this to inject a fast, offline client (e.g. {"sleep": lambda s: None, "min_interval": 0}); the app never touches it.
CLIENT_OPTIONS: dict[str, Any] = {}

LEVELS = {"Puntuadas": "scored", "Solo candidatas": "candidates", "En vigilancia": "watch", "Sin liquidez suficiente": "no_liquidity"}
PER_PAGE_OPTIONS = [9, 18, 27]
PROTOCOL_FILTERS = ["Todas", "Con datos de protocolo"]
VENUE_FILTERS = {"Revolut o Kraken": "any", "Kraken": "kraken", "Revolut": "revolut", "En las dos": "both", "Todas": "all"}
FILTER_DEFAULTS = {"crypto_filter_text": "", "crypto_filter_level": "Puntuadas", "crypto_filter_venue": "Revolut o Kraken", "crypto_filter_protocol": "Todas",
                   "crypto_per_page": PER_PAGE_OPTIONS[0]}
RISK_NOTE = ("Las criptomonedas pueden perder casi todo su valor, y las monedas pequeñas son especialmente volátiles y fáciles de manipular. "
             "Esta pantalla es investigación local: no es una recomendación de compra ni una predicción.")
PAGE_DESCRIPTION = ("Monedas pequeñas con señales de mercado fuertes: mucha rotación de volumen, volumen por encima de su media, subida a 7 y 30 días "
                    "o ruptura de máximos. La búsqueda consulta CoinGecko, excluye stablecoins y versiones envueltas, y marca los riesgos de volumen "
                    "sospechoso y dilución.")
RISK_EXPLANATIONS = {
    "rotación sospechosa": "El volumen de un día iguala o supera la capitalización: puede ser volumen artificial o una falsa sensación de liquidez. "
                           "Limita la puntuación a 44 y no suma puntos de rotación.",
    "moneda reciente": "CoinGecko tiene menos de 90 días de historial de esta moneda: hay poco recorrido para juzgar su comportamiento. "
                       "Con menos de 30 días la puntuación se limita a 44 (y sin 31 días de volumen no hay volumen relativo).",
    "contrato con señales graves": "La comprobación de contrato (GoPlus) encontró una o más señales graves: véase la pestaña Seguridad. Limita la puntuación a 44.",
    "dilución alta": "Gran parte del suministro todavía no circula (circulante / total < 0,3) o la valoración totalmente diluida es al menos 3 veces la "
                     "capitalización: pueden llegar desbloqueos que presionen el precio. Limita la puntuación a 69, es decir, como mucho nivel bajo.",
}
MANUAL_CHECKS = (
    "Confirmar el precio y el volumen en un exchange o en una segunda fuente: el volumen agregado puede incluir mercados con poca liquidez real.",
    "Revisar el contrato y la distribución de tenedores (concentración, liquidez bloqueada): la pestaña Seguridad lo comprueba bajo demanda, pero solo con lo que GoPlus evalúa y no siempre hay datos.",
    "Mirar el calendario de desbloqueos del suministro y la antigüedad de la moneda.",
    "Comprobar que no es una versión envuelta o derivada, ni un token duplicado con nombre parecido.",
    "Verificar si hay un catalizador real (listado, producto, noticia) o solo momentum técnico.",
)


@dataclass
class CryptoHooks:
    data_dir: Path
    safe_demo: bool
    blocked_message: Callable[[str], str]
    heading: Callable[..., Any]
    render_banner: Callable[[], Any]
    tier_style: Callable[[str], dict]  # {"border", "chip_bg", "chip_fg"} for a crypto tier
    css_big: str
    css_compact: str
    css_cards: str
    tokens: dict[str, Any] = field(default_factory=dict)  # ink, text, secondary, border, link, radius, radius_small, accent_text, accent_border, surface


def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and abs(value) != float("inf") else None


def fmt_usd(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "N/D"
    if number >= 1e9:
        text = f"{number / 1e9:.2f} mil M$"
    elif number >= 1e6:
        text = f"{number / 1e6:.1f} M$"
    elif number >= 1e3:
        text = f"{number / 1e3:.0f} k$"
    else:
        text = f"{number:.0f} $"
    return text.replace(".", ",")


def fmt_pct(value: Any) -> str:
    number = _num(value)
    return "N/D" if number is None else f"{number:+.1f} %".replace(".", ",")


def fmt_ratio(value: Any) -> str:
    number = _num(value)
    return "N/D" if number is None else f"{number:.2f}".replace(".", ",")


def fmt_price(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "N/D"
    text = f"{number:,.2f}" if number >= 1 else (f"{number:.8f}".rstrip("0").rstrip(".") if number >= 1e-8 else "< 0.00000001")
    return text.replace(",", "_").replace(".", ",").replace("_", ".") + " $"


def fmt_supply(value: Any) -> str:
    number = _num(value)
    return "no declarado" if number is None else f"{number:,.0f}".replace(",", ".")


def fmt_funding(value: Any) -> str:
    number = _num(value)
    return "N/D" if number is None else f"{number * 100:+.4f} %".replace(".", ",")


def fmt_history(item: dict) -> str:
    days = item.get("history_days")
    if not days:
        return "N/D (sin serie diaria)"
    return "un año o más" if item.get("history_capped") else f"{int(days):,} días".replace(",", ".")


def coin_url(coin_id: Any) -> str:
    return f"https://www.coingecko.com/en/coins/{quote(str(coin_id), safe='')}"


def card_key(coin_id: Any) -> str:
    """A widget key that is unique per coin: the readable part is only cosmetic, the short hash is what keeps two ids apart."""
    readable = "".join(ch if ch.isalnum() else "_" for ch in str(coin_id))[:40]
    return f"{readable}_{hashlib.sha1(str(coin_id).encode('utf-8')).hexdigest()[:8]}"


def _chip(hooks: CryptoHooks, tier: str) -> str:
    style = hooks.tier_style(tier)
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;background:{style["chip_bg"]};color:{style["chip_fg"]};'
            f'font-size:12px;font-weight:700;white-space:nowrap;">{escape(tier_label(tier))}</span>')


def _risk_chip(hooks: CryptoHooks, text: str) -> str:
    t = hooks.tokens
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;border:1px solid {t["accent_border"]};background:{t["surface"]};'
            f'color:{t["accent_text"]};font-size:12px;font-weight:700;white-space:nowrap;">{escape(text)}</span>')


def _info_chip(hooks: CryptoHooks, text: str) -> str:
    t = hooks.tokens
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;border:1px solid {t["border"]};background:#ffffff;'
            f'color:{t["secondary"]};font-size:12px;font-weight:700;white-space:nowrap;">{escape(text)}</span>')


def attribution_html(hooks: CryptoHooks) -> str:
    """The API terms ask for "Powered by CoinGecko", displayed prominently and not smaller than size 10."""
    return (f'<div style="font-size:14px;margin:4px 0 10px;"><a href="{escape(ATTRIBUTION_URL, quote=True)}" target="_blank" rel="noopener noreferrer" '
            f'style="color:{hooks.tokens["link"]};font-weight:700;text-decoration:underline;">{escape(ATTRIBUTION_TEXT)} ↗</a></div>')


def _build_client(hooks: CryptoHooks) -> tuple[CoinGeckoClient | None, ProtectedCache, UsageCounter]:
    cache_dir, usage_file = default_paths(hooks.data_dir)
    usage = UsageCounter(usage_file)
    cache = ProtectedCache(cache_dir)
    cache.purge_expired()  # third-party data does not outlive 24 hours on disk
    if read_api_key() is None:
        return None, cache, usage
    return CoinGeckoClient(usage=usage, **CLIENT_OPTIONS), cache, usage


def render_usage_line(usage: UsageCounter) -> None:
    status = usage.status()
    text = f"Llamadas a CoinGecko este mes ({status['month']}): {status['calls']:,} de {status['cap']:,} (tope de seguridad; el plan gratuito permite 10.000)."
    if status["assumed"]:
        text += " El contador estaba dañado: se parte de una cifra prudente."
    (st.warning if status["warn"] else st.caption)(text)


def render_missing_key() -> None:
    st.info(
        f"Falta la clave gratuita de CoinGecko. Crea una cuenta con el plan Demo en coingecko.com/en/api, genera la clave y guárdala en la variable de entorno "
        f"de usuario `{KEY_ENV}`. Después cierra y vuelve a abrir esta aplicación. La clave no se escribe nunca en pantalla ni en ningún archivo del proyecto."
    )


def render_summary(hooks: CryptoHooks, summary: dict) -> None:
    t = hooks.tokens
    tiers = summary["tiers"]
    box = f"background:#fff;border:1px solid {t['border']};border-radius:{t['radius_small']}px;padding:10px;text-align:center;"
    number = f"font-size:20px;font-weight:700;color:{t['ink']};"
    label = f"font-size:12px;color:{t['secondary']};"
    none_pass = " Ninguna supera el umbral explosivo." if not summary["candidates"] else ""
    excluded = ", ".join(f"{name} {count:,}" for name, count in sorted(summary["excluded_by"].items())) or "ninguna"
    when = summary["fetched_at"][:16].replace("T", " ")
    boxes = "".join(
        f'<div style="{box}"><b style="{number}">{tiers.get(tier, 0):,}</b><br><span style="{label}">{name}</span></div>'
        for name, tier in (("Alto", TIER_HIGH), ("Medio", TIER_MEDIUM), ("Bajo", TIER_LOW), ("Vigilancia", TIER_WATCH), ("Sin liquidez", TIER_NO_LIQUIDITY))
    )
    st.markdown(
        f"""
        <div style="border:1px solid #f2e2bb;border-left:6px solid {t['accent_border']};border-radius:{t['radius']}px;padding:16px 20px;margin:12px 0 16px;background:{t['surface']};">
          <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;flex-wrap:wrap;">
            <div style="flex:2;min-width:260px;">
              <div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:{t['accent_text']};font-weight:700;">Unicornios cripto</div>
              <div style="font-size:28px;font-weight:800;color:{t['ink']};margin-top:2px;">{summary['candidates']:,} candidatas explosivas</div>
              <div style="font-size:13px;color:{t['secondary']};margin-top:4px;">{summary['universe']:,} monedas leídas · {summary['excluded']:,} excluidas ({escape(excluded)}) ·
              {summary['gated']:,} con liquidez suficiente · {summary['detail_loaded']:,} con serie diaria.{none_pass}<br>
              Datos de CoinGecko de las {escape(when)} UTC{' (de la caché local de 24 h)' if summary['from_cache'] else ''}.</div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(74px,1fr));gap:10px;flex:3;min-width:260px;">{boxes}</div>
          </div>
          <div style="font-size:12px;color:{t['secondary']};margin-top:10px;">Puntuación explosiva cripto v1: heurística local de investigación de 0 a 100 (el máximo alcanzable es {MAX_SCORE}); no es una recomendación financiera ni predice rentabilidad.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Esta búsqueda usó {summary['calls_used']:,} llamadas a CoinGecko.")
    if summary.get("quality_status") == "unavailable":
        st.caption("No se pudieron consultar los datos de protocolo de DefiLlama: las tarjetas no muestran TVL ni comisiones en esta búsqueda.")
    elif "with_quality" in summary:
        st.caption(f"Calidad (DefiLlama, datos públicos): {summary['with_quality']:,} monedas tienen datos de protocolo (TVL o comisiones). Para las demás no hay datos, y eso no es una señal negativa: no son protocolos DeFi.")
    render_venue_notes(summary)
    if summary.get("perps_status") == "unavailable":
        st.caption("No se pudo consultar la lista de perpetuas de Binance: las tarjetas no muestran derivados en esta búsqueda.")
    elif summary.get("perps_status") == "unverified":
        st.caption("No se pudieron obtener precios frescos de CoinGecko para verificar la identidad de las perpetuas: las tarjetas no muestran derivados en esta búsqueda.")
    elif "with_perp" in summary:
        conflicts = f" Se descartaron {summary['perp_conflicts']:,} coincidencias de símbolo cuyo precio fresco no encajaba (otra moneda con el mismo símbolo)." if summary.get("perp_conflicts") else ""
        st.caption(f"Derivados (Binance, datos públicos): {summary['with_perp']:,} monedas tienen perpetuo con identidad verificada por precio fresco.{conflicts}")
    if summary["stopped"] == "budget":
        st.warning(f"Se agotó el presupuesto de llamadas del mes durante la búsqueda: {summary['detail_skipped']:,} monedas se puntuaron sin su serie diaria (con ese dato ausente su puntuación no pasa de 44).")
    elif summary["stopped"] == "rate_limited":
        st.warning(f"CoinGecko limitó el ritmo durante la búsqueda: {summary['detail_skipped']:,} monedas se puntuaron sin su serie diaria (con ese dato ausente su puntuación no pasa de 44). Espera un minuto y repite: lo ya cargado no vuelve a gastar llamadas.")
    if summary.get("contract_flagged"):
        st.caption(f"{summary['contract_flagged']:,} monedas tienen señales graves de contrato en las comprobaciones de esta sesión: su puntuación se limitó a 44.")
    if summary["detail_failed"]:
        st.warning(f"No se pudo cargar la serie diaria de {summary['detail_failed']:,} monedas: se puntuaron sin ella (máximo 44).")


def render_venue_notes(summary: dict) -> None:
    """Where the person can trade, one line per source, with what is missing said plainly (a missing source never reads as 'not available')."""
    if "kraken_status" not in summary:
        return
    if summary["kraken_status"] == "unavailable":
        st.caption("No se pudo consultar el catálogo de Kraken: esta búsqueda no sabe qué monedas se pueden operar allí.")
    elif summary["kraken_status"] == "unverified":
        st.caption("No se pudieron obtener precios frescos de CoinGecko para verificar las monedas de Kraken: esta búsqueda no marca ninguna como operable allí.")
    else:
        conflicts = f" Se descartaron {summary['kraken_conflicts']:,} coincidencias de símbolo cuyo precio fresco no encajaba (otra moneda con el mismo símbolo)." if summary.get("kraken_conflicts") else ""
        st.caption(f"Kraken (catálogo público): {summary['with_kraken']:,} monedas tienen mercado en USD o EUR con identidad verificada por precio fresco.{conflicts}")
    status = summary.get("revolut_status")
    if status == "missing":
        st.caption(f"No hay lista de Revolut: crea el archivo `data/{REVOLUT_FILENAME}` con un símbolo por línea (por ejemplo `AAVE;Aave`) y repite la búsqueda. Mientras tanto «Revolut» no marca ninguna moneda.")
    elif status in ("empty", "unreadable"):
        st.caption(f"La lista de Revolut (`data/{REVOLUT_FILENAME}`) está {'vacía' if status == 'empty' else 'ilegible'}: «Revolut» no marca ninguna moneda.")
    elif status == "ok":
        unverified = f" {summary['revolut_unverified']:,} comparten símbolo con otra moneda o tienen otro nombre: no verificadas, no cuentan." if summary.get("revolut_unverified") else ""
        skipped = f" Se ignoraron {summary['revolut_skipped']:,} líneas que no se entendieron." if summary.get("revolut_skipped") else ""
        st.caption(f"Revolut (tu lista de {summary['revolut_listed']:,} símbolos): {summary['with_revolut']:,} monedas confirmadas por símbolo y nombre.{unverified}{skipped} "
                   f"En las dos plataformas: {summary['with_both']:,}.")
    if "candidates_operable" in summary:
        st.caption(f"De las {summary['candidates']:,} candidatas explosivas, {summary['candidates_operable']:,} se pueden operar en Revolut o Kraken.")


def _card(hooks: CryptoHooks, item: dict) -> None:
    t = hooks.tokens
    style = hooks.tier_style(item["tier"])
    suffix = card_key(item["coin_id"])
    key = f"crypto_card_{suffix}"
    rank = f" · puesto {item['market_cap_rank']:,}" if item.get("market_cap_rank") else ""
    chips = "".join(_risk_chip(hooks, flag.capitalize()) for flag in item.get("risk_flags", []))
    where = venue_label(item.get("venues"))
    if where:
        chips += _info_chip(hooks, f"Operable en {where}")
    perp = item.get("perp")
    if perp:
        chips += _info_chip(hooks, f"Con perpetuo · financiación {fmt_funding(perp.get('funding_rate'))}")
        if squeeze_hint(perp.get("funding_rate"), item.get("change_7d_pct")):
            chips += _info_chip(hooks, "Financiación negativa con subida")
    quality = item.get("quality")
    if has_protocol_data(quality):
        if _num(quality.get("tvl")) and quality["tvl"] > 0:
            chips += _info_chip(hooks, f"Protocolo · TVL {fmt_usd(quality['tvl'])}")
        if _num(quality.get("fees_30d")) and quality["fees_30d"] > 0:
            chips += _info_chip(hooks, f"Comisiones 30 d {fmt_usd(quality['fees_30d'])}")
    drivers = " · ".join(item["drivers"]) if item["drivers"] else "ninguna todavía"
    missing = item.get("missing_signals") or []
    figures = (f"Capitalización {fmt_usd(item.get('market_cap_usd'))} · volumen 24 h {fmt_usd(item.get('volume_24h_usd'))} · rotación {fmt_ratio(item.get('turnover_24h'))}<br>"
               f"7 d {fmt_pct(item.get('change_7d_pct'))} · 30 d {fmt_pct(item.get('change_30d_pct'))}")
    with st.container(border=True, key=key, height="stretch"):
        st.markdown(
            f"""
            <style>.st-key-{key} {{ border-left: 6px solid {style['border']}; }}</style>
            <div style="font-weight:700;color:{t['ink']};font-size:15px;line-height:1.3;">{escape(str(item.get('name') or item['symbol']))}</div>
            <div style="color:{t['secondary']};font-size:12px;">{escape(str(item['symbol']))}{escape(rank)}</div>
            <div style="font-size:12px;margin-top:6px;"><a href="{escape(coin_url(item['coin_id']), quote=True)}" target="_blank" rel="noopener noreferrer" style="color:{t['link']};font-weight:600;text-decoration:underline;white-space:nowrap;">CoinGecko ↗</a></div>
            <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-top:10px;"><span style="font-size:32px;font-weight:800;color:{t['ink']};">{int(item['score'])}<span style="font-size:14px;font-weight:600;color:{t['secondary']};">/100</span></span>{_chip(hooks, item['tier'])}</div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:6px;">{chips}</div>
            <div style="font-size:13px;color:{t['text']};margin-top:8px;">{figures}</div>
            <div style="font-size:13px;color:{t['text']};margin-top:8px;"><b>Señales detectadas:</b> {escape(drivers)}</div>
            <div style="font-size:13px;color:{t['secondary']};">{('<b>Faltan:</b> ' + escape(' · '.join(missing))) if missing else ''}</div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Ver ficha completa · {item['symbol']}", key=f"crypto_fullpage_select_{suffix}", use_container_width=True):
            st.session_state["crypto_fullpage_coin_id"] = item["coin_id"]
            st.rerun()


def restore_filters() -> None:
    """Streamlit drops the state of widgets that are not drawn in a run, and the filters are not drawn on a coin's page. Their values are
    mirrored in plain keys and put back before the widgets are drawn again (the same approach as the stock screen)."""
    for key, default in FILTER_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = st.session_state.get(f"saved_{key}", default)


def save_filters() -> None:
    for key in FILTER_DEFAULTS:
        if key in st.session_state:
            st.session_state[f"saved_{key}"] = st.session_state[key]


def render_results(hooks: CryptoHooks, scored: list[dict]) -> None:
    restore_filters()
    st.markdown("## Monedas por revisar")
    st.caption("Vista de investigación: ordena las monedas por puntuación; abre una ficha para ver por qué puntúa así. No es recomendación financiera ni predice rentabilidad.")
    c_text, c_level, c_venue, c_protocol, c_per = st.columns([3, 2, 2, 2, 1])
    needle = c_text.text_input("Buscar moneda o símbolo", key="crypto_filter_text", placeholder="Ej.: pepe o bonk")
    level_label = c_level.selectbox("Nivel", list(LEVELS), key="crypto_filter_level")
    venue_text = c_venue.selectbox("Dónde operar", list(VENUE_FILTERS), key="crypto_filter_venue",
                                   help="Monedas que puedes comprar en Kraken (su catálogo público) o en Revolut (tu lista). «Todas» quita el filtro. Solo es información: no suma puntos.")
    protocol_label = c_protocol.selectbox("Protocolo DeFi", PROTOCOL_FILTERS, key="crypto_filter_protocol",
                                          help="«Con datos de protocolo»: monedas que DefiLlama sigue como protocolo con TVL o comisiones. La mayoría de las monedas no lo son, y eso no es una mala señal.")
    per_page = c_per.selectbox("Por página", PER_PAGE_OPTIONS, key="crypto_per_page")
    save_filters()
    signature = (needle, level_label, venue_text, protocol_label, per_page, len(scored))
    if st.session_state.get("crypto_filter_signature") != signature:
        st.session_state["crypto_filter_signature"] = signature
        st.session_state["crypto_page"] = 1  # a new filter starts again from the first page
    venue = VENUE_FILTERS[venue_text]
    rows = filter_results(scored, needle, LEVELS[level_label], protocol_only=protocol_label != PROTOCOL_FILTERS[0], venue=venue)
    summary = st.session_state.get("crypto_summary") or {}
    if venue != "all" and (summary.get("kraken_status", "ok") != "ok" or summary.get("revolut_status", "ok") != "ok"):
        st.caption("El filtro «Dónde operar» solo usa las fuentes que han respondido en esta búsqueda (véase arriba): lo que falte no se da por no disponible, simplemente no se sabe.")
    if not rows:
        st.info("No hay monedas para estos filtros." + (" Prueba con otro texto, con «Puntuadas» o con «Dónde operar: Todas»." if (needle or level_label != "Puntuadas" or venue != "all" or protocol_label != PROTOCOL_FILTERS[0]) else ""))
        return
    shown, page, pages = paginate(rows, int(st.session_state.get("crypto_page", 1)), int(per_page))
    st.session_state["crypto_page"] = page
    first = (page - 1) * int(per_page)
    st.caption(f"Mostrando {first + 1:,}–{first + len(shown):,} de {len(rows):,} monedas · orden: nivel, puntuación y rotación.")
    st.markdown(hooks.css_cards, unsafe_allow_html=True)
    for start in range(0, len(shown), 3):
        for col, item in zip(st.columns(3), shown[start:start + 3]):
            with col:
                _card(hooks, item)
    if pages > 1:
        prev_col, label_col, next_col = st.columns([1, 2, 1])
        if prev_col.button("← Anteriores", key="crypto_page_prev", disabled=page <= 1, use_container_width=True):
            st.session_state["crypto_page"] = page - 1
            st.rerun()
        label_col.markdown(f"<div style='text-align:center;padding-top:8px;'>Página {page:,} de {pages:,}</div>", unsafe_allow_html=True)
        if next_col.button("Siguientes →", key="crypto_page_next", disabled=page >= pages, use_container_width=True):
            st.session_state["crypto_page"] = page + 1
            st.rerun()


# ------------------------------------------------------------------------------------------------------------------- a coin's page

def market_rows(item: dict) -> list[tuple[str, str]]:
    circulating, total, cap, fdv = _num(item.get("circulating_supply")), _num(item.get("total_supply")), _num(item.get("market_cap_usd")), _num(item.get("fdv_usd"))
    rel = _num(item.get("rel_vol_rolling"))
    breakout = item.get("breakout_30d")
    return [
        ("Puesto por capitalización", f"{item['market_cap_rank']:,}".replace(",", ".") if item.get("market_cap_rank") else "N/D"),
        ("Precio", fmt_price(item.get("price_usd"))),
        ("Capitalización", fmt_usd(cap)), ("Volumen 24 h", fmt_usd(item.get("volume_24h_usd"))),
        ("Rotación (volumen 24 h / capitalización)", fmt_ratio(item.get("turnover_24h"))),
        ("Cambio 24 h", fmt_pct(item.get("change_24h_pct"))), ("Cambio 7 d", fmt_pct(item.get("change_7d_pct"))),
        ("Cambio 14 d", fmt_pct(item.get("change_14d_pct"))), ("Cambio 30 d", fmt_pct(item.get("change_30d_pct"))),
        ("Volumen relativo (24 h móvil / media de 30 días completos)", f"{fmt_ratio(rel)} ×" if rel is not None else "N/D (sin serie diaria)"),
        ("Ruptura del máximo de cierre de 30 días", "sí" if breakout is True else ("no" if breakout is False else "N/D (sin serie diaria)")),
        ("Historial en CoinGecko", fmt_history(item)),
        ("Suministro circulante", fmt_supply(circulating)), ("Suministro total", fmt_supply(total)), ("Suministro máximo", fmt_supply(item.get("max_supply"))),
        ("Circulante / total", fmt_ratio(circulating / total) if circulating is not None and total else "N/D"),
        ("Valoración totalmente diluida (FDV)", fmt_usd(fdv)), ("FDV / capitalización", fmt_ratio(fdv / cap) if fdv is not None and cap else "N/D"),
        ("Última actualización de CoinGecko", str(item.get("last_updated") or "N/D").replace("T", " ")[:16] + " UTC" if item.get("last_updated") else "N/D"),
    ]


def breakdown_rows(item: dict) -> list[dict]:
    def value_text(signal: str, value: Any) -> str:
        if signal.startswith("rotación") or signal.startswith("volumen relativo"):
            return f"{fmt_ratio(value)}" + (" ×" if signal.startswith("volumen") and _num(value) is not None else "")
        if signal.startswith("momentum"):
            return fmt_pct(value)
        if signal.startswith("ruptura"):
            return "sí" if value is True else ("no" if value is False else "N/D")
        return fmt_usd(value)

    return [{"Señal": b["signal"].capitalize(), "Valor": value_text(b["signal"], b["value"]), "Puntos": b["points"], "¿Señal fuerte?": "sí" if b["strong"] else "—"}
            for b in item.get("breakdown", [])]


def _load_series(client: CoinGeckoClient | None, cache: ProtectedCache, coin_id: str) -> tuple[Any, str | None]:
    """The coin's daily series (from the 24 h cache, or one call). Returns (series or None, a reason when there is none)."""
    if client is None:
        return None, f"No hay clave de CoinGecko en este equipo (`{KEY_ENV}`): no se puede cargar la serie diaria."
    try:
        return load_daily_series(client, cache, coin_id).data, None
    except BudgetExhausted:
        return None, "No hay presupuesto de llamadas suficiente para cargar la serie diaria de esta moneda."
    except RateLimited:
        return None, "CoinGecko ha limitado el ritmo de peticiones; espera un minuto y vuelve a abrir la ficha."
    except CoinGeckoError as error:
        return None, f"No se pudo cargar la serie diaria. {error}"
    except Exception as error:  # never show str(error): it could carry request details
        return None, f"No se pudo cargar la serie diaria ({type(error).__name__})."


def contract_checks() -> dict:
    """The on-demand contract checks of this session, by coin id. In memory only: nothing from GoPlus is written to disk."""
    return st.session_state.setdefault("crypto_contract_checks", {})


def adjusted_summary(summary: dict, results: list[dict]) -> dict:
    """The search summary with the tier counts of the results as they are now (after the contract checks of the session)."""
    tiers = summarize(results)
    flagged = sum(1 for r in results if "contrato con señales graves" in r.get("risk_flags", []))
    operable = sum(1 for r in results if r["tier"] in CANDIDATE_TIERS and venue_matches(r.get("venues"), "any"))
    return summary | {"tiers": tiers, "candidates": sum(tiers.get(t, 0) for t in CANDIDATE_TIERS), "contract_flagged": flagged, "candidates_operable": operable}


def _pct(value: Any) -> str:
    number = _num(value)
    return "N/D" if number is None else f"{number * 100:.1f} %".replace(".", ",")


def render_check(check: dict) -> None:
    when = str(check.get("checked_at", ""))[:16].replace("T", " ")
    status = check.get("status")
    if status == "no_contract":
        st.info("Esta moneda no tiene contrato en CoinGecko (parece una cadena propia): no hay comprobación posible. Eso no la hace ni segura ni peligrosa: **no verificado**.")
    elif status == "unsupported_chain":
        st.info("Los contratos de esta moneda están en cadenas que GoPlus no cubre (" + ", ".join(check.get("platforms", [])) + "): **no verificado**.")
    elif status == "no_data":
        tried = "; ".join(f"{t['platform']}: {t['outcome']}" for t in check.get("tried", []))
        st.info(f"GoPlus no tiene datos de este contrato en las cadenas probadas ({tried}). **No verificado**: la ausencia de datos no significa que el contrato sea seguro; en el piloto GoPlus respondió con datos solo para cerca del 40 % de los contratos consultados.")
    elif status == "error":
        st.warning(check.get("error") or "No se pudo completar la comprobación.")
    elif status == "checked":
        assessment = check["assessment"]
        where = f"{check['platform']}, {check['address'][:6]}…{check['address'][-4:]}" if len(str(check.get("address"))) > 12 else str(check.get("platform"))
        main = " (cadena principal según CoinGecko)" if check.get("primary") else ""
        st.caption(f"Contrato en {where}{main}. Comprobado a las {when} UTC con GoPlus Security. Se evaluaron {assessment['evaluated']} de {assessment['of']} comprobaciones graves.")
        if check.get("other_platforms"):
            st.caption("La moneda también existe en " + ", ".join(check["other_platforms"]) + " (no comprobado).")
        if assessment["severe"]:
            st.error("**Señales graves:** " + "; ".join(assessment["severe"]) + ". La puntuación de la moneda se limita a 44.")
        else:
            st.info(f"**{check['verdict'].capitalize()}.** Eso no es una garantía: GoPlus omite los campos que no puede evaluar y puede equivocarse; hay riesgos que no comprueba.")
        for note in assessment["notes"]:
            st.warning(note)
        if assessment["info"]:
            st.markdown("#### Información del contrato")
            for entry in assessment["info"]:
                st.write(("⚠ " if entry["level"] == "alert" else "• ") + entry["label"])
        holders = assessment["holders"]
        st.markdown("#### Tenedores")
        count = f"{holders['count']:,}".replace(",", ".") if holders["count"] is not None else "N/D"
        st.caption(f"Número de tenedores según GoPlus: {count} · los 10 mayores concentran {_pct(holders['top10_share'])} (sin contratos, bloqueados ni cuentas etiquetadas: {_pct(holders['top10_share_free'])}). Indicio: incluye contratos de liquidez y exchanges, y GoPlus puede fallar.")
        if holders["top"]:
            st.dataframe(pd.DataFrame([{"Cuenta": h["address"], "Porcentaje": _pct(h["percent"]), "Etiqueta": h["tag"] or "—", "¿Contrato?": "sí" if h["contract"] else "no", "¿Bloqueada?": "sí" if h["locked"] else "no"}
                                       for h in holders["top"]]), use_container_width=True, hide_index=True)
    st.caption("GoPlus es un servicio de terceros: sus límites y condiciones no están documentados y sus datos a veces fallan. Esta comprobación no suma puntos; solo una señal grave limita la puntuación.")


def render_security_tab(item: dict, client: CoinGeckoClient | None, cache: ProtectedCache) -> None:
    st.markdown("Comprueba el contrato de la moneda con **GoPlus Security** (servicio gratuito de terceros): señales graves como honeypot, propietario oculto o imposibilidad de vender, y datos de tenedores. **No es automática**: se hace al pulsar el botón, para una moneda cada vez.")
    checks = contract_checks()
    check = checks.get(item["coin_id"])
    suffix = card_key(item["coin_id"])
    if client is None and check is None:
        st.info(f"No hay clave de CoinGecko en este equipo (`{KEY_ENV}`): hace falta para obtener la dirección del contrato.")
    if st.button("Comprobar contrato" if check is None else "Repetir la comprobación", key=f"crypto_contract_check_{suffix}", disabled=client is None):
        with st.spinner("Consultando el contrato…"):
            checks[item["coin_id"]] = check_contract(client, cache, item["coin_id"])
        st.rerun()  # redraw the whole page: the score and the tier may have changed
    if check is None:
        st.caption(f"Coste: una llamada a CoinGecko (la lista de contratos, 24 h en caché cifrada) y hasta {MAX_CHAINS} consultas a GoPlus con una pausa entre ellas. Si GoPlus no tiene datos, el resultado es «no verificado» y no cambia nada.")
        return
    render_check(check)


@st.cache_data(ttl=300, show_spinner=False)
def _load_perp_detail(symbol: str, mark_price: float) -> tuple[dict | None, str | None]:
    """Open interest and long/short ratio of a verified perpetual, kept in memory for five minutes (a tab switch reruns the page)."""
    try:
        return fetch_perp_detail({"symbol": symbol, "mark_price": mark_price}), None
    except DerivativesError as error:
        return None, str(error)
    except Exception as error:  # never show str(error): it could carry request details
        return None, f"No se pudieron consultar los derivados ({type(error).__name__})."


def render_quality_tab(item: dict) -> None:
    summary = st.session_state.get("crypto_summary") or {}
    quality = item.get("quality")
    note = "Solo información: no suma puntos. Fuente: DefiLlama (datos públicos)."
    if summary.get("quality_status") == "unavailable":
        st.info("No se pudieron consultar los datos de protocolo de DefiLlama en esta búsqueda.")
        st.caption(note)
        return
    if quality is None:
        st.info("Esta moneda no es un protocolo DeFi seguido por DefiLlama (la mayoría de las monedas explosivas no lo son): **sin datos de calidad**, y eso no es una señal negativa ni positiva.")
        st.caption(note)
        return
    chains = ", ".join(quality.get("chains") or []) or "N/D"
    link = f" · [{quality['url']}]({quality['url']})" if quality.get("url") else ""
    st.caption(f"Protocolo **{quality['name']}** ({quality.get('category') or 'sin categoría'}) en {chains}{link}")
    if not has_protocol_data(quality):
        st.info("DefiLlama sigue esta moneda como protocolo pero **no registra TVL ni comisiones** (es habitual en juegos, NFT o cadenas propias): no hay datos de calidad que mostrar.")
        st.caption(note)
        return
    ratios = valuation_ratios(quality, item.get("market_cap_usd"))
    rows = [
        ("TVL (valor depositado)", fmt_usd(quality.get("tvl"))), ("Cambio del TVL a 1 d", fmt_pct(quality.get("tvl_change_1d"))),
        ("Cambio del TVL a 7 d", fmt_pct(quality.get("tvl_change_7d"))), ("Cambio del TVL a 1 mes", fmt_pct(quality.get("tvl_change_1m"))),
        ("Comisiones 24 h", fmt_usd(quality.get("fees_24h"))), ("Comisiones 30 d", fmt_usd(quality.get("fees_30d"))), ("Comisiones 1 año", fmt_usd(quality.get("fees_1y"))),
        ("Ingresos del protocolo 30 d", fmt_usd(quality.get("revenue_30d"))), ("Ingresos del protocolo 1 año", fmt_usd(quality.get("revenue_1y"))),
        ("Capitalización / TVL", fmt_ratio(ratios["mcap_to_tvl"])), ("Capitalización / comisiones del último año", fmt_ratio(ratios["mcap_to_fees_1y"])),
        ("Capitalización / ingresos del último año", fmt_ratio(ratios["mcap_to_revenue_1y"])),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Dato", "Valor"]), use_container_width=True, hide_index=True)
    st.caption("Lectura con cautela: el TVL puede incluir doble recuento e incentivos que lo inflan, y las comisiones que paga la gente no son ingresos del token. Un cociente «N/D» significa que falta el dato o es cero. " + note)


def render_derivatives_tab(item: dict) -> None:
    perp = item.get("perp")
    summary = st.session_state.get("crypto_summary") or {}
    if not perp:
        if summary.get("perps_status") == "unverified":
            st.info("No se pudieron obtener precios frescos de CoinGecko para verificar la identidad de las perpetuas en esta búsqueda: no se muestran derivados.")
        elif item.get("perp_conflict"):
            st.info("Binance tiene un contrato con el mismo símbolo, pero su precio no coincide con el precio fresco de CoinGecko, así que se descarta: podría ser otra moneda. No se muestran derivados.")
        elif summary.get("perps_status") == "unavailable":
            st.info("No se pudo consultar la lista de perpetuas de Binance en esta búsqueda.")
        else:
            st.info("Esta moneda no tiene perpetuo USDT en Binance. Los derivados son la única señal con equivalente directo del «short squeeze», pero solo existen para una parte de las monedas.")
        st.caption("Solo información: los derivados no suman puntos. Fuente: Binance (datos públicos).")
        return
    gap = f"{perp['price_gap'] * 100:.1f}".replace(".", ",")
    st.caption(f"Perpetuo {perp['symbol']} en Binance. Identidad verificada: su precio de marca difiere un {gap} % del precio fresco de CoinGecko.")
    detail, error = _load_perp_detail(perp["symbol"], float(perp["mark_price"]))
    if detail is None:
        st.info(error)
        st.caption("Solo información: los derivados no suman puntos. Fuente: Binance (datos públicos).")
        return
    nxt = perp.get("next_funding_time")
    when = pd.to_datetime(nxt, unit="ms", utc=True).strftime("%Y-%m-%d %H:%M UTC") if nxt else "N/D"
    rows = [
        ("Tasa de financiación actual (por periodo)", fmt_funding(perp.get("funding_rate"))), ("Próxima financiación", when),
        ("Open interest (valor)", fmt_usd(detail.get("open_interest_usd"))),
        ("Cambio del open interest a 7 d", fmt_pct(detail.get("oi_change_7d_pct"))), ("Cambio del open interest a 30 d", fmt_pct(detail.get("oi_change_30d_pct"))),
        ("Ratio largos/cortos (cuentas, último día)", fmt_ratio(detail.get("long_short_ratio"))),
        ("Ratio largos/cortos, mínimo y máximo de 30 d", f"{fmt_ratio(detail.get('long_short_min_30d'))} – {fmt_ratio(detail.get('long_short_max_30d'))}"),
        ("Cuentas largas", f"{_num(detail.get('long_account_share')) * 100:.1f} %".replace(".", ",") if _num(detail.get("long_account_share")) is not None else "N/D"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Dato", "Valor"]), use_container_width=True, hide_index=True)
    if squeeze_hint(perp.get("funding_rate"), item.get("change_7d_pct")):
        st.warning("Financiación negativa con subida a 7 días: los cortos pagan a los largos mientras el precio sube. Es el montaje que precede a un «short squeeze», pero es un indicio para mirar, no una señal.")
    else:
        st.write("La financiación negativa mientras el precio sube (indicio de «short squeeze») no se da ahora en esta moneda.")
    st.caption("Solo información: los derivados no suman puntos. Fuente: Binance (datos públicos); el historial del ratio largos/cortos y del open interest se limita a 30 días.")


def render_venues_section(item: dict) -> None:
    summary = st.session_state.get("crypto_summary") or {}
    venues = item.get("venues") or {}
    kraken, revolut = venues.get("kraken"), venues.get("revolut")
    st.markdown("#### Dónde operar")
    if kraken:
        gap = f"{kraken['price_gap'] * 100:.1f}".replace(".", ",")
        st.write(f"- **Kraken:** mercado {kraken['pair']} (identidad verificada: su precio difiere un {gap} % del precio fresco de CoinGecko).")
    elif summary.get("kraken_status") in ("unavailable", "unverified"):
        st.write("- **Kraken:** no se pudo comprobar en esta búsqueda.")
    elif venues.get("kraken_conflict"):
        st.write("- **Kraken:** hay un mercado con el mismo símbolo, pero su precio no encaja con esta moneda (parece otra): no verificado.")
    else:
        st.write("- **Kraken:** sin mercado en USD ni EUR.")
    if revolut and revolut.get("status") == "confirmed":
        st.write(f"- **Revolut:** en tu lista como «{revolut['name']}» (símbolo y nombre coinciden).")
    elif revolut:
        st.write(f"- **Revolut:** tu lista tiene este símbolo como «{revolut['name']}», pero no se puede confirmar que sea esta moneda (otro nombre u otra moneda con el mismo símbolo): no verificado.")
    elif summary.get("revolut_status") in ("missing", "empty", "unreadable"):
        st.write("- **Revolut:** sin lista de Revolut que consultar.")
    else:
        st.write("- **Revolut:** no está en tu lista.")
    st.caption("Disponibilidad según el catálogo público de Kraken y tu propia lista de Revolut, que puede estar desactualizada: confírmalo en la plataforma antes de operar. Solo información: no suma puntos.")


def render_coin_page(hooks: CryptoHooks, item: dict, client: CoinGeckoClient | None, cache: ProtectedCache) -> None:
    t = hooks.tokens
    style = hooks.tier_style(item["tier"])
    suffix = card_key(item["coin_id"])
    if st.button("← Volver al listado", key="crypto_fullpage_back"):
        st.session_state.pop("crypto_fullpage_coin_id", None)
        st.rerun()
    rank = f" · puesto {item['market_cap_rank']:,}" if item.get("market_cap_rank") else ""
    chips = "".join(_risk_chip(hooks, flag.capitalize()) for flag in item.get("risk_flags", []))
    st.markdown(
        f"""
        <div style="border:1px solid {t['border']};border-left:6px solid {style['border']};border-radius:{t['radius']}px;padding:18px 22px;margin:10px 0 18px;background:#ffffff;">
          <div style="font-weight:700;color:{t['ink']};font-size:22px;">{escape(str(item.get('name') or item['symbol']))}</div>
          <div style="color:{t['secondary']};font-size:13px;margin-top:2px;">{escape(str(item['symbol']))}{escape(rank)}</div>
          <div style="font-size:13px;margin-top:8px;"><a href="{escape(coin_url(item['coin_id']), quote=True)}" target="_blank" rel="noopener noreferrer" style="color:{t['link']};font-weight:600;text-decoration:underline;white-space:nowrap;">CoinGecko ↗</a></div>
          <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-top:10px;"><span style="font-size:44px;font-weight:800;color:{t['ink']};">{int(item['score'])}<span style="font-size:16px;font-weight:600;color:{t['secondary']};">/100</span></span>{_chip(hooks, item['tier'])}</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    why_tab, data_tab, chart_tab, perp_tab, security_tab, quality_tab = st.tabs(["Resumen", "Datos", "Gráfico", "Derivados", "Seguridad", "Calidad"])
    with why_tab:
        render_venues_section(item)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Señales detectadas")
            for driver in item["drivers"] or ["Sin señales explosivas suficientes."]:
                st.write(f"- {driver}")
        with c2:
            st.markdown("#### Qué señales faltan")
            missing = item.get("missing_signals") or []
            for signal in missing or ["Ninguna señal crítica faltante."]:
                st.write(f"- {signal}")
        flags = item.get("risk_flags") or []
        st.markdown("#### Riesgos marcados")
        for flag in flags:
            st.write(f"- **{flag.capitalize()}.** {RISK_EXPLANATIONS.get(flag, '')}")
        if not flags:
            st.write("- Ninguno de los dos riesgos automáticos (volumen sospechoso, dilución) salta en esta moneda. Eso no la hace segura: hay riesgos que estas señales no cubren (el contrato se comprueba aparte, en la pestaña Seguridad).")
        st.markdown("#### Qué revisar manualmente")
        for check in MANUAL_CHECKS:
            st.write(f"- {check}")
        st.caption(item.get("guardrail_text", "No es una recomendación financiera ni predice rentabilidad."))
    with data_tab:
        st.markdown("#### Cifras de mercado")
        st.dataframe(pd.DataFrame(market_rows(item), columns=["Dato", "Valor"]), use_container_width=True, hide_index=True)
        st.markdown("#### Puntuación por señal")
        if item.get("breakdown"):
            st.dataframe(pd.DataFrame(breakdown_rows(item)), use_container_width=True, hide_index=True)
            caps = item.get("caps_applied") or []
            line = f"Puntos antes de los topes: {item['points_before_caps']}. Puntuación final: {int(item['score'])}."
            st.caption(line + ("" if caps else " Ningún tope la reduce."))
            for cap in caps:
                st.write(f"- **Tope aplicado:** {cap['reason']} → máximo {cap['max']}.")
        else:
            st.write("Esta moneda no se puntúa: " + tier_label(item["tier"]).lower() + ".")
        st.caption("No es recomendación financiera ni predice rentabilidad. Datos de CoinGecko.")
    with chart_tab:
        series, reason = _load_series(client, cache, item["coin_id"])
        if series is None:
            st.info(reason)
        elif not any(p.get("price_usd") is not None for p in series):
            st.info("CoinGecko no devolvió cierres diarios para esta moneda.")
        else:
            figure = daily_series_figure(series)
            st.markdown(f'<div style="font-weight:700;color:{t["ink"]};font-size:15px;margin:8px 0 2px;">{escape(str(item["symbol"]))} · cierre diario y volumen</div>', unsafe_allow_html=True)
            st.plotly_chart(figure, use_container_width=True, key=f"crypto_chart_{suffix}")
            st.caption(chart_key_text(has_volume=any(p.get("volume_usd") is not None for p in series), has_reference=reference_high(series) is not None))
            st.caption(f"{len(series):,} días completos · {series[0]['date']} a {series[-1]['date']} · sin velas: el plan gratuito de CoinGecko no da velas diarias, y no se inventan.")
        st.caption("Vista visual de investigación; no ejecuta órdenes ni conecta con ningún broker.")
    with perp_tab:
        render_derivatives_tab(item)
    with security_tab:
        render_security_tab(item, client, cache)
    with quality_tab:
        render_quality_tab(item)


def _search(hooks: CryptoHooks, client: CoinGeckoClient, cache: ProtectedCache) -> None:
    bar = st.progress(0.0, text="Preparando la búsqueda…")

    def on_progress(done: int, total: int, label: str) -> None:
        bar.progress(min(done / max(total, 1), 1.0), text=f"Cargando {label} · {done} de {total}")

    try:
        result = run_search(client, cache, progress=on_progress, revolut_path=Path(hooks.data_dir) / REVOLUT_FILENAME)
    except MissingApiKey:
        bar.empty()
        render_missing_key()
        return
    except BudgetExhausted as error:
        bar.empty()
        st.warning(f"No hay presupuesto de llamadas suficiente para esta búsqueda. {error}")
        return
    except RateLimited:
        bar.empty()
        st.warning("CoinGecko ha limitado el ritmo de peticiones. Espera un minuto y vuelve a intentarlo: lo ya cargado no vuelve a gastar llamadas.")
        return
    except CoinGeckoError as error:
        bar.empty()
        st.error(f"CoinGecko no respondió como se esperaba. {error}")
        return
    except Exception as error:  # never show str(error): it could carry request details
        bar.empty()
        st.error(f"La búsqueda falló ({type(error).__name__}). No se ha guardado nada.")
        return
    bar.empty()
    st.session_state["crypto_results"] = result.scored
    st.session_state["crypto_summary"] = result.summary
    st.session_state["crypto_search_done"] = True
    st.session_state.pop("crypto_fullpage_coin_id", None)  # new results: no stale coin page
    st.rerun()  # redraw with the compact button and the results in their final layout


def selected_coin(results: list[dict]) -> dict | None:
    """The coin whose own page is open, if it is among the results (a filter never kicks the person out of it)."""
    selected = st.session_state.get("crypto_fullpage_coin_id")
    return next((r for r in results if r["coin_id"] == selected), None) if selected else None


def render_crypto_page(hooks: CryptoHooks) -> None:
    done = bool(st.session_state.get("crypto_search_done"))
    results = overlay_checks(st.session_state.get("crypto_results", []), st.session_state.get("crypto_contract_checks", {})) if done else []
    item = selected_coin(results) if done else None
    if item is not None:
        client, cache, _ = _build_client(hooks)
        for key in FILTER_DEFAULTS:  # not drawn here, but kept alive while the coin's page is open; the mirror covers a run that loses them
            if key in st.session_state:
                st.session_state[key] = st.session_state[key]
        hooks.render_banner()
        st.markdown(attribution_html(hooks), unsafe_allow_html=True)
        render_coin_page(hooks, item, client, cache)
        return
    hooks.heading(st, "Unicornios cripto", PAGE_DESCRIPTION)
    hooks.render_banner()
    st.markdown(attribution_html(hooks), unsafe_allow_html=True)
    st.warning(RISK_NOTE)
    client, cache, usage = _build_client(hooks)
    st.markdown(hooks.css_compact if done else hooks.css_big, unsafe_allow_html=True)
    if client is None:
        render_missing_key()
        st.button("🔎 Buscar Unicornios cripto", key="crypto_search", type="primary", use_container_width=True, disabled=True)
        return
    clicked = st.button("🔎 Buscar Unicornios cripto", key="crypto_search", type="primary", use_container_width=True, disabled=hooks.safe_demo,
                        help="Consulta CoinGecko (solo lectura). Los datos se guardan cifrados en este equipo como máximo 24 horas.")
    if hooks.safe_demo:
        st.info(hooks.blocked_message("Buscar unicornios cripto"))
    st.caption("Alcance: unas 2.000 monedas por capitalización, sin stablecoins, versiones envueltas ni liquid staking. Uso personal: la clave de CoinGecko es tuya.")
    render_usage_line(usage)
    if clicked and not hooks.safe_demo:
        _search(hooks, client, cache)
    if done:
        render_summary(hooks, adjusted_summary(st.session_state["crypto_summary"], results))
        render_results(hooks, results)
    st.caption("Datos de mercado de CoinGecko.")
