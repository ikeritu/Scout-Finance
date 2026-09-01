#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_v2_37.reports import DISCLAIMER, asset_markdown, manifest, ranking_markdown, to_html, watchlist_markdown
from src.ui_v2_37.watchlists import add, create, export_csv, import_json_bytes, read, remove, update


def main() -> int:
    asset = {"asset_id": "P155", "ticker": "4040", "company_name": "Example", "market": "JPX", "eligibility_status": "ELIGIBLE_PARTIAL", "confidence": "HIGH", "total_score": 73.19, "rank": 1, "pillar_scores": {"quality": 80.0}}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path, watchlist = create(root, "Mi análisis", "Privada")
        add(watchlist, asset, note="=unsafe")
        update(watchlist, "P155", "REVIEW_LATER", "revisar publicación")
        from src.ui_v2_37.watchlists import atomic_write
        atomic_write(path, watchlist)
        loaded = read(path)
        assert loaded["items"][0]["research_status"] == "REVIEW_LATER"
        assert b"'=unsafe" not in export_csv(loaded) and b"revisar publicaci" in export_csv(loaded)
        imported = import_json_bytes(json.dumps(loaded, ensure_ascii=False).encode())
        assert imported["watchlist_id"] == loaded["watchlist_id"]
        for forbidden in ("allocation", "target_price", "broker_order"):
            assert forbidden not in json.dumps(imported)
        assert DISCLAIMER in asset_markdown(asset, "2026-08-31")
        assert DISCLAIMER in ranking_markdown([asset], "2026-08-31")
        assert DISCLAIMER in watchlist_markdown(loaded, "2026-08-31")
        html = to_html(asset_markdown(asset, "2026-08-31"))
        assert b"<!doctype html>" in html and b"asesoramiento financiero" in html
        report_manifest = json.loads(manifest("asset", "2026-08-31"))
        assert report_manifest["phase7_decision"] == "INSUFFICIENT_EVIDENCE"
        assert report_manifest["historically_validated_scoring"] is False and report_manifest["broker_action"] is False
        remove(loaded, "P155"); assert not loaded["items"]
    print("PASS: v2.37 watchlists/reports/atomic/private/no-trading-fields/mandatory-disclaimer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
