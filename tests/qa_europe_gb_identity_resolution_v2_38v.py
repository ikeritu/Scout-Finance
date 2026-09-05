#!/usr/bin/env python3
"""Offline QA for the v2.38V GB identity resolver. No real network calls:
urllib.request.urlopen is mocked. Covers the dry-run gate, fail-closed
exact-match logic, the trailing-digit-suffix fallback (and that it never
applies silently -- ticker_form_matched must say which form resolved it),
and atomic-write / determinism-adjacent behavior.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_europe_gb_identity_v2_38v.py"


def module():
    spec = importlib.util.spec_from_file_location("resolve_europe_gb_identity_v2_38v", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "company_name", "jurisdiction_code", "mic", "country"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def gb_row(asset_id: str, ticker: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "company_name": "UKI0", "jurisdiction_code": "GB", "mic": "XLON", "country": "GB"}


def fake_response(payload: object):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_dry_run_does_not_touch_network():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "AAA"), gb_row("U2", "BBB")])
        with mock.patch("urllib.request.urlopen") as urlopen:
            report = mod.build(matrix, root / "out", execute=False, limit=0)
        assert urlopen.call_count == 0
        assert report["status"] == "DRY_RUN"
        assert report["input_assets"] == 2
        assert report["network_used"] is False


def test_exact_match_resolves_and_disagreement_does_not():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "SCT"), gb_row("U2", "AMBIG")])
        responses = {
            "SCT": {"data": [{"name": "SOFTCAT PLC", "exchCode": "LN", "shareClassFIGI": "BBGXXX"}]},
            "AMBIG": {"data": [{"name": "COMPANY A", "exchCode": "LN"}, {"name": "COMPANY B", "exchCode": "LN"}]},
        }

        def side_effect(request, timeout=30):
            jobs = json.loads(request.data.decode("utf-8"))
            return fake_response([responses[job["idValue"]] for job in jobs])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            report = mod.build(matrix, root / "out", execute=True, limit=0)
        assert report["resolved"] == 1 and report["unresolved"] == 1
        matrix_rows = list(csv.DictReader((root / "out" / "europe_gb_identity_resolution_matrix_v2_38v.csv").open(encoding="utf-8")))
        by_ticker = {r["ticker"]: r for r in matrix_rows}
        assert by_ticker["SCT"]["resolved_company_name"] == "SOFTCAT PLC"
        assert by_ticker["SCT"]["ticker_form_matched"] == "raw"
        assert by_ticker["AMBIG"]["resolution_status"] == "unresolved"
        assert by_ticker["AMBIG"]["resolution_reason"] == "disagreeing_names_across_openfigi_records"


def test_trailing_digit_fallback_resolves_and_is_labeled_not_silent():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "RIO1")])
        call_log = []

        def side_effect(request, timeout=30):
            jobs = json.loads(request.data.decode("utf-8"))
            call_log.append([job["idValue"] for job in jobs])
            values = jobs[0]["idValue"]
            if values == "RIO1":
                return fake_response([{"warning": "No identifier found."}])
            if values == "RIO":
                return fake_response([{"data": [{"name": "RIO TINTO PLC", "exchCode": "LN", "shareClassFIGI": "BBGRIO"}]}])
            raise AssertionError(f"unexpected ticker queried: {values}")

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            report = mod.build(matrix, root / "out", execute=True, limit=0)
        assert report["resolved"] == 1
        matrix_rows = list(csv.DictReader((root / "out" / "europe_gb_identity_resolution_matrix_v2_38v.csv").open(encoding="utf-8")))
        row = matrix_rows[0]
        assert row["ticker"] == "RIO1"  # reported under the ORIGINAL source ticker, not the stripped form
        assert row["resolved_company_name"] == "RIO TINTO PLC"
        assert row["ticker_form_matched"] == "stripped_trailing_digits"
        assert row["resolution_reason"] == "exact_openfigi_ticker_lse_match_after_stripping_trailing_digit_suffix"
        assert call_log == [["RIO1"], ["RIO"]]  # raw attempted first, stripped only as a fallback


def test_no_match_and_no_strippable_form_stays_unresolved_without_extra_call():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "ABCD")])  # no trailing digits -- nothing to strip
        call_log = []

        def side_effect(request, timeout=30):
            jobs = json.loads(request.data.decode("utf-8"))
            call_log.append([job["idValue"] for job in jobs])
            return fake_response([{"warning": "No identifier found."}])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            report = mod.build(matrix, root / "out", execute=True, limit=0)
        assert report["unresolved"] == 1
        assert call_log == [["ABCD"]]  # only the raw attempt -- no fallback call was made


def test_atomic_write_no_stray_tmp_files():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_matrix(matrix, [gb_row("U1", "SCT")])
        with mock.patch("urllib.request.urlopen", return_value=fake_response([{"data": [{"name": "SOFTCAT PLC", "exchCode": "LN"}]}])), mock.patch("time.sleep"):
            mod.build(matrix, root / "out", execute=True, limit=0)
        assert not list((root / "out").glob("*.tmp"))


CASES = [
    test_dry_run_does_not_touch_network,
    test_exact_match_resolves_and_disagreement_does_not,
    test_trailing_digit_fallback_resolves_and_is_labeled_not_silent,
    test_no_match_and_no_strippable_form_stays_unresolved_without_extra_call,
    test_atomic_write_no_stray_tmp_files,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38V-gb-identity-resolution/dry-run-gate/fail-closed-exact-match/trailing-digit-fallback-not-silent/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
