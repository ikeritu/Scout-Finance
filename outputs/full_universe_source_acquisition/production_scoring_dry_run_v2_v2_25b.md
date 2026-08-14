# Scout Finance — v2.25B Production Scoring Dry Run v2

**Status:** `PRODUCTION_SCORING_DRY_RUN_V2_COMPLETED_NO_PROMOTION`

## Result

The deterministic v2.23D formula was reapplied to the immutable v2.24F promoted metadata artifact. Exactly **33,498** rows were scored and **9,591** pre-existing non-common-equity policy rows remained excluded.

- Input SHA256: `01fef82316a458c65d42c08cb993feed9e0cc8178f4f7bf4f08835f169bfa74c`
- Output SHA256: `4a041712e66034044388dddb0d556c17dbba4bc1a982a6ae7e43d7b57ded5a8f`
- Mean score: **70.6094**
- Median: **60.4**
- Changed rows vs v2.23D: **16,116**
- Mean absolute delta: **10.0086**
- Maximum absolute delta: **35.4**
- Critical failed checks: **0**

The score remains a deterministic quality/scope/provider dry-run score. It is **not** an investment-attractiveness ranking.

## Guardrails

- `attractiveness_score_available=False`
- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `promoted_metadata_artifact_modified=False`
- `active_pointer_modified=False`
- `openai_called=False`
- `broker_called=False`
- `full59k=DEPRECATED_DEFERRED`

**Recommended next phase:** `v2.25C — Score Stability Audit`.
