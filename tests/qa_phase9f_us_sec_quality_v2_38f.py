#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38f_us_sec_fundamental_normalization"
SCRIPT = ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|SCOUT_FINANCE_SEC_USER_AGENT\s*=", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def assert_no_secrets() -> None:
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    report = json.loads((OUT / "us_sec_fundamental_aggregate_report_v2_38f.json").read_text(encoding="utf-8"))
    assert report["input_us_rows"] == 9200
    assert report["input_us_eligible"] == 5011
    assert report["input_cik_resolved"] >= 4896
    assert report["raw_cache_published"] is False
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["phase9c_authorized"] is False
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["status"] in {
        "PARTIAL_US_SEC_FUNDAMENTAL_NORMALIZATION_NOT_SCORING",
        "COMPLETED_US_SEC_FUNDAMENTAL_NORMALIZATION_NOT_SCORING",
    }
    quality = rows(OUT / "us_sec_fundamental_quality_v2_38f.csv")
    assert len(quality) == report["companies_processed"]
    assert {r["quality_status"] for r in quality} <= {"NORMALIZED_READY", "NORMALIZED_PARTIAL", "NO_NORMALIZABLE_FACTS"}
    if report["input_enriched_sec_ready"] >= 592:
        assert report["companies_processed"] >= 592
        assert report["records_written"] > 0
        assert report["companies_normalized_ready"] + report["companies_normalized_partial"] > 0
    manifest = json.loads((OUT / "us_sec_fundamental_manifest_v2_38f.json").read_text(encoding="utf-8"))
    assert "us_sec_fundamental_records_v2_38f.jsonl" in manifest["outputs"]
    assert manifest["guardrails"]["recommendations_generated"] is False
    assert_no_secrets()
    print("PASS: v2.38F/quality/manifest/cache-aware/no-secrets/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
