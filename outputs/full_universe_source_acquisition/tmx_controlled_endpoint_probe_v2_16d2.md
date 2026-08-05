# v2.16D2 - TMX Controlled Endpoint Probe

Status: **TMX_CONTROLLED_ENDPOINT_PROBE_COMPLETED_NO_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED**

Phase type: **controlled-endpoint-probe-only**

Generated at UTC: `2026-08-05T08:31:45.369483+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Probe summary

- v2.16D status: `TMX_VALIDATION_COMPLETED_ENDPOINT_SEEDS_DETECTED_REBUILD_STILL_BLOCKED`
- v2.16D recommended next phase: `v2.16D2 - TMX Controlled Endpoint Probe`
- Seed rows loaded: `873`
- Selected probe seeds: `1`
- Probe results: `1`
- Max probes: `40`
- OK count: `1`
- Error count: `0`
- Promising count: `0`
- Medium/better evidence count: `0`
- JSON-like count: `0`
- HTML-like count: `1`
- JS-like count: `0`
- Status counts: `{'200': 1}`
- Shape counts: `{'html_like': 1}`
- Evidence counts: `{'low': 1}`
- Critical failed checks: `0`

## Probe results preview

- `52492a2a188c4330` source=`tmx_listed_company_directory` status=200 ok=True shape=html_like evidence=low promising=False url=`https://www.tmx.com/TSXVenture/TSXVentureHttpController?GetPage=LcdbSearch` notes=`html_like_with_markers_review_only`

## Checks

- v2_16d_validation_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_validation_v2_16d.json
- v2_16d_seeds_csv_exists: PASS (critical) — outputs\full_universe_source_acquisition\tmx_candidate_endpoint_seeds_v2_16d.csv
- v2_16d_status_valid: PASS (critical) — TMX_VALIDATION_COMPLETED_ENDPOINT_SEEDS_DETECTED_REBUILD_STILL_BLOCKED
- v2_16d_recommended_d2: PASS (critical) — v2.16D2 - TMX Controlled Endpoint Probe
- allowed_seeds_loaded: PASS (critical) — seed_rows=873
- probe_seeds_selected: PASS (critical) — selected=1
- controlled_probe_executed: PASS (critical) — results=1
- at_least_one_http_ok: PASS (warning) — ok_count=1
- medium_or_better_evidence_review: FAIL (warning) — medium_or_better=0
- promising_endpoint_review: FAIL (warning) — promising_count=0
- error_count_review: PASS (warning) — error_count=0
- no_raw_payload_saved_to_disk: PASS (critical) — payload_saved_to_disk=False
- query_sweep_not_performed: PASS (critical) — query_sweep_performed=False
- candidate_rows_not_extracted: PASS (critical) — candidate_rows_extracted=False
- security_rows_not_extracted: PASS (critical) — security_rows_extracted=False
- canonical_dataset_not_read: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) — outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- normalization_not_performed: PASS (critical) — normalization_performed=False
- net_new_filtering_not_performed: PASS (critical) — net_new_filtering_performed=False
- expanded_universe_not_rebuilt: PASS (critical) — expanded_universe_rebuilt=False
- full_source_still_blocked: PASS (critical) — 38287 < 50000

## Guards

- Network download performed in v2.16D2: true
- Controlled endpoint probe executed: true
- Raw payload saved to disk: false
- HTTP body sampled in memory only: true
- New raw files downloaded: false
- Query sweep performed: false
- Generated URLs or parameter sweep: false
- Candidate rows extracted: false
- Security rows extracted: false
- Canonical dataset read: false
- Canonical dataset modified: false
- Normalization performed: false
- Net-new filtering performed: false
- Expanded universe rebuilt: false
- Repo-wide renormalization performed: false
- Scoring recalculated: false
- OpenAI called: false
- Broker called: false
- Full 59k universe launched: false
- Overwrite allowed: false

## Conclusion

TMX controlled endpoint probe completed.

This phase probes only endpoint seeds already allowed by v2.16D. It does not generate new URLs, does not perform a query sweep, does not save raw payloads, does not extract securities or candidates, does not read or modify the canonical expanded universe, does not normalize, does not calculate net-new rows and does not rebuild.

## Recommended next phase

`v2.16E - TMX Candidate Extraction Dry Run`
