"""QA for promoting Unicorns to a primary app screen."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app_v2_37.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_app_tree() -> ast.Module:
    return ast.parse(APP.read_text(encoding="utf-8"))


def find_screens(tree: ast.Module) -> dict[str, str]:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SCREENS":
                    require(isinstance(node.value, ast.Dict), "SCREENS must be a dict literal")
                    return {
                        key.value: value.value
                        for key, value in zip(node.value.keys, node.value.values)
                        if isinstance(key, ast.Constant) and isinstance(value, ast.Constant)
                    }
    raise AssertionError("SCREENS was not found")


def test_unicorns_is_primary_navigation_screen() -> None:
    screens = find_screens(read_app_tree())
    ordered_keys = list(screens)
    require("global_unicorns" in screens, "Unicorns screen missing from navigation")
    require(screens["global_unicorns"] == "🦄 Unicornios", "Unexpected Unicorns label")
    require(ordered_keys.index("global_unicorns") == 1, "Unicorns must be directly after Inicio")


def test_unicorns_has_dedicated_renderer_and_dispatch() -> None:
    source = APP.read_text(encoding="utf-8")
    require("def render_global_unicorns(" in source, "Dedicated Unicorns renderer missing")
    require("def explain_unicorn_reason(" in source, "Detailed Unicorns explanation helper missing")
    require("def unicorn_criterion_badges(" in source, "Unicorn criteria badges helper missing")
    require('"global_unicorns": render_global_unicorns' in source, "Unicorns renderer missing from dispatch")
    require('row.get("unicorn_status") == "EVALUATED_UNICORN"' in source, "Unicorns screen must filter evaluated unicorns")
    require("No constituye asesoramiento financiero" in source, "Unicorns screen must preserve no-advice language")
    require('height=620' in source, "Unicorns table must be scrollable instead of visually capped")
    require('on_select="rerun"' in source, "Unicorns table must support row selection when Streamlit allows it")
    require("Detalle del unicornio" in source, "Unicorns screen must expose per-company detail")
    require("Por qué es unicornio" in source, "Unicorns screen must explain why each company is a unicorn")
    require("motivo técnico original" in source, "Unicorns screen must preserve original technical traceability")
    require("Tarjetas visuales" in source, "Unicorns screen must provide visual cards mode")
    require("Tabla completa" in source, "Unicorns screen must preserve complete table mode")
    require("Criterios cumplidos" in source, "Unicorns screen must show criterion badges/details")
    require("selected_unicorn_asset_id" in source, "Unicorns screen must keep selected card detail state")
    require("def unicorn_sort_key(" in source, "Unicorns screen must provide deterministic sort modes")
    require("Ordenar por" in source, "Unicorns screen must expose sorting")
    require("Top países" in source and "Top bolsas" in source, "Unicorns screen must show top country/exchange summaries")
    require("Exportar unicornios filtrados" in source, "Unicorns screen must export filtered unicorns")
    require("Comparar 2-3" in source and "Comparador de unicornios" in source, "Unicorns screen must compare selected unicorns")
    require("scout_finance_unicornios_filtrados_v2_44e.csv" in source, "Unicorns export filename must be versioned")
    require("def unicorn_watchlist_asset(" in source, "Unicorns screen must map rows into watchlist assets")
    require("Añadir a watchlist" in source, "Unicorn cards must support adding to watchlist")
    require("Añadir este unicornio a watchlist" in source, "Unicorn detail must support adding to watchlist")
    require("blocked_message(\"Añadir unicornios a watchlist\")" in source, "Unicorn watchlist writes must respect safe demo mode")
    require("atomic_write(watchlist_path, watchlist_data)" in source, "Unicorn watchlist writes must be persisted atomically")
    require("def unicorn_probability(" in source, "Unicorns screen must expose an explainable unicorn probability helper")
    require('col.expander("Ver detalle")' in source, "Unicorn card detail must open inline instead of relying on hidden scroll state")
    require("Posibilidad de unicornio" in source, "Unicorn cards/details must show unicorn probability")
    require("confianza de clasificación" in source, "Unicorn probability must be framed as classification confidence")
    require("no es probabilidad de rentabilidad" in source, "Unicorn probability must not imply expected return")
    require("No es precio objetivo" in source or "no es precio objetivo" in source, "Unicorn probability must not imply a price target")
    require("def professional_unicorn_report(" in source, "Unicorns screen must generate a professional report")
    require("Generar informe profesional" in source, "Unicorns screen must expose a clickable professional report action")
    require("Informe profesional de unicornio" in source, "Unicorn report must have a professional title")
    require("Resumen ejecutivo" in source and "Revision manual recomendada" in source, "Unicorn report must include professional sections")
    require("Descargar informe Markdown" in source, "Unicorn report must be downloadable")
    require("Preparado para IA opcional futura" in source or "integración con IA queda preparada" in source, "Unicorn report must document optional future AI integration")
    require("sin llamadas externas" in source, "Unicorn report generation must remain offline in this phase")
    require("def unicorn_evidence_grade(" in source, "Unicorn cockpit must expose an evidence quality semaphore")
    require("Ranking interno de unicornios" in source, "Unicorn cockpit must expose internal unicorn ordering")
    require("Filtros rápidos" in source, "Unicorn cockpit must expose quick filters")
    require("def unicorn_radar_values(" in source, "Unicorn cockpit must expose radar evidence values")
    require("Notas personales" in source and "save_unicorn_notes" in source, "Unicorn cockpit must support local notes")
    require("Export pack investigación" in source, "Unicorn cockpit must export a research pack")
    require("Comparador profesional" in source, "Unicorn cockpit must include professional comparison")
    require("IA opcional para análisis extendido" in source, "Unicorn cockpit must prepare optional AI analysis without enabling network calls")


def main() -> None:
    test_unicorns_is_primary_navigation_screen()
    test_unicorns_has_dedicated_renderer_and_dispatch()
    print("v2.44B unicorns primary screen QA passed")


if __name__ == "__main__":
    main()
