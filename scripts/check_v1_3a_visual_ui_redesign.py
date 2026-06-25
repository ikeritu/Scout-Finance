from __future__ import annotations

import py_compile
from pathlib import Path


def ok(msg: str) -> None:
    print("OK   " + msg)


def fail(msg: str) -> None:
    print("FAIL " + msg)
    raise SystemExit(1)


def require(condition: bool, msg: str) -> None:
    ok(msg) if condition else fail(msg)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    app_path = root / "app.py"
    config_path = root / ".streamlit" / "config.toml"

    print("Scout Finance — v1.3A Visual UI Redesign checker")
    print("=" * 92)

    require(app_path.exists(), f"File exists: {app_path}")
    text = app_path.read_text(encoding="utf-8")

    markers = [
        "v1.3 UI redesign",
        "v1.3A Visual UI Redesign packaged",
        "_inject_scout_theme",
        "--sf-primary",
        "font-family: 'Inter'",
        "_sf12a_load_revalidated_candidates",
        "phase7c4_pipeline_revalidation_top_candidates.csv",
        "_get_latest_final_view_df(mode=mode, top_n=top_n)",
        "_sf12a_render_fallback_notice(final_df, context=\"pestaña de ranking\")",
        "_sf12a_render_fallback_notice(final_df, context=\"ficha individual\")",
        "pueden no coincidir con las candidatas revalidadas",
        "PHASE 7D.1 DASHBOARD HOTFIX SUPERSEDED BY v1.2A",
        "if not _sf12a_disable_global_post_main_render():",
    ]

    for marker in markers:
        require(marker in text, f"app.py contains marker: {marker}")

    forbidden_old_ranking = """latest_run_id = get_latest_run_id(mode=mode)

    if latest_run_id is None:
        st.info("No hay datos para mostrar.")
        return pd.DataFrame()

    final_df = get_top_final_research_view(
        run_id=latest_run_id,
        mode=mode,
        top_n=top_n,
    )

    if final_df.empty:
        st.info("La vista final está vacía.")
        return final_df
"""
    require(forbidden_old_ranking not in text, "Ranking no longer uses old empty final-view-only source")

    require(config_path.exists(), f"File exists: {config_path}")
    config = config_path.read_text(encoding="utf-8")
    for marker in ["#0E7C86", "#F4F6F8", "primaryColor", "backgroundColor"]:
        require(marker in config, f"config.toml contains marker: {marker}")

    py_compile.compile(str(app_path), doraise=True)
    ok("app.py compiles")

    print()
    print("Result")
    print("-" * 92)
    print("OK   v1.3A Visual UI Redesign is valid")


if __name__ == "__main__":
    main()
