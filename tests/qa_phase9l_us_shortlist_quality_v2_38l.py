#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38l_us_explained_shortlist"
SCRIPT = ROOT / "scripts/build_us_explained_shortlist_v2_38l.py"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|TWELVE_DATA_API_KEY\s*=", re.I)
FORBIDDEN_RE = re.compile(r"\b(buy|sell|hold|price target|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT), "--limit", "50"], cwd=ROOT, check=True, capture_output=True, text=True)
    shortlist = rows(OUT / "us_explained_shortlist_v2_38l.csv")
    notes = rows(OUT / "us_explained_shortlist_research_notes_v2_38l.csv")
    quality = rows(OUT / "us_explained_shortlist_quality_v2_38l.csv")
    rejections = rows(OUT / "us_explained_shortlist_rejections_v2_38l.csv")
    report = json.loads((OUT / "us_explained_shortlist_aggregate_report_v2_38l.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38L-us-explained-shortlist"
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["recommendation_generated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["guardrails"]["financial_advice"] is False
    assert report["guardrails"]["phase9c_authorized"] is False
    assert len(shortlist) == len(quality) == report["shortlist_size"]
    assert len({r["asset_id"] for r in shortlist}) == len(shortlist)
    assert report["rejected_rows"] == len(rejections)
    assert [int(r["shortlist_rank"]) for r in shortlist] == list(range(1, len(shortlist) + 1))
    assert all(r["candidate_matrix_status"] == "CANDIDATE_MATRIX_READY" for r in shortlist)
    assert all(r["recommendation_generated"] == "false" and r["financial_advice"] == "false" for r in shortlist)
    assert all(r["research_explanation"] and r["next_research_steps"] for r in shortlist)
    assert len(notes) >= len(shortlist) * 3
    manifest = json.loads((OUT / "us_explained_shortlist_manifest_v2_38l.json").read_text(encoding="utf-8"))
    assert "us_explained_shortlist_v2_38l.csv" in manifest["outputs"]
    for path in OUT.glob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert not SECRET_RE.search(text), path
    for row in shortlist:
        language = " ".join([
            row["inclusion_reason"],
            row["research_explanation"],
            row["next_research_steps"],
        ])
        assert not FORBIDDEN_RE.search(language), row["asset_id"]
    for row in notes:
        assert not FORBIDDEN_RE.search(row["note"]), row["asset_id"]
    print("PASS: v2.38L/quality/manifest/no-secrets/no-final-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
