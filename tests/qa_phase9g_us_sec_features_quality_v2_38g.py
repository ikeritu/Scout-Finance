#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38g_us_sec_fundamental_features"
SCRIPT = ROOT / "scripts/build_us_sec_fundamental_features_v2_38g.py"
INPUT = ROOT / "outputs/full_universe_source_acquisition/v2_38f_us_sec_fundamental_normalization/us_sec_fundamental_records_v2_38f.jsonl"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|SCOUT_FINANCE_SEC_USER_AGENT\s*=", re.I)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def assert_no_secrets() -> None:
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path


def main() -> int:
    assert INPUT.exists(), "v2.38F normalized JSONL must exist locally; it is intentionally not committed if large"
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    report = json.loads((OUT / "us_sec_fundamental_feature_aggregate_report_v2_38g.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38G-us-sec-fundamental-features"
    assert report["status"] in {"PARTIAL_US_SEC_FUNDAMENTAL_FEATURES_NOT_SCORING", "COMPLETED_US_SEC_FUNDAMENTAL_FEATURES_NOT_SCORING"}
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["phase9c_authorized"] is False
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["raw_cache_published"] is False
    features = read_rows(OUT / "us_sec_fundamental_features_v2_38g.csv")
    quality = read_rows(OUT / "us_sec_fundamental_feature_quality_v2_38g.csv")
    assert len(features) == report["companies_input"] == len(quality)
    assert {r["feature_quality_status"] for r in features} <= {"FEATURES_READY", "FEATURES_PARTIAL", "INSUFFICIENT_FEATURE_EVIDENCE"}
    if report["input_records"] > 0:
        assert report["companies_input"] > 0
        assert report["companies_features_ready"] + report["companies_features_partial"] > 0
    manifest = json.loads((OUT / "us_sec_fundamental_features_manifest_v2_38g.json").read_text(encoding="utf-8"))
    assert "us_sec_fundamental_features_v2_38g.csv" in manifest["outputs"]
    assert manifest["guardrails"]["recommendations_generated"] is False
    assert_no_secrets()
    print("PASS: v2.38G/quality/manifest/local-jsonl/no-secrets/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
