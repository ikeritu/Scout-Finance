#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_price_features_v2_38h.py"


def write_candidates(path: Path) -> None:
    fields = ["asset_id", "ticker", "company_name", "exchange"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Analytics Inc.", "exchange": "NASDAQ"})
        writer.writerow({"asset_id": "U00002", "ticker": "THIN", "company_name": "Thin History Corp.", "exchange": "NYSE"})


def write_prices(path: Path, days: int, start_price: float, slope: float, volume: int | None) -> None:
    fields = ["date", "adjusted_close", "volume"]
    start = date(2025, 1, 1)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for idx in range(days):
            writer.writerow({
                "date": (start + timedelta(days=idx)).isoformat(),
                "adjusted_close": round(start_price + slope * idx, 4),
                "volume": "" if volume is None else volume + idx,
            })


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run(candidates: Path, price_root: Path, out: Path) -> dict:
    result = subprocess.run([sys.executable, str(SCRIPT), "--candidates-path", str(candidates), "--price-root", str(price_root), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        candidates = base / "candidates.csv"
        prices = base / "prices"
        out1 = base / "out1"
        out2 = base / "out2"
        prices.mkdir()
        write_candidates(candidates)
        write_prices(prices / "U00001.csv", 260, 50.0, 0.5, 100000)
        write_prices(prices / "THIN.csv", 10, 10.0, 0.1, None)
        payload = run(candidates, prices, out1)
        payload2 = run(candidates, prices, out2)
        assert payload == payload2
        rows = read_rows(out1 / "us_price_features_v2_38h.csv")
        assert len(rows) == 2
        good = next(r for r in rows if r["asset_id"] == "U00001")
        assert good["price_feature_quality_status"] == "PRICE_FEATURES_READY"
        assert good["adjusted_prices_available"] == "true"
        assert good["liquidity_available_flag"] == "true"
        assert good["momentum_consistency_flag"] == "true"
        assert good["trend_positive_flag"] == "true"
        assert good["near_52w_high_flag"] == "true"
        assert float(good["return_1m"]) > 0
        assert float(good["return_12m"]) > 0
        assert float(good["price_vs_sma_50"]) > 0
        assert float(good["volatility_3m"]) >= 0
        bad = next(r for r in rows if r["asset_id"] == "U00002")
        assert bad["price_feature_quality_status"] == "INSUFFICIENT_PRICE_EVIDENCE"
        rejections = read_rows(out1 / "us_price_feature_rejections_v2_38h.csv")
        assert any(r["asset_id"] == "U00002" and r["reason"] == "insufficient_rows" for r in rejections)
        assert payload["recommendations_generated"] is False
    print("PASS: v2.38H/builder/offline/deterministic/momentum-trend-risk-liquidity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
