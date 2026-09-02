#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38e_us_sec_enrichment_expansion"
BUILDER = ROOT / "scripts/build_us_sec_enrichment_expansion_v2_38e.py"
OVERLAY = ROOT / "outputs/full_universe_source_acquisition/v2_38d_us_sec_foundation/us_sec_identity_overlay_v2_38d.csv"
ALLOWED = {
    "ENRICHED_SEC_READY",
    "ENRICHED_PARTIAL_COMPANYFACTS_ONLY",
    "ENRICHED_PARTIAL_SUBMISSIONS_ONLY",
    "SEC_CIK_RESOLVED_PENDING_COLLECTION",
    "SEC_CIK_REVIEW_REQUIRED",
    "SEC_NOT_ELIGIBLE",
    "SEC_COLLECTION_FAILED",
    "SEC_SOURCE_UNAVAILABLE",
}
SECRET_RE = re.compile(r"api[_-]?key\\s*[:=]|refresh[_-]?token\\s*[:=]|bearer\\s+[a-z0-9]|authorization\\s*[:=]|SCOUT_FINANCE_SEC_USER_AGENT\\s*=", re.I)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def first_resolved() -> dict[str, str]:
    for row in read_rows(OVERLAY):
        if row["identity_status"] == "US_SEC_CIK_RESOLVED" and row["cik"]:
            return row
    return {}


def assert_no_secrets() -> None:
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True, capture_output=True, text=True)
    rows = read_rows(OUT / "us_sec_enrichment_readiness_v2_38e.csv")
    assert len(rows) == 9200 == len({r["asset_id"] for r in rows})
    assert {r["enrichment_status"] for r in rows} <= ALLOWED
    assert all(len(r["evidence_hash"]) == 64 for r in rows)
    report = json.loads((OUT / "us_sec_enrichment_aggregate_report_v2_38e.json").read_text(encoding="utf-8"))
    assert report["status"] in {"PARTIAL_US_SEC_ENRICHMENT_EXPANSION_NOT_SCORING", "COMPLETED_US_SEC_ENRICHMENT_EXPANSION_NOT_SCORING"}
    assert report["us_rows"] == 9200 and report["us_eligible"] == 5011
    assert report["cik_resolved"] == 0 or report["cik_resolved"] >= 4896
    assert report["raw_cache_published"] is False
    assert report["guardrails"]["phase9c_authorized"] is False
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert_no_secrets()
    selected = first_resolved()
    if selected:
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            cik = selected["cik"]
            (cache / "submissions").mkdir()
            (cache / "companyfacts").mkdir()
            (cache / "submissions" / f"CIK{cik}.json").write_text(
                json.dumps({"filings": {"recent": {"form": ["8-K", "10-Q", "10-K"], "filingDate": ["2026-01-15", "2026-05-10", "2026-03-01"]}}}),
                encoding="utf-8",
            )
            (cache / "companyfacts" / f"CIK{cik}.json").write_text(
                json.dumps({"facts": {"us-gaap": {"Revenues": {}, "NetIncomeLoss": {}, "Assets": {}, "Liabilities": {}, "EarningsPerShareBasic": {}}}}),
                encoding="utf-8",
            )
            subprocess.run([sys.executable, str(BUILDER), "--cache-dir", str(cache), "--limit", "5"], cwd=ROOT, check=True, capture_output=True, text=True)
            cached_report = json.loads((OUT / "us_sec_enrichment_aggregate_report_v2_38e.json").read_text(encoding="utf-8"))
            assert cached_report["enriched_sec_ready"] >= 1
            cached_rows = read_rows(OUT / "us_sec_enrichment_readiness_v2_38e.csv")
            enriched = next(r for r in cached_rows if r["asset_id"] == selected["asset_id"])
            assert enriched["enrichment_status"] == "ENRICHED_SEC_READY"
            assert enriched["submissions_available"] == "true"
            assert enriched["companyfacts_available"] == "true"
            assert "10-K" in enriched["available_forms"] and "10-Q" in enriched["available_forms"]
            assert "revenue" in enriched["basic_concepts_available"]
        subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True, capture_output=True, text=True)
    print("PASS: v2.38E/readiness/offline/schema/cache-aware/no-secrets/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
