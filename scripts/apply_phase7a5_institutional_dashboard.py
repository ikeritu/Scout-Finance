
from __future__ import annotations

import ast
import py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app.py"
BACKUP_PATH = PROJECT_ROOT / "app_before_phase7a5.py"

PHASE7A5_FUNCTIONS = """
def _sf7a5_build_institutional_universe_summary() -> dict:
    scouting_dir = _sf5g_project_root() / "outputs" / "scouting"

    cleaning_summary = _sf5h_read_json(scouting_dir / "universe_cleaning_summary.json")
    comparison_report = _sf5h_read_json(scouting_dir / "institutional_cleaning_comparison_report.json")

    metrics = comparison_report.get("metrics", {}) if comparison_report else {}
    pre = metrics.get("pre_cleaning", {})
    post = metrics.get("post_cleaning", {})

    return {
        "cleaning_available": bool(cleaning_summary),
        "comparison_available": bool(comparison_report),
        "input_rows": cleaning_summary.get("input_rows", 0) if cleaning_summary else 0,
        "clean_rows": cleaning_summary.get("clean_rows", 0) if cleaning_summary else 0,
        "excluded_rows": cleaning_summary.get("excluded_rows", 0) if cleaning_summary else 0,
        "clean_rate_percent": cleaning_summary.get("clean_rate_percent", 0) if cleaning_summary else 0,
        "excluded_rate_percent": cleaning_summary.get("excluded_rate_percent", 0) if cleaning_summary else 0,
        "clean_distribution": cleaning_summary.get("clean_distribution", {}) if cleaning_summary else {},
        "excluded_distribution": cleaning_summary.get("excluded_distribution", {}) if cleaning_summary else {},
        "market_data_success_pre": pre.get("market_data_success_rate_percent", 0),
        "market_data_success_post": post.get("market_data_success_rate_percent", 0),
        "market_data_success_delta": metrics.get("market_data_success_rate_delta_points", 0),
        "stage1_pass_pre": pre.get("stage1_pass_rate_percent", 0),
        "stage1_pass_post": post.get("stage1_pass_rate_percent", 0),
        "stage1_pass_delta": metrics.get("stage1_pass_rate_delta_points", 0),
        "stage1_rejection_pre": pre.get("stage1_rejection_rate_percent", 0),
        "stage1_rejection_post": post.get("stage1_rejection_rate_percent", 0),
        "stage1_rejection_delta": metrics.get("stage1_rejection_rate_delta_points", 0),
        "openai_called": comparison_report.get("openai_called", False) if comparison_report else False,
        "paid_api_called": comparison_report.get("paid_api_called", False) if comparison_report else False,
        "yfinance_called": comparison_report.get("yfinance_called", False) if comparison_report else False,
        "app_modified_by_report": comparison_report.get("app_modified", False) if comparison_report else False,
    }


def _render_institutional_universe_dashboard() -> None:
    st.markdown("### 🏦 Universo institucional")
    st.caption(
        "Capa profesional de limpieza de universo: separa instrumentos fuera de alcance "
        "antes de enriquecer market data y antes de Stage 1."
    )

    summary = _sf7a5_build_institutional_universe_summary()

    if not summary.get("cleaning_available"):
        st.warning(
            "No se encuentra `universe_cleaning_summary.json`. "
            "Ejecuta `python -m src.clean_universe_institutional`."
        )
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Universo bruto", summary.get("input_rows", 0))
    col2.metric("Universo limpio", summary.get("clean_rows", 0))
    col3.metric("Excluidos", summary.get("excluded_rows", 0))
    col4.metric("Excluded rate", f"{summary.get('excluded_rate_percent', 0)}%")

    st.success(
        "Limpieza institucional activa: warrants, rights, units, preferred, deuda, fondos, "
        "ETNs y SPACs quedan fuera del universo inicial antes de Stage 1."
    )

    col_a, col_b, col_c = st.columns(3)
    col_a.metric(
        "Market data success",
        f"{summary.get('market_data_success_post', 0)}%",
        f"{summary.get('market_data_success_delta', 0)} pts",
    )
    col_b.metric(
        "Stage 1 pass rate",
        f"{summary.get('stage1_pass_post', 0)}%",
        f"{summary.get('stage1_pass_delta', 0)} pts",
    )
    col_c.metric(
        "Stage 1 rejection rate",
        f"{summary.get('stage1_rejection_post', 0)}%",
        f"{summary.get('stage1_rejection_delta', 0)} pts",
    )

    excluded_distribution = summary.get("excluded_distribution", {})
    clean_distribution = summary.get("clean_distribution", {})

    left, right = st.columns(2)

    with left:
        st.markdown("#### Distribución universo limpio")
        if clean_distribution:
            clean_df = pd.DataFrame(
                [{"Instrumento": key, "Count": value} for key, value in clean_distribution.items()]
            )
            st.dataframe(clean_df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay distribución limpia disponible.")

    with right:
        st.markdown("#### Instrumentos excluidos")
        if excluded_distribution:
            excluded_df = pd.DataFrame(
                [{"Instrumento": key, "Count": value} for key, value in excluded_distribution.items()]
            ).sort_values("Count", ascending=False)
            st.dataframe(excluded_df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay instrumentos excluidos.")

    with st.expander("Ver lectura profesional del cambio", expanded=False):
        st.markdown(
            "**Interpretación institucional**\n\n"
            "La limpieza de universo no es un filtro financiero. Es una capa previa de definición "
            "del universo invertible. Esto evita que warrants, rights, units, preferreds o SPACs "
            "sean tratados como empresas rechazadas por métricas financieras.\n\n"
            "**Antes:** Stage 1 mezclaba ruido instrumental con empresas analizables.\n\n"
            "**Ahora:** Stage 1 trabaja sobre un universo más limpio, auditable y defendible."
        )

        detail_df = pd.DataFrame(
            [
                {"Control": "Cleaning summary disponible", "Valor": summary.get("cleaning_available")},
                {"Control": "Comparison report disponible", "Valor": summary.get("comparison_available")},
                {"Control": "OpenAI llamado en informe", "Valor": summary.get("openai_called")},
                {"Control": "API de pago llamada en informe", "Valor": summary.get("paid_api_called")},
                {"Control": "yfinance llamado en informe", "Valor": summary.get("yfinance_called")},
                {"Control": "app.py modificado por informe", "Valor": summary.get("app_modified_by_report")},
            ]
        )
        st.dataframe(detail_df, use_container_width=True, hide_index=True)

    st.markdown(
        "`Universo bruto` → `Institutional Universe Cleaning` → "
        "`Universo limpio` → `Market data enrichment` → `Stage 1 liquidity & investability`"
    )

"""


def main() -> int:
    print("Scout Finance — Phase 7A.5 apply institutional universe dashboard")
    print("=" * 74)

    if not APP_PATH.exists():
        print(f"FAIL app.py not found: {APP_PATH}")
        return 1

    original = APP_PATH.read_text(encoding="utf-8", errors="replace")
    content = original

    if "_render_institutional_universe_dashboard" in content:
        print("OK   Phase 7A.5 functions already present in app.py")
    else:
        main_idx = content.find("def main() -> None:")
        if main_idx == -1:
            print("FAIL Could not find `def main() -> None:` in app.py")
            return 1

        content = content[:main_idx] + PHASE7A5_FUNCTIONS + "\n" + content[main_idx:]

        if not BACKUP_PATH.exists():
            BACKUP_PATH.write_text(original, encoding="utf-8")
            print(f"OK   Backup created: {BACKUP_PATH}")
        else:
            print(f"OK   Backup already exists: {BACKUP_PATH}")

    if "_render_institutional_universe_dashboard()" not in content:
        target = "        _render_fundamental_enrichment_dashboard()\n"
        replacement = (
            "        _render_fundamental_enrichment_dashboard()\n"
            "        st.divider()\n"
            "        _render_institutional_universe_dashboard()\n"
        )

        if target not in content:
            print("FAIL Could not find Phase 6F dashboard render call.")
            print("Expected marker: _render_fundamental_enrichment_dashboard()")
            return 1

        content = content.replace(target, replacement, 1)
        print("OK   Phase 7A.5 dashboard render call inserted")
    else:
        print("OK   Phase 7A.5 dashboard render call already present")

    APP_PATH.write_text(content, encoding="utf-8")

    try:
        py_compile.compile(str(APP_PATH), doraise=True)
        ast.parse(APP_PATH.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        print(f"FAIL app.py validation failed after patch: {exc}")
        return 1

    print("OK   app.py compiles after Phase 7A.5 patch")
    print("OK   No OpenAI/API/yfinance call performed")
    print("OK   releases/v0.6 not modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
