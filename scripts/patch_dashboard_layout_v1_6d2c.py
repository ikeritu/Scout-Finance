from __future__ import annotations

from pathlib import Path


APP = Path("app.py")

OLD = '''    with dashboard_tab:
        _render_dashboard_tab(mode, top_n)
        st.divider()
        _render_global_funnel_summary_dashboard()
        st.divider()
        _render_fundamental_enrichment_dashboard()
        st.divider()
        _render_institutional_universe_dashboard()
'''

NEW = '''    with dashboard_tab:
        _render_dashboard_tab(mode, top_n)

        with st.expander("Embudo global de scouting", expanded=False):
            _render_global_funnel_summary_dashboard()

        with st.expander("Cobertura de fundamentales", expanded=False):
            _render_fundamental_enrichment_dashboard()

        with st.expander("Universo institucional", expanded=False):
            _render_institutional_universe_dashboard()
'''


def main() -> int:
    text = APP.read_text(encoding="utf-8")

    marker = "# v1.6D2C dashboard layout consolidation packaged"
    if marker not in text:
        text = marker + "\n" + text

    if OLD not in text:
        raise SystemExit("Target dashboard block not found. No changes applied.")

    text = text.replace(OLD, NEW, 1)
    APP.write_text(text, encoding="utf-8")

    print("Scout Finance ? v1.6D2C Dashboard Layout Consolidation")
    print("=" * 92)
    print("OK   Dashboard secondary panels moved into collapsed expanders")
    print("OK   Main dashboard render remains first and unchanged")
    print("OK   No scoring/ranking logic changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
