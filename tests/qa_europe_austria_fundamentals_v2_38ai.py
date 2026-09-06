#!/usr/bin/env python3
"""Offline QA for the v2.38AI Austria fundamentals runner. No real
network calls, no real credential -- FIXTURE_KEY is a throwaway string,
never the real SCOUT_FINANCE_FIRMENAKTE_API_KEY value. The fixture
response shape below mirrors the real PORR AG (fnr 34853f) response
confirmed live before writing the script.
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
SCRIPT = ROOT / "scripts/run_europe_austria_fundamentals_v2_38ai.py"
CREDENTIAL_ENV = "SCOUT_FINANCE_FIRMENAKTE_API_KEY"
FIXTURE_KEY = "test-fixture-key-not-real"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_gleif_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "legal_name", "home_country", "gleif_lookup_status", "national_registration_number"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def at_row(asset_id: str, ticker: str, legal_name: str, fnr: str) -> dict[str, str]:
    return {"asset_id": asset_id, "ticker": ticker, "legal_name": legal_name, "home_country": "AT", "gleif_lookup_status": "resolved", "national_registration_number": fnr}


def run(mod, argv: list[str], env: dict[str, str]) -> tuple[int, str]:
    old_argv, old_environ = sys.argv, dict(os.environ)
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
        os.environ.clear()
        os.environ.update(old_environ)
    return code, buf.getvalue()


def fake_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


PORR_LIKE_PAYLOAD = {
    "fnr": "34853f", "name": "PORR AG", "isActive": True,
    "legalForm": {"text": "Aktiengesellschaft"}, "court": {"text": "Wien"},
    "parsedJahresabschluesse": [
        {
            "documentKey": "034853_test_doc", "documentDate": "2025-12-31T00:00:00Z",
            "bilanz": {"bilanzSumme": 1775949626.05, "anlageVermoegen": 1038668932.46, "umlaufvermoegen": 686180478.78, "eigenkapital": 589899666.58, "verbindlichkeiten": 1150919959.54, "rueckstellungen": 35129999.93, "liquidesVermoegen": 152519795.44},
            "guv": {"umsatzerloese": 212437331.95, "betriebsErfolg": 9525735.09, "ergebnisVorSteuern": 48976735.75, "jahresueberschuss": 40622686.02},
        },
        {
            "documentKey": "034853_test_doc_prior", "documentDate": "2024-12-31T00:00:00Z",
            "bilanz": {"bilanzSumme": 1600000000.0, "anlageVermoegen": None, "umlaufvermoegen": None, "eigenkapital": 550000000.0, "verbindlichkeiten": None, "rueckstellungen": None, "liquidesVermoegen": None},
            "guv": {"umsatzerloese": 200000000.0, "betriebsErfolg": None, "ergebnisVorSteuern": None, "jahresueberschuss": 35000000.0},
        },
    ],
}


def test_dry_run_reports_austria_eligible_without_network():
    mod = module("at_fund_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [at_row("U1", "ABS2", "PORR AG", "34853f")])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")], {})
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_assets"] == 1


def test_execute_without_credential_is_blocked():
    mod = module("at_fund_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [at_row("U1", "ABS2", "PORR AG", "34853f")])
        code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {})
        assert code == 2 and json.loads(out)["reason"] == "credential_missing"


def test_real_porr_shape_extracts_multi_year_records_and_no_credential_leak():
    """Reproduces the exact real response shape confirmed live for PORR AG
    (fnr 34853f): 2 fiscal years, each with bilanz + guv, one year with
    some fields null (recorded as not-tagged, never guessed)."""
    mod = module("at_fund_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_gleif_matrix(matrix, [at_row("U1", "ABS2", "PORR AG", "34853f")])

        captured_headers = []
        captured_user_agents = []

        def side_effect(request, timeout=30):
            captured_headers.append(request.get_header("X-api-key"))
            captured_user_agents.append(request.get_header("User-agent"))
            return fake_response(PORR_LIKE_PAYLOAD)

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--records-output", str(root / "out" / "records.jsonl"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})
        report = json.loads(out.strip().splitlines()[-1])
        assert report["companies_fetched"] == 1
        assert report["total_records"] == 2 * (7 + 4)  # 2 years x (7 bilanz + 4 guv) concepts
        assert report["extracted_values"] == 11 + 4  # year 1 fully populated (11 concepts), year 2 has 7 nulled fields, 4 present
        assert captured_headers == [FIXTURE_KEY]
        assert FIXTURE_KEY not in json.dumps(report)
        # Real bug found live: the default Python-urllib User-Agent triggers
        # a Cloudflare 403 (error 1010) on this provider -- confirm the
        # honest, descriptive User-Agent is actually being sent, never the
        # library default and never a browser impersonation.
        assert captured_user_agents == ["ScoutFinanceResearch/1.0 (+non-commercial research script)"]

        records = [json.loads(line) for line in (root / "out" / "records.jsonl").open(encoding="utf-8")]
        by_period = {}
        for r in records:
            by_period.setdefault(r["period_end"], {})[r["concept"]] = r
        assert by_period["2025-12-31"]["bilanzSumme"]["value"] == 1775949626.05
        assert by_period["2025-12-31"]["bilanzSumme"]["normalized_fundamentals_present"] is True
        assert by_period["2024-12-31"]["anlageVermoegen"]["value"] is None
        assert by_period["2024-12-31"]["anlageVermoegen"]["normalized_fundamentals_present"] is False
        # Real accounting identity confirmed for PORR AG's actual FY2025
        # filing before accepting this result: Assets = Liabilities +
        # Provisions + Equity (Austrian Bilanz shows Rueckstellungen as a
        # distinct third component, not folded into Verbindlichkeiten).
        y2025 = by_period["2025-12-31"]
        reconstructed = y2025["verbindlichkeiten"]["value"] + y2025["rueckstellungen"]["value"] + y2025["eigenkapital"]["value"]
        assert abs(reconstructed - y2025["bilanzSumme"]["value"]) < 0.01
        assert not list((root / "out").glob("*.tmp"))


CASES = [
    test_dry_run_reports_austria_eligible_without_network,
    test_execute_without_credential_is_blocked,
    test_real_porr_shape_extracts_multi_year_records_and_no_credential_leak,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38AI-austria-fundamentals/dry-run-gate/blocked-without-credential/real-porr-shape/no-credential-leak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
