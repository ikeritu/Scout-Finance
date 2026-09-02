#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38h_us_price_features"
SCRIPT = ROOT / "scripts/build_us_price_features_v2_38h.py"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|SCOUT_FINANCE_SEC_USER_AGENT\s*=", re.I)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def assert_no_secrets() -> None:
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    report = json.loads((OUT / "us_price_feature_aggregate_report_v2_38h.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38H-us-price-features"
    assert report["status"] in {"PRICE_FEATURES_BLOCKED_NO_LOCAL_US_PRICE_HISTORY", "COMPLETED_US_PRICE_FEATURES_NOT_SCORING"}
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["phase9c_authorized"] is False
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["raw_cache_published"] is False
    features = read_rows(OUT / "us_price_features_v2_38h.csv")
    quality = read_rows(OUT / "us_price_feature_quality_v2_38h.csv")
    assert len(features) == len(quality) == report["companies_input"]
    if report["status"] == "PRICE_FEATURES_BLOCKED_NO_LOCAL_US_PRICE_HISTORY":
        assert report["companies_input"] == 0
        assert report["price_files_discovered"] == 0
        assert report["rejected_rows"] >= 0
    else:
        assert report["companies_input"] > 0
        assert report["price_files_discovered"] > 0
    manifest = json.loads((OUT / "us_price_features_manifest_v2_38h.json").read_text(encoding="utf-8"))
    assert "us_price_features_v2_38h.csv" in manifest["outputs"]
    assert manifest["guardrails"]["recommendations_generated"] is False
    assert_no_secrets()
    print("PASS: v2.38H/quality/fail-closed-or-local-price/no-secrets/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
