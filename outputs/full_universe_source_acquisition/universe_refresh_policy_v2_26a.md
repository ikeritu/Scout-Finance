# Scout Finance — v2.26A Universe Refresh Policy

**Status:** `UNIVERSE_REFRESH_POLICY_COMPLETED_NO_REFRESH_EXECUTED`

## Policy decision

`CONTROLLED_STAGED_REFRESH_FAIL_CLOSED`

Refreshes must be staged, immutable and fail closed. A downloaded provider file or a newly built universe is never operational merely because it exists.

## Frozen baselines

Two references are intentionally kept distinct:

- Operational identity baseline: **43,089 rows**, v2.21H, SHA256 `9d33b0e4d7e309889d67e5a6d67c2fdfd4475b0d7cf5bf51ab0b71acb4db4707`.
- Promoted metadata comparison baseline: **43,089 rows**, v2.24F, SHA256 `01fef82316a458c65d42c08cb993feed9e0cc8178f4f7bf4f08835f169bfa74c`.

v2.26A modifies neither baseline nor either operational pointer.

## Refresh lifecycle

1. Save immutable raw provider snapshot with timestamp and SHA256.
2. Normalize into an isolated provider candidate.
3. Run provider checks and thresholds.
4. Build an isolated universe candidate.
5. Produce complete add/remove/change/conflict ledgers.
6. Validate rollback in v2.26D.
7. Decide promotion or freeze in v2.26E.
8. Only after approval, perform an atomic pointer swap.

## Important controls

- Global row delta above **5%** blocks the candidate unless an approved market event explains it.
- Provider changes above **max(100 rows, 15%)** block that provider candidate.
- Unresolved duplicate identities: **0 permitted**.
- New/changed derived values require **100% provenance**.
- Previously populated metadata cannot be blanked without approved evidence.
- First-cycle deletions are quarantined, not immediately removed.
- `__MISSING_PROVIDER__` remains outside automated refresh.
- At least three promoted generations and 12 months of raw snapshots are retained.

## Scoring isolation

Throughout v2.26:

- `production_scoring_authorized=False`
- `scoring_promoted=False`
- scoring pointer remains `NO_ACTIVE_PRODUCTION_SCORING_FAIL_CLOSED`
- universe refresh cannot implicitly activate the diagnostic v2.25B score

## Phase result

No provider was called, no candidate was created and no pointer was modified. This phase defines the enforceable policy for the controlled dry run.

**Recommended next phase:** `v2.26B — Provider Refresh Dry Run`.
