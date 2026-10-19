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

from src.crypto_v2_50 import default_paths
from src.crypto_v2_50.cache import ProtectedCache
from src.crypto_v2_50.charts import chart_key_text, daily_series_figure, reference_high
from src.crypto_v2_50.derivatives import DerivativesError, fetch_perp_detail, squeeze_hint
from src.crypto_v2_50.coingecko import (ATTRIBUTION_TEXT, ATTRIBUTION_URL, KEY_ENV, BudgetExhausted, CoinGeckoClient, CoinGeckoError, MissingApiKey, RateLimited,
                                        load_daily_series, read_api_key)
from src.crypto_v2_50.scoring import MAX_SCORE, TIER_HIGH, TIER_LOW, TIER_MEDIUM, TIER_NO_LIQUIDITY, TIER_WATCH, tier_label
from src.crypto_v2_50.search import filter_results, paginate, run_search
from src.crypto_v2_50.usage import UsageCounter

# Tests set this to inject a fast, offline client (e.g. {"sleep": lambda s: None, "min_interval": 0}); the app never touches it.
CLIENT_OPTIONS: dict[str, Any] = {}

LEVELS = {"Puntuadas": "scored", "Solo candidatas": "candidates", "En vigilancia": "watch", "Sin liquidez suficiente": "no_liquidity"}
PER_PAGE_OPTIONS = [9, 18, 27]
FILTER_DEFAULTS = {"crypto_filter_text": "", "crypto_filter_level": "Puntuadas", "crypto_per_page": PER_PAGE_OPTIONS[0]}
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
    "dilución alta": "Gran parte del suministro todavía no circula (circulante / total < 0,3) o la valoración totalmente diluida es al menos 3 veces la "
                     "capitalización: pueden llegar desbloqueos que presionen el precio. Limita la puntuación a 69, es decir, como mucho nivel bajo.",
}
MANUAL_CHECKS = (
    "Confirmar el precio y el volumen en un exchange o en una segunda fuente: el volumen agregado puede incluir mercados con poca liquidez real.",
    "Revisar el contrato y la distribución de tenedores (concentración, liquidez bloqueada): esa comprobación todavía no está automatizada.",
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
    if summary["detail_failed"]:
        st.warning(f"No se pudo cargar la serie diaria de {summary['detail_failed']:,} monedas: se puntuaron sin ella (máximo 44).")


def _card(hooks: CryptoHooks, item: dict) -> None:
    t = hooks.tokens
    style = hooks.tier_style(item["tier"])
    suffix = card_key(item["coin_id"])
    key = f"crypto_card_{suffix}"
    rank = f" · puesto {item['market_cap_rank']:,}" if item.get("market_cap_rank") else ""
    chips = "".join(_risk_chip(hooks, flag.capitalize()) for flag in item.get("risk_flags", []))
    perp = item.get("perp")
    if perp:
        chips += _info_chip(hooks, f"Con perpetuo · financiación {fmt_funding(perp.get('funding_rate'))}")
        if squeeze_hint(perp.get("funding_rate"), item.get("change_7d_pct")):
            chips += _info_chip(hooks, "Financiación negativa con subida")
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
    c_text, c_level, c_per = st.columns([3, 2, 1])
    needle = c_text.text_input("Buscar moneda o símbolo", key="crypto_filter_text", placeholder="Ej.: pepe o bonk")
    level_label = c_level.selectbox("Nivel", list(LEVELS), key="crypto_filter_level")
    per_page = c_per.selectbox("Por página", PER_PAGE_OPTIONS, key="crypto_per_page")
    save_filters()
    signature = (needle, level_label, per_page, len(scored))
    if st.session_state.get("crypto_filter_signature") != signature:
        st.session_state["crypto_filter_signature"] = signature
        st.session_state["crypto_page"] = 1  # a new filter starts again from the first page
    rows = filter_results(scored, needle, LEVELS[level_label])
    if not rows:
        st.info("No hay monedas para estos filtros." + (" Prueba con otro texto o con «Puntuadas»." if (needle or level_label != "Puntuadas") else ""))
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


@st.cache_data(ttl=300, show_spinner=False)
def _load_perp_detail(symbol: str, mark_price: float) -> tuple[dict | None, str | None]:
    """Open interest and long/short ratio of a verified perpetual, kept in memory for five minutes (a tab switch reruns the page)."""
    try:
        return fetch_perp_detail({"symbol": symbol, "mark_price": mark_price}), None
    except DerivativesError as error:
        return None, str(error)
    except Exception as error:  # never show str(error): it could carry request details
        return None, f"No se pudieron consultar los derivados ({type(error).__name__})."


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
    why_tab, data_tab, chart_tab, perp_tab = st.tabs(["Resumen", "Datos", "Gráfico", "Derivados"])
    with why_tab:
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
            st.write("- Ninguno de los dos riesgos automáticos (volumen sospechoso, dilución) salta en esta moneda. Eso no la hace segura: hay riesgos que aún no se comprueban.")
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


def _search(hooks: CryptoHooks, client: CoinGeckoClient, cache: ProtectedCache) -> None:
    bar = st.progress(0.0, text="Preparando la búsqueda…")

    def on_progress(done: int, total: int, label: str) -> None:
        bar.progress(min(done / max(total, 1), 1.0), text=f"Cargando {label} · {done} de {total}")

    try:
        result = run_search(client, cache, progress=on_progress)
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
    item = selected_coin(st.session_state.get("crypto_results", [])) if done else None
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
        render_summary(hooks, st.session_state["crypto_summary"])
        render_results(hooks, st.session_state["crypto_results"])
    st.caption("Datos de mercado de CoinGecko.")
