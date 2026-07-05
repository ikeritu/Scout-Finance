# Scout Finance ? v2.5B Next Provider Acquisition Plan

- Phase: v2.5B
- Method: next_provider_acquisition_plan_v1
- Created at: 2026-07-05T22:24:44+00:00
- Plan status: **NEXT_PROVIDER_PLAN_READY**
- Readiness score: **90/100**
- Current included rows: 5648
- First expansion target: 15000
- Full-source threshold: 50000
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

## Provider candidates

### 1. NYSE Listed Directory

- Provider ID: `nyse_listed_directory`
- Decision: **NEXT_PROVIDER_CANDIDATE**
- Expected value: HIGH
- Risk: MEDIUM
- Recommended phase: v2.5C
- Role: Close gap for NYSE coverage and validate against Nasdaq Trader otherlisted overlap.
- Notes: Use as the next controlled provider because it was already identified in the source expansion inventory.

### 2. Additional official exchange listing files

- Provider ID: `exchange_official_listings_additional`
- Decision: **QUEUE_AFTER_NYSE**
- Expected value: HIGH
- Risk: MEDIUM
- Recommended phase: v2.5D_or_later
- Role: Increase public equity universe beyond Nasdaq Trader partial coverage.
- Notes: Only add after NYSE route is implemented and validated.

### 3. SEC company tickers/company facts mapping

- Provider ID: `sec_company_tickers`
- Decision: **OPTIONAL_IDENTIFIER_ENRICHMENT**
- Expected value: MEDIUM
- Risk: MEDIUM
- Recommended phase: v2.6_or_later
- Role: Improve identifier mapping and public company coverage, not necessarily exchange-listed universe completeness.
- Notes: Useful later for CIK/ticker mapping, but should not be treated as full listing source by itself.

### 4. Third-party public datasets

- Provider ID: `kaggle_or_third_party_datasets`
- Decision: **DEFER**
- Expected value: MEDIUM
- Risk: HIGH
- Recommended phase: not_first_choice
- Role: Possible row-count expansion, but requires stricter license and freshness review.
- Notes: Do not use before official provider routes unless explicitly reviewed.

## Recommended next phase

- **v2.5C ? Controlled NYSE Provider Acquisition Plan**
- Mode: plan first, no download
- Reason: NYSE was already identified as first-expansion provider candidate.

## Positives

- v2.5A revalidation artifact found: outputs/full_universe_source_acquisition/expanded_source_revalidation_gate_v2_5a.json
- v2.4D closure artifact found: outputs/full_universe_source_acquisition/expanded_source_partial_closure_v2_4d.json
- v2.5A gate decision accepted: EXPANDED_SOURCE_REVALIDATED_PARTIAL_BELOW_TARGET
- Current expanded source has usable rows: 5648

## Blockers

- No blockers detected.

## Warnings

- Rows still needed for first expansion target: 9352
- Rows still needed for full-source threshold: 44352

## Recommendation

Proceed with v2.5C as a plan-only NYSE provider acquisition gate. Do not download more data until that plan is reviewed.

Important: v2.5B is a planning artifact only. It does not download data, call OpenAI, call a broker, execute scoring, overwrite active outputs, or launch full 59k.