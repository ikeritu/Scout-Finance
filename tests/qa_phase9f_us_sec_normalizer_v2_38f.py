#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/normalize_us_sec_fundamentals_v2_38f.py"
EXPECTED_ROWS = 9200


def write_readiness(path: Path, cik: str) -> None:
    fields = ["asset_id", "ticker", "company_name", "exchange", "cik", "enrichment_status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({
            "asset_id": "U00001",
            "ticker": "AAA",
            "company_name": "Alpha Analytics Inc.",
            "exchange": "NASDAQ",
            "cik": cik,
            "enrichment_status": "ENRICHED_SEC_READY",
        })
        for idx in range(2, EXPECTED_ROWS + 1):
            writer.writerow({
                "asset_id": f"U{idx:05d}",
                "ticker": f"T{idx}",
                "company_name": f"Company {idx}",
                "exchange": "NASDAQ",
                "cik": "",
                "enrichment_status": "SEC_NOT_ELIGIBLE",
            })


def write_companyfacts(path: Path) -> None:
    fact = {
        "fy": 2025,
        "fp": "FY",
        "form": "10-K",
        "filed": "2026-02-20",
        "end": "2025-12-31",
        "frame": "CY2025",
    }
    metrics = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": 150000000,
        "NetIncomeLoss": 18000000,
        "Assets": 400000000,
        "Liabilities": 120000000,
        "StockholdersEquity": 280000000,
        "NetCashProvidedByUsedInOperatingActivities": 35000000,
        "PaymentsToAcquirePropertyPlantAndEquipment": -9000000,
        "EarningsPerShareBasic": 1.25,
        "EarningsPerShareDiluted": 1.2,
    }
    payload = {"facts": {"us-gaap": {}}}
    for concept, value in metrics.items():
        unit = "USD/shares" if concept.startswith("EarningsPerShare") else "USD"
        payload["facts"]["us-gaap"][concept] = {"units": {unit: [dict(fact, val=value)]}}
    path.write_text(json.dumps(payload), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        cache = base / "cache"
        out = base / "out"
        readiness = base / "readiness.csv"
        cik = "0000000001"
        (cache / "companyfacts").mkdir(parents=True)
        write_readiness(readiness, cik)
        write_companyfacts(cache / "companyfacts" / f"CIK{cik}.json")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--cache-dir", str(cache), "--readiness-path", str(readiness), "--output-dir", str(out)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["recommendations_generated"] is False
        report = json.loads((out / "us_sec_fundamental_aggregate_report_v2_38f.json").read_text(encoding="utf-8"))
        assert report["companies_processed"] == 1
        assert report["companies_normalized_ready"] == 1
        assert report["records_written"] == 9
        rows = [json.loads(line) for line in (out / "us_sec_fundamental_records_v2_38f.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 9
        assert {r["metric"] for r in rows} == set(json.loads((ROOT / "config/us_sec_fundamental_normalization_contract_v1.json").read_text(encoding="utf-8"))["allowed_metrics"])
        assert all(r["phase"] == "v2.38F" and r["taxonomy"] == "us-gaap" for r in rows)
        assert all(r["form"] == "10-K" and r["period_type"] == "annual" for r in rows)
        assert report["guardrails"]["network_calls"] == 0
        assert report["guardrails"]["scoring_calculated"] is False
        assert report["guardrails"]["ranking_calculated"] is False
        assert report["guardrails"]["recommendations_generated"] is False
    print("PASS: v2.38F/normalizer/offline/companyfacts-to-jsonl/traceable/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
