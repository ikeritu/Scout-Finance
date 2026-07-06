# Scout Finance ? v2.5G NYSE Usability Decision Gate

- Phase: v2.5G
- Method: nyse_usability_decision_gate_v1
- Created at: 2026-07-06T09:58:03+00:00
- Decision status: **NYSE_USABILITY_DECISION_DEEP_JS_REVIEW_REQUIRED**
- Readiness score: **70/100**
- NYSE usability decision: **REQUIRES_DEEP_JS_PAYLOAD_REVIEW**
- Recommended next phase: **v2.5H ? NYSE Deep JS Payload Review**

## Consolidated evidence

- v2.5D acquisition status: **NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED**
- v2.5D extracted rows: 0
- v2.5E discovery status: **NYSE_ENDPOINT_DISCOVERY_API_CANDIDATE_FOUND**
- v2.5E API candidates: 1
- v2.5E CSV candidates: 0
- v2.5E JavaScript assets: 11
- v2.5F validation status: **NYSE_ENDPOINT_CANDIDATE_VALIDATION_JS_HINTS_FOUND**
- v2.5F endpoint status: **ENDPOINT_HTTP_FAILED**
- v2.5F endpoint status code: 404
- v2.5F JS assets inspected: 8
- v2.5F JS findings: 143

## Source expansion state

- Current included rows: 5648
- Target first expansion rows: 15000
- Minimum full source rows: 50000
- Rows needed for first expansion target: 9352
- Rows needed for full-source threshold: 44352
- Full 59k remains blocked: true
- Expanded universe rebuild allowed: false

## Decision matrix

- raw_html_downloaded: True
- normalized_rows_available: False
- direct_csv_candidate_available: False
- api_candidate_available: True
- proxy_directly_usable: False
- js_payload_hints_available: True
- safe_to_rebuild_expanded_universe: False

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

## Positives

- v2.5D acquisition artifact found: outputs/full_universe_source_acquisition/controlled_nyse_provider_acquisition_real_v2_5d.json
- v2.5E discovery artifact found: outputs/full_universe_source_acquisition/nyse_endpoint_discovery_review_v2_5e.json
- v2.5F validation artifact found: outputs/full_universe_source_acquisition/nyse_endpoint_candidate_validation_v2_5f.json
- v2.5D status accepted: NYSE_PROVIDER_ACQUISITION_RAW_ONLY_REVIEW_REQUIRED
- v2.5E status accepted: NYSE_ENDPOINT_DISCOVERY_API_CANDIDATE_FOUND
- v2.5F status accepted: NYSE_ENDPOINT_CANDIDATE_VALIDATION_JS_HINTS_FOUND
- NYSE raw acquisition produced 0 normalized rows, so rebuild remains blocked.
- No direct CSV candidate detected.
- API candidates detected: 1
- Proxy endpoint direct request failed with 404, so it is not directly usable.
- JS hints detected: 143
- JS assets inspected: 8

## Blockers

- No blockers detected.

## Warnings

- Rows still needed for first expansion target: 9352
- Rows still needed for full-source threshold: 44352

## Recommendation

Do not rebuild expanded_universe from NYSE yet. Continue only with deep JS payload review, or defer NYSE and move to another official provider.

Important: v2.5G is a decision gate only. It does not download data, rebuild expanded_universe, execute scoring, call OpenAI, call a broker, overwrite active outputs, or launch full 59k.