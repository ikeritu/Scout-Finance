#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from backtesting.core import BacktestIntegrityError, assert_point_in_time, execution_index, information_date, select_fundamentals

base = {"asset_id": "A", "metric": "eps_basic", "value": 1, "period_end": "2024-12-31", "publication_date": "2025-02-01", "period_type": "annual", "record_id": "1"}
assert_point_in_time(base, "2025-02-28")
try:
    assert_point_in_time(base, "2025-01-31")
    raise AssertionError("future disclosure accepted")
except BacktestIntegrityError as exc:
    assert str(exc) == "lookahead_fundamental_after_signal"
missing = dict(base, publication_date=None, retrieved_at="2025-01-01T00:00:00Z")
try:
    information_date(missing)
    raise AssertionError("retrieved_at fallback accepted")
except BacktestIntegrityError as exc:
    assert str(exc) == "missing_verified_publication_date"
selected = select_fundamentals([base, missing], "2025-02-28")
assert selected["A"]["eps_basic"]["record_id"] == "1"
assert selected["__audit__"]["blocked_missing_publication_date"]["count"] == 1
assert execution_index(["2025-02-28", "2025-03-03", "2025-03-04"], "2025-02-28", 1) == 1
try:
    execution_index(["2025-02-28", "2025-03-03"], "2025-02-28", 0)
    raise AssertionError("same-close execution accepted")
except BacktestIntegrityError:
    pass
print("PASS: v2.36 no-lookahead/publication-required/retrieval-forbidden/execution-lag")
