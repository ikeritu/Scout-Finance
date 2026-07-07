# Scout Finance ? v2.9G OTC Markets Closure Report

- Phase: v2.9G
- Method: otc_markets_closure_report_v1
- Created at: 2026-07-07T12:49:21+00:00
- Closure status: **OTC_MARKETS_CLOSED_VALID_BUT_NOT_ENOUGH**
- Readiness score: **95/100**
- Closure decision: **OTC_MARKETS_CLOSED_REFERENCE_OR_ENRICHMENT_ONLY_NO_REBUILD**
- Recommended next phase: **v2.10A ? Next Provider Route**

## Closed block

- v2.9A ? Next Official Provider Route
- v2.9B ? OTC Markets Acquisition Plan
- v2.9C ? OTC Markets Acquisition Real
- v2.9D ? OTC Markets Validation
- v2.9G ? OTC Markets Closure Report

## Skipped phases

- v2.9E ? Rebuild Expanded Source With OTC Markets
- v2.9F ? Validate Expanded Source With OTC Markets

Skip reason: OTC Markets produced only 25 net-new rows, below the 5800 rows required to consider expansion rebuild.

## Final result

- Current expanded rows: 9200
- Current exclusions rows: 10056
- OTC raw rows: 25
- OTC normalized candidate rows: 25
- OTC net-new candidate rows: 25
- OTC duplicate exchange+ticker keys: 0
- OTC issues: 0
- Projected rows if rebuilt: 9225

## Threshold status

- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- Expected full rows: 59000
- First expansion unlocked if rebuilt: False
- Full source unlocked if rebuilt: False
- Rows still needed first expansion after OTC: 5775
- Rows still needed full source after OTC: 40775

## Provider assessment

- Schema valid: true
- Raw download success: true
- Usable for bulk expansion: false
- Usable for reference: true
- Usable for enrichment: true
- Rebuild allowed: false
- Reason: valid schema and 25 net-new rows, but insufficient for expansion target.

## Decision

```text
OTC_MARKETS_CLOSED_VALID_BUT_NOT_ENOUGH
OTC_MARKETS_REFERENCE_OR_ENRICHMENT_ONLY
REBUILD_SKIPPED
FULL_59K_REMAINS_BLOCKED
NEXT_RECOMMENDED_PHASE: v2.10A_NEXT_PROVIDER_ROUTE
```

## Next options

### Option A ? Continue source expansion

- Next phase: `v2.10A ? Next Provider Route`
- Status: recommended

### Option B ? Return to product/MVP

- Next phase: product/MVP roadmap refresh
- Status: available

## Tag recommendation

- `v2.9_otc_markets_closed_valid_but_not_enough`

## Controls

- Network download performed: false
- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false
- Closure only: true
- Rebuild skipped: true

## Positives

- v2.9A route artifact found: outputs/full_universe_source_acquisition/next_official_provider_route_v2_9a.json
- v2.9B OTC acquisition plan artifact found: outputs/full_universe_source_acquisition/otc_markets_acquisition_plan_v2_9b.json
- v2.9C OTC acquisition real artifact found: outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.json
- v2.9D OTC validation artifact found: outputs/full_universe_source_acquisition/otc_markets_validation_v2_9d.json
- Closure input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Closure input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv
- Closure input available: data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv
- Closure input available: data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_page.html
- v2.9A route status accepted: NEXT_OFFICIAL_PROVIDER_ROUTE_READY
- v2.9A route decision accepted: OTC_MARKETS_SELECTED_AS_NEXT_PROVIDER_ROUTE
- v2.9B plan status accepted: OTC_MARKETS_ACQUISITION_PLAN_READY
- v2.9B plan decision accepted: OTC_MARKETS_CONTROLLED_ACQUISITION_APPROVED
- v2.9C acquisition status accepted: OTC_MARKETS_ACQUISITION_COMPLETED
- v2.9C acquisition decision accepted: OTC_MARKETS_RAW_SOURCE_READY_FOR_VALIDATION
- v2.9D validation status accepted: OTC_MARKETS_VALIDATED_INSUFFICIENT_FOR_EXPANSION
- v2.9D validation decision accepted: OTC_MARKETS_VALID_BUT_NOT_ENOUGH_REFERENCE_OR_ENRICHMENT_ONLY

## Blockers

- No blockers detected.

## Warnings

- OTC Markets route downloaded and validated successfully, but only 25 net-new rows were found.
- OTC Markets is not enough to unlock the 15000-row first expansion target.
- OTC Markets is not enough to unlock the 50000-row full-source threshold.
- v2.9E rebuild is explicitly skipped because 25 net-new rows are far below the 5800-row minimum needed.
- Full 59k dry-run remains blocked.

## Recommendation

Close v2.9 with tag, skip v2.9E/v2.9F, and proceed to v2.10A Next Provider Route.

Important: v2.9G is closure-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.