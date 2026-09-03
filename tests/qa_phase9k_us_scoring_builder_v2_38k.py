#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_experimental_scores_v2_38k.py"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run(matrix: Path, out: Path) -> dict:
    result = subprocess.run([sys.executable, str(SCRIPT), "--input-matrix", str(matrix), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def main() -> int:
    fields = [
        "asset_id", "ticker", "company_name", "exchange", "cik",
        "candidate_matrix_status", "evidence_level", "missing_reason",
        "revenue_growth_yoy", "net_margin", "free_cash_flow_margin",
        "debt_to_assets", "profitability_positive_flag", "growth_positive_flag",
        "balance_sheet_risk_flag", "return_3m", "return_6m", "return_12m",
        "price_vs_sma_200", "volatility_3m", "volatility_6m",
        "max_drawdown_6m", "max_drawdown_12m", "trend_positive_flag",
        "recent_high_breakout_flag", "liquidity_available_flag",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        matrix = base / "matrix.csv"
        out1 = base / "out1"
        out2 = base / "out2"
        write_csv(matrix, fields, [
            {
                "asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Analytics Inc.",
                "exchange": "NASDAQ", "cik": "0000000001", "candidate_matrix_status": "CANDIDATE_MATRIX_READY",
                "evidence_level": "high", "missing_reason": "", "revenue_growth_yoy": "0.42",
                "net_margin": "0.18", "free_cash_flow_margin": "0.12", "debt_to_assets": "0.25",
                "profitability_positive_flag": "true", "growth_positive_flag": "true",
                "balance_sheet_risk_flag": "false", "return_3m": "0.14", "return_6m": "0.22",
                "return_12m": "0.55", "price_vs_sma_200": "0.24", "volatility_3m": "0.28",
                "volatility_6m": "0.32", "max_drawdown_6m": "-0.12", "max_drawdown_12m": "-0.18",
                "trend_positive_flag": "true", "recent_high_breakout_flag": "true",
                "liquidity_available_flag": "true",
            },
            {
                "asset_id": "U00002", "ticker": "BBB", "company_name": "Beta Builders Inc.",
                "exchange": "NYSE", "cik": "0000000002", "candidate_matrix_status": "CANDIDATE_MATRIX_READY",
                "evidence_level": "high", "missing_reason": "", "revenue_growth_yoy": "-0.05",
                "net_margin": "-0.03", "free_cash_flow_margin": "-0.02", "debt_to_assets": "0.85",
                "profitability_positive_flag": "false", "growth_positive_flag": "false",
                "balance_sheet_risk_flag": "true", "return_3m": "-0.08", "return_6m": "-0.15",
                "return_12m": "-0.25", "price_vs_sma_200": "-0.12", "volatility_3m": "0.65",
                "volatility_6m": "0.72", "max_drawdown_6m": "-0.38", "max_drawdown_12m": "-0.52",
                "trend_positive_flag": "false", "recent_high_breakout_flag": "false",
                "liquidity_available_flag": "true",
            },
            {
                "asset_id": "U00003", "ticker": "CCC", "company_name": "Core Cloud Inc.",
                "exchange": "NASDAQ", "cik": "0000000003", "candidate_matrix_status": "CANDIDATE_MATRIX_PARTIAL_PRICE",
                "evidence_level": "medium", "missing_reason": "price_features_missing_or_partial",
            },
        ])
        payload = run(matrix, out1)
        assert payload == run(matrix, out2)
        rows = read_rows(out1 / "us_experimental_scores_v2_38k.csv")
        assert len(rows) == 3
        assert rows[0]["research_rank"] == "1"
        assert rows[0]["ticker"] == "AAA"
        assert float(rows[0]["experimental_score"]) > float(rows[1]["experimental_score"])
        assert rows[2]["score_bucket"] == "REVIEW_REQUIRED"
        assert rows[2]["experimental_score"] == ""
        assert all(r["recommendation_generated"] == "false" for r in rows)
        assert payload["scored_companies"] == 2
        assert payload["unscored_companies"] == 1
    print("PASS: v2.38K/builder/offline/deterministic/rank-ready-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
