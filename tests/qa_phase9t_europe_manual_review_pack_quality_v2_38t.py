#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_manual_review_pack_v2_38t.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38t_europe_manual_review_pack"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]", re.I)
ACTION_RE = re.compile(r"\b(buy|sell|hold|strong buy|recommendation|target price|undervalued|overvalued|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def non_identity_text(row: dict[str, str]) -> str:
    identity = {"asset_id", "ticker", "company_name_source_value", "home_exchange", "home_mic", "home_country", "home_currency", "source_row_hash"}
    return " ".join(value for key, value in row.items() if key not in identity)


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    matrix = rows(OUT / "europe_manual_review_pack_matrix_v2_38t.csv")
    checklist = rows(OUT / "europe_manual_review_pack_checklist_v2_38t.csv")
    exclusions = rows(OUT / "europe_manual_review_pack_exclusions_v2_38t.csv")
    summary = json.loads((OUT / "europe_manual_review_pack_summary_v2_38t.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "europe_manual_review_pack_manifest_v2_38t.json").read_text(encoding="utf-8"))

    assert len(matrix) == 17
    assert len(checklist) == 51
    assert len(exclusions) == 672
    assert summary["manual_review_pack_assets_expected"] == 17
    assert summary["manual_review_pack_assets_actual"] == 17
    assert summary["provider_pilot_assets_excluded"] == 617
    assert summary["official_filings_review_assets_excluded"] == 55
    assert summary["total_excluded_assets"] == 672
    assert summary["assets_with_placeholder_identity"] == 17
    assert summary["checklist_actions_total"] == 51
    assert summary["ready_for_future_manual_review_execution_assets"] == 0
    for key in ["network_used", "scraping_used", "api_used", "real_filings_downloaded", "real_fundamentals_present", "normalized_fundamentals_created", "scoring_created", "ranking_created", "recommendations_created", "phase9c_authorized"]:
        assert summary[key] is False

    assert {row["route_from_38q"] for row in matrix} == {"FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED"}
    assert {row["home_mic"] for row in matrix} == {"XDUB"}
    assert {row["home_country"] for row in matrix} == {"IE"}
    assert {row["identity_verified"] for row in matrix} == {"false"}
    assert {row["company_name_source_value"] for row in matrix} == {"UKI0"}
    assert all("placeholder pattern" in row["notes"] for row in matrix)
    assert {row["action_status"] for row in checklist} == {"PENDING_HUMAN_ACTION"}
    assert {row["action_sequence"] for row in checklist} == {"1", "2", "3"}
    assert all(row["fundamental_route_status"] != "FUNDAMENTALS_ROUTE_MANUAL_REVIEW_REQUIRED" for row in exclusions)
    assert all(row["network_allowed"] == "false" and row["scraping_allowed"] == "false" and row["api_allowed"] == "false" for row in checklist + exclusions)

    for row in matrix + checklist + exclusions:
        assert "CBOE" not in row.get("home_mic", row.get("mic", "")).upper()
        assert not ACTION_RE.search(non_identity_text(row)), row.get("asset_id", "")
    for artifact in manifest["outputs"].values():
        assert artifact["bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path
    print("PASS: v2.38T/quality/manual-review/identity-not-invented/no-network-no-advice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
