# Security Sensitive Files Audit v2.39C

Decision: `SECURITY_SENSITIVE_FILES_AUDIT_READY`.

This offline audit reviews tracked repository files, relevant untracked local files, sensitive extensions, secret-like patterns, local paths, binary/publication risks and `.gitignore` policy before broader release preparation.

## Results

- Tracked files scanned: 4185
- Untracked files reviewed: 4
- Patterns checked: 8
- PASS rows: 4
- WARN rows: 67
- BLOCKER rows: 0
- Gitignore policy: `WARN`

## Guardrails

No network, scoring, ranking, methodology, weights, dataset mutation, broker workflow, tag creation or GitHub release was performed.

## Gitignore Warnings

Missing recommended patterns: `.pytest_cache, *.tmp, *.log`.

## Warnings Documented

| Path | Category | Evidence | Remediation |
| --- | --- | --- | --- |
| `Auditoria_Scout_Finance.docx` | sensitive_extensions | tracked extension .docx | Review whether this file belongs in public Git. |
| `CHANGELOG.md` | public_documentation_claims | cvrselvbetjening@erst.dk | Review and redact if this is real sensitive information. |
| `CHANGELOG.md` | public_documentation_claims | zefix@bj.admin.ch | Review and redact if this is real sensitive information. |
| `VERSION.md` | public_documentation_claims | zefix@bj.admin.ch | Review and redact if this is real sensitive information. |
| `app.py` | passwords | password = st.text_input( | Review and redact if this is real sensitive information. |
| `app_v0_5_stable.py` | passwords | password = st.text_input( | Review and redact if this is real sensitive information. |
| `app_v0_6_stable.py` | passwords | password = st.text_input( | Review and redact if this is real sensitive information. |
| `outputs/full_universe_source_acquisition/asx_candidate_extraction_dry_run_rows_v2_20e.csv` | oversized_files | 5278877 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/cboe_europe_normalized_candidates_v2_11e.csv` | oversized_files | 20628746 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_candidate_asx_v2_20g.csv` | oversized_files | 9389852 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_candidate_hkex_v2_19p.csv` | oversized_files | 8627341 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_candidate_nse_india_v2_17g.csv` | oversized_files | 8192878 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_candidate_tmx_v2_16g.csv` | oversized_files | 7916109 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_candidate_twse_tpex_v2_18g.csv` | oversized_files | 8541783 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_exclusions_v2_11e.csv` | oversized_files | 15714442 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_11e.csv` | oversized_files | 5356957 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_12e.csv` | oversized_files | 6476310 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_13e.csv` | oversized_files | 7257817 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv` | oversized_files | 7915990 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_20m_asx_promoted.csv` | oversized_files | 9389852 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_21d_c_colombia_candidate.csv` | oversized_files | 9515644 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_21d_s_singapore_candidate.csv` | oversized_files | 9511466 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_21e_c_colombia_promoted.csv` | oversized_files | 9515644 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_21e_s_singapore_promoted.csv` | oversized_files | 9511466 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_21g_final_reference.csv` | oversized_files | 9515644 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_21h_activated_operational_reference.csv` | oversized_files | 9515644 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/expanded_universe_v2_24f_metadata_promoted.csv` | oversized_files | 10089148 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/hkex_candidate_extraction_dry_run_candidates_v2_19n.csv` | oversized_files | 8073954 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/hkex_candidate_validation_against_canonical_dry_run_exclusions_v2_19o.csv` | oversized_files | 10001010 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/hkex_candidate_validation_against_canonical_dry_run_validated_candidates_v2_19o.csv` | oversized_files | 10224843 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/metadata_improvement_dry_run_overlay_v2_24e.csv` | oversized_files | 6845770 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/nse_india_candidate_extraction_candidates_v2_17e.csv` | oversized_files | 9431170 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/nse_india_candidate_extraction_exclusions_v2_17e.csv` | oversized_files | 26389523 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/nse_india_candidate_validation_classified_candidates_v2_17f.csv` | oversized_files | 11202955 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/production_scoring_dry_run_v2_scores_v2_25b.csv` | oversized_files | 10004942 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/fallback_symbols_traded/symbols_traded_bxe.html` | oversized_files | 9849501 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/fallback_symbols_traded/symbols_traded_cxe.html` | oversized_files | 9889739 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/fallback_symbols_traded/symbols_traded_dxe.html` | oversized_files | 6287811 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/raw/cboe_europe_v2_11c/fallback_symbols_traded/symbols_traded_trf.html` | oversized_files | 20760867 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/datasets/002_downloads_en_RDF_StaticData_xetr.zip` | sensitive_extensions | tracked extension .zip | Review whether this file belongs in public Git. |
| `outputs/full_universe_source_acquisition/raw/deutsche_boerse_xetra_v2_14c/datasets/002_downloads_en_RDF_StaticData_xetr.zip` | oversized_files | 6974014 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/raw/hkex_v2_12c/ListOfSecurities.xlsx` | sensitive_extensions | tracked extension .xlsx | Review whether this file belongs in public Git. |
| `outputs/full_universe_source_acquisition/raw/hkex_v2_19l_fix/01_full_list_of_securities.xlsx` | sensitive_extensions | tracked extension .xlsx | Review whether this file belongs in public Git. |
| `outputs/full_universe_source_acquisition/raw/hkex_v2_19l_fix/09_list_of_dual_counter_securities.xlsx` | sensitive_extensions | tracked extension .xlsx | Review whether this file belongs in public Git. |
| `outputs/full_universe_source_acquisition/raw/jpx_v2_13c/datasets/002_jpx_dataset_candidate_jpx_discovered_workbook_candidate.xlsx` | sensitive_extensions | tracked extension .xlsx | Review whether this file belongs in public Git. |
| `outputs/full_universe_source_acquisition/scoring_formula_redesign_dry_run_scores_v2_23d.csv` | oversized_files | 10053232 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/v2_38am_global_macro_geopolitical_context/global_macro_geopolitical_context_v2_38am.csv` | oversized_files | 7736253 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/v2_38am_global_macro_geopolitical_context/global_macro_geopolitical_notes_v2_38am.csv` | oversized_files | 9884159 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/v2_38bo_global_scoring_eligibility/global_scoring_eligibility_v2_38bo.csv` | oversized_files | 6490293 bytes | Confirm the file is intentionally tracked. |
| `outputs/full_universe_source_acquisition/v2_38c_us_eu_priority_coverage/eu_universe_census_v2_38c.csv` | oversized_files | 5487677 bytes | Confirm the file is intentionally tracked. |

Next recommended phase: `v2.39D-clean-windows-install-validation`.
