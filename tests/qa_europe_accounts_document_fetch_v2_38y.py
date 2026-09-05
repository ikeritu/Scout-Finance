#!/usr/bin/env python3
"""Offline QA for the v2.38Y accounts document fetch runner (full
40-company expansion). No real network calls, no real credential --
FIXTURE_KEY is a throwaway string.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fetch_europe_accounts_documents_v2_38y.py"
CREDENTIAL_ENV = "SCOUT_FINANCE_COMPANIES_HOUSE_API_KEY"
FIXTURE_KEY = "test-fixture-key-not-real"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_lookup_matrix(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["asset_id", "ticker", "resolved_company_name", "company_number", "lookup_status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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


def fake_json_response(payload: dict):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    cm.__exit__.return_value = False
    return cm


def build_zip_bytes(inner_name: str, content: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(inner_name, content)
    return buf.getvalue()


def test_dry_run_reports_resolved_assets_without_network():
    mod = module("fetch_y_1")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [{"asset_id": "U1", "ticker": "DGE", "resolved_company_name": "DIAGEO PLC", "company_number": "00023307", "lookup_status": "resolved"}])
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out")], {})
        assert code == 0 and urlopen.call_count == 0
        assert json.loads(out)["status"] == "DRY_RUN" and json.loads(out)["eligible_assets"] == 1


def test_execute_without_credential_is_blocked():
    mod = module("fetch_y_2")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [{"asset_id": "U1", "ticker": "DGE", "resolved_company_name": "DIAGEO PLC", "company_number": "00023307", "lookup_status": "resolved"}])
        code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--execute"], {})
        assert code == 2 and json.loads(out)["reason"] == "credential_missing"


def test_pdf_only_is_blocked_zip_is_fetched_and_extracted_across_many_rows():
    """Same PDF-vs-ZIP classification as v2.38W, exercised with more rows
    (mixed PDF-only / ZIP / a hard HTTP error) to confirm the run continues
    past individual failures at the larger 40-company scale."""
    mod = module("fetch_y_3")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        matrix = root / "matrix.csv"
        write_lookup_matrix(matrix, [
            {"asset_id": "U1", "ticker": "PDF", "resolved_company_name": "PDF ONLY PLC", "company_number": "111", "lookup_status": "resolved"},
            {"asset_id": "U2", "ticker": "ZIP", "resolved_company_name": "ZIP CO PLC", "company_number": "222", "lookup_status": "resolved"},
            {"asset_id": "U3", "ticker": "ERR", "resolved_company_name": "ERROR CO PLC", "company_number": "333", "lookup_status": "resolved"},
        ])
        zip_bytes = build_zip_bytes("report/report.xhtml", b"<html>fake ixbrl</html>")

        import urllib.error

        def side_effect(request, timeout=30):
            url = request.full_url
            if "filing-history" in url:
                if "333" in url:
                    raise urllib.error.HTTPError(url, 500, "err", hdrs=None, fp=io.BytesIO(b"{}"))
                number = "111" if "111" in url else "222"
                doc_id = "doc-pdf" if number == "111" else "doc-zip"
                return fake_json_response({"items": [{"date": "2026-01-01", "type": "AA", "links": {"document_metadata": f"https://document-api.example/document/{doc_id}"}}]})
            if "doc-pdf" in url:
                return fake_json_response({"resources": {"application/pdf": {"content_length": 100}}})
            if "doc-zip" in url:
                return fake_json_response({"resources": {"application/zip": {"content_length": 100}}})
            raise AssertionError(f"unexpected URL {url}")

        def opener_open(self, req, timeout=30):
            if "content" in req.full_url:
                raise urllib.error.HTTPError(req.full_url, 302, "redirect", hdrs={"Location": "https://s3.example/fake.zip"}, fp=None)
            raise AssertionError("unexpected opener call")

        s3_response = mock.MagicMock()
        s3_response.__enter__.return_value.read.return_value = zip_bytes
        s3_response.__exit__.return_value = False

        def urlopen_side_effect(request_or_url, timeout=30):
            if isinstance(request_or_url, str) and "s3.example" in request_or_url:
                return s3_response
            return side_effect(request_or_url, timeout)

        with mock.patch("urllib.request.urlopen", side_effect=urlopen_side_effect), mock.patch.object(mod.NoRedirect, "redirect_request", return_value=None), mock.patch("urllib.request.OpenerDirector.open", opener_open), mock.patch("time.sleep"):
            code, out = run(mod, ["--input-matrix", str(matrix), "--output-dir", str(root / "out"), "--raw-cache", str(root / "raw"), "--execute"], {CREDENTIAL_ENV: FIXTURE_KEY})

        report = json.loads(out.strip().splitlines()[-1])
        assert report["fetched"] == 1 and report["blocked_or_error"] == 2
        rows = list(csv.DictReader((root / "out" / "europe_accounts_document_fetch_matrix_v2_38y.csv").open(encoding="utf-8")))
        by_ticker = {r["ticker"]: r for r in rows}
        assert by_ticker["PDF"]["fetch_status"] == "blocked" and by_ticker["PDF"]["fetch_reason"] == "accounts_format_not_parseable_pdf_only"
        assert by_ticker["ZIP"]["fetch_status"] == "fetched"
        assert by_ticker["ERR"]["fetch_status"] == "error" and "filing_history_call_failed" in by_ticker["ERR"]["fetch_reason"]
        assert not list((root / "out").glob("*.tmp"))
        raw = json.dumps(report)
        assert FIXTURE_KEY not in raw


CASES = [
    test_dry_run_reports_resolved_assets_without_network,
    test_execute_without_credential_is_blocked,
    test_pdf_only_is_blocked_zip_is_fetched_and_extracted_across_many_rows,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38Y-accounts-document-fetch/dry-run-gate/pdf-vs-zip-classification/continues-past-errors/no-credential-leak")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
