"""Binance USDT-margined perpetuals, public data only (v2.50I). Pure functions over an injectable transport: no key, no Streamlit.

Why identity is checked: in the v2.50H pilot 84 of 155 pre-selected coins matched a perpetual by SYMBOL, but only 74 had a mark price within
10% of CoinGecko's: 10 matches were different coins sharing a symbol. A perpetual is linked to a coin only when its price agrees; otherwise the
coin is reported as a symbol conflict and no derivatives data is attached.

The data is information: it adds no points to the score in v1. Binance's terms say the API is not for arbitrage or high-frequency use and may be
restricted without notice, so the app asks for one list per search and three small calls per coin page.
"""
from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from typing import Callable

from .signals import finite

BASE_URL = "https://fapi.binance.com"
PRICE_TOLERANCE = 0.10
CONTRACT_MULTIPLIERS = {"1000000": 1_000_000, "10000": 10_000, "1000": 1_000, "1M": 1_000_000}  # e.g. 1000PEPEUSDT quotes 1,000 coins
_SYMBOL = re.compile(r"^(1000000|10000|1000|1M)?([A-Z0-9]+?)USDT$")

Transport = Callable[[str, float], tuple[int, dict, bytes]]


class DerivativesError(Exception):
    """Safe by construction: a status and a short reason, never a URL or a response body."""


def default_transport(url: str, timeout: float) -> tuple[int, dict, bytes]:
    import certifi

    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": "scout-finance-local", "accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def _get(path: str, params: dict | None = None, transport: Transport | None = None, timeout: float = 20.0):
    query = ("?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))) if params else ""
    try:
        status, _headers, body = (transport or default_transport)(BASE_URL + path + query, timeout)
    except Exception as error:  # the message could contain the request; keep only the type
        raise DerivativesError(f"Binance no respondió ({type(error).__name__}).") from None
    if status in (418, 429):
        raise DerivativesError("Binance limitó el ritmo de peticiones.")
    if status != 200:
        raise DerivativesError(f"Binance respondió con HTTP {status}.")
    try:
        return json.loads(body)
    except ValueError:
        raise DerivativesError("Binance devolvió una respuesta que no es JSON.") from None


def fetch_perpetuals(transport: Transport | None = None) -> dict[str, list[dict]]:
    """Every USDT perpetual in one call, keyed by base asset (the symbol without the quote and without a x1000 prefix)."""
    data = _get("/fapi/v1/premiumIndex", None, transport)
    if not isinstance(data, list):
        raise DerivativesError("La lista de perpetuas tiene una forma inesperada.")
    perps: dict[str, list[dict]] = {}
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("symbol"), str):
            continue
        match = _SYMBOL.match(item["symbol"])
        mark = finite(item.get("markPrice"))
        if not match or mark is None or mark <= 0:
            continue
        factor = CONTRACT_MULTIPLIERS.get(match.group(1) or "", 1)
        perps.setdefault(match.group(2), []).append({
            "symbol": item["symbol"], "factor": factor, "mark_price": mark, "funding_rate": finite(item.get("lastFundingRate")),
            "next_funding_time": int(item["nextFundingTime"]) if finite(item.get("nextFundingTime")) else None,
        })
    return perps


def match_perpetual(row: dict, perps: dict[str, list[dict]], tolerance: float = PRICE_TOLERANCE, price: float | None = None) -> tuple[dict | None, bool]:
    """(the verified perpetual or None, whether a perpetual with that symbol existed but could not be confirmed). The link needs the price to
    agree. `price` is a FRESH price of the coin: the market data of a search can be hours old (a 24 h cache) and a micro-cap moves more than 10%
    in hours, so comparing a live Binance mark with a stale price would reject real matches. Without it the row's own price is used."""
    candidates = perps.get(str(row.get("symbol") or "").upper(), [])
    price = finite(price) if price is not None else finite(row.get("price_usd"))
    if not candidates:
        return None, False
    best = None
    if price is not None and price > 0:
        for candidate in candidates:
            gap = abs(candidate["mark_price"] / candidate["factor"] / price - 1)
            if gap < tolerance and (best is None or gap < best["price_gap"]):
                best = candidate | {"price_gap": gap}
    return best, best is None


def squeeze_hint(funding_rate: float | None, change_7d_pct: float | None) -> bool:
    """Negative funding (shorts pay longs: the crowd leans short) while the price rose over 7 days: the setup behind a short squeeze. An
    indication to look at, not a signal."""
    funding, change = finite(funding_rate), finite(change_7d_pct)
    return funding is not None and change is not None and funding < 0 and change > 0


def _rows(data) -> list[dict]:
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []


def fetch_perp_detail(perp: dict, transport: Transport | None = None) -> dict:
    """Open interest, its 30-day change and the long/short account ratio of one verified perpetual (three small calls)."""
    symbol = perp["symbol"]
    oi = _get("/fapi/v1/openInterest", {"symbol": symbol}, transport)
    contracts = finite(oi.get("openInterest")) if isinstance(oi, dict) else None
    history = _rows(_get("/futures/data/openInterestHist", {"symbol": symbol, "period": "1d", "limit": 30}, transport))
    ratios = _rows(_get("/futures/data/globalLongShortAccountRatio", {"symbol": symbol, "period": "1d", "limit": 30}, transport))
    values = [v for v in (finite(r.get("sumOpenInterestValue")) for r in history) if v is not None]

    def change(back: int) -> float | None:
        return (values[-1] / values[-1 - back] - 1) * 100 if len(values) > back and values[-1 - back] > 0 else None

    ratio_values = [v for v in (finite(r.get("longShortRatio")) for r in ratios) if v is not None]
    longs = finite(ratios[-1].get("longAccount")) if ratios else None
    return {
        "symbol": symbol,
        "open_interest_usd": contracts * perp["mark_price"] if contracts is not None else None,  # contracts x the price quoted per contract
        "oi_change_7d_pct": change(7), "oi_change_30d_pct": (values[-1] / values[0] - 1) * 100 if len(values) >= 2 and values[0] > 0 else None,
        "oi_history_days": len(values),
        "long_short_ratio": ratio_values[-1] if ratio_values else None, "long_account_share": longs,
        "long_short_min_30d": min(ratio_values) if ratio_values else None, "long_short_max_30d": max(ratio_values) if ratio_values else None,
        "ratio_history_days": len(ratio_values),
    }
