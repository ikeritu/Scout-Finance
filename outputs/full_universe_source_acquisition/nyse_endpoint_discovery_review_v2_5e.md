# Scout Finance ? v2.5E NYSE Endpoint Discovery Review

- Phase: v2.5E
- Method: nyse_endpoint_discovery_review_v1
- Created at: 2026-07-06T08:31:31+00:00
- Discovery status: **NYSE_ENDPOINT_DISCOVERY_API_CANDIDATE_FOUND**
- Readiness score: **75/100**
- Usability decision: **POTENTIALLY_USABLE_AFTER_ENDPOINT_VALIDATION**
- Raw HTML: `data/raw/source_providers/nyse_listed_directory/nyse_listings_directory_stock.html`
- Candidate count: 39
- API candidates: 1
- GraphQL candidates: 0
- CSV candidates: 0
- JSON candidates: 0
- JavaScript assets: 11

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

## Candidate type counts

- other: 22
- javascript_asset: 11
- listing_related: 5
- api_candidate: 1

## Top candidates

- score 35 ? listing_related ? `https://www.nyse.com/listings_directory/stock`
- score 30 ? api_candidate ? `https://www.nyse.com/api/sites/nyse/proxy`
- score 25 ? listing_related ? `https://www.nyse.com/listings-process`
- score 25 ? listing_related ? `https://www.nyse.com/listings/gallery`
- score 25 ? listing_related ? `https://www.nyse.com/listings/resources`
- score 20 ? listing_related ? `https://listingmanager.nyse.com`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks//var/opt/jenkins/workspace/ont-end-monorepo_release_2026-26/packages/website-components/build/components/feedback/Spinner-DwaMFcMk.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/__generated__/components/demos-BOS4m3ic.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/__generated__/components/main-Bg6Hb68w.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/__generated__/components/meta-BWKtRhNE.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/node_modules/-pnpm/@theice-pushpop@3-5-0_@types-express@4-17-25/node_modules/@theice/pushpop/build/array/replace-IbWvJqX2.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/node_modules/-pnpm/date-fns@2-30-0/node_modules/date-fns/addYears/index-js-commonjs-es-import-N9QxKcO-.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/node_modules/-pnpm/react-router@6-30-1_react@18-3-1/node_modules/react-router/dist/index-js-commonjs-proxy-CNaJNpJV.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/shared/breadcrumb-context/BreadCrumbContext-DDWejWVZ.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/shared/utils/isCmsTemplateName-CHdGwdya.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/chunks/shared/utils/shouldUseProxy-Bv9cgI89.js`
- score 10 ? javascript_asset ? `https://static.nyse.com/cms/41.10.2/hydrate.js`
- score 5 ? other ? `http://localnyse:3000`
- score 5 ? other ? `https://careers.ice.com/jobs?keywords=NYSE&sortBy=relevance&page=1`
- score 5 ? other ? `https://connect.nyse.com/Registration/Signup.aspx`
- score 5 ? other ? `https://static.nyse.com`
- score 5 ? other ? `https://static.nyse.com/cms/41.10.2/assets/icegroupweb-nyse.css`
- score 5 ? other ? `https://static.nyse.com/cms/41.10.2/assets/nyse.css`
- score 5 ? other ? `https://www.facebook.com/nyse`
- score 5 ? other ? `https://www.instagram.com/nyse`
- score 5 ? other ? `https://www.linkedin.com/company/nyse`
- score 5 ? other ? `https://www.nyse.com`
- score 5 ? other ? `https://www.nyse.com/article/nyse-closing-auction-insiders-guide`
- score 5 ? other ? `https://www.nyse.com/data-insights`
- score 5 ? other ? `https://www.nyse.com/data-products`

## Keyword counts

- nyse: 166
- listings: 24
- directory: 8
- stock: 7
- equity: 5
- instrument: 5
- quote: 2
- api: 1
- symbol: 1
- __next_data__: 0
- apollo: 0
- application/json: 0
- csv: 0
- download: 0
- graphql: 0
- mft: 0
- next_data: 0
- ticker: 0

## Positives

- v2.5D acquisition artifact found: outputs/full_universe_source_acquisition/controlled_nyse_provider_acquisition_real_v2_5d.json
- v2.5D acquisition status accepted: NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED
- Raw NYSE HTML found: data/raw/source_providers/nyse_listed_directory/nyse_listings_directory_stock.html
- Endpoint/asset candidates detected: 39
- Potential API/JSON candidates detected: api=1, graphql=0, json=0
- JavaScript assets detected for possible follow-up inspection: 11

## Blockers

- No blockers detected.

## Warnings

- No direct CSV candidate detected.

## Recommendation

Proceed to v2.5F to inspect candidate endpoints/assets before deciding whether NYSE is usable.

Important: v2.5E is an endpoint discovery review only. It does not download new data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.