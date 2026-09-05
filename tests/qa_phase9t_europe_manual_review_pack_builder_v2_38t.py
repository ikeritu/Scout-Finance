#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_manual_review_pack_v2_38t.py"


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    fields = [
        "asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country",
        "home_currency", "source_type", "primary_fundamental_route", "secondary_fundamental_route",
        "fundamental_route_status", "expected_identifier", "provider_symbol_candidate",
        "filing_registry_candidate", "route_confidence", "blocker_reason", "phase", "network_calls",
        "fundamentals_downloaded", "fundamentals_normalized", "scoring_calculated",
        "ranking_calculated", "recommendations_generated", "phase9c_authorized",
    ]
    base = {
        "home_currency": "EUR", "secondary_fundamental_route": "provider_api_required",
        "provider_symbol_candidate": "", "route_confidence": "LOW", "blocker_reason": "",
        "phase": "v2.38Q-europe-fundamentals-route-foundation", "network_calls": "0",
        "fundamentals_downloaded": "false", "fundamentals_normalized": "false",
        "scoring_calculated": "false", "ranking_calculated": "false",
        "recommendations_generated": "false", "phase9c_authorized": "false",
    }
    rows = [
        dict(base, asset_id="U40001", ticker="AAA", company_name="UKI0", home_exchange="Euronext Dublin", home_mic="XDUB", home_country="IE", source_type="manual_review", primary_fundamental_route="issuer_filings_manual_review", fundamental_route_status="FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED", expected_identifier="UNKNOWN_REVIEW", filing_registry_candidate=""),
        dict(base, asset_id="U40002", ticker="BBB", company_name="UKI0", home_exchange="Euronext Dublin", home_mic="XDUB", home_country="IE", source_type="manual_review", primary_fundamental_route="issuer_filings_manual_review", fundamental_route_status="FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED", expected_identifier="UNKNOWN_REVIEW", filing_registry_candidate=""),
        dict(base, asset_id="U40003", ticker="CCC", company_name="CCC Plc", home_exchange="London Stock Exchange", home_mic="XLON", home_country="GB", source_type="official_filing_registry", primary_fundamental_route="uk_companies_house_filings", fundamental_route_status="FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW", expected_identifier="COMPANY_REGISTRY_ID", route_confidence="MEDIUM", filing_registry_candidate="uk_companies_house_filings:CCC"),
        dict(base, asset_id="U40004", ticker="DDD", company_name="DDD AG", home_exchange="XETRA", home_mic="XETR", home_country="DE", source_type="provider_api", primary_fundamental_route="eodhd_fundamentals", fundamental_route_status="FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT", expected_identifier="PROVIDER_SYMBOL", route_confidence="HIGH", filing_registry_candidate=""),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        routes = root / "routes.csv"
        q_summary = root / "q.json"
        out = root / "out"
        write_csv(routes, rows, fields)
        q_summary.write_text(json.dumps({"input_assets": 10, "routed_assets": 4}) + "\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-routes", str(routes), "--input-route-summary", str(q_summary), "--output-dir", str(out)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        matrix = read_rows(out / "europe_manual_review_pack_matrix_v2_38t.csv")
        checklist = read_rows(out / "europe_manual_review_pack_checklist_v2_38t.csv")
        exclusions = read_rows(out / "europe_manual_review_pack_exclusions_v2_38t.csv")
        assert len(matrix) == 2
        assert len(checklist) == 6  # 2 assets x 3 required actions
        assert len(exclusions) == 2
        assert all(row["identity_verified"] == "false" for row in matrix)
        assert all(row["company_name_source_value"] == "UKI0" for row in matrix)
        assert all("known upstream placeholder pattern" in row["notes"] for row in matrix)
        by_reason = {row["asset_id"]: row["exclusion_reason"] for row in exclusions}
        assert by_reason["U40003"] == "official_filings_review_not_manual_review"
        assert by_reason["U40004"] == "provider_pilot_not_manual_review"
        assert {row["action_status"] for row in checklist} == {"PENDING_HUMAN_ACTION"}
    print("PASS: v2.38T/builder/offline/manual-review-filter-and-checklist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
