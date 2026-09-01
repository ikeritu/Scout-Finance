#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/resolve_jpx_global_symbols_v2_38b.py"
SPEC = importlib.util.spec_from_file_location("resolver", SCRIPT)
resolver = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(resolver)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    row = {"asset_id": "U00002", "ticker": "1332", "company_name": "Nissui Corporation", "exchange": "JPX"}
    resolved, reason = resolver.exact_resolution(row, [{"Date": "2026-01-01", "CoNameEn": "Nissui Corporation", "Code": "13320"}])
    assert reason == "resolved" and resolved["provider_symbol"] == "13320"
    assert resolver.exact_resolution(row, [{"Date": "2026-01-01", "CoNameEn": "Other", "Code": "13320"}])[1] == "company_name_mismatch"
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp); source = base / "source.csv"; known = base / "known.csv"; overlay = base / "overlay.csv"; review = base / "review.csv"; runtime = base / "runtime"
        source_rows = [
            {"asset_id": "U00001", "ticker": "1301", "company_name": "Known", "exchange": "JPX", "eligibility_status": "ELIGIBLE", "identity_status": "COMPLETE"},
            {"asset_id": "U00002", "ticker": "1332", "company_name": "Nissui Corporation", "exchange": "JPX", "eligibility_status": "ELIGIBLE", "identity_status": "COMPLETE"},
            {"asset_id": "U00003", "ticker": "1333", "company_name": "Maruha", "exchange": "JPX", "eligibility_status": "ELIGIBLE", "identity_status": "COMPLETE"},
            {"asset_id": "U00004", "ticker": "1352", "company_name": "Pending", "exchange": "JPX", "eligibility_status": "ELIGIBLE", "identity_status": "COMPLETE"},
        ]
        write_csv(source, source_rows)
        write_csv(known, [{"ticker": "1301", "status": "resolved_prior", "provider_symbol": "13010"}])
        write_csv(overlay, [{"asset_id": "U00002", "ticker": "1332", "exchange": "JPX", "provider_symbol": "13320", "resolution_status": "EXACT_COMPANY_NAME_MATCH", "evidence_source": "J-Quants equities master"}])
        write_csv(review, [{"asset_id": "U00003", "ticker": "1333", "exchange": "JPX", "review_status": "MANUAL_REVIEW_REQUIRED", "reason": "company_name_mismatch", "evidence_source": "J-Quants equities master"}])
        command = [sys.executable, str(SCRIPT), "--limit", "5", "--source", str(source), "--known", str(known), "--overlay", str(overlay), "--review", str(review), "--runtime", str(runtime)]
        dry = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        payload = json.loads(dry.stdout)
        assert dry.returncode == 0
        assert payload["status"] == "DRY_RUN"
        assert payload["asset_ids"] == ["U00004"]
        assert payload["manual_review"] == 1
        assert payload["remaining_actionable"] == 1
        clean_env = {key: value for key, value in os.environ.items() if key != resolver.TOKEN_ENV}
        blocked = subprocess.run([*command, "--execute"], cwd=ROOT, text=True, capture_output=True, env=clean_env)
        assert blocked.returncode == 2 and json.loads(blocked.stdout)["reason"] == "credential_missing"
        oversized = subprocess.run([sys.executable, str(SCRIPT), "--limit", "501"], cwd=ROOT, text=True, capture_output=True)
        assert oversized.returncode == 2
        try:
            resolver.write_overlay(overlay, [resolved, resolved])
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate overlay was accepted")
    print("PASS: v2.38B JPX-global-resolver/dry-run/resume/exact-match/manual-review/no-retry/credential-gate/atomic-overlay/max500/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
