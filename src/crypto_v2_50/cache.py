"""Short-lived, encrypted cache for CoinGecko data (v2.50C).

CoinGecko's API terms (read in v2.50B) discourage storing its data and say that, if cached, it must be refreshed at least every
24 hours and stored with strong encryption. So:
  * entries live at most 24 hours and an expired file is deleted, never used;
  * what reaches the disk is encrypted with Windows DPAPI (per-user, no extra dependency, called through ctypes);
  * where DPAPI is not available the cache stays in memory only: plain text is never written;
  * an unreadable or damaged file is deleted (it is third-party data under those terms, unlike the user's own files, which are
    set aside), and the data is fetched again.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

DEFAULT_TTL = timedelta(hours=24)
_ENTROPY = b"scout-finance-crypto-cache-v2.50C"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def dpapi_available() -> bool:
    return sys.platform == "win32"


def _blob(data: bytes):
    import ctypes
    from ctypes import wintypes

    class DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    buffer = ctypes.create_string_buffer(data, len(data))
    return DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer, DataBlob


def _dpapi(data: bytes, protect: bool) -> bytes:
    import ctypes

    source, keep_alive, DataBlob = _blob(data)
    entropy, keep_entropy, _ = _blob(_ENTROPY)
    out = DataBlob()
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    if protect:
        ok = crypt32.CryptProtectData(ctypes.byref(source), None, ctypes.byref(entropy), None, None, 0x1, ctypes.byref(out))
    else:
        ok = crypt32.CryptUnprotectData(ctypes.byref(source), None, ctypes.byref(entropy), None, None, 0x1, ctypes.byref(out))
    if not ok:
        raise OSError("DPAPI call failed")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        kernel32.LocalFree(out.pbData)
        del keep_alive, keep_entropy


def dpapi_protect(data: bytes) -> bytes:
    return _dpapi(data, True)


def dpapi_unprotect(data: bytes) -> bytes:
    return _dpapi(data, False)


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_.-]+", "_", name.lower()).strip("._")[:60] or "entry"
    return f"{cleaned}-{hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]}"


class ProtectedCache:
    """`protect`/`unprotect` are injectable so tests can run anywhere; by default DPAPI on Windows and none elsewhere (memory only)."""

    def __init__(self, directory: Path, ttl: timedelta = DEFAULT_TTL, clock: Callable[[], datetime] = utc_now,
                 protect: Callable[[bytes], bytes] | None | str = "default", unprotect: Callable[[bytes], bytes] | None = None) -> None:
        self.directory = Path(directory)
        self.ttl = ttl
        self.clock = clock
        if protect == "default":
            protect, unprotect = (dpapi_protect, dpapi_unprotect) if dpapi_available() else (None, None)
        self._protect, self._unprotect = protect, unprotect  # type: ignore[assignment]
        self._memory: dict[str, tuple[datetime, Any]] = {}

    @property
    def persistent(self) -> bool:
        return self._protect is not None and self._unprotect is not None

    def _path(self, name: str) -> Path:
        return self.directory / f"{safe_name(name)}.bin"

    def _expired(self, fetched_at: datetime) -> bool:
        return self.clock() - fetched_at >= self.ttl

    def get(self, name: str) -> tuple[Any, datetime] | None:
        """The cached payload and the moment it was fetched, or None when there is nothing fresh enough."""
        entry = self._memory.get(name)
        if entry is not None:
            if not self._expired(entry[0]):
                return entry[1], entry[0]
            self._memory.pop(name, None)
        if not self.persistent:
            return None
        path = self._path(name)
        try:
            blob = path.read_bytes()
        except OSError:
            return None
        try:
            record = json.loads(self._unprotect(blob).decode("utf-8"))  # type: ignore[misc]
            fetched_at = datetime.fromisoformat(record["fetched_at"])
            payload = record["payload"]
            if fetched_at.tzinfo is None:
                raise ValueError("naive timestamp")
        except Exception:  # damaged, tampered or from another user: third-party data under a 24 h rule, so it is deleted
            self._delete(path)
            return None
        if self._expired(fetched_at):
            self._delete(path)
            return None
        self._memory[name] = (fetched_at, payload)
        return payload, fetched_at

    def put(self, name: str, payload: Any) -> bool:
        """Keep the payload. Returns True when it was also written (encrypted) to disk, False when it stays in memory only."""
        now = self.clock()
        self._memory[name] = (now, payload)
        if not self.persistent:
            return False
        try:
            data = json.dumps({"fetched_at": now.isoformat(), "payload": payload}, separators=(",", ":")).encode("utf-8")
            blob = self._protect(data)  # type: ignore[misc]
            self.directory.mkdir(parents=True, exist_ok=True)
            path = self._path(name)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_bytes(blob)
            os.replace(tmp, path)
            return True
        except (OSError, ValueError, TypeError):
            return False

    @staticmethod
    def _delete(path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            pass

    def purge_expired(self) -> int:
        """Delete every file older than the TTL (by modification time, without decrypting) and leftovers of interrupted writes."""
        removed = 0
        if not self.directory.is_dir():
            return 0
        cutoff = self.clock().timestamp() - self.ttl.total_seconds()
        for path in list(self.directory.glob("*.bin")) + list(self.directory.glob("*.tmp")):
            try:
                if path.suffix == ".tmp" or path.stat().st_mtime <= cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
        return removed

    def clear(self) -> None:
        self._memory.clear()
        if self.directory.is_dir():
            for path in list(self.directory.glob("*.bin")) + list(self.directory.glob("*.tmp")):
                self._delete(path)
