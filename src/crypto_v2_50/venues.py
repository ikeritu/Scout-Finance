"""Where a coin can be traded: Kraken (public catalogue) and Revolut (the person's own list) (v2.50L, phase 8). Pure functions over an injectable
transport and a text file: no key, no Streamlit.

Kraken: its public API (`AssetPairs`, `Ticker`) is official, free and keyless. A coin is linked to a Kraken market only when the SYMBOL matches and the
Kraken price agrees with a FRESH CoinGecko price within 10% (the same identity rule as the Binance perpetuals: several coins share a symbol).

Revolut: it publishes no API or fixed catalogue, so the list is the person's own, kept in a local file (one `TICKER;Name` per line, or tab separated,
`#` for comments). The ticker alone is not an identity either (a ticker like AI or T belongs to many coins), so the NAME must agree with CoinGecko's,
and exactly one coin of the search may qualify: anything else is reported as unverified, never as available.

Both facts are information for filtering: they add no points to the score.
"""
from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, Mapping

from .signals import finite

KRAKEN_URL = "https://api.kraken.com/0/public"
PRICE_TOLERANCE = 0.10
QUOTES = ("USD", "EUR")  # the quotes a person in the euro area trades with; USD is preferred (CoinGecko's price is in dollars)
BASE_ALIASES = {"XBT": "BTC", "XDG": "DOGE"}  # Kraken's own names for Bitcoin and Dogecoin
FIAT = {"EUR", "USD", "GBP", "AUD", "CAD", "CHF", "JPY"}  # currency pairs (EUR/USD) are not coins
_TICKER = re.compile(r"^[A-Z0-9]{1,15}$")
HEADER_WORDS = {"TICKER", "SYMBOL", "SIMBOLO", "SÍMBOLO", "TICKERS"}

Transport = Callable[[str, float], tuple[int, dict, bytes]]


class VenueError(Exception):
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


def _get(path: str, transport: Transport | None, timeout: float = 30.0) -> dict:
    try:
        status, _headers, body = (transport or default_transport)(KRAKEN_URL + path, timeout)
    except Exception as error:  # the message could contain the request; keep only the type
        raise VenueError(f"Kraken no respondió ({type(error).__name__}).") from None
    if status == 429:
        raise VenueError("Kraken limitó el ritmo de peticiones.")
    if status != 200:
        raise VenueError(f"Kraken respondió con HTTP {status}.")
    try:
        data = json.loads(body)
    except ValueError:
        raise VenueError("Kraken devolvió una respuesta que no es JSON.") from None
    if not isinstance(data, dict) or not isinstance(data.get("result"), dict):
        raise VenueError("Kraken devolvió una respuesta con una forma inesperada.")
    if data.get("error"):
        raise VenueError("Kraken respondió con un error.")  # the error text is not repeated
    return data["result"]


def fetch_kraken_markets(transport: Transport | None = None) -> dict[str, list[dict]]:
    """Every online spot market quoted in USD or EUR, keyed by base asset: [{pair, quote, price_usd}]. Two calls: the catalogue and every ticker.
    A EUR price is converted with Kraken's own EUR/USD market; without it the EUR markets are left out rather than guessed."""
    pairs = _get("/AssetPairs", transport)
    tickers = _get("/Ticker", transport)
    eur_usd = None
    for name, pair in pairs.items():
        if isinstance(pair, dict) and pair.get("wsname") == "EUR/USD":
            eur_usd = _last(tickers.get(name))
    markets: dict[str, list[dict]] = {}
    for name, pair in pairs.items():
        if not isinstance(pair, dict) or pair.get("status") not in (None, "online"):
            continue
        wsname = pair.get("wsname")
        if not isinstance(wsname, str) or wsname.count("/") != 1:
            continue
        base, quote = wsname.split("/")
        if quote not in QUOTES:
            continue
        last = _last(tickers.get(name))
        if last is None:
            continue
        price = last if quote == "USD" else (last * eur_usd if eur_usd else None)
        if price is None or price <= 0:
            continue
        base = BASE_ALIASES.get(base.upper(), base.upper())
        if base in FIAT:
            continue
        markets.setdefault(base, []).append({"pair": wsname, "quote": quote, "price_usd": price})
    return markets


def _last(ticker) -> float | None:
    closes = ticker.get("c") if isinstance(ticker, dict) else None
    return finite(closes[0]) if isinstance(closes, list) and closes else None


def match_kraken(row: Mapping, markets: Mapping[str, list[dict]], price: float | None, tolerance: float = PRICE_TOLERANCE) -> tuple[dict | None, bool]:
    """(the verified market or None, whether a market with that symbol existed but could not be confirmed). The link needs a fresh price of the coin
    to agree with Kraken's within the tolerance; without a price nothing is linked."""
    candidates = markets.get(str(row.get("symbol") or "").upper(), [])
    if not candidates:
        return None, False
    reference = finite(price)
    best = None
    if reference is not None and reference > 0:
        for candidate in candidates:
            gap = abs(candidate["price_usd"] / reference - 1)
            if gap < tolerance and (best is None or gap < best["price_gap"] or (gap == best["price_gap"] and candidate["quote"] == "USD")):
                best = candidate | {"price_gap": gap}
    return best, best is None


# ------------------------------------------------------------------------------------------------------------------ Revolut (the person's list)

def parse_revolut_list(text: str) -> tuple[list[dict], int]:
    """([{symbol, name}], the number of lines that were not understood). Lines are `TICKER<TAB>Name…`, `TICKER;Name` or `TICKER,Name`; blank
    lines, `#` comments and a header row are ignored; a symbol is kept once."""
    entries: dict[str, dict] = {}
    skipped = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        separator = "\t" if "\t" in line else (";" if ";" in line else ("," if "," in line else None))
        parts = [p.strip() for p in (line.split(separator) if separator else [line])]
        symbol = parts[0].upper()
        if symbol in HEADER_WORDS:
            continue
        if not _TICKER.match(symbol):
            skipped += 1
            continue
        entries.setdefault(symbol, {"symbol": symbol, "name": parts[1] if len(parts) > 1 and parts[1] else None})
    return list(entries.values()), skipped


def load_revolut_list(path: Path) -> dict:
    """{status, entries, skipped, path}: status is ok | missing | empty | unreadable. The file is the person's own and is only read."""
    path = Path(path)
    if not path.exists():
        return {"status": "missing", "entries": [], "skipped": 0, "path": str(path)}
    try:
        entries, skipped = parse_revolut_list(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError):
        return {"status": "unreadable", "entries": [], "skipped": 0, "path": str(path)}
    return {"status": "ok" if entries else "empty", "entries": entries, "skipped": skipped, "path": str(path)}


def _words(name: object) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(name or "").casefold())


def names_agree(revolut_name: object, coin_name: object) -> bool:
    """The same words in the same order, or one name being the other with extra words AFTER it ("Kyber Network Crystal v2" and "Kyber Network
    Crystal"; "Sky" and "Sky Protocol"). A word that only starts the same way ("Sky" and "Skyrim") does not agree."""
    a, b = _words(revolut_name), _words(coin_name)
    if not a or not b:
        return False
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return long_[:len(short)] == short


def match_revolut(rows: Iterable[Mapping], entries: list[dict]) -> dict[str, dict]:
    """{coin id: {"status": "confirmed" | "unverified", "name": the name on the person's list}} for the coins whose symbol is on the list.
    Confirmed needs the name to agree and exactly one coin of the search to qualify for that symbol; every other coin with the symbol is unverified."""
    by_symbol: dict[str, list[Mapping]] = {}
    wanted = {e["symbol"]: e for e in entries}
    for row in rows:
        symbol = str(row.get("symbol") or "").upper()
        if symbol in wanted:
            by_symbol.setdefault(symbol, []).append(row)
    out: dict[str, dict] = {}
    for symbol, coins in by_symbol.items():
        name = wanted[symbol]["name"]
        agreeing = [c for c in coins if names_agree(name, c.get("name"))]
        for coin in coins:
            confirmed = len(agreeing) == 1 and coin is agreeing[0]
            out[coin["coin_id"]] = {"status": "confirmed" if confirmed else "unverified", "name": name}
    return out


# ------------------------------------------------------------------------------------------------------------------ what the page uses

VENUE_FILTERS = ("all", "any", "kraken", "revolut", "both")


def available(venues: Mapping | None) -> tuple[bool, bool]:
    """(on Kraken, on Revolut): confirmed facts only."""
    venues = venues or {}
    return bool(venues.get("kraken")), (venues.get("revolut") or {}).get("status") == "confirmed"


def venue_label(venues: Mapping | None) -> str | None:
    on_kraken, on_revolut = available(venues)
    return "Kraken + Revolut" if on_kraken and on_revolut else ("Kraken" if on_kraken else ("Revolut" if on_revolut else None))


def venue_matches(venues: Mapping | None, mode: str) -> bool:
    on_kraken, on_revolut = available(venues)
    return {"all": True, "any": on_kraken or on_revolut, "kraken": on_kraken, "revolut": on_revolut, "both": on_kraken and on_revolut}[mode]
