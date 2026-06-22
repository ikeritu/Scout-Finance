from __future__ import annotations

import ast
import py_compile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
BACKUP_PATH = PROJECT_ROOT / "app_before_phase7a5.py"
BROKEN_BACKUP_PATH = PROJECT_ROOT / "app_broken_phase7a5_before_hotfix_7a5_2.py"

PHASE7A5_FUNCTIONS = '\ndef _sf7a5_build_institutional_universe_summary() -> dict:\n    scouting_dir = _sf5g_project_root() / "outputs" / "scouting"\n\n    cleaning_summary = _sf5h_read_json(scouting_dir / "universe_cleaning_summary.json")\n    comparison_report = _sf5h_read_json(scouting_dir / "institutional_cleaning_comparison_report.json")\n\n    metrics = comparison_report.get("metrics", {}) if comparison_report else {}\n    pre = metrics.get("pre_cleaning", {})\n    post = metrics.get("post_cleaning", {})\n\n    return {\n        "cleaning_available": bool(cleaning_summary),\n        "comparison_available": bool(comparison_report),\n        "input_rows": cleaning_summary.get("input_rows", 0) if cleaning_summary else 0,\n        "clean_rows": cleaning_summary.get("clean_rows", 0) if cleaning_summary else 0,\n        "excluded_rows": cleaning_summary.get("excluded_rows", 0) if cleaning_summary else 0,\n        "clean_rate_percent": cleaning_summary.get("clean_rate_percent", 0) if cleaning_summary else 0,\n        "excluded_rate_percent": cleaning_summary.get("excluded_rate_percent", 0) if cleaning_summary else 0,\n        "clean_distribution": cleaning_summary.get("clean_distribution", {}) if cleaning_summary else {},\n        "excluded_distribution": cleaning_summary.get("excluded_distribution", {}) if cleaning_summary else {},\n        "market_data_success_pre": pre.get("market_data_success_rate_percent", 0),\n        "market_data_success_post": post.get("market_data_success_rate_percent", 0),\n        "market_data_success_delta": metrics.get("market_data_success_rate_delta_points", 0),\n        "stage1_pass_pre": pre.get("stage1_pass_rate_percent", 0),\n        "stage1_pass_post": post.get("stage1_pass_rate_percent", 0),\n        "stage1_pass_delta": metrics.get("stage1_pass_rate_delta_points", 0),\n        "stage1_rejection_pre": pre.get("stage1_rejection_rate_percent", 0),\n        "stage1_rejection_post": post.get("stage1_rejection_rate_percent", 0),\n        "stage1_rejection_delta": metrics.get("stage1_rejection_rate_delta_points", 0),\n        "openai_called": comparison_report.get("openai_called", False) if comparison_report else False,\n        "paid_api_called": comparison_report.get("paid_api_called", False) if comparison_report else False,\n        "yfinance_called": comparison_report.get("yfinance_called", False) if comparison_report else False,\n        "app_modified_by_report": comparison_report.get("app_modified", False) if comparison_report else False,\n    }\n\n\ndef _render_institutional_universe_dashboard() -> None:\n    st.markdown("### 🏦 Universo institucional")\n    st.caption(\n        "Capa profesional de limpieza de universo: separa instrumentos fuera de alcance "\n        "antes de enriquecer market data y antes de Stage 1."\n    )\n\n    summary = _sf7a5_build_institutional_universe_summary()\n\n    if not summary.get("cleaning_available"):\n        st.warning(\n            "No se encuentra `universe_cleaning_summary.json`. "\n            "Ejecuta `python -m src.clean_universe_institutional`."\n        )\n        return\n\n    col1, col2, col3, col4 = st.columns(4)\n    col1.metric("Universo bruto", summary.get("input_rows", 0))\n    col2.metric("Universo limpio", summary.get("clean_rows", 0))\n    col3.metric("Excluidos", summary.get("excluded_rows", 0))\n    col4.metric("Excluded rate", f"{summary.get(\'excluded_rate_percent\', 0)}%")\n\n    st.success(\n        "Limpieza institucional activa: warrants, rights, units, preferred, deuda, fondos, "\n        "ETNs y SPACs quedan fuera del universo inicial antes de Stage 1."\n    )\n\n    col_a, col_b, col_c = st.columns(3)\n    col_a.metric(\n        "Market data success",\n        f"{summary.get(\'market_data_success_post\', 0)}%",\n        f"{summary.get(\'market_data_success_delta\', 0)} pts",\n    )\n    col_b.metric(\n        "Stage 1 pass rate",\n        f"{summary.get(\'stage1_pass_post\', 0)}%",\n        f"{summary.get(\'stage1_pass_delta\', 0)} pts",\n    )\n    col_c.metric(\n        "Stage 1 rejection rate",\n        f"{summary.get(\'stage1_rejection_post\', 0)}%",\n        f"{summary.get(\'stage1_rejection_delta\', 0)} pts",\n    )\n\n    left, right = st.columns(2)\n\n    with left:\n        st.markdown("#### Distribución universo limpio")\n        clean_distribution = summary.get("clean_distribution", {})\n        if clean_distribution:\n            clean_df = pd.DataFrame(\n                [{"Instrumento": key, "Count": value} for key, value in clean_distribution.items()]\n            )\n            st.dataframe(clean_df, use_container_width=True, hide_index=True)\n        else:\n            st.info("No hay distribución limpia disponible.")\n\n    with right:\n        st.markdown("#### Instrumentos excluidos")\n        excluded_distribution = summary.get("excluded_distribution", {})\n        if excluded_distribution:\n            excluded_df = pd.DataFrame(\n                [{"Instrumento": key, "Count": value} for key, value in excluded_distribution.items()]\n            ).sort_values("Count", ascending=False)\n            st.dataframe(excluded_df, use_container_width=True, hide_index=True)\n        else:\n            st.info("No hay instrumentos excluidos.")\n\n    with st.expander("Ver lectura profesional del cambio", expanded=False):\n        professional_note = (\n            "**Interpretación institucional**\\\\n\\\\n"\n            "La limpieza de universo no es un filtro financiero. Es una capa previa de definición "\n            "del universo invertible. Esto evita que warrants, rights, units, preferreds o SPACs "\n            "sean tratados como empresas rechazadas por métricas financieras.\\\\n\\\\n"\n            "**Antes:** Stage 1 mezclaba ruido instrumental con empresas analizables.\\\\n\\\\n"\n            "**Ahora:** Stage 1 trabaja sobre un universo más limpio, auditable y defendible."\n        )\n        st.markdown(professional_note)\n\n        detail_df = pd.DataFrame(\n            [\n                {"Control": "Cleaning summary disponible", "Valor": summary.get("cleaning_available")},\n                {"Control": "Comparison report disponible", "Valor": summary.get("comparison_available")},\n                {"Control": "OpenAI llamado en informe", "Valor": summary.get("openai_called")},\n                {"Control": "API de pago llamada en informe", "Valor": summary.get("paid_api_called")},\n                {"Control": "yfinance llamado en informe", "Valor": summary.get("yfinance_called")},\n                {"Control": "app.py modificado por informe", "Valor": summary.get("app_modified_by_report")},\n            ]\n        )\n        st.dataframe(detail_df, use_container_width=True, hide_index=True)\n\n    st.markdown(\n        "`Universo bruto` → `Institutional Universe Cleaning` → "\n        "`Universo limpio` → `Market data enrichment` → `Stage 1 liquidity & investability`"\n    )\n\n'


def _compile_status(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _remove_existing_phase7a5(content: str) -> str:
    start = content.find("def _sf7a5_build_institutional_universe_summary")
    end = content.find("def main() -> None:")

    if start != -1 and end != -1 and start < end:
        content = content[:start] + content[end:]

    content = content.replace(
        "        st.divider()\n        _render_institutional_universe_dashboard()\n",
        "",
    )
    return content


def main() -> int:
    print("Scout Finance — Phase 7A.5.2 dashboard hotfix")
    print("=" * 70)

    if not APP_PATH.exists():
        print(f"FAIL app.py not found: {APP_PATH}")
        return 1

    compiles, error = _compile_status(APP_PATH)

    if not compiles:
        print(f"WARN app.py currently broken: {error}")

        if not BACKUP_PATH.exists():
            print(f"FAIL Backup not found: {BACKUP_PATH}")
            print("Manual recovery needed from app_v0_6_stable.py or releases/v0.6/app.py")
            return 1

        shutil.copy2(APP_PATH, BROKEN_BACKUP_PATH)
        shutil.copy2(BACKUP_PATH, APP_PATH)
        print(f"OK   Broken app backed up to: {BROKEN_BACKUP_PATH}")
        print(f"OK   app.py restored from: {BACKUP_PATH}")
    else:
        print("OK   app.py compiles before patch")

    content = APP_PATH.read_text(encoding="utf-8", errors="replace")
    content = _remove_existing_phase7a5(content)

    main_idx = content.find("def main() -> None:")
    if main_idx == -1:
        print("FAIL Could not find `def main() -> None:`")
        return 1

    content = content[:main_idx] + PHASE7A5_FUNCTIONS + "\n" + content[main_idx:]

    target = "        _render_fundamental_enrichment_dashboard()\n"
    replacement = (
        "        _render_fundamental_enrichment_dashboard()\n"
        "        st.divider()\n"
        "        _render_institutional_universe_dashboard()\n"
    )

    if target not in content:
        print("FAIL Could not find `_render_fundamental_enrichment_dashboard()` in Dashboard tab")
        return 1

    content = content.replace(target, replacement, 1)
    APP_PATH.write_text(content, encoding="utf-8")

    compiles, error = _compile_status(APP_PATH)
    if not compiles:
        print(f"FAIL app.py still broken after hotfix: {error}")
        return 1

    print("OK   Phase 7A.5 dashboard inserted")
    print("OK   app.py compiles after hotfix")
    print("OK   No OpenAI/API/yfinance call performed")
    print("OK   releases/v0.6 not modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
