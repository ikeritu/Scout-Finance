#!/usr/bin/env python3
"""Offline QA for the two block-D acquisition adapters (J-Quants
fins/summary, TWSE MOPS opendata). No network calls: urlopen is mocked via
unittest.mock; the J-Quants "key" used is a throwaway fixture string, never
the real SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN value. time.sleep is patched
out so backoff/delay paths run instantly.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
JQUANTS_SCRIPT = ROOT / "scripts/download_jquants_fundamentals_v2_34d.py"
TWSE_SCRIPT = ROOT / "scripts/download_twse_mops_fundamentals_v2_34d.py"
API_KEY_ENV = "SCOUT_FINANCE_JQUANTS_REFRESH_TOKEN"
FIXTURE_KEY = "test-fixture-key-not-real"

MANIFEST_FIELDS = ["asset_id", "pilot_id", "ticker", "provider_symbol_jquants", "provider_symbol_twse", "company_name", "exchange"]


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_manifest(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in MANIFEST_FIELDS})


def jpx_row(pilot_id: str, code: str) -> dict:
    return {"asset_id": pilot_id, "pilot_id": pilot_id, "ticker": code, "provider_symbol_jquants": f"{code}0", "exchange": "JPX"}


def twse_row(pilot_id: str, code: str) -> dict:
    return {"asset_id": pilot_id, "pilot_id": pilot_id, "ticker": f"{code}.TW", "provider_symbol_twse": f"{code}.TW", "exchange": "TWSE"}


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


def http_error(code: int, body: str = "{}"):
    return urllib.error.HTTPError("https://api.jquants.com/v2/fins/summary", code, "err", hdrs=None, fp=io.BytesIO(body.encode()))


def fake_response(body_bytes: bytes):
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = body_bytes
    cm.__exit__.return_value = False
    return cm


def last_json(out: str) -> dict:
    return json.loads(out.strip().splitlines()[-1])


# --- J-Quants adapter ---

def test_jquants_blocked_without_execute_then_without_key():
    mod = module(JQUANTS_SCRIPT, "dl_jquants_fund_v2_34d_1")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [jpx_row("P001", "1301")] * 1)

        code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(tmp_path / "out")], {API_KEY_ENV: FIXTURE_KEY})
        assert code == 2 and "BLOCKED" in out and "--execute" in out

        code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(tmp_path / "out"), "--execute"], {})
        assert code == 2 and "BLOCKED" in out and API_KEY_ENV in out


def test_jquants_resumability_atomic_write_and_no_key_leak():
    mod = module(JQUANTS_SCRIPT, "dl_jquants_fund_v2_34d_2")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        (out_dir / "P001.json").write_text(json.dumps({"asset": {"pilot_id": "P001"}, "disclosures": []}), encoding="utf-8")

        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [jpx_row("P001", "1301"), jpx_row("P002", "1802")])

        payload = {"data": [{"Code": "18020", "Sales": "1000"}]}
        with mock.patch("urllib.request.urlopen") as urlopen, mock.patch("time.sleep"):
            urlopen.return_value = fake_response(json.dumps(payload).encode("utf-8"))
            code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute"], {API_KEY_ENV: FIXTURE_KEY})
        report = last_json(out)
        assert code == 0 and report["collected"] == 1 and report["skipped_existing"] == 1
        assert not list(out_dir.glob("*.json.tmp"))
        raw = json.dumps(report)
        assert FIXTURE_KEY not in raw and "https://" not in raw
        # only one real network call was made (P001 skipped as already collected)
        assert urlopen.call_count == 1


def test_jquants_continues_after_http_error_and_reports_taxonomy_code():
    mod = module(JQUANTS_SCRIPT, "dl_jquants_fund_v2_34d_3")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [jpx_row("P001", "1301"), jpx_row("P002", "1802")])

        def side_effect(request, timeout=30):
            if "13010" in request.full_url:
                raise http_error(500)
            return fake_response(json.dumps({"data": [{"Code": "18020", "Sales": "1000"}]}).encode("utf-8"))

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute"], {API_KEY_ENV: FIXTURE_KEY})
        report = last_json(out)
        assert code == 1 and report["collected"] == 1 and report["failed"] == 1
        failure = report["failures"][0]
        assert failure["pilot_id"] == "P001" and failure["error_type"] == "HTTP_ERROR" and failure["http_status"] == 500


def test_jquants_identity_mismatch_and_empty_response_are_classified():
    mod = module(JQUANTS_SCRIPT, "dl_jquants_fund_v2_34d_4")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [jpx_row("P001", "1301"), jpx_row("P002", "1802")])

        def side_effect(request, timeout=30):
            if "13010" in request.full_url:
                return fake_response(json.dumps({"data": [{"Code": "99999", "Sales": "1000"}]}).encode("utf-8"))
            return fake_response(json.dumps({"data": []}).encode("utf-8"))

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute"], {API_KEY_ENV: FIXTURE_KEY})
        report = last_json(out)
        by_id = {f["pilot_id"]: f for f in report["failures"]}
        assert by_id["P001"]["error_type"] == "IDENTITY_MISMATCH"
        assert by_id["P002"]["error_type"] == "EMPTY_RESPONSE"


def test_jquants_limit_and_asset_id_filters():
    mod = module(JQUANTS_SCRIPT, "dl_jquants_fund_v2_34d_5")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [jpx_row("P001", "1301"), jpx_row("P002", "1802"), jpx_row("P003", "1994")])

        with mock.patch("urllib.request.urlopen") as urlopen, mock.patch("time.sleep"):
            urlopen.return_value = fake_response(json.dumps({"data": [{"Code": "13010", "Sales": "1"}]}).encode("utf-8"))
            code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute", "--asset-id", "P001"], {API_KEY_ENV: FIXTURE_KEY})
        report = last_json(out)
        assert code == 0 and report["input_assets"] == 1 and report["collected"] == 1
        assert list(out_dir.glob("P*.json")) == [out_dir / "P001.json"]


# --- TWSE MOPS adapter ---

MOPS_HEADER_MAP = {
    "company_info": "出表日期,公司代號,公司名稱\n",
    "income_statement": "出表日期,年度,季別,公司代號,公司名稱,營業收入\n",
    "balance_sheet": "出表日期,年度,季別,公司代號,公司名稱,資產總計\n",
    "profitability_ratios": "出表日期,年度,季別,公司代號,公司名稱,毛利率\n",
}


def mops_csv_bytes(kind: str, rows: list[str]) -> bytes:
    body = MOPS_HEADER_MAP[kind] + "".join(r + "\n" for r in rows)
    return body.encode("utf-8-sig")


def test_twse_blocked_without_execute():
    mod = module(TWSE_SCRIPT, "dl_twse_mops_fund_v2_34d_1")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [twse_row("P016", "1101")])
        code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(tmp_path / "out")], {})
        assert code == 2 and "BLOCKED" in out and "--execute" in out


def test_twse_download_extraction_atomic_and_no_url_leak():
    mod = module(TWSE_SCRIPT, "dl_twse_mops_fund_v2_34d_2")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [twse_row("P016", "1101"), twse_row("P017", "1525")])

        responses = {
            "t187ap03_L": mops_csv_bytes("company_info", ["1150831,1101,Taiwan Cement", "1150831,1525,Other Co"]),
            "t187ap06_L_ci": mops_csv_bytes("income_statement", ["1150901,115,2,1101,Taiwan Cement,71289957.00", "1150901,115,2,1525,Other Co,1000.00"]),
            "t187ap07_L_ci": mops_csv_bytes("balance_sheet", ["1150901,115,2,1101,Taiwan Cement,596016531.00", "1150901,115,2,1525,Other Co,2000.00"]),
            "t187ap17_L": mops_csv_bytes("profitability_ratios", ["1150901,115,2,1101,Taiwan Cement,18.22", "1150901,115,2,1525,Other Co,5.0"]),
        }

        def side_effect(request, timeout=60, context=None):
            for code, body in responses.items():
                if code in request.full_url:
                    return fake_response(body)
            raise AssertionError(f"unexpected URL {request.full_url}")

        with mock.patch("urllib.request.urlopen", side_effect=side_effect), mock.patch("time.sleep"):
            code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute"], {})
        report = last_json(out)
        assert code == 0 and report["extracted"] == 2 and report["failed"] == 0
        assert not list(out_dir.glob("**/*.json.tmp"))
        p016 = json.loads((out_dir / "P016.json").read_text(encoding="utf-8"))
        assert p016["snapshot_files"]["income_statement"][0]["公司代號"] == "1101"
        raw = json.dumps(report)
        assert "https://" not in raw


def test_twse_raw_snapshot_cache_avoids_refetch_on_second_run():
    mod = module(TWSE_SCRIPT, "dl_twse_mops_fund_v2_34d_3")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [twse_row("P016", "1101")])

        responses = {
            "t187ap03_L": mops_csv_bytes("company_info", ["1150831,1101,Taiwan Cement"]),
            "t187ap06_L_ci": mops_csv_bytes("income_statement", ["1150901,115,2,1101,Taiwan Cement,71289957.00"]),
            "t187ap07_L_ci": mops_csv_bytes("balance_sheet", ["1150901,115,2,1101,Taiwan Cement,596016531.00"]),
            "t187ap17_L": mops_csv_bytes("profitability_ratios", ["1150901,115,2,1101,Taiwan Cement,18.22"]),
        }

        def side_effect(request, timeout=60, context=None):
            for code, body in responses.items():
                if code in request.full_url:
                    return fake_response(body)
            raise AssertionError(f"unexpected URL {request.full_url}")

        with mock.patch("urllib.request.urlopen", side_effect=side_effect) as urlopen, mock.patch("time.sleep"):
            run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute"], {})
            first_calls = urlopen.call_count
            (out_dir / "P016.json").unlink()  # force re-extraction, but raw snapshots should already be cached
            code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute"], {})
        assert urlopen.call_count == first_calls  # no new network calls on the second run
        report = last_json(out)
        assert code == 0 and report["extracted"] == 1


def test_twse_schema_mismatch_blocks_with_no_partial_extraction():
    mod = module(TWSE_SCRIPT, "dl_twse_mops_fund_v2_34d_4")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        out_dir = tmp_path / "out"
        manifest = tmp_path / "manifest.csv"
        write_manifest(manifest, [twse_row("P016", "1101")])

        bad_csv = "wrong_column,other\nx,y\n".encode("utf-8-sig")

        with mock.patch("urllib.request.urlopen") as urlopen, mock.patch("time.sleep"):
            urlopen.return_value = fake_response(bad_csv)
            code, out = run(mod, ["--manifest", str(manifest), "--output-dir", str(out_dir), "--execute"], {})
        report = last_json(out)
        assert code == 1 and report["status"] == "BLOCKED_DOWNLOAD_FAILED"
        assert report["download_failures"][0]["error_type"] == "SCHEMA_MISMATCH"
        assert not list(out_dir.glob("P*.json"))


CASES = [
    test_jquants_blocked_without_execute_then_without_key,
    test_jquants_resumability_atomic_write_and_no_key_leak,
    test_jquants_continues_after_http_error_and_reports_taxonomy_code,
    test_jquants_identity_mismatch_and_empty_response_are_classified,
    test_jquants_limit_and_asset_id_filters,
    test_twse_blocked_without_execute,
    test_twse_download_extraction_atomic_and_no_url_leak,
    test_twse_raw_snapshot_cache_avoids_refetch_on_second_run,
    test_twse_schema_mismatch_blocks_with_no_partial_extraction,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.34D-fundamentals-acquisition/fail-closed/resumable/atomic-write/error-taxonomy/no-network/no-real-key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
