#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_official_filings_review_v2_38s.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38s_europe_official_filings_review"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]", re.I)
ACTION_RE = re.compile(r"\b(buy|sell|hold|strong buy|recommendation|target price|undervalued|overvalued|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def non_identity_text(row: dict[str, str]) -> str:
    identity = {"asset_id", "ticker", "company_name", "exchange", "mic", "country", "currency", "isin", "source_row_hash"}
    return " ".join(value for key, value in row.items() if key not in identity)


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    matrix = rows(OUT / "europe_official_filings_review_matrix_v2_38s.csv")
    jurisdiction_plan = rows(OUT / "europe_official_filings_jurisdiction_plan_v2_38s.csv")
    identifiers = rows(OUT / "europe_official_filings_identifier_requirements_v2_38s.csv")
    exclusions = rows(OUT / "europe_official_filings_review_exclusions_v2_38s.csv")
    summary = json.loads((OUT / "europe_official_filings_review_summary_v2_38s.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "europe_official_filings_review_manifest_v2_38s.json").read_text(encoding="utf-8"))
    assert len(matrix) == 55
    assert len(identifiers) == 55
    assert len(exclusions) == 634
    assert summary["official_filings_review_assets_expected"] == 55
    assert summary["official_filings_review_assets_actual"] == 55
    assert summary["provider_pilot_assets_excluded"] == 617
    assert summary["manual_review_assets_excluded"] == 17
    assert summary["jurisdiction_counts"] == {"ES": 15, "GB": 40}
    assert summary["identifier_resolution_required_assets"] == 55
    assert summary["ready_for_future_official_execution_assets"] == 0
    for key in ["network_used", "scraping_used", "api_used", "real_filings_downloaded", "real_fundamentals_present", "normalized_fundamentals_created", "scoring_created", "ranking_created", "recommendations_created", "phase9c_authorized"]:
        assert summary[key] is False
    assert {row["route_from_38q"] for row in matrix} == {"FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW"}
    assert {row["jurisdiction_code"] for row in matrix} == {"ES", "GB"}
    assert {row["filing_identifier_present"] for row in matrix} == {"false"}
    assert {row["filing_identifier_value"] for row in matrix} == {""}
    assert {row["identifier_confidence"] for row in matrix} == {"NONE"}
    assert {row["resolution_status"] for row in identifiers} == {"IDENTIFIER_RESOLUTION_REQUIRED"}
    assert {row["can_execute_official_collection_now"] for row in identifiers} == {"false"}
    assert all(row["network_allowed"] == "false" and row["scraping_allowed"] == "false" and row["api_allowed"] == "false" for row in jurisdiction_plan + exclusions)
    assert all(row["fundamental_route_status"] != "FUNDAMENTALS_ROUTE_READY_FOR_OFFICIAL_FILINGS_REVIEW" for row in exclusions)
    for row in matrix + jurisdiction_plan + identifiers + exclusions:
        assert "CBOE" not in row.get("mic", "").upper()
        assert not ACTION_RE.search(non_identity_text(row)), row.get("asset_id", row.get("jurisdiction_code", ""))
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path
    print("PASS: v2.38S/quality/official-review/no-identifiers-invented/no-network-no-advice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
