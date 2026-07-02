# Scout Finance — v1.6D1A App.py Dead-Code Audit

## Scope

- File: `D:\Proyectos\💰 Scout Finance\app.py`
- Total lines: 8042
- Functions found: 214

## Important note

This is a static audit. `unused_candidates` are not automatically safe to delete.
Streamlit callbacks, dynamic dispatch, and helper references can produce false positives.

## main()

- `main()` line: 7981

## Top-level executable statements outside function definitions

- Line 27: `'\nStreamlit app.\n\nPrivate MVP interface for the equity research assistant.\n\nCurrent scope:\n- Password-protected private interface.\n- Demo/real mode selec`
- Line 99: `APP_TITLE = 'Scout Finance — Private Research MVP'`
- Line 100: `DEFAULT_TOP_N = 20`
- Line 103: `CATEGORY_LABELS = {'high_priority_research': 'Alta prioridad', 'medium_priority_research': 'Media prioridad', 'watchlist': 'Watchlist', 'low_priority': 'Baja pr`
- Line 114: `FEEDBACK_LABELS = {'interesting': 'Interesante', 'discard': 'Descartar', 'review_later': 'Revisar después', 'false_positive': 'Falso positivo', 'needs_more_rese`
- Line 126: `st.set_page_config(page_title=APP_TITLE, page_icon='📊', layout='wide')`
- Line 435: `_inject_scout_theme()`

## Functions defined after main()

- None detected.

## Unused function candidates

- Line 450: `_render_login()`
- Line 605: `_short_openai_reason()`
- Line 743: `_render_faq_main()`
- Line 2517: `_sf15a_render_local_scoring_panel()`
- Line 2579: `_sf15b_render_explainability_panel()`
- Line 2634: `_sf15b_render_explainability_block()`
- Line 2720: `_sf15d_badge_summary()`
- Line 2742: `_sf15d_render_explainability_block()`
- Line 2786: `_sf15d_render_ux_polish_panel()`
- Line 2827: `_sf15d2_human_category()`
- Line 2833: `_sf15d2_human_status()`
- Line 2839: `_sf15d2_human_provider()`
- Line 2845: `_sf15d2_render_company_explainability()`
- Line 3080: `_sf16b_fundamentals_status_for_ticker()`
- Line 3134: `_sf16c1_active_score()`
- Line 3138: `_sf16c1_active_reason()`
- Line 3152: `_sf16c1_display_score()`
- Line 3159: `_sf16c1_human_category()`
- Line 3178: `_sf16c1_human_status()`
- Line 3239: `_sf16c2_display_score()`
- Line 3262: `_sf16c4_active_reason()`
- Line 3279: `_sf16c4_active_source_label()`
- Line 3301: `_sf16c4_is_combined_active()`
- Line 4407: `_shorten_ai_state()`
- Line 4523: `_sf16c_render_combined_scoring_panel()`
- Line 4546: `_sf16c_human_category()`
- Line 4561: `_sf16c_human_status()`
- Line 4774: `_render_final_view()`
- Line 5192: `_sf12a_disable_global_post_main_render()`
- Line 5465: `_sf14b_render_real_universe_panel()`
- Line 5555: `_sf14c_render_real_candidates_panel()`
- Line 5589: `_sf14c1_is_input_only_row()`
- Line 5606: `_sf14c1_input_only_caption()`
- Line 5644: `_sf14d_render_scoring_bridge_panel()`
- Line 5702: `_sf14d1_display_metric_value()`
- Line 5744: `_sf14e_render_market_data_panel()`
- Line 5929: `_sf_exec_best_company_label()`
- Line 6118: `_sf16c5_source_card_label()`
- Line 6131: `_sf16c5_render_dashboard_combined_notice()`
- Line 6735: `_render_history_technical_tab()`
- Line 6921: `_render_settings_tab()`
- Line 7313: `_render_stage3_candidates_tab()`

## Phase / hotfix / superseded markers

- Line 1: `# v1.6D1B post-main dead blocks cleanup packaged`
- Line 2: `# v1.6C8 data source detection refactor packaged`
- Line 3: `# v1.6C6 dashboard combined warning final fix packaged`
- Line 4: `# v1.6C5 dashboard combined source card fix packaged`
- Line 5: `# v1.6C4 combined UI final polish packaged`
- Line 6: `# v1.6C3 active combined ranking normalizer fix packaged`
- Line 7: `# v1.6C2 combined score legacy field bridge packaged`
- Line 8: `# v1.6C1 combined score UI priority fix packaged`
- Line 9: `# v1.6C combined scoring v1 packaged`
- Line 10: `# v1.6B1 remove duplicate main invocation hotfix packaged`
- Line 11: `# v1.6B fundamentals UI integration packaged`
- Line 12: `# v1.6A2 fundamentals panel helper order fix packaged`
- Line 13: `# v1.6A1 fundamentals dashboard panel hook fix packaged`
- Line 14: `# v1.6A fundamentals input bridge packaged`
- Line 15: `# v1.5D3 final UX polish render path fix packaged`
- Line 16: `# v1.5D2 UX polish runtime application fix packaged`
- Line 17: `# v1.5D1 company detail explainability hook fix packaged`
- Line 18: `# v1.5D ranking explainability UX polish packaged.`
- Line 19: `# v1.5C real universe scale test packaged.`
- Line 20: `# v1.5C1 scale test output restore hotfix packaged.`
- Line 21: `# v1.5B ranking explainability packaged.`
- Line 22: `# v1.5A local scoring v0 packaged.`
- Line 23: `# v1.4F2 manual market data percent normalization packaged.`
- Line 24: `# v1.4F market data UI integration packaged.`
- Line 25: `# v1.4F1 market data UI runtime hotfix packaged.`
- Line 26: `# v1.4E2 market data provider fallback packaged.`
- Line 135: `# v1.3A Visual UI Redesign packaged: CSS redesign + v1.2A fallback alignment.`
- Line 136: `# v1.4A data source transparency packaged.`
- Line 137: `# v1.4B real universe input packaged.`
- Line 138: `# v1.4C real universe candidates packaged.`
- Line 139: `# v1.4C1 real universe UI wording fix packaged.`
- Line 140: `# v1.4C1 hotfix real universe label packaged.`
- Line 141: `# v1.4D real universe scoring bridge packaged.`
- Line 142: `# v1.4D1 metadata score UI cleanup packaged.`
- Line 143: `# v1.4E real market data adapter packaged.`
- Line 144: `# v1.4E1 market data adapter hotfix packaged.`
- Line 2434: `# >>> v1.4F1 MARKET DATA UI RUNTIME HOTFIX HELPERS`
- Line 2481: `# <<< v1.4F1 MARKET DATA UI RUNTIME HOTFIX HELPERS`
- Line 2483: `# >>> v1.5A LOCAL SCORING V0 HELPERS`
- Line 2548: `# <<< v1.5A LOCAL SCORING V0 HELPERS`
- Line 2550: `# >>> v1.5B RANKING EXPLAINABILITY PANEL`
- Line 2600: `# <<< v1.5B RANKING EXPLAINABILITY PANEL`
- Line 2604: `# >>> v1.5B RANKING EXPLAINABILITY HELPERS`
- Line 2652: `# <<< v1.5B RANKING EXPLAINABILITY HELPERS`
- Line 2656: `# >>> v1.5D RANKING EXPLAINABILITY UX POLISH HELPERS`
- Line 2793: `# <<< v1.5D RANKING EXPLAINABILITY UX POLISH HELPERS`
- Line 2797: `# >>> v1.5D2 UX POLISH RUNTIME APPLICATION FIX HELPERS`
- Line 2889: `# <<< v1.5D2 UX POLISH RUNTIME APPLICATION FIX HELPERS`
- Line 2893: `# >>> v1.5D3 FINAL UX POLISH RENDER PATH FIX HELPERS`
- Line 3001: `# <<< v1.5D3 FINAL UX POLISH RENDER PATH FIX HELPERS`
- Line 3005: `# >>> v1.6B FUNDAMENTALS UI INTEGRATION HELPERS`
- Line 3118: `# <<< v1.6B FUNDAMENTALS UI INTEGRATION HELPERS`
- Line 3122: `# >>> v1.6C1 COMBINED SCORE UI PRIORITY FIX HELPERS`
- Line 3210: `# <<< v1.6C1 COMBINED SCORE UI PRIORITY FIX HELPERS`
- Line 3214: `# >>> v1.6C2 COMBINED SCORE LEGACY FIELD BRIDGE UI HELPERS`
- Line 3257: `# <<< v1.6C2 COMBINED SCORE LEGACY FIELD BRIDGE UI HELPERS`
- Line 3261: `# >>> v1.6C4 COMBINED UI FINAL POLISH HELPERS`
- Line 3314: `# <<< v1.6C4 COMBINED UI FINAL POLISH HELPERS`
- Line 4502: `# >>> v1.6C COMBINED SCORING V1 UI HELPERS`
- Line 4571: `# <<< v1.6C COMBINED SCORING V1 UI HELPERS`
- Line 4868: `# >>> v1.2A UI ALIGNMENT PATCH HELPERS`
- Line 5195: `# <<< v1.2A UI ALIGNMENT PATCH HELPERS`
- Line 5197: `# >>> v1.4A DATA SOURCE TRANSPARENCY HELPERS`
- Line 5412: `# <<< v1.4A DATA SOURCE TRANSPARENCY HELPERS`
- Line 5518: `# <<< v1.4B REAL UNIVERSE INPUT MVP HELPERS`
- Line 5520: `# >>> v1.4C REAL UNIVERSE CANDIDATES HELPERS`
- Line 5586: `# <<< v1.4C REAL UNIVERSE CANDIDATES HELPERS`
- Line 5588: `# >>> v1.4C1 REAL UNIVERSE UI WORDING FIX HELPERS`
- Line 5608: `# <<< v1.4C1 REAL UNIVERSE UI WORDING FIX HELPERS`
- Line 5610: `# >>> v1.4D REAL UNIVERSE SCORING BRIDGE HELPERS`
- Line 5672: `# <<< v1.4D REAL UNIVERSE SCORING BRIDGE HELPERS`
- Line 5674: `# >>> v1.4D1 METADATA SCORE UI CLEANUP HELPERS`
- Line 5710: `# <<< v1.4D1 METADATA SCORE UI CLEANUP HELPERS`
- Line 5712: `# >>> v1.4E REAL MARKET DATA ADAPTER HELPERS`
- Line 5766: `# <<< v1.4E REAL MARKET DATA ADAPTER HELPERS`
- Line 6026: `# >>> v1.6A FUNDAMENTALS INPUT BRIDGE PANEL`
- Line 6071: `# <<< v1.6A FUNDAMENTALS INPUT BRIDGE PANEL`
- Line 6075: `# >>> v1.6C5 DASHBOARD COMBINED SOURCE CARD FIX HELPERS`
- Line 6141: `# <<< v1.6C5 DASHBOARD COMBINED SOURCE CARD FIX HELPERS`
- Line 6145: `# >>> v1.6C6 DASHBOARD COMBINED WARNING FINAL FIX HELPERS`
- Line 6180: `# <<< v1.6C6 DASHBOARD COMBINED WARNING FINAL FIX HELPERS`
- Line 7883: `# PHASE 7D.2 INSTITUTIONAL COUNT HOTFIX APPLIED`
