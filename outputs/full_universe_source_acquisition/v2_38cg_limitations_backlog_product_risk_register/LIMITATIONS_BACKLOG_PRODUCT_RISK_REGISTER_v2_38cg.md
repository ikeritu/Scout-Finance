# Limitations Backlog And Product Risk Register v2.38CG

Decision: `PRODUCT_RISK_REGISTER_READY_WITH_NON_BLOCKING_LIMITATIONS`.

This phase consolidates known limitations, product risks, environment warnings and technical debt before final release-candidate audit. It does not change scoring, ranking, methodology, weights, datasets, UI, recommendations, network behavior or broker capabilities.

## Executive Summary

- Risks registered: 14
- Blocking risks: 0
- Backlog limitations: 11
- Environment warnings: 2
- Product positioning risks: 2
- Legal/compliance risks: 1

## Categories

- `DATA_COVERAGE`: 4
- `DATA_QUALITY`: 1
- `ENVIRONMENT`: 2
- `LEGAL_COMPLIANCE`: 1
- `METHODOLOGY`: 1
- `OPERATIONAL`: 1
- `PACKAGING`: 1
- `PRODUCT_POSITIONING`: 2
- `UX`: 1

## Risks

- `RISK-001` Ranking experimental may be read as investment advice (HIGH, MITIGATED). Blocking: `false`.
- `RISK-002` 270 assets blocked by low real factor coverage (MEDIUM, ACCEPTED_LIMITATION). Blocking: `false`.
- `RISK-003` 26 assets have no scoring adapter (MEDIUM, ACCEPTED_LIMITATION). Blocking: `false`.
- `RISK-004` 124 assets require manual or special-model review (HIGH, DEFERRED). Blocking: `false`.
- `RISK-005` No real browser screenshots in v2.38CF environment (MEDIUM, OPEN). Blocking: `false`.
- `RISK-006` Manifest-based package without heavy ZIP (LOW, ACCEPTED_LIMITATION). Blocking: `false`.
- `RISK-007` Windows local environment dependency drift (MEDIUM, MITIGATED). Blocking: `false`.
- `RISK-008` Cboe Europe mass identity expansion deferred (MEDIUM, DEFERRED). Blocking: `false`.
- `RISK-009` UK official source automation blocked (MEDIUM, BLOCKED). Blocking: `false`.
- `RISK-010` Offshore or low-disclosure sources remain incomplete (MEDIUM, ACCEPTED_LIMITATION). Blocking: `false`.
- `RISK-011` Current scoring method lacks predictive validation claim (HIGH, MITIGATED). Blocking: `false`.
- `RISK-012` Legal/compliance no-advice boundary must remain intact (HIGH, MITIGATED). Blocking: `false`.
- `RISK-013` UX exposes multiple separated populations (LOW, MITIGATED). Blocking: `false`.
- `RISK-014` Product is still local release candidate, not final publication (MEDIUM, ACCEPTED_LIMITATION). Blocking: `false`.

## Blocking Status

No blocking product risks are active for the next phase. Known limitations remain visible and accepted/deferred with mitigation.

## Next

Proceed to `v2.38CH -- Release candidate audit`.
