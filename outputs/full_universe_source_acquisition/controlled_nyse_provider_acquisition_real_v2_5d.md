# Scout Finance ? v2.5D Controlled NYSE Provider Acquisition Real

- Phase: v2.5D
- Method: controlled_nyse_provider_acquisition_real_v1
- Created at: 2026-07-06T08:16:23+00:00
- Acquisition status: **NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED**
- Readiness score: **60/100**
- Provider: `nyse_listed_directory`
- Source URL: `https://www.nyse.com/listings_directory/stock`
- Network status: **SUCCESS**
- Raw file: `data/raw/source_providers/nyse_listed_directory/nyse_listings_directory_stock.html`
- Raw file size bytes: 73063
- Raw SHA256: `61ddbd85e8fd3634b32c43996be561b8fc955175dde5f3f3c71a7beda806d570`
- Detected HTML tables: 0
- Extracted rows: 0

## Controls

- OpenAI called: false
- Broker called: false
- Market data recalculated: false
- Scoring recalculated: false
- Full 59k universe launched: false
- Financial advice: false
- Network download performed: true
- Active outputs overwritten: false

## Provider outputs

- Provider directory: `data/raw/source_providers/nyse_listed_directory`
- Raw HTML: `data/raw/source_providers/nyse_listed_directory/nyse_listings_directory_stock.html`
- Preliminary normalized CSV: not created
- Sample CSV: `outputs/full_universe_source_acquisition/controlled_nyse_provider_acquisition_real_sample_v2_5d.csv`

## Positives

- v2.5C plan artifact found: outputs/full_universe_source_acquisition/controlled_nyse_provider_acquisition_plan_v2_5c.json
- v2.5C plan status accepted: CONTROLLED_NYSE_PROVIDER_PLAN_READY
- Raw NYSE response written: data/raw/source_providers/nyse_listed_directory/nyse_listings_directory_stock.html
- NYSE listings page downloaded from https://www.nyse.com/listings_directory/stock

## Blockers

- No blockers detected.

## Warnings

- No usable listing rows could be extracted from NYSE HTML without browser automation or a dedicated CSV/API endpoint.
- Raw acquisition succeeded, but normalized provider rows require manual endpoint/API review.

## Recommendation

Review the raw NYSE HTML and identify a stable public CSV/API endpoint before rebuilding expanded source.

Important: v2.5D is an isolated provider acquisition step. It does not rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.