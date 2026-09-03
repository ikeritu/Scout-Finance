#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38m_macro_geopolitical_context"
SCRIPT = ROOT / "scripts/build_macro_geopolitical_context_v2_38m.py"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|TWELVE_DATA_API_KEY\s*=", re.I)
ACTION_RE = re.compile(r"\b(buy|sell|hold|price target|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    taxonomy = rows(OUT / "macro_geopolitical_taxonomy_v2_38m.csv")
    context = rows(OUT / "us_shortlist_macro_context_v2_38m.csv")
    notes = rows(OUT / "us_shortlist_macro_notes_v2_38m.csv")
    quality = rows(OUT / "macro_geopolitical_quality_v2_38m.csv")
    rejections = rows(OUT / "macro_geopolitical_rejections_v2_38m.csv")
    report = json.loads((OUT / "macro_geopolitical_aggregate_report_v2_38m.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38M-macro-geopolitical-context"
    assert report["status"] == "COMPLETED_MACRO_GEOPOLITICAL_CONTEXT_STATIC_NOT_RECOMMENDATIONS"
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["live_news_used"] is False
    assert report["guardrails"]["llm_runtime_classification"] is False
    assert report["guardrails"]["ranking_modified"] is False
    assert report["guardrails"]["scoring_modified"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert len(taxonomy) == report["themes_defined"]
    assert len(context) == len(quality) == report["shortlist_assets"] - report["rejected_rows"]
    assert len(notes) == report["notes"]
    assert len(rejections) == report["rejected_rows"]
    assert len({r["asset_id"] for r in context}) == len(context)
    for row in context:
        opportunity = float(row["macro_opportunity_score"])
        risk = float(row["macro_risk_score"])
        balance = float(row["macro_balance"])
        assert 0 <= opportunity <= 100
        assert 0 <= risk <= 100
        assert abs(balance - (opportunity - risk)) < 0.0001
        assert "INTEREST_RATES" in row["applicable_themes"]
        assert row["recommendation_generated"] == "false"
        assert row["financial_advice"] == "false"
        language = " ".join([
            row["macro_context_summary"],
            row["macro_positive_context"],
            row["macro_risk_context"],
            row["macro_limitations"],
            row["next_macro_research_steps"],
        ])
        assert not ACTION_RE.search(language), row["asset_id"]
    for row in notes:
        assert not ACTION_RE.search(row["note"]), row["asset_id"]
    manifest = json.loads((OUT / "macro_geopolitical_manifest_v2_38m.json").read_text(encoding="utf-8"))
    assert "us_shortlist_macro_context_v2_38m.csv" in manifest["outputs"]
    for path in OUT.glob("*"):
        if path.is_file():
            assert not SECRET_RE.search(path.read_text(encoding="utf-8")), path
    print("PASS: v2.38M/quality/manifest/no-secrets/static-context")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
