# v2.18B - TWSE + TPEx Acquisition Plan

Status: **TWSE_TPEX_ACQUISITION_PLAN_COMPLETED_RAW_ACQUISITION_READY_50K_GATE_STILL_BLOCKED_FULL59K_DEPRECATED**

Phase type: **acquisition-plan-only**

Generated at UTC: `2026-08-11T08:50:40.641434+00:00`

## Executive summary

v2.18B creates the acquisition plan for the TWSE + TPEx Taiwan route.

This is a plan-only phase. It does not perform network calls, downloads, raw acquisition, candidate extraction, canonical comparison, scoring, OpenAI calls, broker calls or full59k work.

The active target remains 50,000 candidates. The current validated candidate dataset has `40300` rows, so `9700` additional validated candidate rows are needed.

## Current state

- Active canonical dataset: `outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv`
- Active canonical rows: `38287`
- Validated candidate dataset: `outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv`
- Validated candidate rows: `40300`
- Final target candidates: `50000`
- Rows needed to 50k: `9700`
- Candidate completion: `80.6%`
- Final 50k candidate gate: `BLOCKED`
- full59k: `DEPRECATED_DEFERRED`

## Planned sources

- P1 `twse_openapi_swagger` — TWSE — discovery_catalog — https://openapi.twse.com.tw/
- P2 `twse_listed_company_profile` — TWSE — primary_twse_candidate_source — https://openapi.twse.com.tw/v1/opendata/t187ap03_L
- P3 `twse_stock_day_all` — TWSE — twse_symbol_name_crosscheck — https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
- P4 `twse_latest_listed_companies` — TWSE — new_listing_crosscheck — https://www.twse.com.tw/en/company/newlisting?response=html
- P5 `tpex_openapi_swagger` — TPEx — discovery_catalog — https://www.tpex.org.tw/openapi/
- P6 `tpex_daily_stock_quotes` — TPEx — primary_tpex_candidate_source — https://www.tpex.org.tw/en-us/mainboard/trading/info/pricing.html
- P7 `tpex_stock_pricing_page` — TPEx — tpex_symbol_name_crosscheck — https://www.tpex.org.tw/en-us/mainboard/trading/info/stock-pricing.html
- P8 `tpex_mainboard_applicant_companies` — TPEx — applicant_review_only — https://www.tpex.org.tw/en-us/mainboard/applying/status/company.html
- P9 `tpex_gisa_company` — TPEx — deferred_or_review_only — https://www.tpex.org.tw/openapi/

## Filter policy

- `catalog_only` / source_handling: do_not_extract_candidates_directly — catalog/swagger/html index sources are for discovery only
- `ordinary_equity_filter` / include: eligible_for_candidate_extraction — include only official TWSE/TPEx listed/mainboard ordinary equity rows with code and company name
- `ordinary_equity_filter` / exclude: exclude_or_review — exclude ETF, ETN, fund, REIT, warrant, bond, beneficiary certificate, preferred share, rights, futures-linked product
- `ordinary_equity_filter` / exclude: exclude_or_review — exclude obvious ETF/ETN/security product code families such as 00xx where identified by source metadata/name
- `ordinary_equity_filter` / exclude: exclude_or_review — exclude names containing ETF, ETN, FUND, REIT, WARRANT, BOND, INDEX, 指數, 基金, 債, 權證, 特別股
- `applicant_exclusion_policy` / exclude: review_only — applicant or pending listing companies are diagnostics only unless separately confirmed listed/tradable
- `non_mainboard_review_policy` / review: review_possible_future_route — GISA, emerging, applicant or non-mainboard data require separate review bucket

## Acquisition route

- v2.18C — Raw Acquisition
- v2.18D — Raw Validation
- v2.18E — Candidate Extraction Dry Run
- v2.18F — Candidate Validation Against Canonical Dry Run
- v2.18G — Expanded Rebuild Candidate
- v2.18H — Expanded Validation
- v2.18I — Closure Report

## Checks

- v2_18a_report_exists: PASS (critical) — outputs\full_universe_source_acquisition\next_provider_route_selection_v2_18a.json
- v2_18a_status_expected: PASS (critical) — NEXT_PROVIDER_ROUTE_SELECTION_COMPLETED_TWSE_TPEX_SELECTED_50K_TARGET_ACTIVE_FULL59K_DEPRECATED
- canonical_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_v2_14e.csv
- validated_candidate_dataset_exists: PASS (critical) — outputs\full_universe_source_acquisition\expanded_universe_candidate_nse_india_v2_17g.csv
- active_canonical_rows_expected: PASS (critical) — active_canonical_rows=38287
- validated_candidate_rows_expected: PASS (critical) — validated_candidate_rows=40300
- rows_needed_to_50k_expected: PASS (critical) — rows_needed_to_50k=9700
- candidate_schema_matches_canonical: PASS (critical) — canonical_cols=33 candidate_cols=33
- source_plan_has_twse_and_tpex: PASS (critical) — ['TPEx', 'TWSE']
- selected_provider_matches_v2_18a: PASS (critical) — TWSE + TPEx Taiwan
- final_target_50k_active: PASS (critical) — 50000
- full59k_deprecated: PASS (critical) — DEPRECATED_DEFERRED_NOT_ACTIVE
- canonical_sha_unchanged: PASS (critical) — canonical sha unchanged
- network_not_used: PASS (critical) — network_download_performed=False
- raw_acquisition_not_performed: PASS (critical) — raw_acquisition_performed=False
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- canonical_comparison_not_performed: PASS (critical) — canonical_comparison_performed=False
- new_expanded_dataset_not_written: PASS (critical) — new_expanded_dataset_written=False
- scoring_not_recalculated: PASS (critical) — scoring_recalculated=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Guards

- Network download performed: false
- Endpoint calls performed: false
- Query sweep performed: false
- Raw acquisition performed: false
- Raw files written: false
- Candidate extraction performed: false
- Canonical comparison performed: false
- Canonical dataset read: true
- Validated candidate dataset read: true
- Source plan written: true
- Filter policy written: true
- Acquisition actions written: true
- Schema plan written: true
- Canonical dataset modified: false
- Canonical SHA unchanged: `True`
- Active canonical replaced: false
- New expanded dataset written: false
- Expanded universe rebuilt as canonical: false
- Final target 50k active: true
- full59k target deprecated: true
- full59k universe launched: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Overwrite allowed: false

## Conclusion

v2.18B completes the TWSE + TPEx acquisition plan and prepares v2.18C raw acquisition.

## Recommended next phase

`v2.18C - TWSE + TPEx Raw Acquisition`
