# Scout Finance ? v1.6D3A Legacy Helper Usage Audit

- File: `D:\Proyectos\💰 Scout Finance\app.py`
- Legacy helpers found: 34
- No-call candidates: 12

## No-call candidates

- Line 2562: `_sf15a_render_local_scoring_panel()`
- Line 2624: `_sf15b_render_explainability_panel()`
- Line 2679: `_sf15b_render_explainability_block()`
- Line 2765: `_sf15d_badge_summary()`
- Line 2787: `_sf15d_render_explainability_block()`
- Line 2831: `_sf15d_render_ux_polish_panel()`
- Line 2872: `_sf15d2_human_category()`
- Line 2878: `_sf15d2_human_status()`
- Line 2884: `_sf15d2_human_provider()`
- Line 2890: `_sf15d2_render_company_explainability()`
- Line 3168: `_sf16c1_value()`
- Line 3179: `_sf16c1_score_float()`

## Legacy helpers with calls

- Line 2529: `_sf15a_local_score_status()` called at [2563]
- Line 2585: `_sf15a_is_local_score_row()` called at [3374]
- Line 2596: `_sf15b_explainability_status()` called at [2625]
- Line 2650: `_sf15b_split_factors()` called at [2692, 2693, 2695, 2696]
- Line 2658: `_sf15b_render_factor_list()` called at [2692, 2693, 2695, 2696]
- Line 2667: `_sf15b_is_explainability_row()` called at [2681]
- Line 2702: `_sf15d_human_category()` called at [2874]
- Line 2720: `_sf15d_human_status()` called at [2880]
- Line 2736: `_sf15d_human_provider()` called at [2886]
- Line 2746: `_sf15d_short_text()` called at [2762, 2779, 2868]
- Line 2753: `_sf15d_factor_list()` called at [2761, 2766, 2789, 2790, 2791, 2792, 2793]
- Line 2760: `_sf15d_first_factor()` called at [2783]
- Line 2770: `_sf15d_prepare_ranking_display()` called at [7853]
- Line 2843: `_sf15d2_humanize_dataframe()` called at [2875, 2881, 2887, 7853]
- Line 3189: `_sf16c1_humanize_ranking_df()` called at [4629]
- Line 3213: `_sf16c2_human_category()` called at [3291]
- Line 3228: `_sf16c2_human_status()` called at [2519, 3323]
- Line 3237: `_sf16c2_humanize_any_ranking_df()` called at [4631]
- Line 6015: `_sf16c5_active_combined_summary()` called at [6053]
- Line 6052: `_sf16c5_is_combined_active()` called at [6094, 5122]
- Line 6062: `_sf16c6_combined_dashboard_message()` called at [6095]
- Line 6093: `_sf16c6_render_combined_dashboard_notice()` called at [5123]

## Full legacy inventory

- Line 2529: `_sf15a_local_score_status()` ? calls: [2563]
- Line 2562: `_sf15a_render_local_scoring_panel()` ? calls: none
- Line 2585: `_sf15a_is_local_score_row()` ? calls: [3374]
- Line 2596: `_sf15b_explainability_status()` ? calls: [2625]
- Line 2624: `_sf15b_render_explainability_panel()` ? calls: none
- Line 2650: `_sf15b_split_factors()` ? calls: [2692, 2693, 2695, 2696]
- Line 2658: `_sf15b_render_factor_list()` ? calls: [2692, 2693, 2695, 2696]
- Line 2667: `_sf15b_is_explainability_row()` ? calls: [2681]
- Line 2679: `_sf15b_render_explainability_block()` ? calls: none
- Line 2702: `_sf15d_human_category()` ? calls: [2874]
- Line 2720: `_sf15d_human_status()` ? calls: [2880]
- Line 2736: `_sf15d_human_provider()` ? calls: [2886]
- Line 2746: `_sf15d_short_text()` ? calls: [2762, 2779, 2868]
- Line 2753: `_sf15d_factor_list()` ? calls: [2761, 2766, 2789, 2790, 2791, 2792, 2793]
- Line 2760: `_sf15d_first_factor()` ? calls: [2783]
- Line 2765: `_sf15d_badge_summary()` ? calls: none
- Line 2770: `_sf15d_prepare_ranking_display()` ? calls: [7853]
- Line 2787: `_sf15d_render_explainability_block()` ? calls: none
- Line 2831: `_sf15d_render_ux_polish_panel()` ? calls: none
- Line 2843: `_sf15d2_humanize_dataframe()` ? calls: [2875, 2881, 2887, 7853]
- Line 2872: `_sf15d2_human_category()` ? calls: none
- Line 2878: `_sf15d2_human_status()` ? calls: none
- Line 2884: `_sf15d2_human_provider()` ? calls: none
- Line 2890: `_sf15d2_render_company_explainability()` ? calls: none
- Line 3168: `_sf16c1_value()` ? calls: none
- Line 3179: `_sf16c1_score_float()` ? calls: none
- Line 3189: `_sf16c1_humanize_ranking_df()` ? calls: [4629]
- Line 3213: `_sf16c2_human_category()` ? calls: [3291]
- Line 3228: `_sf16c2_human_status()` ? calls: [2519, 3323]
- Line 3237: `_sf16c2_humanize_any_ranking_df()` ? calls: [4631]
- Line 6015: `_sf16c5_active_combined_summary()` ? calls: [6053]
- Line 6052: `_sf16c5_is_combined_active()` ? calls: [6094, 5122]
- Line 6062: `_sf16c6_combined_dashboard_message()` ? calls: [6095]
- Line 6093: `_sf16c6_render_combined_dashboard_notice()` ? calls: [5123]