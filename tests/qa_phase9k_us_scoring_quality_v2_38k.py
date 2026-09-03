#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38k_us_experimental_scoring"
SCRIPT = ROOT / "scripts/build_us_experimental_scores_v2_38k.py"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|TWELVE_DATA_API_KEY\s*=", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    scores = rows(OUT / "us_experimental_scores_v2_38k.csv")
    components = rows(OUT / "us_experimental_score_components_v2_38k.csv")
    quality = rows(OUT / "us_experimental_score_quality_v2_38k.csv")
    rejections = rows(OUT / "us_experimental_score_rejections_v2_38k.csv")
    report = json.loads((OUT / "us_experimental_score_aggregate_report_v2_38k.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38K-us-experimental-scoring"
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["scoring_calculated"] is True
    assert report["guardrails"]["ranking_calculated"] is True
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["guardrails"]["broker_actions_allowed"] is False
    assert len(scores) == len(quality) == report["input_candidates"] - report["rejected_rows"]
    assert len(components) == len(scores) * 5
    assert report["rejected_rows"] == len(rejections)
    ranked = [r for r in scores if r["research_rank"]]
    assert len(ranked) == report["scored_companies"]
    assert [int(r["research_rank"]) for r in ranked] == list(range(1, len(ranked) + 1))
    assert all(0 <= float(r["experimental_score"]) <= 100 for r in ranked)
    assert all(r["recommendation_generated"] == "false" for r in scores)
    assert all("buy" not in r["experimental_score_notes"].lower() or "not a recommendation" in r["experimental_score_notes"].lower() for r in scores)
    manifest = json.loads((OUT / "us_experimental_score_manifest_v2_38k.json").read_text(encoding="utf-8"))
    assert "us_experimental_scores_v2_38k.csv" in manifest["outputs"]
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path
    print("PASS: v2.38K/quality/manifest/no-secrets/no-final-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
