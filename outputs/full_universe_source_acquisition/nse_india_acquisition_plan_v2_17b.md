# v2.17B - NSE India Acquisition Plan

Status: **NSE_INDIA_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_FULL_SOURCE_STILL_BLOCKED**

Phase type: **provider-acquisition-plan-only**

Generated at UTC: `2026-08-06T09:02:34.859999+00:00`

## Executive plan

NSE India acquisition planning is complete.

The primary planned source is the NSE All Reports CM MII security file for NSE listed securities. The main cross-check source is the NSE Securities Available for Trading equity segment CSV. Exclusion/reference lists are explicitly planned for ETFs, REITs, INVITs, IDRs, warrants, preference shares, mutual funds and debt instruments.

No download is performed in this phase.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completion: `76.57%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Source plan

- **1. nse_all_reports_cm_mii_security_file_nse_listed** — role=`primary_bulk_candidate_source`, format=`csv.gz`, risk=`medium`
- **2. nse_all_reports_cm_mii_security_file_nse_and_bse_exclusive** — role=`secondary_bulk_candidate_source_review`, format=`csv.gz`, risk=`medium_high`
- **3. nse_securities_available_equity_segment** — role=`cross_check_and_candidate_source`, format=`csv`, risk=`medium`
- **4. nse_securities_available_sme** — role=`review_candidate_source`, format=`csv`, risk=`medium`
- **5. nse_changes_company_names** — role=`reference_only`, format=`csv`, risk=`low`
- **6. nse_changes_symbols** — role=`reference_only`, format=`csv`, risk=`low`
- **7. nse_idrs** — role=`explicit_exclusion_reference`, format=`csv`, risk=`low`
- **8. nse_preference_shares** — role=`explicit_exclusion_reference`, format=`csv`, risk=`low`
- **9. nse_warrants** — role=`explicit_exclusion_reference`, format=`csv`, risk=`low`
- **10. nse_etfs** — role=`explicit_exclusion_reference`, format=`csv`, risk=`low`
- **11. nse_close_ended_mf** — role=`explicit_exclusion_reference`, format=`csv`, risk=`low`
- **12. nse_reits** — role=`explicit_exclusion_reference`, format=`csv`, risk=`low`
- **13. nse_invits** — role=`explicit_exclusion_reference`, format=`csv`, risk=`low`
- **14. nse_debt_instruments** — role=`explicit_exclusion_reference`, format=`csv`, risk=`medium`

## Filter policy

- **include_nse_listed_ordinary_equity** — `include_after_validation`: NSE listed ordinary/fully paid equity shares
- **review_sme_equity** — `review`: NSE SME/Emerge equity
- **exclude_bse_exclusive_until_explicit_scope** — `exclude_or_review`: BSE Exclusive securities inside NSE file route
- **exclude_etf** — `exclude`: ETF
- **exclude_reit_invit** — `exclude`: REIT / INVIT units
- **exclude_mutual_funds** — `exclude`: Close-ended mutual fund schemes
- **exclude_debt** — `exclude`: Debt instruments
- **exclude_warrants** — `exclude`: Warrants
- **exclude_idr** — `exclude`: Indian Depository Receipts
- **review_preference_shares** — `exclude_or_manual_review`: Preference shares
- **reference_symbol_name_changes** — `reference_only`: Company name/symbol changes

## Checks

- v2_17a_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\next_provider_route_selection_v2_17a.json
- v2_17a_status_expected: PASS (critical) — NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_NSE_INDIA_SELECTED_FULL_SOURCE_STILL_BLOCKED
- v2_17a_recommended_b: PASS (critical) — v2.17B - NSE India Acquisition Plan
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- canonical_rows_expected: PASS (critical) — canonical_rows=38287
- nse_primary_source_present: PASS (critical) — primary NSE MII security file
- nse_equity_crosscheck_present: PASS (critical) — equity segment CSV
- exclusion_sources_present: PASS (critical) — exclusion_sources=8
- source_plan_count: PASS (critical) — sources=14
- filter_policy_count: PASS (critical) — policies=11
- actions_created: PASS (critical) — actions=14 sources=14
- full_source_still_blocked: PASS (critical) — 38287 < 50000
- network_not_used_in_plan: PASS (critical) — network_download_performed=False
- endpoint_calls_not_performed: PASS (critical) — endpoint_calls_performed=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- full_59k_not_launched: PASS (critical) — full_59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- v2.17A report read: true
- Canonical dataset read: true
- Canonical dataset modified: false
- Provider route confirmed: true
- Acquisition plan created: true
- Raw acquisition performed: false
- Raw files downloaded: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Net-new filtering applied to canonical: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Full source gate unblocked: false
- Overwrite allowed: false

## Conclusion

v2.17B defines the NSE India acquisition plan only.

v2.17C may perform raw acquisition from the planned NSE sources, but must still avoid parsing, candidate extraction, canonical comparison, rebuild and full-source unlock.

## Recommended next phase

`v2.17C - NSE India Raw Acquisition`
