# v2.21C3 — Official Endpoint / Downloadable Listing Discovery

Status: **TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_COMPLETED_PARTIAL_STRUCTURED_ENDPOINTS_FOUND_REVIEW_REQUIRED**

Phase type: **targeted-market-official-endpoint-download-discovery**

Generated at UTC: `2026-08-12T22:32:30.750923+00:00`

## Executive summary

v2.21C3 discovers and validates official-domain structured endpoints or downloadable listing candidates for Colombia/BVC and Singapore/SGX.

This phase is discovery-only. It does not accept candidates, deduplicate, rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Discovery decision: `PARTIAL_OR_NO_STRUCTURED_ENDPOINT_COVERAGE_REVIEW_REQUIRED`
- Approved for v2.21C4: `False`
- Approved for v2.21D: `False`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Endpoint candidates tested: `21`
- Endpoint fetches successful: `21`
- Structured endpoint candidates found: `2`
- Markets with structured endpoint: `1`
- Structured sample rows: `80`
- v2.21D blocked: `True`
- Critical failed checks: `0`
- Warning failed checks: `1`

## Market endpoint readiness

- `COLOMBIA_BVC` — ready `False` — structured endpoints `0` — best records `0` — `official_pages_fetched_but_no_structured_records`
- `SINGAPORE_SGX` — ready `True` — structured endpoints `2` — best records `1278` — `structured_endpoint_ready_for_v2_21c4`

## Endpoint validation

- `BVC_LISTADO_EMISORES_MERCADO_LOCAL_PAGE` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/listado-de-emisores-mercado-local`
- `BVC_LISTADO_EMISORES_MERCADO_GLOBAL_PAGE` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/listado-de-emisores-mercado-global`
- `BVC_MERCADO_LOCAL_RENTA_VARIABLE_PAGE` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/mercado-local-en-linea?tab=renta-variable_mercado-local`
- `BVC_ACCIONES_PAGE` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/acciones`
- `SGX_SECURITIES_V1_1_JSON_MINIMAL` — `SINGAPORE_SGX` — status `STRUCTURED_ENDPOINT_CANDIDATE_FOUND` — records `1278` — url `https://api.sgx.com/securities/v1.1?excludetypes=bonds&params=nc%2Ccn%2Cs%2Cp%2Cc%2Cchange_vs_pc%2Cchange_vs_pc_percentage%2Ccx%2Cdp%2Cdpc%2Ctrading_time`
- `SGX_SECURITIES_V1_1_JSON_EXTENDED` — `SINGAPORE_SGX` — status `STRUCTURED_ENDPOINT_CANDIDATE_FOUND` — records `1278` — url `https://api.sgx.com/securities/v1.1?excludetypes=bonds&params=nc%2Cadjusted-vwap%2Cb%2Cbv%2Cp%2Cc%2Cchange_vs_pc%2Cchange_vs_pc_percentage%2Ccx%2Ccn%2Cdp%2Cdpc%2Cdu%2Ced%2Cfn%2Ch%2Ciiv%2Ciopv%2Clt%2Cl%2Co%2Cp_%2Cpv%2Cptd%2Cs%2Csv%2Ctrading_time%2Cv_%2Cv%2Cvl%2Cvwap%2Cvwap-currency`
- `SGX_SECURITIES_PRICES_PAGE` — `SINGAPORE_SGX` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.sgx.com/stock-exchange/securities-prices?code=stocks`
- `SGX_CORPORATE_INFORMATION_PAGE` — `SINGAPORE_SGX` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.sgx.com/securities/corporate-information?pagesize=100`
- `DISCOVERED__mercado_local_en_linea_2` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/mercado-local-en-linea?tab=renta-variable_mercado-global-colombiano`
- `DISCOVERED__mercados_productos_y_servicios_renta_variable_4` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/mercados/productos-y-servicios/renta-variable`
- `DISCOVERED__renta_variable_descripcion_general_5` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/renta-variable-descripcion-general`
- `DISCOVERED__derivados_de_renta_variable_7` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/derivados-de-renta-variable`
- `DISCOVERED__renta_variable_8` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/renta-variable`
- `DISCOVERED__mercados_post_negociacion_servicios_a_emisores_9` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/mercados/post-negociacion/servicios-a-emisores`
- `DISCOVERED__administracion_de_acciones_10` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/administracion-de-acciones`
- `DISCOVERED__ser_un_emisor_11` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/ser-un-emisor`
- `DISCOVERED__se_un_emisor_de_renta_fija_12` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/se-un-emisor-de-renta-fija`
- `DISCOVERED__se_un_emisor_de_renta_variable_13` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/se-un-emisor-de-renta-variable`
- `DISCOVERED__comite_de_emisores_14` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/comite-de-emisores`
- `DISCOVERED__resultados_e_informacion_sobre_emisores_15` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/resultados-e-informacion-sobre-emisores`
- `DISCOVERED__emisores_con_reconocimiento_ir_16` — `COLOMBIA_BVC` — status `NO_STRUCTURED_CANDIDATE_RECORDS_FOUND` — records `0` — url `https://www.bvc.com.co/emisores-con-reconocimiento-ir`

## Decision register

- `ENDPOINT_DISCOVERY_001` — accepted `True` — Do not use v2.21C regex-only candidates.
- `ENDPOINT_DISCOVERY_002` — accepted `True` — Use only official-domain structured endpoints or downloadable files.
- `ENDPOINT_DISCOVERY_003` — accepted `True` — Require structured extraction retry before rebuild.
- `ENDPOINT_DISCOVERY_004` — accepted `True` — Keep operational base unchanged.
- `ENDPOINT_DISCOVERY_005` — accepted `True` — Keep scoring/OpenAI/broker/full59k deferred.

## Checks

- v2_21b_status_expected: PASS (critical) — TARGETED_MARKET_ACQUISITION_RAW_VALIDATION_COMPLETED_COLOMBIA_SINGAPORE_RAW_SOURCES_AVAILABLE_NO_DATASET_CHANGES_SCORING_DEFERRED
- v2_21c_status_expected: PASS (critical) — TARGETED_MARKET_CANDIDATE_EXTRACTION_DEDUP_DRY_RUN_COMPLETED_NEW_CANDIDATES_READY_FOR_REBUILD_NO_DATASET_CHANGES_SCORING_DEFERRED
- v2_21c2_status_expected: PASS (critical) — TARGETED_MARKET_CANDIDATE_FALSE_POSITIVE_REVIEW_COMPLETED_ACCEPTED_CANDIDATES_INVALIDATED_REBUILD_BLOCKED_SOURCE_DISCOVERY_REQUIRED
- v2_21c2_blocks_v2_21d: PASS (critical) — v2_21d_blocked=True
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_column_count_expected: PASS (critical) — columns=33
- endpoint_inventory_created: PASS (critical) — endpoint_inventory=21
- endpoint_fetches_attempted: PASS (critical) — fetch_rows=21;inventory=21
- at_least_one_endpoint_fetch_successful: PASS (critical) — successes=21
- all_markets_structured_endpoint_ready: FAIL (warning) — ready_markets=1;required=2
- at_least_one_market_structured_endpoint_ready: PASS (warning) — ready_markets=1
- discovery_only_no_candidate_acceptance: PASS (critical) — v2.21C3 does not accept or deduplicate candidates
- structured_extraction_not_performed: PASS (critical) — structured candidate extraction deferred to v2.21C4
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21C3_REVIEW - Missing Official Structured Endpoint Review`
