# Rollback runbook — v2.26D

1. Read the current operational pointer and record its content SHA-256.
2. Resolve the target generation from a declared slot only: current, previous, or rollback.
3. Require the target artifact to exist.
4. Stream the artifact; verify data-row count and SHA-256 against the pointer inventory.
5. Prepare a new pointer document without overwriting any dataset.
6. Re-read the branch head and current pointer; abort on drift.
7. Commit the pointer as a fast-forward-only atomic change.
8. Re-read the committed pointer and target; repeat row and SHA-256 checks.
9. On any failure, do not write or force-update the pointer.
10. Scoring activation is out of scope and must remain fail-closed.

## Validated logical paths

- current → previous → current
- current → rollback → current
- candidate replay → current
- missing artifact / SHA mismatch / row mismatch → fail closed

This runbook requires an explicit gate before any real pointer mutation.
