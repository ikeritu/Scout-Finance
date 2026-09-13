#!/usr/bin/env python3
"""Offline QA for v2.38BY ranking UX hardening.

This test intentionally avoids starting Streamlit. It validates the UI
surface as source text plus the real v2.38BV result populations.
"""
from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_v2_37.py"
RESULTS = ROOT / "outputs/full_universe_source_acquisition/v2_38bv_global_research_ranking/global_research_ranking_results_v2_38bv.json"


def test_app_stays_parseable():
    ast.parse(APP.read_text(encoding="utf-8"))


def test_real_ranking_populations_still_match_v2_38bx():
    rows = json.loads(RESULTS.read_text(encoding="utf-8"))
    counts = Counter(row["eligibility_status"] for row in rows)
    assert len(rows) == 1111
    assert counts["ELIGIBLE_PARTIAL"] == 318
    assert counts["PARTIAL_COMPARABILITY"] == 373
    assert counts["REVIEW_REQUIRED"] == 124
    assert counts["BLOCKED"] == 270
    assert counts["NOT_YET_SCORED_NO_ADAPTER"] == 26


def test_hardened_ranking_controls_are_present():
    text = APP.read_text(encoding="utf-8")
    required = [
        "filter_global_ranking_rows",
        "global_ranking_export_frame",
        "global_ranking_search",
        "global_ranking_score_range",
        "global_ranking_coverage_range",
        "global_ranking_top_n",
        "Descargar CSV filtrado",
        "Cobertura insuficiente",
        "st.tabs",
        "v2.38BV",
        "v2.38BX",
    ]
    for token in required:
        assert token in text, token


def test_export_surface_excludes_private_watchlist_data():
    text = APP.read_text(encoding="utf-8")
    start = text.index("def global_ranking_export_frame")
    end = text.index("def global_ranking_display_frame")
    export_block = text[start:end]
    assert "watchlist" not in export_block.lower()
    assert "note" not in export_block.lower()
    assert "research_status" not in export_block
    assert "google_finance_search" in export_block


def test_ui_does_not_recompute_scoring_or_call_network():
    text = APP.read_text(encoding="utf-8")
    forbidden = [
        "score_assets(",
        "percentile_scores(",
        "build_raw_factors(",
        "build_global_research_ranking_v2_38bv",
        "requests.",
        "httpx.",
        "urlopen(",
        "subprocess.",
        "os.system(",
    ]
    for token in forbidden:
        assert token not in text, token


CASES = [
    test_app_stays_parseable,
    test_real_ranking_populations_still_match_v2_38bx,
    test_hardened_ranking_controls_are_present,
    test_export_surface_excludes_private_watchlist_data,
    test_ui_does_not_recompute_scoring_or_call_network,
]


def main() -> int:
    for case in CASES:
        case()
    print("PASS: v2.38BY/ui-ranking-ux-hardening/read-only/export-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
