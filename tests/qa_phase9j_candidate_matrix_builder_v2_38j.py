#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_candidate_feature_matrix_v2_38j.py"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run(identity: Path, fundamentals: Path, prices: Path, out: Path) -> dict:
    result = subprocess.run([sys.executable, str(SCRIPT), "--identity-path", str(identity), "--fundamentals-path", str(fundamentals), "--prices-path", str(prices), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        identity = base / "identity.csv"
        fundamentals = base / "fundamentals.csv"
        prices = base / "prices.csv"
        out1 = base / "out1"
        out2 = base / "out2"
        write_csv(identity, ["asset_id", "ticker", "exchange", "company_name", "cik"], [
            {"asset_id": "U00001", "ticker": "AAA", "exchange": "NASDAQ", "company_name": "Alpha Analytics Inc.", "cik": "0000000001"},
            {"asset_id": "U00002", "ticker": "BBB", "exchange": "NYSE", "company_name": "Beta Builders Inc.", "cik": "0000000002"},
            {"asset_id": "U00003", "ticker": "CCC", "exchange": "NASDAQ", "company_name": "Core Cloud Inc.", "cik": "0000000003"},
        ])
        write_csv(fundamentals, ["asset_id", "ticker", "company_name", "exchange", "cik", "feature_quality_status", "revenue_yoy_growth", "net_margin", "liabilities_to_assets", "free_cash_flow_margin", "positive_fcf_flag"], [
            {"asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Analytics Inc.", "exchange": "NASDAQ", "cik": "0000000001", "feature_quality_status": "FEATURES_READY", "revenue_yoy_growth": "0.25", "net_margin": "0.12", "liabilities_to_assets": "0.3", "free_cash_flow_margin": "0.08", "positive_fcf_flag": "true"},
            {"asset_id": "U00002", "ticker": "BBB", "company_name": "Beta Builders Inc.", "exchange": "NYSE", "cik": "0000000002", "feature_quality_status": "FEATURES_READY", "revenue_yoy_growth": "-0.1", "net_margin": "-0.02", "liabilities_to_assets": "0.8", "free_cash_flow_margin": "", "positive_fcf_flag": "false"},
        ])
        write_csv(prices, ["asset_id", "ticker", "company_name", "exchange", "price_feature_quality_status", "return_1m", "return_3m", "return_6m", "return_12m", "volatility_3m", "volatility_6m", "max_drawdown_6m", "max_drawdown_12m", "price_vs_sma_50", "price_vs_sma_200", "sma_50_vs_sma_200", "trend_positive_flag", "recent_high_breakout_flag", "near_52w_high_flag", "recovery_from_drawdown_flag", "avg_volume_1m", "avg_volume_3m", "liquidity_available_flag"], [
            {"asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Analytics Inc.", "exchange": "NASDAQ", "price_feature_quality_status": "PRICE_FEATURES_READY", "return_1m": "0.02", "return_3m": "0.08", "return_6m": "0.11", "return_12m": "0.3", "volatility_3m": "0.1", "volatility_6m": "0.2", "max_drawdown_6m": "-0.1", "max_drawdown_12m": "-0.2", "price_vs_sma_50": "0.04", "price_vs_sma_200": "0.12", "sma_50_vs_sma_200": "0.07", "trend_positive_flag": "true", "recent_high_breakout_flag": "false", "near_52w_high_flag": "true", "recovery_from_drawdown_flag": "true", "avg_volume_1m": "100000", "avg_volume_3m": "90000", "liquidity_available_flag": "true"},
            {"asset_id": "U00003", "ticker": "CCC", "company_name": "Core Cloud Inc.", "exchange": "NASDAQ", "price_feature_quality_status": "PRICE_FEATURES_READY", "return_1m": "0.01", "return_3m": "0.05", "return_6m": "0.07", "return_12m": "0.18", "volatility_3m": "0.2", "volatility_6m": "0.25", "max_drawdown_6m": "-0.2", "max_drawdown_12m": "-0.3", "price_vs_sma_50": "0.01", "price_vs_sma_200": "0.03", "sma_50_vs_sma_200": "0.02", "trend_positive_flag": "true", "recent_high_breakout_flag": "false", "near_52w_high_flag": "false", "recovery_from_drawdown_flag": "true", "avg_volume_1m": "80000", "avg_volume_3m": "85000", "liquidity_available_flag": "true"},
        ])
        payload = run(identity, fundamentals, prices, out1)
        assert payload == run(identity, fundamentals, prices, out2)
        rows = read_rows(out1 / "us_candidate_feature_matrix_v2_38j.csv")
        assert [r["asset_id"] for r in rows] == ["U00001", "U00002", "U00003"]
        assert rows[0]["candidate_matrix_status"] == "CANDIDATE_MATRIX_READY"
        assert rows[1]["candidate_matrix_status"] == "CANDIDATE_MATRIX_PARTIAL_PRICE"
        assert rows[2]["candidate_matrix_status"] == "CANDIDATE_MATRIX_PARTIAL_FUNDAMENTALS"
        assert rows[0]["scoring_calculated"] == "False"
        assert rows[0]["ranking_calculated"] == "False"
        assert rows[0]["recommendation_generated"] == "False"
        assert payload["matrix_ready"] == 1
        assert payload["partial_price"] == 1
        assert payload["partial_fundamentals"] == 1
    print("PASS: v2.38J/builder/offline/deterministic/join-statuses/no-ranking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
