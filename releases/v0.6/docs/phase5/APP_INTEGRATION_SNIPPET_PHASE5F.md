# App integration snippet — Phase 5F

This snippet can be added later to `app.py` inside a new tab or inside the existing Ranking/Dashboard section.

It is intentionally isolated and does not call OpenAI.

```python
from src.scouting_candidates import (
    build_scouting_candidates_summary,
    load_scouting_candidates,
    prepare_candidates_display_df,
)


def _render_stage3_candidates_tab() -> None:
    st.subheader("🧭 Candidatos Stage 3")
    st.caption(
        "Candidatas generadas por el embudo global. "
        "No llama a OpenAI y no sustituye el modo demo actual."
    )

    summary = build_scouting_candidates_summary()

    if not summary.get("available"):
        st.info(
            "No hay candidatos Stage 3 disponibles todavía. "
            "Ejecuta Fase 5E para generar outputs/scouting/top_100_candidates.csv."
        )
        return

    col1, col2, col3 = st.columns(3)

    files = summary.get("files", {})
    col1.metric("Top 20", files.get("Top 20 — Deep research", {}).get("rows", 0))
    col2.metric("Top 50", files.get("Top 50 — Watchlist", {}).get("rows", 0))
    col3.metric("Top 100", files.get("Top 100 — Candidates", {}).get("rows", 0))

    top_company = summary.get("top_company")
    if top_company:
        st.success(
            f"Mejor candidata Stage 3: "
            f"{top_company.get('ticker')} — "
            f"{top_company.get('final_stage3_score')} puntos — "
            f"{top_company.get('stage3_category')}"
        )

    df = load_scouting_candidates(limit=100)
    display_df = prepare_candidates_display_df(df)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv_bytes = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar candidatos Stage 3",
        data=csv_bytes,
        file_name="stage3_candidates_display.csv",
        mime="text/csv",
        use_container_width=True,
    )
```

Suggested placement:
- Preferred: new tab `Candidatos Stage 3`
- Alternative: inside existing `Ranking`
- Do not remove the existing demo/ranking flow yet.
