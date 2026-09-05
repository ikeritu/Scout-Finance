#!/usr/bin/env python3
"""Offline QA for the v2.38Z Ireland CRO lookup runner. No real network
calls. Unlike the UK Companies House lookup, this endpoint needs no
credential at all -- confirmed via desk research and a live probe before
writing the script (the CRO's Company Records dataset is fully public on
opendata.cro.ie) -- so there is no "blocked without credential" case to
test here, only the dry-run gate and the fail-closed matching logic.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_europe_ireland_cro_lookup_v2_38z.py"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_resolved_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "isin", "resolution_status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(mod, argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    old_argv, old_environ = sys.argv, dict(os.environ)
    if env is not None:
        os.environ.clear()
        os.environ.update(env)
    sys.argv = [mod.__name__, *argv]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = mod.main()
    except SystemExit as exc:
        code = exc.code
    finally:
        sys.argv = old_argv
        if env is not None:
            os.environ.clear()
            os.environ.update(old_environ)
    return code, buf.getvalue()


def fake_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_dry_run_reports_eligible_without_network():
    mod = module("cro_lookup_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [{"asset_id": "U1", "ticker": "RY4C", "resolved_company_name": "RYANAIR HLDGS PLC", "isin": "IE00BYTBXV33", "resolution_status": "resolved"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")])
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_assets"] == 1


def test_no_credential_needed_execute_runs_directly():
    """Confirms the real, deliberate design difference from UK Companies
    House: this endpoint is fully public, so --execute alone (no
    credential env var) must proceed straight to a real network call,
    never a credential_missing block."""
    mod = module("cro_lookup_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [{"asset_id": "U1", "ticker": "RY4C", "resolved_company_name": "RYANAIR HLDGS PLC", "isin": "IE00BYTBXV33", "resolution_status": "resolved"}])
        with mock.patch("urllib.request.urlopen", side_effect=lambda *a, **k: fake_response({"result": {"records": []}})) as urlopen, mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        assert code == 0 and urlopen.call_count == 1
        report = json.loads(out.strip().splitlines()[-1])
        assert report["credentials_used"] is False


def test_exact_active_match_resolves_and_abbreviated_name_stays_unresolved():
    """Real case this test reproduces: Xetra abbreviates 'Holdings' to
    'HLDGS' in its Instrument field, so 'RYANAIR HLDGS PLC' does not
    exact-normalize-match the real registered name 'RYANAIR HOLDINGS
    PUBLIC LIMITED COMPANY' -- this must stay honestly unresolved, never
    guessed, exactly like the abbreviated GB names in v2.38Y."""
    mod = module("cro_lookup_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_resolved_matrix(matrix, [
            {"asset_id": "U1", "ticker": "LIN", "resolved_company_name": "LINDE PLC", "isin": "IE000S9YS762", "resolution_status": "resolved"},
            {"asset_id": "U2", "ticker": "RY4C", "resolved_company_name": "RYANAIR HLDGS PLC", "isin": "IE00BYTBXV33", "resolution_status": "resolved"},
        ])
        responses = {
            "LINDE PLC": {"result": {"records": [{"company_num": "700000", "company_name": "LINDE PUBLIC LIMITED COMPANY", "company_status": "Normal ", "company_type": "PLC - Public Limited Company", "company_reg_date": "2018-01-01T00:00:00"}]}},
            "RYANAIR HLDGS PLC": {"result": {"records": [{"company_num": "249885", "company_name": "RYANAIR HOLDINGS PUBLIC LIMITED COMPANY", "company_status": "Normal ", "company_type": "PLC - Public Limited Company", "company_reg_date": "1996-06-05T00:00:00"}]}},
        }

        def side_effect(request, timeout=30):
            query = request.full_url.split("q=")[1].split("&")[0]
            import urllib.parse
            name = urllib.parse.unquote_plus(query)
            return fake_response(responses[name])

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"])
        report = json.loads(out.strip().splitlines()[-1])
        assert report["profiles_confirmed"] == 1 and report["unresolved_or_error"] == 1
        rows = list(csv.DictReader((root / "out" / "europe_ireland_cro_lookup_matrix_v2_38z.csv").open(encoding="utf-8")))
        by_ticker = {r["ticker"]: r for r in rows}
        assert by_ticker["LIN"]["company_number"] == "700000"
        assert by_ticker["RY4C"]["lookup_status"] == "unresolved" and by_ticker["RY4C"]["lookup_reason"] == "no_exact_normalized_name_match"
        assert not list((root / "out").glob("*.tmp"))


def test_normalize_handles_dotted_and_irish_specific_suffixes():
    mod = module("cro_lookup_4")
    assert mod.normalize("MEDTRONIC PUBLIC LIMITED COMPANY") == "MEDTRONIC"
    assert mod.normalize("MEDTRONIC PLC") == "MEDTRONIC"
    assert mod.normalize("SOME CO UNLIMITED COMPANY") == "SOME CO"
    assert mod.normalize("SOME CO P.L.C.") == "SOME CO"


CASES = [
    test_dry_run_reports_eligible_without_network,
    test_no_credential_needed_execute_runs_directly,
    test_exact_active_match_resolves_and_abbreviated_name_stays_unresolved,
    test_normalize_handles_dotted_and_irish_specific_suffixes,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38Z-ireland-cro-lookup/dry-run-gate/no-credential-needed/fail-closed-name-match/no-guessing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
