# Freeze Candidate Version v2.38CI

Decision: `FREEZE_CANDIDATE_VERSION_LOCKED_WITH_DOCUMENTED_LIMITATIONS`.

This phase freezes the release candidate audited by `v2.38CH`. It does not publish the final product and does not alter ranking, scoring, methodology, weights, datasets, UI, broker workflows or financial-advice guardrails.

## Frozen State

- Source phase: `v2.38CH-release-candidate-audit`
- Source status: `RELEASE_CANDIDATE_AUDIT_PASS_WITH_DOCUMENTED_LIMITATIONS`
- Freeze checks: 40
- Failures: 0
- Warnings: 0
- Blocking issues: 0
- Documented limitations preserved: 14

## Frozen Ranking Counts

- Total: 1111
- Main ranking: 318
- Partial comparability: 373
- Review required: 124
- Blocked: 270
- No adapter: 26

## Guardrails

All freeze guardrails remain closed: no network, no scoring recomputation, no weight change, no methodology change, no dataset mutation, no UI change, no recommendations, no financial advice, no broker action and no final publication.

Next recommended phase: `v2.38CJ-release-handoff`.
