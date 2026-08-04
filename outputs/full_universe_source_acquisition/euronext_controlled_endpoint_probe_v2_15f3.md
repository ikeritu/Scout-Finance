# v2.15F3 - Euronext Controlled Endpoint Probe

Status: **EURONEXT_CONTROLLED_ENDPOINT_PROBE_COMPLETED_PROMISING_ENDPOINTS_REBUILD_STILL_BLOCKED**

Phase type: **controlled-probe-only**

Generated at UTC: `2026-08-04T11:38:01.879683+00:00`

## Current state

- Canonical dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv`
- Current rows: `38287`
- Full source threshold: `50000`
- Rows needed: `11713`
- Source-to-50k completed: `76.6%`
- Full source gate: `BLOCKED`
- Full 59k dry-run: `BLOCKED`

## Probe config

- Max probes: 30
- Max bytes per probe: 250000
- Timeout seconds: 35
- Payload storage: disabled
- Securities extraction: disabled

## Probe summary

- Probe plan rows: 1184
- Selected probe rows: 30
- Results: 30
- HTTP OK count: 30
- Error count: 0
- Promising count: 30
- Medium or better evidence count: 2
- Controlled probe quality: `medium`
- Status counts: `{'200': 30}`
- Shape counts: `{'json_like': 2, 'html_like': 28}`
- Probe type counts: `{'json_or_ajax_metadata_probe': 2, 'live_listing_dynamic_probe': 28}`
- Evidence counts: `{'medium': 2, 'low': 28}`
- Critical failed checks: 0

## First probe results

- probe=fadba7b6f3060cf1 type=json_or_ajax_metadata_probe status=200 shape=json_like evidence=medium promising=True url=https://live.euronext.com/en/instrumentSearch/searchJsonByMic?listMics&amp;instruType=Stock&amp;idBlockSearchBox=134
- probe=d9534f9c8846e89c type=json_or_ajax_metadata_probe status=200 shape=json_like evidence=medium promising=True url=https://live.euronext.com/en/instrumentSearch/searchJSON
- probe=fe79497e18312c5a type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/milan/equities/global-equity-market/list
- probe=1121ea764807f970 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/products/equities/global-equity-market/list
- probe=5695ef8ac07a90eb type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/markets/amsterdam/equities/list?page=0
- probe=4953adaee04eeaeb type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/markets/brussels/equities/list?page=0
- probe=5bcd8a2fdd8549b7 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/markets/dublin/equities/list?page=0
- probe=c937db948d3dc07c type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/markets/lisbon/equities/list?page=0
- probe=f53265b310760355 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/markets/milan/equities/list?page=0
- probe=75646fb3750c1d29 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/markets/oslo/equities/list?page=0
- probe=93d06c459f738e1d type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/markets/paris/equities/list?page=0
- probe=5990df11ae33d87d type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/de/products/equities/list
- probe=2a56bcc391f114c4 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/amsterdam/equities/list
- probe=99b68ed6622d9f72 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/amsterdam/equities/list?page=0
- probe=d232c172541aa1f5 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/brussels/equities/access/list
- probe=aec547e74e6987a3 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/brussels/equities/euronext/list
- probe=626d32fd14de1117 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/brussels/equities/expert/list
- probe=d36227b0b8b4f395 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/brussels/equities/growth/list
- probe=9e196949e8903ae0 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/brussels/equities/list
- probe=dbccb4f4b83c224f type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/brussels/equities/list?page=0
- probe=b5bf5e0bfdd4a2a4 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/dublin/equities/access/list
- probe=82f01ad5400bae67 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/dublin/equities/euronext/list
- probe=a164d98b0c7c267b type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/dublin/equities/growth/list
- probe=14a2d67425f79904 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/dublin/equities/list
- probe=24aad6fd4c8ab2ce type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/dublin/equities/list?page=0
- probe=cc2a04fc7b8b701e type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/lisbon/equities/access/list
- probe=532a51d82c4044ce type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/lisbon/equities/euronext/list
- probe=99b11f834aad81a9 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/lisbon/equities/list
- probe=8ab2f9ffe1f796a2 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/lisbon/equities/list?page=0
- probe=b282ffc0a509f265 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low promising=True url=https://live.euronext.com/en/markets/milan/equities/euronext/list

## Promising probe results

- probe=fadba7b6f3060cf1 type=json_or_ajax_metadata_probe status=200 shape=json_like evidence=medium url=https://live.euronext.com/en/instrumentSearch/searchJsonByMic?listMics&amp;instruType=Stock&amp;idBlockSearchBox=134
- probe=d9534f9c8846e89c type=json_or_ajax_metadata_probe status=200 shape=json_like evidence=medium url=https://live.euronext.com/en/instrumentSearch/searchJSON
- probe=fe79497e18312c5a type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/milan/equities/global-equity-market/list
- probe=1121ea764807f970 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/products/equities/global-equity-market/list
- probe=5695ef8ac07a90eb type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/markets/amsterdam/equities/list?page=0
- probe=4953adaee04eeaeb type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/markets/brussels/equities/list?page=0
- probe=5bcd8a2fdd8549b7 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/markets/dublin/equities/list?page=0
- probe=c937db948d3dc07c type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/markets/lisbon/equities/list?page=0
- probe=f53265b310760355 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/markets/milan/equities/list?page=0
- probe=75646fb3750c1d29 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/markets/oslo/equities/list?page=0
- probe=93d06c459f738e1d type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/markets/paris/equities/list?page=0
- probe=5990df11ae33d87d type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/de/products/equities/list
- probe=2a56bcc391f114c4 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/amsterdam/equities/list
- probe=99b68ed6622d9f72 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/amsterdam/equities/list?page=0
- probe=d232c172541aa1f5 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/brussels/equities/access/list
- probe=aec547e74e6987a3 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/brussels/equities/euronext/list
- probe=626d32fd14de1117 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/brussels/equities/expert/list
- probe=d36227b0b8b4f395 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/brussels/equities/growth/list
- probe=9e196949e8903ae0 type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/brussels/equities/list
- probe=dbccb4f4b83c224f type=live_listing_dynamic_probe status=200 shape=html_like evidence=low url=https://live.euronext.com/en/markets/brussels/equities/list?page=0

## Checks

- v2_15f2_revision_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_extraction_strategy_revision_v2_15f2.json
- probe_plan_exists: PASS (critical) - outputs\full_universe_source_acquisition\euronext_endpoint_probe_plan_v2_15f2.csv
- selected_probe_rows_available: PASS (critical) - selected_rows=30
- endpoint_probe_executed: PASS (critical) - results=30
- at_least_one_http_ok: PASS (warning) - ok_count=30
- promising_endpoint_review: PASS (warning) - promising_count=30
- canonical_dataset_not_read: PASS (critical) - outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- canonical_dataset_not_modified: PASS (critical) - outputs/full_universe_source_acquisition/expanded_universe_v2_14e.csv
- no_payload_saved_to_disk: PASS (critical) - payload_saved_to_disk=False
- no_security_row_extraction: PASS (critical) - security_rows_extracted=False
- no_normalization: PASS (critical) - normalization_performed=False
- no_net_new_filtering: PASS (critical) - net_new_filtering=False
- no_expanded_universe_rebuild: PASS (critical) - expanded_universe_rebuilt=False
- full_source_still_blocked: PASS (critical) - current_rows=38287

## Guards

- Network download performed in v2.15F3: true
- Endpoint probe executed: true
- HTTP body sampled in memory only: true
- Raw payload saved to disk: false
- Raw files downloaded: false
- Raw files modified after write: false
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

## Important note

This phase performs controlled endpoint probing only.

It samples HTTP responses in memory for metadata and superficial payload shape. It does not save raw payloads, does not extract security rows, does not normalize instruments, does not calculate net-new rows, does not read or modify the canonical expanded universe, does not rebuild the expanded universe, does not score equities, does not call OpenAI, does not call broker APIs and does not launch full 59k.

## Recommended next phase

`v2.15F4 - Euronext Endpoint Payload Shape Validation`
