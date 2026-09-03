#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_price_features_v2_38p.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38p_europe_price_features"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|TWELVE_DATA_API_KEY\s*=|EODHD_API_KEY\s*=", re.I)
ACTION_RE = re.compile(r"\b(buy|sell|hold|price target|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    features = rows(OUT / "europe_price_features_v2_38p.csv")
    quality = rows(OUT / "europe_price_feature_quality_v2_38p.csv")
    rejections = rows(OUT / "europe_price_feature_rejections_v2_38p.csv")
    report = json.loads((OUT / "europe_price_feature_aggregate_report_v2_38p.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "europe_price_features_manifest_v2_38p.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38P-europe-price-features"
    assert report["status"] in {"PRICE_FEATURES_BLOCKED_NO_LOCAL_EUROPE_PRICE_HISTORY", "COMPLETED_EUROPE_PRICE_FEATURES_NOT_SCORING"}
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["cboe_europe_source_forbidden"] is True
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["guardrails"]["phase9c_authorized"] is False
    assert report["raw_cache_published"] is False
    assert len(features) == report["companies_input"]
    assert len(rejections) == report["rejected_rows"]
    if report["status"] == "PRICE_FEATURES_BLOCKED_NO_LOCAL_EUROPE_PRICE_HISTORY":
        assert report["companies_input"] == 0
        assert report["price_files_discovered"] == 0
    else:
        assert report["companies_input"] > 0
        assert report["price_files_discovered"] > 0
    for row in features:
        assert row["home_exchange"] != "CBOE_EUROPE"
        assert row["scoring_calculated"] == "false"
        assert row["ranking_calculated"] == "false"
        assert row["recommendations_generated"] == "false"
        assert row["phase9c_authorized"] == "false"
        assert row["price_quality_status"].startswith("EUROPE_PRICE_FEATURES_")
    for row in rejections:
        language = " ".join([row["rejection_status"], row["rejection_reason"]])
        assert not ACTION_RE.search(language), row["asset_id"]
    assert len(quality) >= len(features)
    assert "europe_price_features_v2_38p.csv" in manifest["outputs"]
    assert "europe_price_feature_aggregate_report_v2_38p.json" in manifest["outputs"]
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path
    print("PASS: v2.38P/quality/fail-closed-or-local-price/no-secrets/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
