#!/usr/bin/env python3
"""Block v2.38BJ: fetch real SEC submissions + companyfacts JSON for the
538 companies v2.38BI resolved a real CIK for (the Cboe Europe secondary
candidates under country=US, GLEIF-identified by v2.38BC, now CIK-
matched by v2.38BI).

Reuses v2.38E's own proven, resumable, rate-limited, atomic-write fetch
functions (fetch_json/write_json) UNMODIFIED, imported directly -- same
pattern already used to bring Joby Aviation's real data in for v2.38BA.
Writes to its own separate cache directory
(sec_raw_cache_v2_38bj), never touching the v2.38E cache that backs the
fixed-count-guarded 555-company pipeline.

Requires SCOUT_FINANCE_SEC_USER_AGENT (the same credential already used
for the other 555 companies + Joby Aviation -- no new policy decision)
and an explicit --execute flag. Resumable: any CIK already fully cached
(both submissions and companyfacts present) is skipped without a network
call, so this can be re-run in bounded --limit chunks exactly like
v2.38BC's chunked Cboe Europe resolution.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import time
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bi_us_cboe_secondary_identity_sec/us_cboe_secondary_identity_sec_v2_38bi.csv"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38bj_us_cboe_secondary_sec_enrichment"
CACHE_DIR = OUT / "sec_raw_cache_v2_38bj"
MAX_LIMIT = 250


def load_v38e():
    spec = importlib.util.spec_from_file_location("run_us_sec_enrichment_v2_38e", ROOT / "scripts/run_us_sec_enrichment_v2_38e.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_candidates() -> list[dict[str, str]]:
    if not IDENTITY_INPUT.exists():
        raise SystemExit(f"BLOCKED: run scripts/resolve_us_cboe_secondary_identity_sec_v2_38bi.py first ({IDENTITY_INPUT} not found)")
    with IDENTITY_INPUT.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return sorted((r for r in rows if r.get("fetch_status") == "resolved" and r.get("cik")), key=lambda r: (r["asset_id"], r["ticker"]))


def emit(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= MAX_LIMIT:
        return emit({"status": "BLOCKED", "reason": "batch_limit_must_be_1_to_250"}, 2)

    v38e = load_v38e()
    rows = load_candidates()
    selected = v38e.select_batch(rows, args.cache_dir, args.limit)
    skipped_existing = len(rows) - len([r for r in rows if not v38e.has_cache(args.cache_dir, r["cik"])])

    if not args.execute:
        return emit({"status": "DRY_RUN", "eligible_with_cik": len(rows), "skipped_existing": skipped_existing, "selected": len(selected), "network_calls": 0, "phase9c_authorized": False})

    user_agent = os.environ.get("SCOUT_FINANCE_SEC_USER_AGENT", "").strip()
    if not user_agent:
        return emit({"status": "BLOCKED", "reason": "sec_user_agent_missing"}, 2)

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    failures: list[dict] = []
    collected = 0
    network_calls = 0
    submissions_available = 0
    companyfacts_available = 0
    for row in selected:
        cik = row["cik"]
        row_ok = True
        for kind in ("submissions", "companyfacts"):
            try:
                ok, calls, _ = v38e.fetch_one(kind, cik, user_agent, args.cache_dir)
                network_calls += calls
                if kind == "submissions":
                    submissions_available += int(ok)
                else:
                    companyfacts_available += int(ok)
                if calls and args.sleep_seconds > 0:
                    time.sleep(args.sleep_seconds)
            except urllib.error.HTTPError as exc:
                reason = "sec_rate_limited" if exc.code == 429 else f"sec_{kind}_error"
                failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": kind, "reason": reason, "http_status": exc.code})
                row_ok = False
                if exc.code in {403, 429}:
                    return emit(_payload(selected, collected, skipped_existing, failures, network_calls, submissions_available, companyfacts_available), 1)
            except Exception as exc:  # noqa: BLE001
                failures.append({"asset_id": row["asset_id"], "ticker": row["ticker"], "cik": cik, "source": kind, "reason": f"sec_{kind}_error", "detail": exc.__class__.__name__})
                row_ok = False
        collected += int(row_ok)
    return emit(_payload(selected, collected, skipped_existing, failures, network_calls, submissions_available, companyfacts_available), 0 if not failures else 1)


def _payload(selected, collected, skipped_existing, failures, network_calls, submissions_available, companyfacts_available) -> dict:
    return {
        "status": "COMPLETED_WITH_ERRORS" if failures else "COMPLETED",
        "selected": len(selected), "collected": collected, "skipped_existing": skipped_existing,
        "failed": len(failures), "failures": failures, "network_calls": network_calls,
        "submissions_available": submissions_available, "companyfacts_available": companyfacts_available,
        "scoring_calculated": False, "ranking_calculated": False, "recommendations_generated": False, "phase9c_authorized": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
