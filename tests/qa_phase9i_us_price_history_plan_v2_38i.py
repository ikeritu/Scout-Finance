#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_us_price_history_acquisition_plan_v2_38i.py"


def write_features(path: Path) -> None:
    fields = ["asset_id", "ticker", "company_name", "exchange", "feature_quality_status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"asset_id": "U00003", "ticker": "CCC", "company_name": "Charlie Corp.", "exchange": "NYSE", "feature_quality_status": "FEATURES_PARTIAL"})
        writer.writerow({"asset_id": "U00001", "ticker": "AAA", "company_name": "Alpha Inc.", "exchange": "NASDAQ", "feature_quality_status": "FEATURES_READY"})
        writer.writerow({"asset_id": "U00002", "ticker": "BBB", "company_name": "Beta Inc.", "exchange": "NASDAQ", "feature_quality_status": "FEATURES_READY"})


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        features = base / "features.csv"
        out = base / "out"
        raw = base / "raw"
        raw.mkdir()
        write_features(features)
        (raw / "U00002.csv").write_text("date,close,adjusted_close,volume,provider,provider_symbol\n2026-01-01,10,10,100,twelvedata,BBB\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), "--features-path", str(features), "--output-dir", str(out), "--raw-cache", str(raw)], cwd=ROOT, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        rows = read_rows(out / "us_price_history_acquisition_plan_v2_38i.csv")
        assert [r["asset_id"] for r in rows] == ["U00001", "U00002", "U00003"]
        assert rows[0]["priority_bucket"] == "FEATURES_READY"
        assert rows[1]["acquisition_status"] == "LOCAL_PRICE_READY"
        assert len({r["asset_id"] for r in rows}) == 3
        assert payload["recommendations_generated"] is False
    print("PASS: v2.38I/plan/deterministic/priority/local-ready/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
