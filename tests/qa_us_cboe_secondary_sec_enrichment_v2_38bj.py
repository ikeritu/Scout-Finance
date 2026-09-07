#!/usr/bin/env python3
"""Offline QA for v2.38BJ -- the SEC submissions/companyfacts fetcher for
the 538 v2.38BI-resolved Cboe-secondary US candidates. No network calls:
these tests only exercise candidate loading, dry-run reporting and the
--limit bound; the actual network fetch functions (fetch_one/write_json)
are reused unmodified from v2.38E, whose own QA suite already covers
them (qa_phase9e_us_sec_runner_v2_38e.py)."""
from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_us_cboe_secondary_sec_enrichment_v2_38bj.py"

IDENTITY_FIELDS = ["asset_id", "ticker", "company_name", "cik", "sec_name", "sec_ticker", "sec_exchange", "match_tier", "fetch_status", "fetch_reason", "phase", "created_at_utc"]


def module():
    spec = importlib.util.spec_from_file_location("run_us_cboe_secondary_sec_enrichment_v2_38bj", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_identity_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=IDENTITY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def identity_row(asset_id: str, ticker: str, cik: str, fetch_status: str = "resolved") -> dict:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": f"{ticker} Co", "cik": cik, "sec_name": "", "sec_ticker": "", "sec_exchange": "", "match_tier": "exact_normalized_name", "fetch_status": fetch_status, "fetch_reason": "", "phase": "", "created_at_utc": ""}


def test_only_resolved_rows_with_a_cik_are_eligible_candidates():
    """Ambiguous and unresolved rows from v2.38BI must never reach the
    network fetcher -- there is no CIK to fetch for them."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "identity.csv"
        write_identity_csv(path, [
            identity_row("U1", "AAA", "0001111111", "resolved"),
            identity_row("U2", "BBB", "", "unresolved"),
            identity_row("U3", "CCC", "", "ambiguous"),
        ])
        original = mod.IDENTITY_INPUT
        mod.IDENTITY_INPUT = path
        try:
            candidates = mod.load_candidates()
        finally:
            mod.IDENTITY_INPUT = original
    assert len(candidates) == 1
    assert candidates[0]["asset_id"] == "U1"


def test_missing_identity_input_raises_blocked_not_a_silent_empty_run():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        original = mod.IDENTITY_INPUT
        mod.IDENTITY_INPUT = Path(tmp) / "does_not_exist.csv"
        try:
            raised = False
            try:
                mod.load_candidates()
            except SystemExit:
                raised = True
        finally:
            mod.IDENTITY_INPUT = original
    assert raised


def test_dry_run_reports_selection_without_any_network_call(monkeypatch=None):
    """Omitting --execute must never touch the network -- reuses v2.38E's
    select_batch()/has_cache() (already proven) against a synthetic
    two-candidate identity file, in-process so IDENTITY_INPUT can be
    monkeypatched without touching the real 538-row file."""
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        identity_path = Path(tmp) / "identity.csv"
        write_identity_csv(identity_path, [identity_row("U1", "AAA", "0001111111"), identity_row("U2", "BBB", "0002222222")])
        original = mod.IDENTITY_INPUT
        mod.IDENTITY_INPUT = identity_path
        try:
            v38e = mod.load_v38e()
            rows = mod.load_candidates()
            selected = v38e.select_batch(rows, Path(tmp) / "cache", 10)
        finally:
            mod.IDENTITY_INPUT = original
    assert len(rows) == 2
    assert len(selected) == 2
    assert not (Path(tmp) / "cache").exists()  # no cache directory ever created without --execute


def test_batch_limit_out_of_range_is_rejected():
    result = subprocess.run([sys.executable, str(SCRIPT), "--limit", "0"], capture_output=True, text=True, cwd=ROOT)
    assert '"status": "BLOCKED"' in result.stdout
    assert "batch_limit_must_be_1_to_250" in result.stdout


def test_execute_without_user_agent_is_blocked_never_silently_skipped():
    import os
    env = dict(os.environ)
    env.pop("SCOUT_FINANCE_SEC_USER_AGENT", None)
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--limit", "1", "--execute", "--cache-dir", str(Path(tmp) / "cache")],
            capture_output=True, text=True, cwd=ROOT, env=env,
        )
    assert '"status": "BLOCKED"' in result.stdout
    assert "sec_user_agent_missing" in result.stdout


CASES = [
    test_only_resolved_rows_with_a_cik_are_eligible_candidates,
    test_missing_identity_input_raises_blocked_not_a_silent_empty_run,
    test_dry_run_reports_selection_without_any_network_call,
    test_batch_limit_out_of_range_is_rejected,
    test_execute_without_user_agent_is_blocked_never_silently_skipped,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BJ-us-cboe-secondary-sec-enrichment/candidate-filter/blocked-no-agent/limit-bound/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
