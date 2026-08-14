# Scout Finance — v2.24F Metadata Promotion / Freeze Decision

**Status:** `METADATA_PROMOTION_FREEZE_DECISION_COMPLETED_PROMOTED_ARTIFACT_CREATED_POINTER_UNCHANGED`

## Decision

The v2.24E deterministic overlay is **approved and promoted as a controlled immutable metadata artifact**. The existing canonical dataset and active operational pointer remain unchanged; activation is deliberately deferred rather than performed silently.

- Promoted dataset: `outputs/full_universe_source_acquisition/expanded_universe_v2_24f_metadata_promoted.csv`
- Rows: **43,089**
- Promoted SHA256: `01fef82316a458c65d42c08cb993feed9e0cc8178f4f7bf4f08835f169bfa74c`
- Deterministically improved cells: **56,002**
- Provenance: **100%**
- Overwrites: **0**
- Critical failed checks: **0**

## Freeze boundary

HKEX, missing-provider rows and ambiguous CBOE Europe geography remain frozen and unresolved. No value is guessed. ASX/SGX controls remain unchanged through the accepted v2.24E overlay.

## Operational guardrails

- `metadata_artifact_promoted=True`
- `canonical_dataset_modified=False`
- `active_pointer_modified=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.24G — Metadata Closure Report`.
