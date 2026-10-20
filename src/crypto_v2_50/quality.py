"""Protocol quality data from DefiLlama (v2.50K, phase 7): TVL, fees and revenue of the coins that are DeFi protocols. Pure functions over an
injectable transport: no key, no Streamlit, no disk.

What the v2.50K pilot established and this module honours:
  * the free API needs no key but its limits and terms are not documented, so a search downloads three lists (about 18 MB) and the result is kept
    in memory for one hour, never on disk;
  * `/protocols` carries CoinGecko's id (`gecko_id`) for ~2,400 protocols, which is an exact identity; the fees lists carry `defillamaId`, which
    is the protocol's `id` there, so they are mapped through it;
  * only about 13% of the pre-selected coins have TVL or fees: for the rest "no data" is NEUTRAL (the coin is not a DeFi protocol), never a
    negative signal. The data is information: it adds no points to the score.
"""
from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping

from .signals import finite

BASE_URL = "https://api.llama.fi"
CACHE_SECONDS = 3600
FEES_PATH = "/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"

Transport = Callable[[str, float], tuple[int, dict, bytes]]
_CACHE: dict[str, Any] = {}


class QualityError(Exception):
    """Safe by construction: a short reason, never a URL or a response body."""


def default_transport(url: str, timeout: float) -> tuple[int, dict, bytes]:
    import certifi

    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": "scout-finance-local", "accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def clear_cache() -> None:
    _CACHE.clear()


def _get(path: str, transport: Transport | None, timeout: float = 60.0) -> Any:
    try:
        status, _headers, body = (transport or default_transport)(BASE_URL + path, timeout)
    except Exception as error:  # the message could contain the request; keep only the type
        raise QualityError(f"DefiLlama no respondió ({type(error).__name__}).") from None
    if status == 429:
        raise QualityError("DefiLlama limitó el ritmo de peticiones.")
    if status != 200:
        raise QualityError(f"DefiLlama respondió con HTTP {status}.")
    try:
        return json.loads(body)
    except ValueError:
        raise QualityError("DefiLlama devolvió una respuesta que no es JSON.") from None


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def parse_protocols(raw: Any) -> dict[str, dict]:
    """{DefiLlama protocol id: the fields we keep} for the protocols that carry a CoinGecko id. Everything else is dropped to keep memory small."""
    if not isinstance(raw, list):
        raise QualityError("La lista de protocolos tiene una forma inesperada.")
    out: dict[str, dict] = {}
    for p in raw:
        if not isinstance(p, dict) or not _text(p.get("gecko_id")) or p.get("id") is None:
            continue
        slug = _text(p.get("slug"))
        out[str(p["id"])] = {
            "gecko_id": p["gecko_id"].strip(), "name": _text(p.get("name")) or slug or "?", "slug": slug, "category": _text(p.get("category")),
            "chains": [c for c in (p.get("chains") or []) if isinstance(c, str)][:12], "tvl": finite(p.get("tvl")), "tvl_change_1d": finite(p.get("change_1d")),
            "tvl_change_7d": finite(p.get("change_7d")), "tvl_change_1m": finite(p.get("change_1m")),
        }
    return out


def parse_dimension(raw: Any) -> dict[str, dict]:
    """{DefiLlama protocol id: {24h, 7d, 30d, 1y}} of a fees or revenue overview."""
    protocols = raw.get("protocols") if isinstance(raw, dict) else None
    if not isinstance(protocols, list):
        raise QualityError("La lista de comisiones tiene una forma inesperada.")
    out: dict[str, dict] = {}
    for p in protocols:
        if not isinstance(p, dict) or p.get("defillamaId") is None:
            continue
        out[str(p["defillamaId"])] = {"24h": finite(p.get("total24h")), "7d": finite(p.get("total7d")), "30d": finite(p.get("total30d")), "1y": finite(p.get("total1y"))}
    return out


def build_index(protocols: dict[str, dict], fees: dict[str, dict], revenue: dict[str, dict]) -> dict[str, dict]:
    """{CoinGecko id: quality record}. A protocol that DefiLlama tracks but with no TVL and no fees is still a record (its fields are zero or None)."""
    index: dict[str, dict] = {}
    for llama_id, p in protocols.items():
        f, r = fees.get(llama_id, {}), revenue.get(llama_id, {})
        index[p["gecko_id"]] = {
            "name": p["name"], "slug": p["slug"], "category": p["category"], "chains": p["chains"], "tvl": p["tvl"],
            "tvl_change_1d": p["tvl_change_1d"], "tvl_change_7d": p["tvl_change_7d"], "tvl_change_1m": p["tvl_change_1m"],
            "fees_24h": f.get("24h"), "fees_7d": f.get("7d"), "fees_30d": f.get("30d"), "fees_1y": f.get("1y"),
            "revenue_24h": r.get("24h"), "revenue_7d": r.get("7d"), "revenue_30d": r.get("30d"), "revenue_1y": r.get("1y"),
            "url": f"https://defillama.com/protocol/{p['slug']}" if p["slug"] else None,
        }
    return index


def fetch_quality_index(transport: Transport | None = None, now: Callable[[], float] = time.monotonic, use_cache: bool = True) -> dict[str, dict]:
    """The quality index, from memory when it is less than an hour old, otherwise three downloads (protocols, fees, revenue)."""
    if use_cache and _CACHE and now() - _CACHE["at"] < CACHE_SECONDS:
        return _CACHE["index"]
    protocols = parse_protocols(_get("/protocols", transport))
    fees = parse_dimension(_get(FEES_PATH + "&dataType=dailyFees", transport))
    revenue = parse_dimension(_get(FEES_PATH + "&dataType=dailyRevenue", transport))
    index = build_index(protocols, fees, revenue)
    _CACHE.update({"at": now(), "index": index})
    return index


def has_protocol_data(record: Mapping | None) -> bool:
    """TVL or 30-day fees above zero: the definition used in the pilot's coverage figure."""
    if not record:
        return False
    tvl, fees = finite(record.get("tvl")), finite(record.get("fees_30d"))
    return bool((tvl is not None and tvl > 0) or (fees is not None and fees > 0))


def valuation_ratios(record: Mapping, market_cap: Any) -> dict:
    """Market cap over TVL and over the last year's fees and revenue: each is None unless its denominator is positive."""
    cap = finite(market_cap)

    def ratio(denominator: Any) -> float | None:
        value = finite(denominator)
        return cap / value if cap is not None and cap > 0 and value is not None and value > 0 else None

    return {"mcap_to_tvl": ratio(record.get("tvl")), "mcap_to_fees_1y": ratio(record.get("fees_1y")), "mcap_to_revenue_1y": ratio(record.get("revenue_1y"))}
