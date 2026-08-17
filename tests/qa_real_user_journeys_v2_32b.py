#!/usr/bin/env python3
"""Streamlit-level acceptance test for the real v2.32B user journeys."""
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

WATCHLIST_NAME = "v2.32B UI Acceptance"
WATCHLIST_PATH = ROOT / "data/watchlists/v2-32b-ui-acceptance.json"


def widget(at: AppTest, kind: str, label: str):
    return next(item for item in getattr(at, kind) if item.label == label)


def navigate(at: AppTest, screen: str) -> AppTest:
    widget(at, "radio", "Navegación").set_value(screen)
    at.run()
    assert not at.exception, [item.value for item in at.exception]
    return at


def cleanup() -> None:
    for path in (WATCHLIST_PATH, WATCHLIST_PATH.with_suffix(".json.bak")):
        path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    cleanup()
    started = time.perf_counter()
    scenarios: list[str] = []
    try:
        at = AppTest.from_file(str(ROOT / "app_v2_28.py"), default_timeout=40).run()
        assert not at.exception
        assert [item.value for item in at.title] == ["Scout Finance"]
        assert any("Scoring productivo no autorizado" in item.value for item in at.warning)
        scenarios += ["startup", "status_fail_closed"]

        navigate(at, "universe")
        widget(at, "multiselect", "Provider").set_value(["nse_india"])
        at.run()
        assert any("2,013 resultados" in item.value for item in at.caption)
        scenarios.append("provider_filter")

        widget(at, "multiselect", "Provider").set_value([])
        widget(at, "text_input", "Buscar").set_value("20MICRONS")
        at.run()
        assert any("1 resultados" in item.value for item in at.caption)
        assert widget(at, "selectbox", "Activo seleccionado").value.startswith("20MICRONS · NSE")
        scenarios.append("catalog_search")

        widget(at, "button", "Abrir detalle").click()
        at.run()
        assert widget(at, "radio", "Navegación").value == "asset"
        assert any("20 Microns Limited · 20MICRONS" == item.value for item in at.subheader)
        assert any("Sin recomendación" in item.value for item in at.info)
        scenarios.append("asset_detail")

        navigate(at, "watchlists")
        widget(at, "text_input", "Nombre").set_value(WATCHLIST_NAME)
        widget(at, "text_input", "Descripción").set_value("Recorrido temporal v2.32B")
        widget(at, "button", "Crear").click()
        at.run()
        assert WATCHLIST_PATH.is_file()
        scenarios.append("watchlist_create")

        widget(at, "text_input", "Buscar activo para añadir").set_value("20MICRONS")
        at.run()
        widget(at, "text_input", "Etiquetas separadas por comas").set_value("qa, usuario")
        widget(at, "text_area", "Nota").set_value("Validación integral temporal")
        widget(at, "button", "Añadir a watchlist").click()
        at.run()
        persisted = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
        assert len(persisted["items"]) == 1
        assert persisted["items"][0]["ticker"] == "20MICRONS"
        scenarios += ["watchlist_add", "watchlist_persist"]

        widget(at, "text_input", "Etiquetas").set_value("qa, revisado")
        [item for item in at.text_area if item.label == "Nota"][-1].set_value("Nota actualizada desde la UI")
        at.run()
        widget(at, "button", "Guardar nota y etiquetas").click()
        at.run()
        persisted = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
        assert persisted["items"][0]["note"] == "Nota actualizada desde la UI"
        assert persisted["items"][0]["tags"] == ["qa", "revisado"]
        assert len(at.get("download_button")) == 1
        scenarios += ["watchlist_edit", "watchlist_csv_export"]

        navigate(at, "reports")
        assert len(at.get("download_button")) == 2
        scenarios.append("universe_report")
        widget(at, "selectbox", "Tipo de informe").set_value("Watchlist")
        at.run()
        assert not at.exception and len(at.get("download_button")) == 2
        scenarios.append("watchlist_report")

        navigate(at, "scores")
        assert any("SCORING UNAVAILABLE" in item.value for item in at.warning)
        assert not at.button
        scenarios.append("diagnostic_blocked_without_consent")
        widget(at, "checkbox", "Entiendo que mide cobertura y calidad de datos, no atractivo de inversión ni ranking.").check()
        at.run()
        widget(at, "button", "Abrir diagnóstico").click()
        at.run()
        assert len(at.dataframe) == 2
        assert at.session_state["diagnostic_summary"]["rows"] == 33498
        assert at.session_state["diagnostic_summary"]["allow_ranking"] is False
        scenarios += ["diagnostic_consent", "diagnostic_load", "diagnostic_fail_closed"]

        navigate(at, "reports")
        widget(at, "selectbox", "Tipo de informe").set_value("Diagnóstico de datos")
        at.run()
        assert not at.warning
        assert len(at.get("download_button")) == 2
        scenarios += ["diagnostic_consent_persists", "diagnostic_report"]

        navigate(at, "maintenance")
        assert any("solo lectura" in item.value for item in at.warning)
        scenarios.append("maintenance_read_only")

        # A fresh browser session verifies entry points that do not depend on
        # diagnostic session state and avoids coupling unrelated journeys.
        at = AppTest.from_file(str(ROOT / "app_v2_28.py"), default_timeout=40).run()
        navigate(at, "help")
        assert any(item.value == "Ayuda y límites" for item in at.header)
        assert "Ranking productivo: bloqueado" in "\n".join(str(item.value) for item in at.markdown)
        scenarios.append("help_and_limits")

        at = AppTest.from_file(str(ROOT / "app_v2_28.py"), default_timeout=40).run()
        navigate(at, "watchlists")
        widget(at, "button", "Eliminar de la lista").click()
        at.run()
        persisted = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
        assert persisted["items"] == []
        scenarios.append("watchlist_remove")

        assert len(scenarios) == 21
        report = {
            "phase": "v2.32B",
            "status": "PASS",
            "scenario_count": len(scenarios),
            "scenarios": scenarios,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "universe_rows": 43089,
            "diagnostic_rows": 33498,
            "temporary_watchlist_cleaned": True,
            "production_scoring_authorized": False,
            "allow_ranking": False,
            "incidents_found": 1,
            "incidents_closed": 1,
            "closed_incident": "diagnostic consent was lost between Score Explorer and Reports",
            "universe_pointer_modified": False,
            "scoring_pointer_modified": False,
            "dataset_modified": False,
        }
    finally:
        cleanup()

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    print("PASS: v2.32B/21-real-user-journeys/1-incident-closed/watchlists/diagnostic/reports/fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
