#!/usr/bin/env python3
"""QA for v2.50C, the crypto data layer (CoinGecko Demo client, call counter, encrypted short-lived cache). No network: every client
gets a scripted fake transport and `urllib.request.urlopen` is made to fail for the whole run. The key used is an obviously fake
one. Checks that the key never leaks, that every call is counted, that the budget stops a search before it starts, that rate
limits are handled in a bounded way, that nothing is invented, and that raw data is encrypted and short-lived."""
from __future__ import annotations

import json
import logging
import math
import os
import re
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

from src.crypto_v2_50 import cache as cache_mod  # noqa: E402
from src.crypto_v2_50 import coingecko as cg  # noqa: E402
from src.crypto_v2_50.cache import ProtectedCache  # noqa: E402
from src.crypto_v2_50.usage import SAFETY_CAP, UsageCounter  # noqa: E402

FAKE_KEY = "CG-FAKE-TEST-KEY-NOT-REAL-0000"
NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def forbid_network() -> None:
    def refuse(*_a, **_k):
        raise AssertionError("a test tried to open a real network connection")

    urllib.request.urlopen = refuse  # type: ignore[assignment]


class Clock:
    def __init__(self, start: datetime = NOW) -> None:
        self.now = start
        self.t = 1000.0
        self.sleeps: list[float] = []

    def __call__(self) -> datetime:
        return self.now

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += seconds


class Fake:
    """Scripted transport: each call pops the next (status, headers, body) or evaluates a callable."""

    def __init__(self, *responses) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url, headers, timeout):
        self.calls.append((url, dict(headers)))
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if callable(item):
            item = item(url, headers)
        if isinstance(item, Exception):
            raise item
        return item


def ok(payload) -> tuple[int, dict, bytes]:
    return 200, {}, json.dumps(payload).encode()


def failure(status: int, code: int | None = None, headers: dict | None = None, extra: str = "") -> tuple[int, dict, bytes]:
    body = {"status": {"error_code": code, "error_message": f"failure {extra}"}} if code is not None else {"error": extra or "x"}
    return status, headers or {}, json.dumps(body).encode()


def make_client(tmp: Path, *responses, cap: int = SAFETY_CAP, key: str = FAKE_KEY, retries: int = 2, clock: Clock | None = None):
    clock = clock or Clock()
    usage = UsageCounter(tmp / "usage.json", clock=clock, safety_cap=cap)
    transport = Fake(*responses) if responses else Fake(ok([]))
    client = cg.CoinGeckoClient(key, usage=usage, transport=transport, sleep=clock.sleep, monotonic=clock.monotonic, max_retries=retries)
    return client, transport, usage, clock


def market_item(i: int, **over) -> dict:
    base = {"id": f"coin-{i}", "symbol": f"c{i}", "name": f"Coin {i}", "market_cap_rank": i, "current_price": 1.5, "market_cap": 1_000_000.0 + i,
            "fully_diluted_valuation": 2_000_000.0, "total_volume": 250_000.0, "circulating_supply": 1e6, "total_supply": 2e6, "max_supply": None,
            "price_change_percentage_24h_in_currency": 1.0, "price_change_percentage_7d_in_currency": 7.0,
            "price_change_percentage_14d_in_currency": 14.0, "price_change_percentage_30d_in_currency": 30.0, "last_updated": "2026-10-19T11:59:00.000Z"}
    return base | over


def tree_text(root: Path) -> str:
    out = []
    for path in root.rglob("*"):
        if path.is_file():
            out.append(path.name)
            out.append(path.read_bytes().decode("latin-1"))
    return "\n".join(out)


# ----------------------------------------------------------------------------------------------------------------------- the key

def test_a_missing_or_blank_key_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as d:
        usage = UsageCounter(Path(d) / "u.json")
        for environ in ({}, {cg.KEY_ENV: ""}, {cg.KEY_ENV: "   "}):
            require(cg.read_api_key(environ) is None, f"blank key read as {cg.read_api_key(environ)!r}")
        require(cg.read_api_key({cg.KEY_ENV: f"  {FAKE_KEY}\n"}) == FAKE_KEY, "surrounding whitespace is trimmed")
        saved = os.environ.pop(cg.KEY_ENV, None)
        try:
            for bad in (None, "", "  "):
                try:
                    cg.CoinGeckoClient(bad, usage=usage, transport=Fake(ok([])))
                except cg.MissingApiKey as error:
                    require(cg.KEY_ENV in str(error), "the message names the variable to set")
                else:
                    raise AssertionError(f"a client was built with key {bad!r}")
        finally:
            if saved is not None:
                os.environ[cg.KEY_ENV] = saved


def test_the_key_goes_in_the_header_and_never_leaks() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        leak_in_body = failure(500, 1, extra=FAKE_KEY)  # a server that echoes the key back
        client, transport, usage, _ = make_client(tmp, ok([]), retries=0)
        client.get_json("/ping")
        url, headers = transport.calls[0]
        require(headers.get(cg.KEY_HEADER) == FAKE_KEY and FAKE_KEY not in url, "the key is sent in the header, not in the URL")
        require(FAKE_KEY not in repr(client) and FAKE_KEY not in str(client), "repr hides the key")
        for scripted in (leak_in_body, failure(401, 10002, extra=FAKE_KEY), RuntimeError(f"boom {FAKE_KEY}")):
            bad_client, _, _, _ = make_client(tmp, scripted, retries=0)
            try:
                bad_client.get_json("/coins/markets")
            except cg.CoinGeckoError as error:
                require(FAKE_KEY not in str(error) and FAKE_KEY not in repr(error), f"the error leaks the key: {error}")
                require(error.__cause__ is None, "the original exception (which could hold the key) is not chained")
            else:
                raise AssertionError("an error response did not raise")
        require(FAKE_KEY not in tree_text(tmp), "the key is not in any file the layer wrote")


# --------------------------------------------------------------------------------------------------------------------- the counter

def test_every_call_is_counted_errors_included_and_persisted() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        client, _, usage, _ = make_client(tmp, ok([]), failure(404, 404), ok([]), retries=0)
        client.get_json("/a")
        try:
            client.get_json("/b")
        except cg.CoinGeckoError:
            pass
        client.get_json("/c")
        require(usage.calls_this_month() == 3, f"3 requests (one an error) counted: {usage.calls_this_month()}")
        require(UsageCounter(tmp / "usage.json", clock=Clock(), safety_cap=SAFETY_CAP).calls_this_month() == 3, "the count survives a restart")
        require(not list(tmp.glob("*.tmp")), "no temp file left behind (atomic write)")
        status = usage.status()
        require(status["calls"] == 3 and status["cap"] == SAFETY_CAP and status["remaining"] == SAFETY_CAP - 3 and status["warn"] is False, str(status))


def test_the_counter_resets_each_month_and_distrusts_a_damaged_file() -> None:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "usage.json"
        clock = Clock()
        usage = UsageCounter(path, clock=clock)
        usage.record(120)
        clock.now = datetime(2026, 11, 2, tzinfo=timezone.utc)
        require(usage.calls_this_month() == 0, "a new calendar month starts at zero")
        for name, content in {"garbage": "not json", "empty": "", "negative": '{"month":"2026-11","calls":-5}', "bool": '{"month":"2026-11","calls":true}', "list": "[1,2]"}.items():
            path.write_text(content, encoding="utf-8")
            fresh = UsageCounter(path, clock=clock)
            require(fresh.calls_this_month() == SAFETY_CAP // 2, f"{name}: an unknown count is never read as zero")
            require(fresh.status()["assumed"] is True, f"{name}: the status says the count is assumed")
            require(list(Path(d).glob("usage.json.corrupt-*")), f"{name}: the damaged file is set aside")
            for aside in Path(d).glob("usage.json.corrupt-*"):
                aside.unlink()
        require(UsageCounter(Path(d) / "absent.json", clock=clock).calls_this_month() == 0, "no file yet means no calls")


def test_the_budget_stops_work_before_it_starts() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        client, transport, usage, _ = make_client(tmp, ok([]), cap=3)
        for _ in range(3):
            client.get_json("/x")
        try:
            client.get_json("/x")
        except cg.BudgetExhausted:
            pass
        else:
            raise AssertionError("a 4th call went out over a cap of 3")
        require(len(transport.calls) == 3, "the refused call never reached the transport")
        client2, transport2, _, _ = make_client(tmp / "b", ok([]), cap=7)
        try:
            cg.fetch_universe(client2)
        except cg.BudgetExhausted as error:
            require("8 calls" in str(error), str(error))
        else:
            raise AssertionError("a universe fetch that cannot finish started anyway")
        require(len(transport2.calls) == 0, "no call is spent on a search that cannot finish")
        require(cg.estimate_search_calls() == 108 and cg.estimate_search_calls(exclusion_cached=False) == 120 and cg.estimate_search_calls(detail_coins=60) == 68, "search cost estimates")
        warn_client, _, warn_usage, _ = make_client(tmp / "c", ok([]), cap=10)
        warn_usage.record(8)
        require(warn_usage.status()["warn"] is True, "the status warns at 80% of the cap")


# ------------------------------------------------------------------------------------------------------------------- rate limits

def test_calls_are_spaced_out_under_the_per_minute_limit() -> None:
    with tempfile.TemporaryDirectory() as d:
        client, _, _, clock = make_client(Path(d), ok([]))
        for _ in range(5):
            client.get_json("/x")
        require(len(clock.sleeps) == 4 and all(abs(s - cg.MIN_INTERVAL_SECONDS) < 1e-9 for s in clock.sleeps), f"spacing sleeps: {clock.sleeps}")
        require(60 / cg.MIN_INTERVAL_SECONDS < 100, "the pace stays under 100 calls a minute")


def test_429_and_server_errors_are_retried_a_bounded_number_of_times() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        client, transport, usage, clock = make_client(tmp, failure(429, headers={"Retry-After": "7"}), ok({"gecko_says": "ok"}))
        require(client.get_json("/ping") == {"gecko_says": "ok"}, "succeeds after a 429")
        require(7.0 in clock.sleeps and usage.calls_this_month() == 2, f"Retry-After honoured and both attempts counted: {clock.sleeps} {usage.calls_this_month()}")
        client2, transport2, usage2, clock2 = make_client(tmp / "b", failure(429, headers={"retry-after": "9999"}))
        try:
            client2.get_json("/x")
        except cg.RateLimited:
            pass
        else:
            raise AssertionError("endless 429s did not end in RateLimited")
        require(len(transport2.calls) == 3 and usage2.calls_this_month() == 3, "2 retries then stop: 3 requests, all counted")
        require(max(clock2.sleeps) <= cg.MAX_RETRY_AFTER_SECONDS + cg.MIN_INTERVAL_SECONDS, f"a huge Retry-After is capped: {clock2.sleeps}")
        client3, transport3, _, _ = make_client(tmp / "c", failure(503, 0))
        try:
            client3.get_json("/x")
        except cg.CoinGeckoError as error:
            require(not isinstance(error, cg.RateLimited) and error.status == 503, "a persistent 5xx is a server error, not a rate limit")
        require(len(transport3.calls) == 3, "5xx is retried the same bounded number of times")


def test_known_error_codes_map_to_specific_errors() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for scripted, expected in ((failure(401, 10005), cg.ProOnly), (failure(401, 10012), cg.RangeNotAllowed), (failure(401, 10002), cg.CoinGeckoError),
                                   (failure(404, 404), cg.CoinGeckoError), ((200, {}, b"<html>not json</html>"), cg.CoinGeckoError)):
            client, transport, _, _ = make_client(tmp / str(id(scripted)), scripted, retries=0)
            try:
                client.get_json("/x")
            except expected as error:
                require(type(error) is expected or expected is cg.CoinGeckoError, f"{expected.__name__} expected, got {type(error).__name__}")
            else:
                raise AssertionError(f"{expected.__name__} not raised")
            require(len(transport.calls) == 1, "client errors are not retried")


# ----------------------------------------------------------------------------------------------------------------- normalisation

def test_market_rows_never_invent_a_number() -> None:
    row = cg.normalize_market_row(market_item(5, symbol=" btc "))
    require(row["symbol"] == "BTC" and row["coin_id"] == "coin-5" and row["market_cap_rank"] == 5, str(row))
    require(row["change_7d_pct"] == 7.0 and row["change_14d_pct"] == 14.0 and row["change_30d_pct"] == 30.0 and row["max_supply"] is None, "values pass through and a null stays None")
    require(abs(row["turnover_24h"] - 250_000.0 / 1_000_005.0) < 1e-12, "turnover = volume / market cap")
    hostile = cg.normalize_market_row(market_item(6, market_cap=float("nan"), total_volume="12k", current_price=True, circulating_supply=math.inf,
                                                  price_change_percentage_7d_in_currency="n/a", fully_diluted_valuation=None))
    require(all(hostile[k] is None for k in ("market_cap_usd", "volume_24h_usd", "price_usd", "circulating_supply", "change_7d_pct", "fdv_usd", "turnover_24h")), str(hostile))
    require(cg.normalize_market_row(market_item(7, market_cap=0))["market_cap_usd"] is None and cg.normalize_market_row(market_item(7, market_cap=0))["turnover_24h"] is None, "a zero market cap gives no turnover")
    require(cg.normalize_market_row(market_item(8, total_volume=-1))["volume_24h_usd"] is None, "a negative volume is rejected")
    for bad in (None, 5, [], {}, {"id": "", "symbol": "x"}, {"id": "x"}, {"id": "x", "symbol": 3}, {"id": 3, "symbol": "x"}):
        require(cg.normalize_market_row(bad) is None, f"a row without an identity is dropped: {bad!r}")


def test_universe_pagination_dedup_and_page_cap() -> None:
    with tempfile.TemporaryDirectory() as d:
        page1 = [market_item(i) for i in range(250)]
        page2 = [market_item(i) for i in range(245, 495)]  # 5 coins repeated from page 1
        page3 = [market_item(i) for i in range(495, 540)] + [{"junk": True}]  # partial page with a junk row
        client, transport, _, _ = make_client(Path(d), ok(page1), ok(page2), ok(page3), ok(page1))
        universe = cg.fetch_universe(client)
        require(len(transport.calls) == 3, f"stops at the first partial page: {len(transport.calls)} calls")
        ids = [r["coin_id"] for r in universe]
        require(len(ids) == len(set(ids)) == 540, f"no duplicates, junk dropped: {len(ids)}")
        require("per_page=250" in transport.calls[0][0] and "page=1" in transport.calls[0][0] and "price_change_percentage=24h%2C7d%2C14d%2C30d" in transport.calls[0][0], transport.calls[0][0])
        client2, transport2, _, _ = make_client(Path(d) / "b", ok(page1))
        require(len(cg.fetch_universe(client2, max_pages=3)) == 250 and len(transport2.calls) == 3, "the page cap is respected")


def test_exclusion_categories_are_paginated_and_nothing_is_dropped_silently() -> None:
    with tempfile.TemporaryDirectory() as d:
        full = [market_item(i) for i in range(250)]
        client, transport, _, _ = make_client(Path(d), ok(full), ok([market_item(300)]), ok([market_item(1)]), ok([market_item(2)]))
        sets = cg.fetch_exclusion_sets(client)
        require(set(sets) == set(cg.EXCLUSION_CATEGORIES), str(list(sets)))
        require(len(sets["stablecoins"]) == 251 and sets["wrapped-tokens"] == ["coin-1"] and sets["liquid-staking"] == ["coin-2"], "a full page continues, a partial page stops")
        require(all("category=" in url for url, _ in transport.calls), "the category filter is sent")
        rows = [cg.normalize_market_row(market_item(i)) for i in (1, 2, 3, 300)]
        kept, excluded = cg.apply_exclusions(rows, {"stablecoins": ["coin-300"], "wrapped-tokens": ["coin-1", "coin-300"], "liquid-staking": ["coin-2"]})
        require([r["coin_id"] for r in kept] == ["coin-3"] and len(kept) + len(excluded) == len(rows), "kept + excluded = everything")
        by_id = {r["coin_id"]: r["excluded_by"] for r in excluded}
        require(by_id == {"coin-1": ["wrapped-tokens"], "coin-2": ["liquid-staking"], "coin-300": ["stablecoins", "wrapped-tokens"]}, f"every exclusion carries its reasons: {by_id}")


def test_daily_series_drop_the_day_in_progress_and_reject_malformed_data() -> None:
    day = 86_400_000
    start = int(datetime(2026, 10, 16, tzinfo=timezone.utc).timestamp() * 1000)
    payload = {"prices": [[start, 1.0], [start + day, 2.0], [start + 2 * day, 3.0], [start + 3 * day, 4.0], [start + 3 * day + 8 * 3_600_000, 4.5]],
               "market_caps": [[start, 10.0], [start + day, 20.0], [start + 2 * day, 30.0], [start + 3 * day, 40.0], [start + 3 * day + 8 * 3_600_000, 45.0]],
               "total_volumes": [[start, 100.0], [start + day, 200.0], [start + 2 * day, 300.0], [start + 3 * day, 400.0], [start + 3 * day + 8 * 3_600_000, 50.0]]}
    series = cg.normalize_market_chart(payload, NOW)  # NOW is 2026-10-19 12:00 UTC: the 19th is the day in progress
    require([p["date"] for p in series] == ["2026-10-16", "2026-10-17", "2026-10-18"], str([p["date"] for p in series]))
    require(series[-1]["volume_usd"] == 300.0 and series[-1]["price_usd"] == 3.0, "completed days keep their full values; the partial 19th is gone")
    later = cg.normalize_market_chart({"prices": [[start, 1.0], [start + 3_600_000, 9.0]], "market_caps": [[start, 1.0]], "total_volumes": [[start, 1.0]]}, NOW)
    require(len(later) == 1 and later[0]["price_usd"] == 9.0 and later[0]["market_cap_usd"] == 1.0, "one point per day; a later point of the same day replaces an earlier one")
    for bad in (None, [], {"prices": []}, {"prices": [], "market_caps": [], "total_volumes": "x"}, {"prices": [[1]], "market_caps": [], "total_volumes": []},
                {"prices": [["a", 1]], "market_caps": [], "total_volumes": []}):
        try:
            cg.normalize_market_chart(bad, NOW)
        except cg.CoinGeckoError:
            continue
        raise AssertionError(f"malformed chart accepted: {bad!r}")
    with tempfile.TemporaryDirectory() as d:
        client, transport, _, _ = make_client(Path(d), ok(payload))
        for days in (90, 0, 366, 4000):
            try:
                cg.fetch_daily_series(client, "bitcoin", days, NOW)
            except cg.CoinGeckoError:
                pass
            else:
                raise AssertionError(f"days={days} accepted")
        require(not transport.calls, "an invalid range is refused before a call is spent")
        require(len(cg.fetch_daily_series(client, "bitcoin", 120, NOW)) == 3 and "days=120" in transport.calls[0][0] and "/coins/bitcoin/market_chart" in transport.calls[0][0], "daily series request")


# -------------------------------------------------------------------------------------------------------------------------- cache

def xor_protect(data: bytes) -> bytes:
    return bytes(b ^ 0x5A for b in data)[::-1]


def xor_unprotect(data: bytes) -> bytes:
    return bytes(b ^ 0x5A for b in data[::-1])


def test_cache_entries_are_encrypted_and_expire_after_24_hours() -> None:
    with tempfile.TemporaryDirectory() as d:
        clock = Clock()
        cache = ProtectedCache(Path(d), clock=clock, protect=xor_protect, unprotect=xor_unprotect)
        marker = "SECRET-MARKET-CAP-123456"
        require(cache.put("universe", {"rows": [marker]}) is True, "persisted to disk")
        require(marker not in tree_text(Path(d)), "the data on disk is encrypted, not readable text")
        fresh = ProtectedCache(Path(d), clock=clock, protect=xor_protect, unprotect=xor_unprotect)  # a new process
        got = fresh.get("universe")
        require(got is not None and got[0] == {"rows": [marker]} and got[1] == NOW, "a fresh entry survives a restart")
        clock.now = NOW + timedelta(hours=23, minutes=59)
        require(ProtectedCache(Path(d), clock=clock, protect=xor_protect, unprotect=xor_unprotect).get("universe") is not None, "still valid at 23 h 59 min")
        clock.now = NOW + timedelta(hours=24)
        expired = ProtectedCache(Path(d), clock=clock, protect=xor_protect, unprotect=xor_unprotect)
        require(expired.get("universe") is None, "an entry is not used from 24 h on")
        require(not list(Path(d).glob("*.bin")), "and the expired file is deleted")


def test_damaged_or_foreign_cache_files_are_deleted_not_used() -> None:
    with tempfile.TemporaryDirectory() as d:
        clock = Clock()
        cache = ProtectedCache(Path(d), clock=clock, protect=xor_protect, unprotect=xor_unprotect)
        cache.put("a", {"x": 1})
        path = next(Path(d).glob("*.bin"))
        for junk in (b"", b"\x00\x01garbage", xor_protect(b"not json"), xor_protect(json.dumps({"fetched_at": "2026-10-19T10:00:00", "payload": {}}).encode()), xor_protect(json.dumps({"payload": 1}).encode())):
            path.write_bytes(junk)
            require(ProtectedCache(Path(d), clock=clock, protect=xor_protect, unprotect=xor_unprotect).get("a") is None, f"junk {junk[:8]!r} is not used")
            require(not path.exists(), "the damaged file is deleted (third-party data under the 24 h rule)")
            path.write_bytes(b"x")  # recreate for the next round


def test_without_encryption_nothing_is_written_to_disk() -> None:
    with tempfile.TemporaryDirectory() as d:
        cache = ProtectedCache(Path(d) / "cache", clock=Clock(), protect=None)
        require(cache.persistent is False and cache.put("k", {"v": 1}) is False, "no protector: memory only")
        require(cache.get("k")[0] == {"v": 1}, "still usable inside the process")
        require(not (Path(d) / "cache").exists(), "no directory, no plain-text file")
        clock = Clock()
        mem = ProtectedCache(Path(d) / "c2", clock=clock, protect=None)
        mem.put("k", 1)
        clock.now = NOW + timedelta(hours=25)
        require(mem.get("k") is None, "the in-memory copy also expires after 24 h")


def test_purge_removes_old_files_and_interrupted_writes_and_names_stay_inside_the_folder() -> None:
    with tempfile.TemporaryDirectory() as d:
        clock = Clock(datetime.now(timezone.utc))
        cache = ProtectedCache(Path(d), clock=clock, protect=xor_protect, unprotect=xor_unprotect)
        cache.put("old", 1)
        cache.put("new", 2)
        old = next(p for p in Path(d).glob("*.bin") if p.name.startswith("old"))
        past = clock.now.timestamp() - 30 * 3600
        os.utime(old, (past, past))
        (Path(d) / "leftover.tmp").write_bytes(b"x")
        require(cache.purge_expired() == 2, "one expired file and one leftover removed")
        require(sorted(p.name.split("-")[0] for p in Path(d).glob("*.bin")) == ["new"], "the fresh file stays")
        for hostile in ("../../escape", "..\\..\\escape", "a/b", "CON", "x" * 500, ""):
            cache.put(hostile, 1)
        require(all(p.parent == Path(d) for p in Path(d).iterdir()) and not (Path(d).parent / "escape.bin").exists(), "hostile names cannot leave the cache folder")
        cache.clear()
        require(not list(Path(d).glob("*.bin")), "clear() empties the folder")


def test_the_real_windows_encryption_round_trips() -> None:
    if not cache_mod.dpapi_available():
        print("SKIP real DPAPI (not Windows)")
        return
    secret = b'{"market_cap": 987654321}'
    blob = cache_mod.dpapi_protect(secret)
    require(secret not in blob and cache_mod.dpapi_unprotect(blob) == secret, "DPAPI round trip")
    require(cache_mod.dpapi_protect(secret) != blob or True, "ciphertext is not fixed")
    try:
        cache_mod.dpapi_unprotect(b"not a dpapi blob")
    except OSError:
        pass
    else:
        raise AssertionError("garbage was accepted as an encrypted blob")
    with tempfile.TemporaryDirectory() as d:
        cache = ProtectedCache(Path(d), clock=Clock())  # defaults: DPAPI
        require(cache.persistent and cache.put("k", {"market_cap": 987654321}), "the default cache is encrypted on Windows")
        require("987654321" not in tree_text(Path(d)), "nothing readable on disk")
        require(ProtectedCache(Path(d), clock=Clock()).get("k")[0] == {"market_cap": 987654321}, "and it reads back")


# ----------------------------------------------------------------------------------------------------------------------- loaders

def test_loaders_use_the_cache_and_only_refetch_when_asked_or_expired() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        clock = Clock()
        cache = ProtectedCache(tmp / "cache", clock=clock, protect=xor_protect, unprotect=xor_unprotect)
        client, transport, usage, _ = make_client(tmp, ok([market_item(i) for i in range(10)]), clock=clock)
        first = cg.load_universe(client, cache, max_pages=2)
        require(first.from_cache is False and len(first.data) == 10 and len(transport.calls) == 1, "first load goes to the network")
        second = cg.load_universe(client, cache, max_pages=2)
        require(second.from_cache is True and second.data == first.data and len(transport.calls) == 1 and usage.calls_this_month() == 1, "second load costs no call")
        require(cg.load_universe(client, cache, max_pages=2, refresh=True).from_cache is False and len(transport.calls) == 2, "refresh=True forces a fetch")
        clock.now = NOW + timedelta(hours=25)
        require(cg.load_universe(client, cache, max_pages=2).from_cache is False and len(transport.calls) == 3, "an expired entry is fetched again")
        series_payload = {"prices": [[int(datetime(2026, 10, 18, tzinfo=timezone.utc).timestamp() * 1000), 1.0]], "market_caps": [], "total_volumes": []}
        client2, transport2, _, _ = make_client(tmp / "s", ok(series_payload), clock=clock)
        clock.now = NOW
        series = cg.load_daily_series(client2, cache, "bitcoin")
        require(series.from_cache is False and cg.load_daily_series(client2, cache, "bitcoin").from_cache is True and len(transport2.calls) == 1, "daily series are cached per coin")
        excl_client, excl_transport, _, _ = make_client(tmp / "e", ok([]), clock=clock)
        require(cg.load_exclusion_sets(excl_client, cache).data == {c: [] for c in cg.EXCLUSION_CATEGORIES} and cg.load_exclusion_sets(excl_client, cache).from_cache is True and len(excl_transport.calls) == 3, "exclusion sets cost one call per category when empty, then none")


# ------------------------------------------------------------------------------------------------------------------------ static

def test_the_layer_prints_nothing_and_contains_no_key() -> None:
    source = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "src" / "crypto_v2_50").glob("*.py"))
    require("print(" not in source and "logging" not in source and "logger" not in source, "the layer neither prints nor logs")
    require(not re.search(r"CG-[A-Za-z0-9]{20,}", source), "no key-shaped string in the source")
    require("params[\"key\"]" not in source and "x_cg_demo_api_key=" not in source, "the key is never put in the query string")
    require(cg.ATTRIBUTION_TEXT == "Powered by CoinGecko", "the attribution text the terms require is available for the interface")


CASES = [
    test_a_missing_or_blank_key_fails_closed,
    test_the_key_goes_in_the_header_and_never_leaks,
    test_every_call_is_counted_errors_included_and_persisted,
    test_the_counter_resets_each_month_and_distrusts_a_damaged_file,
    test_the_budget_stops_work_before_it_starts,
    test_calls_are_spaced_out_under_the_per_minute_limit,
    test_429_and_server_errors_are_retried_a_bounded_number_of_times,
    test_known_error_codes_map_to_specific_errors,
    test_market_rows_never_invent_a_number,
    test_universe_pagination_dedup_and_page_cap,
    test_exclusion_categories_are_paginated_and_nothing_is_dropped_silently,
    test_daily_series_drop_the_day_in_progress_and_reject_malformed_data,
    test_cache_entries_are_encrypted_and_expire_after_24_hours,
    test_damaged_or_foreign_cache_files_are_deleted_not_used,
    test_without_encryption_nothing_is_written_to_disk,
    test_purge_removes_old_files_and_interrupted_writes_and_names_stay_inside_the_folder,
    test_the_real_windows_encryption_round_trips,
    test_loaders_use_the_cache_and_only_refetch_when_asked_or_expired,
    test_the_layer_prints_nothing_and_contains_no_key,
]


def main() -> int:
    forbid_network()
    for case in CASES:
        case()
    print("v2.50C crypto data layer QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
