# v2.21C3_REVIEW — Missing Official Structured Endpoint Review

Status: **TARGETED_MARKET_MISSING_ENDPOINT_REVIEW_COMPLETED_SPLIT_ROUTE_APPROVED_SGX_READY_COLOMBIA_REGULATORY_DISCOVERY_REQUIRED**

Phase type: **targeted-market-missing-official-structured-endpoint-review**

Generated at UTC: `2026-08-12T22:49:50.902050+00:00`

## Executive summary

v2.21C3_REVIEW resolves the partial endpoint discovery result from v2.21C3.

The decision is to split the route: Singapore/SGX may proceed to structured extraction dry run, while Colombia/BVC remains blocked and moves to a regulator-source discovery path using official Superfinanciera/SIMEV/RNVE candidates.

This phase is review-only. It does not extract candidates, deduplicate, rebuild, promote, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Review decision: `SPLIT_ROUTE_APPROVED_SINGAPORE_READY_COLOMBIA_REGULATORY_DISCOVERY_REQUIRED`
- Approved for Singapore structured extraction: `True`
- Approved for Colombia regulatory discovery: `True`
- Approved for global v2.21C4: `False`
- Approved for v2.21D: `False`
- Operational base rows: `42708`
- Operational base SHA256: `892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127`
- Rollback rows: `38287`
- Rollback SHA256: `cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f`
- Colombia/BVC endpoint ready: `False`
- Singapore/SGX endpoint ready: `True`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Market review

- `COLOMBIA_BVC` — endpoint ready `False` — extraction approved `False` — next `v2.21C3B - Colombia Regulatory Source Discovery`
- `SINGAPORE_SGX` — endpoint ready `True` — extraction approved `True` — next `v2.21C4S - Singapore Structured Candidate Extraction + Dedup Dry Run`

## Route options

- `ROUTE_A_WAIT_FOR_COLOMBIA` — approved `False` — priority `low` — Wait until Colombia/BVC has official structured endpoint
- `ROUTE_B_USE_BVC_REGEX_OR_SHELL_HTML` — approved `False` — priority `rejected` — Use current BVC shell/regex output
- `ROUTE_C_SPLIT_MARKETS` — approved `True` — priority `high` — Split route: advance Singapore; keep Colombia pending
- `ROUTE_D_COLOMBIA_REGULATORY_DISCOVERY` — approved `True` — priority `high` — Open Colombia regulator-source discovery

## Colombia alternative official sources

- `COLOMBIA_SUPERFINANCIERA_SIMEV_VALORES_INSCRITOS` — discovery `True` — extraction `False` — Superintendencia Financiera de Colombia
- `COLOMBIA_SUPERFINANCIERA_RNVE_OFERTAS_PUBLICAS` — discovery `True` — extraction `False` — Superintendencia Financiera de Colombia
- `COLOMBIA_BVC_MANUAL_DOWNLOAD_REVIEW` — discovery `True` — extraction `False` — Bolsa de Valores de Colombia

## Decision register

- `MISSING_ENDPOINT_REVIEW_001` — accepted `True` — Keep v2.21D blocked.
- `MISSING_ENDPOINT_REVIEW_002` — accepted `True` — Do not use BVC shell HTML or regex extraction.
- `MISSING_ENDPOINT_REVIEW_003` — accepted `True` — Approve split route.
- `MISSING_ENDPOINT_REVIEW_004` — accepted `True` — Open Colombia regulatory source discovery.
- `MISSING_ENDPOINT_REVIEW_005` — accepted `True` — Keep operational base unchanged.
- `MISSING_ENDPOINT_REVIEW_006` — accepted `True` — Keep scoring/OpenAI/broker/full59k deferred.

## Checks

- v2_21c3_status_expected: PASS (critical) — TARGETED_MARKET_OFFICIAL_ENDPOINT_DISCOVERY_COMPLETED_PARTIAL_STRUCTURED_ENDPOINTS_FOUND_REVIEW_REQUIRED
- v2_21c3_partial_decision_expected: PASS (critical) — PARTIAL_OR_NO_STRUCTURED_ENDPOINT_COVERAGE_REVIEW_REQUIRED
- v2_21c3_approved_for_v2_21c4_false: PASS (critical) — approved_for_v2_21c4=False
- v2_21c3_approved_for_v2_21d_false: PASS (critical) — approved_for_v2_21d=False
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- schema_column_count_expected: PASS (critical) — columns=33
- colombia_endpoint_not_ready_confirmed: PASS (critical) — colombia_ready=False
- singapore_endpoint_ready_confirmed: PASS (critical) — singapore_ready=True
- split_route_approved: PASS (critical) — Singapore can advance separately; Colombia remains pending.
- colombia_regulatory_discovery_approved: PASS (critical) — Superfinanciera/SIMEV/RNVE discovery route approved.
- global_v2_21c4_not_approved: PASS (critical) — Global Colombia+Singapore extraction remains blocked.
- v2_21d_rebuild_blocked: PASS (critical) — v2.21D remains blocked.
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- dedup_not_performed: PASS (critical) — dedup_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_performed=False
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

Primary: `v2.21C4S - Singapore Structured Candidate Extraction + Dedup Dry Run`

Secondary: `v2.21C3B - Colombia Regulatory Source Discovery`
