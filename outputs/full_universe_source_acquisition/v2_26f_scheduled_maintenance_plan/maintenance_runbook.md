# Scheduled maintenance runbook

## Standard monthly window

1. Snapshot branch head and operational pointer SHA-256.
2. Run read-only provider probes.
3. Replay providers into a new immutable staging artifact; never overwrite a prior dataset.
4. Require 14/14 providers or a documented provider waiver.
5. Produce a row-level disposition ledger.
6. Verify candidate rows, SHA-256, identity uniqueness, quality band and metadata non-regression.
7. Run v2.26C delta classification against the current operational universe.
8. Re-run rollback validation.
9. Publish reports and choose one result:
   - **PASS / eligible for human gate**
   - **HOLD / remediation required**
   - **FAIL-CLOSED / incident response**
10. Only a separately approved promotion gate may update the pointer by atomic fast-forward.
11. Scoring activation remains separate and must never be inferred.

## Current priority

The next monthly run must first resolve the missing provider and 2,013-row gap carried from v2.26B/v2.26E.

## Change freeze

On P1: stop all candidate promotions, retain the last verified operational pointer, validate rollback, and preserve evidence. No force push, history rewrite, or dataset overwrite is permitted.
