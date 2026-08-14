# Ranking consumer safety contract

1. Read the operational scoring pointer before loading any score artifact.
2. Require all pointer checks: supported schema, active status, active artifact, authorization, promotion, and matching SHA-256.
3. If any check fails, return `SCORING_UNAVAILABLE` and retain metadata-only catalog access.
4. Never fall back automatically to the v2.25B diagnostic artifact.
5. The diagnostic artifact may be opened only in an explicit internal diagnostic context and must display:
   - “Data-readiness diagnostic — not investment analysis”
   - 33,498/43,089 coverage
   - 9,591 instruments without scores
   - attractiveness weight 0
6. Do not emit best/worst, top pick, opportunity, buy, sell, hold, target, allocation, or broker-action semantics outside an authorized production state.
7. Unknown metadata and unscored rows must remain visible and selectable.
8. Ranks are scoped to the active filter set and use `identity_key` as the final deterministic tie-break.
9. Production score rows must disclose formula version, timestamp, coverage, components, and confidence.
10. Exports and UI consumers must apply this contract unchanged.
