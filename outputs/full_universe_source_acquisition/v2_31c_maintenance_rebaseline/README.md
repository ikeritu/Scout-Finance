# v2.31C — Maintenance State and Alert Rebaseline

Status: **14/14 baseline active · 10/10 blocking alerts green**.

The historical 13/14 maintenance state is replaced by the promoted operational baseline:

- Universe: 43,089 rows.
- Providers: 14/14.
- Missing provider rows: 0.
- Duplicate identities: 0.
- Pointer, artifact and XZ integrity: healthy.
- Performance and memory: within thresholds.
- Production scoring: false and fail-closed.

Ten blocking alerts now have explicit thresholds and responses. One advisory remains pending: the supervised live provider probe planned for v2.31D. It cannot modify the operational pointer or authorize scoring.

Next: **v2.31D — live provider probe**.
