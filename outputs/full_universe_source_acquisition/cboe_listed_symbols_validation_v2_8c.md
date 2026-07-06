# Scout Finance ? v2.8C Cboe Listed Symbols Validation

- Phase: v2.8C
- Method: cboe_listed_symbols_validation_v1
- Created at: 2026-07-06T22:06:07+00:00
- Validation status: **CBOE_VALIDATED_WITH_NET_NEW_CANDIDATES**
- Readiness score: **85/100**
- Cboe decision: **CBOE_USABLE_AS_CANDIDATE_PROVIDER_PENDING_REBUILD_PLAN**
- Recommended next phase: **v2.8D ? Rebuild Expanded Source With Cboe Plan**

## Schema summary

- Listed CSV rows: 1490
- Listed CSV best header line: 0
- Listed CSV fields: `Name, Volume, Ask Size, Ask Price, Bid Size, Bid Price, Last Price, Shares Matched, Shares Routed`
- Listed detected fields: `{'symbol_field': '', 'name_field': 'Name', 'exchange_field': '', 'type_field': ''}`

- Symbols traded/downloaded CSV rows: 1220
- Symbols traded/downloaded CSV best header line: 0
- Symbols traded/downloaded CSV fields: `measurement_month, trade_date, symbol, listed_mic, round_lot_size`
- Symbols traded/downloaded detected fields: `{'symbol_field': 'symbol', 'name_field': '', 'exchange_field': '', 'type_field': ''}`

- Listed XML root: `bats`
- Symbols traded XML root: `cboe`

## Coverage summary

- Current expanded rows: 8007
- Existing exchange+ticker keys loaded: 8007
- Normalized candidate rows: 1220
- Net-new exchange+ticker rows: 1193
- Projected rows if added: 9200
- First expansion unlocked if added: False
- Full source unlocked if added: False

## Download review

- Downloaded symbols_traded CSV URL: `https://cdn.cboe.com/data/us/equities/rpt_cboe_listed_lot_size/cboe_listed_lot_size.csv`
- Proper symbols_traded CSV link candidates discovered: 3
  - `https://cdn.cboe.com/data/us/equities/market_statistics/symbols_traded/edgx/cboe_symbols_traded_edgx.csv`
  - `https://www.cboe.com/us/equities/market_statistics/symbols_traded/?mkt=edgx?download=csv`
  - `https://www.cboe.com/us/equities/market_statistics/symbols_traded/?mkt=edgx?output=csv`

## Outputs

- schema_detail_csv: `outputs/full_universe_source_acquisition/cboe_listed_symbols_schema_detail_v2_8c.csv`
- normalized_candidate_csv: `outputs/full_universe_source_acquisition/cboe_listed_symbols_normalized_candidate_v2_8c.csv`
- net_new_candidates_csv: `outputs/full_universe_source_acquisition/cboe_listed_symbols_net_new_candidates_v2_8c.csv`
- sample_csv: `outputs/full_universe_source_acquisition/cboe_listed_symbols_validation_sample_v2_8c.csv`

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: false
- Active outputs overwritten: false
- Expanded universe rebuilt: false
- Validation only: true

## Positives

- v2.8B acquisition artifact found: outputs/full_universe_source_acquisition/cboe_listed_symbols_acquisition_real_v2_8b.json
- v2.8B acquisition status accepted: CBOE_LISTED_SYMBOLS_ACQUISITION_COMPLETED_WITH_REVIEW_REQUIRED
- Required validation input available: data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.csv
- Required validation input available: data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.xml
- Required validation input available: data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.csv
- Required validation input available: data/raw/source_providers/cboe_listed_symbols/cboe_symbols_traded_raw.xml
- Required validation input available: outputs/full_universe_source_acquisition/cboe_listed_symbols_discovered_links_v2_8b.csv
- Required validation input available: outputs/full_universe_source_acquisition/cboe_listed_symbols_schema_probe_v2_8b.csv
- Required validation input available: data/raw/expanded_universe/expanded_universe_v2_7b.csv
- cboe_us_equities_symbols_traded_downloaded normalized candidate rows: 1220
- Normalized candidate CSV written: outputs/full_universe_source_acquisition/cboe_listed_symbols_normalized_candidate_v2_8c.csv
- Net-new candidate CSV written: outputs/full_universe_source_acquisition/cboe_listed_symbols_net_new_candidates_v2_8c.csv
- Discovered proper symbols_traded CSV link candidates: 3

## Blockers

- No blockers detected.

## Warnings

- No symbol/ticker field detected for data/raw/source_providers/cboe_listed_symbols/cboe_listed_symbols_raw.csv
- v2.8B downloaded Cboe lot-size CSV into symbols_traded slot before the real symbols_traded CSV. v2.8D/v2.8B2 may need corrected download priority.

## Recommendation

Use v2.8D to plan rebuild only if net-new candidates are meaningful; otherwise correct Cboe download priority or close Cboe as reference/review-required.

Important: v2.8C is validation-only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.