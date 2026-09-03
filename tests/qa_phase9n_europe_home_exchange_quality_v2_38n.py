#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_home_exchange_resolution_v2_38n.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38n_europe_home_exchange_resolution"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|TWELVE_DATA_API_KEY\s*=", re.I)
ACTION_RE = re.compile(r"\b(buy|sell|hold|price target|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    resolved = rows(OUT / "europe_home_exchange_resolution_v2_38n.csv")
    review = rows(OUT / "europe_home_exchange_review_v2_38n.csv")
    country = rows(OUT / "europe_home_exchange_country_summary_v2_38n.csv")
    routes = rows(OUT / "europe_home_exchange_route_matrix_v2_38n.csv")
    batches = rows(OUT / "europe_home_exchange_batch_plan_v2_38n.csv")
    report = json.loads((OUT / "europe_home_exchange_aggregate_report_v2_38n.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "europe_home_exchange_manifest_v2_38n.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38N-europe-home-exchange-resolution"
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["cboe_europe_is_secondary_by_default"] is True
    assert report["guardrails"]["home_exchange_required_for_europe_enrichment"] is True
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["guardrails"]["phase9c_authorized"] is False
    assert len(resolved) == report["europe_rows"]
    assert len(review) == report["manual_review_or_blocked"]
    assert country
    assert routes
    assert batches
    assert "europe_home_exchange_resolution_v2_38n.csv" in manifest["outputs"]
    assert "europe_home_exchange_aggregate_report_v2_38n.json" in manifest["outputs"]
    statuses = {r["resolution_status"] for r in resolved}
    assert "CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED" in statuses
    for row in resolved:
        assert row["scoring_calculated"] == "false"
        assert row["ranking_calculated"] == "false"
        assert row["recommendations_generated"] == "false"
        assert row["phase9c_authorized"] == "false"
        if row["exchange"] == "CBOE_EUROPE":
            assert row["listing_role"] in {"SECONDARY_CBOE_EUROPE", "ADR_GDR"}
            assert row["resolution_status"] in {"CBOE_SECONDARY_HOME_EXCHANGE_REQUIRED", "ADR_GDR_REVIEW_REQUIRED"}
            assert row["home_exchange"] == ""
            assert row["home_mic"] == ""
            assert row["provider_route_status"] != "READY_FOR_PRICE_HISTORY_PILOT"
        language = " ".join([row["review_reason"], row["evidence_source"]])
        assert not ACTION_RE.search(language), row["asset_id"]
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path
    print("PASS: v2.38N/quality/manifest/no-secrets/no-cboe-primary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
