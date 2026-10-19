"""The crypto page (v2.50F): title, attribution, one big search button, and the results after the search.

Drawing only: the search itself is `src.crypto_v2_50.search.run_search`. The app passes its tokens and helpers in `CryptoHooks`
(importing the app from here would run it twice). Results live in the session, in memory: nothing from CoinGecko is written to
disk here (the encrypted 24 h cache of the data layer is the only copy).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import streamlit as st

from src.crypto_v2_50 import default_paths
from src.crypto_v2_50.cache import ProtectedCache
from src.crypto_v2_50.coingecko import ATTRIBUTION_TEXT, ATTRIBUTION_URL, KEY_ENV, BudgetExhausted, CoinGeckoClient, CoinGeckoError, MissingApiKey, RateLimited, read_api_key
from src.crypto_v2_50.scoring import MAX_SCORE, TIER_HIGH, TIER_LOW, TIER_MEDIUM, TIER_NO_LIQUIDITY, TIER_WATCH, tier_label
from src.crypto_v2_50.search import filter_results, paginate, run_search
from src.crypto_v2_50.usage import UsageCounter

# Tests set this to inject a fast, offline client (e.g. {"sleep": lambda s: None, "min_interval": 0}); the app never touches it.
CLIENT_OPTIONS: dict[str, Any] = {}

LEVELS = {"Puntuadas": "scored", "Solo candidatas": "candidates", "En vigilancia": "watch", "Sin liquidez suficiente": "no_liquidity"}
PER_PAGE_OPTIONS = [9, 18, 27]
RISK_NOTE = ("Las criptomonedas pueden perder casi todo su valor, y las monedas pequeñas son especialmente volátiles y fáciles de manipular. "
             "Esta pantalla es investigación local: no es una recomendación de compra ni una predicción.")
PAGE_DESCRIPTION = ("Monedas pequeñas con señales de mercado fuertes: mucha rotación de volumen, volumen por encima de su media, subida a 7 y 30 días "
                    "o ruptura de máximos. La búsqueda consulta CoinGecko, excluye stablecoins y versiones envueltas, y marca los riesgos de volumen "
                    "sospechoso y dilución.")


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
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


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


def coin_url(coin_id: Any) -> str:
    return f"https://www.coingecko.com/en/coins/{quote(str(coin_id), safe='')}"


def _chip(hooks: CryptoHooks, tier: str) -> str:
    style = hooks.tier_style(tier)
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;background:{style["chip_bg"]};color:{style["chip_fg"]};'
            f'font-size:12px;font-weight:700;white-space:nowrap;">{escape(tier_label(tier))}</span>')


def _risk_chip(hooks: CryptoHooks, text: str) -> str:
    t = hooks.tokens
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;border:1px solid {t["accent_border"]};background:{t["surface"]};'
            f'color:{t["accent_text"]};font-size:12px;font-weight:700;white-space:nowrap;">{escape(text)}</span>')


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
    if summary["stopped"] == "budget":
        st.warning(f"Se agotó el presupuesto de llamadas del mes durante la búsqueda: {summary['detail_skipped']:,} monedas se puntuaron sin su serie diaria (con ese dato ausente su puntuación no pasa de 44).")
    elif summary["stopped"] == "rate_limited":
        st.warning(f"CoinGecko limitó el ritmo durante la búsqueda: {summary['detail_skipped']:,} monedas se puntuaron sin su serie diaria (con ese dato ausente su puntuación no pasa de 44). Espera un minuto y repite: lo ya cargado no vuelve a gastar llamadas.")
    if summary["detail_failed"]:
        st.warning(f"No se pudo cargar la serie diaria de {summary['detail_failed']:,} monedas: se puntuaron sin ella (máximo 44).")


def _card(hooks: CryptoHooks, item: dict) -> None:
    t = hooks.tokens
    style = hooks.tier_style(item["tier"])
    key = "crypto_card_" + "".join(ch if ch.isalnum() else "_" for ch in str(item["coin_id"]))
    rank = f" · puesto {item['market_cap_rank']:,}" if item.get("market_cap_rank") else ""
    chips = "".join(_risk_chip(hooks, flag.capitalize()) for flag in item.get("risk_flags", []))
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


def render_results(hooks: CryptoHooks, scored: list[dict]) -> None:
    st.markdown("## Monedas por revisar")
    st.caption("Vista de investigación: ordena las monedas por puntuación. No es recomendación financiera ni predice rentabilidad.")
    c_text, c_level, c_per = st.columns([3, 2, 1])
    needle = c_text.text_input("Buscar moneda o símbolo", key="crypto_filter_text", placeholder="Ej.: pepe o bonk")
    level_label = c_level.selectbox("Nivel", list(LEVELS), key="crypto_filter_level")
    per_page = c_per.selectbox("Por página", PER_PAGE_OPTIONS, key="crypto_per_page")
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
    st.rerun()  # redraw with the compact button and the results in their final layout


def render_crypto_page(hooks: CryptoHooks) -> None:
    hooks.heading(st, "Unicornios cripto", PAGE_DESCRIPTION)
    hooks.render_banner()
    st.markdown(attribution_html(hooks), unsafe_allow_html=True)
    st.warning(RISK_NOTE)
    client, cache, usage = _build_client(hooks)
    done = bool(st.session_state.get("crypto_search_done"))
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
