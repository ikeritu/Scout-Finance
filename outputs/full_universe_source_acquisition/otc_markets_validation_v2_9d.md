# Scout Finance ? v2.9D OTC Markets Validation

- Phase: v2.9D
- Method: otc_markets_validation_v1
- Created at: 2026-07-07T12:05:50+00:00
- Validation status: **OTC_MARKETS_VALIDATED_INSUFFICIENT_FOR_EXPANSION**
- Readiness score: **82/100**
- Validation decision: **OTC_MARKETS_VALID_BUT_NOT_ENOUGH_REFERENCE_OR_ENRICHMENT_ONLY**
- Recommended next phase: **v2.9G ? OTC Markets Closure Report OR v2.10A next provider route**

## Provider

- Provider ID: `otc_markets_stock_screener`
- Raw CSV: `data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv`

## Schema

- Raw fields: Symbol, Security Name, Tier, Price, Change %, Vol, Sec Type, Country, State
- Missing expected fields: []
- Symbol field: `Symbol`
- Name field: `Security Name`
- Tier field: `Tier`
- Security type field: `Sec Type`
- Country field: `Country`
- State field: `State`

## Row summary

- Raw rows: 25
- Normalized candidate rows: 25
- Net-new candidate rows: 25
- Overlap rows: 0
- Duplicate exchange+ticker keys: 0
- Issues count: 0

## Distribution

- Tier counts: {'Pink Limited': 16, 'OTCID': 9}
- Security type counts: {'Common Stock': 20, 'Foreign Ordinary Shares': 5}
- Country counts: {'USA': 17, 'Canada': 4, 'China': 2, 'United Arab Emirates': 1, 'Australia': 1}

## Threshold status

- Current expanded rows: 9200
- Projected rows if rebuilt: 9225
- Target first expansion rows: 15000
- Minimum full-source rows: 50000
- First expansion unlocked if rebuilt: False
- Full source unlocked if rebuilt: False
- Rows still needed first expansion after OTC: 5775
- Rows still needed full source after OTC: 40775

## Outputs

- Normalized candidate CSV: `outputs/full_universe_source_acquisition/otc_markets_normalized_candidate_v2_9d.csv`
- Net-new candidate CSV: `outputs/full_universe_source_acquisition/otc_markets_net_new_candidates_v2_9d.csv`
- Duplicates CSV: `outputs/full_universe_source_acquisition/otc_markets_duplicates_v2_9d.csv`
- Issues CSV: `outputs/full_universe_source_acquisition/otc_markets_issues_v2_9d.csv`
- Validation JSON: `outputs/full_universe_source_acquisition/otc_markets_validation_v2_9d.json`
- Validation report: `outputs/full_universe_source_acquisition/otc_markets_validation_v2_9d.md`

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
- Validation only: true

## Positives

- v2.9C acquisition artifact found: outputs/full_universe_source_acquisition/otc_markets_acquisition_real_v2_9c.json
- v2.9C acquisition status accepted: OTC_MARKETS_ACQUISITION_COMPLETED
- v2.9C acquisition decision accepted: OTC_MARKETS_RAW_SOURCE_READY_FOR_VALIDATION
- Validation input available: data/raw/source_providers/otc_markets_stock_screener/otc_markets_stock_screener_raw.csv
- Validation input available: data/raw/expanded_universe/expanded_universe_v2_8e.csv
- Validation input available: data/raw/expanded_universe/expanded_universe_exclusions_v2_8e.csv
- Expected OTC schema fields detected.
- OTC symbol field detected: Symbol
- OTC security name field detected: Security Name
- OTC tier field detected: Tier
- OTC security type field detected: Sec Type

## Blockers

- No blockers detected.

## Warnings

- OTC route is insufficient for first expansion: 25 raw rows < 5800 rows needed.
- OTC net-new rows are insufficient for first expansion: 25 < 5800 rows needed.

## Recommendation

Do not rebuild. Close OTC route as valid schema/reference/enrichment but insufficient for expansion; proceed to next provider route.

Important: v2.9D is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.