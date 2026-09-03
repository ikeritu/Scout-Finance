#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38j_us_candidate_feature_matrix"
SCRIPT = ROOT / "scripts/build_us_candidate_feature_matrix_v2_38j.py"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|TWELVE_DATA_API_KEY\s*=", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    matrix = rows(OUT / "us_candidate_feature_matrix_v2_38j.csv")
    quality = rows(OUT / "us_candidate_feature_matrix_quality_v2_38j.csv")
    rejections = rows(OUT / "us_candidate_feature_matrix_rejections_v2_38j.csv")
    report = json.loads((OUT / "us_candidate_feature_matrix_aggregate_report_v2_38j.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38J-us-candidate-feature-matrix"
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert len(matrix) == len(quality) == report["candidates_total"]
    assert len({r["asset_id"] for r in matrix}) == len(matrix)
    assert [r["asset_id"] for r in matrix] == sorted(r["asset_id"] for r in matrix)
    assert report["matrix_ready"] + report["partial_price"] + report["partial_fundamentals"] + report["insufficient_evidence"] + report["blocked"] == len(matrix)
    assert report["rejected_rows"] == len(rejections)
    assert all(r["scoring_calculated"] == "False" and r["ranking_calculated"] == "False" and r["recommendation_generated"] == "False" for r in matrix)
    manifest = json.loads((OUT / "us_candidate_feature_matrix_manifest_v2_38j.json").read_text(encoding="utf-8"))
    assert "us_candidate_feature_matrix_v2_38j.csv" in manifest["outputs"]
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path
    print("PASS: v2.38J/quality/manifest/no-secrets/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
