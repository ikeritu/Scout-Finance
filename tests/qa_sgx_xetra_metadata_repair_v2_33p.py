#!/usr/bin/env python3
"""Offline QA for the SGX and Xetra metadata repair scripts (v2.33P).
SGX repair is pure local logic (no network to mock). Xetra repair's
OpenFIGI calls are mocked entirely -- no real network, no credentials
needed for either provider.
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


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def test_sgx_repair_row_logic():
    mod = module("repair_sgx_schema_v2_33p")
    good = {"ticker": "0.845", "company_name": "LVR", "missing_company_name": "False",
            "eligibility_decision_v2_33b2": "hold_provider_schema_sgx", "eligibility_reason_v2_33b2": "x"}
    repaired, reason = mod.repair_row(good)
    assert reason == "repaired"
    assert repaired["ticker"] == "LVR"
    assert repaired["company_name"] == ""
    assert repaired["missing_company_name"] == "True"

    bad_ticker = {"ticker": "ABC", "company_name": "LVR", "missing_company_name": "False",
                  "eligibility_decision_v2_33b2": "x", "eligibility_reason_v2_33b2": "x"}
    repaired2, reason2 = mod.repair_row(bad_ticker)
    assert repaired2 is None and reason2 == "ticker_field_not_a_plain_decimal_price_pattern_mismatch"

    bad_name = {"ticker": "0.845", "company_name": "Not A Ticker Name", "missing_company_name": "False",
                "eligibility_decision_v2_33b2": "x", "eligibility_reason_v2_33b2": "x"}
    repaired3, reason3 = mod.repair_row(bad_name)
    assert repaired3 is None and reason3 == "company_name_field_not_ticker_like_pattern_mismatch"


def extract_last_json(out: str) -> dict:
    text = out.split("PASS:")[0] if "PASS:" in out else out
    start = text.rindex("\n{\n") + 1 if "\n{\n" in text else text.index("{")
    return json.loads(text[start:])


def fake_mapping_response(entries_by_isin: dict[str, list[dict]], isins_in_batch: list[str]):
    payload = [{"data": entries_by_isin.get(isin, [])} if entries_by_isin.get(isin) is not None else {"warning": "No identifier found."} for isin in isins_in_batch]
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def test_xetra_blocked_without_execute():
    mod = module("repair_xetra_schema_v2_33p")
    code, out = run(mod, [])
    assert code == 2 and "BLOCKED" in out and "--execute" in out


def test_xetra_resolves_exact_agreement_and_blocks_disagreement():
    mod = module("repair_xetra_schema_v2_33p")

    base = {"row_number": "0", "isin": "", "ticker": "", "company_name": "", "missing_company_name": "True",
            "eligibility_decision_v2_33b2": "hold_provider_schema_xetra", "eligibility_reason_v2_33b2": "xetra_company_name_field_contains_classification_codes"}
    fake_rows = [
        {**base, "row_number": "1", "isin": "AT0000743059", "ticker": "OMV", "company_name": "AST0"},
        {**base, "row_number": "2", "isin": "DE0000000002", "ticker": "XYZ", "company_name": "GER0"},
        {**base, "row_number": "3", "isin": "DE0000000003", "ticker": "NOM", "company_name": "GER0"},
    ]
    with mock.patch.object(mod, "load_census", return_value=fake_rows):
        def side_effect(request, timeout=30):
            return fake_mapping_response(
                {
                    "AT0000743059": [{"name": "OMV AG"}, {"name": "OMV AG"}],
                    "DE0000000002": [{"name": "COMPANY A"}, {"name": "COMPANY B"}],  # disagreement
                    "DE0000000003": [],  # no record
                },
                ["AT0000743059", "DE0000000002", "DE0000000003"],
            )

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"), \
                 mock.patch.object(mod, "OUT_DIR", Path(tmp)):
                code, out = run(mod, ["--execute", "--write"])
        report = extract_last_json(out)
        assert report["held_rows"] == 3
        assert report["repaired"] == 1 and report["unresolved"] == 2
        assert report["unresolved_reasons"]["disagreeing_names_across_openfigi_records"] == 1
        assert report["unresolved_reasons"]["no_openfigi_record_for_isin"] == 1
        assert code == 1  # non-empty unresolved is expected, not an error


CASES = [
    test_sgx_repair_row_logic,
    test_xetra_blocked_without_execute,
    test_xetra_resolves_exact_agreement_and_blocks_disagreement,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.33P-metadata-repair/sgx-column-unshift/xetra-isin-exact-match/fail-closed/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
