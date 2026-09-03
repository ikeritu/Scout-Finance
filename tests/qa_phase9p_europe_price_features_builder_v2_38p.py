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
SCRIPT = ROOT / "scripts/build_europe_price_features_v2_38p.py"


def write_plan(path: Path) -> None:
    fields = ["asset_id", "ticker", "company_name", "home_exchange", "home_mic", "home_country", "home_currency", "provider", "provider_symbol"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerow({"asset_id": "U30001", "ticker": "AAA", "company_name": "Alpha AG", "home_exchange": "XETRA", "home_mic": "XETR", "home_country": "DE", "home_currency": "EUR", "provider": "stooq", "provider_symbol": "aaa.de"})
        writer.writerow({"asset_id": "U30002", "ticker": "BBB", "company_name": "Beta Plc", "home_exchange": "LSE", "home_mic": "XLON", "home_country": "GB", "home_currency": "GBP", "provider": "eodhd", "provider_symbol": "BBB.LSE"})
        writer.writerow({"asset_id": "U30003", "ticker": "CCC", "company_name": "Thin SA", "home_exchange": "Euronext Paris", "home_mic": "XPAR", "home_country": "FR", "home_currency": "EUR", "provider": "eodhd", "provider_symbol": "CCC.PA"})
        writer.writerow({"asset_id": "U30004", "ticker": "CBOE", "company_name": "Blocked", "home_exchange": "CBOE_EUROPE", "home_mic": "CBOE", "home_country": "", "home_currency": "EUR", "provider": "stooq", "provider_symbol": "cboe"})


def write_prices(path: Path, days: int, start_price: float, slope: float, volume: int) -> None:
    fields = ["date", "open", "high", "low", "close", "adjusted_close", "volume", "provider", "provider_symbol", "home_exchange", "home_mic", "home_currency"]
    start = date(2025, 1, 1)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for idx in range(days):
            price = round(start_price + slope * idx, 4)
            writer.writerow({
                "date": (start + timedelta(days=idx)).isoformat(),
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "adjusted_close": price,
                "volume": volume + idx,
                "provider": "fixture",
                "provider_symbol": path.stem,
                "home_exchange": "fixture",
                "home_mic": "fixture",
                "home_currency": "EUR",
            })


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        plan = base / "plan.csv"
        prices = base / "prices"
        out1 = base / "out1"
        out2 = base / "out2"
        prices.mkdir()
        write_plan(plan)
        write_prices(prices / "U30001.csv", 260, 50.0, 0.5, 100000)
        write_prices(prices / "U30002.csv", 130, 25.0, 0.2, 50000)
        write_prices(prices / "U30003.csv", 40, 15.0, 0.1, 10000)
        for out in (out1, out2):
            result = subprocess.run([sys.executable, str(SCRIPT), "--plan-path", str(plan), "--price-root", str(prices), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True)
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["recommendations_generated"] is False
        assert (out1 / "europe_price_features_v2_38p.csv").read_text(encoding="utf-8") == (out2 / "europe_price_features_v2_38p.csv").read_text(encoding="utf-8")
        rows = read_rows(out1 / "europe_price_features_v2_38p.csv")
        by_id = {r["asset_id"]: r for r in rows}
        assert by_id["U30001"]["price_quality_status"] == "EUROPE_PRICE_FEATURES_READY"
        assert by_id["U30001"]["trend_positive_flag"] == "true"
        assert float(by_id["U30001"]["return_12m"]) > 0
        assert by_id["U30002"]["price_quality_status"] == "EUROPE_PRICE_FEATURES_PARTIAL"
        assert by_id["U30003"]["price_quality_status"] == "EUROPE_PRICE_FEATURES_INSUFFICIENT"
        quality = read_rows(out1 / "europe_price_feature_quality_v2_38p.csv")
        assert len(quality) == len(rows) + 1
        rejections = read_rows(out1 / "europe_price_feature_rejections_v2_38p.csv")
        assert any(r["asset_id"] == "U30004" and r["rejection_status"] == "EUROPE_PRICE_FEATURES_REJECTED_CBOE_SOURCE" for r in rejections)
    print("PASS: v2.38P/builder/offline/deterministic/momentum-trend-risk-liquidity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
