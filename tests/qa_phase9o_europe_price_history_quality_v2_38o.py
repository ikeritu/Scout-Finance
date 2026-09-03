#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_europe_price_history_acquisition_plan_v2_38o.py"
OUT = ROOT / "outputs/full_universe_source_acquisition/v2_38o_europe_price_history_acquisition"
SECRET_RE = re.compile(r"api[_-]?key\s*[:=]|refresh[_-]?token\s*[:=]|bearer\s+[a-z0-9]|authorization\s*[:=]|TWELVE_DATA_API_KEY\s*=|EODHD_API_KEY\s*=", re.I)
ACTION_RE = re.compile(r"\b(buy|sell|hold|price target|expected return|guaranteed|will rise)\b", re.I)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    plan = rows(OUT / "europe_price_history_acquisition_plan_v2_38o.csv")
    ledger = rows(OUT / "europe_price_history_batch_ledger_v2_38o.csv")
    report = json.loads((OUT / "europe_price_history_collection_report_v2_38o.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "europe_price_history_manifest_v2_38o.json").read_text(encoding="utf-8"))
    assert report["phase"] == "v2.38O-europe-price-history-acquisition"
    assert report["guardrails"]["network_calls"] == 0
    assert report["guardrails"]["cboe_europe_source_forbidden"] is True
    assert report["guardrails"]["scoring_calculated"] is False
    assert report["guardrails"]["ranking_calculated"] is False
    assert report["guardrails"]["recommendations_generated"] is False
    assert report["guardrails"]["phase9c_authorized"] is False
    assert report["raw_cache_published"] is False
    assert len(plan) == report["candidates_total"]
    assert isinstance(ledger, list)
    assert "europe_price_history_acquisition_plan_v2_38o.csv" in manifest["outputs"]
    assert "europe_price_history_collection_report_v2_38o.json" in manifest["outputs"]
    allowed_statuses = {
        "READY_FOR_COLLECTION",
        "COLLECTED",
        "BLOCKED_PROVIDER_UNSUPPORTED",
        "BLOCKED_CBOE_SECONDARY_SOURCE",
        "BLOCKED_CREDENTIAL_MISSING",
        "BLOCKED_NETWORK_ERROR",
        "BLOCKED_PROVIDER_ERROR",
        "BLOCKED_INSUFFICIENT_HISTORY",
        "SKIPPED_EXISTING_CACHE",
    }
    for row in plan:
        assert row["collection_status"] in allowed_statuses
        assert row["home_exchange"] != "CBOE_EUROPE"
        assert row["home_mic"] != ""
        assert row["provider_symbol"] != ""
        assert row["scoring_calculated"] == "false"
        assert row["ranking_calculated"] == "false"
        assert row["recommendations_generated"] == "false"
        assert row["phase9c_authorized"] == "false"
        assert not ACTION_RE.search(row["failure_reason"])
    for path in OUT.glob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert not SECRET_RE.search(text), path
    print("PASS: v2.38O/quality/manifest/no-secrets/no-cboe-primary/no-recommendations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
