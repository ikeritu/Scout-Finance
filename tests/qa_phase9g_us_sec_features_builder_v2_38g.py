#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_sec_fundamental_features_v2_38g.py"
FEATURES = "us_sec_fundamental_features_v2_38g.csv"
REJECTIONS = "us_sec_fundamental_feature_rejections_v2_38g.csv"


def write_jsonl(path: Path) -> None:
    rows = []
    base = {
        "asset_id": "U00001",
        "ticker": "AAA",
        "company_name": "Alpha Analytics Inc.",
        "exchange": "NASDAQ",
        "cik": "0000000001",
        "unit": "USD",
        "fp": "FY",
        "form": "10-K",
        "taxonomy": "us-gaap",
        "quality_flags": [],
        "period_type": "annual",
        "phase": "v2.38F",
    }
    values = {
        2023: {"revenue": 80, "net_income": 8, "assets": 180, "liabilities": 75, "equity": 105, "operating_cash_flow": 12, "capex": -4},
        2024: {"revenue": 100, "net_income": 10, "assets": 200, "liabilities": 80, "equity": 120, "operating_cash_flow": 20, "capex": -5},
        2025: {"revenue": 130, "net_income": 18, "assets": 230, "liabilities": 85, "equity": 145, "operating_cash_flow": 28, "capex": -6},
    }
    for fy, metrics in values.items():
        for metric, value in metrics.items():
            rows.append(dict(base, metric=metric, value=value, fy=fy, filed=f"{fy + 1}-02-20", end=f"{fy}-12-31", frame=f"CY{fy}", source_concept=metric))
    bad = dict(base, asset_id="U00002", ticker="BAD", company_name="Bad Denominator Corp.", cik="0000000002", fy=2025, filed="2026-02-20", end="2025-12-31", frame="CY2025")
    for metric, value in {"revenue": 0, "net_income": 4, "assets": 0, "liabilities": 10, "equity": 0, "operating_cash_flow": 3, "capex": 2}.items():
        rows.append(dict(bad, metric=metric, value=value, source_concept=metric))
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def write_quality(path: Path) -> None:
    fields = ["asset_id", "ticker", "company_name", "exchange", "cik", "enrichment_status", "records", "metrics_available", "annual_records", "quarterly_records", "latest_filed", "latest_period_end", "quality_status", "missing_metrics", "quality_flags"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Analytics Inc.", "exchange": "NASDAQ", "cik": "0000000001", "enrichment_status": "ENRICHED_SEC_READY", "records": "21", "metrics_available": "", "annual_records": "21", "quarterly_records": "0", "latest_filed": "2026-02-20", "latest_period_end": "2025-12-31", "quality_status": "NORMALIZED_READY", "missing_metrics": "", "quality_flags": ""})


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_once(records: Path, quality: Path, out: Path) -> dict:
    result = subprocess.run([sys.executable, str(SCRIPT), "--input-records", str(records), "--quality-path", str(quality), "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        records = base / "records.jsonl"
        quality = base / "quality.csv"
        out1 = base / "out1"
        out2 = base / "out2"
        write_jsonl(records)
        write_quality(quality)
        payload = run_once(records, quality, out1)
        payload2 = run_once(records, quality, out2)
        assert payload == payload2
        rows = read_rows(out1 / FEATURES)
        assert len(rows) == 2
        good = next(r for r in rows if r["asset_id"] == "U00001")
        assert good["feature_quality_status"] == "FEATURES_READY"
        assert float(good["revenue_yoy_growth"]) == 0.3
        assert float(good["net_margin"]) == round(18 / 130, 6)
        assert float(good["return_on_assets"]) == round(18 / 230, 6)
        assert float(good["return_on_equity"]) == round(18 / 145, 6)
        assert float(good["free_cash_flow"]) == 22
        assert float(good["free_cash_flow_margin"]) == round(22 / 130, 6)
        assert good["growth_acceleration_flag"] == "true"
        assert good["margin_expansion_flag"] == "true"
        assert good["positive_fcf_flag"] == "true"
        bad = next(r for r in rows if r["asset_id"] == "U00002")
        assert bad["feature_quality_status"] == "FEATURES_PARTIAL"
        rejections = read_rows(out1 / REJECTIONS)
        assert any(r["asset_id"] == "U00002" and r["reason"].startswith("missing_or_invalid") for r in rejections)
        assert payload["recommendations_generated"] is False
    print("PASS: v2.38G/builder/offline/deterministic/ratios-growth-fcf/rejections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
