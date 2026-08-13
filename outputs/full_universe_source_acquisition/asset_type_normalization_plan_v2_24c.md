# Scout Finance — v2.24C Asset Type Normalization Plan

**Status:** `ASSET_TYPE_NORMALIZATION_PLAN_COMPLETED_NO_DATASET_MODIFICATION`

## Baseline

Planning-only phase over canonical dataset `expanded_universe_v2_21h_activated_operational_reference.csv` (43,089 rows; SHA256 `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`). No canonical or pointer modification is authorized.

| Field | Present | Missing | Coverage | Distinct known |
|---|---:|---:|---:|---:|
| asset_type | 5,111 | 37,978 | 11.8615% | 9 |
| instrument_type | 37,876 | 5,213 | 87.9018% | 19 |
| instrument_scope | 11,570 | 31,519 | 26.8514% | 12 |

`instrument_type` is the strongest existing taxonomy anchor.

## Provider gap partition

The three audited gaps reconcile exactly to provider buckets:

- CBOE Europe: 21,154 asset + 21,154 scope missing; type complete.
- Nasdaq Listed: 3,244 asset missing; type/scope complete.
- Nasdaq Other Listed: 2,404 asset missing; type/scope complete.
- SEC: 2,359 asset missing; type/scope complete.
- JPX: 3,705 asset + 3,705 scope missing; type complete.
- Cboe US: 1,193 asset missing; type/scope complete.
- HKEX securities list: 2,804 missing in all three fields.
- Missing-provider bucket: 2,013 type + 2,013 scope missing; asset complete.
- Xetra: 1,424 scope missing; asset/type complete.
- TWSE: 696 asset missing; type/scope complete.
- HKEX: 396 missing in all three fields.
- SFC/BVC: 23 asset + 23 scope missing; type complete.
- ASX (1,316) and SGX structured endpoint (358): complete for the three fields.

Totals: **37,978 asset_type**, **5,213 instrument_type**, **31,519 instrument_scope** missing; zero unexplained residual rows.

## Semantic model

Provider vocabularies are heterogeneous and must not be globally string-replaced. Existing evidence includes Nasdaq `COMMON_STOCK / IN_SCOPE` and `ADR / IN_SCOPE_ADR`; CBOE Europe types such as `EQTY` and `ETF`; and ASX combinations such as `ordinary_equity / equity / ordinary_equity`, `a_reit_equity_like / reit / a_reit_equity_like`, and `ordinary_or_equity_like_unclassified / equity_like / ordinary_or_equity_like_unclassified`.

The normalized overlay must keep raw provider values and use three separate contracts:

- `asset_type`: broad family — common equity, ADR equity, REIT/equity-like, preferred equity, fund-like, ETF, fixed income, rights/derivative-like, certificate/structured, other/unresolved.
- `instrument_type`: granular subtype — common stock, ADR, REIT, preferred share, ETF, fund, closed-end fund, bond, note, debenture, right, certificate, structured product, other/unresolved.
- `instrument_scope`: policy-neutral analytical class. It must not silently encode production-score eligibility.

## Prior policy reuse

v2.22C2 identified 9,591 rows for exclusion from its common-equity scoring dry run using explicit categories including ETF, fund, fixed income, preferred instruments, rights and certificates. That policy may corroborate normalization, but name/text matching alone is forbidden because v2.22C2 also found false-positive contexts where fund-like wording coexisted with explicit common-stock/ordinary-share classification.

## Deterministic rules

1. Preserve all existing non-empty raw values.
2. Provider-native classification has precedence.
3. Provider-specific mappings precede generic mappings.
4. Populated field pairs may resolve a missing field only when the relation is deterministic within that provider.
5. Reverse mapping is allowed only when 1:1; never infer a granular subtype from a broad family when multiple possibilities exist.
6. Text/name/ticker patterns cannot be the sole auto-fill evidence.
7. Conflicts become `CONFLICT_REVIEW_REQUIRED`; no overwrite.
8. Ambiguous mappings become `UNRESOLVED_REVIEW_REQUIRED`.
9. Missing-provider rows require stronger evidence.
10. Metadata normalization remains separate from scoring eligibility.

## Provider strategy

- **CBOE Europe:** map provider type to normalized asset/scope only when deterministic. `ETF` is a candidate for deterministic mapping; broad `EQTY` is not automatically common equity because project evidence includes fund-like rows carrying `EQTY`.
- **Nasdaq/Cboe US/SEC:** use validated type/scope pairs to fill broad asset family.
- **JPX/TWSE/Xetra/SFC:** use explicit provider mappings based on their populated fields.
- **HKEX blocks:** keep unclassified rows unresolved unless authoritative/provider-native classification is available; names alone are insufficient.
- **ASX/SGX:** use complete rows as control populations, not as universal vocabulary templates.

## Registry and provenance

v2.24E must consume a versioned registry with at least: `rule_id`, `source_provider`, `source_field`, `source_value`, optional source-scope/exchange constraint, `target_field`, `normalized_value`, `rule_basis`, `rule_confidence`, `source_evidence`, `overwrite_allowed=False`, `active`, `notes`.

Every derived row must record `normalization_rule_id`, `normalization_status`, `normalization_source`, and `normalization_confidence`.

Allowed statuses: `PRESERVED_EXISTING`, `NORMALIZED_DETERMINISTIC`, `UNRESOLVED_REVIEW_REQUIRED`, `CONFLICT_REVIEW_REQUIRED`.

## v2.24E acceptance gates

- exactly 43,089 rows;
- canonical SHA unchanged during dry run;
- baseline/post coverage for all three taxonomy fields;
- fills by provider/field/rule;
- unresolved and conflict counts;
- cross-field consistency matrix;
- 100% provenance for derived values;
- zero silent overwrites;
- operational pointer unchanged;
- no scoring execution/promotion.

Coverage improvement alone is insufficient: deterministic semantics and provenance have precedence.

## Decisions / closure

- Provider-specific normalization approved; global replacements rejected.
- Overlay-first model approved; existing raw values preserved.
- v2.22C2 policy reusable only as corroborating evidence.
- Fully unclassified HKEX rows remain unresolved without authoritative evidence.
- Execution deferred to **v2.24E — Metadata Improvement Dry Run**.
- Promotion/freeze deferred to **v2.24F**.

Guardrails: `canonical_dataset_modified=False`; `active_pointer_modified=False`; `metadata_normalization_executed=False`; `metadata_backfill_executed=False`; `production_scoring_authorized=False`; `scoring_promoted=False`; `full59k=DEPRECATED_DEFERRED`.

**Recommended next phase:** `v2.24D — Provider Quality Matrix`.
