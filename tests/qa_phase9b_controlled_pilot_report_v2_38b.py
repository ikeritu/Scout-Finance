#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_phase9b_controlled_pilot_report_v2_38b.py"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def write_price(path: Path, pilot_id: str, row: dict) -> None:
    path.write_text(json.dumps({"pilot": {"pilot_id": pilot_id}, "prices": [row]}) + "\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        overlay = [{"asset_id": f"U{i:05d}", "ticker": str(i), "exchange": "JPX", "provider_symbol": f"{i}0", "resolution_status": "EXACT_COMPANY_NAME_MATCH", "evidence_source": "J-Quants equities master"} for i in range(1, 26)]
        twse = [{"pilot_id": f"U{i:05d}", "ticker": f"{i}.TW", "company_name": "fixture", "exchange": "TWSE", "provider_symbol": str(i)} for i in range(101, 126)]
        write_csv(base / "jpx_symbol_resolution_overlay_25_v2_38b.csv", overlay)
        write_csv(base / "twse_collection_pilot_25_v2_38b.csv", twse)
        jpx_dir = base / "jpx_price_pilot_25_results_v2_38b"; jpx_dir.mkdir()
        twse_dir = base / "twse_collection_pilot_25_results_v2_38b"; twse_dir.mkdir()
        for row in overlay:
            write_price(jpx_dir / f"{row['asset_id']}.json", row["asset_id"], {"Date": "2026-01-02", "Code": row["provider_symbol"], "O": 1, "H": 1, "L": 1, "C": 1, "Vo": 1})
        for row in twse:
            write_price(twse_dir / f"{row['pilot_id']}.json", row["pilot_id"], {"Date": "2026-01-02", "Open": 1, "High": 1, "Low": 1, "Close": 1, "Volume_shares": 1})
        output = base / "report.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "--base", str(base), "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["totals"] == {"assets": 50, "invalid_assets": 0, "price_rows": 50}
        assert report["status"] == "CONTROLLED_PILOT_VALIDATED_NOT_GLOBAL_PROMOTION"
        assert report["markets"]["TWSE"]["adjusted_prices"] is False
        assert report["guardrails"]["phase9c_authorized"] is False
        (jpx_dir / "U00001.json").unlink()
        blocked = subprocess.run([sys.executable, str(SCRIPT), "--base", str(base), "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
        assert blocked.returncode == 2 and json.loads(blocked.stdout)["status"] == "BLOCKED"
    print("PASS: v2.38B controlled-pilot/aggregate-only/identity/schema/fail-closed/no-phase9c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
