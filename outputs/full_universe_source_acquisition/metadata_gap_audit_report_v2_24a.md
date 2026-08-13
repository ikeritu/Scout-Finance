# Scout Finance — v2.24A Metadata Gap Audit

**Status:** `METADATA_GAP_AUDIT_COMPLETED_NO_DATASET_MODIFICATION`

## Audit basis

This phase is a deterministic audit over metadata coverage evidence computed in v2.23B. The evidence remains valid because `main` still points to the v2.23F closure and the canonical dataset identity is unchanged.

- Dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_21h_activated_operational_reference.csv`
- Rows: **43,089**
- SHA256: `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`

## Primary gaps

| Field | Missing rows | Missing % | Coverage % | Next phase |
|---|---:|---:|---:|---|
| country | 21,154 | 49.0937% | 50.9063% | v2.24B |
| MIC | 32,367 | 75.1166% | 24.8834% | v2.24B |
| currency | 31,778 | 73.7497% | 26.2503% | v2.24B |

## Provider concentration

`cboe_europe_reference_data` has 21,154 rows and accounts for 100.0000% of all missing country, 65.3567% of all missing MIC and 66.5681% of all missing currency. It is therefore the first deterministic mapping target for v2.24B.

## Scorable dry-run impact

On the 33,498-row non-promoted scoring reference: country has 11,790 missing (35.1961%), MIC 22,825 (68.1384%), and currency 22,236 (66.3801%). Production scoring remains blocked.

## Separate taxonomy block

`asset_type` (37,978 missing), `instrument_type` (5,213 missing) and `instrument_scope` (31,519 missing) remain isolated for **v2.24C — Asset Type Normalization Plan**.

## Closure

`v2.24A` is closed as a read-only metadata gap audit. Primary next gate: **v2.24B — Country / MIC / Currency Backfill Plan**.

Guardrails remain unchanged: `canonical_dataset_modified=False`; `metadata_backfill_executed=False`; `production_scoring_authorized=False`; `scoring_promoted=False`; `openai_called=False`; `broker_called=False`; `full59k=DEPRECATED_DEFERRED`.
