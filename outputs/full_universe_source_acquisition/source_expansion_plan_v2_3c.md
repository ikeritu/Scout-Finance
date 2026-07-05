# Scout Finance ? v2.3C Source Expansion Plan

- Phase: v2.3C
- Method: source_expansion_plan_v1
- Created at: 2026-07-05T09:47:08+00:00
- Plan status: **SOURCE_EXPANSION_PLAN_READY**
- Readiness score: **100/100**
- Strategy input decision: **EXTERNAL_OR_EXPANDED_SOURCE_REQUIRED**
- Expected full rows: 59000
- Minimum full source rows: 50000
- Target first expansion rows: 15000

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false

## Canonical schema

- `ticker` ? required: Normalized ticker/symbol. Must be uppercase and non-empty.
- `company_name` ? required: Company/security name from source.
- `exchange` ? required: Exchange or market identifier.
- `country` ? required: Country or market region.
- `sector` ? optional: Sector if available.
- `industry` ? optional: Industry if available.
- `market_cap` ? optional: Market capitalization if available.
- `source_provider` ? required: Provider or exchange source name.
- `source_file` ? required: Original source file path or source identifier.
- `instrument_type` ? required: COMMON_STOCK, ETF, FUND, ADR, PREFERRED, WARRANT, etc.
- `instrument_scope` ? required: IN_SCOPE or OUT_OF_SCOPE for Scout Finance universe.
- `classification_confidence` ? required: HIGH, MEDIUM or LOW confidence after classification.
- `classification_reason` ? required: Short reason for instrument inclusion/exclusion.

## Source groups

### Priority 1 ? US official exchange symbol lists

- Status: PRIMARY_ROUTE
- Risk: LOW_MEDIUM
- Target exchanges: NASDAQ, NYSE, AMEX
- Expected use: Expand and refresh current US public-market universe.

### Priority 2 ? Additional North American listings

- Status: SECONDARY_ROUTE
- Risk: MEDIUM
- Target exchanges: NYSE Arca, Cboe, OTC candidates only if explicitly approved
- Expected use: Increase coverage after core US exchanges are stable.

### Priority 3 ? European official exchange lists

- Status: LATER_ROUTE
- Risk: HIGH
- Target exchanges: London, Euronext, Frankfurt/Xetra, Madrid/BME, SIX
- Expected use: Move toward global universe once US expansion is reproducible.

### Priority 4 ? Asia-Pacific official exchange lists

- Status: LATER_ROUTE
- Risk: HIGH
- Target exchanges: Tokyo, Hong Kong, Singapore, Australia
- Expected use: Long-term global expansion.

## Deduplication rules

- Primary key must be exchange + ticker, not ticker alone.
- Ticker collisions across exchanges must be preserved as separate instruments.
- Exact duplicate exchange+ticker rows must be collapsed.
- If duplicate rows have conflicting company names, keep the longest non-empty name and flag warning.
- If duplicate rows have conflicting country/exchange values, flag blocker for that source.
- Never merge different instrument types under one ticker without explicit classification.

## Exclusion rules

- Exclude instruments without ticker.
- Exclude obvious test rows, placeholders and malformed symbols.
- Exclude warrants, rights, units and preferred shares from IN_SCOPE unless explicitly approved.
- Classify ETFs/funds separately; do not mix with common-stock scouting unless approved.
- ADR treatment must be explicit: either IN_SCOPE_ADR or OUT_OF_SCOPE_ADR.
- Rows with low classification confidence must be reviewable before full dry-run.

## Validation gates

### v2.3D ? Source Provider Inventory

- Goal: Create a machine-readable inventory of target source providers/exchanges.
- Unlock condition: Providers listed with expected schema and acquisition method.

### v2.3E ? Expanded Source Builder Skeleton

- Goal: Create a no-network skeleton that combines local provider files if present.
- Unlock condition: Builder can run safely without downloads and without scoring.

### v2.3F ? Expanded Source Validation

- Goal: Validate the expanded source using canonical schema and row thresholds.
- Unlock condition: At least 15000 rows for first expansion, later 50000+ rows for full gate.

### repeat_v2.2C ? Repeat Source Validation

- Goal: Run v2.2C against the expanded source.
- Unlock condition: Ticker mapping, duplicates and blockers clean.

### repeat_v2.2E ? Repeat Full Dry Run Gate

- Goal: Run v2.2E again after expanded source exists.
- Unlock condition: Source rows >= 50000 and safety controls clean.

## Positives

- v2.3B strategy found and readable: outputs/full_universe_source_acquisition/full_universe_source_strategy_v2_3b.json
- v2.3B confirms that an expanded source is required.

## Blockers

- No blockers detected.

## Warnings

- No warnings detected.

## Recommendation

Proceed to v2.3D Source Provider Inventory. Do not download data yet.

Important: v2.3C is a plan only. It does not download data, execute scoring, call OpenAI, call a broker, or launch full 59k.