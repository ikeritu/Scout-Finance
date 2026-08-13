# v2.21C3B — Colombia Regulatory Discovery + Extraction Decision

Status: **COLOMBIA_REGULATORY_DISCOVERY_EXTRACTION_DECISION_COMPLETED_STRUCTURED_SOURCE_READY_EXTRACTION_APPROVED_NO_DATASET_CHANGES_SCORING_DEFERRED**

Phase type: **colombia-regulatory-discovery-extraction-decision**

Generated at UTC: `2026-08-13T08:23:10.587804+00:00`

## Executive summary

v2.21C3B performs Colombia regulatory source discovery and an extraction decision using only official Superfinanciera/SIMEV/RNVE sources.

This phase does not extract candidates, deduplicate, rebuild, promote Colombia, update pointers, run scoring, call OpenAI, call brokers, or launch full59k.

## Summary

- Colombia decision: `COLOMBIA_STRUCTURED_REGULATORY_SOURCE_READY_EXTRACTION_PLANNING_APPROVED`
- Approved for Colombia structured extraction: `True`
- Approved for Colombia traversal review: `True`
- Sources tested: `12`
- Fetches successful: `12`
- Structured sources found: `8`
- Traversable sources found: `0`
- Sample rows collected: `38`
- Singapore promoted rows: `43066`
- Singapore promoted SHA256: `8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f`
- Critical failed checks: `0`
- Warning failed checks: `0`

## Source validation

- `SFC_SIMEV2_RNVE_HOME` — fetch `True` — score `0` — status `NO_USABLE_STRUCTURED_REGULATORY_SOURCE_FOUND`
- `SFC_SIMEV2_EMISORES_INSCRITOS_VIGENTES` — fetch `True` — score `0` — status `NO_USABLE_STRUCTURED_REGULATORY_SOURCE_FOUND`
- `SFC_SIMEV_FINANCIAL_INSTITUTION_LIST_RNVE` — fetch `True` — score `8` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_VALORES_INSCRITOS_007_001` — fetch `True` — score `18` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_VALORES_INSCRITOS_004_261` — fetch `True` — score `18` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_VALORES_INSCRITOS_050_261` — fetch `True` — score `18` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_PRECIO_ACCIONES_001_001` — fetch `True` — score `14` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_PRECIO_ACCIONES_001_142` — fetch `True` — score `14` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_PRECIO_ACCIONES_002_023` — fetch `True` — score `14` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_PRECIO_ACCIONES_022_053` — fetch `True` — score `14` — status `STRUCTURED_REGULATORY_SOURCE_READY_FOR_EXTRACTION_PLANNING`
- `SFC_RNVE_INFORMATION_PAGE` — fetch `True` — score `0` — status `NO_USABLE_STRUCTURED_REGULATORY_SOURCE_FOUND`
- `SFC_MARKET_VALUE_INFORMATION_PAGE` — fetch `True` — score `6` — status `NO_USABLE_STRUCTURED_REGULATORY_SOURCE_FOUND`

## Decision register

- `COLOMBIA_REG_DISCOVERY_001` — accepted `True` — Do not extract from BVC shell HTML or regex output.
- `COLOMBIA_REG_DISCOVERY_002` — accepted `True` — Use only official Superfinanciera/SIMEV/RNVE sources for Colombia review.
- `COLOMBIA_REG_DISCOVERY_003` — accepted `True` — Approve Colombia structured extraction only if table/field structure is sufficient.
- `COLOMBIA_REG_DISCOVERY_004` — accepted `True` — Keep Singapore promoted artifact unchanged.
- `COLOMBIA_REG_DISCOVERY_005` — accepted `True` — Keep scoring/OpenAI/broker/full59k deferred.

## Checks

- singapore_promotion_status_expected: PASS (critical) — SINGAPORE_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_READY_POINTER_NOT_UPDATED_SCORING_DEFERRED
- singapore_promoted_artifact_approved: PASS (critical) — approved_as_promoted_artifact=True
- singapore_pointer_not_updated: PASS (critical) — pointer_update_performed=False
- operational_base_rows_expected: PASS (critical) — operational_rows=42708
- operational_base_sha_expected: PASS (critical) — 892aaadd2fb87026fa63a935534afe851cbadfb420d48f28b90fd6aedd3f0127
- rollback_rows_expected: PASS (critical) — rollback_rows=38287
- rollback_sha_expected: PASS (critical) — cf88f95efc0f8c9dd58a1a00dc755db1aca7a713bc799eebc8ce6a0bda5f353f
- singapore_promoted_rows_expected: PASS (critical) — singapore_promoted_rows=43066
- singapore_promoted_sha_expected: PASS (critical) — 8b6aa52eca0b7e5625aaeb8875d3806157fe30f7595cd698b5d0071ea2187c2f
- schema_column_count_expected: PASS (critical) — columns=33
- official_source_inventory_created: PASS (critical) — sources=12
- all_sources_official_hosts: PASS (critical) — all seed hosts are official Superfinanciera hosts
- at_least_one_regulatory_fetch_successful: PASS (critical) — successful_fetches=12
- colombia_structured_source_ready: PASS (warning) — structured_sources=8
- colombia_traversal_or_source_review_available: PASS (warning) — structured=8;traversable=0
- candidate_extraction_not_performed: PASS (critical) — candidate_extraction_performed=False
- dedup_not_performed: PASS (critical) — dedup_performed=False
- expanded_rebuild_not_performed: PASS (critical) — expanded_rebuild_performed=False
- singapore_promoted_artifact_not_modified: PASS (critical) — Singapore promoted artifact SHA unchanged
- operational_base_not_modified: PASS (critical) — operational base SHA unchanged
- rollback_not_modified: PASS (critical) — rollback SHA unchanged
- canonical_dataset_not_modified: PASS (critical) — canonical_dataset_modified=False
- active_canonical_not_replaced: PASS (critical) — active_canonical_replaced=False
- pointer_update_not_performed: PASS (critical) — pointer_update_performed=False
- scoring_not_authorized: PASS (critical) — scoring_authorized=False
- openai_not_called: PASS (critical) — openai_called=False
- broker_not_called: PASS (critical) — broker_called=False
- full59k_not_launched: PASS (critical) — full59k_universe_launched=False

## Recommended next phase

`v2.21D_C - Colombia Conditional Build / Freeze`
