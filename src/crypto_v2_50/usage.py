"""Call counter for the CoinGecko Demo plan (v2.50C).

CoinGecko does not expose the remaining quota on the Demo plan (`/key` is paid-only and no response carries quota headers, see
v2.50B), so the app counts its own calls. Every request counts, errors included. The counter is the app's own bookkeeping (call
numbers and dates), not CoinGecko data, so it is stored as plain JSON.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# The plan allows 10,000 calls a month. The hard stop is lower on purpose: it leaves room for probes made by hand, and the plan's
# month may not be the calendar month (that is not documented), so the counter resets on the calendar month and keeps a margin.
SAFETY_CAP = 8_000
WARN_FRACTION = 0.8


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


class UsageCounter:
    def __init__(self, path: Path, clock: Callable[[], datetime] = utc_now, safety_cap: int = SAFETY_CAP) -> None:
        self.path = Path(path)
        self.clock = clock
        self.safety_cap = safety_cap

    def _month(self) -> str:
        return self.clock().strftime("%Y-%m")

    def _read(self) -> dict:
        """The stored state for the current month. A missing file is a fresh month; an unreadable one is set aside and the count is
        assumed to be half the safety cap (an unknown count must never be read as zero)."""
        month = self._month()
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {"month": month, "calls": 0, "assumed": False}
        except OSError:
            return {"month": month, "calls": self.safety_cap // 2, "assumed": True}
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or not isinstance(data.get("calls"), int) or isinstance(data.get("calls"), bool) or data["calls"] < 0 or not isinstance(data.get("month"), str):
                raise ValueError("unexpected shape")
        except ValueError:
            assumed = {"month": month, "calls": self.safety_cap // 2, "assumed": True}
            try:
                self.path.replace(self.path.with_name(f"{self.path.name}.corrupt-{self.clock():%Y%m%d%H%M%S}"))
                atomic_write_text(self.path, json.dumps(assumed, sort_keys=True))  # keep the assumption: the next read must not see "no file" (= zero)
            except OSError:
                pass
            return assumed
        if data["month"] != month:
            return {"month": month, "calls": 0, "assumed": False}
        return {"month": month, "calls": data["calls"], "assumed": bool(data.get("assumed", False))}

    def calls_this_month(self) -> int:
        return self._read()["calls"]

    def remaining(self) -> int:
        return max(0, self.safety_cap - self.calls_this_month())

    def can_afford(self, calls: int) -> bool:
        return self.calls_this_month() + max(0, calls) <= self.safety_cap

    def record(self, calls: int = 1) -> int:
        state = self._read()
        state["calls"] += calls
        state["last_call_utc"] = self.clock().isoformat(timespec="seconds")
        atomic_write_text(self.path, json.dumps(state, sort_keys=True))
        return state["calls"]

    def status(self) -> dict:
        state = self._read()
        return {
            "month": state["month"], "calls": state["calls"], "cap": self.safety_cap, "remaining": max(0, self.safety_cap - state["calls"]),
            "warn": state["calls"] >= self.safety_cap * WARN_FRACTION, "assumed": state["assumed"],
        }
