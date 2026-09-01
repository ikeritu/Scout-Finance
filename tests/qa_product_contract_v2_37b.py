#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    contract = json.loads((ROOT / "config/product_ui_contract_v1.json").read_text(encoding="utf-8"))
    language = json.loads((ROOT / "config/product_language_policy_v1.json").read_text(encoding="utf-8"))
    assert contract["product_version"] == "v2.37"
    assert contract["canonical_entrypoint"] == "app_v2_37.py"
    assert contract["phase7_decision"] == "INSUFFICIENT_EVIDENCE"
    assert contract["main_ranking_markets"] == ["JPX"]
    assert contract["partial_markets"] == ["TWSE"]
    assert set(contract["review_required_assets"]) == {"P020", "P178"}
    for key in ("historically_validated_scoring", "investment_advice", "broker_integration", "automated_trading", "public_deployment_authorized", "network_calls_authorized"):
        assert contract[key] is False
    assert "no constituye asesoramiento financiero" in contract["required_disclaimer"].lower()
    all_text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8").lower()
        for path in ("app_v2_37.py", "src/ui_v2_37/ui.py", "src/ui_v2_37/reports.py")
    )
    assert language["required_context"].lower() in all_text
    for forbidden in ("oportunidad garantizada", "señal de compra", "rentabilidad asegurada"):
        assert forbidden not in all_text
    assert "yfinance" not in all_text and "requests.get" not in all_text and "urlopen" not in all_text
    app = (ROOT / "app_v2_37.py").read_text(encoding="utf-8")
    for screen in ("home", "universe", "ranking", "asset", "compare", "watchlist", "reports", "help"):
        assert f'"{screen}"' in app
    for polish_marker in ("Clasificable parcial", "Margen absoluto superior al 300 %", "Entidad financiera: requiere", "stack=False", 'placeholder="Todos"'):
        assert polish_marker in app
    assert '"N/D" if a.get("total_score") is None' in app
    assert "prefers-reduced-motion" in (ROOT / "src/ui_v2_37/ui.py").read_text(encoding="utf-8")
    assert "demo" not in app.lower()
    print("PASS: v2.37B product-contract/experimental-language/local-only/no-broker/no-network")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
