# Required Outputs Diagnostics v2.38CD

Decision: `LOCAL_APP_READY_WITH_WARNINGS`.

This phase inventories the files required to run Scout Finance locally and to display the real experimental global ranking. It does not call the network, recompute scoring, change methodology, update weights, mutate datasets, change the UI, create recommendations, or enable broker actions.

## Output Checklist

- Outputs checked: 24
- Present: 24
- Optional: 0
- Blocking missing: 0

## Blocking Status

No blocking required outputs are missing.

## Missing Or Degraded Data

- `europe_ambiguous_identity_review`: Ambiguous European Cboe identities still require manual review before promotion. Blocking: `false`.
- `cboe_mass_identity_scaleup`: Mass Cboe Europe identity expansion remains deferred pending explicit scope decision. Blocking: `false`.
- `uk_official_source_blocked`: UK official source path is documented as blocked for safe automation. Blocking: `false`.
- `jurisdictions_without_adapter`: Some assets remain NOT_YET_SCORED_NO_ADAPTER and are excluded from scored ranking populations. Blocking: `false`.
- `low_coverage_blocked_assets`: Assets with insufficient real factor coverage remain BLOCKED and visible as limitations. Blocking: `false`.

## Local Decision

The local app and experimental ranking remain usable with warnings because required runtime, ranking, release-candidate, startup-validation and user-guide outputs are present. Known European coverage, provider and adapter gaps stay documented as non-blocking limitations.

Next recommended phase: `v2.38CE -- Windows reproducible local packaging`.
