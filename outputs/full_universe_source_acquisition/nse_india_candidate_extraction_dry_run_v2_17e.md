# v2.17E - NSE India Candidate Extraction Dry Run

Status: **NSE_INDIA_CANDIDATE_EXTRACTION_DRY_RUN_COMPLETED_CANDIDATES_FOUND_CANONICAL_COMPARISON_STILL_BLOCKED**

Phase type: **candidate-extraction-dry-run-only**

Generated at UTC: `2026-08-06T11:57:37.603542+00:00`

## Executive summary

NSE India candidate extraction dry run completed.

This phase extracts preliminary candidates and exclusions from locally validated NSE raw files. It does not read the canonical dataset, does not compare candidates against canonical symbols, does not apply net-new filtering and does not create or modify any expanded universe dataset.

## Current state

- Active canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completion: `76.57%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Extraction summary

- Valid profiles read: `14`
- Raw candidates before dedupe: `14737`
- Deduped candidates: `11802`
- Exclusions: `39384`
- Candidate source counts: `{'nse_all_reports_cm_mii_security_file_nse_listed': 9738, 'nse_securities_available_equity_segment': 2064}`
- Candidate confidence counts: `{'medium': 9738, 'high': 2064}`
- Candidate series counts: `{'BE': 3129, 'BL': 3198, 'EQ': 3693, 'SM': 766, 'ST': 766, 'BZ': 227, 'SZ': 23}`
- Exclusion reason counts: `{'bse_exclusive_scope_review_not_candidate': 5000, 'invalid_isin_format': 455, 'excluded_mii_non_equity_series:N0': 1020, 'excluded_mii_non_equity_series:U0': 1020, 'excluded_name_keyword:ncd': 1649, 'excluded_mii_non_equity_series:N1': 77, 'excluded_mii_non_equity_series:U1': 77, 'excluded_mii_non_equity_series:NO': 7, 'excluded_mii_non_equity_series:UO': 7, 'excluded_mii_non_equity_series:NF': 9, 'excluded_mii_non_equity_series:UF': 9, 'excluded_mii_non_equity_series:GS': 286, 'excluded_mii_non_equity_series:M3': 1, 'excluded_mii_non_equity_series:Y3': 1, 'excluded_mii_non_equity_series:NG': 8, 'excluded_mii_non_equity_series:UG': 8, 'excluded_mii_non_equity_series:N2': 26, 'excluded_mii_non_equity_series:U2': 26, 'excluded_mii_non_equity_series:N3': 20, 'excluded_mii_non_equity_series:U3': 20, 'excluded_mii_non_equity_series:NE': 11, 'excluded_mii_non_equity_series:UE': 11, 'excluded_mii_non_equity_series:N6': 13, 'excluded_mii_non_equity_series:U6': 13, 'excluded_mii_non_equity_series:NH': 9, 'excluded_mii_non_equity_series:UH': 9, 'excluded_mii_non_equity_series:NP': 6, 'excluded_mii_non_equity_series:UP': 6, 'excluded_mii_non_equity_series:N7': 10, 'excluded_mii_non_equity_series:U7': 10, 'excluded_mii_non_equity_series:ND': 14, 'excluded_mii_non_equity_series:UD': 14, 'excluded_mii_non_equity_series:TB': 1011, 'excluded_mii_non_equity_series:IQ': 2868, 'excluded_mii_non_equity_series:RL': 3104, 'excluded_mii_non_equity_series:AF': 331, 'excluded_mii_non_equity_series:T0': 525, 'excluded_mii_non_equity_series:TL': 524, 'excluded_mii_non_equity_series:IT': 8, 'excluded_mii_non_equity_series:IZ': 1, 'excluded_mii_non_equity_series:SG': 4484, 'excluded_mii_non_equity_series:NL': 7, 'excluded_mii_non_equity_series:UL': 7, 'excluded_name_keyword:bond': 238, 'excluded_mii_non_equity_series:NB': 22, 'excluded_mii_non_equity_series:UB': 19, 'excluded_mii_non_equity_series:NA': 17, 'excluded_mii_non_equity_series:UA': 16, 'excluded_mii_non_equity_series:N5': 12, 'excluded_mii_non_equity_series:U5': 13, 'excluded_mii_non_equity_series:N8': 12, 'excluded_mii_non_equity_series:U8': 12, 'excluded_mii_non_equity_series:N9': 14, 'excluded_mii_non_equity_series:U9': 14, 'excluded_mii_non_equity_series:NN': 6, 'excluded_mii_non_equity_series:UN': 6, 'excluded_mii_non_equity_series:NC': 19, 'excluded_mii_non_equity_series:UC': 16, 'excluded_mii_non_equity_series:NI': 7, 'excluded_mii_non_equity_series:UI': 7, 'excluded_mii_non_equity_series:NM': 7, 'excluded_mii_non_equity_series:UM': 7, 'excluded_mii_non_equity_series:NS': 3, 'excluded_mii_non_equity_series:US': 3, 'excluded_mii_non_equity_series:NR': 3, 'excluded_mii_non_equity_series:UR': 3, 'excluded_mii_non_equity_series:NQ': 5, 'excluded_mii_non_equity_series:UQ': 5, 'excluded_mii_non_equity_series:NK': 7, 'excluded_mii_non_equity_series:UK': 7, 'excluded_mii_non_equity_series:NJ': 7, 'excluded_mii_non_equity_series:UJ': 7, 'excluded_mii_non_equity_series:N4': 14, 'excluded_mii_non_equity_series:U4': 14, 'excluded_mii_non_equity_series:M4': 1, 'excluded_mii_non_equity_series:Y4': 1, 'excluded_mii_non_equity_series:M5': 1, 'excluded_mii_non_equity_series:Y5': 1, 'excluded_mii_non_equity_series:NU': 1, 'excluded_mii_non_equity_series:UU': 1, 'excluded_mii_non_equity_series:NT': 1, 'excluded_mii_non_equity_series:UT': 1, 'excluded_mii_non_equity_series:NV': 2, 'excluded_mii_non_equity_series:UV': 2, 'excluded_mii_non_equity_series:NW': 2, 'excluded_mii_non_equity_series:UW': 2, 'excluded_mii_non_equity_series:M6': 1, 'excluded_mii_non_equity_series:Y6': 1, 'excluded_mii_non_equity_series:M7': 1, 'excluded_mii_non_equity_series:Y7': 1, 'excluded_mii_non_equity_series:M8': 1, 'excluded_mii_non_equity_series:Y8': 1, 'excluded_mii_non_equity_series:L1': 87, 'excluded_mii_non_equity_series:NX': 2, 'excluded_mii_non_equity_series:UX': 2, 'excluded_mii_non_equity_series:NZ': 2, 'excluded_mii_non_equity_series:UZ': 2, 'excluded_mii_non_equity_series:M2': 2, 'excluded_mii_non_equity_series:Y2': 2, 'excluded_mii_non_equity_series:M0': 1, 'excluded_mii_non_equity_series:Y0': 1, 'excluded_mii_non_equity_series:19': 1, 'excluded_mii_non_equity_series:Z9': 1, 'excluded_mii_non_equity_series:M9': 1, 'excluded_mii_non_equity_series:Y9': 1, 'excluded_mii_non_equity_series:SL': 766, 'excluded_mii_non_equity_series:SQ': 766, 'excluded_mii_non_equity_series:SO': 204, 'excluded_mii_non_equity_series:E1': 63, 'excluded_mii_non_equity_series:X1': 63, 'excluded_mii_non_equity_series:O1': 4, 'excluded_mii_non_equity_series:P1': 4, 'excluded_mii_non_equity_series:K1': 5, 'excluded_mii_non_equity_series:W1': 5, 'excluded_name_keyword:gsec': 9, 'excluded_name_keyword:etf': 306, 'excluded_mii_non_equity_series:MF': 2895, 'excluded_mii_non_equity_series:R1': 82, 'excluded_mii_non_equity_series:V1': 81, 'excluded_mii_non_equity_series:L2': 26, 'excluded_mii_non_equity_series:L3': 12, 'excluded_mii_non_equity_series:L4': 6, 'excluded_mii_non_equity_series:R2': 26, 'excluded_mii_non_equity_series:R3': 12, 'excluded_mii_non_equity_series:R4': 6, 'excluded_mii_non_equity_series:V2': 25, 'excluded_mii_non_equity_series:V3': 12, 'excluded_mii_non_equity_series:V4': 6, 'excluded_mii_non_equity_series:SE': 50, 'excluded_mii_non_equity_series:SF': 50, 'excluded_mii_non_equity_series:RV': 19, 'excluded_name_keyword:trust': 106, 'excluded_mii_non_equity_series:ID': 11, 'excluded_mii_non_equity_series:IO': 7, 'excluded_mii_non_equity_series:IV': 11, 'excluded_name_keyword:gold': 120, 'excluded_name_keyword:silver': 55, 'excluded_mii_non_equity_series:BO': 18, 'excluded_name_keyword:pref': 11, 'excluded_mii_non_equity_series:TO': 7, 'excluded_mii_non_equity_series:B1': 3, 'excluded_mii_non_equity_series:I1': 3, 'excluded_name_keyword:reit': 12, 'excluded_mii_non_equity_series:RO': 1, 'excluded_mii_non_equity_series:RR': 1, 'excluded_mii_non_equity_series:RT': 1, 'excluded_mii_non_equity_series:LS': 2, 'excluded_mii_non_equity_series:D1': 2, 'excluded_mii_non_equity_series:S1': 2, 'excluded_mii_non_equity_series:A1': 1, 'excluded_mii_non_equity_series:G1': 4, 'excluded_name_keyword:warrant': 18, 'excluded_mii_non_equity_series:DS': 1, 'excluded_mii_non_equity_series:BB': 18, 'excluded_name_keyword:fund': 27, 'excluded_mii_non_equity_series:L5': 4, 'excluded_mii_non_equity_series:L6': 1, 'excluded_mii_non_equity_series:L7': 1, 'excluded_mii_non_equity_series:L8': 1, 'excluded_mii_non_equity_series:L9': 1, 'excluded_mii_non_equity_series:LA': 1, 'excluded_mii_non_equity_series:LB': 1, 'excluded_mii_non_equity_series:LC': 1, 'excluded_mii_non_equity_series:LD': 1, 'excluded_mii_non_equity_series:LE': 1, 'excluded_mii_non_equity_series:LF': 1, 'excluded_mii_non_equity_series:LG': 1, 'excluded_mii_non_equity_series:LH': 1, 'excluded_mii_non_equity_series:LI': 1, 'excluded_mii_non_equity_series:LJ': 1, 'excluded_mii_non_equity_series:R5': 4, 'excluded_mii_non_equity_series:R6': 1, 'excluded_mii_non_equity_series:R7': 1, 'excluded_mii_non_equity_series:R8': 1, 'excluded_mii_non_equity_series:R9': 1, 'excluded_mii_non_equity_series:RA': 1, 'excluded_mii_non_equity_series:RB': 1, 'excluded_mii_non_equity_series:RC': 1, 'excluded_mii_non_equity_series:RD': 1, 'excluded_mii_non_equity_series:RE': 1, 'excluded_mii_non_equity_series:RF': 1, 'excluded_mii_non_equity_series:RG': 1, 'excluded_mii_non_equity_series:RH': 1, 'excluded_mii_non_equity_series:RI': 1, 'excluded_mii_non_equity_series:RJ': 1, 'excluded_mii_non_equity_series:V5': 4, 'excluded_mii_non_equity_series:V6': 1, 'excluded_mii_non_equity_series:V7': 1, 'excluded_mii_non_equity_series:V8': 1, 'excluded_mii_non_equity_series:V9': 1, 'excluded_mii_non_equity_series:VA': 1, 'excluded_mii_non_equity_series:VB': 1, 'excluded_mii_non_equity_series:VC': 1, 'excluded_mii_non_equity_series:VD': 1, 'excluded_mii_non_equity_series:VE': 1, 'excluded_mii_non_equity_series:VF': 1, 'excluded_mii_non_equity_series:VG': 1, 'excluded_mii_non_equity_series:VH': 1, 'excluded_mii_non_equity_series:VI': 1, 'excluded_mii_non_equity_series:VJ': 1, 'excluded_mii_non_equity_series:K3': 2, 'excluded_mii_non_equity_series:W3': 2, 'excluded_mii_non_equity_series:IA': 6, 'excluded_mii_non_equity_series:B3': 1, 'excluded_mii_non_equity_series:E3': 1, 'excluded_mii_non_equity_series:I3': 1, 'excluded_mii_non_equity_series:T3': 1, 'excluded_mii_non_equity_series:X3': 1, 'excluded_mii_non_equity_series:G2': 2, 'excluded_mii_non_equity_series:G3': 2, 'excluded_mii_non_equity_series:G4': 2, 'excluded_mii_non_equity_series:G5': 2, 'excluded_mii_non_equity_series:G6': 2, 'excluded_mii_non_equity_series:G7': 2, 'excluded_mii_non_equity_series:G9': 1, 'excluded_mii_non_equity_series:M1': 3, 'excluded_mii_non_equity_series:Y1': 2, 'excluded_mii_non_equity_series:MA': 1, 'excluded_mii_non_equity_series:YA': 1, 'excluded_mii_non_equity_series:MC': 1, 'excluded_mii_non_equity_series:YC': 1, 'excluded_mii_non_equity_series:NY': 1, 'excluded_mii_non_equity_series:UY': 1, 'excluded_mii_non_equity_series:MB': 1, 'excluded_mii_non_equity_series:YB': 1, 'excluded_name_keyword:invit': 15, 'excluded_mii_non_equity_series:SP': 3, 'excluded_mii_non_equity_series:TT': 1, 'excluded_mii_non_equity_series:D2': 1, 'excluded_mii_non_equity_series:S2': 1, 'excluded_mii_non_equity_series:F1': 1, 'excluded_mii_non_equity_series:Q1': 1, 'excluded_mii_non_equity_series:GB': 2, 'excluded_mii_non_equity_series:G8': 1, 'excluded_mii_non_equity_series:DE': 1, 'excluded_mii_non_equity_series:DL': 1, 'excluded_mii_non_equity_series:DR': 1, 'excluded_mii_non_equity_series:T1': 1, 'excluded_mii_non_equity_series:O2': 1, 'excluded_mii_non_equity_series:P2': 1, 'excluded_source_idr': 4, 'excluded_source_preference_shares': 4, 'excluded_source_warrants': 1, 'excluded_source_close_ended_mf': 119, 'excluded_source_etf': 341, 'reference_only_company_name_changes': 2321, 'reference_only_symbol_changes': 1053, 'excluded_source_invit': 7, 'excluded_source_reit': 5, 'excluded_source_debt': 6066}`
- Critical failed checks: `0`

## Source diagnostics

- `nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive` role=`bse_exclusive_scope_review_not_candidate` rows=`36243` raw_candidates=`0` deduped=`0` exclusions=`5000`
- `nse_all_reports_cm_mii_security_file_nse_listed` role=`primary_mii_security_file` rows=`36243` raw_candidates=`11802` deduped=`9738` exclusions=`24441`
- `nse_securities_available_equity_segment` role=`primary_equity_segment_csv` rows=`2397` raw_candidates=`2380` deduped=`2064` exclusions=`17`
- `nse_securities_available_sme` role=`sme_equity_review_csv` rows=`560` raw_candidates=`555` deduped=`0` exclusions=`5`
- `nse_idrs` role=`excluded_source_idr` rows=`4` raw_candidates=`0` deduped=`0` exclusions=`4`
- `nse_preference_shares` role=`excluded_source_preference_shares` rows=`4` raw_candidates=`0` deduped=`0` exclusions=`4`
- `nse_warrants` role=`excluded_source_warrants` rows=`1` raw_candidates=`0` deduped=`0` exclusions=`1`
- `nse_close_ended_mf` role=`excluded_source_close_ended_mf` rows=`119` raw_candidates=`0` deduped=`0` exclusions=`119`
- `nse_etfs` role=`excluded_source_etf` rows=`341` raw_candidates=`0` deduped=`0` exclusions=`341`
- `nse_changes_company_names` role=`reference_only_company_name_changes` rows=`2321` raw_candidates=`0` deduped=`0` exclusions=`2321`
- `nse_changes_symbols` role=`reference_only_symbol_changes` rows=`1053` raw_candidates=`0` deduped=`0` exclusions=`1053`
- `nse_invits` role=`excluded_source_invit` rows=`7` raw_candidates=`0` deduped=`0` exclusions=`7`
- `nse_reits` role=`excluded_source_reit` rows=`5` raw_candidates=`0` deduped=`0` exclusions=`5`
- `nse_debt_instruments` role=`excluded_source_debt` rows=`6066` raw_candidates=`0` deduped=`0` exclusions=`6066`

## Checks

- v2_17d_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_raw_validation_v2_17d.json
- v2_17d_status_expected: PASS (critical) — NSE_INDIA_RAW_VALIDATION_COMPLETED_RAW_FILES_VALID_CANDIDATE_EXTRACTION_READY_FULL_SOURCE_STILL_BLOCKED
- v2_17d_recommended_e: PASS (critical) — v2.17E - NSE India Candidate Extraction Dry Run
- file_profile_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_raw_validation_file_profile_v2_17d.csv
- source_diagnostics_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_raw_validation_source_diagnostics_v2_17d.csv
- schema_profile_exists: PASS (critical) — outputs\full_universe_source_acquisition\nse_india_raw_validation_schema_profile_v2_17d.csv
- valid_profiles_present: PASS (critical) — valid_profiles=14
- candidate_sources_read: PASS (critical) — sources_read=['nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive', 'nse_all_reports_cm_mii_security_file_nse_listed', 'nse_changes_company_names', 'nse_changes_symbols', 'nse_close_ended_mf', 'nse_debt_instruments', 'nse_etfs', 'nse_idrs', 'nse_invits', 'nse_preference_shares', 'nse_reits', 'nse_securities_available_equity_segment', 'nse_securities_available_sme', 'nse_warrants']
- candidate_rows_extracted: PASS (critical) — deduped_candidates=11802 raw_before_dedupe=14737
- equity_segment_candidates_present: PASS (critical) — equity_candidates=2064
- exclusions_generated: PASS (critical) — exclusions=39384
- explicit_exclusion_sources_used: PASS (critical) — exclusion_sources=['nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive', 'nse_all_reports_cm_mii_security_file_nse_listed', 'nse_changes_company_names', 'nse_changes_symbols', 'nse_close_ended_mf', 'nse_debt_instruments', 'nse_etfs', 'nse_idrs', 'nse_invits', 'nse_preference_shares', 'nse_reits', 'nse_securities_available_equity_segment', 'nse_securities_available_sme', 'nse_warrants']
- candidate_symbols_valid: PASS (critical) — all candidate symbols valid
- candidate_names_present: PASS (critical) — all candidate names present
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- network_not_used: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- raw_files_read: PASS (critical) — raw_files_read=True
- candidate_extraction_performed: PASS (critical) — candidate_extraction_performed=True
- canonical_dataset_not_read: PASS (critical) — canonical_dataset_read=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- net_new_filtering_not_applied: PASS (critical) — net_new_filtering_applied=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17D report read: true
- Raw validation profiles read: true
- Raw files read: true
- Candidate extraction performed: true
- Candidate rows extracted: `True`
- Exclusion rows extracted: `True`
- Canonical dataset read: false
- Canonical dataset modified: false
- Canonical comparison performed: false
- Net-new filtering applied: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17E generated a candidate extraction dry run for NSE India and prepared the artifacts for v2.17F canonical validation.

## Recommended next phase

`v2.17F - NSE India Candidate Validation Against Canonical Dry Run`
