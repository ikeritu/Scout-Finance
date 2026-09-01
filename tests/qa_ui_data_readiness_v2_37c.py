#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_v2_37.repository import (
    AGGREGATE_REL, DERIVED_REL, LOCAL_RESULTS_REL, NORMALIZED_REL, PRICE_RELS,
    UNIVERSE_REL, DataMode, load_product_data,
)

def copy_input(root: Path, relative: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / relative, target)


def assert_canonical_population(data) -> None:
    assert len(data.assets) == 50 and len({a["asset_id"] for a in data.assets}) == 50
    assert Counter(a["eligibility_status"] for a in data.assets) == {
        "ELIGIBLE_PARTIAL": 41, "PARTIAL_COMPARABILITY": 7, "REVIEW_REQUIRED": 2,
    }
    assert all(a["rank"] is None for a in data.assets if a["market"] == "TWSE")
    assert {a["asset_id"] for a in data.assets if a["eligibility_status"] == "REVIEW_REQUIRED"} == {"P020", "P178"}
    assert len([a for a in data.assets if a["rank"]]) == (41 if data.local_scoring else 10)


def main() -> int:
    installed = load_product_data(ROOT)
    assert installed.mode in {DataMode.AGGREGATE_ONLY, DataMode.PARTIAL_DATA, DataMode.REAL_LOCAL_READY}
    assert_canonical_population(installed)

    with tempfile.TemporaryDirectory() as directory:
        sandbox = Path(directory)
        blocked = load_product_data(sandbox)
        assert blocked.mode == DataMode.BLOCKED_MISSING_DATA and not blocked.assets
        copy_input(sandbox, UNIVERSE_REL); copy_input(sandbox, AGGREGATE_REL)
        aggregate = load_product_data(sandbox)
        assert aggregate.mode == DataMode.AGGREGATE_ONLY
        assert_canonical_population(aggregate)
        detailed = []
        for asset in aggregate.assets:
            detailed.append({
                "asset_id": asset["asset_id"], "eligibility_status": asset["eligibility_status"],
                "confidence": asset["confidence"], "total_score": asset["total_score"], "rank": asset["rank"],
                "coverage_weight": 1.0, "pillar_scores": {}, "raw_factors": {},
                "review_reasons": asset["review_reasons"], "explanation": {},
            })
        local = sandbox / LOCAL_RESULTS_REL; local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(detailed), encoding="utf-8")
        for relative in (NORMALIZED_REL, DERIVED_REL):
            path = sandbox / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("", encoding="utf-8")
        for relative in PRICE_RELS.values(): (sandbox / relative).mkdir(parents=True, exist_ok=True)
        ready = load_product_data(sandbox)
        assert ready.mode == DataMode.REAL_LOCAL_READY and ready.local_scoring and ready.local_fundamentals and ready.local_prices
    print("PASS: v2.37C data-readiness/50-assets/41-main/7-partial/2-review/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
