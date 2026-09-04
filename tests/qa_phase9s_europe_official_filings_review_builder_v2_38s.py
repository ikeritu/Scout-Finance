#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_official_filings_review_v2_38s.py"


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
        "provider_symbol_candidate": "", "route_confidence": "MEDIUM", "blocker_reason": "",
        "phase": "v2.38Q-europe-fundamentals-route-foundation", "network_calls": "0",
        "fundamentals_downloaded": "false", "fundamentals_normalized": "false",
        "scoring_calculated": "false", "ranking_calculated": "false",
        "recommendations_generated": "false", "phase9c_authorized": "false",
    }
    rows = [
        dict(base, asset_id="U39001", ticker="AAA", company_name="AAA SA", home_exchange="BME", home_mic="XMAD", home_country="ES", source_type="official_filing_registry", primary_fundamental_route="cnmv_issuer_filings", fundamental_route_status="FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW", expected_identifier="ISIN", filing_registry_candidate="cnmv_issuer_filings:AAA"),
        dict(base, asset_id="U39002", ticker="BBB", company_name="BBB Plc", home_exchange="London Stock Exchange", home_mic="XLON", home_country="GB", source_type="official_filing_registry", primary_fundamental_route="uk_companies_house_filings", fundamental_route_status="FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW", expected_identifier="COMPANY_REGISTRY_ID", filing_registry_candidate="uk_companies_house_filings:BBB"),
        dict(base, asset_id="U39003", ticker="CCC", company_name="CCC AG", home_exchange="XETRA", home_mic="XETR", home_country="DE", source_type="provider_api", primary_fundamental_route="eodhd_fundamentals", fundamental_route_status="FUNDAMENTALS_ROUTE_READY_FOR_PROVIDER_PILOT", expected_identifier="PROVIDER_SYMBOL", filing_registry_candidate=""),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        routes = root / "routes.csv"
        q_summary = root / "q.json"
        r_summary = root / "r.json"
        r_exclusions = root / "rx.csv"
        out = root / "out"
        write_csv(routes, rows, fields)
        q_summary.write_text(json.dumps({"input_assets": 10, "routed_assets": 3}) + "\n", encoding="utf-8")
        r_summary.write_text(json.dumps({"provider_pilot_assets_actual": 1}) + "\n", encoding="utf-8")
        write_csv(r_exclusions, rows[:2], fields)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input-routes", str(routes), "--input-route-summary", str(q_summary), "--input-provider-summary", str(r_summary), "--input-provider-exclusions", str(r_exclusions), "--output-dir", str(out)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        matrix = read_rows(out / "europe_official_filings_review_matrix_v2_38s.csv")
        exclusions = read_rows(out / "europe_official_filings_review_exclusions_v2_38s.csv")
        identifiers = read_rows(out / "europe_official_filings_identifier_requirements_v2_38s.csv")
        assert len(matrix) == 2
        assert len(exclusions) == 1
        assert len(identifiers) == 2
        assert {row["jurisdiction_code"] for row in matrix} == {"ES", "GB"}
        assert all(row["filing_identifier_present"] == "false" for row in matrix)
        assert all(row["filing_identifier_value"] == "" for row in matrix)
        assert exclusions[0]["exclusion_reason"] == "provider_pilot_not_official_review"
    print("PASS: v2.38S/builder/offline/official-review-filter-and-identifiers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
