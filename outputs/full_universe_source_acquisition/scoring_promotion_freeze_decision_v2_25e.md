# Scout Finance — v2.25E Scoring Promotion / Freeze Decision

**Status:** `SCORING_FROZEN_NO_PRODUCTION_PROMOTION`

## Final decision

The v2.25B formula is **not promoted**. It is frozen and retained only as a deterministic **data-readiness diagnostic**.

`FREEZE_CURRENT_FORMULA_AS_DATA_READINESS_DIAGNOSTIC`

## Why promotion is blocked

- v2.25A authorized only a controlled dry run and blocked production.
- v2.25C found **46.03% band migration** despite correlation of **0.8906**.
- v2.25D reconstructed every score exactly, but financial attractiveness contributes **0 points**.
- **67.38%** of the mean score comes from metadata quality.
- Only **39.07%** of rows have all seven audited metadata fields.
- **10,523** rows share the same score of 44.5.

Promoting this output would mislabel data completeness and provider quality as investment attractiveness.

## Frozen contract

Allowed:

- metadata and provider QA
- universe-readiness diagnostics
- controlled research comparisons

Forbidden:

- investment recommendations or buy/sell signals
- production ranking
- broker actions
- portfolio allocation

Reopening requires authorized financial inputs, validated labels, a separate formula redesign, repeated stability/explainability gates and an explicit promotion decision.

## Guardrails

- `production_scoring_authorized=False`
- `scoring_promoted=False`
- `diagnostic_score_role=DATA_READINESS_ONLY`
- `operational_scoring_pointer_created=False`
- promoted metadata, universe pointer and historical scores unchanged
- OpenAI and broker not used
- `full59k=DEPRECATED_DEFERRED`
- critical failed checks: **0**

**Recommended next phase:** `v2.25F — Operational Scoring Pointer Hardening`.
