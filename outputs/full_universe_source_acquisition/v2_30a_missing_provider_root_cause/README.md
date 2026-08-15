# v2.30A — Missing Provider Root-Cause & Recovery Plan

Status: **ROOT CAUSE IDENTIFIED; RECOVERY NOT YET AUTHORIZED; HOLD**.

The 2,013-row placeholder bucket is a single, coherent NSE India equity cohort. Every row has `provider=nse_india_v2_17g`, while the canonical `source_provider` field is null. This explains why v2.26B grouped the cohort as `__MISSING_PROVIDER__` and could not authorize a refresh route.

This phase does not rewrite those rows. It identifies the candidate provider and defines the evidence gates required before recovery.

## Evidence summary

- 2,013/2,013 rows: exchange NSE, country India, asset type equity, currency INR.
- 2,013 unique symbols, ISINs and instrument IDs.
- 2,013/2,013 rows carry the legacy provider value `nse_india_v2_17g`.
- 2,013/2,013 rows have no canonical `source_provider`, `source_file` or `source_url`.
- The cohort identification is strong; the precise historical transformation that dropped the canonical field remains to be proven.

## Decision

No provider route is authorized in v2.30A. The next phase must recover immutable NSE evidence, validate the deterministic alias, and run a controlled replay. Universe and scoring pointers remain unchanged; promotion remains fail-closed.

## Next

v2.30B — NSE Provider Evidence Recovery and Controlled Replay.
