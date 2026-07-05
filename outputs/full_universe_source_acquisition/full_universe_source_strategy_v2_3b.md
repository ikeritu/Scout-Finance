# Scout Finance ? v2.3B Full Universe Source Strategy

- Phase: v2.3B
- Method: full_universe_source_strategy_v1
- Created at: 2026-07-05T09:34:19+00:00
- Decision: **EXTERNAL_OR_EXPANDED_SOURCE_REQUIRED**
- Readiness score: **60/100**
- Expected full rows: 59000
- Minimum full source rows: 50000

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false

## v2.3A audit input

- path: outputs/full_universe_source_acquisition/full_universe_source_acquisition_audit_v2_3a.json
- exists: True
- audit_status: NO_FULL_SOURCE_FOUND_PARTIAL_AVAILABLE
- csv_files_scanned: 194
- full_candidates_count: 0
- partial_candidates_count: 13

## Best local candidate

- Path: `data/raw/universe_source_real.csv`
- Rows: 7053
- Status: PARTIAL_SOURCE_ONLY
- Scope: PARTIAL_REAL_SOURCE_FOR_SMALL_BATCH
- Ticker column: Symbol

## Strategy options

### Strategy A ? Expand current public exchange universe ? **RECOMMENDED**

Build a larger source by combining official symbol lists from NASDAQ/NYSE/AMEX and additional exchanges.

- Risk: MEDIUM
- Next step: Create v2.3C source expansion plan and define provider/exchange list.

Pros:
- Auditable and reproducible.
- Can reuse current Symbol -> ticker mapping.
- Keeps the project close to real public market data.
- Best fit for incremental validation.

Cons:
- May still not reach 59k without global exchanges.
- Requires careful deduplication by ticker/exchange/country.
- Needs clear source provenance per exchange.

### Strategy B ? Global multi-exchange universe

Create a broader global universe across US, Europe, Asia and other listed markets.

- Risk: HIGH
- Next step: Use only after Strategy A is stable.

Pros:
- Most likely path to 50k-59k instruments.
- Better long-term fit for global scouting.

Cons:
- Higher normalization complexity.
- Ticker collisions across exchanges are likely.
- Country, currency and exchange metadata become mandatory.

### Strategy C ? Close 59k as future and keep 5k-7k mode

Accept the current partial universe as the operating universe for now.

- Risk: LOW
- Next step: Tag current state and continue with MVP/product improvements.

Pros:
- Lowest technical risk.
- Current pipeline already validates partial source and small batch.
- Allows moving back to product features.

Cons:
- Does not satisfy the original 59k ambition.
- Full 59k dry-run remains blocked.

### Strategy D ? External complete dataset

Find or purchase/download a complete listed-companies dataset and validate it.

- Risk: MEDIUM_HIGH
- Next step: Only use if license, freshness and schema are clear.

Pros:
- Fastest route if a trustworthy dataset is available.
- Could immediately unlock v2.2C/v2.2E repeat.

Cons:
- Licensing and freshness risk.
- Potential hidden quality issues.
- May introduce non-reproducible dependency.

## Positives

- v2.3A audit found and readable: outputs/full_universe_source_acquisition/full_universe_source_acquisition_audit_v2_3a.json
- CSV files scanned in v2.3A: 194
- Best local candidate: data/raw/universe_source_real.csv with 7053 rows.

## Blockers

- No blockers detected.

## Warnings

- No local full universe source exists.
- Current local universe is partial and cannot unlock full 59k.

## Recommendation

Do not run full 59k. Choose a source expansion strategy first. Recommended route: build an expanded public-market universe by combining official exchange symbol lists, then normalize and validate it before repeating v2.2C and v2.2E.

Important: v2.3B is a strategy gate only. It does not download data, execute scoring, call OpenAI, call a broker, or launch full 59k.