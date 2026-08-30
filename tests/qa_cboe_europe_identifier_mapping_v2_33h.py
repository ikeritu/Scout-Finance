#!/usr/bin/env python3
"""Offline QA for the Cboe Europe / OpenFIGI identifier-mapping script
(v2.33H). No network calls: OpenFIGI's search endpoint is mocked. OpenFIGI
needs no account or API key for this usage, so there is no credential to
protect here -- these tests only verify the exact-match / fail-closed logic
and the normalization rules.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_cboe_europe_identifiers_v2_33h.py"

SAMPLE_FIELDS = ["pilot_id", "ticker", "company_name", "exchange"]


def module():
    spec = importlib.util.spec_from_file_location("resolve_cboe_europe_identifiers_v2_33h", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_sample(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAMPLE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run(mod, argv: list[str]) -> tuple[int, str]:
    old_argv = sys.argv
    sys.argv = [mod.__name__, *argv]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = mod.main()
    except SystemExit as exc:
        code = exc.code
    finally:
        sys.argv = old_argv
    return code, buf.getvalue()


def test_normalize_strips_legal_suffixes_and_reg():
    mod = module()
    assert mod.normalize("Boeing Co/The") == "BOEING"
    assert mod.normalize("Henkel AG & Co KGaA") == "HENKEL"
    assert mod.normalize("SIEMENS AG-REG") == "SIEMENS"
    assert mod.normalize("British American Tobacco PLC") == "BRITISH AMERICAN TOBACCO"


def extract_last_json(out: str) -> dict:
    text = out.split("PASS:")[0]
    start = text.rindex("\n{\n") + 1 if "\n{\n" in text else text.index("{")
    return json.loads(text[start:])


def fake_search_response(entries: list[dict]):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps({"data": entries}).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_exact_match_resolves_and_excludes_non_common_stock():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P001", "ticker": "XXX", "company_name": "Test Co", "exchange": "CBOE_EUROPE"}])
        entries = [
            {"figi": "F1", "name": "TEST CO", "exchCode": "US", "compositeFIGI": "F1", "shareClassFIGI": "SC1", "securityType": "Common Stock", "securityType2": "Common Stock"},
            {"figi": "F2", "name": "TEST CO", "exchCode": "GR", "compositeFIGI": "F1", "shareClassFIGI": "SC1", "securityType": "Common Stock", "securityType2": "Common Stock"},
            {"figi": "F3", "name": "TEST CO", "exchCode": "EU", "compositeFIGI": "F3", "shareClassFIGI": "SC2ADR", "securityType": "Depositary Receipt", "securityType2": "Depositary Receipt"},
        ]
        with mock.patch("urllib.request.urlopen", return_value=fake_search_response(entries)), mock.patch("time.sleep"):
            code, out = run(mod, [str(sample), str(tmp_path / "out")])
        assert code == 0
        csv_path = tmp_path / "out" / "cboe_europe_identifier_mapping_v2_33h.csv"
        assert csv_path.exists() and not list((tmp_path / "out").glob("*.csv.tmp"))
        rows = {r["pilot_id"]: r for r in csv.DictReader(csv_path.open(encoding="utf-8"))}
        assert rows["P001"]["status"] == "identified_candidate"
        assert rows["P001"]["share_class_figi"] == "SC1"
        assert rows["P001"]["composite_exchange_codes"] == "US"


def test_ambiguous_distinct_companies_blocked():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P002", "ticker": "YYY", "company_name": "Ambiguous Co", "exchange": "CBOE_EUROPE"}])
        entries = [
            {"figi": "G1", "name": "AMBIGUOUS CO", "exchCode": "US", "compositeFIGI": "G1", "shareClassFIGI": "SCA", "securityType": "Common Stock", "securityType2": "Common Stock"},
            {"figi": "G2", "name": "AMBIGUOUS CO", "exchCode": "JP", "compositeFIGI": "G2", "shareClassFIGI": "SCB", "securityType": "Common Stock", "securityType2": "Common Stock"},
        ]
        with mock.patch("urllib.request.urlopen", return_value=fake_search_response(entries)), mock.patch("time.sleep"):
            code, out = run(mod, [str(sample), str(tmp_path / "out")])
        rows = {r["pilot_id"]: r for r in csv.DictReader((tmp_path / "out" / "cboe_europe_identifier_mapping_v2_33h.csv").open(encoding="utf-8"))}
        assert code == 0
        assert rows["P002"]["status"] == "unresolved" and rows["P002"]["reason"] == "ambiguous_multiple_distinct_companies_matched"


def test_no_match_and_missing_share_class_figi_ignored():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [{"pilot_id": "P003", "ticker": "ZZZ", "company_name": "Nomatch Co", "exchange": "CBOE_EUROPE"}])
        entries = [
            {"figi": "H1", "name": "SOMETHING ELSE", "exchCode": "US", "compositeFIGI": "H1", "shareClassFIGI": "SCC", "securityType": "Common Stock", "securityType2": "Common Stock"},
            {"figi": "H2", "name": "NOMATCH CO", "exchCode": "EU", "compositeFIGI": "H3", "shareClassFIGI": None, "securityType": "Common Stock", "securityType2": "Common Stock"},
        ]
        with mock.patch("urllib.request.urlopen", return_value=fake_search_response(entries)), mock.patch("time.sleep"):
            code, out = run(mod, [str(sample), str(tmp_path / "out")])
        rows = {r["pilot_id"]: r for r in csv.DictReader((tmp_path / "out" / "cboe_europe_identifier_mapping_v2_33h.csv").open(encoding="utf-8"))}
        assert code == 0
        assert rows["P003"]["status"] == "unresolved" and rows["P003"]["reason"] == "no_exact_normalized_name_match"


def test_only_filter_limits_rows():
    mod = module()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = tmp_path / "sample.csv"
        write_sample(sample, [
            {"pilot_id": "P001", "ticker": "AAA", "company_name": "Alpha Co", "exchange": "CBOE_EUROPE"},
            {"pilot_id": "P002", "ticker": "BBB", "company_name": "Beta Co", "exchange": "CBOE_EUROPE"},
        ])
        entries = [{"figi": "I1", "name": "ALPHA CO", "exchCode": "US", "compositeFIGI": "I1", "shareClassFIGI": "SCD", "securityType": "Common Stock", "securityType2": "Common Stock"}]
        with mock.patch("urllib.request.urlopen", return_value=fake_search_response(entries)), mock.patch("time.sleep"):
            code, out = run(mod, [str(sample), str(tmp_path / "out"), "--only", "P001"])
        report = extract_last_json(out)
        assert code == 0 and report["input_rows"] == 1


CASES = [
    test_normalize_strips_legal_suffixes_and_reg,
    test_exact_match_resolves_and_excludes_non_common_stock,
    test_ambiguous_distinct_companies_blocked,
    test_no_match_and_missing_share_class_figi_ignored,
    test_only_filter_limits_rows,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.33H-cboe-europe-mapping/exact-match-only/no-guessing/no-network/atomic-write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
