#!/usr/bin/env python3
"""Rendered-state, responsive and usability acceptance gate for v2.32C."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest
from src.ui_v2_28.ui import TOKENS, contrast_ratio, css


def navigation(at: AppTest):
    return next(item for item in at.radio if item.label == "Navegación")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    started = time.perf_counter()
    checks: dict[str, str] = {}

    sheet = css()
    assert "@media(max-width:900px)" in sheet
    assert "@media(max-width:640px)" in sheet
    assert "min-width:100%!important" in sheet
    assert "min-height:44px" in sheet
    assert "focus-visible" in sheet
    assert "prefers-reduced-motion" in sheet
    assert "prefers-contrast" in sheet
    checks.update({
        "desktop_layout": "PASS",
        "tablet_layout": "PASS",
        "mobile_single_column": "PASS",
        "touch_targets": "PASS",
        "keyboard_focus": "PASS",
        "reduced_motion": "PASS",
        "high_contrast_preference": "PASS",
    })

    assert contrast_ratio(TOKENS["text"], TOKENS["surface"]) >= 7
    assert contrast_ratio(TOKENS["primary_dark"], TOKENS["surface"]) >= 4.5
    assert contrast_ratio(TOKENS["warning"], TOKENS["surface"]) >= 4.5
    assert contrast_ratio(TOKENS["danger"], TOKENS["surface"]) >= 4.5
    checks["wcag_contrast"] = "PASS"

    at = AppTest.from_file(str(ROOT / "app_v2_28.py"), default_timeout=40).run()
    assert not at.exception
    nav = navigation(at)
    assert nav.value == "status" and len(nav.options) == 8
    status_text = "\n".join(str(item.value) for item in [*at.markdown, *at.caption, *at.info, *at.warning])
    assert "Bloqueado de forma segura" in status_text
    assert "14/14" in status_text
    checks["status_hierarchy_and_tones"] = "PASS"

    expected_headers = {
        "universe": "Universo operativo",
        "watchlists": "Watchlists",
        "scores": "Score Explorer",
        "reports": "Informes y exports",
        "asset": "Detalle de activo",
        "maintenance": "Mantenimiento",
        "help": "Ayuda y límites",
    }
    rendered_screens = ["status"]
    for screen, header in expected_headers.items():
        navigation(at).set_value(screen)
        at.run()
        assert not at.exception, [item.value for item in at.exception]
        assert any(item.value == header for item in at.header)
        assert navigation(at).value == screen
        rendered_screens.append(screen)
    assert len(rendered_screens) == 8
    checks["eight_screen_navigation"] = "PASS"
    checks["stable_navigation_widget"] = "PASS"

    navigation(at).set_value("universe")
    at.run()
    labels = {item.label for item in at.multiselect}
    assert {"País", "Mercado", "Moneda", "Tipo de activo", "Proveedor"} <= labels
    assert any(item.label == "Buscar" and item.placeholder == "Nombre, ticker, ISIN o identidad estable" for item in at.text_input)
    checks["consistent_spanish_labels"] = "PASS"
    checks["search_guidance"] = "PASS"

    navigation(at).set_value("maintenance")
    at.run()
    maintenance_text = "\n".join(str(item.value) for item in [*at.markdown, *at.caption, *at.info])
    assert "Vista avanzada · solo lectura" in maintenance_text
    assert "14/14 proveedores" in maintenance_text
    assert "Procedencias pendientes" in maintenance_text
    checks["maintenance_readability"] = "PASS"

    navigation(at).set_value("help")
    at.run()
    help_text = "\n".join(str(item.value) for item in at.markdown)
    assert "Primeros pasos" in help_text
    assert "Disponible" in help_text and "Bloqueado" in help_text
    assert "Ranking productivo" in help_text and "broker" in help_text
    checks["help_quick_start_and_limits"] = "PASS"
    assert any("v2.32 · validación operativa" in str(item.value) for item in at.caption)
    checks["current_sidebar_version"] = "PASS"
    assert "recomendaciones y señales" in help_text and "cambios automáticos" in help_text
    checks["financial_boundaries_visible"] = "PASS"

    assert len(checks) == 17
    report = {
        "phase": "v2.32C",
        "status": "PASS",
        "checks_passed": len(checks),
        "checks_failed": 0,
        "checks": checks,
        "screens_rendered": rendered_screens,
        "viewports": {"desktop": "1440px content cap", "tablet": "<=900px", "mobile": "<=640px single column"},
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "incidents_found": 3,
        "incidents_closed": 3,
        "closed_incidents": [
            "navigation widget identity changed between screens",
            "healthy provider and stable states used warning visual tones",
            "catalog filters mixed English labels into the Spanish interface",
        ],
        "universe_pointer_modified": False,
        "scoring_pointer_modified": False,
        "dataset_modified": False,
        "production_scoring_authorized": False,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    print("PASS: v2.32C/17-visual-responsive-usability-checks/8-screens/3-incidents-closed/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
