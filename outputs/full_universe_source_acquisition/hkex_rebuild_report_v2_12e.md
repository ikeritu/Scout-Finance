# v2.12E - Rebuild Expanded Source With HKEX

Status: **HKEX_REBUILD_COMPLETED_FULL_SOURCE_STILL_BLOCKED**

Phase type: **rebuild-only**

Generated at UTC: `2026-07-08T11:28:29.237510+00:00`

## Validation gate

- Decision file: `outputs\full_universe_source_acquisition\hkex_validation_decision_v2_12d.csv`
- Validation decision: `HKEX_CANDIDATE_SOURCE_VALIDATION_PASSED_FOR_REBUILD_REVIEW_FULL_SOURCE_STILL_BLOCKED`
- Rebuild allowed by validation: `True`

## Conservative HKEX allowlist

Accepted only:

- Equity / Equity Securities (GEM)
- Equity / Equity Securities (Main Board)
- Equity / Investment Companies
- Equity / Trading Only Securities

Excluded all non-equity, derivative, debt, ETF, REIT, warrant, CBBC and review-required rows.

## Counts

- Baseline rows: 30354
- HKEX candidate rows reviewed: 17589
- HKEX rows added: 2804
- Exclusions: 14785
- New expanded rows: 33158
- Duplicate exchange+ticker keys: 0
- First expansion threshold: 15000
- First expansion unlocked: True
- Full source threshold: 50000
- Full source unlocked: False
- Rows needed full source: 16842

## Accepted subcategory breakdown

- Equity / Equity Securities (Main Board): 2467
- Equity / Equity Securities (GEM): 309
- Equity / Investment Companies: 22
- Equity / Trading Only Securities: 6

## Exclusion reason breakdown

- NON_EQUITY_CATEGORY_EXCLUDED: 14783
- EQUITY_SUBCATEGORY_NOT_IN_ALLOWLIST: 2

## Hard guards

- phase_type: rebuild-only
- network_download_performed: False
- raw_files_modified: False
- workbook_parsed_from_existing_raw: True
- normalization_performed: True
- net_new_filtering_performed: True
- expanded_universe_rebuilt: True
- scoring_recalculated: False
- openai_called: False
- broker_called: False
- full_59k_universe_launched: False
- overwrite_allowed: False

## Outputs

- `outputs\full_universe_source_acquisition\expanded_universe_v2_12e.csv`
- `outputs\full_universe_source_acquisition\expanded_universe_exclusions_v2_12e.csv`
- `outputs\full_universe_source_acquisition\hkex_normalized_candidates_v2_12e.csv`
- `outputs\full_universe_source_acquisition\hkex_rebuild_report_v2_12e.json`
- `outputs\full_universe_source_acquisition\hkex_rebuild_report_v2_12e.md`

## Scope note

v2.12E does not score, call OpenAI, call broker APIs or launch full 59k.

Full 59k remains blocked unless the expanded source reaches the source-complete gate and receives explicit approval.
