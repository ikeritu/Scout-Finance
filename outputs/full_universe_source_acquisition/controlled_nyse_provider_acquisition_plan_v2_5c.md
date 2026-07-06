# Scout Finance ? v2.5C Controlled NYSE Provider Acquisition Plan

- Phase: v2.5C
- Method: controlled_nyse_provider_acquisition_plan_v1
- Created at: 2026-07-06T07:55:24+00:00
- Plan status: **CONTROLLED_NYSE_PROVIDER_PLAN_READY**
- Readiness score: **95/100**
- Current included rows: 5648
- Rows needed for first expansion target: 9352
- Rows needed for full-source threshold: 44352

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Active outputs overwritten: false

## NYSE provider plan

- Provider ID: `nyse_listed_directory`
- Provider name: NYSE Listed Directory
- Provider type: official_exchange_listing_source
- Priority: 1
- Real acquisition phase: v2.5D
- Mode: PLAN_ONLY_NO_DOWNLOAD
- Expected role: Add official NYSE-listed instrument coverage and compare/merge with existing Nasdaq Trader otherlisted coverage.

## Expected inputs

- nyse_listed_directory_source: `data/raw/source_providers/nyse_listed_directory/` ? format: csv_or_downloaded_exchange_file

## Expected canonical columns

- `ticker`
- `company_name`
- `exchange`
- `country`
- `source_provider`
- `source_file`
- `instrument_type`
- `instrument_scope`
- `classification_confidence`
- `classification_reason`
- `sector`
- `industry`
- `market_cap`
- `raw_exchange_code`
- `raw_etf_flag`
- `raw_test_issue_flag`

## Deduplication rules

- Primary uniqueness key must remain exchange+ticker.
- If NYSE rows duplicate existing Nasdaq Trader otherlisted NYSE rows, keep one canonical record.
- Prefer official exchange-specific provider row when provider confidence is higher.
- Never overwrite active MVP outputs during provider acquisition.
- Write NYSE raw and normalized files in isolated provider folder.

## Risk register

- **HIGH** ? Overlap with Nasdaq Trader otherlisted NYSE rows: Run post-acquisition duplicate comparison by exchange+ticker before rebuilding expanded source.
- **MEDIUM** ? Provider schema drift: Validate headers and row count before canonical normalization.
- **MEDIUM** ? Non-common-stock instruments included: Reuse current instrument classification/exclusion rules before inclusion.
- **MEDIUM** ? Low incremental row gain: Report gross rows, duplicate rows, excluded rows, and net new included rows separately.
- **LOW** ? Network/download instability: Keep network acquisition isolated in v2.5D with timeout and no downstream rebuild by default.

## Acceptance criteria for v2.5D

- Download or acquire NYSE provider file into isolated raw provider folder.
- No OpenAI calls.
- No broker calls.
- No scoring recalculation.
- No full 59k launch.
- No overwrite of active MVP outputs.
- Produce raw acquisition JSON and Markdown report.
- Report network status, URL/source path, file size, row count, headers, and errors.

## Acceptance criteria before v2.5E rebuild

- NYSE provider file exists and is readable.
- Headers/schema are understood.
- Row count is reported.
- Duplicate risk against existing expanded source is measured.
- Instrument classification rules are prepared.
- Commit checkpoint exists before rebuild.

## Positives

- v2.5B provider plan artifact found: outputs/full_universe_source_acquisition/next_provider_acquisition_plan_v2_5b.json
- v2.5A revalidation artifact found: outputs/full_universe_source_acquisition/expanded_source_revalidation_gate_v2_5a.json
- v2.5B plan status accepted: NEXT_PROVIDER_PLAN_READY
- Current expanded source rows confirmed: 5648

## Blockers

- No blockers detected.

## Warnings

- Rows still needed for first expansion target before NYSE acquisition: 9352
- Rows still needed for full-source threshold before NYSE acquisition: 44352

## Recommendation

Proceed to v2.5D as isolated real NYSE provider acquisition. Do not rebuild expanded source until NYSE acquisition output is reviewed.

Important: v2.5C is a planning artifact only. It does not download data, call OpenAI, call a broker, execute scoring, overwrite active outputs, or launch full 59k.